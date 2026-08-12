"""Active TASK-039E3 recovery V2 execution coordinator.

This additive R1C path executes one corrected capability probe, freezes its
provider custody, and then starts the frozen scientific arms directly.  It has
no legacy compatibility acknowledgement and keeps capability and scientific
provider custody in distinct typed ledgers.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    FrozenProviderRequestV1,
    MockProviderResponseV1,
    ProviderCallSlotV1,
)
from paperworks.v6.task039e3_recovery_authorization_v2 import (
    GitExecutionStateV2,
    HISTORICAL_CAPABILITY_RECEIPT_HASH,
    HISTORICAL_PROVIDER_LEDGER_HEAD_HASH,
    PriorAuthorityStateV2,
    R0_BUNDLE_HASH,
    R0_COMMIT,
    R1A_COMMIT,
    R1A_TIMEOUT_AUTHORITY_HASH,
    R1B_AUDIT_COMMIT_B,
    R1B_AUDIT_RECEIPT_HASH,
    R1B_COMMIT_A,
    R1B_COMMIT_B,
    R1B_INDEPENDENT_AUDIT_BUNDLE_HASH,
    RecoveryProbeAccountingV2,
)
from paperworks.v6.task039e3_recovery_capability_v1 import (
    RecoveryCapabilityGateResultV1,
    build_recovery_capability_request_v1,
    evaluate_recovery_capability_response_v1,
)
from paperworks.v6.task039e3_recovery_custody_v2 import (
    RecoveryCapabilityProviderLedgerV2,
    ScientificModelIdentityMismatchAbortV2,
    ScientificProviderLedgerV2,
    TypedProviderAccountingV2,
    build_typed_provider_accounting_v2,
)
from paperworks.v6.task039e3_recovery_live_transport_v2 import (
    RecoveryLiveOpenAIChatCompletionsTransportV2,
)
from paperworks.v6.task039e3_recovery_science_v2 import (
    PostCapabilityAuthorityV2,
    ScientificLedgersV2,
    run_post_capability_scientific_execution_v2,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)
from paperworks.v6.task039e3_scientific_execution_v1 import (
    DurableConstructionOutcomeLedgerV1,
    DurableConstructionProposalLedgerV1,
    DurableDirectNumberLedgerV1,
)


RECOVERY_STATUS_PASS = "passed_task039e3_recovery_capability_gate"
RECOVERY_STATUS_BLOCK = "blocked_task039e3_recovery_capability_gate"
_RETRYABLE = frozenset(
    {"connection_failure", "connection_reset", "timeout_before_response", "http_429", "http_5xx"}
)


class TASK039E3RecoveryExecutionV2Error(ValueError):
    """Fail-closed R1C/R2 execution boundary error."""


@dataclass(frozen=True)
class RecoveryCapabilityExecutionV2:
    request: FrozenProviderRequestV1
    response: MockProviderResponseV1
    gate: RecoveryCapabilityGateResultV1
    accounting: RecoveryProbeAccountingV2
    transport_attempts: int
    transport_retries: int

    def __post_init__(self) -> None:
        if self.accounting.current_recovery_probe_count != 1:
            raise TASK039E3RecoveryExecutionV2Error("one recovery probe is required")
        if self.transport_attempts not in {1, 2, 3}:
            raise TASK039E3RecoveryExecutionV2Error("capability attempt count differs")
        if self.transport_retries != self.transport_attempts - 1:
            raise TASK039E3RecoveryExecutionV2Error("capability retry count differs")


def execute_recovery_capability_probe_v2(
    transport: RecoveryLiveOpenAIChatCompletionsTransportV2,
) -> RecoveryCapabilityExecutionV2:
    """Execute exactly one logical corrected probe with at most three attempts."""

    if transport.calls != 0 or transport.attempt_custody:
        raise TASK039E3RecoveryExecutionV2Error(
            "recovery capability transport must begin unused"
        )
    request = build_recovery_capability_request_v1()
    accounting = RecoveryProbeAccountingV2().allocate_recovery_probe()
    response: MockProviderResponseV1 | None = None
    attempts = 0
    for attempts in range(1, 4):
        response = transport.send(request)
        retryable = not response.response_present and response.outcome in _RETRYABLE
        if response.response_present or not retryable:
            break
    if response is None:
        raise TASK039E3RecoveryExecutionV2Error("capability transport returned no event")
    gate = evaluate_recovery_capability_response_v1(response)
    accounting.with_transport_attempts(attempts)
    return RecoveryCapabilityExecutionV2(
        request=request,
        response=response,
        gate=gate,
        accounting=accounting,
        transport_attempts=attempts,
        transport_retries=attempts - 1,
    )


def freeze_capability_custody_v2(
    *,
    execution: RecoveryCapabilityExecutionV2,
    transport: RecoveryLiveOpenAIChatCompletionsTransportV2,
    ledger: RecoveryCapabilityProviderLedgerV2,
) -> Mapping[str, Any]:
    """Append the sole real capability slot and return a self-hashed binding."""

    slot = ProviderCallSlotV1(
        None,
        stable_hash_v1({"fixture": "SYNTHETIC_CAPABILITY_CHECK"}),
        "CAPABILITY",
        1,
        False,
    )
    record = ledger.append(
        slot=slot,
        request_hash=execution.request.request_hash,
        response_present=execution.response.response_present,
        provider_response_metadata={
            "outcome": execution.response.outcome,
            "status_code": execution.response.status_code,
            "model": execution.response.model,
            "response_id": execution.response.response_id,
            "finish_reason": execution.response.finish_reason,
            "token_usage": dict(execution.response.token_usage) if execution.response.token_usage else None,
        },
        transport_attempts=transport.attempt_custody,
        parse_status="pass" if execution.gate.gate_status == "PASS" else "rejected",
        proposal_core_hash=None,
        terminal_slot_state=(
            "completed_structured"
            if execution.gate.gate_status == "PASS"
            else "completed_model_identity_mismatch"
            if execution.response.outcome == "model_identity_integrity"
            else "completed_invalid_response"
            if execution.response.response_present
            else "transport_exhausted"
        ),
    )
    return {
        "provider_ledger_hash": ledger.ledger_hash,
        "provider_ledger_head_hash": record.record_hash,
        "record_count": 1,
        "durably_frozen": True,
        "system_fingerprint": (
            transport.attempt_custody[-1].system_fingerprint
            if transport.attempt_custody
            else None
        ),
    }


def build_recovery_capability_receipt_v2(
    *,
    execution: RecoveryCapabilityExecutionV2,
    execution_commit: str,
    source_manifest_hash: str,
    r2_authorization_hash: str,
    custody_binding: Mapping[str, Any],
) -> dict[str, Any]:
    response = execution.response
    content = {
        "schema_version": "2.0.0",
        "artifact_type": "task039e3_recovery_capability_gate_receipt_v2",
        "task_id": "TASK-039E3-R2_RECOVERY_EXECUTION",
        "status": RECOVERY_STATUS_PASS if execution.gate.gate_status == "PASS" else RECOVERY_STATUS_BLOCK,
        "execution_commit": execution_commit,
        "source_manifest_hash": source_manifest_hash,
        "r2_authorization_hash": r2_authorization_hash,
        "historical_capability_probe_count": 1,
        "current_recovery_capability_logical_calls": 1,
        "cumulative_real_provider_capability_probes": 2,
        "transport_attempts": execution.transport_attempts,
        "transport_retries": execution.transport_retries,
        "requested_model": "gpt-5.4-2026-03-05",
        "returned_model": response.model,
        "response_id": response.response_id,
        "finish_reason": response.finish_reason,
        "usage": dict(response.token_usage) if response.token_usage else None,
        "system_fingerprint": custody_binding.get("system_fingerprint"),
        "gate": execution.gate.to_dict(),
        "capability_provider_ledger_hash": custody_binding["provider_ledger_hash"],
        "capability_provider_ledger_head_hash": custody_binding["provider_ledger_head_hash"],
        "local_compatibility_slots": 0,
        "credential_persisted": False,
        "authorization_header_persisted": False,
    }
    return finalize_public_artifact_v1(content)


def run_capability_then_science_v2(
    *,
    execution_commit: str,
    source_manifest_hash: str,
    r2_authorization_hash: str,
    e1_private_root: Path,
    recovery_private_root: Path,
    public_cohort: Mapping[str, Any],
    relation_identities: tuple[str, ...],
    transport: RecoveryLiveOpenAIChatCompletionsTransportV2,
    progress: Any = print,
) -> dict[str, Any]:
    """Active V2 state machine; E1 is unreachable until custody and receipt exist."""

    capability_ledger = RecoveryCapabilityProviderLedgerV2(
        recovery_private_root / "recovery_capability_provider_v2.jsonl",
        attempt_supplier=lambda: transport.attempt_custody,
    )
    execution = execute_recovery_capability_probe_v2(transport)
    custody = freeze_capability_custody_v2(
        execution=execution, transport=transport, ledger=capability_ledger
    )
    receipt = build_recovery_capability_receipt_v2(
        execution=execution,
        execution_commit=execution_commit,
        source_manifest_hash=source_manifest_hash,
        r2_authorization_hash=r2_authorization_hash,
        custody_binding=custody,
    )
    receipt_path = recovery_private_root / "recovery_capability_receipt_v2.json"
    write_public_artifact_atomic_v1(receipt_path, receipt)
    if execution.gate.gate_status != "PASS":
        return {
            "status": RECOVERY_STATUS_BLOCK,
            "capability_receipt": receipt,
            "capability_custody": dict(custody),
            "scientific_calls": 0,
            "local_compatibility_slots": 0,
        }

    scientific_root = recovery_private_root / "scientific"
    scientific_root.mkdir(exist_ok=False)
    attempt_start = len(transport.attempt_custody)
    scientific_ledger = ScientificProviderLedgerV2(
        scientific_root / "scientific_provider_v2.jsonl",
        attempt_supplier=lambda: transport.attempt_custody[attempt_start:],
    )
    proposal_ledger = DurableConstructionProposalLedgerV1(scientific_root / "proposals_v2.jsonl")
    outcome_ledger = DurableConstructionOutcomeLedgerV1(scientific_root / "outcomes_v2.jsonl")
    direct_ledger = DurableDirectNumberLedgerV1(scientific_root / "direct_v2.jsonl")
    try:
        scientific = run_post_capability_scientific_execution_v2(
            authority=PostCapabilityAuthorityV2(
                gate_status="PASS",
                capability_custody_frozen=bool(custody["durably_frozen"]),
                capability_receipt_durable=receipt_path.is_file(),
                capability_receipt_hash=receipt["artifact_hash"],
            ),
            e1_private_root=e1_private_root,
            public_cohort=public_cohort,
            relation_identities=relation_identities,
            transport=transport,
            ledgers=ScientificLedgersV2(
                provider=scientific_ledger,
                proposal=proposal_ledger,
                outcome=outcome_ledger,
                direct_number=direct_ledger,
            ),
            progress=progress,
        )
    except ScientificModelIdentityMismatchAbortV2 as exc:
        return {
            "status": "failed_task039e3_model_identity_integrity",
            "capability_receipt": receipt,
            "scientific_provider_ledger_hash": exc.provider_ledger_hash,
            "last_completed_slot": exc.record.slot.to_dict(),
            "actual_returned_model": exc.actual_returned_model,
            "actual_response_id": exc.actual_response_id,
            "terminal_slot_state": exc.record.terminal_slot_state,
            "automatic_resume_authorized": False,
        }
    finally:
        scientific_ledger.close()
        proposal_ledger.close()
        outcome_ledger.close()
        direct_ledger.close()

    scientific_attempts = len(transport.attempt_custody) - attempt_start
    accounting = build_typed_provider_accounting_v2(
        capability_transport_attempts=execution.transport_attempts,
        scientific_logical_calls=scientific.scientific_logical_calls,
        scientific_transport_attempts=scientific_attempts,
        full_scientific_run_complete=True,
    )
    return {
        "status": "passed_task039e3_rule_construction_scientific_execution",
        "capability_receipt": receipt,
        "capability_custody": dict(custody),
        "scientific_result": scientific.to_dict(),
        "scientific_provider_ledger_hash": scientific_ledger.ledger_hash,
        "typed_accounting": accounting.to_dict(),
    }


def _verify_self_hashed_artifact(path: Path, expected: str) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise TASK039E3RecoveryExecutionV2Error(f"artifact unavailable: {path.name}")
    field = "artifact_hash" if "artifact_hash" in document else "self_hash"
    supplied = document.get(field)
    content = {key: value for key, value in document.items() if key != field}
    if supplied != expected or stable_hash_v1(content) != expected:
        raise TASK039E3RecoveryExecutionV2Error(f"artifact binding differs: {path.name}")
    return document


def load_prior_authority_state_v2(repository_root: Path) -> PriorAuthorityStateV2:
    reports = repository_root / "docs" / "task_reports"
    r0 = _verify_self_hashed_artifact(
        reports / "TASK-039E3_R0_RECEIPT.json", R0_BUNDLE_HASH
    )
    if r0.get("component_artifact_hashes", {}).get("recovery") != (
        "8b1b55c4ed96b0642737e616dd60b271684d59738c8186211abb9c6c46cd1362"
    ):
        raise TASK039E3RecoveryExecutionV2Error("R0 recovery binding differs")
    _verify_self_hashed_artifact(
        reports / "TASK-039E3_R1A_TIMEOUT_AUTHORITY.json", R1A_TIMEOUT_AUTHORITY_HASH
    )
    audit = _verify_self_hashed_artifact(
        reports / "TASK-039E3_R1B_AUDIT_RECEIPT.json", R1B_AUDIT_RECEIPT_HASH
    )
    if audit.get("independent_audit_bundle_hash") != R1B_INDEPENDENT_AUDIT_BUNDLE_HASH:
        raise TASK039E3RecoveryExecutionV2Error("R1B audit bundle differs")
    return PriorAuthorityStateV2(
        R0_COMMIT,
        R0_BUNDLE_HASH,
        R1A_COMMIT,
        R1A_TIMEOUT_AUTHORITY_HASH,
        R1B_COMMIT_A,
        R1B_COMMIT_B,
        R1B_AUDIT_COMMIT_B,
        R1B_INDEPENDENT_AUDIT_BUNDLE_HASH,
        R1B_AUDIT_RECEIPT_HASH,
    )


def collect_git_execution_state_v2(
    repository_root: Path, source_manifest: Mapping[str, Any]
) -> GitExecutionStateV2:
    manifest = verify_public_artifact_v1(source_manifest)

    def run(*args: str, text: bool = True) -> Any:
        return subprocess.run(
            ["git", *args], cwd=repository_root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text,
        ).stdout

    head = run("rev-parse", "HEAD").strip()
    status = run("status", "--porcelain=v1")
    index_clean = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repository_root, check=False
    ).returncode == 0
    records = manifest.get("source_records")
    match = isinstance(records, list)
    if match:
        for record in records:
            if not isinstance(record, Mapping):
                match = False
                break
            path = record.get("repository_path")
            if not isinstance(path, str):
                match = False
                break
            blob = run("rev-parse", f"{head}:{path}").strip()
            data = run("show", f"{head}:{path}", text=False)
            if blob != record.get("git_blob_sha") or sha256(data).hexdigest() != record.get("sha256"):
                match = False
                break
    return GitExecutionStateV2(
        head_commit=head,
        worktree_clean=not bool(status),
        index_clean=index_clean,
        source_manifest_hash=manifest["artifact_hash"],
        source_blobs_match_manifest=match,
    )


__all__ = [
    "RecoveryCapabilityExecutionV2",
    "TASK039E3RecoveryExecutionV2Error",
    "build_recovery_capability_receipt_v2",
    "collect_git_execution_state_v2",
    "execute_recovery_capability_probe_v2",
    "freeze_capability_custody_v2",
    "load_prior_authority_state_v2",
    "run_capability_then_science_v2",
]
