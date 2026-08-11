"""TASK-039D0 arm-blind normal relation-profiling protocol.

This module contains immutable protocol records and pure synthetic helpers.  It
never opens a dataset.  Real HAI access remains a later TASK-039D1 concern and
is restricted by :class:`TASK039DDataAccessPolicyV1`.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, ClassVar, Mapping, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    freeze_json,
    reject_unknown_fields,
    require_finite,
    require_sha256,
    stable_hash_v1,
    thaw_json,
)
from paperworks.v6.continuous_step_protocol_v1 import (
    SustainedStepEventV1,
    calibration_confirmation_gate_v1,
    classify_event_isolation_v1,
    extract_sustained_step_events_v1,
    fit_support_gate_v1,
)


TASK039C_INTEGRATION_COMMIT = "9ac4578603b81385dc9592cd5db5076d83a3fb66"
DATASET_MANIFEST_HASH = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
BR1_PROTOCOL_BUNDLE_HASH = "5e57e1103b95d8cb24bf55f9ff85a989773dbe05816479dc79c493de044a7bbd"
CANDIDATE_COHORT_HASH = "6d488da608c2804e8cf3a183c4904403eb9904ad858c85beb34b48cb8bd79254"
CANDIDATE_IDENTITY_LIST_HASH = "b02304acef7f83c393b73563e486a80fcf32f3ec1997d65051493fe8dbef186c"
C0_PAIR_UNIVERSE_HASH = "fc072d3e18ce4623972c2cb64f6266727092ecae03fdb0f0dd929d705e1d8557"
SOURCE_IDENTITY_HASH = "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234"
TARGET_IDENTITY_HASH = "063037980aae4f0eaf45fbebb59f2aa0a924fbad583f3818107a793dfe7248e7"
RELATION_FAMILY = "continuous_step_delayed_response_v1"
PROCESS_ID = "P1"
PROCESS_NAME = "Boiler"
FIT_FILES = ("hai-train1.csv", "hai-train2.csv")
CALIBRATION_FILE = "hai-train3.csv"
NORMAL_GUARD_FILE = "hai-train4.csv"
HORIZONS = (1, 5, 10, 30, 60)
SOURCE_ROLES = ("control_command", "actuator_state", "actuator_feedback")

FROZEN_SOURCES = (
    "P1_FCV01D", "P1_FCV01Z", "P1_FCV02D", "P1_FCV02Z",
    "P1_FCV03D", "P1_FCV03Z", "P1_LCV01D", "P1_LCV01Z",
    "P1_PCV01D", "P1_PCV01Z", "P1_PCV02Z", "P1_PP04",
)
FROZEN_TARGETS = (
    "P1_FT01", "P1_FT01Z", "P1_FT02", "P1_FT02Z", "P1_FT03", "P1_FT03Z",
    "P1_LIT01", "P1_PIT01", "P1_PIT02", "P1_TIT01", "P1_TIT02", "P1_TIT03",
)
FROZEN_SOURCE_ROLES = {
    "P1_FCV01D": "control_command", "P1_FCV01Z": "actuator_feedback",
    "P1_FCV02D": "control_command", "P1_FCV02Z": "actuator_feedback",
    "P1_FCV03D": "control_command", "P1_FCV03Z": "actuator_feedback",
    "P1_LCV01D": "control_command", "P1_LCV01Z": "actuator_feedback",
    "P1_PCV01D": "control_command", "P1_PCV01Z": "actuator_feedback",
    "P1_PCV02Z": "actuator_feedback", "P1_PP04": "actuator_state",
}

ARM_EVIDENCE_FIELDS = frozenset({
    "origin_arms", "origin_arm_count", "overlap_category", "META", "STAT", "GDN",
    "meta_rank", "meta_tier", "stat_score", "stat_correlation", "stat_horizon",
    "gdn_rank", "gdn_similarity", "gdn_frequency", "rank", "evidence_tier",
    "selected_horizon_seconds", "r_train1", "r_train2", "stability_strength",
    "edge_selection_frequency", "median_upstream_graph_similarity",
})
BR2_PAIR_RESULT_NAMES = frozenset({
    "fit_supported_pairs", "confirmed_pairs", "selected_horizons", "selected_directions",
    "pair_consistencies", "pair_effect_ratios", "source_numeric_parameters",
    "target_numeric_parameters", "private_relation_ledger",
})


class RelationProfilingProtocolError(V6FoundationError):
    """Raised when the frozen TASK-039D0 protocol boundary is violated."""


@dataclass(frozen=True)
class _FrozenProtocolArtifact:
    """Immutable, closed-field, deterministic protocol artifact."""

    payload: Mapping[str, Any]
    ARTIFACT_TYPE: ClassVar[str] = ""
    PAYLOAD_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        if not self.ARTIFACT_TYPE:
            raise RelationProfilingProtocolError("artifact type is missing")
        try:
            reject_unknown_fields(self.payload, self.PAYLOAD_FIELDS, self.ARTIFACT_TYPE)
        except V6FoundationError as exc:
            raise RelationProfilingProtocolError(str(exc)) from exc
        missing = sorted(self.PAYLOAD_FIELDS - set(self.payload))
        if missing:
            raise RelationProfilingProtocolError(
                f"{self.ARTIFACT_TYPE} missing fields: {', '.join(missing)}"
            )
        object.__setattr__(self, "payload", freeze_json(self.payload))
        self._validate()

    def _validate(self) -> None:
        """Enforce closed scientific and authority enums at the contract edge."""

        value = thaw_json(self.payload)
        kind = self.ARTIFACT_TYPE
        if kind == "relation_profiling_protocol_v1":
            if value["status"] != "protocol_freeze_only" or value["process"] != PROCESS_ID:
                raise RelationProfilingProtocolError("protocol scope/status is not frozen")
            if value["relation_family"] != RELATION_FAMILY or value["candidate_count"] != 47:
                raise RelationProfilingProtocolError("protocol identity is not frozen")
        elif kind == "profiling_identity_view_v1":
            candidates = value["candidates"]
            pairs = []
            for item in candidates:
                allowed = {"source", "target", "process", "relation_family", "candidate_cohort_hash"}
                if set(item) != allowed or set(item) & ARM_EVIDENCE_FIELDS:
                    raise RelationProfilingProtocolError("profiling identity contains arm evidence")
                if item["source"] not in FROZEN_SOURCES or item["target"] not in FROZEN_TARGETS:
                    raise RelationProfilingProtocolError("profiling identity is outside the P1 universe")
                if item["process"] != PROCESS_ID or item["relation_family"] != RELATION_FAMILY:
                    raise RelationProfilingProtocolError("profiling identity scope is not frozen")
                if item["candidate_cohort_hash"] != CANDIDATE_COHORT_HASH:
                    raise RelationProfilingProtocolError("profiling cohort hash is not frozen")
                pairs.append((item["source"], item["target"]))
            if value["candidate_count"] != 47 or len(pairs) != 47 or len(set(pairs)) != 47:
                raise RelationProfilingProtocolError("profiling view must bind 47 unique pairs")
        elif kind == "candidate_provenance_analysis_view_v1":
            if value["candidate_count"] != 47 or not value["join_allowed_after_outcomes_frozen"]:
                raise RelationProfilingProtocolError("provenance view boundary is not frozen")
            if value["join_key"] != ["source", "target"]:
                raise RelationProfilingProtocolError("provenance join key is not frozen")
        elif kind == "source_scale_policy_v1":
            if value["fit_files"] != list(FIT_FILES) or value["minimum_nontrivial_amplitudes"] != 20:
                raise RelationProfilingProtocolError("source scale fit scope is not frozen")
            if value["numeric_epsilon"] != 1e-12 or value["train3_influences_parameters"]:
                raise RelationProfilingProtocolError("source scale authority is invalid")
        elif kind == "source_step_profiling_policy_v1":
            expected_records = [{"source": source, "semantic_role": FROZEN_SOURCE_ROLES[source]} for source in FROZEN_SOURCES]
            if value["source_context"] != list(FROZEN_SOURCES) or value["source_records"] != expected_records:
                raise RelationProfilingProtocolError("all-12-source context/roles are not frozen")
            if value["refractory_seconds"] != 10 or value["isolation_radius_seconds"] != 2:
                raise RelationProfilingProtocolError("event clustering/isolation is not frozen")
            if not value["file_local_only"] or value["cross_file_windows_allowed"] or value["directions_pooled"]:
                raise RelationProfilingProtocolError("event file/direction boundary is invalid")
        elif kind == "target_response_profiling_policy_v1":
            if value["target_context"] != list(FROZEN_TARGETS) or value["target_role"] != "continuous_process_sensor":
                raise RelationProfilingProtocolError("all-12-target context is not frozen")
            if value["response_horizons_seconds"] != list(HORIZONS):
                raise RelationProfilingProtocolError("response horizons are not frozen")
            if value["pair_specific_scale"] or value["arm_specific_scale"] or value["train3_influences_scale"]:
                raise RelationProfilingProtocolError("target scale scope is invalid")
        elif kind == "directional_relation_selection_policy_v1":
            if value["source_step_directions"] != ["step_up", "step_down"]:
                raise RelationProfilingProtocolError("source direction enum is not closed")
            if value["target_response_directions"] != ["increase", "decrease"]:
                raise RelationProfilingProtocolError("target direction enum is not closed")
            if value["equality_passes"] or value["lower_ranked_fallback_allowed"]:
                raise RelationProfilingProtocolError("strict agreement/no-fallback is not frozen")
        elif kind == "relation_fit_gate_policy_v1":
            expected = (20, 5, 5, 0.70, 0.60, 0.60, 2.0)
            observed = (value["total_usable_minimum"], value["train1_usable_minimum"],
                        value["train2_usable_minimum"], value["pooled_consistency_minimum"],
                        value["train1_consistency_minimum"], value["train2_consistency_minimum"],
                        value["robust_effect_ratio_minimum"])
            if observed != expected or value["arm_specific_gate_allowed"]:
                raise RelationProfilingProtocolError("fit gate is not frozen")
        elif kind == "directional_relation_identity_v1":
            if value["source"] not in FROZEN_SOURCES or value["target"] not in FROZEN_TARGETS:
                raise RelationProfilingProtocolError("directional identity is outside the universe")
            if value["source_step_direction"] not in {"step_up", "step_down"}:
                raise RelationProfilingProtocolError("source step direction is invalid")
            if value["target_response_direction"] not in {"increase", "decrease"}:
                raise RelationProfilingProtocolError("target response direction is invalid")
            if value["selected_horizon_is_identity"] or value["relation_family"] != RELATION_FAMILY:
                raise RelationProfilingProtocolError("directional identity semantics are not frozen")
        elif kind == "relation_confirmation_policy_v1":
            if value["outcomes"] != ["calibration_confirmed", "calibration_conflict"]:
                raise RelationProfilingProtocolError("confirmation outcomes are not closed")
            if value["execution_authorized"] or value["retuning_allowed"]:
                raise RelationProfilingProtocolError("D2 execution/retuning is prohibited")
        elif kind == "relation_profiling_outcome_policy_v1":
            if value["pair_states"] != ["fit_supported_pair", "fit_unsupported_pair"]:
                raise RelationProfilingProtocolError("pair outcome enum is not closed")
        elif kind == "numeric_evidence_authority_policy_v1":
            if value["d1_parameter_class"] != "normal_relation_profile_fit_derived":
                raise RelationProfilingProtocolError("numeric parameter class is not frozen")
            if value["evidence_authority"] != "construction_evidence" or value["runtime_authority"] != "not_granted":
                raise RelationProfilingProtocolError("numeric authority boundary is invalid")
        elif kind == "candidate_method_comparison_policy_v1":
            if value["primary_k"] != 20 or value["arms"] != ["META", "STAT", "GDN"]:
                raise RelationProfilingProtocolError("method comparison budget/arms are not frozen")
            if value["precision_term_allowed"] or value["winner_selection_d0"] or value["winner_selection_d1"]:
                raise RelationProfilingProtocolError("method comparison claim boundary is invalid")
            if value["d2_gate_tuning_from_d1_allowed"] or not value["shared_pair_outcome_invariant"]:
                raise RelationProfilingProtocolError("method comparison invariant is invalid")
        elif kind == "task039d_data_access_policy_v1":
            if value["d0_feature_values_authorized"] or value["d2_real_confirmation_authorized"]:
                raise RelationProfilingProtocolError("D0/D2 data authority is prohibited")
            if value["normal_guard_access_authorized"] or value["br2_pair_results_authorized"]:
                raise RelationProfilingProtocolError("guard/BR2 authority is prohibited")
            if value["candidate_arm_evidence_visible_to_profiler"]:
                raise RelationProfilingProtocolError("profiler must remain arm blind")
        elif kind == "task039d1_authorization_v1":
            if not value["train1_authorized"] or not value["train2_authorized"]:
                raise RelationProfilingProtocolError("D1 fit files must be authorized")
            forbidden = ("train3_authorized", "train4_authorized", "test_labels_attacks_authorized",
                         "br2_pair_result_access", "candidate_arm_evidence_visible_to_profiler",
                         "rule_v2_authorized", "agent_authorized", "detector_runtime_authorized")
            if any(value[field] for field in forbidden):
                raise RelationProfilingProtocolError("D1 authorization exceeds its boundary")
        elif kind == "task039d_protocol_bundle_v1":
            if value["status"] != "passed_task039d0_relation_profiling_protocol_freeze":
                raise RelationProfilingProtocolError("D0 bundle status is invalid")
            if value["unresolved_fields"] or value["real_hai_feature_access"]:
                raise RelationProfilingProtocolError("D0 bundle cannot contain unresolved/data access")
            if value["d2_execution_authorized"] or value["rule_v2_authorized"]:
                raise RelationProfilingProtocolError("D0 bundle exceeds its authority")

    def _content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": self.ARTIFACT_TYPE,
            **thaw_json(self.payload),
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        result = self._content_dict()
        result["artifact_hash"] = self.artifact_hash
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "_FrozenProtocolArtifact":
        allowed = cls.PAYLOAD_FIELDS | {"schema_version", "artifact_type", "artifact_hash"}
        reject_unknown_fields(data, allowed, cls.ARTIFACT_TYPE)
        if data.get("schema_version") != V6_FOUNDATION_SCHEMA_VERSION:
            raise RelationProfilingProtocolError("schema_version must be 1.0.0")
        if data.get("artifact_type") != cls.ARTIFACT_TYPE:
            raise RelationProfilingProtocolError("artifact_type does not match")
        result = cls({key: data[key] for key in cls.PAYLOAD_FIELDS})
        if data.get("artifact_hash") not in {None, result.artifact_hash}:
            raise RelationProfilingProtocolError("artifact_hash does not match content")
        return result


def _artifact_class(name: str, artifact_type: str, fields: Sequence[str]) -> type[_FrozenProtocolArtifact]:
    return type(
        name,
        (_FrozenProtocolArtifact,),
        {"ARTIFACT_TYPE": artifact_type, "PAYLOAD_FIELDS": frozenset(fields)},
    )


RelationProfilingProtocolV1 = _artifact_class(
    "RelationProfilingProtocolV1", "relation_profiling_protocol_v1",
    ("task_id", "status", "dataset_manifest_hash", "process", "process_name",
     "relation_family", "br1_protocol_bundle_hash", "task039c_commit", "cohort_hash",
     "identity_list_hash", "candidate_count", "original_pair_universe_count",
     "pair_universe_hash", "source_identity_hash", "target_identity_hash",
     "execution_sequence", "claim_boundary"),
)
ProfilingIdentityViewPolicyV1 = _artifact_class(
    "ProfilingIdentityViewPolicyV1", "profiling_identity_view_policy_v1",
    ("allowed_fields", "prohibited_fields", "profiler_input_artifact_type",
     "provenance_join_timing", "invariance_requirement", "arm_specific_policy_allowed"),
)
ProfilingIdentityViewV1 = _artifact_class(
    "ProfilingIdentityViewV1", "profiling_identity_view_v1",
    ("cohort_hash", "identity_list_hash", "candidate_count", "process", "relation_family", "candidates"),
)
CandidateProvenanceAnalysisViewV1 = _artifact_class(
    "CandidateProvenanceAnalysisViewV1", "candidate_provenance_analysis_view_v1",
    ("cohort_hash", "candidate_count", "join_key", "join_allowed_after_outcomes_frozen", "candidates"),
)
SourceScalePolicyV1 = _artifact_class(
    "SourceScalePolicyV1", "source_scale_policy_v1",
    ("fit_files", "difference_scope", "pooling_order", "noise_scale_formula", "numeric_epsilon",
     "amplitude_pre_window_seconds", "amplitude_post_window_seconds", "amplitude_formula",
     "nontrivial_rule", "minimum_nontrivial_amplitudes", "q75_method", "step_threshold_formula",
     "stability_tolerance_formula", "train3_influences_parameters", "parameter_class"),
)
SourceStepProfilingPolicyV1 = _artifact_class(
    "SourceStepProfilingPolicyV1", "source_step_profiling_policy_v1",
    ("source_context", "source_records", "source_count", "source_roles", "event_pre_window_seconds",
     "event_post_window_seconds", "event_threshold_rule", "directions", "stability_fraction_minimum",
     "refractory_seconds", "refractory_linkage", "cluster_retention", "exact_tie_break",
     "isolation_radius_seconds", "isolation_boundary_inclusive", "isolation_source_count",
     "file_local_only", "cross_file_windows_allowed", "directions_pooled"),
)
TargetResponseProfilingPolicyV1 = _artifact_class(
    "TargetResponseProfilingPolicyV1", "target_response_profiling_policy_v1",
    ("target_context", "target_role", "target_count", "fit_files", "noise_scale_formula", "noise_scale_scope",
     "pair_specific_scale", "arm_specific_scale", "baseline_window_seconds", "baseline_formula",
     "response_horizons_seconds", "response_window_seconds", "response_formula",
     "increase_rule", "decrease_rule", "neutral_interval", "right_censor_incomplete",
     "impute_censored", "train3_influences_scale"),
)
DirectionalRelationSelectionPolicyV1 = _artifact_class(
    "DirectionalRelationSelectionPolicyV1", "directional_relation_selection_policy_v1",
    ("source_step_directions", "target_response_directions", "horizons_seconds",
     "directions_evaluated_independently", "per_file_statistics", "pooled_statistics",
     "strict_direction_agreement", "equality_passes", "ranking_order",
     "selection_before_fit_gate", "lower_ranked_fallback_allowed", "no_eligible_status"),
)
RelationFitGatePolicyV1 = _artifact_class(
    "RelationFitGatePolicyV1", "relation_fit_gate_policy_v1",
    ("total_usable_minimum", "train1_usable_minimum", "train2_usable_minimum",
     "pooled_consistency_minimum", "train1_consistency_minimum", "train2_consistency_minimum",
     "robust_effect_ratio_minimum", "strict_direction_agreement_required", "all_conditions_required",
     "failure_status", "arm_specific_gate_allowed"),
)
RelationConfirmationPolicyV1 = _artifact_class(
    "RelationConfirmationPolicyV1", "relation_confirmation_policy_v1",
    ("planned_task", "execution_authorized", "file", "input_scope", "reused_fit_fields",
     "alternative_horizon_search", "opposite_direction_search", "usable_minimum",
     "source_direction_unchanged", "selected_consistency_strictly_greater_than_opposite",
     "directional_consistency_minimum", "robust_effect_ratio_minimum",
     "retuning_allowed", "all_conditions_required", "outcomes"),
)
DirectionalRelationIdentityV1 = _artifact_class(
    "DirectionalRelationIdentityV1", "directional_relation_identity_v1",
    ("source", "source_step_direction", "target", "target_response_direction",
     "selected_horizon_is_identity", "relation_family"),
)
RelationProfilingOutcomePolicyV1 = _artifact_class(
    "RelationProfilingOutcomePolicyV1", "relation_profiling_outcome_policy_v1",
    ("candidate_pair_count", "directional_opportunity_maximum", "directional_records_preserved",
     "directional_failure_reasons_preserved", "pair_fit_supported_definition",
     "pair_states", "d1_ledgers", "public_exclusions"),
)
CandidateMethodComparisonPolicyV1 = _artifact_class(
    "CandidateMethodComparisonPolicyV1", "candidate_method_comparison_policy_v1",
    ("primary_k", "arms", "profile_once_per_unique_pair", "join_provenance_after_outcomes",
     "metrics", "coverage_denominator_sources", "coverage_denominator_targets",
     "confirmed_overlap_reporting", "shared_pair_outcome_invariant", "precision_term_allowed",
     "winner_selection_d0", "winner_selection_d1", "d2_gate_tuning_from_d1_allowed"),
)
NumericEvidenceAuthorityPolicyV1 = _artifact_class(
    "NumericEvidenceAuthorityPolicyV1", "numeric_evidence_authority_policy_v1",
    ("d1_parameter_class", "d1_construction_eligibility_requires_d2",
     "confirmed_relation_primitive_is_rule", "confirmed_relation_numeric_fields",
     "evidence_authority", "runtime_authority", "llm_numeric_invention_required",
     "rule_v2_authorized", "verifier_authority", "runtime_authority_granted"),
)
TASK039DDataAccessPolicyV1 = _artifact_class(
    "TASK039DDataAccessPolicyV1", "task039d_data_access_policy_v1",
    ("d0_feature_values_authorized", "d1_fit_files", "d1_process", "d1_real_fit_profiling_authorized",
     "d2_confirmation_file", "d2_real_confirmation_authorized", "normal_guard_file",
     "normal_guard_access_authorized", "prohibited_files", "labels_authorized", "attacks_authorized",
     "p2_p3_p4_values_authorized", "br2_pair_results_authorized",
     "candidate_arm_evidence_visible_to_profiler", "private_ledger_access_authorized"),
)
TASK039D1AuthorizationV1 = _artifact_class(
    "TASK039D1AuthorizationV1", "task039d1_authorization_v1",
    ("d0_protocol_hash", "candidate_cohort_hash", "candidate_identity_list_hash", "candidate_count",
     "process", "relation_family", "train1_authorized", "train2_authorized", "train3_authorized",
     "train4_authorized", "test_labels_attacks_authorized", "br2_pair_result_access",
     "candidate_arm_evidence_visible_to_profiler", "real_fit_profiling_authorized",
     "rule_v2_authorized", "agent_authorized", "detector_runtime_authorized"),
)
TASK039DProtocolBundleV1 = _artifact_class(
    "TASK039DProtocolBundleV1", "task039d_protocol_bundle_v1",
    ("task_id", "status", "authoritative_main_commit", "config_hash", "protocol",
     "identity_view_policy", "profiling_identity_view_hash", "provenance_analysis_view_hash",
     "source_scale_policy", "event_policy", "target_response_policy", "direction_selection_policy",
     "fit_gate_policy", "confirmation_policy", "outcome_policy", "method_comparison_policy",
     "numeric_evidence_policy", "data_access_policy_hash", "d1_authorization_hash",
     "unresolved_fields", "real_hai_feature_access", "d2_execution_authorized",
     "rule_v2_authorized", "artifact_claim"),
)
TASK039D0ProtocolConfigV1 = _artifact_class(
    "TASK039D0ProtocolConfigV1", "task039d0_relation_profiling_protocol_config",
    ("authoritative_task039c_tip", "lineage", "split_roles", "source_context", "target_context",
     "protocol_components", "sequential_authority", "comparison_policy", "public_private_boundary"),
)

ARTIFACT_CLASSES: tuple[type[_FrozenProtocolArtifact], ...] = (
    RelationProfilingProtocolV1, ProfilingIdentityViewPolicyV1, ProfilingIdentityViewV1,
    CandidateProvenanceAnalysisViewV1, SourceScalePolicyV1, SourceStepProfilingPolicyV1,
    TargetResponseProfilingPolicyV1, DirectionalRelationSelectionPolicyV1,
    RelationFitGatePolicyV1, RelationConfirmationPolicyV1, DirectionalRelationIdentityV1,
    RelationProfilingOutcomePolicyV1, CandidateMethodComparisonPolicyV1,
    NumericEvidenceAuthorityPolicyV1, TASK039DDataAccessPolicyV1,
    TASK039D1AuthorizationV1, TASK039DProtocolBundleV1, TASK039D0ProtocolConfigV1,
)
ARTIFACT_CLASS_BY_TYPE = {item.ARTIFACT_TYPE: item for item in ARTIFACT_CLASSES}


def verify_self_hash_v1(document: Mapping[str, Any]) -> None:
    supplied = document.get("artifact_hash")
    if not isinstance(supplied, str):
        raise RelationProfilingProtocolError("artifact_hash is required")
    content = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(content) != supplied:
        raise RelationProfilingProtocolError("artifact_hash does not match content")


def assert_arm_blind_identity_record_v1(record: Mapping[str, Any]) -> None:
    allowed = frozenset({"source", "target", "process", "relation_family", "candidate_cohort_hash"})
    reject_unknown_fields(record, allowed, "profiling_identity_record_v1")
    if set(record) != allowed:
        raise RelationProfilingProtocolError("profiling identity record is incomplete")
    if set(record) & ARM_EVIDENCE_FIELDS:
        raise RelationProfilingProtocolError("candidate-arm evidence is prohibited")
    if record["process"] != PROCESS_ID or record["relation_family"] != RELATION_FAMILY:
        raise RelationProfilingProtocolError("profiling identity is outside the frozen scope")
    if record["candidate_cohort_hash"] != CANDIDATE_COHORT_HASH:
        raise RelationProfilingProtocolError("candidate cohort hash is not frozen")


def profiling_identity_from_candidate_v1(candidate: Mapping[str, Any]) -> dict[str, str]:
    """Project public cohort provenance into the only scientific profiler view."""

    source, target = str(candidate["source"]), str(candidate["target"])
    result = {
        "source": source,
        "target": target,
        "process": PROCESS_ID,
        "relation_family": RELATION_FAMILY,
        "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
    }
    assert_arm_blind_identity_record_v1(result)
    return result


def _finite_files(files: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    if len(files) != 2:
        raise RelationProfilingProtocolError("fit scale requires train1 and train2")
    result: list[tuple[float, ...]] = []
    for values in files:
        sequence = tuple(float(value) for value in values)
        if len(sequence) < 2 or any(not math.isfinite(value) for value in sequence):
            raise RelationProfilingProtocolError("fit files require finite sequences")
        result.append(sequence)
    return tuple(result)


def _mad(values: Sequence[float]) -> float:
    center = statistics.median(values)
    return float(statistics.median(abs(item - center) for item in values))


def q75_linear_v1(values: Sequence[float]) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise RelationProfilingProtocolError("Q75 requires at least one value")
    position = 0.75 * (len(ordered) - 1)
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def multi_file_robust_scale_v1(files: Sequence[Sequence[float]]) -> float:
    """Compute differences file-locally, then pool them for the frozen MAD scale."""

    sequences = _finite_files(files)
    differences = [
        sequence[index] - sequence[index - 1]
        for sequence in sequences
        for index in range(1, len(sequence))
    ]
    return max(1.4826 * _mad(differences), 1e-12)


def derive_multi_file_source_parameters_v1(
    files: Sequence[Sequence[float]],
) -> dict[str, int | float | str | None]:
    """Derive D1 source parameters without cross-file differences or windows."""

    sequences = _finite_files(files)
    noise = multi_file_robust_scale_v1(sequences)
    amplitudes: list[float] = []
    for sequence in sequences:
        for event_index in range(5, len(sequence) - 5 + 1):
            pre = float(statistics.median(sequence[event_index - 5:event_index]))
            post = float(statistics.median(sequence[event_index:event_index + 5]))
            amplitude = abs(post - pre)
            if amplitude > noise:
                amplitudes.append(amplitude)
    if len(amplitudes) < 20:
        return {
            "status": "insufficient_nontrivial_amplitudes",
            "source_noise_scale": noise,
            "nontrivial_amplitude_count": len(amplitudes),
            "source_step_threshold": None,
            "source_stability_tolerance": None,
        }
    threshold = max(5.0 * noise, q75_linear_v1(amplitudes))
    return {
        "status": "supported",
        "source_noise_scale": noise,
        "nontrivial_amplitude_count": len(amplitudes),
        "source_step_threshold": threshold,
        "source_stability_tolerance": max(3.0 * noise, 0.10 * threshold),
    }


def derive_multi_file_target_scale_v1(files: Sequence[Sequence[float]]) -> float:
    return multi_file_robust_scale_v1(files)


def extract_file_local_events_v1(
    files: Mapping[str, Sequence[float]], *, source_step_threshold: float,
    source_stability_tolerance: float,
) -> dict[str, tuple[SustainedStepEventV1, ...]]:
    if set(files) != set(FIT_FILES):
        raise RelationProfilingProtocolError("event extraction requires the two frozen fit files")
    return {
        name: extract_sustained_step_events_v1(
            values, source_step_threshold=source_step_threshold,
            source_stability_tolerance=source_stability_tolerance,
        )
        for name, values in files.items()
    }


def classify_all_source_isolation_v1(
    source_events: Mapping[str, Sequence[SustainedStepEventV1]],
) -> dict[str, tuple[tuple[SustainedStepEventV1, bool], ...]]:
    if set(source_events) != set(FROZEN_SOURCES):
        raise RelationProfilingProtocolError("isolation requires all 12 frozen sources")
    return classify_event_isolation_v1(source_events, isolation_radius_seconds=2)


def rank_direction_horizon_v1(records: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Select one direction/horizon using the preregistered strict order."""

    eligible: list[Mapping[str, Any]] = []
    for record in records:
        required = {
            "target_direction", "horizon_seconds", "pooled_directional_consistency",
            "pooled_robust_effect_ratio", "train1_selected_consistency",
            "train1_opposite_consistency", "train2_selected_consistency",
            "train2_opposite_consistency",
        }
        reject_unknown_fields(record, frozenset(required), "direction_horizon_record_v1")
        if set(record) != required:
            raise RelationProfilingProtocolError("direction/horizon record is incomplete")
        if record["target_direction"] not in {"increase", "decrease"}:
            raise RelationProfilingProtocolError("target direction is invalid")
        if int(record["horizon_seconds"]) not in HORIZONS:
            raise RelationProfilingProtocolError("horizon is invalid")
        for name in required - {"target_direction", "horizon_seconds"}:
            require_finite(record[name], name)
        if (
            float(record["train1_selected_consistency"]) > float(record["train1_opposite_consistency"])
            and float(record["train2_selected_consistency"]) > float(record["train2_opposite_consistency"])
        ):
            eligible.append(record)
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda item: (
            -float(item["pooled_directional_consistency"]),
            -float(item["pooled_robust_effect_ratio"]),
            int(item["horizon_seconds"]),
            str(item["target_direction"]),
        ),
    )


