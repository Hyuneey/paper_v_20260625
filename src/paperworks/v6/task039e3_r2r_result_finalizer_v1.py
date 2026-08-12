"""Offline-finalizable public/private result contract for a future R2R run.

This additive module never reads evidence, credentials, or the network.  It
consumes an already completed fresh R2R cohort, reuses the frozen scientific
metric and canonical-artifact primitives, and makes PASS reachable only after
the R2R terminal receipt has been written last, re-read, and self-hash checked.
The one aborted historical R2 call remains in lifetime accounting only.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeRecordV1,
    ConstructionProposalRecordV1,
    DirectNumberOutcomeV1,
    aggregate_construction_metrics_v1,
    aggregate_direct_number_metrics_v1,
)
from paperworks.v6.task039e3_r2r_capability_reuse_v1 import (
    EXACT_MODEL,
    ValidatedCapabilityReuseR2RV1,
)
from paperworks.v6.task039e3_r2r_authorization_v1 import (
    CAPABILITY_REUSE_BINDING_HASH,
    validate_r2r_authorization_v1,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
    normalize_plain_json_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalLedgerReconstructionV3,
)
from paperworks.v6.task039e3_scientific_execution_v1 import _direct_summary


TASK_ID = "TASK-039E3-R2R-SCIENTIFIC-EXECUTION"
SUCCESS_STATUS = "passed_task039e3_r2r_scientific_execution"
RELATION_COUNT = 42
HISTORICAL_ABORTED_R2_SCIENTIFIC_LOGICAL_CALLS = 1
MINIMUM_R2R_SCIENTIFIC_CALLS = 252
MAXIMUM_R2R_SCIENTIFIC_CALLS = 336

PUBLIC_ARTIFACT_NAMES_R2R_V1: Mapping[str, str] = {
    "capability_reuse": "TASK-039E3_R2R_CAPABILITY_REUSE_BINDING.json",
    "provider_custody": "TASK-039E3_R2R_PROVIDER_CUSTODY_BINDING.json",
    "private_bindings": "TASK-039E3_R2R_PRIVATE_LEDGER_BINDINGS.json",
    "construction_metrics": "TASK-039E3_R2R_CONSTRUCTION_METRICS.json",
    "direct_number_metrics": "TASK-039E3_R2R_DIRECT_NUMBER_METRICS.json",
    "execution_summary": "TASK-039E3_R2R_EXECUTION_SUMMARY.json",
    "data_access_audit": "TASK-039E3_R2R_DATA_ACCESS_AUDIT.json",
    "execution_receipt": "TASK-039E3_R2R_EXECUTION_RECEIPT.json",
}

PRIVATE_ARTIFACT_NAMES_R2R_V1: Mapping[str, str] = {
    "scientific_provider": "TASK039E3_R2R_SCIENTIFIC_PROVIDER_LEDGER.json",
    "proposal_validity": "TASK039E3_R2R_PROPOSAL_VALIDITY_LEDGER.json",
    "construction_outcome": "TASK039E3_R2R_CONSTRUCTION_OUTCOME_LEDGER.json",
    "direct_number": "TASK039E3_R2R_DIRECT_NUMBER_LEDGER.json",
}

_AUTHORITY_FIELD_LENGTHS: Mapping[str, int] = {
    "protocol_bundle_hash": 64,
    "protocol_receipt_hash": 64,
    "forensic_commit_b": 40,
    "forensic_bundle_hash": 64,
    "forensic_receipt_hash": 64,
    "failed_r2_terminal_artifact_hash": 64,
    "failed_r2_scientific_provider_ledger_head_hash": 64,
    "capability_reuse_binding_hash": 64,
    "capability_receipt_hash": 64,
    "capability_provider_ledger_hash": 64,
    "capability_provider_ledger_head_hash": 64,
    "implementation_commit_a": 40,
    "implementation_commit_b": 40,
    "implementation_source_manifest_hash": 64,
    "independent_audit_commit_b": 40,
    "independent_audit_bundle_hash": 64,
    "independent_audit_receipt_hash": 64,
    "r2r_authorization_hash": 64,
}


class TASK039E3R2RResultFinalizationError(RuntimeError):
    """A complete, sanitized R2R terminal result cannot be frozen."""


@dataclass(frozen=True)
class FinalizedR2RScientificResultV1:
    """Returned only after the last-written receipt is durable and verified."""

    status: str
    public_artifact_hashes: Mapping[str, str]
    private_artifact_hashes: Mapping[str, str]
    execution_receipt_hash: str
    public_artifact_order: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status != SUCCESS_STATUS:
            raise TASK039E3R2RResultFinalizationError("successful status differs")
        if self.public_artifact_order[-1:] != ("execution_receipt",):
            raise TASK039E3R2RResultFinalizationError(
                "execution receipt was not materialized last"
            )


def _require_hash(value: Any, name: str, length: int = 64) -> str:
    if (
        not isinstance(value, str)
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TASK039E3R2RResultFinalizationError(
            f"{name} must be a lowercase {length}-character hash"
        )
    return value


def _closed_authority(bindings: Mapping[str, Any]) -> dict[str, str]:
    normalized = normalize_plain_json_v1(bindings)
    if not isinstance(normalized, dict) or set(normalized) != set(
        _AUTHORITY_FIELD_LENGTHS
    ):
        raise TASK039E3R2RResultFinalizationError(
            "R2R result authority bindings are not exact and closed"
        )
    return {
        field: _require_hash(normalized[field], field, length)
        for field, length in _AUTHORITY_FIELD_LENGTHS.items()
    }


def result_authority_bindings_from_r2r_authorization_v1(
    authorization: Mapping[str, Any],
) -> dict[str, str]:
    """Extract the exact terminal-result authority from a validated document."""

    validated = validate_r2r_authorization_v1(authorization)
    bindings = {
        "protocol_bundle_hash": authorization["protocol_bundle_hash"],
        "protocol_receipt_hash": authorization["protocol_receipt_hash"],
        "forensic_commit_b": authorization["forensic_commit_b"],
        "forensic_bundle_hash": authorization["forensic_bundle_hash"],
        "forensic_receipt_hash": authorization["forensic_receipt_hash"],
        "failed_r2_terminal_artifact_hash": authorization[
            "failed_r2_terminal_artifact_hash"
        ],
        "failed_r2_scientific_provider_ledger_head_hash": authorization[
            "failed_r2_scientific_provider_ledger_head_hash"
        ],
        "capability_reuse_binding_hash": authorization[
            "capability_reuse_binding_hash"
        ],
        "capability_receipt_hash": authorization["capability_receipt_hash"],
        "capability_provider_ledger_hash": authorization[
            "capability_provider_ledger_hash"
        ],
        "capability_provider_ledger_head_hash": authorization[
            "capability_provider_ledger_head_hash"
        ],
        "implementation_commit_a": validated.implementation_commit_a,
        "implementation_commit_b": validated.implementation_commit_b,
        "implementation_source_manifest_hash": (
            validated.implementation_source_manifest_hash
        ),
        "independent_audit_commit_b": validated.independent_audit_commit_b,
        "independent_audit_bundle_hash": validated.independent_audit_bundle_hash,
        "independent_audit_receipt_hash": validated.independent_audit_receipt_hash,
        "r2r_authorization_hash": validated.self_hash,
    }
    return _closed_authority(bindings)


def _verified_artifact(document: Mapping[str, Any], name: str) -> dict[str, Any]:
    try:
        return verify_public_artifact_v1(document)
    except Exception as exc:
        raise TASK039E3R2RResultFinalizationError(
            f"{name} is not a verified self-hashed artifact"
        ) from exc


def build_capability_reuse_binding_r2r_v1(
    validated: ValidatedCapabilityReuseR2RV1,
) -> dict[str, Any]:
    """Create the sanitized R2R binding; this cannot issue a capability call."""

    if (
        validated.cumulative_real_provider_capability_probes != 2
        or validated.additional_capability_probes != 0
        or validated.capability_transport_reachable is not False
    ):
        raise TASK039E3R2RResultFinalizationError(
            "capability reuse grants an additional probe or transport"
        )
    return finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_capability_reuse_binding_v1",
            "task_id": TASK_ID,
            "gate_status": "PASS_REUSED",
            "protocol_capability_reuse_binding_hash": (
                CAPABILITY_REUSE_BINDING_HASH
            ),
            "capability_receipt_hash": validated.receipt_hash,
            "capability_provider_ledger_hash": validated.provider_ledger_hash,
            "capability_provider_ledger_head_hash": (
                validated.provider_ledger_head_hash
            ),
            "capability_provider_record_hash": validated.provider_record_hash,
            "cumulative_real_provider_capability_probes": 2,
            "additional_capability_probes": 0,
            "third_capability_probe_authorized": False,
            "capability_transport_reachable": False,
            "local_compatibility_slots": 0,
            "raw_provider_content_public": False,
            "credential_persisted": False,
            "authorization_header_persisted": False,
        }
    )


def provider_custody_binding_from_reconstruction_r2r_v1(
    reconstruction: TransactionalLedgerReconstructionV3,
) -> dict[str, Any]:
    """Project an already reconstructed R2R chain into sanitized custody."""

    return finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_transactional_provider_binding_v1",
            "task_id": TASK_ID,
            **reconstruction.to_dict(),
            "record_count": reconstruction.authoritative_record_count,
            "hash_chain_verified": True,
            "authoritative_head_verified": True,
            "orphan_records_authoritative": False,
            "raw_provider_content_public": False,
        }
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _has_link_component(path: Path) -> bool:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if not current.exists():
            continue
        is_junction = getattr(current, "is_junction", None)
        if current.is_symlink() or (callable(is_junction) and is_junction()):
            return True
    return False


def _validated_path(value: Path, name: str) -> Path:
    if not value.is_absolute() or ".." in value.parts:
        raise TASK039E3R2RResultFinalizationError(
            f"{name} must be absolute and traversal-free"
        )
    if _has_link_component(value):
        raise TASK039E3R2RResultFinalizationError(
            f"{name} must not contain link or junction components"
        )
    return value.resolve(strict=False)


def prepare_r2r_result_roots_v1(
    *,
    repository_root: Path,
    recovery_private_root: Path,
    public_output_root: Path,
    protected_private_roots: Sequence[Path] = (),
) -> tuple[Path, Path]:
    """Create a distinct R2R final directory and new/empty public root."""

    repository = repository_root.resolve(strict=True)
    private = _validated_path(recovery_private_root, "recovery private root")
    public = _validated_path(public_output_root, "public output root")
    protected = tuple(
        _validated_path(path, "protected private root")
        for path in protected_private_roots
    )
    roots = (repository, private, public, *protected)
    for index, left in enumerate(roots):
        for right in roots[index + 1 :]:
            if _is_relative_to(left, right) or _is_relative_to(right, left):
                raise TASK039E3R2RResultFinalizationError(
                    "repository, private roots, and public root must be distinct and unnested"
                )
    if not private.is_dir():
        raise TASK039E3R2RResultFinalizationError(
            "recovery private root must already exist"
        )
    private_final = private / "final_authoritative_r2r_v1"
    if private_final.exists():
        raise TASK039E3R2RResultFinalizationError(
            "R2R private finalization directory must be new"
        )
    if public.exists():
        if not public.is_dir() or any(public.iterdir()):
            raise TASK039E3R2RResultFinalizationError(
                "public output root must be new or empty"
            )
    elif not public.parent.is_dir():
        raise TASK039E3R2RResultFinalizationError(
            "public output root parent must exist"
        )
    private_final.mkdir()
    if not public.exists():
        public.mkdir()
    return private_final, public


def _mapping_record(record: Any, name: str) -> dict[str, Any]:
    if isinstance(record, ConstructionProposalRecordV1):
        normalized = normalize_plain_json_v1(
            {
                "relation_identity": record.relation_identity,
                "arm": record.arm,
                "call_number": record.call_number,
                "project_proposal": record.project_proposal,
                "validity_result": record.validity_result.to_dict(),
                "proposal_hash": record.proposal_hash,
                "validity_hash": record.validity_hash,
                "record_hash": record.record_hash,
            }
        )
    elif isinstance(record, Mapping):
        normalized = normalize_plain_json_v1(record)
    else:
        to_dict = getattr(record, "to_dict", None)
        if not callable(to_dict):
            raise TASK039E3R2RResultFinalizationError(
                f"{name} record is not materializable"
            )
        normalized = normalize_plain_json_v1(to_dict())
    if not isinstance(normalized, dict):
        raise TASK039E3R2RResultFinalizationError(f"{name} record must be an object")
    return normalized


def _coerce_outcome(
    record: ConstructionOutcomeRecordV1 | Mapping[str, Any],
) -> ConstructionOutcomeRecordV1:
    if isinstance(record, ConstructionOutcomeRecordV1):
        return record
    values = {
        key: value
        for key, value in _mapping_record(record, "construction outcome").items()
        if key != "artifact_hash"
    }
    try:
        return ConstructionOutcomeRecordV1(**values)
    except (TypeError, ValueError) as exc:
        raise TASK039E3R2RResultFinalizationError(
            "construction outcome differs from the frozen contract"
        ) from exc


def _coerce_direct(
    record: DirectNumberOutcomeV1 | Mapping[str, Any],
) -> DirectNumberOutcomeV1:
    if isinstance(record, DirectNumberOutcomeV1):
        return record
    values = {
        key: value
        for key, value in _mapping_record(record, "direct-number outcome").items()
        if key != "record_hash"
    }
    if isinstance(values.get("sign_domain_violation_roles"), list):
        values["sign_domain_violation_roles"] = tuple(
            values["sign_domain_violation_roles"]
        )
    try:
        return DirectNumberOutcomeV1(**values)
    except (TypeError, ValueError) as exc:
        raise TASK039E3R2RResultFinalizationError(
            "direct-number outcome differs from the frozen contract"
        ) from exc


def _validate_completed_r2r_science(
    outcomes: Sequence[ConstructionOutcomeRecordV1],
    direct: Sequence[DirectNumberOutcomeV1],
    typed_accounting: Mapping[str, Any],
) -> tuple[dict[str, int], int, dict[str, Any]]:
    identities = {record.relation_identity for record in outcomes}
    if len(identities) != RELATION_COUNT or len(outcomes) != RELATION_COUNT * 4:
        raise TASK039E3R2RResultFinalizationError(
            "fresh R2R cohort must contain four arms for 42 relations"
        )
    for identity in identities:
        if {record.arm for record in outcomes if record.relation_identity == identity} != {
            "T0",
            "T1",
            "T1-B",
            "T2",
        }:
            raise TASK039E3R2RResultFinalizationError(
                "fresh R2R arm coverage differs"
            )
    if len(direct) != RELATION_COUNT or {
        record.relation_identity for record in direct
    } != identities:
        raise TASK039E3R2RResultFinalizationError(
            "R2R direct-number cohort does not match construction relations"
        )
    calls = {
        "T1": sum(
            record.generation_calls_consumed for record in outcomes if record.arm == "T1"
        ),
        "T1-B": sum(
            record.generation_calls_consumed
            for record in outcomes
            if record.arm == "T1-B"
        ),
        "T2": sum(
            record.generation_calls_consumed for record in outcomes if record.arm == "T2"
        ),
        "T1-DIRECT-NUMBER": sum(
            record.generation_calls_consumed for record in direct
        ),
    }
    if (
        calls["T1"] != 42
        or calls["T1-B"] != 126
        or calls["T1-DIRECT-NUMBER"] != 42
        or not 42 <= calls["T2"] <= 126
    ):
        raise TASK039E3R2RResultFinalizationError("R2R arm call counts differ")
    r2r_calls = sum(calls.values())
    if not MINIMUM_R2R_SCIENTIFIC_CALLS <= r2r_calls <= MAXIMUM_R2R_SCIENTIFIC_CALLS:
        raise TASK039E3R2RResultFinalizationError("R2R scientific call budget differs")
    accounting = normalize_plain_json_v1(typed_accounting)
    if not isinstance(accounting, dict):
        raise TASK039E3R2RResultFinalizationError("typed accounting must be an object")
    expected = {
        "historical_aborted_r2_scientific_logical_calls": 1,
        "historical_aborted_r2_provider_authored_scientific_responses": 0,
        "r2r_t1_logical_calls": calls["T1"],
        "r2r_t1b_logical_calls": calls["T1-B"],
        "r2r_t2_logical_calls": calls["T2"],
        "r2r_direct_number_logical_calls": calls["T1-DIRECT-NUMBER"],
        "r2r_scientific_logical_calls": r2r_calls,
        "lifetime_scientific_logical_call_attempts": 1 + r2r_calls,
        "scientific_concurrency": 1,
        "scientific_generation_retries": 0,
        "historical_partial_records_reused": 0,
        "additional_capability_probes": 0,
        "cumulative_real_provider_capability_probes": 2,
        "local_compatibility_slots": 0,
    }
    if any(accounting.get(key) != value for key, value in expected.items()):
        raise TASK039E3R2RResultFinalizationError(
            "typed accounting mixes historical and R2R cohort authority"
        )
    attempts = accounting.get("r2r_scientific_transport_attempts")
    retries = accounting.get("r2r_scientific_transport_retries")
    if (
        isinstance(attempts, bool)
        or not isinstance(attempts, int)
        or isinstance(retries, bool)
        or not isinstance(retries, int)
        or attempts < r2r_calls
        or retries != attempts - r2r_calls
    ):
        raise TASK039E3R2RResultFinalizationError(
            "R2R transport accounting differs"
        )
    return calls, r2r_calls, accounting


def _private_snapshot(
    *, artifact_type: str, records: Sequence[Mapping[str, Any]], source: str
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "artifact_type": artifact_type,
        "task_id": TASK_ID,
        "record_count": len(records),
        "records": list(records),
        "authoritative_snapshot": True,
        "source_classification": source,
        "historical_r2_records_included": 0,
        "storage_boundary": "outside_git_private",
        "raw_contents_public": False,
        "credential_included": False,
        "authorization_header_included": False,
        "chain_of_thought_included": False,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "utility_evaluation_authorized": False,
        "winner_selected": False,
    }


def finalize_successful_r2r_scientific_result_v1(
    *,
    repository_root: Path,
    recovery_private_root: Path,
    public_output_root: Path,
    protected_private_roots: Sequence[Path] = (),
    execution_commit: str,
    source_manifest_hash: str,
    authorization_hash: str,
    configuration_fingerprint: str,
    postcontact_integrity_status: str,
    authority_bindings: Mapping[str, Any],
    capability_reuse_binding: Mapping[str, Any],
    scientific_provider_binding: Mapping[str, Any],
    scientific_provider_records: Sequence[Mapping[str, Any]],
    proposal_records: Sequence[Mapping[str, Any]],
    outcome_records: Sequence[ConstructionOutcomeRecordV1 | Mapping[str, Any]],
    direct_number_records: Sequence[DirectNumberOutcomeV1 | Mapping[str, Any]],
    typed_accounting: Mapping[str, Any],
    scientific_source_hashes: Mapping[str, str],
    artifact_writer: Callable[
        [str | os.PathLike[str], Mapping[str, Any]], dict[str, Any]
    ] = write_public_artifact_atomic_v1,
) -> FinalizedR2RScientificResultV1:
    """Freeze one complete fresh R2R cohort without loading evidence/provider state."""

    _require_hash(execution_commit, "execution commit", 40)
    _require_hash(source_manifest_hash, "source manifest hash")
    _require_hash(authorization_hash, "authorization hash")
    _require_hash(configuration_fingerprint, "configuration fingerprint")
    if postcontact_integrity_status != "verified_unchanged":
        raise TASK039E3R2RResultFinalizationError(
            "post-contact integrity must be verified before R2R finalization"
        )
    authority = _closed_authority(authority_bindings)
    if authority["implementation_commit_a"] != execution_commit:
        raise TASK039E3R2RResultFinalizationError("implementation Commit A differs")
    if authority["implementation_source_manifest_hash"] != source_manifest_hash:
        raise TASK039E3R2RResultFinalizationError("R2R source manifest differs")
    if authority["r2r_authorization_hash"] != authorization_hash:
        raise TASK039E3R2RResultFinalizationError("R2R authorization differs")

    source_hashes = normalize_plain_json_v1(scientific_source_hashes)
    if (
        not isinstance(source_hashes, dict)
        or not source_hashes
        or any(
            not isinstance(path, str)
            or not path
            or _require_hash(value, f"source hash {path}") != value
            for path, value in source_hashes.items()
        )
    ):
        raise TASK039E3R2RResultFinalizationError(
            "scientific source hashes must be a non-empty hash mapping"
        )

    capability = _verified_artifact(capability_reuse_binding, "capability reuse binding")
    if (
        capability.get("artifact_type")
        != "task039e3_r2r_capability_reuse_binding_v1"
        or capability.get("gate_status") != "PASS_REUSED"
        or capability.get("additional_capability_probes") != 0
        or capability.get("cumulative_real_provider_capability_probes") != 2
        or capability.get("third_capability_probe_authorized") is not False
        or capability.get("capability_transport_reachable") is not False
        or capability.get("protocol_capability_reuse_binding_hash")
        != authority["capability_reuse_binding_hash"]
        or capability.get("capability_receipt_hash")
        != authority["capability_receipt_hash"]
        or capability.get("capability_provider_ledger_hash")
        != authority["capability_provider_ledger_hash"]
        or capability.get("capability_provider_ledger_head_hash")
        != authority["capability_provider_ledger_head_hash"]
    ):
        raise TASK039E3R2RResultFinalizationError("capability reuse binding differs")

    scientific_binding = _verified_artifact(
        scientific_provider_binding, "scientific provider binding"
    )
    if (
        scientific_binding.get("artifact_type")
        != "task039e3_r2r_transactional_provider_binding_v1"
        or scientific_binding.get("ledger_kind") != "scientific_provider"
        or scientific_binding.get("hash_chain_verified") is not True
        or scientific_binding.get("authoritative_head_verified") is not True
        or scientific_binding.get("orphan_records") != []
        or scientific_binding.get("pending_files") != []
    ):
        raise TASK039E3R2RResultFinalizationError(
            "scientific provider custody binding differs"
        )
    provider_documents = tuple(
        _mapping_record(record, "scientific provider")
        for record in scientific_provider_records
    )
    if any(
        record.get("logical_call_kind") != "scientific"
        for record in provider_documents
    ):
        raise TASK039E3R2RResultFinalizationError(
            "scientific provider snapshot contains another call family"
        )
    proposal_documents = tuple(
        _mapping_record(record, "proposal-validity") for record in proposal_records
    )
    outcomes = tuple(_coerce_outcome(record) for record in outcome_records)
    direct = tuple(_coerce_direct(record) for record in direct_number_records)
    calls, r2r_calls, accounting = _validate_completed_r2r_science(
        outcomes, direct, typed_accounting
    )
    if (
        len(provider_documents) != r2r_calls
        or scientific_binding.get("record_count") != r2r_calls
    ):
        raise TASK039E3R2RResultFinalizationError(
            "scientific provider record count differs from R2R calls"
        )

    private_root, public_root = prepare_r2r_result_roots_v1(
        repository_root=repository_root,
        recovery_private_root=recovery_private_root,
        public_output_root=public_output_root,
        protected_private_roots=protected_private_roots,
    )
    outcome_documents = tuple(
        {**record.to_dict(), "artifact_hash": record.artifact_hash}
        for record in outcomes
    )
    direct_documents = tuple(
        {
            **record.__dict__,
            "sign_domain_violation_roles": list(record.sign_domain_violation_roles),
            "normalized_absolute_errors": (
                dict(record.normalized_absolute_errors)
                if record.normalized_absolute_errors is not None
                else None
            ),
        }
        for record in direct
    )
    private_inputs = {
        "scientific_provider": _private_snapshot(
            artifact_type="task039e3_r2r_scientific_provider_ledger_v1",
            records=provider_documents,
            source="transactional_provider_ledger",
        ),
        "proposal_validity": _private_snapshot(
            artifact_type="task039e3_r2r_proposal_validity_ledger_v1",
            records=proposal_documents,
            source="fresh_r2r_working_log",
        ),
        "construction_outcome": _private_snapshot(
            artifact_type="task039e3_r2r_construction_outcome_ledger_v1",
            records=outcome_documents,
            source="fresh_r2r_working_log",
        ),
        "direct_number": _private_snapshot(
            artifact_type="task039e3_r2r_direct_number_ledger_v1",
            records=direct_documents,
            source="fresh_r2r_working_log",
        ),
    }
    private_artifacts: dict[str, dict[str, Any]] = {}
    for key in (
        "scientific_provider",
        "proposal_validity",
        "construction_outcome",
        "direct_number",
    ):
        private_artifacts[key] = artifact_writer(
            private_root / PRIVATE_ARTIFACT_NAMES_R2R_V1[key], private_inputs[key]
        )

    main_metrics = aggregate_construction_metrics_v1(outcomes)
    direct_metrics_raw = aggregate_direct_number_metrics_v1(direct)
    direct_summary = _direct_summary(direct_metrics_raw, direct)
    provider_custody = finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_provider_custody_binding_v1",
            "task_id": TASK_ID,
            "provider": "openai",
            "model": EXACT_MODEL,
            "capability_reuse_binding_hash": capability["artifact_hash"],
            "scientific_provider_custody_binding_hash": scientific_binding[
                "artifact_hash"
            ],
            "scientific_provider_ledger_snapshot_hash": private_artifacts[
                "scientific_provider"
            ]["artifact_hash"],
            "scientific_provider_record_count": r2r_calls,
            "historical_failed_r2_ledger_head_hash": authority[
                "failed_r2_scientific_provider_ledger_head_hash"
            ],
            "historical_provider_records_reused": 0,
            "capability_and_scientific_ledgers_separately_typed": True,
            "provider_hash_chain_verified": True,
            "raw_provider_content_public": False,
            "credential_persisted": False,
            "authorization_header_persisted": False,
        }
    )
    private_bindings = finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_private_ledger_bindings_v1",
            "task_id": TASK_ID,
            "scientific_provider_binding_hash": scientific_binding["artifact_hash"],
            "scientific_provider_ledger_hash": private_artifacts[
                "scientific_provider"
            ]["artifact_hash"],
            "proposal_validity_ledger_hash": private_artifacts["proposal_validity"][
                "artifact_hash"
            ],
            "construction_outcome_ledger_hash": private_artifacts[
                "construction_outcome"
            ]["artifact_hash"],
            "direct_number_ledger_hash": private_artifacts["direct_number"][
                "artifact_hash"
            ],
            "provider_records": r2r_calls,
            "proposal_records": len(proposal_documents),
            "outcome_records": len(outcomes),
            "direct_number_records": len(direct),
            "historical_r2_records_included": 0,
            "private_contents_public": False,
            "storage_boundary": "outside_git_private",
        }
    )
    construction_metrics = finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_construction_metrics_v1",
            "task_id": TASK_ID,
            "status": SUCCESS_STATUS,
            "metrics_cohort": "R2R_FRESH_FULL_COHORT_ONLY",
            "main_metrics": main_metrics,
            "scientific_provider_ledger_hash": private_artifacts[
                "scientific_provider"
            ]["artifact_hash"],
            "proposal_validity_ledger_hash": private_artifacts["proposal_validity"][
                "artifact_hash"
            ],
            "construction_outcome_ledger_hash": private_artifacts[
                "construction_outcome"
            ]["artifact_hash"],
            "r2r_scientific_logical_calls": r2r_calls,
            "historical_partial_results_in_metrics": False,
            "winner_selected": False,
        }
    )
    direct_metrics = finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_direct_number_metrics_v1",
            "task_id": TASK_ID,
            "metrics_cohort": "R2R_FRESH_FULL_COHORT_ONLY",
            "relation_count": RELATION_COUNT,
            **direct_summary,
            "historical_partial_results_in_metrics": False,
            "validity_authority": False,
            "runtime_authority": False,
            "winner_selected": False,
        }
    )
    summary = finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_execution_summary_v1",
            "task_id": TASK_ID,
            "status": SUCCESS_STATUS,
            "execution_code_commit": execution_commit,
            "recovery_execution_mode": "FRESH_FULL_COHORT_RESTART",
            "relations_completed": RELATION_COUNT,
            "relations_skipped": 0,
            "t0_outcomes": RELATION_COUNT,
            "t1_outcomes": RELATION_COUNT,
            "t1b_outcomes": RELATION_COUNT,
            "t2_outcomes": RELATION_COUNT,
            "direct_number_results": RELATION_COUNT,
            "scientific_call_counts": calls,
            "r2r_scientific_logical_calls": r2r_calls,
            "historical_aborted_r2_scientific_logical_calls": 1,
            "lifetime_scientific_logical_call_attempts": 1 + r2r_calls,
            "typed_accounting": accounting,
            "historical_partial_results_reused": False,
            "cross_arm_leakage": False,
            "automatic_resume_authorized": False,
            "provider_recontact_authorized": False,
            "rule_v2_authorized": False,
            "runtime_authority": False,
            "utility_evaluation_authorized": False,
            "winner_selected": False,
        }
    )
    access = finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_data_access_audit_v1",
            "task_id": TASK_ID,
            "e1_private_evidence_accessed_after_capability_reuse": True,
            "e1_private_evidence_modified": False,
            "historical_failed_r2_private_root_accessed_for_science": False,
            "historical_failed_r2_private_root_modified": False,
            "hai_source_files_accessed": False,
            "test_labels_attacks_accessed": False,
            "provider_contacted": True,
            "credential_read_by_authorized_live_runner": True,
            "credential_persisted": False,
            "individual_proposals_public": False,
            "raw_private_evidence_public": False,
            "prohibited_access_count": 0,
            "rule_v2_authorized": False,
            "runtime_authority": False,
            "utility_evaluation_authorized": False,
            "winner_selected": False,
        }
    )

    public_documents: Mapping[str, Mapping[str, Any]] = {
        "capability_reuse": capability,
        "provider_custody": provider_custody,
        "private_bindings": private_bindings,
        "construction_metrics": construction_metrics,
        "direct_number_metrics": direct_metrics,
        "execution_summary": summary,
        "data_access_audit": access,
    }
    public_hashes: dict[str, str] = {}
    write_order: list[str] = []
    for key in (
        "capability_reuse",
        "provider_custody",
        "private_bindings",
        "construction_metrics",
        "direct_number_metrics",
        "execution_summary",
        "data_access_audit",
    ):
        written = artifact_writer(
            public_root / PUBLIC_ARTIFACT_NAMES_R2R_V1[key], public_documents[key]
        )
        public_hashes[key] = _require_hash(
            written.get("artifact_hash"), f"written {key} artifact hash"
        )
        write_order.append(key)

    receipt = finalize_public_artifact_v1(
        {
            "schema_version": "1.0.0",
            "artifact_type": "task039e3_r2r_execution_receipt_v1",
            "task_id": TASK_ID,
            "status": SUCCESS_STATUS,
            "execution_code_commit": execution_commit,
            "source_manifest_hash": source_manifest_hash,
            "r2r_authorization_hash": authorization_hash,
            "execution_configuration_fingerprint": configuration_fingerprint,
            "postcontact_integrity_status": postcontact_integrity_status,
            **authority,
            "capability_reuse_artifact_hash": public_hashes["capability_reuse"],
            "provider_custody_binding_hash": public_hashes["provider_custody"],
            "private_ledger_bindings_hash": public_hashes["private_bindings"],
            "construction_metrics_hash": public_hashes["construction_metrics"],
            "direct_number_metrics_hash": public_hashes["direct_number_metrics"],
            "execution_summary_hash": public_hashes["execution_summary"],
            "data_access_audit_hash": public_hashes["data_access_audit"],
            "typed_accounting": accounting,
            "scientific_source_hashes": source_hashes,
            "historical_partial_results_reused": False,
            "individual_proposals_public": False,
            "automatic_resume_authorized": False,
            "provider_recontact_authorized": False,
            "rule_v2_authorized": False,
            "runtime_authority": False,
            "utility_evaluation_authorized": False,
            "winner_selected": False,
        }
    )
    written_receipt = artifact_writer(
        public_root / PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"], receipt
    )
    write_order.append("execution_receipt")
    try:
        observed = json.loads(
            (
                public_root
                / PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]
            ).read_text(encoding="utf-8")
        )
        verified_receipt = verify_public_artifact_v1(observed)
    except Exception as exc:
        raise TASK039E3R2RResultFinalizationError(
            "durable R2R receipt could not be re-read and self-hash verified"
        ) from exc
    if written_receipt != verified_receipt or verified_receipt.get("status") != SUCCESS_STATUS:
        raise TASK039E3R2RResultFinalizationError(
            "durable R2R receipt differs from the intended terminal PASS"
        )
    public_hashes["execution_receipt"] = verified_receipt["artifact_hash"]
    return FinalizedR2RScientificResultV1(
        status=SUCCESS_STATUS,
        public_artifact_hashes=public_hashes,
        private_artifact_hashes={
            key: document["artifact_hash"] for key, document in private_artifacts.items()
        },
        execution_receipt_hash=verified_receipt["artifact_hash"],
        public_artifact_order=tuple(write_order),
    )


__all__ = [
    "FinalizedR2RScientificResultV1",
    "HISTORICAL_ABORTED_R2_SCIENTIFIC_LOGICAL_CALLS",
    "MAXIMUM_R2R_SCIENTIFIC_CALLS",
    "MINIMUM_R2R_SCIENTIFIC_CALLS",
    "PRIVATE_ARTIFACT_NAMES_R2R_V1",
    "PUBLIC_ARTIFACT_NAMES_R2R_V1",
    "SUCCESS_STATUS",
    "TASK039E3R2RResultFinalizationError",
    "build_capability_reuse_binding_r2r_v1",
    "finalize_successful_r2r_scientific_result_v1",
    "prepare_r2r_result_roots_v1",
    "provider_custody_binding_from_reconstruction_r2r_v1",
    "result_authority_bindings_from_r2r_authorization_v1",
]
