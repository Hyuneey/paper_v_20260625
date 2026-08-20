"""Frozen, public-only D0 PCA-SPE detector design authority.

This module performs no data I/O, model fitting, calibration, prediction, or
metric computation.  It preregisters one deterministic normal-only reference
detector and issues its design through process-local factory custody.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from typing import Any, Mapping
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
    ALARM_EPISODE_POLICY,
    ATTACK_EVENT_RECALL_FORMULA,
    NORMAL_FAR_FORMULA,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    CORRECTED_EVENT_POLICY_HASH,
    CORRECTED_METRIC_POLICY_HASH,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-BASELINE-DESIGN-AND-FREEZE-V1"
SCHEMA_VERSION = "1.0.0"
DESIGN_ARTIFACT_TYPE = "task039e3_r2r_d0_detector_design_v1"
CONFIG_ARTIFACT_TYPE = "task039e3_r2r_d0_pca_spe_detector_config_v1"

DETECTOR_ID = "D0_PCA_SPE_V1"
DETECTOR_FAMILY = "PCA_RECONSTRUCTION_SPE"
DETECTOR_ROLE = "REFERENCE_MULTIVARIATE_PROCESS_ANOMALY_DETECTOR"
TRAINING_MODE = "NORMAL_ONLY"
CALIBRATION_MODE = "NORMAL_ONLY"
NUMERIC_BACKEND_FAMILY = "NUMPY_LINEAR_ALGEBRA"
ANOMALY_SCORE = "SQUARED_PREDICTION_ERROR"

DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
PROCESS_FREEZE_HASH = "f263d23ceda5ab5ff3c7459e56669ab1dadd7d30cd2243ad8971301990a86325"
CANONICAL_RULE_VIEW_ID = "d7bcc2b06aedd627db78a0dc104dd6fec5a171f0a2be773180e48ca3e8e52f57"
CANDIDATE_LEARNING_VIEW_ID = "eaa77f331bf79cc6887ccddcfff8818880c1a93c16ebc6fdd2d06a1c8db37eca"
NORMAL_CANDIDATE_FIT_SPLIT_ID = "cf02e3474a0ade49aec518a886fef0fb0c405b311d827f593fdc207cfad9ab7a"
NORMAL_RELATION_CALIBRATION_SPLIT_ID = "c9e31a99364c0db11f4ad958a93de90ac065661c5171bf8601e2861a5706bba5"
NORMAL_GUARD_SPLIT_ID = "0a09b9171925a24d1955023c41a2b1d9b54682b68ad4c5715943908ff80f0923"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
OFFICIAL_HAI_SNAPSHOT_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
HAI_HEADER_SHA256 = "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a"

FROZEN_D1_RULE_PREDICTION_HASH = (
    "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
)

P1_FEATURE_ORDER = (
    "P1_FCV01D",
    "P1_FCV01Z",
    "P1_FCV02D",
    "P1_FCV02Z",
    "P1_FCV03D",
    "P1_FCV03Z",
    "P1_FT01",
    "P1_FT01Z",
    "P1_FT02",
    "P1_FT02Z",
    "P1_FT03",
    "P1_FT03Z",
    "P1_LCV01D",
    "P1_LCV01Z",
    "P1_LIT01",
    "P1_PCV01D",
    "P1_PCV01Z",
    "P1_PCV02D",
    "P1_PCV02Z",
    "P1_PIT01",
    "P1_PIT01_HH",
    "P1_PIT02",
    "P1_PP01AD",
    "P1_PP01AR",
    "P1_PP01BD",
    "P1_PP01BR",
    "P1_PP02D",
    "P1_PP02R",
    "P1_PP04",
    "P1_PP04D",
    "P1_PP04SP",
    "P1_SOL01D",
    "P1_SOL03D",
    "P1_STSP",
    "P1_TIT01",
    "P1_TIT02",
    "P1_TIT03",
)
P1_FEATURE_COUNT = 37
P1_FEATURE_ORDER_HASH = "a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57"
P1_FEATURE_SET_HASH = stable_hash_v1(
    {
        "artifact_type": "d0_p1_feature_set_v1",
        "features": sorted(P1_FEATURE_ORDER),
    }
)

STANDARDIZATION_SCALE_FLOOR = 1e-12
PCA_EXPLAINED_VARIANCE_TARGET = 0.95
NORMAL_CALIBRATION_ALPHA = 0.001
THRESHOLD_QUANTILE = 0.999


class D0DetectorDesignError(ValueError):
    """Fixed-category D0 design custody or semantic rejection."""


@dataclass(frozen=True)
class D0FeatureSchemaAuthorityV1:
    dataset_manifest_id: str
    process_freeze_hash: str
    canonical_rule_view_id: str
    candidate_learning_view_id: str
    official_snapshot_commit: str
    global_header_sha256: str
    process_id: str
    ordered_features: tuple[str, ...]
    feature_count: int
    feature_set_hash: str
    feature_order_hash: str
    canonical_source_column_order: bool
    timestamp_excluded: bool
    labels_excluded: bool
    attack_metadata_excluded: bool
    non_p1_variables_excluded: bool
    feature_values_read_for_design: bool


@dataclass(frozen=True)
class D0DataSplitPolicyV1:
    model_fit_splits: tuple[str, str]
    model_fit_split_identity: str
    threshold_calibration_split: str
    threshold_calibration_split_identity: str
    normal_sanity_split: str
    normal_sanity_split_identity: str
    inner_evaluation_split: str
    inner_metric_split: str
    inner_split_identity: str
    outer_feature_split: str
    outer_label_split: str
    outer_sealed: bool
    train1_train2_concatenated_without_shuffle: bool
    train4_tuning_allowed: bool
    test1_selection_allowed: bool
    test1_label_selection_allowed: bool


@dataclass(frozen=True)
class D0PreprocessingPolicyV1:
    location_estimator: str
    scale_estimator: str
    ddof: int
    scale_floor: float
    scale_expression: str
    fit_scope: str
    robust_scaler_allowed: bool
    minmax_scaler_allowed: bool
    caller_scaler_allowed: bool


@dataclass(frozen=True)
class D0PcaPolicyV1:
    backend_family: str
    deterministic_cpu_linear_algebra: bool
    randomized_algorithm_allowed: bool
    explained_variance_target: float
    component_selection: str
    retained_component_lower_bound: int
    residual_dimension_mandatory: bool
    full_dimension_fallback: str
    loading_sign_anchor: str
    loading_sign_tie_break: str
    loading_sign_orientation: str
    exact_eigenvalue_tie_at_cutoff: str
    anomaly_score: str
    score_smoothing: bool
    temporal_dilation: bool
    point_adjustment: bool


@dataclass(frozen=True)
class D0ThresholdPolicyV1:
    calibration_scope: str
    alpha: float
    upper_quantile: float
    order_statistic_index: str
    interpolation: str
    distributional_approximation: bool
    alarm_comparison_operator: str
    equality_is_alarm: bool
    label_tuning_allowed: bool
    d1_result_tuning_allowed: bool
    test_tuning_allowed: bool


@dataclass(frozen=True)
class D0MetricCompatibilityV1:
    corrected_event_policy_hash: str
    corrected_metric_policy_hash: str
    alarm_episode_policy: str
    attack_event_recall_formula: str
    normal_far_formula: str
    primary_metrics: tuple[str, str]
    metric_selection_allowed: bool


@dataclass(frozen=True)
class D0FutureArtifactContractV1:
    detector_prediction_artifact_type: str
    model_artifact_type: str
    threshold_artifact_type: str
    prediction_label_blind: bool
    raw_scores_publicly_required: bool
    private_model_parameters_allowed_with_public_hash: bool
    private_threshold_allowed_with_public_hash: bool
    detector_error_context_split_role: str
    detector_error_context_purpose: str
    detector_error_context_primary_direction: str
    detector_error_context_supplementary_only: bool
    detector_error_context_validity_authority: bool
    detector_error_context_runtime_authority: bool
    d2_must_consume_frozen_d0_prediction: bool
    d2_must_consume_frozen_d1_prediction: bool
    d2_policy_frozen_in_this_task: bool


@dataclass(frozen=True)
class D0IndependenceDeclarationV1:
    d1_performance_used_for_design: bool
    d1_metric_artifact_read_for_design: bool
    d1_prediction_content_read_for_design: bool
    d1_rule_prediction_hash_bound_for_future_d2: bool
    frozen_d1_rule_prediction_hash: str
    gdn_primary_detector: bool
    detector_selected_for_expected_d1_outperformance: bool


@dataclass(frozen=True)
class D0DetectorDesignV1:
    artifact_type: str
    schema_version: str
    task_id: str
    detector_id: str
    detector_family: str
    detector_role: str
    training_mode: str
    calibration_mode: str
    scientific_llm: bool
    randomized_training: bool
    random_seed_required: bool
    feature_schema: D0FeatureSchemaAuthorityV1
    split_policy: D0DataSplitPolicyV1
    preprocessing_policy: D0PreprocessingPolicyV1
    pca_policy: D0PcaPolicyV1
    threshold_policy: D0ThresholdPolicyV1
    metric_compatibility: D0MetricCompatibilityV1
    future_artifact_contract: D0FutureArtifactContractV1
    independence: D0IndependenceDeclarationV1
    train1_value_reads: int
    train2_value_reads: int
    train3_value_reads: int
    train4_value_reads: int
    test1_value_reads: int
    label_reads: int
    test2_reads: int
    detector_training_executions: int
    detector_inner_executions: int
    d0_authorized: bool
    d2_authorized: bool
    outer_authorized: bool
    design_hash: str

    def to_public_dict(self) -> dict[str, Any]:
        # Normalize tuples to JSON arrays so the committed document has one
        # representation in memory, on disk, and in its canonical hash.
        return json.loads(json.dumps(asdict(self), ensure_ascii=True))


def _design_payload(value: D0DetectorDesignV1) -> dict[str, Any]:
    payload = value.to_public_dict()
    payload.pop("design_hash")
    return payload


def _build_expected_d0_detector_design_v1() -> D0DetectorDesignV1:
    feature_schema = D0FeatureSchemaAuthorityV1(
        DATASET_MANIFEST_ID,
        PROCESS_FREEZE_HASH,
        CANONICAL_RULE_VIEW_ID,
        CANDIDATE_LEARNING_VIEW_ID,
        OFFICIAL_HAI_SNAPSHOT_COMMIT,
        HAI_HEADER_SHA256,
        "P1",
        P1_FEATURE_ORDER,
        P1_FEATURE_COUNT,
        P1_FEATURE_SET_HASH,
        P1_FEATURE_ORDER_HASH,
        True,
        True,
        True,
        True,
        True,
        False,
    )
    split_policy = D0DataSplitPolicyV1(
        ("NORMAL_TRAIN1_MODEL_FIT", "NORMAL_TRAIN2_MODEL_FIT"),
        NORMAL_CANDIDATE_FIT_SPLIT_ID,
        "NORMAL_TRAIN3_THRESHOLD_CALIBRATION",
        NORMAL_RELATION_CALIBRATION_SPLIT_ID,
        "NORMAL_TRAIN4_SANITY_EVALUATION_ONLY",
        NORMAL_GUARD_SPLIT_ID,
        "TEST1_INNER_UTILITY_EVALUATION_ONLY",
        "LABEL_TEST1_INNER_METRIC_EVALUATION_ONLY",
        INNER_SPLIT_ID,
        "TEST2_SEALED_OUTER",
        "LABEL_TEST2_SEALED_OUTER",
        True,
        True,
        False,
        False,
        False,
    )
    preprocessing = D0PreprocessingPolicyV1(
        "POPULATION_MEAN_TRAIN1_TRAIN2",
        "POPULATION_STANDARD_DEVIATION_TRAIN1_TRAIN2",
        0,
        STANDARDIZATION_SCALE_FLOOR,
        "max(population_standard_deviation,1e-12)",
        "EXACT_TRAIN1_PLUS_TRAIN2",
        False,
        False,
        False,
    )
    pca = D0PcaPolicyV1(
        NUMERIC_BACKEND_FAMILY,
        True,
        False,
        PCA_EXPLAINED_VARIANCE_TARGET,
        "SMALLEST_K_WITH_CUMULATIVE_EXPLAINED_VARIANCE_AT_LEAST_0_95",
        1,
        True,
        "IF_SMALLEST_K_EQUALS_D_USE_D_MINUS_1",
        "LARGEST_ABSOLUTE_LOADING_ELEMENT",
        "SMALLEST_FEATURE_INDEX_ON_EXACT_TIE",
        "ANCHOR_LOADING_NONNEGATIVE",
        "FAIL_CLOSED_IF_CUTOFF_SPLITS_EXACT_TIED_EIGENVALUE_BLOCK",
        ANOMALY_SCORE,
        False,
        False,
        False,
    )
    threshold = D0ThresholdPolicyV1(
        "NORMAL_TRAIN3_ONLY",
        NORMAL_CALIBRATION_ALPHA,
        THRESHOLD_QUANTILE,
        "ceil(0.999*n)-1_zero_based_after_ascending_sort",
        "NONE",
        False,
        "score > threshold",
        False,
        False,
        False,
        False,
    )
    metrics = D0MetricCompatibilityV1(
        CORRECTED_EVENT_POLICY_HASH,
        CORRECTED_METRIC_POLICY_HASH,
        ALARM_EPISODE_POLICY,
        ATTACK_EVENT_RECALL_FORMULA,
        NORMAL_FAR_FORMULA,
        ("ATTACK_EVENT_RECALL", "NORMAL_FAR_EPISODES_PER_HOUR"),
        False,
    )
    future = D0FutureArtifactContractV1(
        "DetectorPredictionArtifactV1",
        "D0PcaSpeModelArtifactV1",
        "D0PcaSpeThresholdArtifactV1",
        True,
        False,
        True,
        True,
        "INNER_UTILITY",
        "INNER_UTILITY_ASSESSMENT",
        "FALSE_NEGATIVE",
        True,
        False,
        False,
        True,
        True,
        False,
    )
    independence = D0IndependenceDeclarationV1(
        False,
        False,
        False,
        True,
        FROZEN_D1_RULE_PREDICTION_HASH,
        False,
        False,
    )
    provisional = D0DetectorDesignV1(
        DESIGN_ARTIFACT_TYPE,
        SCHEMA_VERSION,
        TASK_ID,
        DETECTOR_ID,
        DETECTOR_FAMILY,
        DETECTOR_ROLE,
        TRAINING_MODE,
        CALIBRATION_MODE,
        False,
        False,
        False,
        feature_schema,
        split_policy,
        preprocessing,
        pca,
        threshold,
        metrics,
        future,
        independence,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        False,
        False,
        False,
        "",
    )
    return replace(provisional, design_hash=stable_hash_v1(_design_payload(provisional)))


if len(P1_FEATURE_ORDER) != P1_FEATURE_COUNT or len(set(P1_FEATURE_ORDER)) != P1_FEATURE_COUNT:
    raise RuntimeError("D0_FEATURE_SCHEMA_CARDINALITY_REJECTED")
if any(not name.startswith("P1_") for name in P1_FEATURE_ORDER):
    raise RuntimeError("D0_FEATURE_SCHEMA_PROCESS_SCOPE_REJECTED")
if stable_hash_v1({"features": list(P1_FEATURE_ORDER)}) != P1_FEATURE_ORDER_HASH:
    raise RuntimeError("D0_FEATURE_SCHEMA_ORDER_AUTHORITY_REJECTED")


D0_DETECTOR_DESIGN_HASH = _build_expected_d0_detector_design_v1().design_hash

_ISSUED_DESIGNS: dict[int, tuple[weakref.ReferenceType[D0DetectorDesignV1], str]] = {}


def _issue_design(value: D0DetectorDesignV1) -> D0DetectorDesignV1:
    object_id = id(value)

    def cleanup(dead_ref: weakref.ReferenceType[D0DetectorDesignV1]) -> None:
        issued = _ISSUED_DESIGNS.get(object_id)
        if issued is not None and issued[0] is dead_ref:
            _ISSUED_DESIGNS.pop(object_id, None)

    reference = weakref.ref(value, cleanup)
    _ISSUED_DESIGNS[object_id] = (reference, value.design_hash)
    return value


def build_d0_detector_design_v1() -> D0DetectorDesignV1:
    """Issue the sole canonical design.  No caller scientific knobs exist."""

    return _issue_design(_build_expected_d0_detector_design_v1())


def validate_d0_detector_design_v1(value: D0DetectorDesignV1) -> str:
    if type(value) is not D0DetectorDesignV1:
        raise D0DetectorDesignError("D0_DESIGN_TYPE_REJECTED")
    issued = _ISSUED_DESIGNS.get(id(value))
    if issued is None or issued[0]() is not value or issued[1] != value.design_hash:
        raise D0DetectorDesignError("D0_DESIGN_FACTORY_CUSTODY_REJECTED")
    expected = _build_expected_d0_detector_design_v1()
    if value != expected or value.to_public_dict() != expected.to_public_dict():
        raise D0DetectorDesignError("D0_DESIGN_REPLAY_REJECTED")
    if stable_hash_v1(_design_payload(value)) != value.design_hash:
        raise D0DetectorDesignError("D0_DESIGN_SELF_HASH_REJECTED")
    return value.design_hash


def validate_d0_design_document_v1(document: Mapping[str, Any]) -> str:
    if type(document) is not dict:
        raise D0DetectorDesignError("D0_DESIGN_DOCUMENT_TYPE_REJECTED")
    expected = _build_expected_d0_detector_design_v1().to_public_dict()
    if document != expected:
        raise D0DetectorDesignError("D0_DESIGN_DOCUMENT_REPLAY_REJECTED")
    payload = dict(document)
    observed = payload.pop("design_hash", None)
    if observed != stable_hash_v1(payload) or observed != D0_DETECTOR_DESIGN_HASH:
        raise D0DetectorDesignError("D0_DESIGN_DOCUMENT_SELF_HASH_REJECTED")
    return str(observed)


def canonical_config_document_v1() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_type": CONFIG_ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "design": _build_expected_d0_detector_design_v1().to_public_dict(),
        "d1_performance_used_for_design": False,
        "d1_metric_artifact_read_for_design": False,
        "d1_prediction_content_read_for_design": False,
        "d1_rule_prediction_hash_bound_for_future_d2": True,
        "train1_value_reads": 0,
        "train2_value_reads": 0,
        "train3_value_reads": 0,
        "train4_value_reads": 0,
        "test1_value_reads": 0,
        "label_reads": 0,
        "test2_reads": 0,
        "detector_training_executions": 0,
        "detector_inner_executions": 0,
    }
    return {**payload, "config_hash": stable_hash_v1(payload)}


def validate_d0_config_v1(document: Mapping[str, Any]) -> str:
    if type(document) is not dict or document != canonical_config_document_v1():
        raise D0DetectorDesignError("D0_CONFIG_REPLAY_REJECTED")
    payload = dict(document)
    observed = payload.pop("config_hash", None)
    if observed != stable_hash_v1(payload):
        raise D0DetectorDesignError("D0_CONFIG_SELF_HASH_REJECTED")
    return str(observed)


__all__ = [
    "ANOMALY_SCORE",
    "D0_DETECTOR_DESIGN_HASH",
    "DETECTOR_FAMILY",
    "DETECTOR_ID",
    "D0DataSplitPolicyV1",
    "D0DetectorDesignError",
    "D0DetectorDesignV1",
    "D0FeatureSchemaAuthorityV1",
    "D0FutureArtifactContractV1",
    "D0IndependenceDeclarationV1",
    "D0MetricCompatibilityV1",
    "D0PcaPolicyV1",
    "D0PreprocessingPolicyV1",
    "D0ThresholdPolicyV1",
    "NORMAL_CALIBRATION_ALPHA",
    "P1_FEATURE_COUNT",
    "P1_FEATURE_ORDER",
    "P1_FEATURE_ORDER_HASH",
    "P1_FEATURE_SET_HASH",
    "PCA_EXPLAINED_VARIANCE_TARGET",
    "STANDARDIZATION_SCALE_FLOOR",
    "build_d0_detector_design_v1",
    "canonical_config_document_v1",
    "validate_d0_config_v1",
    "validate_d0_design_document_v1",
    "validate_d0_detector_design_v1",
]
