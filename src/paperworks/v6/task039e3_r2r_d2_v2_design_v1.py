"""Frozen D2 V2 native-horizon corroboration preregistration.

This module is design authority only.  It performs no D0, D1, D2, label,
feature, metric, test2, or OUTER I/O.  Its executable helpers accept synthetic
fixtures only and exist to make the causal token semantics mechanically
testable before any scientific execution is authorized.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from typing import Any, Mapping
import weakref

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_d2_design_v1 import (
    ADDED_NORMAL_RECOVERY_FAR_FORMULA,
    D0_MISSED_ATTACK_RECOVERY_FORMULA,
    D0_MISSED_ATTACK_RECOVERY_UNDEFINED_REASON,
    INCREMENTAL_ATTACK_RECALL_FORMULA,
    INCREMENTAL_NORMAL_FAR_FORMULA,
)
from paperworks.v6.task039e3_r2r_utility_evaluator_metrics_v1 import (
    ALARM_EPISODE_POLICY,
    ATTACK_EVENT_RECALL_FORMULA,
    NORMAL_FAR_FORMULA,
)
from paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 import (
    CANONICAL_AUTHORITY_DEFINITION_HASH,
    E1_PUBLIC_MANIFEST_HASH,
    EXECUTABLE_EQUIVALENCE_HASH,
    build_common42_authority_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    CANONICAL_V4_AUTHORITY_HASH,
    CORRECTED_EVENT_POLICY_HASH,
    CORRECTED_METRIC_POLICY_HASH,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-REDESIGN-DECISION-AND-PREREGISTRATION-V1"
SCHEMA_VERSION = "1.0.0"
DESIGN_ARTIFACT_TYPE = "task039e3_r2r_d2_v2_design_authority_v1"
CONFIG_ARTIFACT_TYPE = "task039e3_r2r_d2_v2_native_horizon_corroboration_config_v1"
NATIVE_HORIZON_MAP_ARTIFACT_TYPE = "task039e3_r2r_d2_v2_native_temporal_horizon_map_v1"

D2_V2_ID = "D2_V2_D0_PLUS_NATIVE_HORIZON_MULTI_SOURCE_CORROBORATION_V1"
D2_V2_STAGE_ROLE = "INNER_LABEL_INFORMED_DEVELOPMENT_POLICY"
D2_V2_FUSION_FAMILY = (
    "DETECTOR_PRESERVING_NATIVE_HORIZON_ASYNCHRONOUS_MULTI_SOURCE_CORROBORATION"
)
D2_V2_PRIMARY_TARGET_MECHANISM = "MULTI_SOURCE_ASYNCHRONOUS_RECOVERY_SIGNAL"
D2_V2_DESIGN_OBJECTIVE = (
    "RECOVER_MULTI_SOURCE_ASYNCHRONOUS_RULE_SIGNAL_WITHOUT_TEST1_TUNED_TIME_WINDOW"
)

D2_V1_ID = "D2_D0_PLUS_VERIFIED_RULE_CORROBORATION_V1"
D2_V1_DESIGN_HASH = "eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
D2_V1_COMBINED_PREDICTION_HASH = (
    "cf1005a03d98481b57c3ce2ad74db3e2e5d2dc3a1983d60e0aedb4f46c83b3f5"
)
D2_V1_CONCLUSION = "CURRENT_D2_COMBINED_UTILITY_NOT_SUPPORTED_ON_INNER"
FROZEN_D0_PREDICTION_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
FROZEN_D1_PREDICTION_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
FROZEN_SOURCE_MAP_HASH = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"

NATIVE_TEMPORAL_AUTHORITY_TYPE = (
    "COMMON42_CANONICAL_RULE_DESCRIPTOR_SELECTED_HORIZON_SECONDS_V1"
)
NATIVE_TEMPORAL_AUTHORITY_FIELD = "selected_horizon_seconds"
NATIVE_TEMPORAL_SOURCE_FIELD = "selected_delay_horizon_seconds"
NATIVE_HORIZON_ORIGIN = "FROZEN_PUBLIC_COMMON42_RULE_TEMPORAL_AUTHORITY"
NATIVE_HORIZON_UNIT = "ONE_SECOND_UNITS"
COMMON_RELATION_COUNT = 42
REQUIRED_DISTINCT_SOURCE_COUNT = 2
TOKEN_START_POLICY = "D1_DECISION_PHYSICAL_ROW_INDEX"
TOKEN_EXPIRY_POLICY = "DECISION_PHYSICAL_ROW_INDEX_PLUS_FROZEN_NATIVE_HORIZON_INCLUSIVE"
TOKEN_CLIP_POLICY = "PHYSICAL_SPLIT_END_ONLY"
ACTIVE_TOKEN_FORMULA = "decision_index<=t<=decision_index+native_horizon_seconds"
FUSION_FORMULA = "D2_V2_alarm(t)=D0_alarm(t) OR (cardinality(distinct(active_D1_sources_at_t))>=2)"

TRIGGER_CLASSES = (
    "NONE",
    "D0_ONLY",
    "RULE_RECOVERY_NATIVE_HORIZON",
    "D0_AND_RULE_CORROBORATION_NATIVE_HORIZON",
)

# Public values copied exactly from the already-tracked executable-equivalence
# authority.  These are relation delays, not private calibration values.
FROZEN_NATIVE_HORIZON_BINDINGS: tuple[tuple[str, int], ...] = (
    ("0b2da257d89b11ace02f81328fdcbf10380130e35dd7cff1492194099bc6eb4b", 1),
    ("0e70af83f6bacd3432a230454f601e6386a2996fd816d18e75a79e757b7e1d0f", 5),
    ("0f658a081aaf9d47eb15c8c0547fe31d23d49a43740911ed9f2c3b36a9a429c5", 1),
    ("1289d048e50ee131727a71788166be7feffb285d712e75403ee3046f5d22d9cc", 10),
    ("16cb66eaedd4a1f8685f9d621e8515edbd112c86c635b37ba06e2a30fcc49ffc", 60),
    ("1b68720367a8a6d29c858f5e59fea00736d9ebf8dfdf7ff48973b856fbca561e", 1),
    ("204abd371c860fa8ad746e687b73e8cea948268fd0656435f031b3626ae967ed", 1),
    ("21f6f2a96dd168711b5e0cca999a6b22683f504d8cfb2760888a4ab80fd84b51", 1),
    ("30b80b42163722fbf0fe20f3d258f61ae889294b5a860c21114d6125f2cf62b0", 1),
    ("3864585573b951ad9d9d2be170d6d6094c637e3029347b4851e06f45e8a1ab15", 60),
    ("3c9df59cb467ce444ee90616092ca0cc09cefc55a2bdf727a6938fe0033f9161", 5),
    ("3dbc8a58c388b5c0784ad658db4a17dafa3f5b5cb28192f32f4ffba82256be31", 1),
    ("44a0a75f85e92223cd48c85e36e62974f26ac1b0e1b2b5b8b37c35010f9b0a8d", 10),
    ("48d74de36469bfcc3c077577adaa247f92346d8deedbd5ec803f39cfd37b99cc", 30),
    ("49ffab3ee089c9d1d99fbb8d0d22dfaceb324207f727ba499475bef09afbf532", 1),
    ("4a8e908cbb3fa7b844aaf7238862d047268fed3889a79b5c8b0b42443bc2b125", 60),
    ("4f84d8bb244fcafb82b8a8fbe6c5dd397d329a9d5df311682a8a8ae2206e6680", 1),
    ("53645fb94519c2e374ee51f136f758d513c3c5b2c0fcc640b0b4d1845da53918", 10),
    ("55a52946ca90609619c198ad3da8b1e47140d97dcf8184e22a4a747df669bdd5", 1),
    ("5af9d8c43235f048c32f8dea66d75114e29edf35975ec2687333a8e1362657b5", 1),
    ("5dfc20b41b38244a264cc74f915d4c62d14286db99e0a96921ce11d0698c339b", 1),
    ("5f4495927c0a79d685b710b4531542cdfa1583b5f2bf5fbd0e253201e3902cd0", 5),
    ("75ee416429ab599aa7eb67fc6c045cc266c21fb8b35c2088d6ab810914463381", 60),
    ("771cda117815b723c681559b33c60f7935774cd0b1f27970854b97971b2a10a5", 1),
    ("7c39a5bb783bbcfd757f08a8808fcab0c128cae9ea16742ef6fbdf6d75a9642f", 1),
    ("903262b61a1ed4c1324176ac0405590651941fb8c42c4e0585eba30ca6e72789", 1),
    ("906cd998411c78071974a9e0c96d82d3094c844c4f8d67f97ea72c72496c9785", 60),
    ("99d4230cba35d407b5ebac9fe47c0d0db9020444c1875cc55ab13eb59569dc9f", 1),
    ("9b985c0d4e95a2df49df445e1f5f5b47f54b50c946c168ce129eae595deec6e2", 10),
    ("9c33b11c1095fce4aeda9a9865cb202813edc112fb25ab1385256c878911db8e", 1),
    ("a84e45627c76351d6d867b20a7b00be6b3908dc53a38142c739d9c3480aa73d3", 60),
    ("a8b45686f0af3335d1f7b7f3bebb00d051b296f885daaba647eca936ef5d7745", 60),
    ("ad0d7c6e2e47966df473f98af02d3e9f35f0de9e696fa4e99cc05189dc0d4438", 1),
    ("bc5160b571b18d7438a5855f83747f55a555574f13d458b2903abd656dd5d58b", 60),
    ("bffb5b67d8b04ae8b235dbc7a5a15706c69d6aad34ccd71cc58b181e722ec935", 60),
    ("c574e104acee0e509317e7cd66112725678ecf6bc1759a3e26915b8a8cd7c207", 1),
    ("d6d807ea85531f60daeabc4df766012bffdbaeec004f675b74655965326db8f8", 1),
    ("daaaee2795f7763ba55608107358506f561ccb44da9970be20eaa17cfcf4e63d", 1),
    ("db78e2c122ba53bd39a554c7efee83ec439f11da333e4f61df80da741df43dda", 1),
    ("e2fdbb7013bfbbd896c272e33bdddf96bcf420cbf000c9c103370e591c1be10d", 30),
    ("ed33b18de044e209f7d6db492cc52bc8ea1e782a659fc0747e5c92030a2b1222", 60),
    ("fde2a820965ad298c8d636286b5f85972d853a279c4801f991f94e5550eacac8", 10),
)


class D2V2DesignError(ValueError):
    """Fixed-category V2 design or authority rejection."""


def _strict_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise D2V2DesignError(f"D2_V2_{name.upper()}_BOOLEAN_REJECTED")
    return value


def _strict_int(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise D2V2DesignError(f"D2_V2_{name.upper()}_INTEGER_REJECTED")
    return value


def _strict_string(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise D2V2DesignError(f"D2_V2_{name.upper()}_STRING_REJECTED")
    return value


def _sha(value: object, name: str) -> str:
    text = _strict_string(value, name)
    if len(text) != 64 or text != text.lower():
        raise D2V2DesignError(f"D2_V2_{name.upper()}_HASH_REJECTED")
    try:
        int(text, 16)
    except ValueError as exc:
        raise D2V2DesignError(f"D2_V2_{name.upper()}_HASH_REJECTED") from exc
    return text


@dataclass(frozen=True)
class D2V2NativeHorizonBindingV1:
    relation_binding_hash: str
    native_horizon_seconds: int

    def __post_init__(self) -> None:
        _sha(self.relation_binding_hash, "relation_binding")
        _strict_int(self.native_horizon_seconds, "native_horizon", minimum=1)


@dataclass(frozen=True)
class D2V2NativeTemporalHorizonMapV1:
    artifact_type: str
    schema_version: str
    authority_type: str
    authority_field: str
    authority_source_hash: str
    common42_authority_definition_hash: str
    source_map_hash: str
    entry_count: int
    horizon_unit: str
    entries: tuple[D2V2NativeHorizonBindingV1, ...]
    values_public: bool
    label_derived_count: int
    test1_derived_count: int
    missing_count: int
    ambiguous_count: int
    map_hash: str

    def to_public_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=True))


@dataclass(frozen=True)
class D2V2InputAuthorityV1:
    d2_v1_id: str
    d2_v1_design_hash: str
    d2_v1_combined_prediction_hash: str
    d2_v1_conclusion: str
    d0_detector_prediction_hash: str
    d1_rule_prediction_hash: str
    source_map_hash: str
    common_relation_count: int
    immutable_inputs_required: bool
    d0_rerun_allowed: bool
    d1_rerun_allowed: bool
    rule_reevaluation_allowed: bool


@dataclass(frozen=True)
class D2V2NativeHorizonAuthorityV1:
    authority_available: bool
    authority_type: str
    authority_field: str
    authority_source_hash: str
    authority_definition_hash: str
    canonical_v4_authority_hash: str
    source_map_hash: str
    native_horizon_map_hash: str
    relation_count: int
    unique_relation_count: int
    missing_horizon_count: int
    ambiguous_horizon_count: int
    foreign_relation_count: int
    label_derived_horizon_count: int
    test1_derived_horizon_count: int
    horizon_unit: str
    per_rule_horizon_values_public: bool
    native_temporal_authority_only: bool


@dataclass(frozen=True)
class D2V2EvidenceTokenPolicyV1:
    token_start_policy: str
    token_expiry_policy: str
    token_clip_policy: str
    active_token_formula: str
    causal_runtime: bool
    backdated_rule_evidence: bool
    future_information_used: bool
    global_fixed_temporal_window_seconds: int | None
    diagnostic_gap_values_used_as_parameters: bool
    horizon_multiplier_allowed: bool


@dataclass(frozen=True)
class D2V2CorroborationPolicyV1:
    primary_target_mechanism: str
    required_distinct_source_count: int
    count_distinct_source_variables: bool
    same_source_duplicates_count_once: bool
    native_horizon_rule_corroboration_formula: str
    exact_same_second_included: bool
    single_source_fallback: bool
    source_count_search_allowed: bool
    temporal_window_search_allowed: bool
    anti_fp_simultaneous_exclusion_allowed: bool


@dataclass(frozen=True)
class D2V2FusionPolicyV1:
    fusion_family: str
    design_objective: str
    fusion_formula: str
    d0_alarm_boolean_only: bool
    d0_alarms_preserved: bool
    d0_suppression_allowed: bool
    d0_score_dependency: bool
    rule_reevaluation_dependency: bool
    trainable_fusion: bool
    label_aware_fusion: bool
    scientific_llm_runtime: bool
    trigger_classes: tuple[str, str, str, str]


@dataclass(frozen=True)
class D2V2MetricPolicyV1:
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
    metrics_computed_during_design: bool


@dataclass(frozen=True)
class D2V2FuturePredictionContractV1:
    artifact_type: str
    physical_row_count: int
    first_physical_row_index: int
    last_physical_row_index: int
    record_fields: tuple[str, ...]
    prediction_label_blind: bool
    prediction_frozen_before_label_access: bool
    raw_horizon_values_allowed: bool
    source_set_contents_allowed: bool
    labels_allowed: bool
    d0_scores_allowed: bool
    future_execution_order: tuple[str, ...]


@dataclass(frozen=True)
class D2V2DesignProvenanceV1:
    d2_v1_negative_result_known: bool
    d2_v1_failure_diagnostic_known: bool
    project_level_inner_diagnostic_informed_v2_design: bool
    project_level_test1_labels_informed_problem_formulation: bool
    test1_labels_used_in_prior_diagnostic: bool
    label_file_read_during_this_design_task: bool
    test1_feature_read_during_design: bool
    test2_read_during_design: bool
    d2_v2_predictions_observed_before_freeze: bool
    d2_v2_metrics_observed_before_freeze: bool
    recovery_miss_01_min_gap_seconds_known: bool
    recovery_miss_03_min_gap_seconds_known: bool
    diagnostic_gap_values_used_as_v2_parameters: bool
    alternative_v2_policies_executed: int
    hypothetical_performance_calculations: int
    parameter_sweeps: int
    new_thresholds_selected: int
    new_fixed_temporal_window_selected: bool


@dataclass(frozen=True)
class D2V2DesignAuthorityV1:
    artifact_type: str
    schema_version: str
    task_id: str
    d2_v2_id: str
    stage_role: str
    input_authority: D2V2InputAuthorityV1
    native_horizon_authority: D2V2NativeHorizonAuthorityV1
    evidence_token_policy: D2V2EvidenceTokenPolicyV1
    corroboration_policy: D2V2CorroborationPolicyV1
    fusion_policy: D2V2FusionPolicyV1
    metric_policy: D2V2MetricPolicyV1
    future_prediction_contract: D2V2FuturePredictionContractV1
    provenance: D2V2DesignProvenanceV1
    d2_v2_design_frozen: bool
    d2_v2_authorized: bool
    d2_v2_executed: bool
    d2_v2_result_frozen: bool
    outer_authorized: bool
    remote_egress_status: str
    push_attempted: bool
    design_hash: str

    def to_public_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=True))


@dataclass(frozen=True)
class D2V2SyntheticRuleAlarmV1:
    decision_physical_row_index: int
    relation_binding_hash: str
    source_variable_identity: str
    alarm_emitted: bool

    def __post_init__(self) -> None:
        _strict_int(self.decision_physical_row_index, "decision_index")
        _sha(self.relation_binding_hash, "relation_binding")
        _strict_string(self.source_variable_identity, "source_variable_identity")
        _strict_bool(self.alarm_emitted, "alarm_emitted")


@dataclass(frozen=True)
class D2V2SyntheticEvidenceTokenV1:
    relation_binding_hash: str
    source_variable_identity: str
    start_physical_row_index: int
    expiry_physical_row_index: int


@dataclass(frozen=True)
class D2V2SyntheticCombinedDecisionV1:
    physical_row_index: int
    d2_v2_alarm_emitted: bool
    trigger_class: str
    active_distinct_sources: tuple[str, ...]


def _map_payload(value: D2V2NativeTemporalHorizonMapV1) -> dict[str, Any]:
    payload = value.to_public_dict()
    payload.pop("map_hash")
    return payload


def _build_expected_native_horizon_map_v1() -> D2V2NativeTemporalHorizonMapV1:
    entries = tuple(D2V2NativeHorizonBindingV1(*row) for row in FROZEN_NATIVE_HORIZON_BINDINGS)
    provisional = D2V2NativeTemporalHorizonMapV1(
        NATIVE_HORIZON_MAP_ARTIFACT_TYPE,
        SCHEMA_VERSION,
        NATIVE_TEMPORAL_AUTHORITY_TYPE,
        NATIVE_TEMPORAL_AUTHORITY_FIELD,
        EXECUTABLE_EQUIVALENCE_HASH,
        CANONICAL_AUTHORITY_DEFINITION_HASH,
        FROZEN_SOURCE_MAP_HASH,
        COMMON_RELATION_COUNT,
        NATIVE_HORIZON_UNIT,
        entries,
        True,
        0,
        0,
        0,
        0,
        "",
    )
    return replace(provisional, map_hash=stable_hash_v1(_map_payload(provisional)))


D2_V2_NATIVE_HORIZON_MAP_HASH = _build_expected_native_horizon_map_v1().map_hash


def native_horizon_map_document_v1() -> dict[str, Any]:
    return _build_expected_native_horizon_map_v1().to_public_dict()


def validate_native_horizon_map_document_v1(document: Mapping[str, Any]) -> str:
    if type(document) is not dict or document != native_horizon_map_document_v1():
        raise D2V2DesignError("D2_V2_NATIVE_HORIZON_MAP_REPLAY_REJECTED")
    payload = dict(document)
    observed = payload.pop("map_hash", None)
    if observed != stable_hash_v1(payload) or observed != D2_V2_NATIVE_HORIZON_MAP_HASH:
        raise D2V2DesignError("D2_V2_NATIVE_HORIZON_MAP_SELF_HASH_REJECTED")
    return str(observed)


def resolve_native_horizon_map_from_frozen_authorities_v1(
    executable_equivalence: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
    source_map: Mapping[str, Any],
) -> D2V2NativeTemporalHorizonMapV1:
    """Replay the exact public 42-relation horizon map; accept no alternatives."""

    authority = build_common42_authority_v1(executable_equivalence, evidence_manifest)
    if type(source_map) is not dict:
        raise D2V2DesignError("D2_V2_SOURCE_MAP_TYPE_REJECTED")
    source_payload = dict(source_map)
    observed_source_hash = source_payload.pop("artifact_hash", None)
    if observed_source_hash != stable_hash_v1(source_payload) or observed_source_hash != FROZEN_SOURCE_MAP_HASH:
        raise D2V2DesignError("D2_V2_SOURCE_MAP_REPLAY_REJECTED")
    source_entries = source_map.get("entries")
    if not isinstance(source_entries, list) or len(source_entries) != COMMON_RELATION_COUNT:
        raise D2V2DesignError("D2_V2_SOURCE_MAP_CLOSURE_REJECTED")
    source_bindings = [entry.get("relation_binding_hash") for entry in source_entries if isinstance(entry, Mapping)]
    if len(source_bindings) != COMMON_RELATION_COUNT or len(set(source_bindings)) != COMMON_RELATION_COUNT:
        raise D2V2DesignError("D2_V2_SOURCE_MAP_RELATION_SET_REJECTED")
    resolved = tuple(sorted((item.relation_binding_hash, item.selected_horizon_seconds) for item in authority.relations))
    if resolved != FROZEN_NATIVE_HORIZON_BINDINGS or set(source_bindings) != {item[0] for item in resolved}:
        raise D2V2DesignError("D2_V2_NATIVE_TEMPORAL_AUTHORITY_REJECTED")
    return _build_expected_native_horizon_map_v1()


def _design_payload(value: D2V2DesignAuthorityV1) -> dict[str, Any]:
    payload = value.to_public_dict()
    payload.pop("design_hash")
    return payload


def _build_expected_d2_v2_design_v1() -> D2V2DesignAuthorityV1:
    provisional = D2V2DesignAuthorityV1(
        DESIGN_ARTIFACT_TYPE,
        SCHEMA_VERSION,
        TASK_ID,
        D2_V2_ID,
        D2_V2_STAGE_ROLE,
        D2V2InputAuthorityV1(
            D2_V1_ID,
            D2_V1_DESIGN_HASH,
            D2_V1_COMBINED_PREDICTION_HASH,
            D2_V1_CONCLUSION,
            FROZEN_D0_PREDICTION_HASH,
            FROZEN_D1_PREDICTION_HASH,
            FROZEN_SOURCE_MAP_HASH,
            COMMON_RELATION_COUNT,
            True,
            False,
            False,
            False,
        ),
        D2V2NativeHorizonAuthorityV1(
            True,
            NATIVE_TEMPORAL_AUTHORITY_TYPE,
            NATIVE_TEMPORAL_AUTHORITY_FIELD,
            EXECUTABLE_EQUIVALENCE_HASH,
            CANONICAL_AUTHORITY_DEFINITION_HASH,
            CANONICAL_V4_AUTHORITY_HASH,
            FROZEN_SOURCE_MAP_HASH,
            D2_V2_NATIVE_HORIZON_MAP_HASH,
            42,
            42,
            0,
            0,
            0,
            0,
            0,
            NATIVE_HORIZON_UNIT,
            True,
            True,
        ),
        D2V2EvidenceTokenPolicyV1(
            TOKEN_START_POLICY,
            TOKEN_EXPIRY_POLICY,
            TOKEN_CLIP_POLICY,
            ACTIVE_TOKEN_FORMULA,
            True,
            False,
            False,
            None,
            False,
            False,
        ),
        D2V2CorroborationPolicyV1(
            D2_V2_PRIMARY_TARGET_MECHANISM,
            REQUIRED_DISTINCT_SOURCE_COUNT,
            True,
            True,
            "native_horizon_rule_corroboration(t)=cardinality(S_t)>=2",
            True,
            False,
            False,
            False,
            False,
        ),
        D2V2FusionPolicyV1(
            D2_V2_FUSION_FAMILY,
            D2_V2_DESIGN_OBJECTIVE,
            FUSION_FORMULA,
            True,
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            TRIGGER_CLASSES,
        ),
        D2V2MetricPolicyV1(
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
            False,
        ),
        D2V2FuturePredictionContractV1(
            "ScientificCombinedPredictionArtifactV2",
            54000,
            0,
            53999,
            (
                "physical_row_index",
                "d2_v2_alarm_emitted",
                "trigger_class",
                "sanitized_authority_refs",
            ),
            True,
            True,
            False,
            False,
            False,
            False,
            (
                "VALIDATE_D2_V2_DESIGN",
                "VALIDATE_D0_PREDICTION",
                "VALIDATE_D1_PREDICTION",
                "VALIDATE_SOURCE_MAP",
                "VALIDATE_NATIVE_HORIZON_MAP",
                "PARSE_D0_AND_D1_PREDICTIONS",
                "CONSTRUCT_CAUSAL_EVIDENCE_TOKENS",
                "COMPUTE_NATIVE_HORIZON_CORROBORATION",
                "CONSTRUCT_COMBINED_PREDICTION_V2",
                "FREEZE_COMBINED_PREDICTION_V2",
                "OPEN_LABEL_TEST1_AFTER_PREDICTION_FREEZE",
                "COMPUTE_FROZEN_METRICS",
            ),
        ),
        D2V2DesignProvenanceV1(
            True,
            True,
            True,
            True,
            True,
            False,
            False,
            False,
            False,
            False,
            True,
            True,
            False,
            0,
            0,
            0,
            0,
            False,
        ),
        True,
        False,
        False,
        False,
        False,
        "LOCAL_ONLY_NOT_PUSHED",
        False,
        "",
    )
    return replace(provisional, design_hash=stable_hash_v1(_design_payload(provisional)))


D2_V2_DESIGN_HASH = _build_expected_d2_v2_design_v1().design_hash

_ISSUED_DESIGNS: dict[int, tuple[weakref.ReferenceType[D2V2DesignAuthorityV1], str]] = {}


def build_d2_v2_design_authority_v1() -> D2V2DesignAuthorityV1:
    """Issue the sole frozen V2 design; no caller scientific knobs exist."""

    value = _build_expected_d2_v2_design_v1()
    object_id = id(value)

    def cleanup(dead_ref: weakref.ReferenceType[D2V2DesignAuthorityV1]) -> None:
        issued = _ISSUED_DESIGNS.get(object_id)
        if issued is not None and issued[0] is dead_ref:
            _ISSUED_DESIGNS.pop(object_id, None)

    reference = weakref.ref(value, cleanup)
    _ISSUED_DESIGNS[object_id] = (reference, value.design_hash)
    return value


def validate_d2_v2_design_authority_v1(value: D2V2DesignAuthorityV1) -> str:
    if type(value) is not D2V2DesignAuthorityV1:
        raise D2V2DesignError("D2_V2_DESIGN_TYPE_REJECTED")
    issued = _ISSUED_DESIGNS.get(id(value))
    if issued is None or issued[0]() is not value or issued[1] != value.design_hash:
        raise D2V2DesignError("D2_V2_DESIGN_FACTORY_CUSTODY_REJECTED")
    expected = _build_expected_d2_v2_design_v1()
    if value != expected or value.to_public_dict() != expected.to_public_dict():
        raise D2V2DesignError("D2_V2_DESIGN_REPLAY_REJECTED")
    if stable_hash_v1(_design_payload(value)) != value.design_hash:
        raise D2V2DesignError("D2_V2_DESIGN_SELF_HASH_REJECTED")
    return value.design_hash


def validate_d2_v2_design_document_v1(document: Mapping[str, Any]) -> str:
    if type(document) is not dict or document != _build_expected_d2_v2_design_v1().to_public_dict():
        raise D2V2DesignError("D2_V2_DESIGN_DOCUMENT_REPLAY_REJECTED")
    payload = dict(document)
    observed = payload.pop("design_hash", None)
    if observed != stable_hash_v1(payload) or observed != D2_V2_DESIGN_HASH:
        raise D2V2DesignError("D2_V2_DESIGN_DOCUMENT_SELF_HASH_REJECTED")
    return str(observed)


def canonical_config_document_v1() -> dict[str, Any]:
    design = _build_expected_d2_v2_design_v1()
    payload: dict[str, Any] = {
        "artifact_type": CONFIG_ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "d2_v2_id": D2_V2_ID,
        "d2_v2_design_hash": design.design_hash,
        "d0_prediction_hash": FROZEN_D0_PREDICTION_HASH,
        "d1_prediction_hash": FROZEN_D1_PREDICTION_HASH,
        "source_map_hash": FROZEN_SOURCE_MAP_HASH,
        "native_horizon_authority_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "native_horizon_map_hash": D2_V2_NATIVE_HORIZON_MAP_HASH,
        "required_distinct_source_count": REQUIRED_DISTINCT_SOURCE_COUNT,
        "causal_token_policy": ACTIVE_TOKEN_FORMULA,
        "d0_preservation": "EVERY_FROZEN_D0_ALARM_IS_A_D2_V2_ALARM",
        "single_source_fallback": False,
        "new_fixed_temporal_window": None,
        "d0_score_dependency": False,
        "label_aware_fusion": False,
        "metric_identities": {
            "attack_event_recall": ATTACK_EVENT_RECALL_FORMULA,
            "normal_far": NORMAL_FAR_FORMULA,
            "d0_missed_attack_recovery": D0_MISSED_ATTACK_RECOVERY_FORMULA,
            "incremental_attack_recall": INCREMENTAL_ATTACK_RECALL_FORMULA,
            "added_normal_recovery_far": ADDED_NORMAL_RECOVERY_FAR_FORMULA,
            "incremental_normal_far": INCREMENTAL_NORMAL_FAR_FORMULA,
        },
        "observed_test1_event_gaps_encoded": False,
        "d2_v2_execution_authorized": False,
        "test2_authorized": False,
        "outer_authorized": False,
    }
    return {**payload, "config_hash": stable_hash_v1(payload)}


def validate_d2_v2_config_v1(document: Mapping[str, Any]) -> str:
    if type(document) is not dict or document != canonical_config_document_v1():
        raise D2V2DesignError("D2_V2_CONFIG_REPLAY_REJECTED")
    payload = dict(document)
    observed = payload.pop("config_hash", None)
    if observed != stable_hash_v1(payload):
        raise D2V2DesignError("D2_V2_CONFIG_SELF_HASH_REJECTED")
    return str(observed)


def build_synthetic_causal_tokens_v1(
    rule_alarm_records: tuple[D2V2SyntheticRuleAlarmV1, ...],
    horizon_bindings: tuple[tuple[str, int], ...],
    physical_row_count: int,
) -> tuple[D2V2SyntheticEvidenceTokenV1, ...]:
    """Build causal tokens for synthetic contract tests only."""

    if type(rule_alarm_records) is not tuple or type(horizon_bindings) is not tuple:
        raise D2V2DesignError("D2_V2_SYNTHETIC_INPUT_TYPE_REJECTED")
    count = _strict_int(physical_row_count, "physical_row_count", minimum=1)
    horizon_map: dict[str, int] = {}
    for binding, horizon in horizon_bindings:
        key = _sha(binding, "relation_binding")
        value = _strict_int(horizon, "native_horizon", minimum=1)
        if key in horizon_map:
            raise D2V2DesignError("D2_V2_AMBIGUOUS_SYNTHETIC_HORIZON_REJECTED")
        horizon_map[key] = value
    tokens: list[D2V2SyntheticEvidenceTokenV1] = []
    for record in rule_alarm_records:
        if type(record) is not D2V2SyntheticRuleAlarmV1:
            raise D2V2DesignError("D2_V2_SYNTHETIC_RULE_ALARM_TYPE_REJECTED")
        if record.decision_physical_row_index >= count:
            raise D2V2DesignError("D2_V2_SYNTHETIC_DECISION_INDEX_REJECTED")
        if not record.alarm_emitted:
            continue
        horizon = horizon_map.get(record.relation_binding_hash)
        if horizon is None:
            raise D2V2DesignError("D2_V2_MISSING_SYNTHETIC_HORIZON_REJECTED")
        start = record.decision_physical_row_index
        expiry = min(start + horizon, count - 1)
        tokens.append(
            D2V2SyntheticEvidenceTokenV1(
                record.relation_binding_hash,
                record.source_variable_identity,
                start,
                expiry,
            )
        )
    return tuple(tokens)


def fuse_synthetic_native_horizon_timeline_v1(
    d0_alarm_booleans: tuple[bool, ...],
    tokens: tuple[D2V2SyntheticEvidenceTokenV1, ...],
) -> tuple[D2V2SyntheticCombinedDecisionV1, ...]:
    """Apply the frozen V2 policy to synthetic tokens only."""

    if type(d0_alarm_booleans) is not tuple or type(tokens) is not tuple:
        raise D2V2DesignError("D2_V2_SYNTHETIC_TIMELINE_TYPE_REJECTED")
    d0_values = tuple(_strict_bool(value, "d0_alarm") for value in d0_alarm_booleans)
    result: list[D2V2SyntheticCombinedDecisionV1] = []
    for index, d0_alarm in enumerate(d0_values):
        active_sources = tuple(
            sorted(
                {
                    token.source_variable_identity
                    for token in tokens
                    if token.start_physical_row_index <= index <= token.expiry_physical_row_index
                }
            )
        )
        corroborated = len(active_sources) >= REQUIRED_DISTINCT_SOURCE_COUNT
        if not d0_alarm and not corroborated:
            alarm, trigger = False, "NONE"
        elif d0_alarm and not corroborated:
            alarm, trigger = True, "D0_ONLY"
        elif not d0_alarm and corroborated:
            alarm, trigger = True, "RULE_RECOVERY_NATIVE_HORIZON"
        else:
            alarm, trigger = True, "D0_AND_RULE_CORROBORATION_NATIVE_HORIZON"
        result.append(D2V2SyntheticCombinedDecisionV1(index, alarm, trigger, active_sources))
    return tuple(result)


__all__ = [
    "D2V2CorroborationPolicyV1",
    "D2V2DesignAuthorityV1",
    "D2V2DesignError",
    "D2V2EvidenceTokenPolicyV1",
    "D2V2FuturePredictionContractV1",
    "D2V2FusionPolicyV1",
    "D2V2InputAuthorityV1",
    "D2V2MetricPolicyV1",
    "D2V2NativeHorizonAuthorityV1",
    "D2V2NativeTemporalHorizonMapV1",
    "D2V2SyntheticCombinedDecisionV1",
    "D2V2SyntheticEvidenceTokenV1",
    "D2V2SyntheticRuleAlarmV1",
    "D2_V2_DESIGN_HASH",
    "D2_V2_NATIVE_HORIZON_MAP_HASH",
    "FROZEN_NATIVE_HORIZON_BINDINGS",
    "build_d2_v2_design_authority_v1",
    "build_synthetic_causal_tokens_v1",
    "canonical_config_document_v1",
    "fuse_synthetic_native_horizon_timeline_v1",
    "native_horizon_map_document_v1",
    "resolve_native_horizon_map_from_frozen_authorities_v1",
    "validate_d2_v2_config_v1",
    "validate_d2_v2_design_authority_v1",
    "validate_d2_v2_design_document_v1",
    "validate_native_horizon_map_document_v1",
]
