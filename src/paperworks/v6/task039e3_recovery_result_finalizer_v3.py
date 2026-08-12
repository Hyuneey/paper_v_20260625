"""Complete recovery scientific-result finalization for TASK-039E3 R1D2.

The module is additive and provider-agnostic.  It consumes already completed
scientific records, reuses the frozen E3 metric aggregators, freezes private
authoritative snapshots outside Git, and writes the sanitized public result to
an external empty directory.  The execution receipt is written and verified
last; no successful result exists without that durable receipt.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_execution_prep_v1 import (
    E0_PROTOCOL_BUNDLE_HASH,
    E1_CONSTRUCTION_EVIDENCE_COHORT_HASH,
    E1_MATERIALIZATION_RESULT_HASH,
    E1_PRIVATE_LEDGER_HASH,
    E2_PROTOCOL_BUNDLE_HASH,
    E3_AUTHORIZATION_HASH,
    EXACT_MODEL,
    EXECUTION_SCHEDULE_HASH,
)
from paperworks.v6.task039e3_orchestration_v1 import (
    ConstructionOutcomeRecordV1,
    DirectNumberOutcomeV1,
    PublicConstructionMetricsV1,
    aggregate_construction_metrics_v1,
    aggregate_direct_number_metrics_v1,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    finalize_public_artifact_v1,
    normalize_plain_json_v1,
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)
from paperworks.v6.task039e3_scientific_execution_v1 import _direct_summary
from paperworks.v6.task039e3_recovery_transactional_custody_v3 import (
    TransactionalLedgerReconstructionV3,
)


TASK_ID = "TASK-039E3-R2"
SUCCESS_STATUS = "passed_task039e3_r2_recovery_execution"
RELATION_COUNT = 42
MINIMUM_SCIENTIFIC_CALLS = 252
MAXIMUM_SCIENTIFIC_CALLS = 336

PUBLIC_ARTIFACT_NAMES_V3: Mapping[str, str] = {
    "capability": "TASK-039E3_R2_CAPABILITY_GATE.json",
    "provider_custody": "TASK-039E3_R2_PROVIDER_CUSTODY_BINDING.json",
    "private_bindings": "TASK-039E3_R2_PRIVATE_LEDGER_BINDINGS.json",
    "construction_metrics": "TASK-039E3_R2_CONSTRUCTION_METRICS.json",
    "direct_number_metrics": "TASK-039E3_R2_DIRECT_NUMBER_METRICS.json",
    "execution_summary": "TASK-039E3_R2_EXECUTION_SUMMARY.json",
    "data_access_audit": "TASK-039E3_R2_DATA_ACCESS_AUDIT.json",
    "execution_receipt": "TASK-039E3_R2_EXECUTION_RECEIPT.json",
}

PRIVATE_ARTIFACT_NAMES_V3: Mapping[str, str] = {
    "scientific_provider": "TASK039E3_R2_SCIENTIFIC_PROVIDER_LEDGER.json",
    "proposal_validity": "TASK039E3_R2_PROPOSAL_VALIDITY_LEDGER.json",
    "construction_outcome": "TASK039E3_R2_CONSTRUCTION_OUTCOME_LEDGER.json",
    "direct_number": "TASK039E3_R2_DIRECT_NUMBER_LEDGER.json",
}

_AUTHORITY_FIELDS = (
    "r0_bundle_hash",
    "r1a_timeout_authority_hash",
    "r1b_commit_b",
    "r1c_commit_b",
    "r1c_audit_bundle_hash",
    "r1d2_commit_a",
    "r1d2_commit_b",
    "r1d2_source_manifest_hash",
    "r1d2_audit_commit_b",
    "r1d2_independent_audit_bundle_hash",
    "r1d2_audit_receipt_hash",
    "r2_authorization_hash",
)


class TASK039E3RecoveryResultFinalizationV3Error(RuntimeError):
    """Raised when complete scientific-result materialization cannot finish."""


@dataclass(frozen=True)
class FinalizedScientificResultV3:
    """Verified terminal result returned only after the receipt is durable."""

    status: str
    public_artifact_hashes: Mapping[str, str]
    private_artifact_hashes: Mapping[str, str]
    execution_receipt_hash: str
    public_artifact_order: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status != SUCCESS_STATUS:
            raise TASK039E3RecoveryResultFinalizationV3Error(
                "terminal successful result status differs"
            )
        if self.public_artifact_order[-1:] != ("execution_receipt",):
            raise TASK039E3RecoveryResultFinalizationV3Error(
                "execution receipt was not materialized last"
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


def _validated_requested_path(value: Path, name: str) -> Path:
    if not value.is_absolute() or ".." in value.parts:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            f"{name} must be absolute and traversal-free"
        )
    if _has_link_component(value):
        raise TASK039E3RecoveryResultFinalizationV3Error(
            f"{name} must not contain symlink or junction components"
        )
    return value.resolve(strict=False)


def prepare_result_roots_v3(
    *,
    repository_root: Path,
    recovery_private_root: Path,
    public_output_root: Path,
    protected_private_roots: Sequence[Path] = (),
) -> tuple[Path, Path]:
    """Validate and prepare a private final directory and empty public root."""

    repository = repository_root.resolve(strict=True)
    private = _validated_requested_path(recovery_private_root, "recovery private root")
    public = _validated_requested_path(public_output_root, "public output root")
    protected = tuple(
        _validated_requested_path(path, "protected private root")
        for path in protected_private_roots
    )
    distinct_roots = (repository, private, public, *protected)
    for index, left in enumerate(distinct_roots):
        for right in distinct_roots[index + 1 :]:
            if not (_is_relative_to(left, right) or _is_relative_to(right, left)):
                continue
            raise TASK039E3RecoveryResultFinalizationV3Error(
                "repository, private roots, and public output root must be distinct and unnested"
            )
    if not private.is_dir():
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "recovery private root must already exist"
        )

    private_final = private / "final_authoritative_v3"
    if private_final.exists():
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "private finalization directory must be new"
        )
    if public.exists():
        if not public.is_dir() or any(public.iterdir()):
            raise TASK039E3RecoveryResultFinalizationV3Error(
                "public output root must be new or empty"
            )
    else:
        if not public.parent.is_dir():
            raise TASK039E3RecoveryResultFinalizationV3Error(
                "public output root parent must exist"
            )
    private_final.mkdir()
    if not public.exists():
        public.mkdir()
    return private_final, public


def _require_hash(value: Any, name: str, *, lengths: tuple[int, ...] = (64,)) -> str:
    if (
        not isinstance(value, str)
        or len(value) not in lengths
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TASK039E3RecoveryResultFinalizationV3Error(f"{name} must be a lowercase hash")
    return value


def _require_authority_bindings(bindings: Mapping[str, Any]) -> dict[str, str]:
    normalized = normalize_plain_json_v1(bindings)
    if not isinstance(normalized, dict) or set(normalized) != set(_AUTHORITY_FIELDS):
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "final authority bindings must be exact and closed"
        )
    result: dict[str, str] = {}
    for field in _AUTHORITY_FIELDS:
        lengths = (40,) if field.endswith("commit_a") or field.endswith("commit_b") else (64,)
        result[field] = _require_hash(normalized[field], field, lengths=lengths)
    return result


def _verified_input_artifact(document: Mapping[str, Any], name: str) -> dict[str, Any]:
    try:
        verified = verify_public_artifact_v1(document)
    except Exception as exc:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            f"{name} is not a verified self-hashed artifact"
        ) from exc
    return verified


def provider_custody_binding_from_reconstruction_v3(
    reconstruction: TransactionalLedgerReconstructionV3,
) -> dict[str, Any]:
    """Turn an independently reconstructed transactional chain into a binding."""

    return finalize_public_artifact_v1(
        {
            "schema_version": "3.0.0",
            "artifact_type": "task039e3_r2_transactional_provider_binding_v3",
            **reconstruction.to_dict(),
            "record_count": reconstruction.authoritative_record_count,
            "hash_chain_verified": True,
            "authoritative_head_verified": True,
            "orphan_records_authoritative": False,
        }
    )


def _mapping_record(record: Any, name: str) -> dict[str, Any]:
    if isinstance(record, Mapping):
        normalized = normalize_plain_json_v1(record)
    else:
        to_dict = getattr(record, "to_dict", None)
        if not callable(to_dict):
            raise TASK039E3RecoveryResultFinalizationV3Error(
                f"{name} record is not materializable"
            )
        normalized = normalize_plain_json_v1(to_dict())
    if not isinstance(normalized, dict):
        raise TASK039E3RecoveryResultFinalizationV3Error(f"{name} record must be an object")
    return normalized


def _coerce_outcome(record: ConstructionOutcomeRecordV1 | Mapping[str, Any]) -> ConstructionOutcomeRecordV1:
    if isinstance(record, ConstructionOutcomeRecordV1):
        return record
    fields = {
        key: value
        for key, value in _mapping_record(record, "construction outcome").items()
        if key != "artifact_hash"
    }
    try:
        return ConstructionOutcomeRecordV1(**fields)
    except (TypeError, ValueError) as exc:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "construction outcome cannot be reconstructed under the frozen contract"
        ) from exc


def _coerce_direct(record: DirectNumberOutcomeV1 | Mapping[str, Any]) -> DirectNumberOutcomeV1:
    if isinstance(record, DirectNumberOutcomeV1):
        return record
    fields = {
        key: value
        for key, value in _mapping_record(record, "direct-number").items()
        if key != "record_hash"
    }
    if isinstance(fields.get("sign_domain_violation_roles"), list):
        fields["sign_domain_violation_roles"] = tuple(fields["sign_domain_violation_roles"])
    try:
        return DirectNumberOutcomeV1(**fields)
    except (TypeError, ValueError) as exc:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "direct-number result cannot be reconstructed under the frozen contract"
        ) from exc


def _validate_completed_science(
    outcomes: Sequence[ConstructionOutcomeRecordV1],
    direct: Sequence[DirectNumberOutcomeV1],
    typed_accounting: Mapping[str, Any],
) -> tuple[dict[str, int], int]:
    identities = {item.relation_identity for item in outcomes}
    if len(identities) != RELATION_COUNT or len(outcomes) != RELATION_COUNT * 4:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "construction outcome cohort must contain four arms for 42 relations"
        )
    for identity in identities:
        if {item.arm for item in outcomes if item.relation_identity == identity} != {
            "T0", "T1", "T1-B", "T2"
        }:
            raise TASK039E3RecoveryResultFinalizationV3Error(
                "construction outcome arm coverage differs"
            )
    if len(direct) != RELATION_COUNT or {item.relation_identity for item in direct} != identities:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "direct-number cohort must match the 42 construction relations"
        )

    calls = {
        "T1": sum(item.generation_calls_consumed for item in outcomes if item.arm == "T1"),
        "T1-B": sum(item.generation_calls_consumed for item in outcomes if item.arm == "T1-B"),
        "T2": sum(item.generation_calls_consumed for item in outcomes if item.arm == "T2"),
        "T1-DIRECT-NUMBER": sum(item.generation_calls_consumed for item in direct),
    }
    if calls["T1"] != 42 or calls["T1-B"] != 126 or calls["T1-DIRECT-NUMBER"] != 42:
        raise TASK039E3RecoveryResultFinalizationV3Error("fixed scientific arm call counts differ")
    if not 42 <= calls["T2"] <= 126:
        raise TASK039E3RecoveryResultFinalizationV3Error("T2 call count differs")
    scientific_calls = sum(calls.values())
    if scientific_calls != 210 + calls["T2"] or not (
        MINIMUM_SCIENTIFIC_CALLS <= scientific_calls <= MAXIMUM_SCIENTIFIC_CALLS
    ):
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "total scientific logical-call contract differs"
        )

    accounting = normalize_plain_json_v1(typed_accounting)
    if not isinstance(accounting, dict):
        raise TASK039E3RecoveryResultFinalizationV3Error("typed accounting must be an object")
    expected = {
        "t1_logical_calls": calls["T1"],
        "t1b_logical_calls": calls["T1-B"],
        "t2_logical_calls": calls["T2"],
        "direct_number_logical_calls": calls["T1-DIRECT-NUMBER"],
        "scientific_logical_calls": scientific_calls,
        "scientific_concurrency": 1,
        "scientific_generation_retries": 0,
        "local_compatibility_slots": 0,
    }
    if any(accounting.get(key) != value for key, value in expected.items()):
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "typed accounting disagrees with frozen scientific outcomes"
        )
    attempts = accounting.get("scientific_transport_attempts")
    retries = accounting.get("scientific_transport_retries")
    if (
        isinstance(attempts, bool)
        or not isinstance(attempts, int)
        or isinstance(retries, bool)
        or not isinstance(retries, int)
        or attempts < scientific_calls
        or retries != attempts - scientific_calls
    ):
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "scientific transport accounting differs"
        )
    return calls, scientific_calls


def _private_snapshot_content(
    *, artifact_type: str, records: Sequence[Mapping[str, Any]], working_log_classification: str
) -> dict[str, Any]:
    return {
        "schema_version": "3.0.0",
        "artifact_type": artifact_type,
        "task_id": TASK_ID,
        "record_count": len(records),
        "records": list(records),
        "authoritative_snapshot": True,
        "working_log_classification": working_log_classification,
        "storage_boundary": "outside_git_private",
        "individual_proposals_public": False,
        "raw_calibrated_evidence_public": False,
        "credential_included": False,
        "authorization_header_included": False,
        "chain_of_thought_included": False,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "utility_evaluation_authorized": False,
    }


def finalize_successful_scientific_result_v3(
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
    capability_receipt: Mapping[str, Any],
    capability_provider_binding: Mapping[str, Any],
    scientific_provider_binding: Mapping[str, Any],
    scientific_provider_records: Sequence[Mapping[str, Any]],
    proposal_records: Sequence[Mapping[str, Any]],
    outcome_records: Sequence[ConstructionOutcomeRecordV1 | Mapping[str, Any]],
    direct_number_records: Sequence[DirectNumberOutcomeV1 | Mapping[str, Any]],
    typed_accounting: Mapping[str, Any],
    scientific_source_hashes: Mapping[str, str],
    artifact_writer: Callable[[str | os.PathLike[str], Mapping[str, Any]], dict[str, Any]] = write_public_artifact_atomic_v1,
) -> FinalizedScientificResultV3:
    """Freeze complete private/public scientific results and return only after PASS.

    The caller must already have completed all logical calls.  This function
    performs no evidence loading and no provider operation.
    """

    _require_hash(execution_commit, "execution commit", lengths=(40,))
    _require_hash(source_manifest_hash, "source manifest hash")
    _require_hash(authorization_hash, "authorization hash")
    _require_hash(configuration_fingerprint, "configuration fingerprint")
    if postcontact_integrity_status != "verified_unchanged":
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "post-contact integrity must be verified before result finalization"
        )
    authority = _require_authority_bindings(authority_bindings)
    if authority["r1d2_commit_a"] != execution_commit:
        raise TASK039E3RecoveryResultFinalizationV3Error("R1D2 Commit A binding differs")
    if authority["r1d2_source_manifest_hash"] != source_manifest_hash:
        raise TASK039E3RecoveryResultFinalizationV3Error("R1D2 source manifest binding differs")
    if authority["r2_authorization_hash"] != authorization_hash:
        raise TASK039E3RecoveryResultFinalizationV3Error("R2 authorization binding differs")
    source_hashes = normalize_plain_json_v1(scientific_source_hashes)
    if (
        not isinstance(source_hashes, dict)
        or not source_hashes
        or any(
            not isinstance(path, str)
            or not path
            or _require_hash(value, f"scientific source hash {path}") != value
            for path, value in source_hashes.items()
        )
    ):
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "scientific source hashes must be a non-empty closed hash mapping"
        )

    capability = _verified_input_artifact(capability_receipt, "capability receipt")
    if capability.get("gate_status") not in {"PASS", "pass"}:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "successful scientific finalization requires corrected capability PASS"
        )
    capability_binding = _verified_input_artifact(
        capability_provider_binding, "capability provider custody binding"
    )
    scientific_binding = _verified_input_artifact(
        scientific_provider_binding, "scientific provider custody binding"
    )
    for binding, expected_kind, expected_count in (
        (capability_binding, "recovery_capability", 1),
        (scientific_binding, "scientific_provider", None),
    ):
        if (
            binding.get("artifact_type")
            != "task039e3_r2_transactional_provider_binding_v3"
            or binding.get("ledger_kind") != expected_kind
            or binding.get("hash_chain_verified") is not True
            or binding.get("authoritative_head_verified") is not True
            or binding.get("orphan_records") != []
            or binding.get("pending_files") != []
            or (expected_count is not None and binding.get("record_count") != expected_count)
        ):
            raise TASK039E3RecoveryResultFinalizationV3Error(
                f"{expected_kind} transactional custody binding differs"
            )

    provider_documents = tuple(
        _mapping_record(item, "scientific provider") for item in scientific_provider_records
    )
    if any(document.get("logical_call_kind") != "scientific" for document in provider_documents):
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "scientific provider snapshot contains a non-scientific logical call"
        )
    proposal_documents = tuple(_mapping_record(item, "proposal-validity") for item in proposal_records)
    outcomes = tuple(_coerce_outcome(item) for item in outcome_records)
    direct = tuple(_coerce_direct(item) for item in direct_number_records)
    calls, scientific_calls = _validate_completed_science(outcomes, direct, typed_accounting)
    if len(provider_documents) != scientific_calls:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "scientific provider logical record count differs"
        )
    if scientific_binding.get("record_count") != scientific_calls:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "scientific provider custody binding count differs"
        )

    private_final_root, public_root = prepare_result_roots_v3(
        repository_root=repository_root,
        recovery_private_root=recovery_private_root,
        public_output_root=public_output_root,
        protected_private_roots=protected_private_roots,
    )
    outcome_documents = tuple(
        {**item.to_dict(), "artifact_hash": item.artifact_hash} for item in outcomes
    )
    direct_documents = tuple(
        {
            **item.__dict__,
            "sign_domain_violation_roles": list(item.sign_domain_violation_roles),
            "normalized_absolute_errors": (
                dict(item.normalized_absolute_errors)
                if item.normalized_absolute_errors is not None
                else None
            ),
        }
        for item in direct
    )
    private_inputs = {
        "scientific_provider": _private_snapshot_content(
            artifact_type="task039e3_r2_scientific_provider_ledger_v3",
            records=provider_documents,
            working_log_classification="transactional_provider_ledger_binding",
        ),
        "proposal_validity": _private_snapshot_content(
            artifact_type="task039e3_r2_proposal_validity_ledger_v3",
            records=proposal_documents,
            working_log_classification="non_authoritative_working_log",
        ),
        "construction_outcome": _private_snapshot_content(
            artifact_type="task039e3_r2_construction_outcome_ledger_v3",
            records=outcome_documents,
            working_log_classification="non_authoritative_working_log",
        ),
        "direct_number": _private_snapshot_content(
            artifact_type="task039e3_r2_direct_number_ledger_v3",
            records=direct_documents,
            working_log_classification="non_authoritative_working_log",
        ),
    }
    private_artifacts: dict[str, dict[str, Any]] = {}
    for key in ("scientific_provider", "proposal_validity", "construction_outcome", "direct_number"):
        private_artifacts[key] = artifact_writer(
            private_final_root / PRIVATE_ARTIFACT_NAMES_V3[key], private_inputs[key]
        )

    main_metrics = aggregate_construction_metrics_v1(outcomes)
    direct_raw = aggregate_direct_number_metrics_v1(direct)
    direct_summary = _direct_summary(direct_raw, direct)
    frozen_metrics_contract = PublicConstructionMetricsV1(
        provider_call_ledger_hash=private_artifacts["scientific_provider"]["artifact_hash"],
        proposal_ledger_hash=private_artifacts["proposal_validity"]["artifact_hash"],
        outcome_ledger_hash=private_artifacts["construction_outcome"]["artifact_hash"],
        main_metrics=main_metrics,
        direct_number_metrics=direct_summary,
        scientific_slot_count=scientific_calls,
    ).to_dict()

    provider_custody = finalize_public_artifact_v1(
        {
            "schema_version": "3.0.0",
            "artifact_type": "task039e3_r2_provider_custody_binding_v3",
            "task_id": TASK_ID,
            "provider": "openai",
            "model": EXACT_MODEL,
            "capability_provider_custody_binding_hash": capability_binding["artifact_hash"],
            "scientific_provider_custody_binding_hash": scientific_binding["artifact_hash"],
            "scientific_provider_ledger_snapshot_hash": private_artifacts["scientific_provider"]["artifact_hash"],
            "scientific_provider_record_count": scientific_calls,
            "capability_and_scientific_ledgers_separately_typed": True,
            "provider_hash_chains_verified": bool(
                capability_binding.get("hash_chain_verified", False)
                and scientific_binding.get("hash_chain_verified", False)
            ),
            "individual_proposals_public": False,
            "credential_persisted": False,
            "authorization_header_persisted": False,
        }
    )
    if not provider_custody["provider_hash_chains_verified"]:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "provider hash chains must verify before finalization"
        )

    private_bindings = finalize_public_artifact_v1(
        {
            "schema_version": "3.0.0",
            "artifact_type": "task039e3_r2_private_ledger_bindings_v3",
            "task_id": TASK_ID,
            "capability_provider_ledger_binding_hash": capability_binding["artifact_hash"],
            "scientific_provider_ledger_binding_hash": scientific_binding["artifact_hash"],
            "scientific_provider_ledger_snapshot_hash": private_artifacts["scientific_provider"]["artifact_hash"],
            "proposal_validity_ledger_hash": private_artifacts["proposal_validity"]["artifact_hash"],
            "construction_outcome_ledger_hash": private_artifacts["construction_outcome"]["artifact_hash"],
            "direct_number_ledger_hash": private_artifacts["direct_number"]["artifact_hash"],
            "provider_records": scientific_calls,
            "proposal_records": len(proposal_documents),
            "outcome_records": len(outcomes),
            "direct_number_records": len(direct),
            "authoritative_private_snapshots_finalized": True,
            "working_jsonl_authority": False,
            "private_contents_public": False,
            "storage_boundary": "outside_git_private",
        }
    )
    construction_metrics = finalize_public_artifact_v1(
        {
            "schema_version": "3.0.0",
            "artifact_type": "task039e3_r2_construction_metrics_v3",
            "task_id": TASK_ID,
            "status": SUCCESS_STATUS,
            "main_metrics": main_metrics,
            "provider_call_ledger_hash": private_artifacts["scientific_provider"]["artifact_hash"],
            "proposal_validity_ledger_hash": private_artifacts["proposal_validity"]["artifact_hash"],
            "outcome_ledger_hash": private_artifacts["construction_outcome"]["artifact_hash"],
            "scientific_slot_count": scientific_calls,
            "frozen_metrics_contract_hash": frozen_metrics_contract["artifact_hash"],
            "winner_selected": False,
        }
    )
    direct_metrics = finalize_public_artifact_v1(
        {
            "schema_version": "3.0.0",
            "artifact_type": "task039e3_r2_direct_number_metrics_v3",
            "task_id": TASK_ID,
            "relation_count": RELATION_COUNT,
            **direct_summary,
            "labels_used": False,
            "winner_selected": False,
        }
    )
    accounting = normalize_plain_json_v1(typed_accounting)
    summary = finalize_public_artifact_v1(
        {
            "schema_version": "3.0.0",
            "artifact_type": "task039e3_r2_execution_summary_v3",
            "task_id": TASK_ID,
            "status": SUCCESS_STATUS,
            "execution_code_commit": execution_commit,
            "relations_completed": RELATION_COUNT,
            "relations_skipped": 0,
            "t0_outcomes": RELATION_COUNT,
            "t1_outcomes": RELATION_COUNT,
            "t1b_outcomes": RELATION_COUNT,
            "t2_outcomes": RELATION_COUNT,
            "direct_number_results": RELATION_COUNT,
            "scientific_call_counts": calls,
            "scientific_calls": scientific_calls,
            "typed_accounting": accounting,
            "scientific_retries": 0,
            "cross_arm_leakage": False,
            "winner_selected": False,
            "rule_v2_authorized": False,
            "runtime_authority": False,
            "utility_evaluation_authorized": False,
        }
    )
    access = finalize_public_artifact_v1(
        {
            "schema_version": "3.0.0",
            "artifact_type": "task039e3_r2_data_access_audit_v3",
            "task_id": TASK_ID,
            "e1_private_evidence_accessed_after_capability_pass": True,
            "e1_private_evidence_modified": False,
            "historical_e3_private_root_modified": False,
            "hai_accessed": False,
            "train1_train2_train3_train4_reread": False,
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
        }
    )

    public_documents: dict[str, Mapping[str, Any]] = {
        "capability": capability,
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
        "capability",
        "provider_custody",
        "private_bindings",
        "construction_metrics",
        "direct_number_metrics",
        "execution_summary",
        "data_access_audit",
    ):
        written = artifact_writer(public_root / PUBLIC_ARTIFACT_NAMES_V3[key], public_documents[key])
        public_hashes[key] = written["artifact_hash"]
        write_order.append(key)

    receipt_content: dict[str, Any] = {
        "schema_version": "3.0.0",
        "artifact_type": "task039e3_r2_execution_receipt_v3",
        "task_id": TASK_ID,
        "status": SUCCESS_STATUS,
        "execution_code_commit": execution_commit,
        "source_manifest_hash": source_manifest_hash,
        "r2_authorization_hash": authorization_hash,
        "execution_configuration_fingerprint": configuration_fingerprint,
        "postcontact_integrity_status": postcontact_integrity_status,
        "e3_authorization_hash": E3_AUTHORIZATION_HASH,
        "e0_protocol_bundle_hash": E0_PROTOCOL_BUNDLE_HASH,
        "e1_materialization_result_hash": E1_MATERIALIZATION_RESULT_HASH,
        "e1_construction_cohort_hash": E1_CONSTRUCTION_EVIDENCE_COHORT_HASH,
        "e1_private_ledger_hash": E1_PRIVATE_LEDGER_HASH,
        "e2_protocol_bundle_hash": E2_PROTOCOL_BUNDLE_HASH,
        "execution_schedule_hash": EXECUTION_SCHEDULE_HASH,
        **authority,
        "capability_receipt_hash": public_hashes["capability"],
        "capability_provider_custody_binding_hash": capability_binding["artifact_hash"],
        "provider_custody_binding_hash": public_hashes["provider_custody"],
        "scientific_provider_ledger_hash": private_artifacts["scientific_provider"]["artifact_hash"],
        "proposal_validity_ledger_hash": private_artifacts["proposal_validity"]["artifact_hash"],
        "construction_outcome_ledger_hash": private_artifacts["construction_outcome"]["artifact_hash"],
        "direct_number_ledger_hash": private_artifacts["direct_number"]["artifact_hash"],
        "private_ledger_bindings_hash": public_hashes["private_bindings"],
        "construction_metrics_hash": public_hashes["construction_metrics"],
        "direct_number_metrics_hash": public_hashes["direct_number_metrics"],
        "execution_summary_hash": public_hashes["execution_summary"],
        "data_access_audit_hash": public_hashes["data_access_audit"],
        "typed_accounting": accounting,
        "scientific_source_hashes": source_hashes,
        "individual_proposals_public": False,
        "rule_v2_authorized": False,
        "runtime_authority": False,
        "utility_evaluation_authorized": False,
        "winner_selected": False,
    }
    receipt = finalize_public_artifact_v1(receipt_content)
    written_receipt = artifact_writer(
        public_root / PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"], receipt
    )
    write_order.append("execution_receipt")
    observed_receipt = json.loads(
        (public_root / PUBLIC_ARTIFACT_NAMES_V3["execution_receipt"]).read_text(encoding="utf-8")
    )
    verified_receipt = verify_public_artifact_v1(observed_receipt)
    if written_receipt != verified_receipt or verified_receipt.get("status") != SUCCESS_STATUS:
        raise TASK039E3RecoveryResultFinalizationV3Error(
            "durable final execution receipt verification failed"
        )
    public_hashes["execution_receipt"] = verified_receipt["artifact_hash"]
    return FinalizedScientificResultV3(
        status=SUCCESS_STATUS,
        public_artifact_hashes=public_hashes,
        private_artifact_hashes={
            key: document["artifact_hash"] for key, document in private_artifacts.items()
        },
        execution_receipt_hash=verified_receipt["artifact_hash"],
        public_artifact_order=tuple(write_order),
    )


__all__ = [
    "FinalizedScientificResultV3",
    "PRIVATE_ARTIFACT_NAMES_V3",
    "PUBLIC_ARTIFACT_NAMES_V3",
    "SUCCESS_STATUS",
    "TASK039E3RecoveryResultFinalizationV3Error",
    "finalize_successful_scientific_result_v3",
    "prepare_result_roots_v3",
    "provider_custody_binding_from_reconstruction_v3",
]
