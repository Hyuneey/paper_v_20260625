"""Offline validation for reuse of the durable R2 capability PASS.

This module has no credential, transport, environment, or private-path loader.
Callers must supply the already-read private receipt and a disk-authoritative
transactional-ledger reconstruction.  Reuse is an immutable authority check;
it never creates another capability call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from paperworks.v6.common import require_sha256, stable_hash_v1
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalLedgerReconstructionV3,
)


CAPABILITY_RECEIPT_HASH = (
    "9ee4637da31b585a34eda4bad3b3be1dfa5597396ce1e78ef0564fa53da2b428"
)
CAPABILITY_PROVIDER_LEDGER_HASH = (
    "d6531d990bd70d89d114094f003dd9387e4df2db9cf9c2fc14bb5cf790818294"
)
CAPABILITY_PROVIDER_LEDGER_HEAD_HASH = (
    "e0b449ca96ffbf229954c059780baf8fb115aa79fc5d65802dd19e3a54120471"
)
R1D2_EXECUTION_COMMIT = "2653f2b7349a049f9ca4828d736dfea9462c4748"
COMPLETE_SOURCE_MANIFEST_HASH = (
    "e8f236a8238bad744eced3009e2000bab9597094cab04446d920df0a0ddf9283"
)
CONSUMED_R2_AUTHORIZATION_HASH = (
    "2133f54651447258c00546d6293600f95bbea86500a7ced7ca9bbe820ef373cc"
)
EXACT_MODEL = "gpt-5.4-2026-03-05"
CAPABILITY_RESPONSE_ID = "chatcmpl-EBymHEjpmxFMggRlkPRcAH7HW4tAu"

CAPABILITY_RECEIPT_ARTIFACT_TYPE = "task039e3_recovery_capability_receipt_v3"
CAPABILITY_RECEIPT_TASK_ID = "TASK-039E3-R2_RECOVERY_EXECUTION"
CAPABILITY_PASS_STATUS = "passed_task039e3_recovery_capability_gate"
CAPABILITY_TERMINAL_STATE = "completed_provider_response"


class TASK039E3R2RCapabilityReuseError(ValueError):
    """A historical capability PASS is not safe to reuse."""


def _fail(message: str) -> None:
    raise TASK039E3R2RCapabilityReuseError(message)


def _require_exact(document: Mapping[str, Any], key: str, expected: object) -> None:
    value = document.get(key)
    if type(value) is not type(expected) or value != expected:
        _fail(f"capability receipt {key} differs")


def _verify_self_hash(document: Mapping[str, Any]) -> str:
    claimed = document.get("artifact_hash")
    try:
        artifact_hash = require_sha256(claimed, "capability receipt artifact_hash")  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TASK039E3R2RCapabilityReuseError(
            "capability receipt artifact_hash is invalid"
        ) from exc
    payload = dict(document)
    payload.pop("artifact_hash", None)
    if stable_hash_v1(payload) != artifact_hash:
        _fail("capability receipt self-hash differs")
    if artifact_hash != CAPABILITY_RECEIPT_HASH:
        _fail("capability receipt authority hash differs")
    return artifact_hash


@dataclass(frozen=True)
class CapabilityLedgerObservationR2RV1:
    """Sanitized result of disk-authoritative capability reconstruction."""

    ledger_kind: str
    ledger_hash: str
    head_record_hash: str | None
    authoritative_record_count: int
    orphan_record_hashes: tuple[str, ...]
    pending_files: tuple[str, ...]
    reachable_record: Mapping[str, Any]


@dataclass(frozen=True)
class ValidatedCapabilityReuseR2RV1:
    receipt_hash: str
    provider_ledger_hash: str
    provider_ledger_head_hash: str
    provider_record_hash: str
    cumulative_real_provider_capability_probes: int = 2
    additional_capability_probes: int = 0
    capability_transport_reachable: bool = False


def capability_observation_from_reconstruction_v1(
    reconstruction: TransactionalLedgerReconstructionV3,
) -> CapabilityLedgerObservationR2RV1:
    """Adapt an already verified disk reconstruction without reading a path."""

    if reconstruction.authoritative_record_count != 1:
        _fail("capability ledger must contain exactly one authoritative record")
    return CapabilityLedgerObservationR2RV1(
        ledger_kind=reconstruction.ledger_kind,
        ledger_hash=reconstruction.ledger_hash,
        head_record_hash=reconstruction.head_record_hash,
        authoritative_record_count=reconstruction.authoritative_record_count,
        orphan_record_hashes=reconstruction.orphan_record_hashes,
        pending_files=reconstruction.pending_files,
        reachable_record=reconstruction.reachable_records[0],
    )


def _validate_gate(gate: object) -> None:
    if not isinstance(gate, Mapping):
        _fail("capability receipt gate is absent")
    expected = {
        "gate_status": "PASS",
        "failure_codes": [],
        "provider_model_identity_source": "provider_response_metadata_only",
        "structured_output_authority_source": (
            "observed_strict_schema_parse_and_validation"
        ),
        "transport_response_succeeded": True,
        "model_identity_match": True,
        "refusal_absent": True,
        "structured_parse_pass": True,
        "schema_validation_pass": True,
        "fixture_id_match": True,
        "capability_token_match": True,
    }
    for key, value in expected.items():
        if gate.get(key) != value:
            _fail(f"capability receipt gate {key} differs")
    payload = gate.get("parsed_payload")
    if payload != {
        "fixture_id": "SYNTHETIC_CAPABILITY_CHECK",
        "capability_token": "TASK039E3_STRICT_JSON_SCHEMA_V1",
    }:
        _fail("capability receipt validated fixture differs")


def _validate_attempt(attempt: object) -> None:
    if not isinstance(attempt, Mapping):
        _fail("capability attempt custody is absent")
    expected = {
        "sequence_index": 0,
        "attempt_number": 1,
        "request_hash": (
            "90ba8e7cf83a59573bf6776de65015aa30c1c5037898eef1c38c3e29feec57fd"
        ),
        "response_origin": "provider",
        "transport_response_received": True,
        "provider_payload_received": True,
        "provider_contacted": True,
        "provider_authored_response": True,
        "response_present": True,
        "structured_payload_valid": True,
        "outcome": "successful_response",
        "terminal_classification": CAPABILITY_TERMINAL_STATE,
        "status_code": 200,
        "returned_model": EXACT_MODEL,
        "response_id": CAPABILITY_RESPONSE_ID,
        "finish_reason": "stop",
        "retry_eligible": False,
        "actual_retry_delay_before_attempt_seconds": None,
        "retry_after_seconds_observed": None,
    }
    for key, value in expected.items():
        if attempt.get(key) != value:
            _fail(f"capability attempt {key} differs")
    claimed = attempt.get("record_hash")
    if not isinstance(claimed, str):
        _fail("capability attempt record hash is absent")
    payload = dict(attempt)
    payload.pop("record_hash", None)
    if stable_hash_v1(payload) != claimed:
        _fail("capability attempt record hash differs")


def _validate_record(observation: CapabilityLedgerObservationR2RV1) -> str:
    if observation.ledger_kind != "recovery_capability":
        _fail("capability ledger kind differs")
    if observation.ledger_hash != CAPABILITY_PROVIDER_LEDGER_HASH:
        _fail("capability provider ledger hash differs")
    if observation.head_record_hash != CAPABILITY_PROVIDER_LEDGER_HEAD_HASH:
        _fail("capability provider ledger head differs")
    if observation.authoritative_record_count != 1:
        _fail("capability ledger must contain exactly one authoritative record")
    if observation.orphan_record_hashes:
        _fail("capability ledger contains orphan records")
    if observation.pending_files:
        _fail("capability ledger contains pending files")
    record = observation.reachable_record
    if record.get("record_hash") != CAPABILITY_PROVIDER_LEDGER_HEAD_HASH:
        _fail("capability record hash differs from authoritative head")
    if record.get("sequence_index") != 0 or record.get("previous_record_hash") is not None:
        _fail("capability record chain differs")
    if record.get("ledger_kind") != "recovery_capability":
        _fail("capability record ledger kind differs")
    if record.get("logical_call_kind") != "recovery_capability":
        _fail("capability record logical-call kind differs")
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        _fail("capability record payload is absent")
    expected_payload = {
        "logical_call_kind": "recovery_capability",
        "scientific": False,
        "response_origin": "provider",
        "provider_contacted": True,
        "provider_authored_response": True,
        "transport_response_received": True,
        "provider_payload_received": True,
        "response_present": True,
        "structured_payload_valid": True,
        "returned_model": EXACT_MODEL,
        "response_id": CAPABILITY_RESPONSE_ID,
        "finish_reason": "stop",
        "parse_status": "provider_response_received",
        "terminal_slot_state": CAPABILITY_TERMINAL_STATE,
        "gate_status": "PASS",
    }
    for key, value in expected_payload.items():
        if payload.get(key) != value:
            _fail(f"capability record payload {key} differs")
    attempts = payload.get("transport_attempts")
    if not isinstance(attempts, list) or len(attempts) != 1:
        _fail("capability record attempt count differs")
    _validate_attempt(attempts[0])
    return str(record["record_hash"])


def validate_capability_reuse_v1(
    *,
    private_capability_receipt: Mapping[str, Any],
    ledger_observation: CapabilityLedgerObservationR2RV1,
) -> ValidatedCapabilityReuseR2RV1:
    """Validate exact PASS custody without creating a capability transport."""

    receipt_hash = _verify_self_hash(private_capability_receipt)
    expected = {
        "schema_version": "3.0.0",
        "artifact_type": CAPABILITY_RECEIPT_ARTIFACT_TYPE,
        "task_id": CAPABILITY_RECEIPT_TASK_ID,
        "status": CAPABILITY_PASS_STATUS,
        "gate_status": "PASS",
        "execution_commit": R1D2_EXECUTION_COMMIT,
        "source_manifest_hash": COMPLETE_SOURCE_MANIFEST_HASH,
        "r2_authorization_hash": CONSUMED_R2_AUTHORIZATION_HASH,
        "historical_capability_probes": 1,
        "current_recovery_capability_logical_calls": 1,
        "cumulative_real_provider_capability_probes": 2,
        "transport_attempts": 1,
        "transport_retries": 0,
        "response_present": True,
        "provider_authored_response": True,
        "returned_model": EXACT_MODEL,
        "response_id": CAPABILITY_RESPONSE_ID,
        "finish_reason": "stop",
        "terminal_slot_state": CAPABILITY_TERMINAL_STATE,
        "capability_provider_ledger_hash": CAPABILITY_PROVIDER_LEDGER_HASH,
        "capability_provider_ledger_head_hash": CAPABILITY_PROVIDER_LEDGER_HEAD_HASH,
        "local_compatibility_slots": 0,
        "credential_persisted": False,
        "authorization_header_persisted": False,
    }
    for key, value in expected.items():
        _require_exact(private_capability_receipt, key, value)
    _validate_gate(private_capability_receipt.get("gate"))
    record_hash = _validate_record(ledger_observation)
    return ValidatedCapabilityReuseR2RV1(
        receipt_hash=receipt_hash,
        provider_ledger_hash=ledger_observation.ledger_hash,
        provider_ledger_head_hash=str(ledger_observation.head_record_hash),
        provider_record_hash=record_hash,
    )


__all__ = [
    "CAPABILITY_PROVIDER_LEDGER_HASH",
    "CAPABILITY_PROVIDER_LEDGER_HEAD_HASH",
    "CAPABILITY_RECEIPT_HASH",
    "CapabilityLedgerObservationR2RV1",
    "TASK039E3R2RCapabilityReuseError",
    "ValidatedCapabilityReuseR2RV1",
    "capability_observation_from_reconstruction_v1",
    "validate_capability_reuse_v1",
]
