"""Independent local-only integrity audit for the frozen D0 INNER result.

This script deliberately does not import the authoritative D0 execution
module.  It replays public Git custody and independently duplicates the frozen
float64 PCA-SPE, decision, event, and metric serialization contracts.  Private
paths and numeric values are never returned or printed.
"""

from __future__ import annotations

import ast
import copy
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any, Callable, Mapping, NoReturn, Sequence


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-AUDIT-V1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d0_result_integrity_audit_v1"
SCIENTIFIC_STATUS = "D0_RESULT_INTEGRITY_AUDITED"
REMOTE_EGRESS_STATUS = "LOCAL_ONLY_NOT_PUSHED"
SCHEMA_VERSION = "1.0.0"

BASE_COMMIT = "dd2d103d20e3d61aa31167740929cbe31cf8b942"
EXECUTION_COMMIT_A = "c117087ec43d6e58167e77087e13b6a8a9226d42"
INDEPENDENT_COMMIT_B = "f45c71c9990984f6fa0c552060c8ab51e1e5c9a4"
RESULT_FREEZE_COMMIT_C = "78d758f50657413eed28dc838212be9a1edeffc7"
CONTINUITY_COMMIT_D = "c96adab1ae6f474472f73cc2de0a7c5dab63e24d"
EXPECTED_BRANCH = "task-039e3-r2r-utility-inner-d0-result-integrity-audit-v1"

AUTHORIZATION_FREEZE_COMMIT = "01cd15831246f94b2111fd3d9c0589e639f2d254"
AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST1_D0_PCA_SPE_INNER_V1"
AUTHORIZATION_HASH = "a155fbb2659dc2a8b233db179706a13338a58ae41610f5c6db01f90f3b76a1ef"
PREFLIGHT_HASH = "033f1f9981bb5323e2830fa30d7e6613ce49b7a530e14a50ca2c4df75b848131"
AUTHORIZATION_RECEIPT_HASH = "10540956fe37ccd025d82d1e7a7c61eef26d869c1e9f97c7bda9b2415d4e12f2"
COMMITTED_GRANT_HASH = "ed2077cae7a770cf28f3a576ea9298f7c4530769c58521241b36ffcb213e9671"

EXECUTION_VERSION = "TASK039E3_R2R_D0_INNER_EXECUTION_V1"
EXECUTION_MODE = "REAL_INNER_D0_PCA_SPE"
EXECUTION_IMPLEMENTATION_IDENTITY = (
    "8f00469a632643cd10cc4257f5d1fe380036c7763b03cb70b13d01815a287ee2"
)
EXECUTION_SOURCE_SHA256 = "f4ac5c7d4c7523edbfe0067a03cab5e40567c271433fe65c31046cde278ac66c"
DETECTOR_ID = "D0_PCA_SPE_V1"
DETECTOR_FAMILY = "PCA_RECONSTRUCTION_SPE"
DESIGN_HASH = "357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174"
FEATURE_SET_HASH = "6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515"
FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
PREPROCESSING_HASH = "baae5495094b211731e4fcdf7bab2870e3c81e7c973bfe052fc87b457ccb6270"
MODEL_HASH = "f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b"
THRESHOLD_HASH = "7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695"
SELECTED_K = 10
RESIDUAL_DIMENSIONS = 27
THRESHOLD_COMPARATOR = "score > threshold"

PYTHON_VERSION = "3.12.13"
NUMPY_VERSION = "2.3.5"
EXPECTED_ROWS = 54_000
FEATURE_COUNT = 37
TEST1_FEATURE_SHA256 = "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be"
TEST1_FEATURE_SIZE = 31_255_559
TEST1_LABEL_SHA256 = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
TEST1_LABEL_SIZE = 1_242_017
DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"

EXPECTED_PREDICTION_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
EXPECTED_SCORE_EVIDENCE_HASH = "ee9acb8de899fb8aa13fa70d1675ad61862982ef20ab8815702c7a3c620be91c"
EXPECTED_SCORE_VECTOR_CONTENT_HASH = (
    "e69d28342f42fc0056941961d2e24ad691407bef8e467c0e49a5c45656c048e6"
)
EXPECTED_PRIVATE_METRIC_EVIDENCE_HASH = (
    "628270f3413276d6d76c1ed3e1802679d37eae125898d250bb61524cba151176"
)
EXPECTED_EXECUTION_RUN_HASH = "0593d05790fef3b9264af587c451ece6186db438541a8b14edabbb2ee4bdeeb9"
EXPECTED_POINT_ALARMS = 876
EXPECTED_ALARM_EPISODES = 46
EXPECTED_RECALL = 0.7857142857142857
EXPECTED_FAR = 0.4939336325682589
METRIC_ABS_TOLERANCE = 1e-15

ATTACK_EVENT_POLICY = "MAXIMAL_CONTIGUOUS_STRICT_LABEL_ONE_RUNS_FILE_LOCAL"
ALARM_EPISODE_POLICY = "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
RECALL_FORMULA = (
    "ATTACK_EVENTS_OVERLAPPED_BY_AT_LEAST_ONE_ALARM_EPISODE_DIVIDED_BY_ALL_ATTACK_EVENTS"
)
FAR_FORMULA = (
    "ALARM_EPISODES_WITH_NO_ATTACK_TIMESTAMP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
)

P1_FEATURE_ORDER = (
    "P1_FCV01D", "P1_FCV01Z", "P1_FCV02D", "P1_FCV02Z", "P1_FCV03D",
    "P1_FCV03Z", "P1_FT01", "P1_FT01Z", "P1_FT02", "P1_FT02Z",
    "P1_FT03", "P1_FT03Z", "P1_LCV01D", "P1_LCV01Z", "P1_LIT01",
    "P1_PCV01D", "P1_PCV01Z", "P1_PCV02D", "P1_PCV02Z", "P1_PIT01",
    "P1_PIT01_HH", "P1_PIT02", "P1_PP01AD", "P1_PP01AR", "P1_PP01BD",
    "P1_PP01BR", "P1_PP02D", "P1_PP02R", "P1_PP04", "P1_PP04D",
    "P1_PP04SP", "P1_SOL01D", "P1_SOL03D", "P1_STSP", "P1_TIT01",
    "P1_TIT02", "P1_TIT03",
)

EXECUTION_SOURCE = "src/paperworks/v6/task039e3_r2r_d0_inner_execution_v1.py"
PREDICTION_PATH = (
    "docs/task_reports/"
    "TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
)
METRICS_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_METRICS_V1.json"
ACCOUNTING_PATH = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_ACCOUNTING.json"
)
RESULT_C_PATHS = (
    PREDICTION_PATH,
    METRICS_PATH,
    ACCOUNTING_PATH,
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_IMPLEMENTATION_AUDIT.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_READINESS.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_BUNDLE.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_RECEIPT.json",
    "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_V1_REPORT.md",
)

AUTHORIZATION_PATHS = {
    "restoration": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_TEST1_CUSTODY_RESTORATION_V1.json",
    "preflight": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_PREFLIGHT.json",
    "authorization": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_AUTHORIZATION.json",
    "accounting": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_ACCOUNTING.json",
    "readiness": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_READINESS.json",
    "bundle": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_BUNDLE.json",
    "receipt": "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_EXECUTION_AUTHORIZATION_RESTORATION_V1_RECEIPT.json",
}
AUTHORIZATION_HASHES = {
    "restoration": "dc25f9aa51dc1a31d068110399dd29a7698f273d7cff9621f1634d7e16715ab9",
    "preflight": PREFLIGHT_HASH,
    "authorization": AUTHORIZATION_HASH,
    "accounting": "98493fe49d1c816c713ae2068276717137d6bd321b92e65dd0b23e0ff91b47fe",
    "readiness": "3a105a529fc1adbb85fae1d2a1cfe2a5777e858059ef7cd6a51651b8bea5b93c",
    "bundle": "618f5add4ad13f8c999414add7a294ee25946323baa775b54e4b90838c97e1a0",
    "receipt": AUTHORIZATION_RECEIPT_HASH,
}

EXPECTED_COMMIT_PATHS = {
    EXECUTION_COMMIT_A: {
        "TASKS/TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-V1.md",
        EXECUTION_SOURCE,
        "tests/test_task039e3_r2r_d0_inner_execution_v1.py",
    },
    INDEPENDENT_COMMIT_B: {
        "tests/test_task039e3_r2r_d0_inner_execution_v1_independent.py",
    },
    RESULT_FREEZE_COMMIT_C: set(RESULT_C_PATHS),
    CONTINUITY_COMMIT_D: {
        "docs/project_state/AUTHORITY_INDEX.md",
        "docs/project_state/CURRENT_STATE.json",
        "docs/project_state/CURRENT_STATE.md",
        "docs/project_state/HANDOFF.md",
        "docs/project_state/TASK_LEDGER.md",
    },
}

