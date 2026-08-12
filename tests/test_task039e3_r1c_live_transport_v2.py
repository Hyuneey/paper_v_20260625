"""Offline unit tests for TASK-039E3-R1C recovery transport V2."""

from __future__ import annotations

from io import BytesIO
import json
import unittest
from urllib.error import HTTPError, URLError

from paperworks.v6.task039e3_execution_prep_v1 import TASK039E3PreparationError
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_recovery_live_transport_v2 import (
    MAXIMUM_TRANSPORT_ATTEMPTS,
    MAXIMUM_TRANSPORT_RETRIES,
    RETRY_DELAYS_SECONDS,
    RecoveryLiveOpenAIChatCompletionsTransportV2,
    URLOPEN_TIMEOUT_SECONDS,
)


_MODEL = "gpt-5.4-2026-03-05"


class _Response:
    def __init__(self, document: object, status: int = 200) -> None:
        self.status = status
        self._raw = json.dumps(document).encode("utf-8")

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._raw


def _document(
    *,
    model: str = _MODEL,
    response_id: str = "chatcmpl-r1c",
    refusal: str | None = None,
) -> dict[str, object]:
    return {
        "id": response_id,
        "model": model,
        "system_fingerprint": "fp-r1c",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "fixture_id": RECOVERY_CAPABILITY_FIXTURE_ID,
                            "capability_token": RECOVERY_CAPABILITY_TOKEN,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "refusal": refusal,
                },
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
    }


def _http_error(status: int, retry_after: str | None = None) -> HTTPError:
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    return HTTPError("https://offline.invalid", status, "offline", headers, BytesIO())


