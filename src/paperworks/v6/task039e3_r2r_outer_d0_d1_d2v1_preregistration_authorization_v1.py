"""Sealed three-arm OUTER preregistration and execution authorization.

This module is deliberately non-scientific.  It replays public frozen
authorities, defines immutable contracts, issues one process-local
authorization, and serializes sanitized reports.  It never resolves, opens,
hashes, or parses either real test2 file and contains no model, rule, fusion,
label, event, episode, or metric execution entry point.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[3]
REPORT_ROOT = ROOT / "docs" / "task_reports"
TASK_ID = "TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-PREREGISTRATION-AND-AUTHORIZATION-V1"
STATUS = "passed_task039e3_r2r_utility_outer_d0_d1_d2v1_preregistration_and_authorization_v1"
BRANCH = "task-039e3-r2r-utility-outer-d0-d1-d2v1-preregistration-authorization-v1"
BASE = "634231bb91c57df39eded6d869abe6a2853ae1d1"
NEXT_TASK = "TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-EXECUTION-V1"
SCHEME = "MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"

OUTER_PREREGISTRATION_VERSION = "OuterThreeArmPreregistrationV1"
OUTER_AUTHORIZATION_VERSION = "TASK039E3_R2R_OUTER_D0_D1_D2V1_EXECUTION_AUTHORIZATION_V1"
OUTER_AUTHORIZATION_SCOPE = "HAI_23_05_P1_TEST2_D0_D1_D2V1_CONFIRMATORY_OUTER_V1"
OUTER_SCIENTIFIC_QUESTION_V1 = (
    "Do the frozen Detector-only, verified Rule-only, and D2 V1 Combined "
    "arms generalize to the sealed HAI-23.05 test2 split under exactly the "
    "same scientific authorities and evaluation semantics, without any "
    "OUTER-driven recalibration or redesign?"
)
OUTER_ARMS = ("OUTER_D0_DETECTOR_ONLY", "OUTER_D1_RULE_ONLY", "OUTER_D2_V1_COMBINED")

DATASET_MANIFEST_SHA256 = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
GLOBAL_HEADER_SHA256 = "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a"
TEST2_FEATURE_MANIFEST_PATH = "hai-23.05/hai-test2.csv"
TEST2_FEATURE_SHA256 = "b2b8dd295aefd87e39260fe43cb4c73ee86d6264b0ac4b0761e7efb0c2b545c3"
TEST2_LABEL_MANIFEST_PATH = "hai-23.05/label-test2.csv"
TEST2_LABEL_SHA256 = "8090c44981176e39b0f01a7126a80248ac0b93355c00f9db4d4e2f2106452b92"
TEST2_ROW_COUNT = 230400
HAI_REPOSITORY_SNAPSHOT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"

D0_ID = "D0_PCA_SPE_V1"
D0_DESIGN_SHA256 = "357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174"
D0_IMPLEMENTATION_IDENTITY = "8f00469a632643cd10cc4257f5d1fe380036c7763b03cb70b13d01815a287ee2"
D0_MODEL_SHA256 = "f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b"
D0_THRESHOLD_SHA256 = "7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695"

D1_PORTFOLIO = "COMMON-42"
D1_RELATION_COUNT = 42
D1_CONSTRUCTION_AUTHORITY_SHA256 = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"
D1_DESCRIPTOR_SHA256 = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
D1_REFERENCE_SET_SHA256 = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"
D1_REFERENCE_COUNT = 420
D1_REGISTRY_SHA256 = "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
D1_EVALUATOR_IDENTITY = "af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5"

D2_V1_ID = "D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_V1"
D2_V1_FUSION_FAMILY = "DETECTOR_PRESERVING_MULTI_SOURCE_RULE_CORROBORATION"
D2_V1_DESIGN_SHA256 = "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
D2_SOURCE_MAP_SHA256 = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
D2_SOURCE_MAP_ENTRY_COUNT = 42
D2_SOURCE_MAP_DISTINCT_SOURCES = 9
D2_REQUIRED_DISTINCT_SOURCES = 2

ATTACK_EVENT_POLICY = "MAXIMAL_CONTIGUOUS_STRICT_LABEL_ONE_RUNS_FILE_LOCAL"
ALARM_EPISODE_POLICY = "MAXIMAL_CONTIGUOUS_UNIQUE_ONE_SECOND_DECISION_INDICES_FILE_LOCAL"
PRIMARY_METRICS = ("ATTACK_EVENT_RECALL", "NORMAL_FAR_EPISODES_PER_HOUR")
SECONDARY_METRICS = (
    "D0_MISSED_ATTACKS_DETECTED_BY_D1",
    "D1_POTENTIAL_D0_MISS_RECOVERY_RATE",
    "D0_D1_ATTACK_EVENT_UNION_COVERAGE",
    "D2_D0_MISSED_ATTACK_RECOVERY_RATE",
    "D2_INCREMENTAL_ATTACK_EVENT_RECALL_VERSUS_D0",
    "D2_ADDED_NORMAL_RULE_RECOVERY_FAR_PER_HOUR",
    "D2_INCREMENTAL_NORMAL_FAR_PER_HOUR_VERSUS_D0",
)
EXECUTION_ORDER = (
    "REPLAY_OUTER_AUTHORIZATION",
    "VALIDATE_FROZEN_DATASET_MANIFEST",
    "VALIDATE_D0_AUTHORITY",
    "VALIDATE_D1_AUTHORITY",
    "VALIDATE_D2_V1_AUTHORITY",
    "VALIDATE_PRIVATE_CUSTODY",
    "OPEN_AND_HASH_TEST2_FEATURE",
    "REQUIRE_TEST2_FEATURE_SHA_EXACT",
    "PARSE_TEST2_FEATURE_EXACTLY_ONCE",
    "FREEZE_OUTER_TEST2_FEATURE_SNAPSHOT_V1",
    "EXECUTE_D0_INFERENCE",
    "FREEZE_OUTER_D0_PREDICTION_V1",
    "EXECUTE_D1_RULE_EVALUATION_FROM_SAME_SNAPSHOT",
    "FREEZE_OUTER_D1_PREDICTION_V1",
    "EXECUTE_D2_V1_FUSION",
    "FREEZE_OUTER_D2_V1_COMBINED_PREDICTION_V1",
    "DURABLY_REOPEN_AND_VALIDATE_ALL_THREE_PREDICTIONS",
    "OPEN_AND_HASH_TEST2_LABEL",
    "REQUIRE_TEST2_LABEL_SHA_EXACT",
    "PARSE_TEST2_LABEL_EXACTLY_ONCE",
    "DERIVE_ATTACK_EVENTS",
    "DERIVE_D0_D1_D2_ALARM_EPISODES",
    "COMPUTE_PREREGISTERED_METRICS",
    "FREEZE_PRIVATE_METRIC_EVIDENCE",
    "FREEZE_SANITIZED_OUTER_RESULT",
    "STOP",
)
TRIGGER_CLASSES = ("NONE", "D0_ONLY", "RULE_RECOVERY", "D0_AND_RULE_CORROBORATION")

STATIC_TESTS = 31
INDEPENDENT_ATTACKS = 22

DATASET_MANIFEST_PATH = REPORT_ROOT / "TASK-039A_DATASET_MANIFEST_V2.json"
PUBLIC_AUTHORITIES = {
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_DESIGN_V1_DESIGN.json":
        "3ffcec30d2bc605bf0b4ca15f80fcc3ed40aa283b6ae913e767c0ad9db18ece7",
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_MODEL_RECEIPT.json":
        "913f4a4bcf1771146f9493cded893b10eb97d2d177fe224f855c289d81ef1362",
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D0_TRAINING_V1_THRESHOLD_RECEIPT.json":
        "2ee6fc8aba25d23449c14b08deae2eca0c5b739f6a251e43ead41923c978d326",
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D0_RESULT_INTEGRITY_REPORT_HASH_R1_RECEIPT.json":
        "8f11f019f04e812f3a06f048b466256dfed0ad9b4b219ea033911a155b5d5835",
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D1_RESULT_INTEGRITY_V1_RECEIPT.json":
        "1f42fecce799f09e2dfd73b2bc041f7f7bafd60522d95c004f27aa35b7846a4f",
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_INDEPENDENT_RECEIPT.json":
        "6f671aff17ea193ebf862af0739ee0bee22634f3f337944c14c90172acde34e0",
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_DESIGN_V1_RECEIPT.json":
        "d14feaa9a1fe402159806f29ef7499d9ca1e119902fbf1d12faad7b010b0e245",
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_RESULT_INTEGRITY_V1_RECEIPT.json":
        "c45db852c6d5571ec7930fc12d815b383a29e31939e711eb5f2e84c69807b448",
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_COMPLETION_V1.json":
        "b7034829527d7469459298735d253693b41f20bde6f0ab867bac71e804fa7d06",
    REPORT_ROOT / "TASK-039E3_R2R_UTILITY_INNER_D2_V1_V2_DISPOSITION_V1_RECEIPT.json":
        "4f670ed37aafaeaa7324b18fdae0272d6390bd9ad0e53b5a708207e06ed5e9cc",
}

PREFIX = "TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_V1_"
REPORT_FILENAMES = {
    "DATASET_AUTHORITY": PREFIX + "DATASET_AUTHORITY.json",
    "D0_AUTHORITY": PREFIX + "D0_AUTHORITY.json",
    "D1_AUTHORITY": PREFIX + "D1_AUTHORITY.json",
    "D2_AUTHORITY": PREFIX + "D2_AUTHORITY.json",
    "PREDICTION_ORDERING": PREFIX + "PREDICTION_ORDERING.json",
    "METRIC_POLICY": PREFIX + "METRIC_POLICY.json",
    "ONE_SHOT_POLICY": PREFIX + "ONE_SHOT_POLICY.json",
    "PREREGISTRATION": PREFIX + "PREREGISTRATION.json",
    "AUTHORIZATION": PREFIX + "AUTHORIZATION.json",
    "INDEPENDENT_AUDIT": PREFIX + "INDEPENDENT_AUDIT.json",
    "READINESS": PREFIX + "READINESS.json",
    "BUNDLE": PREFIX + "BUNDLE.json",
    "RECEIPT": PREFIX + "RECEIPT.json",
    "REPORT": PREFIX + "REPORT.md",
}


class OuterAuthorizationError(RuntimeError):
    """Path-free fail-closed authorization error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise OuterAuthorizationError(code)


