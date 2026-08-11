"""Serialization-only recovery contracts for TASK-039D2.

This module has no HAI loader and performs no event, response, or confirmation
calculation.  It validates and serializes the already-frozen D2 private ledger.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Mapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    freeze_json,
    reject_unknown_fields,
    require_sha256,
    stable_hash_v1,
    thaw_json,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    CANDIDATE_COHORT_HASH,
    CANDIDATE_IDENTITY_LIST_HASH,
    DATASET_MANIFEST_HASH,
    PROCESS_ID,
    CandidateProvenanceAnalysisViewV1,
    verify_self_hash_v1,
)


TASK_ID = "TASK-039D2R"
RECOVERY_STATUS = "passed_task039d2r_result_contract_recovery"
SCIENTIFIC_STATUS = "passed_task039d2_one_way_train3_confirmation"
DEFECT_CLASSIFICATION = "non_scientific_result_contract_schema_defect"
ORIGINAL_COMMIT_A = "5524262d8a666093f948f7f01491b4a0b03e568e"
ORIGINAL_BRANCH = "origin/task-039d2-train3-confirmation"
ORIGINAL_FAILED_STATUS = "failed_task039d2_result_contract"
AUDIT_COMMIT = "301fb636b6944e2d2d86be4646605a3d38585165"
PREP_COMMIT = "826820aed3bb6c4205977454c00a9b618a7b6b69"
D2_AUTHORIZATION_HASH = "791f985afdc5f16b5c6b5aec4eb7bcefe1e39bc3b0f262cc0ff56c7ff5071f25"
D0_PROTOCOL_BUNDLE_HASH = "888e3d642eba6f8ad8784d428bc4b27d7db7592d34779ba9a1f817860d76e1eb"
CONFIRMATION_POLICY_HASH = "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27"
METHOD_COMPARISON_POLICY_HASH = "0ccc7a97a5e9b3fe1e5a8a54828ec8f8f7e6482c62eb63f7df62d804c8cae39e"
D1_FIT_RESULT_HASH = "a2767945ef3cec5fa80c3e131b98fdc8a1eeecaa69a97461988d8da90a4e06d3"
D1_PAIR_SUMMARY_HASH = "a466057faa20eacd0692b6a9c19fbbb5b8968135ba4c018310a076aa0393d4f2"
D1_ARM_SUMMARY_HASH = "6589930085ed0d5d87224ef9da88984b1d52d5e2c7bd1e8b295539b6d0da15e8"
D1_SOURCE_LEDGER_HASH = "3eb6ff199dbc67b183d35a804754e557bdfa869a899c754e551cd77e8dcfb304"
D1_TARGET_LEDGER_HASH = "f36f4b424c85b228043f9685a22a25c73d6b165e28714b627cf51e8bbb77f96e"
D1_DIRECTIONAL_LEDGER_HASH = "e372d7ccf4a7dde5f7ccd91049cc73b443b3b19a3a0c563f451aea50e8faddc7"
PROVENANCE_ANALYSIS_VIEW_HASH = "7ab92318611dd7d0252c763c4099a7ee69f3dbab3132308254aeb92f8af2e115"
PRIVATE_D2_LEDGER_HASH = "d349421ae9a866b924c329dcb2546088466866e09f45851ec5d18090509dc062"
PRIVATE_D2_LEDGER_NAME = "TASK039D2_DIRECTIONAL_CONFIRMATION_LEDGER.json"
PRIVATE_D1_SOURCE_NAME = "TASK-039D1_SOURCE_PARAMETER_LEDGER.json"
PRIVATE_D1_TARGET_NAME = "TASK-039D1_TARGET_PARAMETER_LEDGER.json"
PRIVATE_D1_DIRECTIONAL_NAME = "TASK-039D1_DIRECTIONAL_FIT_LEDGER.json"
TRAIN3_RELATIVE_PATH = "hai-23.05/hai-train3.csv"
TRAIN3_SHA256 = "bfcec2dc05adea103e7491546b0e28268faaa26d3cc717d10f4595c94b81e85d"
TRAIN3_BYTE_SIZE = 72774793
TRAIN3_ROW_COUNT = 126000
TRAIN3_HEADER_SHA256 = "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a"

SCIENTIFIC_SOURCE_PATHS = (
    "src/paperworks/profiling/task039d2_real_execution_v1.py",
    "src/paperworks/profiling/task039d2_confirmation_v1.py",
    "src/paperworks/profiling/task039d1_execution_optimization_v1.py",
    "src/paperworks/v6/relation_profiling_protocol_v1.py",
)

COMMIT_A_SCIENTIFIC_SOURCE_HASHES = {
    "src/paperworks/profiling/task039d2_real_execution_v1.py": "88b29be3ec7d77b6004f2974140f8cd3cfbe6316cb9c5de6dc35cc0301b4c1de",
    "src/paperworks/profiling/task039d2_confirmation_v1.py": "dda2151d633aa16740fff1e5c133d83211681da460a08839960fc55d6e1c7c4b",
    "src/paperworks/profiling/task039d1_execution_optimization_v1.py": "756d5c1ec7e506420e8cb49f5aa7827ba9ecd966f4bb18bd56271b571ee7e06e",
    "src/paperworks/v6/relation_profiling_protocol_v1.py": "ba7a7ea29eb0d68077a51442691d201915470d16dca751dff3c214a7ead3c529",
}


class TASK039D2RecoveryError(ValueError):
    """Raised when custody or serialization-only recovery fails closed."""


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = thaw_json(freeze_json(content))
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


def verify_recovery_self_hash_v1(document: Mapping[str, Any]) -> str:
    supplied = str(document.get("artifact_hash", ""))
    require_sha256(supplied, "artifact_hash")
    observed = stable_hash_v1({key: value for key, value in document.items() if key != "artifact_hash"})
    if supplied != observed:
        raise TASK039D2RecoveryError("recovery artifact self-hash mismatch")
    return observed


verify_d2_self_hash_v1 = verify_recovery_self_hash_v1


def load_json_object_v1(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TASK039D2RecoveryError(f"required artifact unavailable: {path.name}") from exc
    if not isinstance(value, dict):
        raise TASK039D2RecoveryError(f"artifact must be an object: {path.name}")
    return value


def write_public_json_v1(path: Path, document: Mapping[str, Any]) -> None:
    serialized = json.dumps(thaw_json(freeze_json(document)), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    if re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]", serialized) or "file://" in serialized:
        raise TASK039D2RecoveryError("absolute local path is prohibited in public recovery artifacts")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8", newline="\n")


def validate_exact_four_source_hash_map_v1(source_hashes: Mapping[str, Any]) -> dict[str, str]:
    if set(source_hashes) != set(SCIENTIFIC_SOURCE_PATHS) or len(source_hashes) != 4:
        raise TASK039D2RecoveryError("scientific_source_hashes must contain the exact four frozen sources")
    normalized = {str(path): str(source_hashes[path]) for path in SCIENTIFIC_SOURCE_PATHS}
    for path, digest in normalized.items():
        require_sha256(digest, f"scientific_source_hashes[{path}]")
    return normalized


def bind_exact_four_source_hash_schema_v1(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Correct only the receipt's fixed four-key source-hash object."""

    result = copy.deepcopy(dict(schema))
    if result.get("properties", {}).get("artifact_type", {}).get("const") != "task039d2_real_execution_receipt_v1":
        raise TASK039D2RecoveryError("receipt schema identity mismatch")
    result["properties"]["scientific_source_hashes"] = {
        "type": "object",
        "additionalProperties": False,
        "required": list(SCIENTIFIC_SOURCE_PATHS),
        "properties": {
            path: {"type": "string", "pattern": "^[a-f0-9]{64}$"}
            for path in SCIENTIFIC_SOURCE_PATHS
        },
    }
    return result


