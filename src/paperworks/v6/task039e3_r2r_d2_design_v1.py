"""Frozen public-only D2 detector/rule fusion preregistration.

This module contains no prediction, metric, label, or dataset I/O.  It binds
immutable input identities, the canonical COMMON-42 source-resolution path,
and one deterministic pointwise fusion policy.  The executable helpers below
operate on synthetic in-memory fixtures only; D2 scientific execution remains
unauthorized.
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
from paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 import (
    CANONICAL_AUTHORITY_DEFINITION_HASH,
    COMMON42_AUTHORITY_CHECK_HASH,
    NormalOnlyAuthorityDefinitionV1,
    validate_canonical_common42_authority_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    CANONICAL_V4_AUTHORITY_HASH,
    CORRECTED_EVENT_POLICY_HASH,
    CORRECTED_METRIC_POLICY_HASH,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-AND-FREEZE-V1"
SCHEMA_VERSION = "1.0.0"
DESIGN_ARTIFACT_TYPE = "task039e3_r2r_d2_design_authority_v1"
CONFIG_ARTIFACT_TYPE = "task039e3_r2r_d2_detector_rule_corroboration_config_v1"

D2_ID = "D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_V1"
D2_ROLE = "PRIMARY_COMBINED_DETECTOR_RULE_ARM"
D2_FUSION_FAMILY = "DETECTOR_PRESERVING_MULTI_SOURCE_RULE_CORROBORATION"
CORRECTION_DIRECTION = "DETECTOR_FALSE_NEGATIVE_RECOVERY"

FROZEN_D0_DETECTOR_PREDICTION_HASH = (
    "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
)
FROZEN_D1_RULE_PREDICTION_HASH = (
    "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
)

COMMON_PORTFOLIO = "COMMON-42"
COMMON_RELATION_COUNT = 42
COMMON42_SOURCE_MAPPING_HASH = (
    "f8c47a212dbf65946f843f7fb0c737ae394a28c08af9ff18f5ac20a58d8891b7"
)
SOURCE_RESOLUTION_POLICY = (
    "D1_RELATION_BINDING_HASH_TO_CANONICAL_V4_RULE_DESCRIPTOR_SOURCE_V1"
)
REQUIRED_DISTINCT_SOURCE_COUNT = 2
SAME_SECOND_POLICY = "EXACT_DECISION_PHYSICAL_ROW_INDEX_EQUALITY"
CORROBORATION_COUNT_RATIONALE = (
    "MINIMUM_NON_SINGLETON_DISTINCT_SOURCE_CORROBORATION"
)

TRIGGER_CLASSES = (
    "NONE",
    "D0_ONLY",
    "RULE_RECOVERY",
    "D0_AND_RULE_CORROBORATION",
)

D0_MISSED_ATTACK_RECOVERY_FORMULA = (
    "D0_MISSED_ATTACK_EVENTS_RECOVERED_BY_RULE_RECOVERY_DIVIDED_BY_ALL_D0_MISSED_ATTACK_EVENTS"
)
D0_MISSED_ATTACK_RECOVERY_UNDEFINED_REASON = "NO_D0_MISSED_ATTACK_EVENTS"
INCREMENTAL_ATTACK_RECALL_FORMULA = (
    "D2_ATTACK_EVENT_RECALL_MINUS_D0_ATTACK_EVENT_RECALL"
)
ADDED_NORMAL_RECOVERY_FAR_FORMULA = (
    "RULE_RECOVERY_ALARM_EPISODES_WITH_ZERO_ATTACK_EVENT_OVERLAP_DIVIDED_BY_NORMAL_LABELED_SECONDS_OVER_3600"
)
INCREMENTAL_NORMAL_FAR_FORMULA = (
    "D2_NORMAL_FAR_EPISODES_PER_HOUR_MINUS_D0_NORMAL_FAR_EPISODES_PER_HOUR"
)


class D2DesignError(ValueError):
    """Fixed-category D2 design custody or semantic rejection."""


def _strict_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise D2DesignError(f"D2_{name.upper()}_BOOLEAN_REJECTED")
    return value


def _strict_index(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise D2DesignError(f"D2_{name.upper()}_INDEX_REJECTED")
    return value


def _strict_nonempty_string(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise D2DesignError(f"D2_{name.upper()}_STRING_REJECTED")
    return value


def _sha(value: object, name: str) -> str:
    text = _strict_nonempty_string(value, name)
    if len(text) != 64:
        raise D2DesignError(f"D2_{name.upper()}_HASH_REJECTED")
    try:
        int(text, 16)
    except ValueError as exc:
        raise D2DesignError(f"D2_{name.upper()}_HASH_REJECTED") from exc
    if text != text.lower():
        raise D2DesignError(f"D2_{name.upper()}_HASH_REJECTED")
    return text


@dataclass(frozen=True)
class D2FrozenInputAuthorityV1:
    d0_prediction_artifact_type: str
    d0_detector_prediction_hash: str
    d1_prediction_artifact_type: str
    d1_rule_prediction_hash: str
    immutable_artifacts_required: bool
    replacement_artifacts_allowed: bool
    reconstructed_artifacts_allowed: bool
    d0_rerun_allowed: bool
    d1_rerun_allowed: bool
    d0_prediction_content_read_for_design: bool
    d1_prediction_content_read_for_design: bool


@dataclass(frozen=True)
class D2SourceResolutionPolicyV1:
    common_portfolio: str
    common_relation_count: int
    common42_authority_check_hash: str
    common42_authority_definition_hash: str
    canonical_v4_authority_hash: str
    common42_source_mapping_hash: str
    source_resolution_policy: str
    d1_prediction_locator_field: str
    relation_identity_field: str
    source_identity_field: str
    exact_relation_binding_lookup_required: bool
    string_convention_inference_allowed: bool
    opportunity_id_inversion_allowed: bool
    absent_binding_fail_closed: bool
    foreign_binding_fail_closed: bool
    ambiguous_binding_fail_closed: bool
    mapping_available: bool


@dataclass(frozen=True)
class D2RuleCorroborationPolicyV1:
    correction_direction: str
    required_distinct_source_count: int
    count_distinct_source_variables: bool
    duplicate_rules_from_same_source_count_once: bool
    corroboration_count_rationale: str
    same_second_policy: str
    temporal_tolerance_seconds: int
    rolling_window_allowed: bool
    temporal_dilation_allowed: bool
    event_expansion_allowed: bool
    corroboration_count_search_allowed: bool


@dataclass(frozen=True)
class D2FusionPolicyV1:
    pointwise_formula: str
    d0_alarm_boolean_only: bool
    d0_alarms_preserved: bool
    d0_suppression_allowed: bool
    rule_recovery_positive_direction_only: bool
    raw_any_rule_or_allowed: bool
    and_gating_allowed: bool
    weighted_fusion_allowed: bool
    d0_score_access_allowed: bool
    d1_numeric_reevaluation_allowed: bool
    label_aware_fusion: bool
    trainable_fusion: bool
    scientific_llm_runtime: bool
    fusion_candidates_compared: int
    hyperparameter_search_performed: bool


@dataclass(frozen=True)
class D2TriggerClassPolicyV1:
    allowed_trigger_classes: tuple[str, str, str, str]
    none_condition: str
    d0_only_condition: str
    rule_recovery_condition: str
    d0_and_rule_corroboration_condition: str
    trigger_class_changes_alarm_semantics: bool


@dataclass(frozen=True)
class D2MetricPolicyV1:
    corrected_event_policy_hash: str
    corrected_metric_policy_hash: str
    alarm_episode_policy: str
    attack_event_recall_formula: str
    normal_far_formula: str
    d0_missed_attack_recovery_formula: str
    d0_missed_attack_recovery_undefined_reason: str
    incremental_attack_recall_formula: str
    added_normal_recovery_far_formula: str
    incremental_normal_far_formula: str
    incremental_baseline: str
    point_adjustment_allowed: bool
    metrics_compute_during_design: bool


@dataclass(frozen=True)
class D2FuturePredictionContractV1:
    artifact_type: str
    physical_row_count: int
    first_physical_row_index: int
    last_physical_row_index: int
    one_record_per_physical_second: bool
    record_fields: tuple[str, ...]
    prediction_label_blind: bool
    prediction_frozen_before_label_access: bool
    optional_relation_ids_allowed: bool
    optional_source_ids_allowed: bool
    raw_numeric_values_allowed: bool
    d0_score_allowed: bool
    labels_allowed: bool
    metrics_allowed: bool
    future_execution_order: tuple[str, ...]


@dataclass(frozen=True)
class D2IndependenceDeclarationV1:
    d0_prediction_content_read_for_design: bool
    d1_prediction_content_read_for_design: bool
    d0_metric_artifact_read_for_design: bool
    d1_metric_artifact_read_for_design: bool
    d0_metrics_used_for_design: bool
    d1_metrics_used_for_design: bool
    test1_used_for_design: bool
    labels_used_for_design: bool
    fusion_candidates_compared: int
    hyperparameter_search_performed: bool
    rule_corroboration_count: int
    corroboration_count_rationale: str


@dataclass(frozen=True)
class D2DesignAuthorityV1:
    artifact_type: str
    schema_version: str
    task_id: str
    d2_id: str
    d2_role: str
    d2_fusion_family: str
    frozen_inputs: D2FrozenInputAuthorityV1
    source_resolution: D2SourceResolutionPolicyV1
    corroboration_policy: D2RuleCorroborationPolicyV1
    fusion_policy: D2FusionPolicyV1
    trigger_policy: D2TriggerClassPolicyV1
    metric_policy: D2MetricPolicyV1
    future_prediction_contract: D2FuturePredictionContractV1
    independence: D2IndependenceDeclarationV1
    scientific_executions: int
    d0_executions: int
    d1_executions: int
    d2_executions: int
    test2_accesses: int
    private_paths_exposed: int
    private_numeric_values_exposed: int
    d2_design_frozen: bool
    d2_authorized: bool
    d2_executed: bool
    outer_authorized: bool
    remote_egress_status: str
    push_attempted: bool
    design_hash: str

    def to_public_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=True))


@dataclass(frozen=True)
class D2ResolvedRuleSourceV1:
    relation_binding_hash: str
    relation_identity: str
    source_variable_identity: str


@dataclass(frozen=True)
class D2SyntheticRuleAlarmV1:
    physical_row_index: int
    relation_binding_hash: str
    source_variable_identity: str
    alarm_emitted: bool

    def __post_init__(self) -> None:
        _strict_index(self.physical_row_index, "physical_row")
        _sha(self.relation_binding_hash, "relation_binding")
        _strict_nonempty_string(self.source_variable_identity, "source_variable_identity")
        _strict_bool(self.alarm_emitted, "alarm_emitted")


@dataclass(frozen=True)
class D2SyntheticCombinedDecisionV1:
    physical_row_index: int
    d2_alarm_emitted: bool
    trigger_class: str
    distinct_rule_sources: tuple[str, ...]


def _design_payload(value: D2DesignAuthorityV1) -> dict[str, Any]:
    payload = value.to_public_dict()
    payload.pop("design_hash")
    return payload


def _build_expected_d2_design_v1() -> D2DesignAuthorityV1:
    frozen_inputs = D2FrozenInputAuthorityV1(
        "ScientificDetectorPredictionArtifactV1",
        FROZEN_D0_DETECTOR_PREDICTION_HASH,
        "ScientificRulePredictionArtifactV1",
        FROZEN_D1_RULE_PREDICTION_HASH,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
    )
    source_resolution = D2SourceResolutionPolicyV1(
        COMMON_PORTFOLIO,
        COMMON_RELATION_COUNT,
        COMMON42_AUTHORITY_CHECK_HASH,
        CANONICAL_AUTHORITY_DEFINITION_HASH,
        CANONICAL_V4_AUTHORITY_HASH,
        COMMON42_SOURCE_MAPPING_HASH,
        SOURCE_RESOLUTION_POLICY,
        "relation_binding_hash",
        "relation_identity",
        "source",
        True,
        False,
        False,
        True,
        True,
        True,
        True,
    )
    corroboration = D2RuleCorroborationPolicyV1(
        CORRECTION_DIRECTION,
        REQUIRED_DISTINCT_SOURCE_COUNT,
        True,
        True,
        CORROBORATION_COUNT_RATIONALE,
        SAME_SECOND_POLICY,
        0,
        False,
        False,
        False,
        False,
    )
    fusion = D2FusionPolicyV1(
        "D2_alarm(t)=D0_alarm(t) OR (cardinality(distinct(D1_alarming_sources_at_t))>=2)",
        True,
        True,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        0,
        False,
    )
    trigger = D2TriggerClassPolicyV1(
        TRIGGER_CLASSES,
        "not_d0_and_not_corroborated",
        "d0_and_not_corroborated",
        "not_d0_and_corroborated",
        "d0_and_corroborated",
        False,
    )
    metrics = D2MetricPolicyV1(
        CORRECTED_EVENT_POLICY_HASH,
        CORRECTED_METRIC_POLICY_HASH,
        ALARM_EPISODE_POLICY,
        ATTACK_EVENT_RECALL_FORMULA,
        NORMAL_FAR_FORMULA,
        D0_MISSED_ATTACK_RECOVERY_FORMULA,
        D0_MISSED_ATTACK_RECOVERY_UNDEFINED_REASON,
        INCREMENTAL_ATTACK_RECALL_FORMULA,
        ADDED_NORMAL_RECOVERY_FAR_FORMULA,
        INCREMENTAL_NORMAL_FAR_FORMULA,
        "D0_DETECTOR_ONLY",
        False,
        False,
    )
    future = D2FuturePredictionContractV1(
        "ScientificCombinedPredictionArtifactV1",
        54000,
        0,
        53999,
        True,
        (
            "physical_row_index",
            "d2_alarm_emitted",
            "trigger_class",
            "optional_provenance_identity_refs",
        ),
        True,
        True,
        True,
        True,
        False,
        False,
        False,
        False,
        (
            "LOAD_EXACT_FROZEN_D0_PREDICTION",
            "LOAD_EXACT_FROZEN_D1_PREDICTION",
            "RESOLVE_CANONICAL_COMMON42_RULE_SOURCES",
            "COMPUTE_EXACT_POINTWISE_D2_FUSION",
            "FREEZE_COMBINED_PREDICTION",
            "LOAD_LABELS_ONLY_AFTER_PREDICTION_FREEZE",
            "COMPUTE_FROZEN_METRICS",
        ),
    )
    independence = D2IndependenceDeclarationV1(
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        0,
        False,
        REQUIRED_DISTINCT_SOURCE_COUNT,
        CORROBORATION_COUNT_RATIONALE,
    )
    provisional = D2DesignAuthorityV1(
        DESIGN_ARTIFACT_TYPE,
        SCHEMA_VERSION,
        TASK_ID,
        D2_ID,
        D2_ROLE,
        D2_FUSION_FAMILY,
        frozen_inputs,
        source_resolution,
        corroboration,
        fusion,
        trigger,
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
        True,
        False,
        False,
        False,
        "LOCAL_ONLY_NOT_PUSHED",
        False,
        "",
    )
    return replace(provisional, design_hash=stable_hash_v1(_design_payload(provisional)))


D2_DESIGN_HASH = _build_expected_d2_design_v1().design_hash

_ISSUED_DESIGNS: dict[int, tuple[weakref.ReferenceType[D2DesignAuthorityV1], str]] = {}


def _issue_design(value: D2DesignAuthorityV1) -> D2DesignAuthorityV1:
    object_id = id(value)

    def cleanup(dead_ref: weakref.ReferenceType[D2DesignAuthorityV1]) -> None:
        issued = _ISSUED_DESIGNS.get(object_id)
        if issued is not None and issued[0] is dead_ref:
            _ISSUED_DESIGNS.pop(object_id, None)

    reference = weakref.ref(value, cleanup)
    _ISSUED_DESIGNS[object_id] = (reference, value.design_hash)
    return value


def build_d2_design_authority_v1() -> D2DesignAuthorityV1:
    """Issue the sole canonical D2 design; no scientific knobs exist."""

    return _issue_design(_build_expected_d2_design_v1())


def validate_d2_design_authority_v1(value: D2DesignAuthorityV1) -> str:
    if type(value) is not D2DesignAuthorityV1:
        raise D2DesignError("D2_DESIGN_TYPE_REJECTED")
    issued = _ISSUED_DESIGNS.get(id(value))
    if issued is None or issued[0]() is not value or issued[1] != value.design_hash:
        raise D2DesignError("D2_DESIGN_FACTORY_CUSTODY_REJECTED")
    expected = _build_expected_d2_design_v1()
    if value != expected or value.to_public_dict() != expected.to_public_dict():
        raise D2DesignError("D2_DESIGN_REPLAY_REJECTED")
    if stable_hash_v1(_design_payload(value)) != value.design_hash:
        raise D2DesignError("D2_DESIGN_SELF_HASH_REJECTED")
    return value.design_hash


def validate_d2_design_document_v1(document: Mapping[str, Any]) -> str:
    if type(document) is not dict:
        raise D2DesignError("D2_DESIGN_DOCUMENT_TYPE_REJECTED")
    expected = _build_expected_d2_design_v1().to_public_dict()
    if document != expected:
        raise D2DesignError("D2_DESIGN_DOCUMENT_REPLAY_REJECTED")
    payload = dict(document)
    observed = payload.pop("design_hash", None)
    if observed != stable_hash_v1(payload) or observed != D2_DESIGN_HASH:
        raise D2DesignError("D2_DESIGN_DOCUMENT_SELF_HASH_REJECTED")
    return str(observed)


def canonical_config_document_v1() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_type": CONFIG_ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "design": _build_expected_d2_design_v1().to_public_dict(),
        "d0_prediction_content_read_for_design": False,
        "d1_prediction_content_read_for_design": False,
        "d0_metric_artifact_read_for_design": False,
        "d1_metric_artifact_read_for_design": False,
        "test1_used_for_design": False,
        "labels_used_for_design": False,
        "scientific_executions": 0,
        "d0_executions": 0,
        "d1_executions": 0,
        "d2_executions": 0,
        "test2_accesses": 0,
        "remote_egress_status": "LOCAL_ONLY_NOT_PUSHED",
        "push_attempted": False,
    }
    return {**payload, "config_hash": stable_hash_v1(payload)}


def validate_d2_config_v1(document: Mapping[str, Any]) -> str:
    if type(document) is not dict or document != canonical_config_document_v1():
        raise D2DesignError("D2_CONFIG_REPLAY_REJECTED")
    payload = dict(document)
    observed = payload.pop("config_hash", None)
    if observed != stable_hash_v1(payload):
        raise D2DesignError("D2_CONFIG_SELF_HASH_REJECTED")
    return str(observed)


def common42_source_mapping_hash_v1(
    authority: NormalOnlyAuthorityDefinitionV1,
) -> str:
    validate_canonical_common42_authority_v1(authority)
    payload = {
        "artifact_type": "task039e3_r2r_d2_common42_source_mapping_v1",
        "common42_authority_definition_hash": authority.authority_definition_hash,
        "mappings": [
            {
                "relation_binding_hash": item.relation_binding_hash,
                "relation_identity": item.relation_identity,
                "source_variable_identity": item.source,
            }
            for item in authority.relations
        ],
    }
    observed = stable_hash_v1(payload)
    if observed != COMMON42_SOURCE_MAPPING_HASH:
        raise D2DesignError("D2_COMMON42_SOURCE_MAPPING_REJECTED")
    return observed


def resolve_d1_alarm_source_v1(
    relation_binding_hash: str,
    authority: NormalOnlyAuthorityDefinitionV1,
) -> D2ResolvedRuleSourceV1:
    """Resolve an explicit D1 relation binding through exact COMMON-42 authority."""

    binding = _sha(relation_binding_hash, "relation_binding")
    common42_source_mapping_hash_v1(authority)
    matches = [item for item in authority.relations if item.relation_binding_hash == binding]
    if len(matches) != 1:
        raise D2DesignError("D2_D1_SOURCE_RESOLUTION_UNAVAILABLE")
    relation = matches[0]
    return D2ResolvedRuleSourceV1(
        relation.relation_binding_hash,
        relation.relation_identity,
        relation.source,
    )


def fuse_d2_point_v1(
    d0_alarm: bool,
    alarming_source_variables: tuple[str, ...],
) -> tuple[bool, str]:
    """Apply the frozen D2 rule to one synthetic physical second."""

    d0 = _strict_bool(d0_alarm, "d0_alarm")
    if type(alarming_source_variables) is not tuple:
        raise D2DesignError("D2_SOURCE_VARIABLE_COLLECTION_REJECTED")
    sources = tuple(
        _strict_nonempty_string(item, "source_variable_identity")
        for item in alarming_source_variables
    )
    corroborated = len(set(sources)) >= REQUIRED_DISTINCT_SOURCE_COUNT
    if not d0 and not corroborated:
        return False, "NONE"
    if d0 and not corroborated:
        return True, "D0_ONLY"
    if not d0 and corroborated:
        return True, "RULE_RECOVERY"
    return True, "D0_AND_RULE_CORROBORATION"


def fuse_synthetic_timeline_v1(
    d0_alarm_booleans: tuple[bool, ...],
    rule_alarm_records: tuple[D2SyntheticRuleAlarmV1, ...],
) -> tuple[D2SyntheticCombinedDecisionV1, ...]:
    """Synthetic-only same-second fusion helper for contract testing."""

    if type(d0_alarm_booleans) is not tuple or type(rule_alarm_records) is not tuple:
        raise D2DesignError("D2_SYNTHETIC_TIMELINE_INPUT_REJECTED")
    d0_values = tuple(_strict_bool(item, "d0_alarm") for item in d0_alarm_booleans)
    by_index: dict[int, list[str]] = {index: [] for index in range(len(d0_values))}
    for record in rule_alarm_records:
        if type(record) is not D2SyntheticRuleAlarmV1:
            raise D2DesignError("D2_SYNTHETIC_RULE_ALARM_TYPE_REJECTED")
        if record.physical_row_index >= len(d0_values):
            raise D2DesignError("D2_SYNTHETIC_RULE_ALARM_INDEX_REJECTED")
        if record.alarm_emitted:
            by_index[record.physical_row_index].append(record.source_variable_identity)
    result: list[D2SyntheticCombinedDecisionV1] = []
    for index, d0_alarm in enumerate(d0_values):
        ordered_sources = tuple(sorted(set(by_index[index])))
        alarm, trigger_class = fuse_d2_point_v1(d0_alarm, ordered_sources)
        result.append(D2SyntheticCombinedDecisionV1(index, alarm, trigger_class, ordered_sources))
    return tuple(result)


__all__ = [
    "ADDED_NORMAL_RECOVERY_FAR_FORMULA",
    "COMMON42_SOURCE_MAPPING_HASH",
    "CORROBORATION_COUNT_RATIONALE",
    "D0_MISSED_ATTACK_RECOVERY_FORMULA",
    "D0_MISSED_ATTACK_RECOVERY_UNDEFINED_REASON",
    "D2DesignAuthorityV1",
    "D2DesignError",
    "D2FrozenInputAuthorityV1",
    "D2FusionPolicyV1",
    "D2FuturePredictionContractV1",
    "D2IndependenceDeclarationV1",
    "D2MetricPolicyV1",
    "D2ResolvedRuleSourceV1",
    "D2RuleCorroborationPolicyV1",
    "D2SourceResolutionPolicyV1",
    "D2SyntheticCombinedDecisionV1",
    "D2SyntheticRuleAlarmV1",
    "D2TriggerClassPolicyV1",
    "D2_DESIGN_HASH",
    "D2_FUSION_FAMILY",
    "D2_ID",
    "D2_ROLE",
    "FROZEN_D0_DETECTOR_PREDICTION_HASH",
    "FROZEN_D1_RULE_PREDICTION_HASH",
    "INCREMENTAL_ATTACK_RECALL_FORMULA",
    "INCREMENTAL_NORMAL_FAR_FORMULA",
    "REQUIRED_DISTINCT_SOURCE_COUNT",
    "SAME_SECOND_POLICY",
    "SOURCE_RESOLUTION_POLICY",
    "TRIGGER_CLASSES",
    "build_d2_design_authority_v1",
    "canonical_config_document_v1",
    "common42_source_mapping_hash_v1",
    "fuse_d2_point_v1",
    "fuse_synthetic_timeline_v1",
    "resolve_d1_alarm_source_v1",
    "validate_d2_config_v1",
    "validate_d2_design_authority_v1",
    "validate_d2_design_document_v1",
]
