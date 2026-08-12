"""Independent offline provider-response forensic oracle for R1C V2."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
import unittest
from urllib.error import HTTPError, URLError

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    ProviderCallSlotV1,
    ScientificRunAbortV1,
    execute_mock_provider_slot_v1,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
    build_recovery_capability_request_v1,
)
from paperworks.v6.task039e3_recovery_custody_v2 import (
    RecoveryCapabilityProviderLedgerV2,
    ScientificProviderLedgerV2,
)
from paperworks.v6.task039e3_recovery_execution_v2 import (
    execute_recovery_capability_probe_v2,
    freeze_capability_custody_v2,
)
from paperworks.v6.task039e3_recovery_live_transport_v2 import (
    RecoveryLiveOpenAIChatCompletionsTransportV2,
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
    response_id: str = "chatcmpl-forensic",
    content: object | None = None,
    refusal: str | None = None,
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
        "system_fingerprint": "fp-forensic",
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
    transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
        api_key="synthetic-audit-only",
        opener=opener,  # type: ignore[arg-type]
        sleeper=lambda _seconds: None,
    )
    mapped = transport.send(build_recovery_capability_request_v1())
    return mapped, transport.attempt_custody[0]


class R1CProviderForensicAudit(unittest.TestCase):
    def test_valid_refusal_and_returned_model_mismatch_metadata(self) -> None:
        cases = (
            (
                "valid",
                _document(),
                "successful_response",
                "completed_provider_response",
                True,
                _MODEL,
                "chatcmpl-forensic",
            ),
            (
                "refusal",
                _document(refusal="synthetic refusal"),
                "provider_refusal",
                "completed_provider_refusal",
                True,
                _MODEL,
                "chatcmpl-forensic",
            ),
            (
                "mismatch",
                _document(model="gpt-unexpected-snapshot", response_id="chatcmpl-unexpected"),
                "model_identity_integrity",
                "completed_model_identity_mismatch",
                True,
                "gpt-unexpected-snapshot",
                "chatcmpl-unexpected",
            ),
        )
        for name, document, outcome, terminal, present, model, response_id in cases:
            with self.subTest(name=name):
                mapped, attempt = _one_attempt(
                    lambda *_args, _document=document, **_kwargs: _response(_document)
                )
                self.assertEqual(mapped.outcome, outcome)
                self.assertEqual(mapped.response_present, present)
                self.assertTrue(attempt.provider_contacted)
                self.assertTrue(attempt.provider_authored_response)
                self.assertEqual(attempt.response_origin, "provider")
                self.assertEqual(attempt.status_code, 200)
                self.assertEqual(attempt.terminal_classification, terminal)
                self.assertFalse(attempt.retry_eligible)
                self.assertEqual(attempt.returned_model, model)
                self.assertEqual(attempt.response_id, response_id)
                self.assertEqual(attempt.finish_reason, "stop")
                self.assertEqual(attempt.system_fingerprint, "fp-forensic")
                self.assertEqual(dict(attempt.token_usage or {}), {
                    "prompt_tokens": 3,
                    "completion_tokens": 2,
                    "total_tokens": 5,
                })

    def test_http_status_forensics_and_retry_classes(self) -> None:
        for status, outcome, retryable in (
            (400, "http_400", False),
            (401, "http_401", False),
            (403, "http_403", False),
            (429, "http_429", True),
            (500, "http_5xx", True),
            (503, "http_5xx", True),
        ):
            with self.subTest(status=status):
                mapped, attempt = _one_attempt(
                    lambda *_args, _status=status, **_kwargs: (_ for _ in ()).throw(
                        _http_error(_status, "7" if _status == 429 else None)
                    )
                )
                self.assertFalse(mapped.response_present)
                self.assertEqual(mapped.outcome, outcome)
                self.assertTrue(attempt.provider_contacted)
                self.assertFalse(attempt.provider_authored_response)
                self.assertEqual(attempt.status_code, status)
                self.assertEqual(attempt.retry_eligible, retryable)
                self.assertEqual(
                    attempt.terminal_classification,
                    "retryable_transport_failure"
                    if retryable
                    else "completed_nonretryable_transport_failure",
                )
                self.assertIsNone(attempt.returned_model)
                self.assertIsNone(attempt.response_id)

    def test_network_failure_forensics_and_retry_classes(self) -> None:
        failures = (
            (TimeoutError("offline timeout"), "timeout_before_response"),
            (socket.timeout("offline timeout"), "timeout_before_response"),
            (ConnectionResetError("offline reset"), "connection_reset"),
            (URLError(ConnectionResetError("offline reset")), "connection_reset"),
            (URLError("offline connect"), "connection_failure"),
        )
        for failure, outcome in failures:
            with self.subTest(failure=type(failure).__name__, outcome=outcome):
                mapped, attempt = _one_attempt(
                    lambda *_args, _failure=failure, **_kwargs: (_ for _ in ()).throw(
                        _failure
                    )
                )
                self.assertFalse(mapped.response_present)
                self.assertEqual(mapped.outcome, outcome)
                self.assertTrue(attempt.provider_contacted)
                self.assertFalse(attempt.provider_authored_response)
                self.assertIsNone(attempt.status_code)
                self.assertTrue(attempt.retry_eligible)
                self.assertEqual(attempt.terminal_classification, "retryable_transport_failure")

    def test_malformed_http_200_attempt_metadata_is_coherent_before_terminal_ledger(self) -> None:
        malformed_cases = (
            ("invalid_utf8", _RawResponse(b"\xff\xfe"), None, None, False),
            ("invalid_json", _RawResponse(b"{not-json"), None, None, False),
            ("non_object", _response(["not", "an", "object"]), None, None, False),
            (
                "invalid_envelope",
                _response({"id": "chatcmpl-shape", "model": _MODEL, "choices": []}),
                _MODEL,
                "chatcmpl-shape",
                False,
            ),
            (
                "malformed_message_content",
                _response(_document(content={"not": "a string"})),
                _MODEL,
                "chatcmpl-forensic",
                True,
            ),
        )
        for name, http_response, model, response_id, mapped_present in malformed_cases:
            with self.subTest(name=name):
                mapped, attempt = _one_attempt(
                    lambda *_args, _response=http_response, **_kwargs: _response
                )
                self.assertEqual(mapped.outcome, "schema_invalid_response")
                self.assertEqual(mapped.response_present, mapped_present)
                self.assertTrue(attempt.provider_contacted)
                self.assertTrue(attempt.provider_authored_response)
                self.assertEqual(attempt.response_origin, "provider")
                self.assertEqual(attempt.status_code, 200)
                self.assertEqual(attempt.returned_model, model)
                self.assertEqual(attempt.response_id, response_id)
                self.assertFalse(attempt.retry_eligible)
                self.assertEqual(
                    attempt.terminal_classification,
                    "completed_schema_invalid_response",
                )

    def test_blocking_malformed_http_200_capability_is_durably_transport_exhausted(self) -> None:
        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-audit-only",
            opener=lambda *_args, **_kwargs: _RawResponse(b"{not-json"),
            sleeper=lambda _seconds: self.fail("malformed response must not retry"),
        )
        execution = execute_recovery_capability_probe_v2(transport)
        self.assertEqual(execution.gate.gate_status, "BLOCK")
        self.assertEqual(
            transport.attempt_custody[0].terminal_classification,
            "completed_schema_invalid_response",
        )
        with TemporaryDirectory(prefix="task039e3-r1c-audit-malformed-cap-") as raw:
            ledger = RecoveryCapabilityProviderLedgerV2(Path(raw) / "capability.jsonl")
            freeze_capability_custody_v2(
                execution=execution,
                transport=transport,
                ledger=ledger,
            )
            durable = json.loads((Path(raw) / "capability.jsonl").read_text("utf-8"))
        self.assertTrue(durable["provider_authored_response"])
        self.assertEqual(durable["transport_attempts"][0]["status_code"], 200)
        self.assertEqual(
            durable["transport_attempts"][0]["outcome"],
            "schema_invalid_response",
        )
        # Blocking audit finding: the terminal logical slot contradicts the
        # received provider-authored HTTP-200 attempt and calls it transport exhaustion.
        self.assertEqual(durable["terminal_slot_state"], "transport_exhausted")

    def test_blocking_malformed_http_200_science_is_durably_transport_exhausted(self) -> None:
        transport = RecoveryLiveOpenAIChatCompletionsTransportV2(
            api_key="synthetic-audit-only",
            opener=lambda *_args, **_kwargs: _RawResponse(b"{not-json"),
            sleeper=lambda _seconds: self.fail("malformed response must not retry"),
        )
        request = build_recovery_capability_request_v1()
        with TemporaryDirectory(prefix="task039e3-r1c-audit-malformed-science-") as raw:
            ledger_path = Path(raw) / "scientific.jsonl"
            ledger = ScientificProviderLedgerV2(
                ledger_path,
                attempt_supplier=lambda: transport.attempt_custody,
            )
            slot = ProviderCallSlotV1(
                0,
                stable_hash_v1({"synthetic": "relation"}),
                "T1",
                1,
                True,
            )
            with self.assertRaises(ScientificRunAbortV1):
                execute_mock_provider_slot_v1(
                    slot=slot,
                    request=request,
                    transport=transport,
                    ledger=ledger,  # type: ignore[arg-type]
                    parse_kind="proposal",
                )
            durable = json.loads(ledger_path.read_text("utf-8"))
        self.assertTrue(durable["provider_authored_response"])
        self.assertEqual(durable["transport_attempts"][0]["status_code"], 200)
        self.assertEqual(durable["transport_attempts"][0]["outcome"], "schema_invalid_response")
        self.assertEqual(durable["terminal_slot_state"], "transport_exhausted")
        self.assertEqual(durable["parse_status"], "transport_failure")


if __name__ == "__main__":
    unittest.main()