def selected_fit_gate_v1(selected: Mapping[str, Any]) -> bool:
    """Apply the fit gate only to the already selected record; no fallback exists."""

    return fit_support_gate_v1(
        total_isolated_events=int(selected["total_usable_responses"]),
        train1_isolated_events=int(selected["train1_usable_responses"]),
        train2_isolated_events=int(selected["train2_usable_responses"]),
        fit_directional_consistency=float(selected["pooled_directional_consistency"]),
        train1_directional_consistency=float(selected["train1_selected_consistency"]),
        train2_directional_consistency=float(selected["train2_selected_consistency"]),
        fit_robust_effect_ratio=float(selected["pooled_robust_effect_ratio"]),
        direction_agrees_across_files=(
            float(selected["train1_selected_consistency"]) > float(selected["train1_opposite_consistency"])
            and float(selected["train2_selected_consistency"]) > float(selected["train2_opposite_consistency"])
        ),
    )


def train3_confirmation_gate_v1(
    *, usable_responses: int, source_direction_unchanged: bool,
    selected_consistency: float, opposite_consistency: float,
    robust_effect_ratio: float, fit_parameters_reused_without_retuning: bool,
) -> bool:
    return calibration_confirmation_gate_v1(
        train3_isolated_events=usable_responses,
        source_direction_unchanged=source_direction_unchanged,
        target_direction_unchanged=selected_consistency > opposite_consistency,
        train3_directional_consistency=selected_consistency,
        train3_robust_effect_ratio=robust_effect_ratio,
        fit_parameters_reused_without_retuning=fit_parameters_reused_without_retuning,
    )


