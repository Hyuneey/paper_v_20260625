from __future__ import annotations

import ast
from email.message import Message
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from urllib.error import HTTPError, URLError

from paperworks.v6.task039e2_execution_configuration_v1 import EXACT_MODEL
from paperworks.v6.task039e3_execution_prep_v1 import ProviderCallSlotV1
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RECOVERY_CAPABILITY_FIXTURE_ID,
    RECOVERY_CAPABILITY_TOKEN,
    build_recovery_capability_request_v1,
    evaluate_recovery_capability_response_v1,
)
from paperworks.v6.task039e3_recovery_execution_v3 import (
    RecoveryCapabilityExecutionV3,
    TASK039E3RecoveryScientificAbortV3Error,
    TransactionalScientificProviderLedgerV3,
    _failure_context_from_state,
    build_recovery_capability_receipt_v3,
    build_typed_accounting_v3,
    execute_recovery_capability_probe_v3,
    freeze_capability_custody_v3,
    write_terminal_failure_receipt_v3,
)
from paperworks.v6.task039e3_recovery_live_transport_v3 import (
    RecoveryLiveOpenAIChatCompletionsTransportV3,
    logical_parse_status_v3,
    terminal_classification_v3,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalHashChainCustodyV3,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_SHA = "1" * 64


class _RawResponse:
    def __init__(self, raw: bytes, status: int = 200) -> None:
        self.raw = raw
        self.status = status

    def __enter__(self) -> "_RawResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.raw


def _raw(document: object, *, status: int = 200) -> _RawResponse:
    return _RawResponse(
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        status=status,
    )


def _document(
    *,
    model: object = EXACT_MODEL,
    response_id: object = "chatcmpl-audit",
    content: object = None,
    refusal: object = None,
    choices: object = None,
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
    if choices is None:
        choices = [
            {
                "finish_reason": "stop",
                "message": {"content": content, "refusal": refusal},
            }
        ]
    return {
        "id": response_id,
        "model": model,
        "choices": choices,
        "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        "system_fingerprint": "fp-audit",
    }


def _http_error(status: int, retry_after: str | None = None) -> HTTPError:
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return HTTPError("https://invalid.test", status, "synthetic", headers, None)


def _send(opener: object):
    transport = RecoveryLiveOpenAIChatCompletionsTransportV3(
        api_key="synthetic-audit-only",
        opener=opener,
        sleeper=lambda _seconds: None,
    )
    response = transport.send(build_recovery_capability_request_v1())
    return transport, response, transport.attempt_custody[-1]


def _project_import_closure(entrypoint: Path) -> tuple[Path, ...]:
    """Resolve project-local paperworks imports without importing the modules."""

    source_root = _REPOSITORY_ROOT / "src"
    pending = [entrypoint.resolve()]
    observed: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in observed:
            continue
        observed.add(path)
        tree = ast.parse(path.read_text("utf-8"), filename=str(path))
        modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
        for module in modules:
            if not module.startswith("paperworks."):
                continue
            candidate = source_root / (module.replace(".", "/") + ".py")
            if candidate.is_file() and candidate.resolve() not in observed:
                pending.append(candidate.resolve())
    return tuple(sorted(observed))


class ProviderSemanticsIndependentAuditTests(unittest.TestCase):
    def test_response_classification_matrix_is_forensically_coherent(self) -> None:
        malformed = (
            ("invalid_utf8", lambda *_a, **_k: _RawResponse(b"\xff")),
            ("invalid_json", lambda *_a, **_k: _RawResponse(b"{")),
            ("non_object", lambda *_a, **_k: _raw([1, 2, 3])),
            ("bad_envelope", lambda *_a, **_k: _raw({"id": "x", "model": EXACT_MODEL})),
            ("bad_message", lambda *_a, **_k: _raw(_document(choices=[{"finish_reason": "stop", "message": 7}]))),
            ("bad_content", lambda *_a, **_k: _raw(_document(content="not-json"))),
        )
        for name, opener in malformed:
            with self.subTest(name=name):
                _, response, attempt = _send(opener)
                expected = {
                    "provider_contacted": True,
                    "transport_response_received": True,
                    "provider_payload_received": True,
                    "provider_authored_response": True,
                    "response_present": True,
                    "status_code": 200,
                    "outcome": "schema_invalid_response",
                    "retry_eligible": False,
                    "terminal": "completed_schema_invalid_response",
                    "parse_status": "schema_invalid_response",
                }
                observed = {
                    "provider_contacted": response.provider_contacted,
                    "transport_response_received": response.transport_response_received,
                    "provider_payload_received": response.provider_payload_received,
                    "provider_authored_response": response.provider_authored_response,
                    "response_present": response.response_present,
                    "status_code": response.status_code,
                    "outcome": response.outcome,
                    "retry_eligible": attempt.retry_eligible,
                    "terminal": terminal_classification_v3(response),
                    "parse_status": logical_parse_status_v3(response),
                }
                self.assertEqual(observed, expected)
                self.assertEqual(attempt.terminal_classification, expected["terminal"])
                if name in {"bad_message", "bad_content"}:
                    self.assertEqual(response.model, EXACT_MODEL)
                    self.assertEqual(response.response_id, "chatcmpl-audit")
                    self.assertEqual(response.finish_reason, "stop")
                    self.assertEqual(dict(response.token_usage or {}), {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5})
                    self.assertEqual(response.system_fingerprint, "fp-audit")
                elif name in {"invalid_utf8", "invalid_json", "non_object"}:
                    self.assertIsNone(response.model)
                    self.assertIsNone(response.response_id)

        failure_cases = (
            (400, "http_400", False),
            (401, "http_401", False),
            (403, "http_403", False),
            (429, "http_429", True),
            (500, "http_5xx", True),
        )
        for status, outcome, retryable in failure_cases:
            with self.subTest(status=status):
                _, response, attempt = _send(
                    lambda *_a, _status=status, **_k: (_ for _ in ()).throw(
                        _http_error(_status, "7" if _status == 429 else None)
                    )
                )
                self.assertTrue(response.provider_contacted)
                self.assertTrue(response.transport_response_received)
                self.assertFalse(response.provider_payload_received)
                self.assertFalse(response.provider_authored_response)
                self.assertFalse(response.response_present)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.outcome, outcome)
                self.assertEqual(attempt.retry_eligible, retryable)
                self.assertEqual(
                    attempt.terminal_classification,
                    "retryable_transport_failure"
                    if retryable
                    else "completed_nonretryable_transport_failure",
                )
                self.assertEqual(logical_parse_status_v3(response), "transport_failure")

        for name, failure, outcome in (
            ("timeout", TimeoutError("synthetic"), "timeout_before_response"),
            ("reset", ConnectionResetError("synthetic"), "connection_reset"),
            ("connection", URLError("synthetic"), "connection_failure"),
        ):
            with self.subTest(name=name):
                _, response, attempt = _send(
                    lambda *_a, _failure=failure, **_k: (_ for _ in ()).throw(_failure)
                )
                self.assertTrue(response.provider_contacted)
                self.assertFalse(response.transport_response_received)
                self.assertFalse(response.response_present)
                self.assertFalse(response.provider_authored_response)
                self.assertEqual(response.outcome, outcome)
                self.assertTrue(attempt.retry_eligible)

    def test_success_refusal_and_model_mismatch_preserve_observed_metadata(self) -> None:
        for name, document, outcome, terminal in (
            (
                "success",
                _document(),
                "successful_response",
                "completed_provider_response",
            ),
            (
                "refusal",
                _document(refusal="synthetic refusal"),
                "provider_refusal",
                "completed_provider_refusal",
            ),
            (
                "mismatch",
                _document(model="gpt-unexpected-snapshot", response_id="chatcmpl-unexpected"),
                "model_identity_integrity",
                "completed_model_identity_mismatch",
            ),
        ):
            with self.subTest(name=name):
                transport, response, attempt = _send(lambda *_a, _d=document, **_k: _raw(_d))
                self.assertTrue(response.response_present)
                self.assertTrue(response.provider_authored_response)
                self.assertEqual(response.outcome, outcome)
                self.assertEqual(attempt.terminal_classification, terminal)
                self.assertFalse(attempt.retry_eligible)
                self.assertEqual(response.finish_reason, "stop")
                self.assertEqual(dict(response.token_usage or {}), {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5})
                self.assertEqual(response.system_fingerprint, "fp-audit")
                self.assertEqual(transport.calls, 1)
                if name == "mismatch":
                    self.assertEqual(response.model, "gpt-unexpected-snapshot")
                    self.assertEqual(response.response_id, "chatcmpl-unexpected")

    def test_malformed_http200_survives_capability_custody_and_failure_receipt(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            transport, response, _ = _send(
                lambda *_a, **_k: _raw(_document(content="not-json"))
            )
            execution = RecoveryCapabilityExecutionV3(
                request=build_recovery_capability_request_v1(),
                response=response,
                gate=evaluate_recovery_capability_response_v1(response),
                transport_attempts=1,
                transport_retries=0,
            )
            custody = TransactionalHashChainCustodyV3(
                root / "capability",
                ledger_kind="recovery_capability",
                allowed_logical_call_kind="recovery_capability",
            )
            binding = freeze_capability_custody_v3(
                execution=execution, transport=transport, custody=custody
            )
            payload = custody.records[-1]["payload"]
            self.assertEqual(payload["terminal_slot_state"], "completed_schema_invalid_response")
            self.assertEqual(payload["parse_status"], "schema_invalid_response")
            self.assertTrue(payload["response_present"])
            self.assertTrue(payload["provider_authored_response"])
            self.assertEqual(payload["returned_model"], EXACT_MODEL)
            self.assertEqual(payload["response_id"], "chatcmpl-audit")
            receipt = build_recovery_capability_receipt_v3(
                execution=execution,
                execution_commit="2" * 40,
                source_manifest_hash=_SHA,
                r2_authorization_hash="3" * 64,
                custody_binding=binding,
            )
            self.assertEqual(receipt["terminal_slot_state"], "completed_schema_invalid_response")
            self.assertTrue(receipt["response_present"])
            context = _failure_context_from_state(
                execution_commit="2" * 40,
                source_manifest_hash=_SHA,
                authorization_hash="3" * 64,
                configuration_fingerprint="4" * 64,
                capability_gate_status="BLOCK",
                capability_custody=custody,
                scientific_custody=None,
                proposal_records=(),
                outcome_records=(),
                direct_records=(),
                transport_attempts=0,
                integrity_guard=SimpleNamespace(blocked=False),
            )
            failure = write_terminal_failure_receipt_v3(
                destination=root / "failure.json",
                failure_stage="recovery_capability_gate",
                failure=RuntimeError("synthetic"),
                context=context,
            )
            self.assertEqual(failure["actual_returned_model"], EXACT_MODEL)
            self.assertEqual(failure["actual_response_id"], "chatcmpl-audit")
            self.assertEqual(failure["terminal_slot_state"], "completed_schema_invalid_response")

    def test_scientific_custody_preserves_malformed_and_mismatch_terminal_observations(self) -> None:
        for name, document, terminal, model, response_id, caller_parse in (
            ("malformed", _document(content="not-json"), "completed_schema_invalid_response", EXACT_MODEL, "chatcmpl-audit", "incomplete_response"),
            ("mismatch", _document(model="gpt-unexpected", response_id="chatcmpl-unexpected"), "completed_model_identity_mismatch", "gpt-unexpected", "chatcmpl-unexpected", "valid_structured"),
        ):
            with self.subTest(name=name), TemporaryDirectory() as raw:
                transport, response, _ = _send(lambda *_a, _d=document, **_k: _raw(_d))
                custody = TransactionalHashChainCustodyV3(
                    Path(raw) / "scientific",
                    ledger_kind="scientific_provider",
                    allowed_logical_call_kind="scientific",
                )
                ledger = TransactionalScientificProviderLedgerV3(
                    custody, attempt_supplier=lambda: transport.attempt_custody
                )
                slot = ProviderCallSlotV1(0, _SHA, "T1", 1, True)
                with self.assertRaises(TASK039E3RecoveryScientificAbortV3Error):
                    ledger.append(
                        slot=slot,
                        request_hash=build_recovery_capability_request_v1().request_hash,
                        response_present=response.response_present,
                        provider_response_metadata={"outcome": response.outcome},
                        transport_attempts=(object(),),
                        parse_status=caller_parse,
                        proposal_core_hash=None,
                        terminal_slot_state="transport_exhausted",
                    )
                payload = custody.records[-1]["payload"]
                self.assertTrue(payload["response_present"])
                self.assertTrue(payload["provider_authored_response"])
                self.assertEqual(payload["terminal_slot_state"], terminal)
                self.assertEqual(payload["provider_response_metadata"]["model"], model)
                self.assertEqual(payload["provider_response_metadata"]["response_id"], response_id)
                self.assertNotEqual(payload["parse_status"], "transport_failure")
                capability_custody = TransactionalHashChainCustodyV3(
                    Path(raw) / "capability",
                    ledger_kind="recovery_capability",
                    allowed_logical_call_kind="recovery_capability",
                )
                context = _failure_context_from_state(
                    execution_commit="2" * 40,
                    source_manifest_hash=_SHA,
                    authorization_hash="3" * 64,
                    configuration_fingerprint="4" * 64,
                    capability_gate_status="PASS",
                    capability_custody=capability_custody,
                    scientific_custody=custody,
                    proposal_records=(),
                    outcome_records=(),
                    direct_records=(),
                    transport_attempts=1,
                    integrity_guard=SimpleNamespace(blocked=False),
                )
                failure = write_terminal_failure_receipt_v3(
                    destination=Path(raw) / "failure.json",
                    failure_stage="scientific_provider_slot",
                    failure=RuntimeError("synthetic"),
                    context=context,
                )
                self.assertEqual(failure["actual_returned_model"], model)
                self.assertEqual(failure["actual_response_id"], response_id)
                self.assertEqual(failure["terminal_slot_state"], terminal)

    def test_typed_accounting_never_cancels_capability_and_scientific_families(self) -> None:
        scientific = SimpleNamespace(
            to_dict=lambda: {
                "scientific_logical_calls": 252,
                "t1_logical_calls": 42,
                "t1b_logical_calls": 126,
                "t2_logical_calls": 42,
                "direct_number_logical_calls": 42,
                "scientific_concurrency": 1,
                "scientific_generation_retries": 0,
            }
        )
        for attempts in (1, 2, 3):
            with self.subTest(attempts=attempts):
                accounting = build_typed_accounting_v3(
                    capability_attempts=attempts,
                    scientific_result=scientific,
                    scientific_transport_attempts=255,
                )
                self.assertEqual(accounting["historical_capability_probes"], 1)
                self.assertEqual(accounting["current_recovery_capability_logical_calls"], 1)
                self.assertEqual(accounting["current_recovery_capability_transport_attempts"], attempts)
                self.assertEqual(accounting["current_recovery_capability_transport_retries"], attempts - 1)
                self.assertEqual(accounting["cumulative_real_provider_capability_probes"], 2)
                self.assertEqual(accounting["scientific_logical_calls"], 252)
                self.assertEqual(accounting["scientific_transport_attempts"], 255)
                self.assertEqual(accounting["scientific_transport_retries"], 3)
                self.assertEqual(accounting["local_compatibility_slots"], 0)

    def test_recovery_probe_is_one_logical_call_with_at_most_three_attempts(self) -> None:
        events = [_http_error(429), TimeoutError("synthetic"), _raw(_document())]

        def opener(*_args: object, **_kwargs: object):
            event = events.pop(0)
            if isinstance(event, BaseException):
                raise event
            return event

        transport = RecoveryLiveOpenAIChatCompletionsTransportV3(
            api_key="synthetic-audit-only", opener=opener, sleeper=lambda _s: None
        )
        execution = execute_recovery_capability_probe_v3(transport)  # structural protocol only
        self.assertEqual(execution.transport_attempts, 3)
        self.assertEqual(execution.transport_retries, 2)
        self.assertEqual(transport.calls, 3)
        self.assertEqual(len(transport.attempt_custody), 3)
        self.assertEqual(execution.gate.gate_status, "PASS")

    def test_b1_b2_b3_active_closure_regression(self) -> None:
        closure = _project_import_closure(
            _REPOSITORY_ROOT / "scripts" / "run_task039e3_recovery_execution_v3.py"
        )
        names = {path.name for path in closure}
        combined = "\n".join(path.read_text("utf-8") for path in closure)
        self.assertNotIn("task039e3_recovery_execution_v1.py", names)
        self.assertNotIn("RecoveryScientificCompatibilityTransportV1", combined)
        self.assertIn("task039e3_recovery_science_v2.py", names)
        self.assertIn("task039e3_recovery_execution_v3.py", names)
        self.assertNotIn("local compatibility", combined.lower())
        self.assertNotIn("task039e3_recovery_execution_v1", combined)


if __name__ == "__main__":
    unittest.main()
