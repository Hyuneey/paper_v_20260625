"""Public-only validator for the D2 design provenance clarification R1.

The validator deliberately uses a closed allowlist.  It does not inspect D0/D1
prediction content, metric artifacts, scientific data, labels, or private custody.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-PROVENANCE-CLARIFICATION-R1"
BASE_COMMIT = "ea1dec8129b10d9941802359d2ab742d83d1f2ed"
DESIGN_COMMIT_A = "8bb227521f28101970e7ea19ae97987d94b3c7c3"
INDEPENDENT_AUDIT_COMMIT_B = "03e58a79842d6f6aa0675595e6f78fca86b76de6"
DESIGN_FREEZE_COMMIT_C = "5ad1c2fb56432be637c177cf64449238fdc1b504"
CONTINUITY_COMMIT_D = BASE_COMMIT

D2_DESIGN_HASH = "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
D0_PREDICTION_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_PREDICTION_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
ORIGINAL_INDEPENDENCE_HASH = "4d684c5b2ea55ea6cd7280f5d64241b4f8483e4988319497388f193fd7db312e"
ORIGINAL_READINESS_HASH = "50a9547cadf0b6dca779dea5f107c6368fdde7d4e1251253c9394e328c1d5aea"
ORIGINAL_BUNDLE_HASH = "2b75563a57d89816b2936d4172762b9d3bca0cf1c8752c780d9c5ecc89cec675"
ORIGINAL_RECEIPT_HASH = "d14feaa9a1fe402159806f29ef7499d9ca1e119902fbf1d12faad7b010b0e245"
DESIGN_MODULE_BLOB = "9f9fb6b7ff4866f63d1f47b7427750c9940ce028"
DESIGN_CONFIG_BLOB = "15d180f903a995030ca9336bf54b4f56b4f0f7ac"

DESIGN_STAGE_ROLE = "INNER_DEVELOPMENT_POLICY_SELECTION"
CONFIRMATORY_STAGE = "OUTER_TEST2"
FUSION_FAMILY = "DETECTOR_PRESERVING_MULTI_SOURCE_RULE_CORROBORATION"
SAME_SECOND_POLICY = "EXACT_DECISION_PHYSICAL_ROW_INDEX_EQUALITY"
SOURCE_COUNT_RATIONALE = "MINIMUM_NON_SINGLETON_DISTINCT_SOURCE_CORROBORATION"
REMOTE_STATE = "LOCAL_ONLY_NOT_PUSHED"

REPORT_PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_"
ORIGINAL_REPORT_HASHES = {
    f"{REPORT_PREFIX}BUNDLE.json": ORIGINAL_BUNDLE_HASH,
    f"{REPORT_PREFIX}CORROBORATION_POLICY.json": "73069cade706c08065e4669dbe6b5c812f1e2d00d91d5e6ecc57e41d696a6751",
    f"{REPORT_PREFIX}DESIGN.json": "74e6d66fc506cf9be0d40848d4f3d5b51b51f398ee0c8448c1453d5344bc0b94",
    f"{REPORT_PREFIX}INDEPENDENCE.json": ORIGINAL_INDEPENDENCE_HASH,
    f"{REPORT_PREFIX}INDEPENDENT_AUDIT.json": "55599576c754c31f00519823d73ded39c924a114ac5eb94d006bba77ddc37932",
    f"{REPORT_PREFIX}INPUT_AUTHORITY.json": "6b483f8007db86f910524fea6204a6119f82c23ff6fa24d1302fc93e98c58fb9",
    f"{REPORT_PREFIX}METRIC_POLICY.json": "a684368a13efe7699862cc626c4c6a28cb5eca342efe3cc3f4bb77adbfbaa012",
    f"{REPORT_PREFIX}READINESS.json": ORIGINAL_READINESS_HASH,
    f"{REPORT_PREFIX}RECEIPT.json": ORIGINAL_RECEIPT_HASH,
}

CLARIFICATION_NAME = "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_PROVENANCE_CLARIFICATION_R1.json"
READINESS_NAME = "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_PROVENANCE_R1_READINESS.json"
BUNDLE_NAME = "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_PROVENANCE_R1_BUNDLE.json"
RECEIPT_NAME = "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_PROVENANCE_R1_RECEIPT.json"


class ProvenanceValidationError(ValueError):
    """Raised when a public provenance contract is not exact."""


def stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def artifact_hash(document: Mapping[str, Any]) -> str:
    payload = dict(document)
    observed = payload.pop("artifact_hash", None)
    if not isinstance(observed, str):
        raise ProvenanceValidationError("artifact hash is absent")
    calculated = stable_hash(payload)
    if observed != calculated:
        raise ProvenanceValidationError("artifact self-hash mismatch")
    return observed


def _require_exact_keys(document: Mapping[str, Any], required: set[str]) -> None:
    if set(document) != required:
        raise ProvenanceValidationError("artifact schema mismatch")


def expected_clarification_payload() -> dict[str, Any]:
    return {
        "artifact_type": "task039e3_r2r_utility_inner_d2_design_provenance_clarification_r1",
        "schema_version": "1.0.0",
        "task_id": TASK_ID,
        "status": "PASS",
        "d2_id": "D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_V1",
        "d2_design_hash": D2_DESIGN_HASH,
        "fusion_family": FUSION_FAMILY,
        "original_independence_hash": ORIGINAL_INDEPENDENCE_HASH,
        "d2_design_commit_a": DESIGN_COMMIT_A,
        "independent_audit_commit_b": INDEPENDENT_AUDIT_COMMIT_B,
        "design_freeze_commit_c": DESIGN_FREEZE_COMMIT_C,
        "d2_continuity_commit_d": CONTINUITY_COMMIT_D,
        "d0_detector_prediction_artifact_hash": D0_PREDICTION_HASH,
        "d1_rule_prediction_artifact_hash": D1_PREDICTION_HASH,
        "codex_design_process_d0_prediction_content_read": False,
        "codex_design_process_d1_prediction_content_read": False,
        "codex_design_process_d0_metric_artifact_read": False,
        "codex_design_process_d1_metric_artifact_read": False,
        "codex_design_process_test1_read": False,
        "codex_design_process_labels_read": False,
        "project_level_d0_inner_baseline_results_known_before_d2_policy_selection": True,
        "project_level_d1_inner_baseline_results_known_before_d2_policy_selection": True,
        "project_level_inner_baseline_characterization_informed_d2_problem_formulation": True,
        "d2_design_stage_role": DESIGN_STAGE_ROLE,
        "d2_confirmatory_stage": CONFIRMATORY_STAGE,
        "d2_frozen_before_execution": True,
        "d2_frozen_before_prediction": True,
        "d2_frozen_before_metric": True,
        "d2_fusion_candidates_compared": 0,
        "d2_hyperparameter_search_performed": False,
        "d2_result_observed_before_freeze": False,
        "d2_prediction_content_observed_before_freeze": False,
        "d2_metric_observed_before_freeze": False,
        "distinct_source_count": 2,
        "distinct_source_count_metric_tuned": False,
        "distinct_source_count_rationale": SOURCE_COUNT_RATIONALE,
        "same_second_policy": SAME_SECOND_POLICY,
        "same_second_window_tuned": False,
        "temporal_window_parameter_exists": False,
        "d0_preservation_policy": "EVERY_FROZEN_D0_ALARM_IS_A_D2_ALARM",
        "d0_score_dependency": False,
        "rule_rerun_dependency": False,
        "test2_accessed_before_d2_design": False,
        "test2_accessed_during_d2_design": False,
        "test2_accessed_during_this_clarification": False,
        "outer_execution_authorized": False,
        "d0_executions": 0,
        "d1_executions": 0,
        "d2_executions": 0,
        "test1_accesses": 0,
        "label_accesses": 0,
        "test2_accesses": 0,
        "design_semantics_changed": False,
        "scientific_prediction_changed": False,
        "provenance_clarified": True,
        "original_d2_artifacts_changed_count": 0,
        "private_paths_exposed": 0,
        "private_numeric_values_exposed": 0,
        "remote_egress_status": REMOTE_STATE,
        "push_attempted": False,
    }


def validate_clarification(document: Mapping[str, Any]) -> str:
    artifact_hash(document)
    expected = expected_clarification_payload()
    _require_exact_keys(document, set(expected) | {"artifact_hash"})
    for key, value in expected.items():
        if document.get(key) != value or type(document.get(key)) is not type(value):
            raise ProvenanceValidationError(f"clarification mismatch: {key}")
    return str(document["artifact_hash"])


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    ).stdout


def validate_original_freeze(repo: Path) -> dict[str, Any]:
    if _git(repo, "rev-parse", "HEAD").decode().strip() == "":
        raise ProvenanceValidationError("HEAD unavailable")
    expected_parents = {
        CONTINUITY_COMMIT_D: DESIGN_FREEZE_COMMIT_C,
        DESIGN_FREEZE_COMMIT_C: INDEPENDENT_AUDIT_COMMIT_B,
        INDEPENDENT_AUDIT_COMMIT_B: DESIGN_COMMIT_A,
    }
    for commit, parent in expected_parents.items():
        actual = _git(repo, "rev-parse", f"{commit}^").decode().strip()
        if actual != parent:
            raise ProvenanceValidationError("frozen D2 lineage mismatch")

    tracked = {
        "src/paperworks/v6/task039e3_r2r_d2_design_v1.py": DESIGN_MODULE_BLOB,
        "configs/v6/task039e3_r2r_d2_detector_rule_corroboration_v1.json": DESIGN_CONFIG_BLOB,
    }
    for relative, expected_blob in tracked.items():
        current_blob = _git(repo, "hash-object", relative).decode().strip()
        if current_blob != expected_blob:
            raise ProvenanceValidationError("frozen design source changed")

    reports = repo / "docs" / "task_reports"
    for name, expected_hash in ORIGINAL_REPORT_HASHES.items():
        path = reports / name
        current = path.read_bytes()
        committed = _git(repo, "show", f"{DESIGN_FREEZE_COMMIT_C}:docs/task_reports/{name}")
        if current != committed:
            raise ProvenanceValidationError("original D2 report bytes changed")
        document = json.loads(current.decode("utf-8"))
        if artifact_hash(document) != expected_hash:
            raise ProvenanceValidationError("original D2 report identity changed")

    design = json.loads((reports / f"{REPORT_PREFIX}DESIGN.json").read_text(encoding="utf-8"))
    policy = json.loads((reports / f"{REPORT_PREFIX}CORROBORATION_POLICY.json").read_text(encoding="utf-8"))
    if design["d2_design_hash"] != D2_DESIGN_HASH or policy["policy"]["required_distinct_source_count"] != 2:
        raise ProvenanceValidationError("frozen D2 semantics changed")
    if policy["policy"]["same_second_policy"] != SAME_SECOND_POLICY:
        raise ProvenanceValidationError("same-second policy changed")
    return {"original_d2_artifacts_changed_count": 0, "d2_design_hash": D2_DESIGN_HASH}


def validate_authority_set(
    clarification: Mapping[str, Any],
    readiness: Mapping[str, Any],
    bundle: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> dict[str, str]:
    clarification_hash = validate_clarification(clarification)
    readiness_hash = artifact_hash(readiness)
    bundle_hash = artifact_hash(bundle)
    receipt_hash = artifact_hash(receipt)

    required_readiness = {
        "clarification_hash": clarification_hash,
        "d2_design_hash": D2_DESIGN_HASH,
        "original_independence_hash": ORIGINAL_INDEPENDENCE_HASH,
        "original_report_hashes": ORIGINAL_REPORT_HASHES,
        "d2_design_semantics_unchanged": True,
        "test2_sealed": True,
        "d2_execution_count": 0,
        "status": "PASS",
    }
    for key, value in required_readiness.items():
        if readiness.get(key) != value:
            raise ProvenanceValidationError(f"readiness mismatch: {key}")

    required_bundle = {
        "clarification_hash": clarification_hash,
        "readiness_hash": readiness_hash,
        "original_d2_readiness_hash": ORIGINAL_READINESS_HASH,
        "original_d2_bundle_hash": ORIGINAL_BUNDLE_HASH,
        "original_d2_receipt_hash": ORIGINAL_RECEIPT_HASH,
        "d2_design_hash": D2_DESIGN_HASH,
        "d0_detector_prediction_artifact_hash": D0_PREDICTION_HASH,
        "d1_rule_prediction_artifact_hash": D1_PREDICTION_HASH,
        "status": "PASS",
    }
    for key, value in required_bundle.items():
        if bundle.get(key) != value:
            raise ProvenanceValidationError(f"bundle mismatch: {key}")

    required_receipt = {
        "clarification_hash": clarification_hash,
        "readiness_hash": readiness_hash,
        "bundle_hash": bundle_hash,
        "status": "passed_task039e3_r2r_utility_inner_d2_design_provenance_clarification_r1",
        "remote_egress_status": REMOTE_STATE,
        "push_attempted": False,
    }
    for key, value in required_receipt.items():
        if receipt.get(key) != value:
            raise ProvenanceValidationError(f"receipt mismatch: {key}")
    return {
        "clarification_hash": clarification_hash,
        "readiness_hash": readiness_hash,
        "bundle_hash": bundle_hash,
        "receipt_hash": receipt_hash,
    }


def load_public_authority_set(repo: Path) -> tuple[dict[str, Any], ...]:
    report_dir = repo / "docs" / "task_reports"
    return tuple(
        json.loads((report_dir / name).read_text(encoding="utf-8"))
        for name in (CLARIFICATION_NAME, READINESS_NAME, BUNDLE_NAME, RECEIPT_NAME)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    validate_original_freeze(repo)
    hashes = validate_authority_set(*load_public_authority_set(repo))
    print(json.dumps({"status": "PASS", **hashes}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