def authorize_value_access_v1(*, task_id: str, relative_file: str) -> None:
    """Fail closed for D0 and permit only D1's two frozen fit filenames."""

    if task_id == "TASK-039D0":
        raise RelationProfilingProtocolError("TASK-039D0 cannot access HAI feature values")
    if task_id != "TASK-039D1" or relative_file not in FIT_FILES:
        raise RelationProfilingProtocolError("file is outside TASK-039D1 authority")


def authorize_br2_reference_v1(*, purpose: str, artifact_name: str) -> None:
    if purpose != "lineage_hash_verification" or artifact_name in BR2_PAIR_RESULT_NAMES:
        raise RelationProfilingProtocolError("BR2 pair-result access is prohibited")


def _policy_instances() -> dict[str, _FrozenProtocolArtifact]:
    protocol = RelationProfilingProtocolV1({
        "task_id": "TASK-039D0", "status": "protocol_freeze_only",
        "dataset_manifest_hash": DATASET_MANIFEST_HASH, "process": PROCESS_ID,
        "process_name": PROCESS_NAME, "relation_family": RELATION_FAMILY,
        "br1_protocol_bundle_hash": BR1_PROTOCOL_BUNDLE_HASH,
        "task039c_commit": TASK039C_INTEGRATION_COMMIT, "cohort_hash": CANDIDATE_COHORT_HASH,
        "identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH, "candidate_count": 47,
        "original_pair_universe_count": 144, "pair_universe_hash": C0_PAIR_UNIVERSE_HASH,
        "source_identity_hash": SOURCE_IDENTITY_HASH, "target_identity_hash": TARGET_IDENTITY_HASH,
        "execution_sequence": ["TASK-039D0:protocol_only", "TASK-039D1:train1_train2_fit_only", "TASK-039D2:one_way_train3_confirmation", "later_rule_construction"],
        "claim_boundary": "common normal relation profiling and deterministic calibration protocol",
    })
    identity_policy = ProfilingIdentityViewPolicyV1({
        "allowed_fields": ["source", "target", "process", "relation_family", "candidate_cohort_hash"],
        "prohibited_fields": sorted(ARM_EVIDENCE_FIELDS),
        "profiler_input_artifact_type": "profiling_identity_view_v1",
        "provenance_join_timing": "after_profiling_outcomes_frozen",
        "invariance_requirement": "same pair -> same profiling result regardless of proposing arm",
        "arm_specific_policy_allowed": False,
    })
    source_scale = SourceScalePolicyV1({
        "fit_files": list(FIT_FILES), "difference_scope": "within_each_file_only",
        "pooling_order": "compute_file_local_differences_then_pool",
        "noise_scale_formula": "max(1.4826*MAD(within-file dx pooled across fit files),1e-12)",
        "numeric_epsilon": 1e-12, "amplitude_pre_window_seconds": 5,
        "amplitude_post_window_seconds": 5, "amplitude_formula": "abs(median(x[t:t+5])-median(x[t-5:t]))",
        "nontrivial_rule": "A>source_noise_scale", "minimum_nontrivial_amplitudes": 20,
        "q75_method": "linear_interpolation_position_0.75_times_n_minus_1",
        "step_threshold_formula": "max(5*source_noise_scale,Q75_linear(A_positive))",
        "stability_tolerance_formula": "max(3*source_noise_scale,0.10*source_step_threshold)",
        "train3_influences_parameters": False, "parameter_class": "normal_relation_profile_fit_derived",
    })
    event = SourceStepProfilingPolicyV1({
        "source_context": list(FROZEN_SOURCES),
        "source_records": [{"source": source, "semantic_role": FROZEN_SOURCE_ROLES[source]} for source in FROZEN_SOURCES],
        "source_count": 12, "source_roles": list(SOURCE_ROLES),
        "event_pre_window_seconds": 5, "event_post_window_seconds": 5,
        "event_threshold_rule": "abs(post_level-pre_level)>=source_step_threshold",
        "directions": ["step_up", "step_down"], "stability_fraction_minimum": 0.8,
        "refractory_seconds": 10, "refractory_linkage": "single_link_file_local",
        "cluster_retention": "largest_absolute_step_amplitude", "exact_tie_break": "earliest_event_index",
        "isolation_radius_seconds": 2, "isolation_boundary_inclusive": True,
        "isolation_source_count": 12, "file_local_only": True,
        "cross_file_windows_allowed": False, "directions_pooled": False,
    })
    target = TargetResponseProfilingPolicyV1({
        "target_context": list(FROZEN_TARGETS), "target_role": "continuous_process_sensor",
        "target_count": 12, "fit_files": list(FIT_FILES),
        "noise_scale_formula": "max(1.4826*MAD(target within-file dy pooled across fit files),1e-12)",
        "noise_scale_scope": "once_per_target_reused_across_candidates", "pair_specific_scale": False,
        "arm_specific_scale": False, "baseline_window_seconds": 5,
        "baseline_formula": "median(target[t-5:t])", "response_horizons_seconds": list(HORIZONS),
        "response_window_seconds": 3, "response_formula": "median(target[t+h:t+h+3])-baseline",
        "increase_rule": "response>target_noise_scale", "decrease_rule": "response<-target_noise_scale",
        "neutral_interval": "[-target_noise_scale,+target_noise_scale]",
        "right_censor_incomplete": True, "impute_censored": False, "train3_influences_scale": False,
    })
    selection = DirectionalRelationSelectionPolicyV1({
        "source_step_directions": ["step_up", "step_down"],
        "target_response_directions": ["increase", "decrease"], "horizons_seconds": list(HORIZONS),
        "directions_evaluated_independently": True,
        "per_file_statistics": ["usable_response_count", "right_censored_count", "directional_match_count", "directional_consistency", "opposite_direction_consistency"],
        "pooled_statistics": ["directional_consistency", "median_target_response", "robust_effect_ratio"],
        "strict_direction_agreement": "selected_train1>opposite_train1 AND selected_train2>opposite_train2",
        "equality_passes": False,
        "ranking_order": ["pooled_directional_consistency_desc", "pooled_robust_effect_ratio_desc", "horizon_asc", "target_direction_lexical"],
        "selection_before_fit_gate": True, "lower_ranked_fallback_allowed": False,
        "no_eligible_status": "direction_unstable",
    })
    fit = RelationFitGatePolicyV1({
        "total_usable_minimum": 20, "train1_usable_minimum": 5, "train2_usable_minimum": 5,
        "pooled_consistency_minimum": 0.70, "train1_consistency_minimum": 0.60,
        "train2_consistency_minimum": 0.60, "robust_effect_ratio_minimum": 2.0,
        "strict_direction_agreement_required": True, "all_conditions_required": True,
        "failure_status": "fit_unsupported", "arm_specific_gate_allowed": False,
    })
    confirmation = RelationConfirmationPolicyV1({
        "planned_task": "TASK-039D2", "execution_authorized": False, "file": CALIBRATION_FILE,
        "input_scope": "D1_fit_supported_directional_relations_only",
        "reused_fit_fields": ["source_noise_scale", "source_step_threshold", "source_stability_tolerance", "target_noise_scale", "source_step_direction", "target_response_direction", "selected_horizon", "pre_post_windows", "response_windows", "refractory_period", "isolation_radius"],
        "alternative_horizon_search": False, "opposite_direction_search": False, "usable_minimum": 5,
        "source_direction_unchanged": True, "selected_consistency_strictly_greater_than_opposite": True,
        "directional_consistency_minimum": 0.60, "robust_effect_ratio_minimum": 1.0,
        "retuning_allowed": False, "all_conditions_required": True,
        "outcomes": ["calibration_confirmed", "calibration_conflict"],
    })
    outcome = RelationProfilingOutcomePolicyV1({
        "candidate_pair_count": 47, "directional_opportunity_maximum": 94,
        "directional_records_preserved": True, "directional_failure_reasons_preserved": True,
        "pair_fit_supported_definition": "at_least_one_source_step_direction_passes_D1_fit_gate",
        "pair_states": ["fit_supported_pair", "fit_unsupported_pair"],
        "d1_ledgers": ["shared_12_source_parameter_ledger", "shared_12_target_parameter_ledger", "directional_relation_fit_ledger", "47_pair_fit_summary"],
        "public_exclusions": ["raw_windows", "event_timestamps", "absolute_paths"],
    })
    comparison = CandidateMethodComparisonPolicyV1({
        "primary_k": 20, "arms": ["META", "STAT", "GDN"], "profile_once_per_unique_pair": True,
        "join_provenance_after_outcomes": True,
        "metrics": {
            "pair_fit_support_yield": "arm_top20_pairs_with_at_least_one_fit_supported_directional_relation/20",
            "confirmed_relation_yield_at_20": "arm_top20_pairs_with_at_least_one_D2_confirmed_directional_relation/20",
            "pair_fit_to_confirmation_transfer": "confirmed_pairs/fit_supported_pairs_or_0_when_denominator_0",
            "directional_fit_count": "fit_supported_directional_relations_among_arm_top20_range_0_to_40",
            "directional_confirmation_count": "D2_confirmed_directional_relations_among_arm_top20_range_0_to_40",
            "directional_transfer": "confirmed_directional_relations/fit_supported_directional_relations_or_0_when_denominator_0",
            "distinct_confirmed_source_coverage_at_20": "distinct_sources_with_confirmed_relation_count_and_rate_over_12",
            "distinct_confirmed_target_coverage_at_20": "distinct_targets_with_confirmed_relation_count_and_rate_over_12",
            "cross_arm_confirmed_pair_overlap": "confirmed_pairs_unique_by_arm_shared_by_two_and_shared_by_all_applicable_arms",
        },
        "coverage_denominator_sources": 12, "coverage_denominator_targets": 12,
        "confirmed_overlap_reporting": ["unique_META", "unique_STAT", "unique_GDN", "shared_two_arms", "shared_all_applicable_arms"],
        "shared_pair_outcome_invariant": True, "precision_term_allowed": False,
        "winner_selection_d0": False, "winner_selection_d1": False,
        "d2_gate_tuning_from_d1_allowed": False,
    })
    numeric = NumericEvidenceAuthorityPolicyV1({
        "d1_parameter_class": "normal_relation_profile_fit_derived",
        "d1_construction_eligibility_requires_d2": True, "confirmed_relation_primitive_is_rule": False,
        "confirmed_relation_numeric_fields": ["source_step_threshold", "source_stability_tolerance", "source_pre_window", "source_post_window", "minimum_source_stability_fraction", "source_refractory", "cross_source_isolation_radius", "selected_delay_horizon", "target_baseline_window", "target_response_window", "target_noise_scale", "source_direction", "target_direction"],
        "evidence_authority": "construction_evidence", "runtime_authority": "not_granted",
        "llm_numeric_invention_required": False, "rule_v2_authorized": False,
        "verifier_authority": False, "runtime_authority_granted": False,
    })
    access = TASK039DDataAccessPolicyV1({
        "d0_feature_values_authorized": False, "d1_fit_files": list(FIT_FILES), "d1_process": PROCESS_ID,
        "d1_real_fit_profiling_authorized": True, "d2_confirmation_file": CALIBRATION_FILE,
        "d2_real_confirmation_authorized": False, "normal_guard_file": NORMAL_GUARD_FILE,
        "normal_guard_access_authorized": False,
        "prohibited_files": [CALIBRATION_FILE, NORMAL_GUARD_FILE, "test", "labels", "attacks", "summary_labels", "private_label_custody"],
        "labels_authorized": False, "attacks_authorized": False, "p2_p3_p4_values_authorized": False,
        "br2_pair_results_authorized": False, "candidate_arm_evidence_visible_to_profiler": False,
        "private_ledger_access_authorized": False,
    })
    return {
        "protocol": protocol, "identity_view_policy": identity_policy, "source_scale_policy": source_scale,
        "event_policy": event, "target_response_policy": target, "direction_selection_policy": selection,
        "fit_gate_policy": fit, "confirmation_policy": confirmation, "outcome_policy": outcome,
        "method_comparison_policy": comparison, "numeric_evidence_policy": numeric,
        "data_access_policy": access,
    }