def stable_hash(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def seal(value: Mapping[str, Any]) -> dict[str, Any]:
    if "artifact_hash" in value:
        fail("OUTER_AUTH_SELF_HASH_FIELD_COLLISION")
    if any(key.endswith("artifact_hash") for key in value):
        fail("OUTER_AUTH_REFERENCED_HASH_FIELD_COLLISION")
    result = dict(value)
    result["artifact_hash"] = stable_hash(result)
    return result


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("OUTER_AUTH_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def strict_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("OUTER_AUTH_JSON_REJECTED")
    if not isinstance(value, dict):
        fail("OUTER_AUTH_JSON_REJECTED")
    return value


def validate_self_hash(document: Mapping[str, Any], expected: str) -> None:
    core = {key: value for key, value in document.items() if key != "artifact_hash"}
    if document.get("artifact_hash") != expected or stable_hash(core) != expected:
        fail("OUTER_AUTH_ARTIFACT_HASH_REJECTED")


@dataclass(frozen=True)
class OuterDatasetAuthorityV1:
    dataset_name: str
    dataset_edition: str
    repository_snapshot_sha1: str
    dataset_manifest_sha256: str
    global_header_sha256: str
    test2_feature_manifest_path: str
    test2_feature_sha256: str
    test2_label_manifest_path: str
    test2_label_sha256: str
    row_count: int
    physical_row_start_inclusive: int
    physical_row_end_exclusive: int
    test2_feature_manifest_binding: bool
    test2_label_manifest_binding: bool
    preregistration_test2_feature_accesses: int
    preregistration_test2_label_accesses: int


@dataclass(frozen=True)
class OuterD0AuthorityV1:
    detector_id: str
    family: str
    role: str
    design_sha256: str
    implementation_identity: str
    model_sha256: str
    threshold_sha256: str
    feature_count: int
    retained_components: int
    residual_dimensions: int
    inference_only: bool
    refit_authorized: bool
    recalibration_authorized: bool
    d0_score_public_or_fusion_access_authorized: bool


@dataclass(frozen=True)
class OuterD1AuthorityV1:
    portfolio: str
    relation_count: int
    construction_authority_sha256: str
    descriptor_sha256: str
    reference_set_sha256: str
    reference_count: int
    private_registry_sha256: str
    evaluator_identity: str
    evaluator_semantic_classes: int
    evaluator_adversarial_cases: int
    evaluator_accepted_invalid: int
    prediction_timestamp_authority: str
    scientific_llm: bool
    rule_generation_authorized: bool
    rule_recalibration_authorized: bool
    rule_selection_authorized: bool


@dataclass(frozen=True)
class OuterD2V1AuthorityV1:
    d2_id: str
    fusion_family: str
    design_sha256: str
    source_map_sha256: str
    source_map_entry_count: int
    source_map_distinct_source_count: int
    required_distinct_source_count: int
    temporal_corroboration_policy: str
    temporal_tolerance_seconds: int
    native_horizon_memory: bool
    d0_preservation_policy: str
    d0_score_dependency: bool
    label_aware_fusion: bool
    trigger_classes: tuple[str, ...]
    d2_v2_execution_authorized: bool


@dataclass(frozen=True)
class OuterPredictionOrderingPolicyV1:
    execution_order: tuple[str, ...]
    feature_snapshot_type: str
    shared_d0_d1_feature_snapshot: bool
    feature_semantic_parse_count: int
    prediction_artifacts: tuple[str, ...]
    prediction_row_count: int
    all_predictions_frozen_and_reopened_before_label: bool
    label_open_step: int
    label_semantic_parse_count: int
    label_before_prediction_freeze_authorized: bool
    attack_metadata_before_prediction_freeze_authorized: bool


@dataclass(frozen=True)
class OuterMetricPolicyV1:
    attack_event_policy: str
    alarm_episode_policy: str
    primary_metrics: tuple[str, ...]
    secondary_metrics: tuple[str, ...]
    weighted_score_authorized: bool
    artificial_pass_threshold_defined: bool
    result_driven_redesign_authorized: bool


@dataclass(frozen=True)
class OuterOneShotExecutionPolicyV1:
    coordinated_outer_scientific_attempts: int
    coordinated_outer_scientific_retries: int
    future_d0_inference_executions: int
    future_d1_rule_evaluation_executions: int
    future_d2_v1_fusion_executions: int
    retry_after_feature_semantic_parse_authorized: bool
    second_outer_candidate_authorized: bool
    post_outer_redesign_authorized: bool


@dataclass(frozen=True)
class OuterThreeArmPreregistrationV1:
    preregistration_version: str
    scientific_question: str
    outer_role: str
    arms: tuple[str, ...]
    arm_count: int
    dataset: OuterDatasetAuthorityV1
    d0: OuterD0AuthorityV1
    d1: OuterD1AuthorityV1
    d2_v1: OuterD2V1AuthorityV1
    ordering: OuterPredictionOrderingPolicyV1
    metrics: OuterMetricPolicyV1
    one_shot: OuterOneShotExecutionPolicyV1
    inner_fusion_development_closed: bool
    d2_v2_developmental_negative_ablation_only: bool
    no_post_outer_development: bool


@dataclass(frozen=True)
class OuterThreeArmExecutionAuthorizationV1:
    authorization_version: str
    authorization_scope: str
    outer_preregistration_sha256: str
    outer_execution_authorized: bool
    outer_d0_execution_authorized: bool
    outer_d1_execution_authorized: bool
    outer_d2_v1_execution_authorized: bool
    outer_d2_v2_execution_authorized: bool
    test2_feature_access_authorized_for_execution: bool
    test2_label_access_authorized_only_after_prediction_freeze: bool
    d0_training_authorized: bool
    d0_recalibration_authorized: bool
    d1_rule_generation_authorized: bool
    d1_rule_recalibration_authorized: bool
    d1_rule_selection_authorized: bool
    d2_fusion_change_authorized: bool
    parameter_search_authorized: bool
    outer_retry_authorized: bool
    post_outer_redesign_authorized: bool


def _canonical_preregistration() -> OuterThreeArmPreregistrationV1:
    dataset = OuterDatasetAuthorityV1(
        "HAI", "23.05", HAI_REPOSITORY_SNAPSHOT, DATASET_MANIFEST_SHA256,
        GLOBAL_HEADER_SHA256, TEST2_FEATURE_MANIFEST_PATH, TEST2_FEATURE_SHA256,
        TEST2_LABEL_MANIFEST_PATH, TEST2_LABEL_SHA256, TEST2_ROW_COUNT, 0,
        TEST2_ROW_COUNT, True, True, 0, 0)
    d0 = OuterD0AuthorityV1(
        D0_ID, "PCA_RECONSTRUCTION_SPE", "REFERENCE_MULTIVARIATE_PROCESS_ANOMALY_DETECTOR",
        D0_DESIGN_SHA256, D0_IMPLEMENTATION_IDENTITY, D0_MODEL_SHA256,
        D0_THRESHOLD_SHA256, 37, 10, 27, True, False, False, False)
    d1 = OuterD1AuthorityV1(
        D1_PORTFOLIO, D1_RELATION_COUNT, D1_CONSTRUCTION_AUTHORITY_SHA256,
        D1_DESCRIPTOR_SHA256, D1_REFERENCE_SET_SHA256, D1_REFERENCE_COUNT,
        D1_REGISTRY_SHA256, D1_EVALUATOR_IDENTITY, 325, 552, 0,
        "decision_physical_row_index", False, False, False, False)
    d2 = OuterD2V1AuthorityV1(
        D2_V1_ID, D2_V1_FUSION_FAMILY, D2_V1_DESIGN_SHA256,
        D2_SOURCE_MAP_SHA256, D2_SOURCE_MAP_ENTRY_COUNT,
        D2_SOURCE_MAP_DISTINCT_SOURCES, D2_REQUIRED_DISTINCT_SOURCES,
        "EXACT_SAME_PHYSICAL_SECOND", 0, False,
        "EVERY_FROZEN_D0_ALARM_IS_A_D2_V1_ALARM", False, False,
        TRIGGER_CLASSES, False)
    ordering = OuterPredictionOrderingPolicyV1(
        EXECUTION_ORDER, "OuterTest2FeatureSnapshotV1", True, 1,
        ("OuterD0PredictionV1", "OuterD1PredictionV1", "OuterD2V1CombinedPredictionV1"),
        TEST2_ROW_COUNT, True, 18, 1, False, False)
    metrics = OuterMetricPolicyV1(
        ATTACK_EVENT_POLICY, ALARM_EPISODE_POLICY, PRIMARY_METRICS,
        SECONDARY_METRICS, False, False, False)
    one_shot = OuterOneShotExecutionPolicyV1(1, 0, 1, 1, 1, False, False, False)
    return OuterThreeArmPreregistrationV1(
        OUTER_PREREGISTRATION_VERSION, OUTER_SCIENTIFIC_QUESTION_V1,
        "ONE_SHOT_CONFIRMATORY_GENERALIZATION_EVALUATION", OUTER_ARMS, 3,
        dataset, d0, d1, d2, ordering, metrics, one_shot, True, True, True)


_PROCESS_PREREGISTRATION = _canonical_preregistration()
_PROCESS_AUTHORIZATION: OuterThreeArmExecutionAuthorizationV1 | None = None
_AUTHORIZATION_ISSUANCES = 0


def get_outer_preregistration() -> OuterThreeArmPreregistrationV1:
    """Return the single process-owned immutable preregistration."""
    return _PROCESS_PREREGISTRATION


def outer_preregistration_hash(value: OuterThreeArmPreregistrationV1) -> str:
    validate_preregistration(value)
    return stable_hash(asdict(value))


def validate_preregistration(value: OuterThreeArmPreregistrationV1) -> None:
    if not isinstance(value, OuterThreeArmPreregistrationV1):
        fail("OUTER_PREREGISTRATION_TYPE_REJECTED")
    if value != _canonical_preregistration():
        fail("OUTER_PREREGISTRATION_MUTATION_REJECTED")


def _authorization_for(preregistration: OuterThreeArmPreregistrationV1) -> OuterThreeArmExecutionAuthorizationV1:
    return OuterThreeArmExecutionAuthorizationV1(
        OUTER_AUTHORIZATION_VERSION, OUTER_AUTHORIZATION_SCOPE,
        outer_preregistration_hash(preregistration), True, True, True, True,
        False, True, True, False, False, False, False, False, False, False,
        False, False)


def issue_outer_execution_authorization(
    preregistration: OuterThreeArmPreregistrationV1,
) -> OuterThreeArmExecutionAuthorizationV1:
    """Issue the one process-local authorization; reconstructed input fails."""
    global _AUTHORIZATION_ISSUANCES, _PROCESS_AUTHORIZATION
    if preregistration is not _PROCESS_PREREGISTRATION:
        fail("OUTER_CALLER_RECONSTRUCTED_PREREGISTRATION_REJECTED")
    if _AUTHORIZATION_ISSUANCES != 0:
        fail("OUTER_SECOND_AUTHORIZATION_ISSUANCE_REJECTED")
    authorization = _authorization_for(preregistration)
    _AUTHORIZATION_ISSUANCES = 1
    _PROCESS_AUTHORIZATION = authorization
    return authorization


def outer_authorization_hash(value: OuterThreeArmExecutionAuthorizationV1) -> str:
    validate_authorization(value)
    return stable_hash(asdict(value))


def validate_authorization(value: OuterThreeArmExecutionAuthorizationV1) -> None:
    if not isinstance(value, OuterThreeArmExecutionAuthorizationV1):
        fail("OUTER_AUTHORIZATION_TYPE_REJECTED")
    if value != _authorization_for(_PROCESS_PREREGISTRATION):
        fail("OUTER_AUTHORIZATION_MUTATION_REJECTED")


def require_process_issued_authorization(value: OuterThreeArmExecutionAuthorizationV1) -> None:
    if value is not _PROCESS_AUTHORIZATION or _AUTHORIZATION_ISSUANCES != 1:
        fail("OUTER_CALLER_RECONSTRUCTED_AUTHORIZATION_REJECTED")


def validate_dataset_manifest_metadata(document: Mapping[str, Any]) -> None:
    validate_self_hash(document, DATASET_MANIFEST_SHA256)
    if document.get("dataset_name") != "HAI" or document.get("dataset_version_or_edition") != "23.05":
        fail("OUTER_DATASET_MANIFEST_REJECTED")
    source = str(document.get("source_reference", ""))
    if not source.endswith("@" + HAI_REPOSITORY_SNAPSHOT):
        fail("OUTER_DATASET_REPOSITORY_SNAPSHOT_REJECTED")
    files = document.get("files")
    if not isinstance(files, list):
        fail("OUTER_DATASET_MANIFEST_REJECTED")
    by_path = {item.get("relative_local_path"): item for item in files if isinstance(item, dict)}
    expected = {
        TEST2_FEATURE_MANIFEST_PATH: TEST2_FEATURE_SHA256,
        TEST2_LABEL_MANIFEST_PATH: TEST2_LABEL_SHA256,
    }
    for path, digest in expected.items():
        item = by_path.get(path)
        if item is None or item.get("sha256") != digest or item.get("row_count") != TEST2_ROW_COUNT:
            fail("OUTER_TEST2_MANIFEST_BINDING_REJECTED")


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True,
                            capture_output=True, check=False)
    if result.returncode:
        fail("OUTER_GIT_AUTHORITY_REPLAY_REJECTED")
    return result.stdout.strip()


def replay_public_authorities() -> None:
    dataset = strict_json(DATASET_MANIFEST_PATH.read_bytes())
    validate_dataset_manifest_metadata(dataset)
    for path, expected in PUBLIC_AUTHORITIES.items():
        document = strict_json(path.read_bytes())
        validate_self_hash(document, expected)
    state = strict_json((ROOT / "docs/project_state/CURRENT_STATE.json").read_bytes())
    validate_self_hash(state, str(state.get("artifact_hash")))
    flags = state.get("state_flags")
    if not isinstance(flags, dict):
        fail("OUTER_CURRENT_STATE_REJECTED")
    expected_flags = {
        "UTILITY_INNER_D2_V1_V2_SCIENTIFIC_DISPOSITION_FROZEN": True,
        "UTILITY_INNER_FUSION_DEVELOPMENT_CLOSED": True,
        "UTILITY_INNER_COMBINED_INCREMENTAL_UTILITY_SUPPORTED": False,
        "UTILITY_OUTER_FINAL_COMBINED_CANDIDATE": D2_V1_ID,
        "UTILITY_OUTER_EXECUTION_AUTHORIZED": False,
    }
    for key, expected in expected_flags.items():
        if flags.get(key) != expected:
            fail("OUTER_REQUIRED_CURRENT_STATE_REJECTED")


def _write_json(path: Path, document: Mapping[str, Any]) -> None:
    path.write_bytes((json.dumps(document, indent=2, sort_keys=True,
        ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8"))


def _report_body(prereg_sha: str, auth_sha: str) -> bytes:
    lines = [
        "# Sealed OUTER D0/D1/D2 V1 preregistration and authorization",
        "",
        f"Task: `{TASK_ID}`",
        f"Status: `{STATUS}`",
        "",
        "Exactly one coordinated confirmatory HAI-23.05 test2 evaluation is authorized for the frozen D0 detector-only, D1 COMMON-42 Rule-only, and D2 V1 combined arms.",
        "",
        f"OUTER preregistration SHA-256: `{prereg_sha}`",
        f"OUTER authorization SHA-256: `{auth_sha}`",
        "",
        "The authorization freezes one shared test2 feature snapshot, D0/D1/D2 V1 prediction freeze before any label access, the established event and episode policies, two primary metrics, seven descriptive secondary metrics, zero retry, and no post-OUTER redesign.",
        "",
        "D2 V2 is excluded. No test2 feature or label file was opened, hashed, or parsed; no scientific arm was executed; no metric was computed in this task.",
        "",
        f"Exact next task: `{NEXT_TASK}`",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_reports(created_at: str,
                  preregistration: OuterThreeArmPreregistrationV1,
                  authorization: OuterThreeArmExecutionAuthorizationV1) -> tuple[dict[str, dict[str, Any]], bytes]:
    prereg_sha = outer_preregistration_hash(preregistration)
    auth_sha = outer_authorization_hash(authorization)
    common = {"schema_version": "1.0.0", "task_id": TASK_ID,
              "created_at_utc": created_at, "status": "PASS"}
    reports: dict[str, dict[str, Any]] = {}
    payloads = {
        "DATASET_AUTHORITY": {**common, "artifact_type": "OuterDatasetAuthorityReportV1",
            "dataset_authority": asdict(preregistration.dataset)},
        "D0_AUTHORITY": {**common, "artifact_type": "OuterD0AuthorityReportV1",
            "d0_authority": asdict(preregistration.d0)},
        "D1_AUTHORITY": {**common, "artifact_type": "OuterD1AuthorityReportV1",
            "d1_authority": asdict(preregistration.d1)},
        "D2_AUTHORITY": {**common, "artifact_type": "OuterD2V1AuthorityReportV1",
            "d2_v1_authority": asdict(preregistration.d2_v1)},
        "PREDICTION_ORDERING": {**common, "artifact_type": "OuterPredictionOrderingReportV1",
            "ordering_policy": asdict(preregistration.ordering)},
        "METRIC_POLICY": {**common, "artifact_type": "OuterMetricPolicyReportV1",
            "metric_policy": asdict(preregistration.metrics)},
        "ONE_SHOT_POLICY": {**common, "artifact_type": "OuterOneShotPolicyReportV1",
            "one_shot_policy": asdict(preregistration.one_shot)},
        "PREREGISTRATION": {**common, "artifact_type": "OuterThreeArmPreregistrationArtifactV1",
            "outer_preregistration_sha256": prereg_sha,
            "preregistration": asdict(preregistration)},
        "AUTHORIZATION": {**common, "artifact_type": "OuterThreeArmExecutionAuthorizationArtifactV1",
            "outer_authorization_sha256": auth_sha,
            "authorization": asdict(authorization), "authorization_issuances": 1},
        "INDEPENDENT_AUDIT": {**common, "artifact_type": "OuterAuthorizationIndependentAuditV1",
            "static_tests": STATIC_TESTS, "independent_attacks": INDEPENDENT_ATTACKS,
            "independent_attacks_rejected": INDEPENDENT_ATTACKS, "accepted_invalid": 0,
            "scientific_executions": 0, "test2_feature_accesses": 0,
            "test2_label_accesses": 0, "outer_executions": 0},
        "READINESS": {**common, "artifact_type": "OuterAuthorizationReadinessV1",
            "outer_preregistration_frozen": True,
            "outer_execution_authorization_issued": True,
            "outer_execution_authorized": True, "outer_executed": False,
            "test2_feature_accesses": 0, "test2_label_accesses": 0,
            "scientific_executions": 0, "accepted_invalid": 0,
            "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
            "push_attempted": False, "blockers": [], "exact_next_task": NEXT_TASK},
    }
    for name, payload in payloads.items():
        reports[name] = seal(payload)
    body = _report_body(prereg_sha, auth_sha)
    body_sha = sha256(body).hexdigest()
    component_sha256s = {name.lower() + "_sha256": doc["artifact_hash"]
                         for name, doc in reports.items()}
    reports["BUNDLE"] = seal({**common, "artifact_type": "OuterAuthorizationBundleV1",
        **component_sha256s, "report_body_sha256": body_sha,
        "outer_preregistration_sha256": prereg_sha,
        "outer_authorization_sha256": auth_sha})
    reports["RECEIPT"] = seal({**common, "artifact_type": "OuterAuthorizationReceiptV1",
        "bundle_sha256": reports["BUNDLE"]["artifact_hash"],
        "report_body_sha256": body_sha,
        "outer_preregistration_sha256": prereg_sha,
        "outer_authorization_sha256": auth_sha,
        "authorization_version": OUTER_AUTHORIZATION_VERSION,
        "authorization_scope": OUTER_AUTHORIZATION_SCOPE,
        "outer_execution_authorized": True, "outer_executed": False,
        "test2_feature_accesses": 0, "test2_label_accesses": 0,
        "exact_next_task": NEXT_TASK})
    footer = (
        "<!-- BEGIN OUTER D0 D1 D2V1 AUTHORIZATION REPORT PROVENANCE V1 -->\n"
        f"Report-Hash-Scheme: {SCHEME}\n"
        f"Report-Self-Hash: {body_sha}\n"
        f"Bundle-Hash: {reports['BUNDLE']['artifact_hash']}\n"
        f"Receipt-Hash: {reports['RECEIPT']['artifact_hash']}\n"
        "<!-- END OUTER D0 D1 D2V1 AUTHORIZATION REPORT PROVENANCE V1 -->\n"
    ).encode("utf-8")
    return reports, body + b"\n" + footer


def validate_markdown(raw: bytes, bundle_sha: str, receipt_sha: str) -> str:
    marker = b"<!-- BEGIN OUTER D0 D1 D2V1 AUTHORIZATION REPORT PROVENANCE V1 -->"
    end = b"<!-- END OUTER D0 D1 D2V1 AUTHORIZATION REPORT PROVENANCE V1 -->"
    if raw.count(marker) != 1 or raw.count(end) != 1 or b"\r" in raw:
        fail("OUTER_AUTH_MARKDOWN_PROVENANCE_REJECTED")
    marker_start = raw.index(marker)
    prefix = raw[:marker_start]
    if not prefix.endswith(b"\n"):
        fail("OUTER_AUTH_MARKDOWN_SEPARATOR_REJECTED")
    body = prefix[:-1]
    body_sha = sha256(body).hexdigest()
    footer = raw[marker_start:].decode("utf-8")
    required = (f"Report-Hash-Scheme: {SCHEME}", f"Report-Self-Hash: {body_sha}",
                f"Bundle-Hash: {bundle_sha}", f"Receipt-Hash: {receipt_sha}")
    if not all(value in footer for value in required):
        fail("OUTER_AUTH_MARKDOWN_BINDING_REJECTED")
    return body_sha


def validate_report_set(reports: Mapping[str, Mapping[str, Any]], markdown: bytes) -> None:
    for name, document in reports.items():
        if tuple(document).count("artifact_hash") != 1:
            fail("OUTER_AUTH_SELF_HASH_FIELD_COLLISION")
        if any(key != "artifact_hash" and key.endswith("artifact_hash") for key in document):
            fail("OUTER_AUTH_REFERENCED_HASH_FIELD_COLLISION")
        validate_self_hash(document, str(document["artifact_hash"]))
        strict_json((json.dumps(document, ensure_ascii=True, allow_nan=False) + "\n").encode())
    body_sha = validate_markdown(markdown, str(reports["BUNDLE"]["artifact_hash"]),
                                 str(reports["RECEIPT"]["artifact_hash"]))
    if body_sha != reports["BUNDLE"].get("report_body_sha256"):
        fail("OUTER_AUTH_REPORT_BODY_HASH_REJECTED")


def freeze_reports() -> dict[str, str]:
    if _git("branch", "--show-current") != BRANCH:
        fail("OUTER_BRANCH_REJECTED")
    if _git("status", "--porcelain"):
        fail("OUTER_PRE_REPORT_WORKTREE_NOT_CLEAN")
    if not _git("merge-base", "--is-ancestor", BASE, "HEAD") == "":
        fail("OUTER_BASE_ANCESTRY_REJECTED")
    changed = set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())
    expected = {
        "TASKS/TASK-039E3-R2R-UTILITY-OUTER-D0-D1-D2V1-PREREGISTRATION-AND-AUTHORIZATION-V1.md",
        "src/paperworks/v6/task039e3_r2r_outer_d0_d1_d2v1_preregistration_authorization_v1.py",
        "tests/test_task039e3_r2r_outer_d0_d1_d2v1_preregistration_authorization_v1.py",
        "tests/test_task039e3_r2r_outer_d0_d1_d2v1_preregistration_authorization_v1_independent.py",
    }
    if changed != expected:
        fail("OUTER_COMMIT_A_CONTENT_REJECTED")
    replay_public_authorities()
    preregistration = get_outer_preregistration()
    authorization = issue_outer_execution_authorization(preregistration)
    require_process_issued_authorization(authorization)
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    reports, markdown = build_reports(created_at, preregistration, authorization)
    validate_report_set(reports, markdown)
    for name, document in reports.items():
        _write_json(REPORT_ROOT / REPORT_FILENAMES[name], document)
    (REPORT_ROOT / REPORT_FILENAMES["REPORT"]).write_bytes(markdown)
    reopened = {name: strict_json((REPORT_ROOT / REPORT_FILENAMES[name]).read_bytes())
                for name in reports}
    validate_report_set(reopened, (REPORT_ROOT / REPORT_FILENAMES["REPORT"]).read_bytes())
    return {name.lower() + "_hash": str(doc["artifact_hash"]) for name, doc in reports.items()} | {
        "outer_preregistration_hash": outer_preregistration_hash(preregistration),
        "outer_authorization_hash": outer_authorization_hash(authorization),
        "report_self_hash": str(reports["BUNDLE"]["report_body_sha256"]),
    }


def _main(argv: Sequence[str]) -> int:
    if tuple(argv) != ("--freeze-reports",):
        fail("OUTER_UNAUTHORIZED_ENTRY_POINT")
    result = freeze_reports()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main(sys.argv[1:]))
    except OuterAuthorizationError as exc:
        print(exc.code, file=sys.stderr)
        raise SystemExit(1)
