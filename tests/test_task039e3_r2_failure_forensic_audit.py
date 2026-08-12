"""Offline, read-only oracles for the R2 guarded-failure forensic audit.

The helpers in this module deliberately accept caller-supplied paths.  Tests
use only temporary synthetic custody and never construct a provider transport,
load a credential, or invoke a live runner.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from typing import Any, Mapping, Sequence

from paperworks.v6.common import stable_hash_v1, thaw_json
from paperworks.v6.task039e2_execution_configuration_v1 import (
    API_BASE_URL,
    API_ENDPOINT,
    EXACT_MODEL,
    MAIN_PROVIDER_SCHEMA_V1,
)
from paperworks.v6.task039e3_execution_prep_v1 import (
    MAIN_PROMPT_HASH,
    FrozenProviderRequestV1,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalLedgerReconstructionV3,
    TransactionalHashChainCustodyV3,
    reconstruct_transactional_ledger_v3,
)


class ForensicAuditError(ValueError):
    """Raised when immutable forensic inputs do not reconcile."""


RETRYABLE_OUTCOMES = frozenset(
    {
        "connection_failure",
        "connection_reset",
        "timeout_before_response",
        "http_429",
        "http_5xx",
    }
)

SCIENTIFIC_ATTEMPT_FIELDS = (
    "request_hash",
    "outcome",
    "status_code",
    "transport_response_received",
    "provider_payload_received",
    "provider_contacted",
    "provider_authored_response",
    "response_present",
    "structured_payload_valid",
    "terminal_classification",
    "retry_eligible",
    "actual_retry_delay_before_attempt_seconds",
    "retry_after_seconds_observed",
    "returned_model",
    "response_id",
    "finish_reason",
    "token_usage",
    "system_fingerprint",
    "provider_payload_hash",
)


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ForensicAuditError(f"JSON object required: {path.name}")
    return value


def verify_self_hashed_object(path: Path) -> dict[str, Any]:
    document = _read_object(path)
    field = "artifact_hash" if "artifact_hash" in document else "self_hash"
    supplied = document.get(field)
    if not isinstance(supplied, str) or stable_hash_v1(
        {key: value for key, value in document.items() if key != field}
    ) != supplied:
        raise ForensicAuditError(f"self-hash differs: {path.name}")
    return document


def reconstruct_provider_custody(
    root: Path, *, ledger_kind: str
) -> TransactionalLedgerReconstructionV3:
    """Use disk-authoritative HEAD semantics without opening a writer."""

    return reconstruct_transactional_ledger_v3(root, ledger_kind=ledger_kind)


def sole_reachable_payload(
    reconstruction: TransactionalLedgerReconstructionV3,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    if reconstruction.authoritative_record_count != 1:
        raise ForensicAuditError("exactly one authoritative record is required")
    if reconstruction.orphan_records or reconstruction.pending_files:
        raise ForensicAuditError("orphan or pending custody is not accepted")
    record = reconstruction.reachable_records[0]
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        raise ForensicAuditError("reachable record payload is unavailable")
    return record, payload


def sanitized_attempt_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    attempts = payload.get("transport_attempts")
    if not isinstance(attempts, list) or len(attempts) != 1:
        raise ForensicAuditError("exactly one transport attempt is required")
    attempt = attempts[0]
    if not isinstance(attempt, Mapping):
        raise ForensicAuditError("attempt custody object is required")
    result = {field: attempt.get(field) for field in SCIENTIFIC_ATTEMPT_FIELDS}
    if not isinstance(result["request_hash"], str):
        raise ForensicAuditError("request hash is unavailable")
    return result


def assert_nonretryable_terminal_consistency(attempt: Mapping[str, Any]) -> None:
    outcome = attempt.get("outcome")
    if outcome in RETRYABLE_OUTCOMES or attempt.get("retry_eligible") is not False:
        raise ForensicAuditError("retryable event was classified nonretryable")
    expected = {
        "response_present": False,
        "terminal_classification": "completed_nonretryable_transport_failure",
    }
    if any(attempt.get(key) != value for key, value in expected.items()):
        raise ForensicAuditError("nonretryable terminal semantics differ")


def reconcile_public_private_failure(
    *,
    public: Mapping[str, Any],
    capability: TransactionalLedgerReconstructionV3,
    scientific: TransactionalLedgerReconstructionV3,
    proposal_count: int,
    outcome_count: int,
    direct_count: int,
) -> dict[str, Any]:
    capability_record, capability_payload = sole_reachable_payload(capability)
    scientific_record, scientific_payload = sole_reachable_payload(scientific)
    attempt = sanitized_attempt_metadata(scientific_payload)
    slot = scientific_payload.get("slot")
    if not isinstance(slot, Mapping):
        raise ForensicAuditError("scientific slot is unavailable")
    expected = {
        "status": "failed_task039e3_r2_recovery_execution",
        "capability_gate_status": capability_payload.get("gate_status"),
        "capability_provider_ledger_head_hash": capability.head_record_hash,
        "scientific_provider_ledger_head_hash": scientific.head_record_hash,
        "last_completed_scientific_slot": dict(slot),
        "completed_scientific_logical_calls": 1,
        "scientific_transport_attempts": 1,
        "proposal_committed_count": proposal_count,
        "outcome_committed_count": outcome_count,
        "direct_number_committed_count": direct_count,
        "actual_returned_model": attempt.get("returned_model"),
        "actual_response_id": attempt.get("response_id"),
        "terminal_slot_state": scientific_payload.get("terminal_slot_state"),
    }
    for key, value in expected.items():
        if public.get(key) != value:
            raise ForensicAuditError(f"public/private disagreement: {key}")
    return {
        "capability_record_hash": capability_record["record_hash"],
        "scientific_record_hash": scientific_record["record_hash"],
        "capability_payload": capability_payload,
        "scientific_payload": scientific_payload,
        "attempt": attempt,
    }


def read_jsonl_metadata(
    path: Path, *, allowed_fields: Sequence[str]
) -> tuple[dict[str, Any], ...]:
    """Read records once and return only an explicit metadata projection."""

    projected: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            value = json.loads(line)
            if not isinstance(value, Mapping):
                raise ForensicAuditError(f"JSONL object required: {path.name}")
            projected.append({field: value.get(field) for field in allowed_fields})
    return tuple(projected)


def validate_frozen_t1_request(request: FrozenProviderRequestV1) -> dict[str, Any]:
    body = dict(request.request_body)
    expected = {
        "model": EXACT_MODEL,
        "reasoning_effort": "none",
        "temperature": 0.7,
        "top_p": 1.0,
        "max_completion_tokens": 1024,
        "n": 1,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "stream": False,
        "store": False,
        "tools": (),
    }
    if request.endpoint != f"{API_BASE_URL}{API_ENDPOINT}":
        raise ForensicAuditError("endpoint differs")
    if request.purpose != "main_initial":
        raise ForensicAuditError("failed request is not initial T1")
    if any(body.get(key) != value for key, value in expected.items()):
        raise ForensicAuditError("frozen sampling contract differs")
    if request.provider_schema_hash != stable_hash_v1(MAIN_PROVIDER_SCHEMA_V1):
        raise ForensicAuditError("main provider schema hash differs")
    json.dumps(
        thaw_json(request.request_body),
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "request_hash": request.request_hash,
        "endpoint": request.endpoint,
        "model": body["model"],
        "prompt_hash": MAIN_PROMPT_HASH,
        "schema_hash": request.provider_schema_hash,
        "request_field_names": sorted(body),
        "request_matches_frozen_protocol": True,
        "request_serializes_as_valid_json": True,
    }


def request_hash_matches_custody(
    request: FrozenProviderRequestV1, custody_request_hash: str
) -> bool:
    return request.request_hash == custody_request_hash


def _attempt(*, outcome: str = "http_400", status: int = 400) -> dict[str, Any]:
    return {
        "request_hash": "a" * 64,
        "outcome": outcome,
        "status_code": status,
        "transport_response_received": True,
        "provider_payload_received": False,
        "provider_contacted": True,
        "provider_authored_response": False,
        "response_present": False,
        "structured_payload_valid": False,
        "terminal_classification": "completed_nonretryable_transport_failure",
        "retry_eligible": False,
        "actual_retry_delay_before_attempt_seconds": None,
        "retry_after_seconds_observed": None,
        "returned_model": None,
        "response_id": None,
        "finish_reason": None,
        "token_usage": None,
        "system_fingerprint": None,
        "provider_payload_hash": None,
    }


def _slot(*, scientific: bool) -> dict[str, Any]:
    return {
        "artifact_type": "scientific_provider_call_slot_v1" if scientific else "provider_call_slot_v1",
        "relation_schedule_index": 0 if scientific else None,
        "relation_binding_hash": "b" * 64,
        "arm": "T1" if scientific else "CAPABILITY",
        "arm_local_call_number": 1,
        "scientific": scientific,
        "schedule_hash": "c" * 64,
    }


class FailureForensicAuditOracleTests(unittest.TestCase):
    def _ledger(
        self, parent: Path, kind: str, logical_kind: str, payload: Mapping[str, Any]
    ) -> Path:
        root = parent / kind
        ledger = TransactionalHashChainCustodyV3(
            root, ledger_kind=kind, allowed_logical_call_kind=logical_kind
        )
        ledger.append(
            logical_call_kind=logical_kind, slot_identity="d" * 64, payload=payload
        )
        return root

    def test_head_authoritative_reconstruction_and_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            cap_payload = {
                "gate_status": "PASS",
                "logical_call_kind": "recovery_capability",
                "transport_attempts": [_attempt(outcome="successful_response", status=200)],
            }
            sci_payload = {
                "logical_call_kind": "scientific",
                "slot": _slot(scientific=True),
                "request_hash": "a" * 64,
                "transport_attempts": [_attempt()],
                "terminal_slot_state": "completed_nonretryable_transport_failure",
            }
            cap = reconstruct_provider_custody(
                self._ledger(
                    parent, "recovery_capability", "recovery_capability", cap_payload
                ),
                ledger_kind="recovery_capability",
            )
            sci = reconstruct_provider_custody(
                self._ledger(parent, "scientific_provider", "scientific", sci_payload),
                ledger_kind="scientific_provider",
            )
            public = {
                "status": "failed_task039e3_r2_recovery_execution",
                "capability_gate_status": "PASS",
                "capability_provider_ledger_head_hash": cap.head_record_hash,
                "scientific_provider_ledger_head_hash": sci.head_record_hash,
                "last_completed_scientific_slot": _slot(scientific=True),
                "completed_scientific_logical_calls": 1,
                "scientific_transport_attempts": 1,
                "proposal_committed_count": 1,
                "outcome_committed_count": 1,
                "direct_number_committed_count": 0,
                "actual_returned_model": None,
                "actual_response_id": None,
                "terminal_slot_state": "completed_nonretryable_transport_failure",
            }
            result = reconcile_public_private_failure(
                public=public, capability=cap, scientific=sci,
                proposal_count=1, outcome_count=1, direct_count=0,
            )
            self.assertEqual(result["attempt"]["outcome"], "http_400")
            assert_nonretryable_terminal_consistency(result["attempt"])

    def test_retryable_event_cannot_be_reported_nonretryable(self) -> None:
        attempt = _attempt(outcome="http_429", status=429)
        with self.assertRaisesRegex(ForensicAuditError, "retryable"):
            assert_nonretryable_terminal_consistency(attempt)

    def test_public_private_disagreement_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            cap = reconstruct_provider_custody(
                self._ledger(
                    parent, "recovery_capability", "recovery_capability",
                    {"gate_status": "PASS", "transport_attempts": [_attempt()]},
                ), ledger_kind="recovery_capability",
            )
            sci = reconstruct_provider_custody(
                self._ledger(
                    parent, "scientific_provider", "scientific", {
                        "slot": _slot(scientific=True),
                        "transport_attempts": [_attempt()],
                        "terminal_slot_state": "completed_nonretryable_transport_failure",
                    },
                ), ledger_kind="scientific_provider",
            )
            with self.assertRaisesRegex(ForensicAuditError, "disagreement"):
                reconcile_public_private_failure(
                    public={"status": "wrong"}, capability=cap, scientific=sci,
                    proposal_count=1, outcome_count=1, direct_count=0,
                )

    def test_jsonl_projection_drops_private_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "working.jsonl"
            path.write_text(
                json.dumps({"arm": "T0", "record_hash": "e" * 64, "private": "hidden"}) + "\n",
                encoding="utf-8",
            )
            projected = read_jsonl_metadata(path, allowed_fields=("arm", "record_hash"))
            self.assertEqual(set(projected[0]), {"arm", "record_hash"})
            self.assertNotIn("private", projected[0])

    def test_request_hash_comparison_is_exact(self) -> None:
        request = FrozenProviderRequestV1(
            purpose="main_initial",
            request_body={
                "model": EXACT_MODEL, "reasoning_effort": "none", "temperature": 0.7,
                "top_p": 1.0, "max_completion_tokens": 1024, "n": 1,
                "presence_penalty": 0, "frequency_penalty": 0, "stream": False,
                "store": False, "tools": [], "messages": [{"role": "user", "content": "synthetic"}],
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "provider_proposal_core_v1", "strict": True,
                    "schema": MAIN_PROVIDER_SCHEMA_V1,
                }},
            },
            model_visible_content_hash=hashlib.sha256(b"synthetic").hexdigest(),
            provider_schema_hash=stable_hash_v1(MAIN_PROVIDER_SCHEMA_V1),
            schema_name="provider_proposal_core_v1",
        )
        contract = validate_frozen_t1_request(request)
        self.assertTrue(contract["request_matches_frozen_protocol"])
        self.assertTrue(request_hash_matches_custody(request, request.request_hash))
        self.assertFalse(request_hash_matches_custody(request, "f" * 64))


if __name__ == "__main__":
    unittest.main()