def build_task039d0_artifacts_v1(cohort_document: Mapping[str, Any]) -> dict[str, _FrozenProtocolArtifact]:
    """Build all D0 artifacts from the frozen public TASK-039C cohort only."""

    verify_self_hash_v1(cohort_document)
    expected = {
        "artifact_hash": CANDIDATE_COHORT_HASH,
        "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH,
        "union_count": 47,
        "selected_process": PROCESS_ID,
        "relation_family": RELATION_FAMILY,
    }
    for field, value in expected.items():
        if cohort_document.get(field) != value:
            raise RelationProfilingProtocolError(f"TASK-039C cohort {field} mismatch")
    identities = list(cohort_document["candidate_identity_list"])
    if len(identities) != 47 or len({(item["source"], item["target"]) for item in identities}) != 47:
        raise RelationProfilingProtocolError("TASK-039C identity list must contain 47 unique pairs")
    candidates = list(cohort_document["candidates"])
    if [(item["source"], item["target"]) for item in candidates] != [(item["source"], item["target"]) for item in identities]:
        raise RelationProfilingProtocolError("cohort candidate order differs from identity list")
    identity_records = [profiling_identity_from_candidate_v1(item) for item in identities]
    identity_view = ProfilingIdentityViewV1({
        "cohort_hash": CANDIDATE_COHORT_HASH, "identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH,
        "candidate_count": 47, "process": PROCESS_ID, "relation_family": RELATION_FAMILY,
        "candidates": identity_records,
    })
    provenance_records = [{
        "source": item["source"], "target": item["target"], "origin_arms": item["origin_arms"],
        "META": item["META"], "STAT": item["STAT"], "GDN": item["GDN"],
    } for item in candidates]
    provenance_view = CandidateProvenanceAnalysisViewV1({
        "cohort_hash": CANDIDATE_COHORT_HASH, "candidate_count": 47,
        "join_key": ["source", "target"], "join_allowed_after_outcomes_frozen": True,
        "candidates": provenance_records,
    })
    policies = _policy_instances()
    config = TASK039D0ProtocolConfigV1({
        "authoritative_task039c_tip": TASK039C_INTEGRATION_COMMIT,
        "lineage": {"dataset_manifest_hash": DATASET_MANIFEST_HASH, "br1_protocol_bundle_hash": BR1_PROTOCOL_BUNDLE_HASH, "candidate_cohort_hash": CANDIDATE_COHORT_HASH, "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH, "pair_universe_hash": C0_PAIR_UNIVERSE_HASH, "source_identity_hash": SOURCE_IDENTITY_HASH, "target_identity_hash": TARGET_IDENTITY_HASH},
        "split_roles": {"NORMAL_CANDIDATE_FIT": list(FIT_FILES), "NORMAL_RELATION_CALIBRATION": CALIBRATION_FILE, "NORMAL_GUARD": NORMAL_GUARD_FILE},
        "source_context": {"count": 12, "records": [{"source": source, "semantic_role": FROZEN_SOURCE_ROLES[source]} for source in FROZEN_SOURCES]},
        "target_context": {"count": 12, "records": [{"target": target, "semantic_role": "continuous_process_sensor"} for target in FROZEN_TARGETS]},
        "protocol_components": {name: item.to_dict() for name, item in policies.items()},
        "sequential_authority": {
            "D0": "protocol_only",
            "D1": "train1_train2_fit_only",
            "D1_commit_A": "TASK-039D1 implement normal relation fit profiling",
            "D1_commit_A_contains_real_HAI_result": False,
            "D1_execution_requires_clean_commit_A": True,
            "D1_post_execution_scientific_change_allowed": False,
            "D1_commit_B": "TASK-039D1 evaluate normal relation fit",
            "D1_commit_B_sanitized_results_only": True,
            "D1_must_end_with_train3_unopened": True,
            "D2": "planned_not_authorized_train3_confirmation",
            "D2_authorization_requires_passed_independently_reviewed_D1": True,
            "train4": "later_normal_guard_only",
        },
        "comparison_policy": policies["method_comparison_policy"].to_dict(),
        "public_private_boundary": {"raw_values": False, "raw_windows": False, "event_timestamps": False, "absolute_paths": False, "private_numeric_ledgers": False},
    })
    d1_auth = TASK039D1AuthorizationV1({
        "d0_protocol_hash": config.artifact_hash, "candidate_cohort_hash": CANDIDATE_COHORT_HASH,
        "candidate_identity_list_hash": CANDIDATE_IDENTITY_LIST_HASH, "candidate_count": 47,
        "process": PROCESS_ID, "relation_family": RELATION_FAMILY, "train1_authorized": True,
        "train2_authorized": True, "train3_authorized": False, "train4_authorized": False,
        "test_labels_attacks_authorized": False, "br2_pair_result_access": False,
        "candidate_arm_evidence_visible_to_profiler": False, "real_fit_profiling_authorized": True,
        "rule_v2_authorized": False, "agent_authorized": False, "detector_runtime_authorized": False,
    })
    bundle = TASK039DProtocolBundleV1({
        "task_id": "TASK-039D0", "status": "passed_task039d0_relation_profiling_protocol_freeze",
        "authoritative_main_commit": TASK039C_INTEGRATION_COMMIT, "config_hash": config.artifact_hash,
        "protocol": policies["protocol"].to_dict(), "identity_view_policy": policies["identity_view_policy"].to_dict(),
        "profiling_identity_view_hash": identity_view.artifact_hash,
        "provenance_analysis_view_hash": provenance_view.artifact_hash,
        "source_scale_policy": policies["source_scale_policy"].to_dict(),
        "event_policy": policies["event_policy"].to_dict(),
        "target_response_policy": policies["target_response_policy"].to_dict(),
        "direction_selection_policy": policies["direction_selection_policy"].to_dict(),
        "fit_gate_policy": policies["fit_gate_policy"].to_dict(),
        "confirmation_policy": policies["confirmation_policy"].to_dict(),
        "outcome_policy": policies["outcome_policy"].to_dict(),
        "method_comparison_policy": policies["method_comparison_policy"].to_dict(),
        "numeric_evidence_policy": policies["numeric_evidence_policy"].to_dict(),
        "data_access_policy_hash": policies["data_access_policy"].artifact_hash,
        "d1_authorization_hash": d1_auth.artifact_hash, "unresolved_fields": [],
        "real_hai_feature_access": False, "d2_execution_authorized": False,
        "rule_v2_authorized": False, "artifact_claim": "protocol_freeze_only_no_real_numeric_result",
    })
    return {
        **policies, "profiling_identity_view": identity_view,
        "provenance_analysis_view": provenance_view, "config": config,
        "d1_authorization": d1_auth, "bundle": bundle,
    }


def schema_for_artifact_v1(example: Mapping[str, Any]) -> dict[str, Any]:
    """Build a closed Draft 2020-12 schema from a deterministic artifact example."""

    artifact_type = str(example["artifact_type"])

    def infer(value: Any) -> dict[str, Any]:
        if value is None:
            return {"type": "null"}
        if isinstance(value, bool):
            return {"type": "boolean"}
        if isinstance(value, int):
            return {"type": "integer"}
        if isinstance(value, float):
            return {"type": "number"}
        if isinstance(value, str):
            return {"type": "string"}
        if isinstance(value, list):
            if not value:
                return {"type": "array", "items": {}}
            schemas = [infer(item) for item in value]
            first = schemas[0]
            item_schema = first if all(item == first for item in schemas) else {"anyOf": _unique_schemas(schemas)}
            return {"type": "array", "items": item_schema}
        if isinstance(value, Mapping):
            return {
                "type": "object", "additionalProperties": False,
                "required": list(value), "properties": {key: infer(item) for key, item in value.items()},
            }
        raise RelationProfilingProtocolError("unsupported schema example value")

    root = infer(example)
    root["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    root["$id"] = f"https://paperworks.local/schemas/v6/{artifact_type}_schema.json"
    root["title"] = artifact_type
    root["properties"]["schema_version"] = {"const": "1.0.0"}
    root["properties"]["artifact_type"] = {"const": artifact_type}
    root["properties"]["artifact_hash"] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    return root


def _unique_schemas(schemas: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    result: list[Mapping[str, Any]] = []
    for schema in schemas:
        if schema not in result:
            result.append(schema)
    return result


__all__ = [
    "RelationProfilingProtocolError", "RelationProfilingProtocolV1",
    "ProfilingIdentityViewPolicyV1", "ProfilingIdentityViewV1",
    "CandidateProvenanceAnalysisViewV1", "SourceScalePolicyV1",
    "SourceStepProfilingPolicyV1", "TargetResponseProfilingPolicyV1",
    "DirectionalRelationSelectionPolicyV1", "RelationFitGatePolicyV1",
    "RelationConfirmationPolicyV1", "DirectionalRelationIdentityV1",
    "RelationProfilingOutcomePolicyV1", "CandidateMethodComparisonPolicyV1",
    "NumericEvidenceAuthorityPolicyV1", "TASK039DDataAccessPolicyV1",
    "TASK039D1AuthorizationV1", "TASK039DProtocolBundleV1",
    "TASK039D0ProtocolConfigV1", "build_task039d0_artifacts_v1",
    "multi_file_robust_scale_v1", "derive_multi_file_source_parameters_v1",
    "derive_multi_file_target_scale_v1", "q75_linear_v1",
    "extract_file_local_events_v1", "classify_all_source_isolation_v1",
    "rank_direction_horizon_v1", "selected_fit_gate_v1",
    "train3_confirmation_gate_v1", "authorize_value_access_v1",
    "authorize_br2_reference_v1", "assert_arm_blind_identity_record_v1",
    "profiling_identity_from_candidate_v1", "schema_for_artifact_v1",
    "verify_self_hash_v1", "ARTIFACT_CLASSES", "ARTIFACT_CLASS_BY_TYPE",
]