def git_blob_sha256_v1(repository_root: Path, commit: str, relative_path: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{40}", commit) or relative_path not in SCIENTIFIC_SOURCE_PATHS:
        raise TASK039D2RecoveryError("invalid scientific source binding")
    result = subprocess.run(
        ["git", "-C", str(repository_root), "show", f"{commit}:{relative_path}"],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise TASK039D2RecoveryError("failed_task039d2r_scientific_source_changed")
    return hashlib.sha256(result.stdout).hexdigest()


def verify_scientific_sources_unchanged_v1(repository_root: Path, commit: str) -> dict[str, str]:
    observed = {
        path: git_blob_sha256_v1(repository_root, commit, path)
        for path in SCIENTIFIC_SOURCE_PATHS
    }
    if observed != COMMIT_A_SCIENTIFIC_SOURCE_HASHES:
        raise TASK039D2RecoveryError("failed_task039d2r_scientific_source_changed")
    return observed


@dataclass(frozen=True)
class RecoveryDirectionalRelationV1:
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    d1_selected_horizon_seconds: int
    source_parameter_record_hash: str
    target_parameter_record_hash: str
    d1_directional_record_hash: str
    artifact_hash: str


@dataclass(frozen=True)
class RecoveryD1PrivateInputsV1:
    source_document: Mapping[str, Any]
    target_document: Mapping[str, Any]
    directional_document: Mapping[str, Any]
    relations: tuple[RecoveryDirectionalRelationV1, ...]


def load_d1_private_inputs_for_recovery_v1(private_root: Path) -> RecoveryD1PrivateInputsV1:
    expected_names = {PRIVATE_D1_SOURCE_NAME, PRIVATE_D1_TARGET_NAME, PRIVATE_D1_DIRECTIONAL_NAME}
    if {path.name for path in private_root.iterdir() if path.is_file()} != expected_names:
        raise TASK039D2RecoveryError("failed_task039d2_private_input_binding")
    source = load_json_object_v1(private_root / PRIVATE_D1_SOURCE_NAME)
    target = load_json_object_v1(private_root / PRIVATE_D1_TARGET_NAME)
    directional = load_json_object_v1(private_root / PRIVATE_D1_DIRECTIONAL_NAME)
    expected = (
        (source, D1_SOURCE_LEDGER_HASH, 12, "task039d1_source_parameter_ledger_v1"),
        (target, D1_TARGET_LEDGER_HASH, 12, "task039d1_target_parameter_ledger_v1"),
        (directional, D1_DIRECTIONAL_LEDGER_HASH, 94, "task039d1_directional_fit_ledger_v1"),
    )
    for document, digest, count, artifact_type in expected:
        if verify_recovery_self_hash_v1(document) != digest or document.get("record_count") != count or document.get("artifact_type") != artifact_type:
            raise TASK039D2RecoveryError("failed_task039d2_private_input_binding")
        for record in document["records"]:
            verify_recovery_self_hash_v1(record)
    source_hashes = {record["source"]: record["artifact_hash"] for record in source["records"]}
    target_hashes = {record["target"]: record["artifact_hash"] for record in target["records"]}
    selected = [record for record in directional["records"] if record.get("fit_result") == "fit_supported"]
    if len(source_hashes) != 12 or len(target_hashes) != 12 or len(selected) != 45:
        raise TASK039D2RecoveryError("failed_task039d2_private_input_binding")
    relations = []
    for record in selected:
        source_hash = source_hashes.get(record["source"])
        target_hash = target_hashes.get(record["target"])
        if (
            source_hash is None or target_hash is None
            or record.get("source_parameter_ref") != source_hash
            or record.get("target_parameter_ref") != target_hash
            or record.get("selected_target_direction") not in {"increase", "decrease"}
            or record.get("selected_horizon_seconds") not in {1, 5, 10, 30, 60}
            or record.get("lower_ranked_fallback_used") is not False
            or record.get("candidate_arm_evidence_visible") is not False
        ):
            raise TASK039D2RecoveryError("failed_task039d2_private_input_binding")
        relation_content = {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "confirmable_directional_relation_v1",
            "source": record["source"],
            "source_step_direction": record["source_step_direction"],
            "target": record["target"],
            "target_response_direction": record["selected_target_direction"],
            "d1_selected_horizon_seconds": record["selected_horizon_seconds"],
            "source_noise_scale_reference": source_hash,
            "source_threshold_reference": source_hash,
            "source_stability_tolerance_reference": source_hash,
            "target_scale_reference": target_hash,
            "d1_directional_record_hash": record["artifact_hash"],
        }
        relations.append(RecoveryDirectionalRelationV1(
            source=record["source"], source_step_direction=record["source_step_direction"],
            target=record["target"], target_response_direction=record["selected_target_direction"],
            d1_selected_horizon_seconds=record["selected_horizon_seconds"],
            source_parameter_record_hash=source_hash, target_parameter_record_hash=target_hash,
            d1_directional_record_hash=record["artifact_hash"], artifact_hash=stable_hash_v1(relation_content),
        ))
    if len({item.d1_directional_record_hash for item in relations}) != 45:
        raise TASK039D2RecoveryError("failed_task039d2_private_input_binding")
    return RecoveryD1PrivateInputsV1(freeze_json(source), freeze_json(target), freeze_json(directional), tuple(relations))


@dataclass(frozen=True)
class FrozenD2LedgerValidationV1:
    ledger: Mapping[str, Any]
    confirmed_count: int
    conflict_count: int


def validate_frozen_d2_ledger_v1(
    ledger: Mapping[str, Any], *, expected_d1_relations: Sequence[Any],
) -> FrozenD2LedgerValidationV1:
    if verify_d2_self_hash_v1(ledger) != PRIVATE_D2_LEDGER_HASH:
        raise TASK039D2RecoveryError("blocked_task039d2r_private_ledger_custody")
    if (
        ledger.get("artifact_type") != "task039d2_directional_confirmation_ledger_v1"
        or ledger.get("record_count") != 45
        or len(ledger.get("records", ())) != 45
        or ledger.get("confirmation_policy_hash") != CONFIRMATION_POLICY_HASH
        or ledger.get("d1_directional_ledger_hash") != D1_DIRECTIONAL_LEDGER_HASH
        or ledger.get("raw_train3_rows_included") is not False
        or ledger.get("raw_windows_included") is not False
        or ledger.get("event_timestamps_included") is not False
        or ledger.get("absolute_paths_included") is not False
    ):
        raise TASK039D2RecoveryError("blocked_task039d2r_private_ledger_custody")
    expected = {relation.d1_directional_record_hash: relation for relation in expected_d1_relations}
    records = {record.get("d1_directional_record_hash"): record for record in ledger["records"]}
    if len(expected) != 45 or len(records) != 45 or set(records) != set(expected):
        raise TASK039D2RecoveryError("blocked_task039d2r_private_ledger_custody")
    confirmed = 0
    for digest, record in records.items():
        verify_d2_self_hash_v1(record)
        relation = expected[digest]
        if (
            record.get("source") != relation.source
            or record.get("source_step_direction") != relation.source_step_direction
            or record.get("target") != relation.target
            or record.get("target_response_direction") != relation.target_response_direction
            or record.get("selected_horizon_seconds") != relation.d1_selected_horizon_seconds
            or record.get("relation_binding_hash") != relation.artifact_hash
            or record.get("source_parameter_record_hash") != relation.source_parameter_record_hash
            or record.get("target_parameter_record_hash") != relation.target_parameter_record_hash
            or record.get("confirmation_status") not in {"calibration_confirmed", "calibration_conflict"}
            or record.get("fit_parameters_reused_without_retuning") is not True
            or any(record.get(field) is not False for field in (
                "parameter_retuning_used", "alternative_horizon_search_used",
                "opposite_direction_search_used", "lower_ranked_fallback_used",
                "candidate_provenance_visible",
            ))
        ):
            raise TASK039D2RecoveryError("blocked_task039d2r_private_ledger_custody")
        confirmed += record["confirmation_status"] == "calibration_confirmed"
    if confirmed != 42:
        raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")
    return FrozenD2LedgerValidationV1(freeze_json(ledger), confirmed, 45 - confirmed)


@dataclass(frozen=True)
class _RecoveryArtifact:
    payload: Mapping[str, Any]
    ARTIFACT_TYPE: ClassVar[str] = ""
    FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        reject_unknown_fields(self.payload, self.FIELDS, self.ARTIFACT_TYPE)
        if set(self.payload) != set(self.FIELDS):
            raise TASK039D2RecoveryError(f"{self.ARTIFACT_TYPE} fields are incomplete")
        object.__setattr__(self, "payload", freeze_json(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return _self_hashed({
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            **thaw_json(self.payload),
        })

    @classmethod
    def from_dict(cls, document: Mapping[str, Any]) -> "_RecoveryArtifact":
        verify_recovery_self_hash_v1(document)
        if document.get("schema_version") != V6_FOUNDATION_SCHEMA_VERSION or document.get("artifact_type") != cls.ARTIFACT_TYPE:
            raise TASK039D2RecoveryError("recovery artifact identity mismatch")
        return cls({key: value for key, value in document.items() if key not in {"schema_version", "artifact_type", "artifact_hash"}})


def _artifact_class(name: str, artifact_type: str, fields: Sequence[str]) -> type[_RecoveryArtifact]:
    return type(name, (_RecoveryArtifact,), {"ARTIFACT_TYPE": artifact_type, "FIELDS": frozenset(fields)})


TASK039D2FailedRunCustodyV1 = _artifact_class(
    "TASK039D2FailedRunCustodyV1", "task039d2_failed_run_custody_v1",
    ("task_id", "status", "defect_classification", "original_execution_commit_a", "original_branch",
     "original_branch_tip", "synthetic_prep_merge_commit", "original_terminal_status", "original_result_commit_b",
     "private_ledger_hash", "private_ledger_record_count", "scientific_computation_completed_before_schema_failure",
     "result_contract_validation_failure_stage", "schema_defect_identifier", "train3_accessed_by_original_run",
     "train1_train2_feature_value_refit_used", "scientific_source_modified_after_train3_read",
     "original_public_outputs_authoritative", "private_scientific_ledger_authoritative_custody_candidate",
     "d2_authorization_hash", "d1_directional_ledger_hash", "confirmation_policy_hash",
     "scientific_source_commit_blob_hashes", "machine_verifiable_evidence", "claim_boundary"),
)

TASK039D2RDataAccessAuditV1 = _artifact_class(
    "TASK039D2RDataAccessAuditV1", "task039d2r_data_access_audit_v1",
    ("task_id", "status", "dataset_manifest_id", "process", "authorized_original_file", "immutable_file_identity",
     "original_scientific_run", "recovery_finalization", "prohibited_access_count", "absolute_local_paths_persisted"),
)

TASK039D2ResultContractRecoveryReceiptV1 = _artifact_class(
    "TASK039D2ResultContractRecoveryReceiptV1", "task039d2_result_contract_recovery_receipt_v1",
    ("task_id", "status", "defect_classification", "original_d2_commit_a", "original_failed_status",
     "original_private_d2_ledger_hash", "original_private_ledger_validated", "frozen_scientific_source_hashes",
     "scientific_source_hash_basis", "scientific_sources_unchanged", "result_contract_recovery_commit",
     "failed_run_custody_hash", "corrected_receipt_schema_hash", "schema_changed", "scientific_code_changed",
     "train3_reread", "hai_values_accessed_during_recovery", "scientific_outcomes_recomputed_from_hai",
     "public_summaries_deterministically_reconstructed_from_frozen_ledger", "four_key_receipt_schema_validated",
     "directional_summary_hash", "pair_summary_hash", "arm_summary_hash", "data_access_audit_hash",
     "execution_receipt_hash", "d2_result_hash", "d2_result_authoritative_after_recovery",
     "independent_d2_audit_still_required", "winner_selected", "rule_v2_authorized", "recommended_next_task"),
)

RECOVERY_ARTIFACT_CLASSES = (
    TASK039D2FailedRunCustodyV1,
    TASK039D2RDataAccessAuditV1,
    TASK039D2ResultContractRecoveryReceiptV1,
)
RECOVERY_CLASS_BY_TYPE = {item.ARTIFACT_TYPE: item for item in RECOVERY_ARTIFACT_CLASSES}


def build_failed_run_custody_v1(
    *, original_branch_tip: str, source_hashes: Mapping[str, str], ledger_validation: FrozenD2LedgerValidationV1,
) -> dict[str, Any]:
    if original_branch_tip != ORIGINAL_COMMIT_A or ledger_validation.confirmed_count != 42 or ledger_validation.conflict_count != 3:
        raise TASK039D2RecoveryError("blocked_task039d2r_private_ledger_custody")
    return TASK039D2FailedRunCustodyV1({
        "task_id": TASK_ID,
        "status": "verified_task039d2_failed_run_custody",
        "defect_classification": DEFECT_CLASSIFICATION,
        "original_execution_commit_a": ORIGINAL_COMMIT_A,
        "original_branch": ORIGINAL_BRANCH,
        "original_branch_tip": original_branch_tip,
        "synthetic_prep_merge_commit": PREP_COMMIT,
        "original_terminal_status": ORIGINAL_FAILED_STATUS,
        "original_result_commit_b": None,
        "private_ledger_hash": PRIVATE_D2_LEDGER_HASH,
        "private_ledger_record_count": 45,
        "scientific_computation_completed_before_schema_failure": True,
        "result_contract_validation_failure_stage": "post_scientific_public_execution_receipt_schema_validation",
        "schema_defect_identifier": "scientific_source_hashes_example_key_undercoverage_v1",
        "train3_accessed_by_original_run": True,
        "train1_train2_feature_value_refit_used": False,
        "scientific_source_modified_after_train3_read": False,
        "original_public_outputs_authoritative": False,
        "private_scientific_ledger_authoritative_custody_candidate": True,
        "d2_authorization_hash": D2_AUTHORIZATION_HASH,
        "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
        "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
        "scientific_source_commit_blob_hashes": validate_exact_four_source_hash_map_v1(source_hashes),
        "machine_verifiable_evidence": {
            "original_branch_tip_equals_commit_a": True,
            "commit_a_has_no_result_commit_b": True,
            "private_ledger_self_hash_valid": True,
            "all_45_private_record_hashes_valid": True,
            "all_45_d1_directional_references_exact": True,
            "commit_a_schema_runtime_cardinality_mismatch_reproduced": True,
        },
        "claim_boundary": "custody evidence for serialization recovery; not an independent scientific audit",
    }).to_dict()


def build_recovery_data_access_audit_v1() -> dict[str, Any]:
    return TASK039D2RDataAccessAuditV1({
        "task_id": TASK_ID,
        "status": "passed_task039d2r_no_reread_data_boundary",
        "dataset_manifest_id": DATASET_MANIFEST_HASH,
        "process": PROCESS_ID,
        "authorized_original_file": TRAIN3_RELATIVE_PATH,
        "immutable_file_identity": {
            "relative_path": TRAIN3_RELATIVE_PATH,
            "sha256": TRAIN3_SHA256,
            "byte_size": TRAIN3_BYTE_SIZE,
            "row_count": TRAIN3_ROW_COUNT,
            "header_sha256": TRAIN3_HEADER_SHA256,
        },
        "original_scientific_run": {
            "train3_accessed": True,
            "train1_feature_values_accessed": False,
            "train2_feature_values_accessed": False,
            "train4_accessed": False,
            "test_accessed": False,
            "labels_accessed": False,
            "attacks_accessed": False,
            "br2_pair_results_accessed": False,
            "d1_private_ledgers_accessed": True,
            "d1_private_ledgers_modified": False,
            "candidate_provenance_visible_during_confirmation": False,
        },
        "recovery_finalization": {
            "train3_accessed": False,
            "train3_reread": False,
            "hai_feature_values_accessed": False,
            "train1_train2_train4_test_labels_attacks_accessed": False,
            "frozen_d2_private_ledger_read": True,
            "d1_private_ledgers_read_for_binding_only": True,
            "candidate_provenance_loaded_after_outcomes_frozen": True,
        },
        "prohibited_access_count": 0,
        "absolute_local_paths_persisted": False,
    }).to_dict()


def build_directional_summary_from_frozen_ledger_v1(ledger: Mapping[str, Any]) -> dict[str, Any]:
    verify_recovery_self_hash_v1(ledger)
    relations = [{
        "source": record["source"], "source_step_direction": record["source_step_direction"],
        "target": record["target"], "target_response_direction": record["target_response_direction"],
        "selected_horizon_seconds": record["selected_horizon_seconds"],
        "d1_directional_record_hash": record["d1_directional_record_hash"],
        "confirmation_status": record["confirmation_status"],
        "private_confirmation_record_hash": record["artifact_hash"],
    } for record in ledger["records"]]
    confirmed = sum(item["confirmation_status"] == "calibration_confirmed" for item in relations)
    return _self_hashed({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039d2_directional_confirmation_summary_v1",
        "task_id": "TASK-039D2", "status": "frozen_task039d2_directional_confirmation_summary",
        "authorization_hash": D2_AUTHORIZATION_HASH, "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
        "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH, "input_relation_count": 45,
        "confirmed_directional_count": confirmed, "conflict_directional_count": 45 - confirmed,
        "relations": relations, "private_ledger_hash": PRIVATE_D2_LEDGER_HASH,
        "private_ledger_record_count": 45, "private_ledger_storage_boundary": "outside_git",
        "private_ledger_contents_public": False, "parameter_retuning_used": False,
        "alternative_horizon_search_used": False, "opposite_direction_search_used": False,
        "lower_ranked_fallback_used": False, "candidate_provenance_visible_during_confirmation": False,
    })


def build_pair_summary_from_frozen_ledger_v1(
    *, d1_pair_summary: Mapping[str, Any], directional_summary: Mapping[str, Any],
) -> dict[str, Any]:
    if verify_recovery_self_hash_v1(d1_pair_summary) != D1_PAIR_SUMMARY_HASH:
        raise TASK039D2RecoveryError("failed_task039d2_private_input_binding")
    verify_recovery_self_hash_v1(directional_summary)
    directions: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for relation in directional_summary["relations"]:
        directions.setdefault((relation["source"], relation["target"]), []).append(relation)
    pair_records = []
    for item in d1_pair_summary["pair_outcomes"]:
        pair = (item["source"], item["target"])
        evaluated = directions.get(pair, [])
        d1_supported = item["pair_fit_status"] == "fit_supported_pair"
        confirmed = any(record["confirmation_status"] == "calibration_confirmed" for record in evaluated)
        if d1_supported != bool(evaluated):
            raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")
        pair_records.append({
            "source": pair[0], "target": pair[1], "d1_fit_supported_pair": d1_supported,
            "d2_evaluated_direction_count": len(evaluated),
            "has_d2_confirmed_directional_relation": confirmed,
        })
    confirmed_pairs = sum(item["has_d2_confirmed_directional_relation"] for item in pair_records)
    return _self_hashed({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039d2_pair_confirmation_summary_v1",
        "task_id": "TASK-039D2", "status": "frozen_task039d2_pair_confirmation_summary",
        "d1_pair_summary_hash": D1_PAIR_SUMMARY_HASH,
        "directional_confirmation_summary_hash": directional_summary["artifact_hash"],
        "candidate_count": 47, "d1_fit_supported_pair_count": 25, "d1_fit_unsupported_pair_count": 22,
        "pairs_with_confirmed_direction_count": confirmed_pairs,
        "d1_supported_pairs_without_confirmed_direction_count": 25 - confirmed_pairs,
        "pair_records": pair_records, "outcomes_frozen_before_provenance_join": True,
    })


def load_provenance_after_recovery_outcomes_frozen_v1(
    *, provenance_path: Path, directional_path: Path, pair_path: Path,
    expected_directional_hash: str, expected_pair_hash: str,
) -> dict[str, Any]:
    for path, digest in ((directional_path, expected_directional_hash), (pair_path, expected_pair_hash)):
        if not path.is_file() or verify_recovery_self_hash_v1(load_json_object_v1(path)) != digest:
            raise TASK039D2RecoveryError("failed_task039d2_arm_blindness")
    provenance = load_json_object_v1(provenance_path)
    verify_self_hash_v1(provenance)
    if provenance.get("artifact_hash") != PROVENANCE_ANALYSIS_VIEW_HASH:
        raise TASK039D2RecoveryError("failed_task039d2_arm_blindness")
    CandidateProvenanceAnalysisViewV1.from_dict(provenance)
    return provenance


def build_arm_summary_from_frozen_ledger_v1(
    *, d1_arm_summary: Mapping[str, Any], pair_summary: Mapping[str, Any],
    directional_summary: Mapping[str, Any], provenance: Mapping[str, Any],
) -> dict[str, Any]:
    if verify_recovery_self_hash_v1(d1_arm_summary) != D1_ARM_SUMMARY_HASH:
        raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")
    pair_by_key = {(item["source"], item["target"]): item for item in pair_summary["pair_records"]}
    direction_by_pair: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for item in directional_summary["relations"]:
        direction_by_pair.setdefault((item["source"], item["target"]), []).append(item)
    provenance_by_key = {(item["source"], item["target"]): item for item in provenance["candidates"]}
    if set(pair_by_key) != set(provenance_by_key) or len(pair_by_key) != 47:
        raise TASK039D2RecoveryError("failed_task039d2_arm_blindness")
    d1_fit = {item["arm"]: item for item in d1_arm_summary["arms"]}
    expected_fit = {"META": (16, 29), "STAT": (17, 33), "GDN": (5, 7)}
    arms = []
    for arm in ("META", "STAT", "GDN"):
        arm_pairs = [pair for pair, item in provenance_by_key.items() if arm in item["origin_arms"]]
        if len(arm_pairs) != 20 or (d1_fit[arm]["pair_fit_supported_count"], d1_fit[arm]["directional_fit_supported_count"]) != expected_fit[arm]:
            raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")
        confirmed_pairs = [pair for pair in arm_pairs if pair_by_key[pair]["has_d2_confirmed_directional_relation"]]
        confirmed_directions = [item for pair in arm_pairs for item in direction_by_pair.get(pair, ()) if item["confirmation_status"] == "calibration_confirmed"]
        sources = {item["source"] for item in confirmed_directions}
        targets = {item["target"] for item in confirmed_directions}
        fit_pairs, fit_directions = expected_fit[arm]
        arms.append({
            "arm": arm, "top20_pair_count": 20, "d1_fit_supported_pair_count": fit_pairs,
            "d1_pair_fit_support_yield": fit_pairs / 20.0, "d1_directional_fit_supported_count": fit_directions,
            "d2_confirmed_pair_count": len(confirmed_pairs), "confirmed_relation_yield_at_20": len(confirmed_pairs) / 20.0,
            "pair_fit_to_confirmation_transfer": len(confirmed_pairs) / fit_pairs if fit_pairs else 0.0,
            "directional_confirmation_count": len(confirmed_directions),
            "directional_transfer": len(confirmed_directions) / fit_directions if fit_directions else 0.0,
            "distinct_confirmed_source_count": len(sources), "distinct_confirmed_source_coverage_at_20": len(sources) / 12.0,
            "distinct_confirmed_target_count": len(targets), "distinct_confirmed_target_coverage_at_20": len(targets) / 12.0,
        })
    confirmed_pairs = [pair for pair, item in pair_by_key.items() if item["has_d2_confirmed_directional_relation"]]
    categories = {name: [] for name in ("META_only", "STAT_only", "GDN_only", "META_STAT_only", "META_GDN_only", "STAT_GDN_only", "all_three")}
    name_by_arms = {
        ("META",): "META_only", ("STAT",): "STAT_only", ("GDN",): "GDN_only",
        ("META", "STAT"): "META_STAT_only", ("META", "GDN"): "META_GDN_only",
        ("STAT", "GDN"): "STAT_GDN_only", ("META", "STAT", "GDN"): "all_three",
    }
    for pair in confirmed_pairs:
        origin = tuple(arm for arm in ("META", "STAT", "GDN") if arm in provenance_by_key[pair]["origin_arms"])
        categories[name_by_arms[origin]].append({"source": pair[0], "target": pair[1]})
    overlap = {name: {"count": len(items), "pairs": items} for name, items in categories.items()}
    overlap["confirmed_union_count"] = len(confirmed_pairs)
    overlap["shared_by_exactly_two_count"] = sum(len(categories[name]) for name in ("META_STAT_only", "META_GDN_only", "STAT_GDN_only"))
    return _self_hashed({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039d2_arm_confirmation_summary_v1",
        "task_id": "TASK-039D2", "status": "descriptive_task039d2_arm_confirmation_summary",
        "method_comparison_policy_hash": METHOD_COMPARISON_POLICY_HASH,
        "pair_confirmation_summary_hash": pair_summary["artifact_hash"],
        "provenance_analysis_view_hash": PROVENANCE_ANALYSIS_VIEW_HASH,
        "primary_k": 20, "arms": arms, "confirmed_pair_overlap": overlap,
        "same_pair_same_d2_outcome_across_all_origin_arms": True,
        "provenance_joined_after_outcomes_frozen": True, "winner_selected": False,
        "claim_boundary": "one-way train3 confirmation metrics; no candidate-method winner",
    })


def build_result_from_frozen_ledger_v1(
    *, directional: Mapping[str, Any], pair: Mapping[str, Any], arm: Mapping[str, Any],
    access: Mapping[str, Any],
) -> dict[str, Any]:
    return _self_hashed({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039d2_result_v1", "task_id": "TASK-039D2", "status": SCIENTIFIC_STATUS,
        "authorization_hash": D2_AUTHORIZATION_HASH, "d0_protocol_bundle_hash": D0_PROTOCOL_BUNDLE_HASH,
        "confirmation_policy_hash": CONFIRMATION_POLICY_HASH, "method_comparison_policy_hash": METHOD_COMPARISON_POLICY_HASH,
        "candidate_cohort_hash": CANDIDATE_COHORT_HASH, "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH,
        "d1_fit_result_hash": D1_FIT_RESULT_HASH, "d1_pair_summary_hash": D1_PAIR_SUMMARY_HASH,
        "d1_source_ledger_hash": D1_SOURCE_LEDGER_HASH, "d1_target_ledger_hash": D1_TARGET_LEDGER_HASH,
        "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH, "input_directional_relation_count": 45,
        "supported_pair_context_count": 25, "confirmed_directional_count": directional["confirmed_directional_count"],
        "conflict_directional_count": directional["conflict_directional_count"],
        "pairs_with_confirmed_direction_count": pair["pairs_with_confirmed_direction_count"],
        "directional_confirmation_summary_hash": directional["artifact_hash"],
        "pair_confirmation_summary_hash": pair["artifact_hash"], "arm_confirmation_summary_hash": arm["artifact_hash"],
        "data_access_audit_hash": access["artifact_hash"], "private_confirmation_ledger_hash": PRIVATE_D2_LEDGER_HASH,
        "parameter_retuning_used": False, "alternative_horizon_search_used": False,
        "opposite_direction_search_used": False, "lower_ranked_fallback_used": False,
        "winner_selected": False, "rule_v2_authorized": False, "agent_authorized": False,
        "runtime_authority": False,
        "claim_boundary": "one-way train3 calibration confirmation; not causality, rule validity, or anomaly performance",
    })


def build_execution_receipt_from_frozen_ledger_v1(
    *, scientific_source_hashes: Mapping[str, str], directional: Mapping[str, Any], pair: Mapping[str, Any],
    arm: Mapping[str, Any], result: Mapping[str, Any], access: Mapping[str, Any],
) -> dict[str, Any]:
    return _self_hashed({
        "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
        "artifact_type": "task039d2_real_execution_receipt_v1", "task_id": "TASK-039D2", "status": SCIENTIFIC_STATUS,
        "execution_code_commit": ORIGINAL_COMMIT_A, "synthetic_prep_merge_commit": "0f4fa325e125abf15741e76603d989105c8ff92e",
        "audit_commit": AUDIT_COMMIT, "authorization_hash": D2_AUTHORIZATION_HASH,
        "scientific_source_hashes": validate_exact_four_source_hash_map_v1(scientific_source_hashes),
        "execution_phase_order": [
            "1_validate_d2_authorization", "2_validate_d1_private_ledgers", "3_construct_45_arm_blind_relations",
            "4_open_train3", "5_extract_all_source_events", "6_freeze_all_source_isolation",
            "7_evaluate_45_one_way_confirmations", "8_freeze_private_confirmation_ledger",
            "9_freeze_public_directional_and_pair_outcomes", "10_load_candidate_provenance",
            "11_calculate_candidate_method_metrics",
        ],
        "outcomes_frozen_before_provenance_join": True, "scientific_source_changed_after_first_train3_read": False,
        "private_ledger_hash": PRIVATE_D2_LEDGER_HASH, "directional_summary_hash": directional["artifact_hash"],
        "pair_summary_hash": pair["artifact_hash"], "arm_summary_hash": arm["artifact_hash"],
        "result_hash": result["artifact_hash"], "data_access_audit_hash": access["artifact_hash"],
        "input_relation_count": 45, "parameter_retuning_used": False, "alternative_horizon_search_used": False,
        "opposite_direction_search_used": False, "lower_ranked_fallback_used": False,
        "train3_accessed": True, "train1_train2_feature_values_accessed": False,
        "train4_test_labels_attacks_accessed": False, "br2_pair_results_accessed": False,
        "candidate_provenance_visible_during_confirmation": False, "rule_v2_authorized": False,
        "recommended_next_task": "TASK-039D2-AUDIT",
    })


def assert_reconstruction_invariance_v1(
    *, directional: Mapping[str, Any], pair: Mapping[str, Any], arm: Mapping[str, Any],
) -> None:
    if (directional.get("confirmed_directional_count"), directional.get("conflict_directional_count")) != (42, 3):
        raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")
    if (pair.get("pairs_with_confirmed_direction_count"), pair.get("d1_supported_pairs_without_confirmed_direction_count")) != (23, 2):
        raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")
    arms = {item["arm"]: item for item in arm.get("arms", ())}
    expected = {
        "META": (15, 0.75, 0.9375, 28, 28 / 29, 7, 7 / 12, 9, 9 / 12),
        "STAT": (17, 0.85, 1.0, 32, 32 / 33, 8, 8 / 12, 8, 8 / 12),
        "GDN": (3, 0.15, 0.6, 5, 5 / 7, 3, 3 / 12, 3, 3 / 12),
    }
    fields = (
        "d2_confirmed_pair_count", "confirmed_relation_yield_at_20", "pair_fit_to_confirmation_transfer",
        "directional_confirmation_count", "directional_transfer", "distinct_confirmed_source_count",
        "distinct_confirmed_source_coverage_at_20", "distinct_confirmed_target_count",
        "distinct_confirmed_target_coverage_at_20",
    )
    if set(arms) != set(expected) or any(tuple(arms[name].get(field) for field in fields) != values for name, values in expected.items()):
        raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")
    overlap = arm.get("confirmed_pair_overlap", {})
    expected_overlap = {
        "META_only": 4, "STAT_only": 5, "GDN_only": 2, "META_STAT_only": 11,
        "META_GDN_only": 0, "STAT_GDN_only": 1, "all_three": 0,
    }
    if any(overlap.get(name, {}).get("count") != count for name, count in expected_overlap.items()):
        raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")
    if overlap.get("confirmed_union_count") != sum(expected_overlap.values()) or overlap.get("confirmed_union_count") != 23:
        raise TASK039D2RecoveryError("failed_task039d2r_frozen_ledger_reconstruction")


def build_recovery_receipt_v1(
    *, recovery_commit: str, custody_hash: str, corrected_schema_hash: str,
    scientific_source_hashes: Mapping[str, str], directional: Mapping[str, Any], pair: Mapping[str, Any],
    arm: Mapping[str, Any], access: Mapping[str, Any], execution_receipt: Mapping[str, Any], result: Mapping[str, Any],
) -> dict[str, Any]:
    for digest in (custody_hash, corrected_schema_hash):
        require_sha256(digest, "recovery binding")
    if not re.fullmatch(r"[a-f0-9]{40}", recovery_commit):
        raise TASK039D2RecoveryError("invalid recovery commit")
    return TASK039D2ResultContractRecoveryReceiptV1({
        "task_id": TASK_ID,
        "status": RECOVERY_STATUS,
        "defect_classification": DEFECT_CLASSIFICATION,
        "original_d2_commit_a": ORIGINAL_COMMIT_A,
        "original_failed_status": ORIGINAL_FAILED_STATUS,
        "original_private_d2_ledger_hash": PRIVATE_D2_LEDGER_HASH,
        "original_private_ledger_validated": True,
        "frozen_scientific_source_hashes": validate_exact_four_source_hash_map_v1(scientific_source_hashes),
        "scientific_source_hash_basis": "exact_commit_a_git_blob_bytes",
        "scientific_sources_unchanged": True,
        "result_contract_recovery_commit": recovery_commit,
        "failed_run_custody_hash": custody_hash,
        "corrected_receipt_schema_hash": corrected_schema_hash,
        "schema_changed": True,
        "scientific_code_changed": False,
        "train3_reread": False,
        "hai_values_accessed_during_recovery": False,
        "scientific_outcomes_recomputed_from_hai": False,
        "public_summaries_deterministically_reconstructed_from_frozen_ledger": True,
        "four_key_receipt_schema_validated": True,
        "directional_summary_hash": directional["artifact_hash"],
        "pair_summary_hash": pair["artifact_hash"],
        "arm_summary_hash": arm["artifact_hash"],
        "data_access_audit_hash": access["artifact_hash"],
        "execution_receipt_hash": execution_receipt["artifact_hash"],
        "d2_result_hash": result["artifact_hash"],
        "d2_result_authoritative_after_recovery": True,
        "independent_d2_audit_still_required": True,
        "winner_selected": False,
        "rule_v2_authorized": False,
        "recommended_next_task": "TASK-039D2-AUDIT",
    }).to_dict()


def schema_for_recovery_artifact_v1(example: Mapping[str, Any]) -> dict[str, Any]:
    def infer(value: Any, field_name: str | None = None) -> dict[str, Any]:
        if value is None:
            return {"type": "null"}
        if isinstance(value, bool):
            return {"type": "boolean"}
        if isinstance(value, int):
            return {"type": "integer", "minimum": 0}
        if isinstance(value, float):
            return {"type": "number"}
        if isinstance(value, str):
            return {"type": "string", **({"pattern": "^[a-f0-9]{64}$"} if field_name and field_name.endswith("_hash") else {})}
        if isinstance(value, list):
            return {"type": "array", "items": {} if not value else infer(value[0])}
        if isinstance(value, Mapping):
            return {"type": "object", "additionalProperties": False, "required": list(value), "properties": {key: infer(item, key) for key, item in value.items()}}
        raise TASK039D2RecoveryError("unsupported recovery schema example")
    schema = infer(example)
    artifact_type = str(example["artifact_type"])
    schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"https://paperworks.local/schemas/v6/{artifact_type}_schema.json", "title": artifact_type})
    schema["properties"]["schema_version"] = {"const": V6_FOUNDATION_SCHEMA_VERSION}
    schema["properties"]["artifact_type"] = {"const": artifact_type}
    schema["properties"]["artifact_hash"] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    if "scientific_source_commit_blob_hashes" in schema["properties"]:
        schema["properties"]["scientific_source_commit_blob_hashes"] = bind_source_map_subschema_v1()
    if "frozen_scientific_source_hashes" in schema["properties"]:
        schema["properties"]["frozen_scientific_source_hashes"] = bind_source_map_subschema_v1()
    return schema


def bind_source_map_subschema_v1() -> dict[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": list(SCIENTIFIC_SOURCE_PATHS),
        "properties": {path: {"type": "string", "pattern": "^[a-f0-9]{64}$"} for path in SCIENTIFIC_SOURCE_PATHS},
    }


def recovery_schema_examples_v1() -> dict[str, dict[str, Any]]:
    digest = "0" * 64
    custody = TASK039D2FailedRunCustodyV1({
        "task_id": TASK_ID, "status": "verified_task039d2_failed_run_custody",
        "defect_classification": DEFECT_CLASSIFICATION, "original_execution_commit_a": ORIGINAL_COMMIT_A,
        "original_branch": ORIGINAL_BRANCH, "original_branch_tip": ORIGINAL_COMMIT_A,
        "synthetic_prep_merge_commit": PREP_COMMIT, "original_terminal_status": ORIGINAL_FAILED_STATUS,
        "original_result_commit_b": None, "private_ledger_hash": PRIVATE_D2_LEDGER_HASH,
        "private_ledger_record_count": 45, "scientific_computation_completed_before_schema_failure": True,
        "result_contract_validation_failure_stage": "post_scientific_public_execution_receipt_schema_validation",
        "schema_defect_identifier": "scientific_source_hashes_example_key_undercoverage_v1",
        "train3_accessed_by_original_run": True, "train1_train2_feature_value_refit_used": False,
        "scientific_source_modified_after_train3_read": False, "original_public_outputs_authoritative": False,
        "private_scientific_ledger_authoritative_custody_candidate": True,
        "d2_authorization_hash": D2_AUTHORIZATION_HASH, "d1_directional_ledger_hash": D1_DIRECTIONAL_LEDGER_HASH,
        "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
        "scientific_source_commit_blob_hashes": COMMIT_A_SCIENTIFIC_SOURCE_HASHES,
        "machine_verifiable_evidence": {"original_branch_tip_equals_commit_a": True, "commit_a_has_no_result_commit_b": True, "private_ledger_self_hash_valid": True, "all_45_private_record_hashes_valid": True, "all_45_d1_directional_references_exact": True, "commit_a_schema_runtime_cardinality_mismatch_reproduced": True},
        "claim_boundary": "custody evidence for serialization recovery; not an independent scientific audit",
    }).to_dict()
    access = build_recovery_data_access_audit_v1()
    recovery = TASK039D2ResultContractRecoveryReceiptV1({
        "task_id": TASK_ID, "status": RECOVERY_STATUS, "defect_classification": DEFECT_CLASSIFICATION,
        "original_d2_commit_a": ORIGINAL_COMMIT_A, "original_failed_status": ORIGINAL_FAILED_STATUS,
        "original_private_d2_ledger_hash": PRIVATE_D2_LEDGER_HASH, "original_private_ledger_validated": True,
        "frozen_scientific_source_hashes": COMMIT_A_SCIENTIFIC_SOURCE_HASHES,
        "scientific_source_hash_basis": "exact_commit_a_git_blob_bytes", "scientific_sources_unchanged": True,
        "result_contract_recovery_commit": ORIGINAL_COMMIT_A, "failed_run_custody_hash": digest,
        "corrected_receipt_schema_hash": digest, "schema_changed": True, "scientific_code_changed": False,
        "train3_reread": False, "hai_values_accessed_during_recovery": False,
        "scientific_outcomes_recomputed_from_hai": False,
        "public_summaries_deterministically_reconstructed_from_frozen_ledger": True,
        "four_key_receipt_schema_validated": True, "directional_summary_hash": digest,
        "pair_summary_hash": digest, "arm_summary_hash": digest, "data_access_audit_hash": digest,
        "execution_receipt_hash": digest, "d2_result_hash": digest,
        "d2_result_authoritative_after_recovery": True, "independent_d2_audit_still_required": True,
        "winner_selected": False, "rule_v2_authorized": False, "recommended_next_task": "TASK-039D2-AUDIT",
    }).to_dict()
    return {item["artifact_type"]: item for item in (custody, access, recovery)}


__all__ = [
    "TASK039D2RecoveryError", "TASK039D2FailedRunCustodyV1", "TASK039D2RDataAccessAuditV1",
    "TASK039D2ResultContractRecoveryReceiptV1", "RECOVERY_ARTIFACT_CLASSES", "RECOVERY_CLASS_BY_TYPE",
    "SCIENTIFIC_SOURCE_PATHS", "COMMIT_A_SCIENTIFIC_SOURCE_HASHES", "ORIGINAL_COMMIT_A",
    "ORIGINAL_FAILED_STATUS", "PRIVATE_D2_LEDGER_HASH", "PRIVATE_D2_LEDGER_NAME", "RECOVERY_STATUS",
    "SCIENTIFIC_STATUS", "DEFECT_CLASSIFICATION", "validate_exact_four_source_hash_map_v1",
    "bind_exact_four_source_hash_schema_v1", "verify_scientific_sources_unchanged_v1",
    "load_json_object_v1", "write_public_json_v1", "load_d1_private_inputs_for_recovery_v1",
    "validate_frozen_d2_ledger_v1", "build_failed_run_custody_v1", "build_recovery_data_access_audit_v1",
    "build_directional_summary_from_frozen_ledger_v1", "build_pair_summary_from_frozen_ledger_v1",
    "load_provenance_after_recovery_outcomes_frozen_v1", "build_arm_summary_from_frozen_ledger_v1",
    "build_result_from_frozen_ledger_v1", "build_execution_receipt_from_frozen_ledger_v1",
    "assert_reconstruction_invariance_v1", "build_recovery_receipt_v1", "schema_for_recovery_artifact_v1",
    "recovery_schema_examples_v1", "verify_recovery_self_hash_v1",
]
