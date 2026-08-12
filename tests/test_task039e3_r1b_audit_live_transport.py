"""Independent offline audit oracle for reused TASK-039E3 live transport."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError, URLError

from paperworks.v6.task039e3_live_transport_v1 import (
    CALL_TIMEOUT_SECONDS,
    LiveOpenAIChatCompletionsTransportV1,
)
from paperworks.v6.task039e3_recovery_execution_v1 import (
    execute_recovery_probe_v1,
    write_recovery_capability_private_custody_v1,
)


_MODEL = "gpt-5.4-2026-03-05"
_UNEXPECTED_MODEL = "gpt-unexpected-audit-fixture"


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
    content: object | None = None,
    refusal: object | None = None,
) -> dict[str, object]:
    if content is None:
        content = json.dumps(
            {
                "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
                "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    return {
        "id": "resp_audit",
        "model": model,
        "system_fingerprint": "fp_audit",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": content, "refusal": refusal},
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
    }


def _http_error(status: int, *, retry_after: str | None = None) -> HTTPError:
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    return HTTPError("https://audit.invalid", status, "audit", headers, BytesIO())


class TestTask039E3R1BAuditLiveTransport(unittest.TestCase):
    def test_timeout_is_thirty_seconds_per_attempt_and_retry_budget_is_two(self) -> None:
        timeouts: list[float] = []
        waits: list[float] = []

        def opener(_request: object, *, timeout: float) -> _Response:
            timeouts.append(timeout)
            raise TimeoutError("offline audit timeout")

        transport = LiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-audit-key",
            opener=opener,
            sleeper=waits.append,
        )
        execution = execute_recovery_probe_v1(transport)
        self.assertEqual(float(CALL_TIMEOUT_SECONDS), 30.0)
        self.assertEqual(timeouts, [30, 30, 30])
        self.assertEqual(waits, [2.0, 4.0])
        self.assertEqual(execution.transport_attempts, 3)
        self.assertEqual(execution.transport_retries, 2)
        self.assertEqual(execution.accounting.current_recovery_probe_count, 1)
        self.assertEqual(
            [item.outcome for item in transport.attempt_custody],
            ["timeout_before_response"] * 3,
        )
        self.assertEqual(
            [item.actual_retry_delay_before_attempt_seconds for item in transport.attempt_custody],
            [None, 2.0, 4.0],
        )

    def test_retryable_connection_reset_and_connection_failure(self) -> None:
        cases = (
            (ConnectionResetError("reset"), "connection_reset"),
            (URLError("offline"), "connection_failure"),
            (URLError(ConnectionResetError("reset")), "connection_reset"),
        )
        for failure, expected in cases:
            with self.subTest(expected=expected, failure=type(failure).__name__):
                calls = 0
                waits: list[float] = []

                def opener(*_args: object, **_kwargs: object) -> _Response:
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        raise failure
                    return _Response(_document())

                transport = LiveOpenAIChatCompletionsTransportV1(
                    api_key="synthetic-audit-key",
                    opener=opener,
                    sleeper=waits.append,
                )
                execution = execute_recovery_probe_v1(transport)
                self.assertEqual(execution.transport_attempts, 2)
                self.assertEqual(transport.attempt_custody[0].outcome, expected)
                self.assertEqual(waits, [2.0])

    def test_http_429_retry_after_and_http_5xx_are_retryable(self) -> None:
        cases = ((429, "http_429", "7", 7.0), (503, "http_5xx", None, 2.0))
        for status, expected, retry_after, expected_wait in cases:
            with self.subTest(status=status):
                calls = 0
                waits: list[float] = []

                def opener(*_args: object, **_kwargs: object) -> _Response:
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        raise _http_error(status, retry_after=retry_after)
                    return _Response(_document())

                transport = LiveOpenAIChatCompletionsTransportV1(
                    api_key="synthetic-audit-key",
                    opener=opener,
                    sleeper=waits.append,
                )
                execution = execute_recovery_probe_v1(transport)
                self.assertEqual(execution.transport_attempts, 2)
                self.assertEqual(transport.attempt_custody[0].outcome, expected)
                self.assertEqual(waits, [expected_wait])

    def test_http_400_401_403_are_terminal_without_retry(self) -> None:
        for status in (400, 401, 403):
            with self.subTest(status=status):
                waits: list[float] = []

                def opener(*_args: object, **_kwargs: object) -> _Response:
                    raise _http_error(status)

                transport = LiveOpenAIChatCompletionsTransportV1(
                    api_key="synthetic-audit-key",
                    opener=opener,
                    sleeper=waits.append,
                )
                execution = execute_recovery_probe_v1(transport)
                self.assertEqual(execution.transport_attempts, 1)
                self.assertEqual(execution.response.outcome, f"http_{status}")
                self.assertEqual(waits, [])

    def test_refusal_is_response_present_and_nonretryable(self) -> None:
        transport = LiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-audit-key",
            opener=lambda *_args, **_kwargs: _Response(
                _document(refusal="declined by audit fixture")
            ),
            sleeper=lambda _seconds: self.fail("refusal must not retry"),
        )
        execution = execute_recovery_probe_v1(transport)
        self.assertEqual(execution.transport_attempts, 1)
        self.assertTrue(execution.response.response_present)
        self.assertTrue(execution.response.refusal)
        self.assertEqual(execution.response.outcome, "provider_refusal")
        self.assertEqual(execution.gate.gate_status, "BLOCK")

    def test_envelope_and_strict_content_schema_failures_are_nonretryable(self) -> None:
        malformed_envelope = {"id": "missing_choices", "model": _MODEL}
        invalid_contents = ("not-json", json.dumps({"fixture_id": "wrong"}))
        documents = (malformed_envelope,) + tuple(
            _document(content=value) for value in invalid_contents
        )
        for index, document in enumerate(documents):
            with self.subTest(index=index):
                transport = LiveOpenAIChatCompletionsTransportV1(
                    api_key="synthetic-audit-key",
                    opener=lambda *_args, _document=document, **_kwargs: _Response(_document),
                    sleeper=lambda _seconds: self.fail("schema failure must not retry"),
                )
                execution = execute_recovery_probe_v1(transport)
                self.assertEqual(execution.transport_attempts, 1)
                self.assertEqual(execution.gate.gate_status, "BLOCK")
                self.assertIn(
                    execution.response.outcome,
                    {"schema_invalid_response", "successful_response"},
                )

    def test_wrong_model_is_terminal_but_actual_observation_is_lost_from_custody(self) -> None:
        raw_document = _document(model=_UNEXPECTED_MODEL)
        transport = LiveOpenAIChatCompletionsTransportV1(
            api_key="synthetic-audit-key",
            opener=lambda *_args, **_kwargs: _Response(raw_document),
            sleeper=lambda _seconds: self.fail("model mismatch must not retry"),
        )
        execution = execute_recovery_probe_v1(transport)
        self.assertEqual(execution.transport_attempts, 1)
        self.assertEqual(execution.transport_retries, 0)
        self.assertEqual(execution.response.outcome, "model_identity_integrity")
        self.assertEqual(execution.response.status_code, 200)
        self.assertFalse(execution.response.response_present)
        self.assertIsNone(execution.response.model)
        self.assertIsNone(execution.response.response_id)

        mapped_attempt = transport.attempt_custody[0].to_dict()
        self.assertIsNone(mapped_attempt["returned_model"])
        self.assertIsNone(mapped_attempt["response_id"])
        self.assertNotIn(_UNEXPECTED_MODEL, json.dumps(mapped_attempt, sort_keys=True))

        with tempfile.TemporaryDirectory(prefix="task039e3-r1b-audit-") as directory:
            binding = write_recovery_capability_private_custody_v1(
                recovery_private_root=Path(directory),
                run_identity="synthetic-r1b-audit-run",
                execution=execution,
            )
            self.assertEqual(binding.record_count, 1)
            ledger_path = Path(directory) / "recovery_capability_provider_calls.jsonl"
            durable = json.loads(ledger_path.read_text(encoding="utf-8"))

        provider_record = durable["provider_record"]
        metadata = provider_record["provider_response_metadata"]
        self.assertEqual(metadata["outcome"], "model_identity_integrity")
        self.assertEqual(metadata["status_code"], 200)
        self.assertIsNone(metadata["model"])
        self.assertFalse(provider_record["response_present"])
        self.assertEqual(provider_record["terminal_slot_state"], "transport_exhausted")
        self.assertNotIn(_UNEXPECTED_MODEL, json.dumps(durable, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