REPORT_BASENAMES = (
    "FREEZE_AUDIT", "SCORE_ORACLE", "PREDICTION_AUDIT",
    "LABEL_INDEPENDENCE_AUDIT", "METRIC_ORACLE", "ACCOUNTING_AUDIT",
    "LEAKAGE_AUDIT", "INDEPENDENT_AUDIT", "READINESS", "BUNDLE", "RECEIPT",
)


class D0ResultIntegrityAuditError(ValueError):
    """A fixed local integrity invariant was rejected."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _fail(code: str) -> NoReturn:
    raise D0ResultIntegrityAuditError(code)


def repository_root_v1() -> Path:
    return Path(__file__).resolve().parents[1]


def canonical_json_v1(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def stable_hash_v1(value: Mapping[str, Any]) -> str:
    return sha256(canonical_json_v1(value).encode("utf-8")).hexdigest()


def self_hashed_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in payload:
        _fail("PREHASHED_PAYLOAD_REJECTED")
    document = dict(payload)
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def validate_self_hash_v1(document: Mapping[str, Any], expected: str | None = None) -> str:
    if type(document) is not dict or type(document.get("artifact_hash")) is not str:
        _fail("SELF_HASH_SCHEMA_REJECTED")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    observed = str(document["artifact_hash"])
    if stable_hash_v1(payload) != observed or (expected is not None and observed != expected):
        _fail("SELF_HASH_REJECTED")
    return observed


def strict_json_v1(content: bytes) -> dict[str, Any]:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail("DUPLICATE_JSON_MEMBER_REJECTED")
            result[key] = value
        return result

    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=pairs_hook)
    except D0ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("JSON_REJECTED")
    if type(value) is not dict:
        _fail("JSON_OBJECT_REQUIRED")
    return value


def git_bytes_v1(root: Path, arguments: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            ("git", *arguments), cwd=root, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
    except BaseException:
        _fail("LOCAL_GIT_UNAVAILABLE")
    if completed.returncode != 0:
        _fail("LOCAL_GIT_REJECTED")
    return completed.stdout


def git_text_v1(root: Path, arguments: Sequence[str]) -> str:
    try:
        return git_bytes_v1(root, arguments).decode("utf-8").strip()
    except D0ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("LOCAL_GIT_TEXT_REJECTED")


def validate_commit_resolution_v1(resolver: Callable[[str], bool]) -> None:
    for commit in (EXECUTION_COMMIT_A, INDEPENDENT_COMMIT_B, RESULT_FREEZE_COMMIT_C, CONTINUITY_COMMIT_D):
        if resolver(commit) is not True:
            _fail("D0_RESULT_INTEGRITY_BLOCKED_LOCAL_COMMIT_MISSING")


def validate_equal_bytes_v1(current: bytes, frozen: bytes) -> None:
    if current != frozen:
        _fail("FROZEN_RESULT_BYTES_REJECTED")


def independent_implementation_identity_v1() -> str:
    policy = {
        "artifact_type": "task039e3_r2r_d0_inner_execution_bridge_semantics_v1",
        "execution_version": EXECUTION_VERSION,
        "execution_mode": EXECUTION_MODE,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "detector_id": DETECTOR_ID,
        "design_hash": DESIGN_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "preprocessing_hash": PREPROCESSING_HASH,
        "model_hash": MODEL_HASH,
        "threshold_hash": THRESHOLD_HASH,
        "selected_k": SELECTED_K,
        "score": "STANDARDIZE_PROJECT_RESIDUAL_SUM_OF_SQUARES",
        "comparator": THRESHOLD_COMPARATOR,
        "prediction_first": True,
        "label_before_prediction": False,
        "attack_event_policy": ATTACK_EVENT_POLICY,
        "alarm_episode_policy": ALARM_EPISODE_POLICY,
        "attack_event_recall_formula": RECALL_FORMULA,
        "normal_far_formula": FAR_FORMULA,
        "test2_authorized": False,
        "d1_execution_authorized": False,
        "d2_authorized": False,
        "retries": 0,
    }
    return stable_hash_v1(policy)


def audit_execution_control_structure_v1(source: bytes) -> dict[str, bool]:
    try:
        text = source.decode("utf-8")
        tree = ast.parse(text)
    except BaseException:
        _fail("EXECUTION_SOURCE_PARSE_REJECTED")
    entry = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "execute_authorized_d0_inner_v1"),
        None,
    )
    if entry is None or any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(entry)):
        _fail("EXECUTION_RETRY_STRUCTURE_REJECTED")
    required_fragments = (
        "if _REAL_ENTRY_ATTEMPTED or _SCIENTIFIC_EXECUTION_COMPLETED",
        "state.require_label_access()",
        "_persist_prediction_before_label_v1(state, prediction)",
        "metric_prediction_bytes = prediction_path.read_bytes()",
        "if prediction_path.read_bytes() != frozen_prediction_bytes",
        "scores > np.float64(threshold)",
    )
    if any(fragment not in text for fragment in required_fragments):
        _fail("PREDICTION_BEFORE_LABEL_CONTROL_REJECTED")
    return {
        "single_execution_guard": True,
        "retry_loop_absent": True,
        "label_guard_present": True,
        "prediction_persisted_and_validated_first": True,
        "metric_stage_reloads_prediction": True,
        "final_prediction_byte_recheck": True,
        "strict_comparator_present": True,
    }


def audit_local_git_v1(root: Path) -> dict[str, Any]:
    if git_text_v1(root, ("branch", "--show-current")) != EXPECTED_BRANCH:
        _fail("LOCAL_AUDIT_BRANCH_REJECTED")
    if git_text_v1(root, ("status", "--porcelain=v1")):
        _fail("LOCAL_WORKTREE_NOT_CLEAN")

    def resolver(commit: str) -> bool:
        try:
            git_bytes_v1(root, ("cat-file", "-e", f"{commit}^{{commit}}"))
            return True
        except D0ResultIntegrityAuditError:
            return False

    validate_commit_resolution_v1(resolver)
    parents = {
        EXECUTION_COMMIT_A: BASE_COMMIT,
        INDEPENDENT_COMMIT_B: EXECUTION_COMMIT_A,
        RESULT_FREEZE_COMMIT_C: INDEPENDENT_COMMIT_B,
        CONTINUITY_COMMIT_D: RESULT_FREEZE_COMMIT_C,
    }
    for commit, parent in parents.items():
        if git_text_v1(root, ("rev-parse", f"{commit}^")) != parent:
            _fail("LOCAL_EXECUTION_LINEAGE_REJECTED")
        observed = set(
            filter(None, git_text_v1(root, ("diff-tree", "--no-commit-id", "--name-only", "-r", commit)).splitlines())
        )
        if observed != EXPECTED_COMMIT_PATHS[commit]:
            _fail("LOCAL_COMMIT_BOUNDARY_REJECTED")
    if git_text_v1(root, ("rev-list", "--merges", f"{BASE_COMMIT}..{CONTINUITY_COMMIT_D}")):
        _fail("LOCAL_EXECUTION_MERGE_REJECTED")

    for relative in RESULT_C_PATHS:
        validate_equal_bytes_v1(
            (root / relative).read_bytes(),
            git_bytes_v1(root, ("show", f"{RESULT_FREEZE_COMMIT_C}:{relative}")),
        )
    source_at_a = git_bytes_v1(root, ("show", f"{EXECUTION_COMMIT_A}:{EXECUTION_SOURCE}"))
    source_current = (root / EXECUTION_SOURCE).read_bytes()
    validate_equal_bytes_v1(source_current, source_at_a)
    if sha256(source_at_a).hexdigest() != EXECUTION_SOURCE_SHA256:
        _fail("EXECUTION_SOURCE_IDENTITY_REJECTED")
    if independent_implementation_identity_v1() != EXECUTION_IMPLEMENTATION_IDENTITY:
        _fail("EXECUTION_IMPLEMENTATION_IDENTITY_REJECTED")
    controls = audit_execution_control_structure_v1(source_current)
    return {
        "local_execution_commit_a_resolvable": True,
        "local_independent_commit_b_resolvable": True,
        "local_result_freeze_commit_c_resolvable": True,
        "local_continuity_commit_d_resolvable": True,
        "post_freeze_mutations": 0,
        "production_changes_after_commit_a": 0,
        "result_changes_after_commit_c": 0,
        "execution_implementation_identity_match": True,
        **controls,
    }


def expected_grant_payload_v1() -> dict[str, Any]:
    return {
        "execution_version": EXECUTION_VERSION,
        "authorization_freeze_commit": AUTHORIZATION_FREEZE_COMMIT,
        "restoration_report_hash": AUTHORIZATION_HASHES["restoration"],
        "preflight_hash": PREFLIGHT_HASH,
        "authorization_hash": AUTHORIZATION_HASH,
        "authorization_accounting_hash": AUTHORIZATION_HASHES["accounting"],
        "authorization_readiness_hash": AUTHORIZATION_HASHES["readiness"],
        "authorization_bundle_hash": AUTHORIZATION_HASHES["bundle"],
        "authorization_receipt_hash": AUTHORIZATION_RECEIPT_HASH,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "detector_id": DETECTOR_ID,
        "design_hash": DESIGN_HASH,
        "preprocessing_hash": PREPROCESSING_HASH,
        "model_hash": MODEL_HASH,
        "threshold_hash": THRESHOLD_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "d0_inner_execution_authorized": True,
        "d0_detector_prediction_authorized": True,
        "test1_feature_scientific_parsing_authorized": True,
        "label_metric_evaluation_authorized": True,
        "label_access_before_prediction_freeze_authorized": False,
        "d1_execution_authorized": False,
        "d1_rerun_authorized": False,
        "d2_authorized": False,
        "fusion_authorized": False,
        "outer_authorized": False,
        "test2_authorized": False,
        "retraining_authorized": False,
        "recalibration_authorized": False,
        "feature_change_authorized": False,
        "model_change_authorized": False,
        "threshold_change_authorized": False,
    }


def validate_authorization_document_v1(document: Mapping[str, Any]) -> None:
    validate_self_hash_v1(document, AUTHORIZATION_HASH)
    required = {
        "authorization_scope": AUTHORIZATION_SCOPE,
        "detector_id": DETECTOR_ID,
        "design_hash": DESIGN_HASH,
        "feature_count": FEATURE_COUNT,
        "feature_set_hash": FEATURE_SET_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "preprocessing_content_hash": PREPROCESSING_HASH,
        "model_content_hash": MODEL_HASH,
        "threshold_content_hash": THRESHOLD_HASH,
        "selected_k": SELECTED_K,
        "residual_dimensions": RESIDUAL_DIMENSIONS,
        "threshold_comparison_operator": THRESHOLD_COMPARATOR,
        "d0_inner_execution_authorized": True,
        "d0_detector_prediction_authorized": True,
        "test1_feature_scientific_parsing_authorized": True,
        "label_metric_evaluation_authorized": True,
        "label_access_before_prediction_freeze_authorized": False,
        "d1_execution_authorized": False,
        "d1_rerun_authorized": False,
        "d2_authorized": False,
        "fusion_authorized": False,
        "outer_authorized": False,
        "test2_authorized": False,
        "retraining_authorized": False,
        "recalibration_authorized": False,
        "feature_change_authorized": False,
        "model_change_authorized": False,
        "threshold_change_authorized": False,
    }
    if any(document.get(key) != value for key, value in required.items()):
        _fail("AUTHORIZATION_SEMANTICS_REJECTED")


def audit_authorization_replay_v1(root: Path) -> dict[str, Any]:
    documents: dict[str, dict[str, Any]] = {}
    for name, relative in AUTHORIZATION_PATHS.items():
        current = (root / relative).read_bytes()
        validate_equal_bytes_v1(
            current, git_bytes_v1(root, ("show", f"{AUTHORIZATION_FREEZE_COMMIT}:{relative}"))
        )
        document = strict_json_v1(current)
        validate_self_hash_v1(document, AUTHORIZATION_HASHES[name])
        documents[name] = document
    validate_authorization_document_v1(documents["authorization"])
    if documents["preflight"].get("artifact_hash") != PREFLIGHT_HASH:
        _fail("AUTHORIZATION_PREFLIGHT_REJECTED")
    if documents["receipt"].get("artifact_hash") != AUTHORIZATION_RECEIPT_HASH:
        _fail("AUTHORIZATION_RECEIPT_REJECTED")
    if stable_hash_v1(expected_grant_payload_v1()) != COMMITTED_GRANT_HASH:
        _fail("COMMITTED_GRANT_REPLAY_REJECTED")
    return {
        "authorization_hash_match": True,
        "preflight_hash_match": True,
        "authorization_receipt_hash_match": True,
        "committed_execution_grant_match": True,
    }


def decision_identity_v1(index: int, alarm: bool, score_hash: str) -> str:
    return stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_d0_detector_decision_identity_v1",
            "execution_implementation_identity": EXECUTION_IMPLEMENTATION_IDENTITY,
            "detector_id": DETECTOR_ID,
            "score_vector_content_hash": score_hash,
            "physical_row_index": index,
            "alarm_emitted": alarm,
        }
    )


PREDICTION_KEYS = {
    "artifact_type", "schema_version", "execution_mode", "authorization_hash",
    "execution_version", "execution_implementation_identity",
    "execution_implementation_commit", "execution_implementation_source_sha256",
    "detector_id", "detector_family", "design_hash", "preprocessing_hash",
    "model_hash", "threshold_hash", "feature_set_hash", "feature_order_hash",
    "test1_feature_sha256", "dataset_manifest_id", "split_id", "row_count",
    "unique_row_count", "score_vector_content_hash", "prediction_records",
    "point_alarm_count", "label_blind", "labels_accessed_before_prediction_freeze",
    "private_score_values_exposed", "private_threshold_value_exposed",
    "private_paths_exposed", "artifact_hash",
}
RECORD_KEYS = {"physical_row_index", "alarm_emitted", "detector_decision_identity"}


def validate_prediction_document_v1(
    document: Mapping[str, Any], *, expected_count: int = EXPECTED_ROWS,
    expected_artifact_hash: str | None = EXPECTED_PREDICTION_HASH,
) -> tuple[int, tuple[int, ...]]:
    validate_self_hash_v1(document, expected_artifact_hash)
    if set(document) != PREDICTION_KEYS:
        _fail("PREDICTION_SCHEMA_REJECTED")
    required = {
        "artifact_type": "ScientificDetectorPredictionArtifactV1",
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "authorization_hash": AUTHORIZATION_HASH,
        "execution_version": EXECUTION_VERSION,
        "execution_implementation_identity": EXECUTION_IMPLEMENTATION_IDENTITY,
        "execution_implementation_commit": EXECUTION_COMMIT_A,
        "execution_implementation_source_sha256": EXECUTION_SOURCE_SHA256,
        "detector_id": DETECTOR_ID,
        "detector_family": DETECTOR_FAMILY,
        "design_hash": DESIGN_HASH,
        "preprocessing_hash": PREPROCESSING_HASH,
        "model_hash": MODEL_HASH,
        "threshold_hash": THRESHOLD_HASH,
        "feature_set_hash": FEATURE_SET_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH,
        "test1_feature_sha256": TEST1_FEATURE_SHA256,
        "dataset_manifest_id": DATASET_MANIFEST_ID,
        "split_id": INNER_SPLIT_ID,
        "row_count": expected_count,
        "unique_row_count": expected_count,
        "label_blind": True,
        "labels_accessed_before_prediction_freeze": False,
        "private_score_values_exposed": 0,
        "private_threshold_value_exposed": 0,
        "private_paths_exposed": 0,
    }
    if any(document.get(key) != value for key, value in required.items()):
        _fail("PREDICTION_BINDING_REJECTED")
    score_hash = document.get("score_vector_content_hash")
    if type(score_hash) is not str or re.fullmatch(r"[a-f0-9]{64}", score_hash) is None:
        _fail("PREDICTION_SCORE_HASH_REJECTED")
    records = document.get("prediction_records")
    if type(records) is not list or len(records) != expected_count:
        _fail("PREDICTION_RECORD_COUNT_REJECTED")
    alarm_indices: list[int] = []
    for index, record in enumerate(records):
        if (
            type(record) is not dict or set(record) != RECORD_KEYS
            or type(record.get("physical_row_index")) is not int
            or record.get("physical_row_index") != index
            or type(record.get("alarm_emitted")) is not bool
            or record.get("detector_decision_identity")
            != decision_identity_v1(index, record["alarm_emitted"], score_hash)
        ):
            _fail("PREDICTION_RECORD_CLOSURE_REJECTED")
        if record["alarm_emitted"]:
            alarm_indices.append(index)
    if document.get("point_alarm_count") != len(alarm_indices):
        _fail("PREDICTION_ALARM_COUNT_REJECTED")
    return len(alarm_indices), tuple(alarm_indices)


def metric_receipt_hash_v1(
    name: str, formula: str, value: float, evidence_hash: str
) -> str:
    return stable_hash_v1(
        {
            "artifact_type": "ScientificD0MetricV1",
            "metric_name": name,
            "formula_identity": formula,
            "value": value,
            "defined": True,
            "undefined_reason": None,
            "private_evidence_hash": evidence_hash,
        }
    )


def validate_metrics_document_v1(document: Mapping[str, Any]) -> None:
    validate_self_hash_v1(document, "bec8629e2dbdc178d750e795ada7b74aaf0f1475c32c5881c13a2e65c0a92cbf")
    if (
        document.get("authorization_hash") != AUTHORIZATION_HASH
        or document.get("detector_prediction_artifact_hash") != EXPECTED_PREDICTION_HASH
        or document.get("private_metric_evidence_hash") != EXPECTED_PRIVATE_METRIC_EVIDENCE_HASH
        or document.get("point_alarm_count") != EXPECTED_POINT_ALARMS
        or document.get("alarm_episode_count") != EXPECTED_ALARM_EPISODES
    ):
        _fail("PUBLIC_METRIC_BINDING_REJECTED")
    expected = (
        ("attack_event_recall", RECALL_FORMULA, EXPECTED_RECALL),
        ("normal_far_episodes_per_hour", FAR_FORMULA, EXPECTED_FAR),
    )
    for key, formula, value in expected:
        metric = document.get(key)
        if (
            type(metric) is not dict
            or metric.get("metric_name") != key
            or metric.get("formula_identity") != formula
            or metric.get("value") != value
            or metric.get("defined") is not True
            or metric.get("undefined_reason") is not None
            or metric.get("private_evidence_hash") != EXPECTED_PRIVATE_METRIC_EVIDENCE_HASH
            or metric.get("artifact_hash")
            != metric_receipt_hash_v1(key, formula, value, EXPECTED_PRIVATE_METRIC_EVIDENCE_HASH)
        ):
            _fail("PUBLIC_METRIC_SEMANTICS_REJECTED")


ACCOUNTING_REQUIRED = {
    "scientific_execution_attempts": 1,
    "scientific_execution_retries": 0,
    "test1_feature_scientific_parses": 1,
    "score_computations": EXPECTED_ROWS,
    "detector_prediction_freezes": 1,
    "label_scientific_parses": 1,
    "label_before_prediction_access": False,
    "attack_event_derivations": 1,
    "metric_computations": 2,
    "D1_content_reads": 0,
    "D1_executions": 0,
    "D2_executions": 0,
    "OUTER_executions": 0,
    "test2_accesses": 0,
    "hai_test2_opens": 0,
    "hai_test2_hashes": 0,
    "label_test2_opens": 0,
    "summary_label_accesses": 0,
    "result_driven_changes": False,
    "private_paths_exposed": 0,
    "private_preprocessing_values_exposed": 0,
    "private_model_values_exposed": 0,
    "private_pca_values_exposed": 0,
    "private_threshold_values_exposed": 0,
    "private_score_values_exposed": 0,
    "execution_run_hash": EXPECTED_EXECUTION_RUN_HASH,
}


def validate_accounting_document_v1(document: Mapping[str, Any]) -> None:
    validate_self_hash_v1(document, "5ea9f8e0963a7e268f010a74aecc4c2a13a5c0bc0986e583fdbcee3eddf7379c")
    if any(document.get(key) != value for key, value in ACCOUNTING_REQUIRED.items()):
        _fail("EXECUTION_ACCOUNTING_REJECTED")


def _rehash_v1(document: dict[str, Any]) -> dict[str, Any]:
    document["artifact_hash"] = stable_hash_v1(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )
    return document


def synthetic_prediction_v1(count: int = 8) -> dict[str, Any]:
    score_hash = "1" * 64
    records = [
        {
            "physical_row_index": index,
            "alarm_emitted": bool(index % 2),
            "detector_decision_identity": decision_identity_v1(index, bool(index % 2), score_hash),
        }
        for index in range(count)
    ]
    return self_hashed_v1(
        {
            "artifact_type": "ScientificDetectorPredictionArtifactV1",
            "schema_version": SCHEMA_VERSION,
            "execution_mode": EXECUTION_MODE,
            "authorization_hash": AUTHORIZATION_HASH,
            "execution_version": EXECUTION_VERSION,
            "execution_implementation_identity": EXECUTION_IMPLEMENTATION_IDENTITY,
            "execution_implementation_commit": EXECUTION_COMMIT_A,
            "execution_implementation_source_sha256": EXECUTION_SOURCE_SHA256,
            "detector_id": DETECTOR_ID,
            "detector_family": DETECTOR_FAMILY,
            "design_hash": DESIGN_HASH,
            "preprocessing_hash": PREPROCESSING_HASH,
            "model_hash": MODEL_HASH,
            "threshold_hash": THRESHOLD_HASH,
            "feature_set_hash": FEATURE_SET_HASH,
            "feature_order_hash": FEATURE_ORDER_HASH,
            "test1_feature_sha256": TEST1_FEATURE_SHA256,
            "dataset_manifest_id": DATASET_MANIFEST_ID,
            "split_id": INNER_SPLIT_ID,
            "row_count": count,
            "unique_row_count": count,
            "score_vector_content_hash": score_hash,
            "prediction_records": records,
            "point_alarm_count": sum(record["alarm_emitted"] for record in records),
            "label_blind": True,
            "labels_accessed_before_prediction_freeze": False,
            "private_score_values_exposed": 0,
            "private_threshold_value_exposed": 0,
            "private_paths_exposed": 0,
        }
    )


def expect_reject_v1(action: Callable[[], Any]) -> bool:
    try:
        action()
    except D0ResultIntegrityAuditError:
        return True
    return False


def run_adversarial_suite_v1(
    authorization: Mapping[str, Any], metrics: Mapping[str, Any], accounting: Mapping[str, Any]
) -> tuple[int, int]:
    good = synthetic_prediction_v1()
    attacks: list[Callable[[], Any]] = []
    attacks.append(lambda: validate_commit_resolution_v1(lambda commit: commit != RESULT_FREEZE_COMMIT_C))
    attacks.append(lambda: validate_equal_bytes_v1(b"changed", b"frozen"))

    def pred_attack(mutator: Callable[[dict[str, Any]], None]) -> Callable[[], Any]:
        def run() -> Any:
            value = copy.deepcopy(good)
            mutator(value)
            _rehash_v1(value)
            return validate_prediction_document_v1(
                value, expected_count=8, expected_artifact_hash=None
            )
        return run

    attacks.extend(
        (
            pred_attack(lambda d: d.__setitem__("point_alarm_count", d["point_alarm_count"] + 1)),
            pred_attack(lambda d: d["prediction_records"].pop()),
            pred_attack(lambda d: d["prediction_records"].append(copy.deepcopy(d["prediction_records"][-1]))),
            pred_attack(lambda d: d["prediction_records"].__setitem__(slice(0, 2), list(reversed(d["prediction_records"][:2])))),
            pred_attack(lambda d: d["prediction_records"][1].__setitem__("physical_row_index", 0)),
            pred_attack(lambda d: d["prediction_records"][1].__setitem__("physical_row_index", 99)),
            pred_attack(lambda d: d["prediction_records"][1].__setitem__("alarm_emitted", False)),
            pred_attack(lambda d: d["prediction_records"][1].__setitem__("detector_decision_identity", "0" * 64)),
            pred_attack(lambda d: d["prediction_records"][0].__setitem__("label", 1)),
            pred_attack(lambda d: d["prediction_records"][0].__setitem__("attack", True)),
            pred_attack(lambda d: d["prediction_records"][0].__setitem__("score", 1.0)),
            pred_attack(lambda d: d["prediction_records"][0].__setitem__("threshold", 1.0)),
            pred_attack(lambda d: d.__setitem__("authorization_hash", "0" * 64)),
            pred_attack(lambda d: d.__setitem__("model_hash", "0" * 64)),
            pred_attack(lambda d: d.__setitem__("threshold_hash", "0" * 64)),
            pred_attack(lambda d: d.__setitem__("test1_feature_sha256", "0" * 64)),
        )
    )

    def auth_attack(key: str, value: Any) -> Callable[[], Any]:
        def run() -> Any:
            document = copy.deepcopy(dict(authorization)); document[key] = value; _rehash_v1(document)
            return validate_authorization_document_v1(document)
        return run

    attacks.extend(
        (
            auth_attack("threshold_comparison_operator", "score >= threshold"),
            auth_attack("d0_inner_execution_authorized", False),
            auth_attack("d1_rerun_authorized", True),
            auth_attack("d2_authorized", True),
            auth_attack("test2_authorized", True),
        )
    )

    def metric_attack(path: tuple[str, ...], value: Any) -> Callable[[], Any]:
        def run() -> Any:
            document = copy.deepcopy(dict(metrics)); target: Any = document
            for key in path[:-1]: target = target[key]
            target[path[-1]] = value; _rehash_v1(document)
            return validate_metrics_document_v1(document)
        return run

    attacks.extend(
        (
            metric_attack(("attack_event_recall", "formula_identity"), "mutated"),
            metric_attack(("attack_event_recall", "value"), 0.0),
        )
    )

    def accounting_attack(key: str, value: Any) -> Callable[[], Any]:
        def run() -> Any:
            document = copy.deepcopy(dict(accounting)); document[key] = value; _rehash_v1(document)
            return validate_accounting_document_v1(document)
        return run

    attacks.extend(
        (
            accounting_attack("scientific_execution_retries", 1),
            accounting_attack("label_before_prediction_access", True),
            accounting_attack("D1_content_reads", 1),
            accounting_attack("D2_executions", 1),
            accounting_attack("test2_accesses", 1),
            accounting_attack("OUTER_executions", 1),
            accounting_attack("result_driven_changes", True),
            accounting_attack("private_paths_exposed", 1),
        )
    )
    accepted = sum(not expect_reject_v1(attack) for attack in attacks)
    return len(attacks), accepted


def load_bindings_path_silently_v1(root: Path) -> dict[str, str]:
    binding_path = root / ".env.custody.local"
    allowed = {
        "HAI_DATA_ROOT", "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1",
        "TASK039E3_D0_PCA_SPE_MODEL_V1", "TASK039E3_D0_PCA_SPE_THRESHOLD_V1",
        "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_REGISTRY_V1",
        "TASK039E3_UTILITY_NORMAL_ONLY_PRIVATE_LOCATOR_V1",
        "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_REGISTRY_V1",
        "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_PRIVATE_LOCATOR_V1",
    }
    pattern = re.compile(r"^([A-Z0-9_]+)='((?:[^']|'\"'\"')*)'$")
    try:
        if binding_path.is_symlink() or not binding_path.is_file():
            _fail("PRIVATE_BINDINGS_UNAVAILABLE")
        values: dict[str, str] = {}
        for line in binding_path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            match = pattern.fullmatch(line)
            if match is None or match.group(1) not in allowed or match.group(1) in values:
                _fail("PRIVATE_BINDINGS_REJECTED")
            values[match.group(1)] = match.group(2).replace("'\"'\"'", "'")
        required = {
            "HAI_DATA_ROOT", "TASK039E3_D0_PCA_SPE_PREPROCESSING_V1",
            "TASK039E3_D0_PCA_SPE_MODEL_V1", "TASK039E3_D0_PCA_SPE_THRESHOLD_V1",
        }
        if not required.issubset(values):
            _fail("PRIVATE_BINDING_MISSING")
        return values
    except D0ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("PRIVATE_BINDINGS_REJECTED")


def private_regular_file_v1(value: str, root: Path) -> Path:
    try:
        path = Path(value); resolved = path.resolve(strict=True); repository = root.resolve()
        if (
            not path.is_absolute() or path.is_symlink() or not path.is_file()
            or resolved == repository or repository in resolved.parents
        ):
            _fail("PRIVATE_FILE_CUSTODY_REJECTED")
        return path
    except D0ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("PRIVATE_FILE_CUSTODY_REJECTED")


def private_directory_v1(value: str, root: Path) -> Path:
    try:
        path = Path(value); resolved = path.resolve(strict=True); repository = root.resolve()
        if (
            not path.is_absolute() or path.is_symlink() or not path.is_dir()
            or resolved == repository or repository in resolved.parents
        ):
            _fail("PRIVATE_DIRECTORY_CUSTODY_REJECTED")
        return path
    except D0ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("PRIVATE_DIRECTORY_CUSTODY_REJECTED")


def raw_hash_v1(path: Path, expected_size: int, expected_hash: str) -> None:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != expected_size:
            _fail("PRIVATE_RAW_IDENTITY_REJECTED")
        digest = sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected_hash:
            _fail("PRIVATE_RAW_HASH_REJECTED")
    except D0ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("PRIVATE_RAW_IDENTITY_REJECTED")


def load_private_json_v1(path: Path, expected_hash: str) -> dict[str, Any]:
    document = strict_json_v1(path.read_bytes())
    validate_self_hash_v1(document, expected_hash)
    return document


def decode_private_model_v1(
    preprocessing: Mapping[str, Any], model: Mapping[str, Any], threshold: Mapping[str, Any]
) -> tuple[Any, Any, Any, float, tuple[str, ...]]:
    import numpy as np

    required_pre = {
        "detector_id": DETECTOR_ID, "design_hash": DESIGN_HASH,
        "feature_order_hash": FEATURE_ORDER_HASH, "combined_row_count": 572_400,
        "python_version": PYTHON_VERSION, "numpy_version": NUMPY_VERSION,
    }
    required_model = {
        "detector_id": DETECTOR_ID, "design_hash": DESIGN_HASH,
        "preprocessing_hash": PREPROCESSING_HASH, "feature_order_hash": FEATURE_ORDER_HASH,
        "fit_row_count": 572_400, "python_version": PYTHON_VERSION,
        "numpy_version": NUMPY_VERSION, "selected_k": SELECTED_K,
        "explained_variance_target": 0.95, "labels_used": False, "test_accessed": False,
    }
    required_threshold = {
        "detector_id": DETECTOR_ID, "design_hash": DESIGN_HASH, "model_hash": MODEL_HASH,
        "calibration_row_count": 126_000, "alpha": 0.001, "upper_quantile": 0.999,
        "q_index": 125_873, "comparison_operator": THRESHOLD_COMPARATOR,
        "labels_used": False, "test_used": False,
    }
    if any(preprocessing.get(k) != v for k, v in required_pre.items()):
        _fail("PRIVATE_PREPROCESSING_REJECTED")
    if any(model.get(k) != v for k, v in required_model.items()):
        _fail("PRIVATE_MODEL_REJECTED")
    if any(threshold.get(k) != v for k, v in required_threshold.items()):
        _fail("PRIVATE_THRESHOLD_REJECTED")
    means_hex = preprocessing.get("means_float_hex"); scales_hex = preprocessing.get("scales_float_hex")
    loadings_hex = model.get("retained_loadings_float_hex"); threshold_hex = threshold.get("threshold_float_hex")
    eigen_hex = model.get("eigenvalues_float_hex")
    if (
        type(means_hex) is not list or len(means_hex) != FEATURE_COUNT
        or type(scales_hex) is not list or len(scales_hex) != FEATURE_COUNT
        or type(loadings_hex) is not list or len(loadings_hex) != FEATURE_COUNT
        or any(type(row) is not list or len(row) != SELECTED_K for row in loadings_hex)
        or type(eigen_hex) is not list or len(eigen_hex) != FEATURE_COUNT
        or type(threshold_hex) is not str
    ):
        _fail("PRIVATE_NUMERIC_SCHEMA_REJECTED")
    try:
        means = np.asarray([float.fromhex(value) for value in means_hex], dtype=np.float64)
        scales = np.asarray([float.fromhex(value) for value in scales_hex], dtype=np.float64)
        loadings = np.asarray(
            [[float.fromhex(value) for value in row] for row in loadings_hex], dtype=np.float64
        )
        threshold_value = float.fromhex(threshold_hex)
        sensitive_hex = tuple(means_hex) + tuple(scales_hex) + tuple(eigen_hex) + tuple(
            value for row in loadings_hex for value in row
        ) + (threshold_hex,)
    except BaseException:
        _fail("PRIVATE_NUMERIC_DECODE_REJECTED")
    if (
        means.shape != (FEATURE_COUNT,) or scales.shape != (FEATURE_COUNT,)
        or loadings.shape != (FEATURE_COUNT, SELECTED_K)
        or means.dtype != np.float64 or scales.dtype != np.float64 or loadings.dtype != np.float64
        or not bool(np.isfinite(means).all()) or not bool(np.isfinite(scales).all())
        or not bool(np.isfinite(loadings).all()) or bool((scales <= 0.0).any())
        or not math.isfinite(threshold_value)
    ):
        _fail("PRIVATE_NUMERIC_VALUE_REJECTED")
    return means, scales, loadings, threshold_value, sensitive_hex


def parse_feature_frame_once_v1(path: Path) -> tuple[Any, tuple[str, ...]]:
    import numpy as np

    matrix = np.empty((EXPECTED_ROWS, FEATURE_COUNT), dtype=np.float64)
    timestamps: list[str] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream); header = next(reader)
            if len(header) != len(set(header)) or "timestamp" not in header:
                _fail("TEST1_FEATURE_HEADER_REJECTED")
            if tuple(name for name in header if name.startswith("P1_")) != P1_FEATURE_ORDER:
                _fail("TEST1_FEATURE_ORDER_REJECTED")
            timestamp_index = header.index("timestamp")
            indices = tuple(header.index(name) for name in P1_FEATURE_ORDER)
            count = 0
            for count, row in enumerate(reader, start=1):
                if count > EXPECTED_ROWS or len(row) != len(header):
                    _fail("TEST1_FEATURE_CLOSURE_REJECTED")
                timestamps.append(row[timestamp_index])
                matrix[count - 1, :] = [float(row[index]) for index in indices]
    except D0ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("TEST1_FEATURE_PARSE_REJECTED")
    if (
        len(timestamps) != EXPECTED_ROWS or len(set(timestamps)) != EXPECTED_ROWS
        or matrix.shape != (EXPECTED_ROWS, FEATURE_COUNT) or matrix.dtype != np.float64
        or not bool(np.isfinite(matrix).all())
    ):
        _fail("TEST1_FEATURE_FRAME_REJECTED")
    return matrix, tuple(timestamps)


def independent_score_oracle_v1(matrix: Any, means: Any, scales: Any, loadings: Any) -> Any:
    import numpy as np

    standardized = (matrix - means) / scales
    projection = (standardized @ loadings) @ loadings.T
    residual = standardized - projection
    scores = np.sum(residual ** 2, axis=1, dtype=np.float64)
    if scores.shape != (EXPECTED_ROWS,) or scores.dtype != np.float64 or not bool(np.isfinite(scores).all()):
        _fail("SCORE_ORACLE_REJECTED")
    return scores


def score_evidence_hashes_v1(scores: Any) -> tuple[str, str]:
    values = [float(value).hex() for value in scores]
    content_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_d0_test1_score_vector_v1",
            "canonical_representation": "PYTHON_FLOAT_HEX_ROW_ORDER",
            "row_count": EXPECTED_ROWS,
            "scores_float_hex": values,
        }
    )
    evidence_hash = stable_hash_v1(
        {
            "artifact_type": "D0Test1ScoreEvidenceV1",
            "schema_version": SCHEMA_VERSION,
            "authorization_hash": AUTHORIZATION_HASH,
            "design_hash": DESIGN_HASH,
            "preprocessing_hash": PREPROCESSING_HASH,
            "model_hash": MODEL_HASH,
            "threshold_hash": THRESHOLD_HASH,
            "test1_feature_sha256": TEST1_FEATURE_SHA256,
            "feature_order_hash": FEATURE_ORDER_HASH,
            "row_count": EXPECTED_ROWS,
            "canonical_score_representation": "PYTHON_FLOAT_HEX_ROW_ORDER",
            "scores_float_hex": values,
            "score_vector_content_hash": content_hash,
        }
    )
    return evidence_hash, content_hash


Interval = tuple[int, int]


def form_alarm_episodes_v1(indices: Sequence[int]) -> tuple[Interval, ...]:
    ordered = sorted(set(indices))
    if not ordered:
        return ()
    episodes: list[Interval] = []
    start = previous = ordered[0]
    for index in ordered[1:]:
        if type(index) is not int or index < 0:
            _fail("ALARM_INDEX_REJECTED")
        if index == previous + 1:
            previous = index; continue
        episodes.append((start, previous + 1)); start = previous = index
    episodes.append((start, previous + 1))
    return tuple(episodes)


def parse_label_once_v1(path: Path, timestamps: tuple[str, ...]) -> tuple[int, ...]:
    observed_timestamps: list[str] = []; labels: list[int] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            if next(reader) != ["timestamp", "label"]:
                _fail("TEST1_LABEL_HEADER_REJECTED")
            for row in reader:
                if len(row) != 2 or row[1] not in {"0", "1"}:
                    _fail("TEST1_LABEL_VALUE_REJECTED")
                observed_timestamps.append(row[0]); labels.append(0 if row[1] == "0" else 1)
    except D0ResultIntegrityAuditError:
        raise
    except BaseException:
        _fail("TEST1_LABEL_PARSE_REJECTED")
    if tuple(observed_timestamps) != timestamps or len(labels) != EXPECTED_ROWS:
        _fail("TEST1_LABEL_ALIGNMENT_REJECTED")
    return tuple(labels)


def derive_attack_events_v1(labels: Sequence[int]) -> tuple[Interval, ...]:
    events: list[Interval] = []; start: int | None = None
    for index, value in enumerate((*labels, 0)):
        if type(value) is not int or value not in {0, 1}:
            _fail("STRICT_LABEL_REJECTED")
        if value == 1 and start is None:
            start = index
        elif value == 0 and start is not None:
            events.append((start, index)); start = None
    return tuple(events)


def overlap_v1(left: Interval, right: Interval) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def interval_set_hash_v1(kind: str, intervals: tuple[Interval, ...]) -> str:
    return stable_hash_v1(
        {
            "artifact_type": f"task039e3_r2r_private_d0_{kind}_interval_set_v1",
            "interval_semantics": "HALF_OPEN_FILE_LOCAL_ONE_SECOND",
            "intervals": [{"start": start, "end": end} for start, end in intervals],
        }
    )


def private_metric_evidence_hash_v1(
    labels: tuple[int, ...], attacks: tuple[Interval, ...], alarms: tuple[Interval, ...],
    score_evidence_hash: str, score_content_hash: str,
) -> tuple[str, float, float]:
    label_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_private_d0_strict_label_vector_v1",
            "label_file_sha256": TEST1_LABEL_SHA256,
            "labels": list(labels),
        }
    )
    attack_hash = interval_set_hash_v1("attack", attacks)
    alarm_hash = interval_set_hash_v1("alarm", alarms)
    recall_numerator = sum(any(overlap_v1(attack, alarm) for alarm in alarms) for attack in attacks)
    far_numerator = sum(not any(overlap_v1(alarm, attack) for attack in attacks) for alarm in alarms)
    normal_seconds = EXPECTED_ROWS - sum(labels)
    recall_value = recall_numerator / len(attacks) if attacks else math.nan
    far_value = far_numerator / (normal_seconds / 3600.0) if normal_seconds else math.nan
    evidence_hash = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_inner_d0_private_metric_evidence_v1",
            "schema_version": SCHEMA_VERSION,
            "authorization_hash": AUTHORIZATION_HASH,
            "strict_label_vector_hash": label_hash,
            "attack_event_set_hash": attack_hash,
            "detector_alarm_episode_set_hash": alarm_hash,
            "attack_event_recall": {"numerator": recall_numerator, "denominator": len(attacks)},
            "normal_far_episodes_per_hour": {
                "numerator": far_numerator,
                "normal_second_denominator": normal_seconds,
                "normal_hour_denominator": normal_seconds / 3600.0,
            },
            "strict_label_vector": list(labels),
            "attack_events": [{"start": start, "end": end} for start, end in attacks],
            "alarm_episodes": [{"start": start, "end": end} for start, end in alarms],
            "score_evidence_hash": score_evidence_hash,
            "score_vector_content_hash": score_content_hash,
            "detector_prediction_artifact_hash": EXPECTED_PREDICTION_HASH,
        }
    )
    return evidence_hash, recall_value, far_value


def iter_keys_v1(value: Any) -> Sequence[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key)); keys.extend(iter_keys_v1(child))
    elif isinstance(value, list):
        for child in value: keys.extend(iter_keys_v1(child))
    return keys


def audit_leakage_v1(
    root: Path, bindings: Mapping[str, str], sensitive_hex: Sequence[str]
) -> dict[str, int | str]:
    forbidden_keys = {
        "means_float_hex", "scales_float_hex", "eigenvalues_float_hex",
        "retained_loadings_float_hex", "threshold_float_hex", "scores_float_hex",
        "strict_label_vector", "labels", "attack_events", "alarm_episodes",
        "normal_second_denominator", "normal_hour_denominator",
    }
    private_tokens = tuple(bindings.values())
    for relative in RESULT_C_PATHS:
        content = (root / relative).read_bytes()
        text = content.decode("utf-8")
        if re.search(r"(?:[A-Za-z]:[\\/]|/(?:Users|home|tmp|var)/)", text):
            _fail("PRIVATE_PATH_LEAKAGE_REJECTED")
        if any(token and token in text for token in private_tokens):
            _fail("PRIVATE_PATH_TOKEN_LEAKAGE_REJECTED")
        if any(token and token in text for token in sensitive_hex):
            _fail("PRIVATE_NUMERIC_LEAKAGE_REJECTED")
        if relative.endswith(".json"):
            document = strict_json_v1(content)
            if forbidden_keys.intersection(iter_keys_v1(document)):
                _fail("PRIVATE_SCHEMA_LEAKAGE_REJECTED")
    return {
        "leak_scan_status": "LEAK_SCAN_PASS",
        "private_paths_exposed": 0,
        "private_preprocessing_values_exposed": 0,
        "private_pca_values_exposed": 0,
        "private_threshold_values_exposed": 0,
        "private_score_values_exposed": 0,
        "label_vectors_exposed": 0,
        "attack_intervals_exposed": 0,
        "private_metric_denominators_exposed": 0,
    }


def utc_now_v1() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_reports_v1(root: Path, outcome: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    audit_commit = git_text_v1(root, ("log", "-1", "--format=%H", "--", "scripts/audit_task039e3_r2r_d0_result_integrity_v1.py"))
    if audit_commit != git_text_v1(root, ("rev-parse", "HEAD")):
        _fail("AUDIT_COMMIT_A_NOT_FROZEN")
    created = utc_now_v1()
    common = {"schema_version": SCHEMA_VERSION, "task_id": TASK_ID, "created_at_utc": created}
    reports: dict[str, dict[str, Any]] = {}
    reports["FREEZE_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_freeze_audit",
        **common, "status": "PASS", "audit_commit_a": audit_commit,
        "base_commit": CONTINUITY_COMMIT_D, "execution_commit_a": EXECUTION_COMMIT_A,
        "independent_commit_b": INDEPENDENT_COMMIT_B,
        "result_freeze_commit_c": RESULT_FREEZE_COMMIT_C,
        "continuity_commit_d": CONTINUITY_COMMIT_D,
        **outcome["git"], "remote_egress_status": REMOTE_EGRESS_STATUS,
        "push_attempted": False,
    })
    reports["SCORE_ORACLE"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_score_oracle",
        **common, "status": "PASS", "numeric_backend": "NUMPY_LINEAR_ALGEBRA",
        "python_version": PYTHON_VERSION, "numpy_version": NUMPY_VERSION,
        "preprocessing_hash_match": True, "model_hash_match": True,
        "threshold_hash_match": True, "test1_feature_hash_match": True,
        "feature_count": FEATURE_COUNT, "score_oracle_row_count": EXPECTED_ROWS,
        "score_evidence_hash": EXPECTED_SCORE_EVIDENCE_HASH,
        "score_evidence_hash_match": True, "score_values_public": False,
        "audit_authoritative_d0_executions": 0,
        "audit_authoritative_model_fits": 0,
        "audit_authoritative_threshold_calibrations": 0,
    })
    reports["PREDICTION_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_prediction_audit",
        **common, "status": "PASS", "detector_prediction_artifact_hash": EXPECTED_PREDICTION_HASH,
        "artifact_hash_match": True, "record_count": EXPECTED_ROWS,
        "unique_row_count": EXPECTED_ROWS, "physical_index_closure": True,
        "point_alarm_oracle": EXPECTED_POINT_ALARMS, "point_alarm_match": True,
        "alarm_episode_oracle": EXPECTED_ALARM_EPISODES, "alarm_episode_match": True,
        "label_blind_schema_pass": True, "private_score_values_exposed": 0,
        "private_threshold_values_exposed": 0,
    })
    reports["LABEL_INDEPENDENCE_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_label_independence_audit",
        **common, "status": "PASS", "prediction_before_label_enforced": True,
        "label_guard_present": True, "prediction_persisted_and_validated_first": True,
        "metric_stage_reloads_prediction": True, "final_prediction_byte_recheck": True,
        "test1_label_hash_match": True, "audit_label_parses": 1,
        "label_influenced_score_or_point_alarm": False, "attack_event_oracle_pass": True,
        "D1_content_reads": 0, "test2_accesses": 0,
    })
    reports["METRIC_ORACLE"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_metric_oracle",
        **common, "status": "PASS", "attack_event_recall_formula": RECALL_FORMULA,
        "attack_event_recall_formula_match": True, "attack_event_recall_value": EXPECTED_RECALL,
        "attack_event_recall_value_match": True, "normal_far_formula": FAR_FORMULA,
        "normal_far_formula_match": True, "normal_far_value": EXPECTED_FAR,
        "normal_far_value_match": True,
        "private_metric_evidence_hash": EXPECTED_PRIVATE_METRIC_EVIDENCE_HASH,
        "private_metric_evidence_hash_match": True,
        "private_metric_denominators_public": False,
    })
    reports["ACCOUNTING_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_accounting_audit",
        **common, "status": "PASS", "original_scientific_execution_attempts": 1,
        "original_scientific_execution_retries": 0,
        "audit_test1_feature_parses": 1, "audit_score_recomputations": EXPECTED_ROWS,
        "audit_point_alarm_recomputations": EXPECTED_ROWS, "audit_label_parses": 1,
        "audit_attack_event_derivations": 1, "audit_metric_recomputations": 2,
        "audit_authoritative_d0_executions": 0, "audit_authoritative_model_fits": 0,
        "audit_authoritative_threshold_calibrations": 0,
        "D1_content_reads": 0, "D1_executions": 0, "D2_executions": 0,
        "OUTER_executions": 0, "test2_accesses": 0,
        "result_driven_changes": False,
    })
    reports["LEAKAGE_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_leakage_audit",
        **common, "status": "PASS", **outcome["leakage"],
    })
    reports["INDEPENDENT_AUDIT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_independent_audit",
        **common, "status": "PASS", "independent_attacks": outcome["independent_attacks"],
        "accepted_invalid": outcome["accepted_invalid"],
        "public_artifact_mutations_only": True, "private_data_used_by_attacks": False,
    })
    reports["READINESS"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_readiness",
        **common, "status": PASS_STATUS, "scientific_status": SCIENTIFIC_STATUS,
        "remote_egress_status": REMOTE_EGRESS_STATUS,
        "freeze_audit_hash": reports["FREEZE_AUDIT"]["artifact_hash"],
        "score_oracle_hash": reports["SCORE_ORACLE"]["artifact_hash"],
        "prediction_audit_hash": reports["PREDICTION_AUDIT"]["artifact_hash"],
        "label_independence_audit_hash": reports["LABEL_INDEPENDENCE_AUDIT"]["artifact_hash"],
        "metric_oracle_hash": reports["METRIC_ORACLE"]["artifact_hash"],
        "accounting_audit_hash": reports["ACCOUNTING_AUDIT"]["artifact_hash"],
        "leakage_audit_hash": reports["LEAKAGE_AUDIT"]["artifact_hash"],
        "independent_audit_hash": reports["INDEPENDENT_AUDIT"]["artifact_hash"],
        "UTILITY_INNER_D0_EXECUTED": True, "UTILITY_INNER_D0_RESULT_FROZEN": True,
        "UTILITY_INNER_D0_RESULT_INTEGRITY_AUDITED": True,
        "UTILITY_INNER_D0_RESULT_INTERPRETATION_READY": True,
        "UTILITY_INNER_D2_AUTHORIZED": False,
        "UTILITY_OUTER_EXECUTION_AUTHORIZED": False,
        "exact_next_task": "TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-AND-FREEZE-V1",
    })
    reports["BUNDLE"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_bundle",
        **common, "status": "PASS", "authorization_hash": AUTHORIZATION_HASH,
        "committed_execution_grant_hash": COMMITTED_GRANT_HASH,
        "execution_implementation_identity": EXECUTION_IMPLEMENTATION_IDENTITY,
        "detector_prediction_artifact_hash": EXPECTED_PREDICTION_HASH,
        "score_evidence_hash": EXPECTED_SCORE_EVIDENCE_HASH,
        "private_metric_evidence_hash": EXPECTED_PRIVATE_METRIC_EVIDENCE_HASH,
        **{f"{name.lower()}_hash": reports[name]["artifact_hash"] for name in REPORT_BASENAMES[:9]},
    })
    reports["RECEIPT"] = self_hashed_v1({
        "artifact_type": "task039e3_r2r_utility_inner_d0_result_integrity_v1_receipt",
        **common, "status": PASS_STATUS, "scientific_status": SCIENTIFIC_STATUS,
        "remote_egress_status": REMOTE_EGRESS_STATUS, "push_attempted": False,
        "readiness_hash": reports["READINESS"]["artifact_hash"],
        "bundle_hash": reports["BUNDLE"]["artifact_hash"],
        "post_freeze_mutations": 0, "accepted_invalid": 0,
        "audit_authoritative_d0_executions": 0, "D1_content_reads": 0,
        "D1_executions": 0, "D2_executions": 0, "OUTER_executions": 0,
        "test2_accesses": 0, "result_driven_changes": False,
        "private_paths_exposed": 0, "private_preprocessing_values_exposed": 0,
        "private_model_values_exposed": 0, "private_pca_values_exposed": 0,
        "private_threshold_values_exposed": 0, "private_score_values_exposed": 0,
        "exact_next_task": "TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-AND-FREEZE-V1",
    })
    return reports


def write_reports_v1(root: Path, reports: Mapping[str, Mapping[str, Any]]) -> None:
    directory = root / "docs/task_reports"
    targets: list[tuple[Path, bytes]] = []
    for basename in REPORT_BASENAMES:
        filename = f"TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_{basename}.json"
        content = (json.dumps(reports[basename], sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
        targets.append((directory / filename, content))
    report = (
        "# TASK-039E3-R2R Utility INNER D0 Result Integrity Audit V1\n\n"
        f"Status: `{PASS_STATUS}`\n\nScientific status: `{SCIENTIFIC_STATUS}`\n\n"
        f"Remote state: `{REMOTE_EGRESS_STATUS}`\n\n"
        "The exact local frozen D0 result passed independent Git, authorization, "
        "implementation, score, prediction, label-order, metric, accounting, and leakage audits. "
        "No authoritative D0 execution, D1 content read, D2 execution, test2 access, result mutation, "
        "or remote egress occurred.\n\n"
        f"- DetectorPrediction: `{EXPECTED_PREDICTION_HASH}`\n"
        f"- Point alarm oracle: `{EXPECTED_POINT_ALARMS}`\n"
        f"- Alarm episode oracle: `{EXPECTED_ALARM_EPISODES}`\n"
        f"- Attack-event Recall oracle: `{EXPECTED_RECALL}`\n"
        f"- Normal FAR episodes/hour oracle: `{EXPECTED_FAR}`\n\n"
        "Exact next task: `TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-AND-FREEZE-V1`.\n"
    ).encode("utf-8")
    targets.append((directory / "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_V1_REPORT.md", report))
    for path, _ in targets:
        if path.exists() or path.is_symlink() or path.with_suffix(path.suffix + ".tmp").exists():
            _fail("AUDIT_REPORT_ALREADY_EXISTS")
    for path, content in targets:
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("xb") as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
    for path, content in targets:
        temporary = path.with_suffix(path.suffix + ".tmp"); os.replace(temporary, path)
        if path.read_bytes() != content:
            _fail("AUDIT_REPORT_REPLAY_REJECTED")


def run_audit_v1() -> dict[str, Any]:
    root = repository_root_v1()
    git_audit = audit_local_git_v1(root)
    authorization_audit = audit_authorization_replay_v1(root)

    prediction = strict_json_v1((root / PREDICTION_PATH).read_bytes())
    metrics = strict_json_v1((root / METRICS_PATH).read_bytes())
    accounting = strict_json_v1((root / ACCOUNTING_PATH).read_bytes())
    validate_prediction_document_v1(prediction)
    validate_metrics_document_v1(metrics)
    validate_accounting_document_v1(accounting)

    bindings = load_bindings_path_silently_v1(root)
    hai_root = private_directory_v1(bindings["HAI_DATA_ROOT"], root)
    preprocessing_path = private_regular_file_v1(bindings["TASK039E3_D0_PCA_SPE_PREPROCESSING_V1"], root)
    model_path = private_regular_file_v1(bindings["TASK039E3_D0_PCA_SPE_MODEL_V1"], root)
    threshold_path = private_regular_file_v1(bindings["TASK039E3_D0_PCA_SPE_THRESHOLD_V1"], root)
    preprocessing = load_private_json_v1(preprocessing_path, PREPROCESSING_HASH)
    model = load_private_json_v1(model_path, MODEL_HASH)
    threshold = load_private_json_v1(threshold_path, THRESHOLD_HASH)
    means, scales, loadings, threshold_value, sensitive_hex = decode_private_model_v1(
        preprocessing, model, threshold
    )
    if platform.python_implementation() != "CPython" or platform.python_version() != PYTHON_VERSION:
        _fail("PYTHON_BACKEND_REJECTED")
    import numpy as np
    if np.__version__ != NUMPY_VERSION:
        _fail("NUMPY_BACKEND_REJECTED")

    feature_path = hai_root / "hai-23.05" / "hai-test1.csv"
    raw_hash_v1(feature_path, TEST1_FEATURE_SIZE, TEST1_FEATURE_SHA256)
    matrix, timestamps = parse_feature_frame_once_v1(feature_path)
    scores = independent_score_oracle_v1(matrix, means, scales, loadings)
    score_evidence_hash, score_content_hash = score_evidence_hashes_v1(scores)
    if score_evidence_hash != EXPECTED_SCORE_EVIDENCE_HASH or score_content_hash != EXPECTED_SCORE_VECTOR_CONTENT_HASH:
        _fail("SCORE_EVIDENCE_HASH_REJECTED")
    alarm_mask = scores > np.float64(threshold_value)
    alarm_indices = tuple(int(index) for index in np.flatnonzero(alarm_mask))
    if len(alarm_indices) != EXPECTED_POINT_ALARMS:
        _fail("POINT_ALARM_ORACLE_REJECTED")
    _, committed_alarm_indices = validate_prediction_document_v1(prediction)
    if alarm_indices != committed_alarm_indices:
        _fail("POINT_ALARM_SET_REJECTED")
    alarm_episodes = form_alarm_episodes_v1(committed_alarm_indices)
    if len(alarm_episodes) != EXPECTED_ALARM_EPISODES:
        _fail("ALARM_EPISODE_ORACLE_REJECTED")

    label_path = hai_root / "hai-23.05" / "label-test1.csv"
    raw_hash_v1(label_path, TEST1_LABEL_SIZE, TEST1_LABEL_SHA256)
    labels = parse_label_once_v1(label_path, timestamps)
    attack_events = derive_attack_events_v1(labels)
    private_metric_hash, recall_value, far_value = private_metric_evidence_hash_v1(
        labels, attack_events, alarm_episodes, score_evidence_hash, score_content_hash
    )
    if private_metric_hash != EXPECTED_PRIVATE_METRIC_EVIDENCE_HASH:
        _fail("PRIVATE_METRIC_EVIDENCE_REJECTED")
    if not math.isclose(recall_value, EXPECTED_RECALL, rel_tol=0.0, abs_tol=METRIC_ABS_TOLERANCE):
        _fail("RECALL_ORACLE_REJECTED")
    if not math.isclose(far_value, EXPECTED_FAR, rel_tol=0.0, abs_tol=METRIC_ABS_TOLERANCE):
        _fail("FAR_ORACLE_REJECTED")

    leakage = audit_leakage_v1(root, bindings, sensitive_hex)
    authorization = strict_json_v1((root / AUTHORIZATION_PATHS["authorization"]).read_bytes())
    independent_attacks, accepted_invalid = run_adversarial_suite_v1(
        authorization, metrics, accounting
    )
    if accepted_invalid != 0:
        _fail("ADVERSARIAL_ACCEPTED_INVALID")

    outcome = {
        "git": git_audit,
        "authorization": authorization_audit,
        "leakage": leakage,
        "independent_attacks": independent_attacks,
        "accepted_invalid": accepted_invalid,
    }
    reports = build_reports_v1(root, outcome)
    write_reports_v1(root, reports)
    return {
        "status": PASS_STATUS,
        "scientific_status": SCIENTIFIC_STATUS,
        "remote_egress_status": REMOTE_EGRESS_STATUS,
        "independent_attacks": independent_attacks,
        "accepted_invalid": accepted_invalid,
        "report_hashes": {name: reports[name]["artifact_hash"] for name in REPORT_BASENAMES},
    }


def main() -> int:
    if sys.argv[1:]:
        print("D0_RESULT_INTEGRITY_AUDIT_ARGUMENTS_REJECTED")
        return 2
    try:
        outcome = run_audit_v1()
    except D0ResultIntegrityAuditError as error:
        print(error.code)
        return 1
    except BaseException:
        print("D0_RESULT_INTEGRITY_AUDIT_INTERNAL_BLOCKED")
        return 1
    print(outcome["status"])
    print(outcome["scientific_status"])
    print(outcome["remote_egress_status"])
    print(f"INDEPENDENT_ATTACKS={outcome['independent_attacks']}")
    print(f"ACCEPTED_INVALID={outcome['accepted_invalid']}")
    for name, digest in outcome["report_hashes"].items():
        print(f"{name}_HASH={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