class RecoveryLiveTransportV2Tests(unittest.TestCase):
    def test_success_uses_exact_timeout_and_records_provider_origin(self) -> None:
        observed: dict[str, object] = {}

        def opener(request: object, *, timeout: float) -> _Response:
            observed["timeout"] = timeout
            observed["authorization_present"] = bool(
                request.get_header("Authorization")
            )
            return _Response(_document())

        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-only-key",
            opener=opener,
            sleeper=lambda _seconds: None,
        )
        response = transport.send(build_recovery_capability_request_v1())
        self.assertTrue(response.response_present)
        self.assertEqual(response.model, _MODEL)
        self.assertEqual(
            observed,
            {"timeout": URLOPEN_TIMEOUT_SECONDS, "authorization_present": True},
        )
        custody = transport.attempt_custody[0].to_dict()
        self.assertEqual(custody["response_origin"], "provider")
        self.assertTrue(custody["provider_contacted"])
        self.assertTrue(custody["provider_authored_response"])
        self.assertEqual(custody["attempt_number"], 1)
        self.assertEqual(custody["terminal_classification"], "completed_provider_response")
        serialized = json.dumps(custody, sort_keys=True)
        self.assertNotIn("synthetic-only-key", serialized)
        self.assertNotIn("Authorization", serialized)

    def test_model_mismatch_preserves_exact_provider_observation_and_is_terminal(self) -> None:
        unexpected_model = "gpt-unexpected"
        unexpected_id = "chatcmpl-unexpected"
        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic",
            opener=lambda *_args, **_kwargs: _Response(
                _document(model=unexpected_model, response_id=unexpected_id)
            ),
            sleeper=lambda _seconds: self.fail("model mismatch must not retry"),
        )
        response = transport.send(build_recovery_capability_request_v1())
        self.assertTrue(response.response_present)
        self.assertEqual(response.outcome, "model_identity_integrity")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.model, unexpected_model)
        self.assertEqual(response.response_id, unexpected_id)
        self.assertEqual(response.finish_reason, "stop")
        self.assertEqual(dict(response.token_usage or {}), {
            "prompt_tokens": 3,
            "completion_tokens": 2,
            "total_tokens": 5,
        })

        custody = transport.attempt_custody[0].to_dict()
        self.assertEqual(custody["returned_model"], unexpected_model)
        self.assertEqual(custody["response_id"], unexpected_id)
        self.assertEqual(custody["status_code"], 200)
        self.assertEqual(custody["finish_reason"], "stop")
        self.assertEqual(custody["system_fingerprint"], "fp-r1c")
        self.assertFalse(custody["retry_eligible"])
        self.assertEqual(
            custody["terminal_classification"],
            "completed_model_identity_mismatch",
        )
        self.assertEqual(transport.calls, 1)

    def test_timeout_retry_budget_and_fixed_waits_are_per_logical_request(self) -> None:
        waits: list[float] = []
        timeouts: list[float] = []

        def opener(_request: object, *, timeout: float) -> _Response:
            timeouts.append(timeout)
            raise TimeoutError("synthetic timeout")

        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic",
            opener=opener,
            sleeper=waits.append,
        )
        request = build_recovery_capability_request_v1()
        responses = [transport.send(request) for _ in range(MAXIMUM_TRANSPORT_ATTEMPTS)]
        self.assertEqual([item.outcome for item in responses], ["timeout_before_response"] * 3)
        self.assertEqual(timeouts, [30.0, 30.0, 30.0])
        self.assertEqual(waits, list(RETRY_DELAYS_SECONDS))
        self.assertEqual(MAXIMUM_TRANSPORT_RETRIES, 2)
        self.assertEqual(
            [item.attempt_number for item in transport.attempt_custody],
            [1, 2, 3],
        )
        with self.assertRaisesRegex(TASK039E3PreparationError, "retry budget"):
            transport.send(request)

    def test_retry_after_overrides_only_the_corresponding_wait(self) -> None:
        attempts = 0
        waits: list[float] = []

        def opener(*_args: object, **_kwargs: object) -> _Response:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise _http_error(429, "7")
            return _Response(_document())

        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic", opener=opener, sleeper=waits.append
        )
        request = build_recovery_capability_request_v1()
        first = transport.send(request)
        second = transport.send(request)
        self.assertEqual(first.outcome, "http_429")
        self.assertTrue(second.response_present)
        self.assertEqual(waits, [7.0])
        first_custody, second_custody = transport.attempt_custody
        self.assertEqual(first_custody.retry_after_seconds_observed, 7.0)
        self.assertEqual(second_custody.actual_retry_delay_before_attempt_seconds, 7.0)

    def test_http_5xx_retries_but_400_401_403_are_terminal(self) -> None:
        for status in (400, 401, 403):
            with self.subTest(status=status):
                transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
                    api_key="synthetic",
                    opener=lambda *_args, _status=status, **_kwargs: (_ for _ in ()).throw(
                        _http_error(_status)
                    ),
                    sleeper=lambda _seconds: self.fail("terminal HTTP error retried"),
                )
                response = transport.send(build_recovery_capability_request_v1())
                self.assertEqual(response.outcome, f"http_{status}")
                self.assertFalse(transport.attempt_custody[0].retry_eligible)

        calls = 0
        waits: list[float] = []

        def retrying(*_args: object, **_kwargs: object) -> _Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise _http_error(503)
            return _Response(_document())

        retry_transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic", opener=retrying, sleeper=waits.append
        )
        request = build_recovery_capability_request_v1()
        self.assertEqual(retry_transport.send(request).outcome, "http_5xx")
        self.assertTrue(retry_transport.send(request).response_present)
        self.assertEqual(waits, [2.0])

    def test_connection_failure_and_reset_retain_retry_parity(self) -> None:
        failures = (
            (URLError("synthetic connection failure"), "connection_failure"),
            (ConnectionResetError("synthetic reset"), "connection_reset"),
            (URLError(ConnectionResetError("synthetic reset")), "connection_reset"),
        )
        for failure, expected in failures:
            with self.subTest(expected=expected):
                calls = 0
                waits: list[float] = []

                def opener(*_args: object, **_kwargs: object) -> _Response:
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        raise failure
                    return _Response(_document())

                transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
                    api_key="synthetic", opener=opener, sleeper=waits.append
                )
                request = build_recovery_capability_request_v1()
                first = transport.send(request)
                second = transport.send(request)
                self.assertEqual(first.outcome, expected)
                self.assertFalse(first.response_present)
                self.assertTrue(transport.attempt_custody[0].retry_eligible)
                self.assertTrue(second.response_present)
                self.assertEqual(waits, [2.0])

    def test_refusal_and_schema_invalid_response_are_nonretryable(self) -> None:
        refusal_transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic",
            opener=lambda *_args, **_kwargs: _Response(_document(refusal="declined")),
            sleeper=lambda _seconds: self.fail("refusal retried"),
        )
        refusal = refusal_transport.send(build_recovery_capability_request_v1())
        self.assertTrue(refusal.response_present)
        self.assertTrue(refusal.refusal)
        self.assertEqual(refusal.outcome, "provider_refusal")
        self.assertFalse(refusal_transport.attempt_custody[0].retry_eligible)

        invalid_transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic",
            opener=lambda *_args, **_kwargs: _Response({"not": "an envelope"}),
            sleeper=lambda _seconds: self.fail("schema failure retried"),
        )
        invalid = invalid_transport.send(build_recovery_capability_request_v1())
        self.assertEqual(invalid.outcome, "schema_invalid_response")
        self.assertFalse(invalid_transport.attempt_custody[0].retry_eligible)

    def test_timeout_override_is_rejected(self) -> None:
        with self.assertRaisesRegex(TASK039E3PreparationError, "R1A authority"):
            RecoveryLiveOpenAIChatCompletionsTransportV2(
                api_key="synthetic", timeout_seconds=60.0
            )


if __name__ == "__main__":
    unittest.main()
