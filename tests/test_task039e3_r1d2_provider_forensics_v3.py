"""Offline provider-forensics tests for TASK-039E3-R1D2 transport V3."""

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
    evaluate_recovery_capability_response_v1,
)
from paperworks.v6.task039e3_recovery_live_transport_v3 import (
    MAXIMUM_TRANSPORT_ATTEMPTS,
    MAXIMUM_TRANSPORT_RETRIES,
    RETRY_DELAYS_SECONDS,
    RecoveryLiveOpenAIChatCompletionsTransportV3,
    URLOPEN_TIMEOUT_SECONDS,
    logical_parse_status_v3,
    terminal_classification_v3,
)


_MODEL = "gpt-5.4-2026-03-05"


class _RawResponse:
    def __init__(self, raw: bytes, status: int = 200) -> None:
        self.status = status
        self._raw = raw

    def __enter__(self) -> "_RawResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._raw


def _response(document: object, status: int = 200) -> _RawResponse:
    return _RawResponse(json.dumps(document).encode("utf-8"), status)


def _document(
    *,
    model: str = _MODEL,
    response_id: str = "chatcmpl-r1d2",
    content: object | None = None,
    refusal: object | None = None,
) -> dict[str, object]:
    if content is None:
        content = json.dumps(
            {
                "fixture_id": RECOVERY_CAPABILITY_FIXTURE_ID,
                "capability_token": RECOVERY_CAPABILITY_TOKEN,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    return {
        "id": response_id,
        "model": model,
        "system_fingerprint": "fp-r1d2",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": content, "refusal": refusal},
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
    }


def _http_error(status: int, retry_after: str | None = None) -> HTTPError:
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    return HTTPError("https://offline.invalid", status, "offline", headers, BytesIO())


def _one_attempt(opener: object):
    transport = RecoveryLiveOpenAIChatCompletionsTransportV3(
        api_key="synthetic-test-only",
        opener=opener,  # type: ignore[arg-type]
        sleeper=lambda _seconds: None,
    )
    mapped = transport.send(build_recovery_capability_request_v1())
    return mapped, transport.attempt_custody[0]


class RecoveryProviderForensicsV3Tests(unittest.TestCase):
    def test_malformed_http_200_is_present_provider_response_not_transport_failure(self) -> None:
        malformed = (
            ("invalid_utf8", _RawResponse(b"\xff\xfe"), None, None),
            ("invalid_json", _RawResponse(b"{not-json"), None, None),
            ("non_object_json", _response(["not", "an", "object"]), None, None),
            (
                "invalid_envelope",
                _response({"id": "chatcmpl-shape", "model": _MODEL, "choices": []}),
                _MODEL,
                "chatcmpl-shape",
            ),
            (
                "malformed_message",
                _response(
                    {
                        "id": "chatcmpl-message",
                        "model": _MODEL,
                        "choices": [{"finish_reason": "stop", "message": []}],
                    }
                ),
                _MODEL,
                "chatcmpl-message",
            ),
            (
                "malformed_message_content",
                _response(_document(content={"not": "a string"})),
                _MODEL,
                "chatcmpl-r1d2",
            ),
            (
                "invalid_structured_json",
                _response(_document(content="{not-structured-json")),
                _MODEL,
                "chatcmpl-r1d2",
            ),
            (
                "non_object_structured_json",
                _response(_document(content="[1,2,3]")),
                _MODEL,
                "chatcmpl-r1d2",
            ),
            (
                "malformed_refusal",
                _response(_document(refusal={"not": "a string"})),
                _MODEL,
                "chatcmpl-r1d2",
            ),
        )
        for name, http_response, returned_model, response_id in malformed:
            with self.subTest(name=name):
                mapped, attempt = _one_attempt(
                    lambda *_args, _response=http_response, **_kwargs: _response
                )
                self.assertTrue(mapped.transport_response_received)
                self.assertTrue(mapped.provider_payload_received)
                self.assertTrue(mapped.provider_contacted)
                self.assertTrue(mapped.provider_authored_response)
                self.assertTrue(mapped.response_present)
                self.assertFalse(mapped.structured_payload_valid)
                self.assertEqual(mapped.status_code, 200)
                self.assertEqual(mapped.outcome, "schema_invalid_response")
                self.assertEqual(mapped.model, returned_model)
                self.assertEqual(mapped.response_id, response_id)
                self.assertIsNotNone(mapped.provider_payload_hash)
                self.assertEqual(
                    terminal_classification_v3(mapped),
                    "completed_schema_invalid_response",
                )
                self.assertEqual(
                    logical_parse_status_v3(mapped), "schema_invalid_response"
                )

                self.assertTrue(attempt.transport_response_received)
                self.assertTrue(attempt.provider_payload_received)
                self.assertTrue(attempt.provider_contacted)
                self.assertTrue(attempt.provider_authored_response)
                self.assertTrue(attempt.response_present)
                self.assertFalse(attempt.structured_payload_valid)
                self.assertEqual(attempt.status_code, 200)
                self.assertFalse(attempt.retry_eligible)
                self.assertEqual(
                    attempt.terminal_classification,
                    "completed_schema_invalid_response",
                )
                serialized = json.dumps(attempt.to_dict(), sort_keys=True)
                self.assertNotIn("transport_exhausted", serialized)
                self.assertNotIn('"outcome": "transport_failure"', serialized)

                gate = evaluate_recovery_capability_response_v1(mapped)
                self.assertEqual(gate.gate_status, "BLOCK")

    def test_unexpected_model_and_response_id_are_preserved_and_terminal(self) -> None:
        unexpected_model = "gpt-unexpected-snapshot"
        unexpected_id = "chatcmpl-unexpected"
        transport = RecoveryLiveOpenAIChatCompletionsTransportV3(
            api_key="synthetic-test-only",
            opener=lambda *_args, **_kwargs: _response(
                _document(model=unexpected_model, response_id=unexpected_id)
            ),
            sleeper=lambda _seconds: self.fail("model mismatch must not retry"),
        )
        mapped = transport.send(build_recovery_capability_request_v1())
        self.assertTrue(mapped.response_present)
        self.assertTrue(mapped.provider_authored_response)
        self.assertEqual(mapped.outcome, "model_identity_integrity")
        self.assertEqual(mapped.model, unexpected_model)
        self.assertEqual(mapped.response_id, unexpected_id)
        self.assertEqual(mapped.finish_reason, "stop")
        self.assertFalse(transport.attempt_custody[0].retry_eligible)
        self.assertEqual(
            transport.attempt_custody[0].terminal_classification,
            "completed_model_identity_mismatch",
        )
        self.assertEqual(transport.calls, 1)

    def test_success_and_refusal_are_coherent_provider_observations(self) -> None:
        for name, refusal, outcome, terminal in (
            ("success", None, "successful_response", "completed_provider_response"),
            (
                "refusal",
                "synthetic refusal",
                "provider_refusal",
                "completed_provider_refusal",
            ),
        ):
            with self.subTest(name=name):
                mapped, attempt = _one_attempt(
                    lambda *_args, _refusal=refusal, **_kwargs: _response(
                        _document(refusal=_refusal)
                    )
                )
                self.assertTrue(mapped.response_present)
                self.assertTrue(mapped.provider_authored_response)
                self.assertEqual(mapped.structured_payload_valid, refusal is None)
                self.assertEqual(mapped.outcome, outcome)
                self.assertEqual(attempt.terminal_classification, terminal)
                self.assertFalse(attempt.retry_eligible)
                self.assertEqual(attempt.returned_model, _MODEL)
                self.assertEqual(attempt.response_id, "chatcmpl-r1d2")
                self.assertEqual(attempt.system_fingerprint, "fp-r1d2")

    def test_exact_timeout_retry_budget_and_retry_after_are_preserved(self) -> None:
        calls = 0
        waits: list[float] = []
        observed_timeouts: list[float] = []

        def opener(_request: object, *, timeout: float) -> _RawResponse:
            nonlocal calls
            calls += 1
            observed_timeouts.append(timeout)
            if calls == 1:
                raise _http_error(429, "7")
            if calls == 2:
                raise TimeoutError("synthetic timeout")
            return _response(_document())

        transport = RecoveryLiveOpenAIChatCompletionsTransportV3(
            api_key="synthetic-test-only", opener=opener, sleeper=waits.append
        )
        request = build_recovery_capability_request_v1()
        first = transport.send(request)
        second = transport.send(request)
        third = transport.send(request)
        self.assertEqual(first.outcome, "http_429")
        self.assertEqual(second.outcome, "timeout_before_response")
        self.assertEqual(third.outcome, "successful_response")
        self.assertEqual(observed_timeouts, [30.0, 30.0, 30.0])
        self.assertEqual(waits, [7.0, 4.0])
        self.assertEqual(MAXIMUM_TRANSPORT_RETRIES, 2)
        self.assertEqual(MAXIMUM_TRANSPORT_ATTEMPTS, 3)
        self.assertEqual(RETRY_DELAYS_SECONDS, (2.0, 4.0))
        self.assertEqual(
            [item.attempt_number for item in transport.attempt_custody], [1, 2, 3]
        )

    def test_http_and_connection_failure_retry_classes_remain_exact(self) -> None:
        for failure, outcome, retryable, transport_received in (
            (_http_error(400), "http_400", False, True),
            (_http_error(401), "http_401", False, True),
            (_http_error(403), "http_403", False, True),
            (_http_error(500), "http_5xx", True, True),
            (TimeoutError("synthetic timeout"), "timeout_before_response", True, False),
            (ConnectionResetError("synthetic reset"), "connection_reset", True, False),
            (URLError("synthetic connection"), "connection_failure", True, False),
        ):
            with self.subTest(outcome=outcome):
                mapped, attempt = _one_attempt(
                    lambda *_args, _failure=failure, **_kwargs: (_ for _ in ()).throw(
                        _failure
                    )
                )
                self.assertFalse(mapped.response_present)
                self.assertFalse(mapped.provider_authored_response)
                self.assertEqual(mapped.outcome, outcome)
                self.assertEqual(mapped.transport_response_received, transport_received)
                self.assertEqual(attempt.retry_eligible, retryable)

    def test_custody_and_request_hashes_exclude_credential_material(self) -> None:
        observed: dict[str, object] = {}

        def opener(request: object, *, timeout: float) -> _RawResponse:
            observed["timeout"] = timeout
            observed["header_present"] = bool(request.get_header("Authorization"))
            return _response(_document())

        transport = RecoveryLiveOpenAIChatCompletionsTransportV3(
            api_key="synthetic-test-only", opener=opener, sleeper=lambda _seconds: None
        )
        transport.send(build_recovery_capability_request_v1())
        self.assertEqual(
            observed,
            {"timeout": URLOPEN_TIMEOUT_SECONDS, "header_present": True},
        )
        serialized = json.dumps(transport.attempt_custody[0].to_dict(), sort_keys=True)
        self.assertNotIn("synthetic-test-only", serialized)
        self.assertNotIn("Authorization", serialized)
        self.assertNotIn("Bearer", serialized)

    def test_timeout_override_and_fourth_retry_attempt_fail_closed(self) -> None:
        with self.assertRaisesRegex(TASK039E3PreparationError, "R1A authority"):
            RecoveryLiveOpenAIChatCompletionsTransportV3(
                api_key="synthetic-test-only", timeout_seconds=31.0
            )

        transport = RecoveryLiveOpenAIChatCompletionsTransportV3(
            api_key="synthetic-test-only",
            opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                TimeoutError("synthetic timeout")
            ),
            sleeper=lambda _seconds: None,
        )
        request = build_recovery_capability_request_v1()
        for _ in range(MAXIMUM_TRANSPORT_ATTEMPTS):
            transport.send(request)
        with self.assertRaisesRegex(TASK039E3PreparationError, "retry budget"):
            transport.send(request)


if __name__ == "__main__":
    unittest.main()
