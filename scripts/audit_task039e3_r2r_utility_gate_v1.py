#!/usr/bin/env python3
"""Read-only metadata gate for TASK-039E3 R2R utility readiness.

This module deliberately has no interface for private data, label arrays,
predictions, rule execution, or utility outcomes.  It verifies only committed
Git/source authority and public dataset/split metadata.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from paperworks.data.contracts_v2 import (
    DatasetManifestV2,
    SealedAccessStatusV2,
    SplitManifestV2,
    SplitRoleV2,
)
from paperworks.data.splits_v2 import DataOperationV2, OPERATION_PERMISSIONS_V2
from paperworks.v6.common import stable_hash_v1


TASK_ID = "TASK-039E3-R2R-UTILITY-FEASIBILITY-AND-AUTHORIZATION-GATE"
BASE_COMMIT = "bc3d930237f1e6b52c6afc02d643d4b6cc1bb0d8"
RESULT_ANALYSIS_COMMIT_A = "0b2c41db90eda1103eb6602eb57bedf2597bd981"
RESULT_ANALYSIS_COMMIT_B = "bc3d930237f1e6b52c6afc02d643d4b6cc1bb0d8"
RESULT_OBSERVATION_BOUNDARY = "a431dd88866e0f65439e3fad567894e0e9058713"
RESULT_ANALYSIS_BUNDLE = "edd96574545504693479def2972740e7c9d065f1883b2d767c307a36c57cfe9d"
RESULT_ANALYSIS_RECEIPT = "d9df904bcc0f823780c82c0a594f124939fe56354e50606c866a71e0e05e999f"
DATASET_MANIFEST_PATH = Path("docs/task_reports/TASK-039A_DATASET_MANIFEST_V2.json")
SPLIT_COLLECTION_PATH = Path("docs/task_reports/TASK-039BR2_SPLIT_MANIFESTS_V2.json")
ANALYSIS_CLAIMS_PATH = Path("docs/task_reports/TASK-039E3_R2R_RESULT_ANALYSIS_CLAIMS.json")
ANALYSIS_RECEIPT_PATH = Path("docs/task_reports/TASK-039E3_R2R_RESULT_ANALYSIS_RECEIPT.json")

UTILITY_ROLES = (
    SplitRoleV2.INNER_UTILITY,
    SplitRoleV2.OUTER_VALIDATION,
    SplitRoleV2.SEALED_EVALUATION,
)
EXPECTED_UTILITY_PERMISSIONS = {
    DataOperationV2.ASSESS_RULE_UTILITY: SplitRoleV2.INNER_UTILITY,
    DataOperationV2.SELECT_RULE_OR_NO_OP: SplitRoleV2.INNER_UTILITY,
    DataOperationV2.REPLAY_OUTER: SplitRoleV2.OUTER_VALIDATION,
    DataOperationV2.RUN_SEALED_EVALUATION: SplitRoleV2.SEALED_EVALUATION,
}
FORBIDDEN_VALUE_KEYS = frozenset(
    {
        "actual_labels",
        "anomaly_timestamps",
        "attack_intervals",
        "ground_truth",
        "ground_truth_labels",
        "label_array",
        "label_values",
        "labels",
        "per_arm_utility",
        "predictions",
        "utility_outcomes",
        "utility_results",
    }
)
UTILITY_PROTOCOL_REQUIREMENTS = (
    "materialize_and_audit_inner_utility_split_before_label_access",
    "freeze_outer_and_sealed_role_plan_without_granting_sealed_access",
    "freeze_offline_candidate_utility_interpreter_semantics",
    "freeze_no_rule_coverage_and_denominator_semantics",
    "freeze_primary_unit_metric_formulas_and_aggregation",
    "freeze_event_or_point_matching_and_no_point_adjustment_policy",
    "freeze_normal_data_only_threshold_sources",
    "freeze_paired_arm_agnostic_comparison_and_statistical_reporting",
    "freeze_private_label_and_result_custody",
    "independently_audit_protocol_before_utility_authorization",
)


class UtilityGateError(ValueError):
    """Public metadata cannot support a fail-closed utility gate."""


def _git(repository_root: Path, *arguments: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and completed.returncode != 0:
        raise UtilityGateError(completed.stderr.strip() or "Git metadata query failed")
    return completed.stdout.strip()


def verify_self_hash(document: Mapping[str, Any]) -> str:
    """Verify a stable_hash_v1 public governance document."""

    observed = document.get("artifact_hash")
    expected = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )
    if observed != expected:
        raise UtilityGateError("public artifact self-hash differs")
    return expected


def assert_metadata_only(value: Any, *, location: str = "root") -> None:
    """Reject label arrays, predictions, or utility outcomes recursively.

    Label field names, encodings, and availability metadata are intentionally
    permitted; the prohibited keys name value-bearing or result-bearing data.
    """

    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in FORBIDDEN_VALUE_KEYS:
                raise UtilityGateError(f"value-bearing field prohibited at {location}.{key}")
            assert_metadata_only(item, location=f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_metadata_only(item, location=f"{location}[{index}]")


def classify_metric_definition(
    definition: Mapping[str, Any] | None,
    *,
    precommitted: bool,
    compatible: bool = True,
) -> str:
    """Classify completeness without selecting or computing a metric."""

    if not compatible:
        return "INCOMPATIBLE_WITH_CURRENT_TASK"
    if definition is None or not precommitted:
        return "NOT_PRECOMMITTED"
    required = {
        "formula",
        "denominator",
        "unit_of_analysis",
        "aggregation",
        "threshold_policy",
        "direction",
    }
    return (
        "PRECOMMITTED_AND_EXACT"
        if required.issubset(definition) and all(definition[key] is not None for key in required)
        else "PRECOMMITTED_BUT_INCOMPLETE"
    )


def temporal_precommitment(
    repository_root: Path,
    *,
    candidate_commit: str,
    result_boundary_commit: str,
) -> bool:
    """Return whether Git proves the candidate predates the supplied boundary."""

    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "merge-base",
            "--is-ancestor",
            candidate_commit,
            result_boundary_commit,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode not in (0, 1):
        raise UtilityGateError("Git temporal-precommitment query failed")
    return completed.returncode == 0


def operation_permission_snapshot() -> dict[str, list[str]]:
    return {
        operation.value: sorted(role.value for role in OPERATION_PERMISSIONS_V2[operation])
        for operation in EXPECTED_UTILITY_PERMISSIONS
    }


def verify_utility_operation_permissions() -> dict[str, Any]:
    observed = operation_permission_snapshot()
    expected = {
        operation.value: [role.value]
        for operation, role in EXPECTED_UTILITY_PERMISSIONS.items()
    }
    if observed != expected:
        raise UtilityGateError("v2 utility split-operation permissions differ")
    return {
        "verified": True,
        "operation_permissions": observed,
        "sealed_evaluation_requires_explicit_approved_status": True,
    }


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise UtilityGateError(f"JSON object required: {path.name}")
    assert_metadata_only(value, location=path.name)
    return value


def _split_collection(document: Mapping[str, Any]) -> tuple[SplitManifestV2, ...]:
    verify_self_hash(document)
    records = document.get("records")
    if not isinstance(records, list):
        raise UtilityGateError("split collection records are unavailable")
    return tuple(SplitManifestV2.from_dict(item) for item in records)


def _blob(repository_root: Path, relative_path: Path) -> str:
    return _git(repository_root, "rev-parse", f"HEAD:{relative_path.as_posix()}")


def audit_repository(repository_root: Path) -> dict[str, Any]:
    """Build a metadata-only gate snapshot from fixed committed inputs."""

    repository_root = repository_root.resolve()
    head = _git(repository_root, "rev-parse", "HEAD")
    dataset_document = _read_json(repository_root / DATASET_MANIFEST_PATH)
    dataset = DatasetManifestV2.from_dict(dataset_document)
    split_document = _read_json(repository_root / SPLIT_COLLECTION_PATH)
    splits = _split_collection(split_document)
    claims = _read_json(repository_root / ANALYSIS_CLAIMS_PATH)
    receipt = _read_json(repository_root / ANALYSIS_RECEIPT_PATH)
    verify_self_hash(claims)
    verify_self_hash(receipt)
    if receipt.get("artifact_hash") != RESULT_ANALYSIS_RECEIPT:
        raise UtilityGateError("scientific-result analysis receipt differs")
    if claims.get("utility_necessity") != "ESSENTIAL":
        raise UtilityGateError("utility necessity authority differs")

    materialized_roles = {split.role for split in splits}
    split_readiness: dict[str, Any] = {}
    for role in UTILITY_ROLES:
        role_splits = [split for split in splits if split.role is role]
        split_readiness[role.value] = {
            "manifest_exists": bool(role_splits),
            "manifest_count": len(role_splits),
            "ready": False,
            "label_metadata_available_at_dataset_level": any(
                item.label_availability.value == "available" for item in dataset.files
            ),
            "sealed_access_status": (
                role_splits[0].sealed_access_status.value
                if len(role_splits) == 1
                else "not_materialized"
            ),
            "required_sealed_status_before_access": (
                SealedAccessStatusV2.APPROVED.value
                if role is SplitRoleV2.SEALED_EVALUATION
                else "not_applicable"
            ),
        }

    source_authority = {}
    for relative_path in (
        Path("src/paperworks/data/contracts_v2.py"),
        Path("src/paperworks/data/splits_v2.py"),
    ):
        raw = (repository_root / relative_path).read_bytes()
        from hashlib import sha256

        source_authority[relative_path.as_posix()] = {
            "git_blob": _blob(repository_root, relative_path),
            "byte_sha256": sha256(raw).hexdigest(),
        }

    snapshot: dict[str, Any] = {
        "task_id": TASK_ID,
        "head": head,
        "input_authority": {
            "result_analysis_commit_a": RESULT_ANALYSIS_COMMIT_A,
            "result_analysis_commit_b": RESULT_ANALYSIS_COMMIT_B,
            "result_observation_boundary": RESULT_OBSERVATION_BOUNDARY,
            "result_analysis_bundle": RESULT_ANALYSIS_BUNDLE,
            "result_analysis_receipt": RESULT_ANALYSIS_RECEIPT,
            "utility_necessity": "ESSENTIAL",
        },
        "split_policy": verify_utility_operation_permissions(),
        "split_collection": {
            "artifact_hash": split_document["artifact_hash"],
            "dataset_manifest_id": dataset.manifest_id,
            "materialized_roles": sorted(role.value for role in materialized_roles),
            "utility_role_readiness": split_readiness,
        },
        "label_boundary": {
            "metadata_only": True,
            "label_values_accessed": False,
            "utility_values_computed": False,
        },
        "source_authority": source_authority,
        "requirements": list(UTILITY_PROTOCOL_REQUIREMENTS),
        "decision": {
            "protocol_readiness_classification": "UTILITY_PROTOCOL_FREEZE_REQUIRED",
            "utility_feasible": "conditional",
            "utility_protocol_precommitted": "partial",
            "utility_protocol_audited": False,
            "utility_execution_authorization_ready": False,
            "sealed_evaluation_authorized": False,
            "next_task": "TASK-039E3-R2R-UTILITY-PROTOCOL-FREEZE",
        },
    }
    snapshot["snapshot_hash"] = stable_hash_v1(snapshot)
    return snapshot


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    args = parser.parse_args(argv)
    snapshot = audit_repository(args.repository_root)
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
