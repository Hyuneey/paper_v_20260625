"""Preregistered continuous-step delayed-response protocol for TASK-039BR1.

The module contains immutable policy artifacts and pure synthetic helpers.  It
does not read datasets, select a process, create a rule, or grant verifier or
runtime authority.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any, ClassVar, Mapping, NamedTuple, Sequence, TypeVar

from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    reject_unknown_fields,
    require_finite,
    stable_hash_v1,
)


BR0_DECISION_HASH = "3eceafb47742af9fc1be5dba82f148d33e31ba3095ba4b8a2d513ab9d4632a7b"
BR0_READINESS_HASH = "c1968c53d605756cd9d16f72306c730fcf6a9b3ceaf61368eba78157bb84f7a2"
BR0_COMMIT = "1cd670fe81f627dad79590709a7f7eaea2671460"
FAMILY_ID = "continuous_step_delayed_response_v1"
NUMERIC_EPSILON = 1e-12


class ContinuousStepProtocolError(V6FoundationError):
    """Raised when the preregistered protocol is violated."""


class StepDirectionV1(str, Enum):
    STEP_UP = "step_up"
    STEP_DOWN = "step_down"


class TargetDirectionV1(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"


class SourceEventStatusV1(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED_SEMANTICS = "unsupported_semantics"
    UNSUPPORTED_SOURCE_SCALE = "unsupported_source_scale"
    INSUFFICIENT_NONTRIVIAL_AMPLITUDES = "insufficient_nontrivial_amplitudes"
    INSUFFICIENT_FIT_EVENTS = "insufficient_fit_events"
    INSUFFICIENT_ISOLATED_EVENTS = "insufficient_isolated_events"
    UNSTABLE_PRE_LEVEL = "unstable_pre_level"
    UNSTABLE_POST_LEVEL = "unstable_post_level"
    CROSS_FILE_UNAVAILABLE = "cross_file_unavailable"
    MANUAL_DATA_CONFLICT = "manual_data_conflict"
    INVALID_SOURCE = "invalid_source"


class ScreeningStatusV1(str, Enum):
    FIT_SUPPORTED = "fit_supported"
    FIT_UNSUPPORTED = "fit_unsupported"
    CALIBRATION_CONFIRMED = "calibration_confirmed"
    CALIBRATION_CONFLICT = "calibration_conflict"
    RIGHT_CENSORED = "right_censored"
    DIRECTION_UNSTABLE = "direction_unstable"
    EFFECT_TOO_SMALL = "effect_too_small"
    INSUFFICIENT_SUPPORT = "insufficient_support"
    INVALID_TARGET = "invalid_target"


class ProcessOutcomeV1(str, Enum):
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    SELECTED = "selected"
    NOT_SELECTED = "not_selected"
    SELECTION_INDETERMINATE = "selection_indeterminate"


def _json_value(value: Any) -> Any:
    if isinstance(value, CreationMetadataV1):
        return value.to_dict()
    if isinstance(value, _ProtocolArtifact):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


ArtifactT = TypeVar("ArtifactT", bound="_ProtocolArtifact")


class _ProtocolArtifact:
    """Shared strict round-trip and self-hash behavior for policy artifacts."""

    ARTIFACT_TYPE: ClassVar[str]
    TUPLE_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def _validate_artifact_identity(self) -> None:
        if getattr(self, "schema_version") != V6_FOUNDATION_SCHEMA_VERSION:
            raise ContinuousStepProtocolError("schema_version must be 1.0.0")
        if getattr(self, "artifact_type") != self.ARTIFACT_TYPE:
            raise ContinuousStepProtocolError("artifact_type does not match contract")

    def _content_dict(self) -> dict[str, Any]:
        return {
            item.name: _json_value(getattr(self, item.name))
            for item in fields(self)
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content_dict())

    def to_dict(self) -> dict[str, Any]:
        result = self._content_dict()
        result["artifact_hash"] = self.artifact_hash
        return result

    @classmethod
    def from_dict(cls: type[ArtifactT], data: Mapping[str, Any]) -> ArtifactT:
        allowed = frozenset(item.name for item in fields(cls)) | {"artifact_hash"}
        try:
            reject_unknown_fields(data, allowed, cls.ARTIFACT_TYPE)
        except V6FoundationError as exc:
            raise ContinuousStepProtocolError(str(exc)) from exc
        kwargs = {item.name: data[item.name] for item in fields(cls)}
        for name in cls.TUPLE_FIELDS:
            kwargs[name] = tuple(kwargs[name])
        if "creation_metadata" in kwargs:
            kwargs["creation_metadata"] = CreationMetadataV1.from_dict(
                kwargs["creation_metadata"]
            )
        result = cls(**kwargs)
        supplied_hash = data.get("artifact_hash")
        if supplied_hash is not None and supplied_hash != result.artifact_hash:
            raise ContinuousStepProtocolError("artifact_hash does not match content")
        return result


def _require_exact_tuple(
    observed: tuple[Any, ...], expected: tuple[Any, ...], field_name: str
) -> None:
    if observed != expected:
        raise ContinuousStepProtocolError(f"{field_name} is not the frozen policy")


@dataclass(frozen=True)
class ContinuousStepRelationFamilyV1(_ProtocolArtifact):
    family_id: str
    family_kind: str
    authority_status: str
    source_cardinality: int
    target_cardinality: int
    source_target_must_differ: bool
    trigger_type: str
    source_step_directions: tuple[str, ...]
    target_directions: tuple[str, ...]
    directional_families: tuple[str, ...]
    violation_semantics: str
    runtime_outputs: tuple[str, ...]
    supported_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    rule_v1_compatible: bool
    requires_versioned_rule_semantics: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_relation_family_v1"

    ARTIFACT_TYPE = "continuous_step_relation_family_v1"
    TUPLE_FIELDS = frozenset(
        {
            "source_step_directions",
            "target_directions",
            "directional_families",
            "runtime_outputs",
            "supported_claims",
            "prohibited_claims",
        }
    )

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if (
            self.family_id != FAMILY_ID
            or self.family_kind != "delayed_response"
            or self.authority_status != "preregistered_experimental_protocol"
        ):
            raise ContinuousStepProtocolError("relation-family identity changed")
        if self.source_cardinality != 1 or self.target_cardinality != 1:
            raise ContinuousStepProtocolError("continuous-step family is pairwise")
        if not self.source_target_must_differ or self.trigger_type != "sustained_continuous_step":
            raise ContinuousStepProtocolError("relation-family structural bound changed")
        _require_exact_tuple(self.source_step_directions, ("step_up", "step_down"), "source_step_directions")
        _require_exact_tuple(self.target_directions, ("increase", "decrease"), "target_directions")
        _require_exact_tuple(
            self.directional_families,
            (
                "step_up->target_increase",
                "step_up->target_decrease",
                "step_down->target_increase",
                "step_down->target_decrease",
            ),
            "directional_families",
        )
        if self.violation_semantics != "missing_expected_response":
            raise ContinuousStepProtocolError("violation semantics changed")
        _require_exact_tuple(self.runtime_outputs, ("binary_anomaly", "abstain"), "runtime_outputs")
        required_prohibited = {"physical_causality", "root_cause", "universal_invariant", "complete_process_model", "attack_mechanism"}
        if not required_prohibited.issubset(self.prohibited_claims):
            raise ContinuousStepProtocolError("prohibited claims are incomplete")
        if self.rule_v1_compatible or not self.requires_versioned_rule_semantics:
            raise ContinuousStepProtocolError("Rule v1 isolation was weakened")


@dataclass(frozen=True)
class ContinuousStepTriggerPolicyV1(_ProtocolArtifact):
    sampling_interval_seconds: float
    pre_window_seconds: int
    post_hold_window_seconds: int
    minimum_stability_fraction: float
    source_refractory_seconds: int
    cross_source_isolation_radius_seconds: int
    numeric_epsilon: float
    source_roles: tuple[str, ...]
    observed_domain: str
    manual_review_required: bool
    metadata_confidence_policy: str
    finite_nonconstant_repeated_changes_all_fit_and_calibration_required: bool
    setpoints_excluded: bool
    discrete_sources_routed_to_family: bool
    data_behavior_grants_control_semantics: bool
    official_graph_grants_source_eligibility: bool
    cross_file_or_split_events_allowed: bool
    candidate_fit_files: tuple[str, ...]
    source_noise_scale_formula: str
    pre_level_formula: str
    post_level_formula: str
    step_amplitude_formula: str
    minimum_nontrivial_amplitudes: int
    q75_method: str
    source_step_threshold_formula: str
    source_stability_tolerance_formula: str
    cluster_retention_policy: str
    exact_amplitude_tie_policy: str
    directions_retained_separately: bool
    calibration_or_target_feedback_used: bool
    final_rule_parameter_authority: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_trigger_policy_v1"

    ARTIFACT_TYPE = "continuous_step_trigger_policy_v1"
    TUPLE_FIELDS = frozenset({"source_roles", "candidate_fit_files"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if require_finite(self.sampling_interval_seconds, "sampling_interval_seconds") != 1.0:
            raise ContinuousStepProtocolError("sampling interval must be one second")
        if (self.pre_window_seconds, self.post_hold_window_seconds) != (5, 5):
            raise ContinuousStepProtocolError("source windows changed")
        if require_finite(self.minimum_stability_fraction, "minimum_stability_fraction") != 0.8:
            raise ContinuousStepProtocolError("minimum stability changed")
        if (self.source_refractory_seconds, self.cross_source_isolation_radius_seconds) != (10, 2):
            raise ContinuousStepProtocolError("refractory or isolation policy changed")
        if require_finite(self.numeric_epsilon, "numeric_epsilon") != NUMERIC_EPSILON:
            raise ContinuousStepProtocolError("numeric epsilon changed")
        _require_exact_tuple(self.source_roles, ("control_command", "actuator_state", "actuator_feedback"), "source_roles")
        if (
            self.observed_domain != "continuous"
            or not self.manual_review_required
            or self.metadata_confidence_policy != "sufficient_under_frozen_metadata_policy"
            or not self.finite_nonconstant_repeated_changes_all_fit_and_calibration_required
            or not self.setpoints_excluded
        ):
            raise ContinuousStepProtocolError("source eligibility boundary changed")
        if (
            self.discrete_sources_routed_to_family
            or self.data_behavior_grants_control_semantics
            or self.official_graph_grants_source_eligibility
            or self.cross_file_or_split_events_allowed
        ):
            raise ContinuousStepProtocolError("source evidence authority was broadened")
        _require_exact_tuple(self.candidate_fit_files, ("hai-train1.csv", "hai-train2.csv"), "candidate_fit_files")
        if self.minimum_nontrivial_amplitudes != 20:
            raise ContinuousStepProtocolError("source calibration support changed")
        if self.q75_method != "linear_interpolation_index_0.75_times_n_minus_1":
            raise ContinuousStepProtocolError("Q75 method must be deterministic")
        if self.calibration_or_target_feedback_used or self.final_rule_parameter_authority:
            raise ContinuousStepProtocolError("screening threshold crossed provenance boundary")
        if not self.directions_retained_separately:
            raise ContinuousStepProtocolError("step directions must remain separate")


@dataclass(frozen=True)
class ContinuousStepResponsePolicyV1(_ProtocolArtifact):
    target_observed_domain: str
    target_pre_window_seconds: int
    target_response_window_seconds: int
    response_horizons_seconds: tuple[int, ...]
    target_baseline_formula: str
    target_response_formula: str
    target_noise_scale_formula: str
    target_noise_fit_role: str
    increase_evidence_rule: str
    decrease_evidence_rule: str
    right_censor_incomplete_windows: bool
    preserve_response_direction: bool
    absolute_response_only_prohibited: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_response_policy_v1"

    ARTIFACT_TYPE = "continuous_step_response_policy_v1"
    TUPLE_FIELDS = frozenset({"response_horizons_seconds"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.target_observed_domain != "continuous":
            raise ContinuousStepProtocolError("target domain must be continuous")
        if (self.target_pre_window_seconds, self.target_response_window_seconds) != (5, 3):
            raise ContinuousStepProtocolError("target windows changed")
        _require_exact_tuple(self.response_horizons_seconds, (1, 5, 10, 30, 60), "response_horizons_seconds")
        if self.target_noise_fit_role != "normal_candidate_fit":
            raise ContinuousStepProtocolError("target scale must be fit-only")
        if not (self.right_censor_incomplete_windows and self.preserve_response_direction and self.absolute_response_only_prohibited):
            raise ContinuousStepProtocolError("target response boundary changed")


@dataclass(frozen=True)
class ContinuousStepFeasibilityPolicyV1(_ProtocolArtifact):
    candidate_fit_files: tuple[str, ...]
    calibration_file: str
    normal_guard_values_prohibited: bool
    screening_dimensions: tuple[str, ...]
    required_aggregate_statistics: tuple[str, ...]
    ranking_order: tuple[str, ...]
    fit_total_isolated_events_minimum: int
    fit_per_file_isolated_events_minimum: int
    fit_directional_consistency_minimum: float
    fit_per_file_directional_consistency_minimum: float
    fit_robust_effect_ratio_minimum: float
    fit_direction_agreement_required: bool
    calibration_isolated_events_minimum: int
    calibration_directional_consistency_minimum: float
    calibration_robust_effect_ratio_minimum: float
    frozen_fit_fields_on_calibration: tuple[str, ...]
    multiple_horizons_do_not_inflate_pairs: bool
    unconditioned_screening_feasibility_only: bool
    final_operating_regime_binding_required: bool
    weighted_score_used: bool
    real_data_executed: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_feasibility_policy_v1"

    ARTIFACT_TYPE = "continuous_step_feasibility_policy_v1"
    TUPLE_FIELDS = frozenset({"candidate_fit_files", "screening_dimensions", "required_aggregate_statistics", "ranking_order", "frozen_fit_fields_on_calibration"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        _require_exact_tuple(self.candidate_fit_files, ("hai-train1.csv", "hai-train2.csv"), "candidate_fit_files")
        if self.calibration_file != "hai-train3.csv" or not self.normal_guard_values_prohibited:
            raise ContinuousStepProtocolError("normal split policy changed")
        _require_exact_tuple(self.screening_dimensions, ("source", "source_step_direction", "target", "target_response_direction", "response_horizon"), "screening_dimensions")
        _require_exact_tuple(self.required_aggregate_statistics, ("usable_isolated_event_count", "right_censored_count", "median_target_response", "directional_consistency", "robust_effect_ratio", "per_file_support"), "required_aggregate_statistics")
        _require_exact_tuple(self.ranking_order, ("highest_directional_consistency", "highest_robust_effect_ratio", "shortest_horizon", "lexicographic_exact_tie_only"), "ranking_order")
        if (self.fit_total_isolated_events_minimum, self.fit_per_file_isolated_events_minimum) != (20, 5):
            raise ContinuousStepProtocolError("fit support counts changed")
        if (self.fit_directional_consistency_minimum, self.fit_per_file_directional_consistency_minimum, self.fit_robust_effect_ratio_minimum) != (0.7, 0.6, 2.0):
            raise ContinuousStepProtocolError("fit support thresholds changed")
        if (self.calibration_isolated_events_minimum, self.calibration_directional_consistency_minimum, self.calibration_robust_effect_ratio_minimum) != (5, 0.6, 1.0):
            raise ContinuousStepProtocolError("calibration thresholds changed")
        _require_exact_tuple(self.frozen_fit_fields_on_calibration, ("source_step_threshold", "source_stability_tolerance", "target_response_direction", "response_horizon"), "frozen_fit_fields_on_calibration")
        if not (self.fit_direction_agreement_required and self.multiple_horizons_do_not_inflate_pairs and self.unconditioned_screening_feasibility_only and self.final_operating_regime_binding_required):
            raise ContinuousStepProtocolError("feasibility scientific boundary changed")
        if self.weighted_score_used or self.real_data_executed:
            raise ContinuousStepProtocolError("BR1 cannot score or execute real data")


@dataclass(frozen=True)
class ContinuousStepProcessSelectionPolicyV1(_ProtocolArtifact):
    compared_processes: tuple[str, ...]
    source_threshold_count_minimum: int
    eligible_target_count_minimum: int
    confirmed_directional_pair_count_minimum: int
    distinct_confirmed_source_count_minimum: int
    distinct_confirmed_target_count_minimum: int
    transfer_rate_minimum: float
    required_fit_files: tuple[str, ...]
    required_calibration_file: str
    normal_guard_values_prohibited: bool
    prohibited_access_count_maximum: int
    maximize_metrics: tuple[str, ...]
    minimize_metrics: tuple[str, ...]
    strict_improvement_metric_minimum: int
    weighted_score_used: bool
    prohibited_selection_bases: tuple[str, ...]
    neither_feasible_status: str
    non_dominance_status: str
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_process_selection_policy_v1"

    ARTIFACT_TYPE = "continuous_step_process_selection_policy_v1"
    TUPLE_FIELDS = frozenset({"compared_processes", "required_fit_files", "maximize_metrics", "minimize_metrics", "prohibited_selection_bases"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        _require_exact_tuple(self.compared_processes, ("P1", "P3"), "compared_processes")
        if (self.source_threshold_count_minimum, self.eligible_target_count_minimum, self.confirmed_directional_pair_count_minimum, self.distinct_confirmed_source_count_minimum, self.distinct_confirmed_target_count_minimum) != (2, 3, 3, 2, 2):
            raise ContinuousStepProtocolError("process feasibility counts changed")
        if require_finite(self.transfer_rate_minimum, "transfer_rate_minimum") != 0.5:
            raise ContinuousStepProtocolError("transfer gate changed")
        _require_exact_tuple(self.required_fit_files, ("hai-train1.csv", "hai-train2.csv"), "required_fit_files")
        if self.required_calibration_file != "hai-train3.csv" or not self.normal_guard_values_prohibited or self.prohibited_access_count_maximum != 0:
            raise ContinuousStepProtocolError("process data boundary changed")
        if self.strict_improvement_metric_minimum != 2 or self.weighted_score_used:
            raise ContinuousStepProtocolError("Pareto policy changed")
        if self.neither_feasible_status != "blocked_no_feasible_continuous_step_process" or self.non_dominance_status != "blocked_continuous_process_selection_indeterminate":
            raise ContinuousStepProtocolError("blocked process statuses changed")


@dataclass(frozen=True)
class ContinuousStepUnsupportedPolicyV1(_ProtocolArtifact):
    source_event_statuses: tuple[str, ...]
    source_target_statuses: tuple[str, ...]
    process_outcomes: tuple[str, ...]
    future_runtime_abstention_reasons: tuple[str, ...]
    invalid_rule_is_abstention: bool
    parameter_binding_failure_is_abstention: bool
    isolation_is_runtime_abstention_rule: bool
    no_rule_created_in_br1: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_unsupported_policy_v1"

    ARTIFACT_TYPE = "continuous_step_unsupported_policy_v1"
    TUPLE_FIELDS = frozenset({"source_event_statuses", "source_target_statuses", "process_outcomes", "future_runtime_abstention_reasons"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        _require_exact_tuple(self.source_event_statuses, tuple(item.value for item in SourceEventStatusV1), "source_event_statuses")
        _require_exact_tuple(self.source_target_statuses, tuple(item.value for item in ScreeningStatusV1), "source_target_statuses")
        _require_exact_tuple(self.process_outcomes, tuple(item.value for item in ProcessOutcomeV1), "process_outcomes")
        if self.invalid_rule_is_abstention or self.parameter_binding_failure_is_abstention or self.isolation_is_runtime_abstention_rule or self.no_rule_created_in_br1:
            raise ContinuousStepProtocolError("unsupported and abstention states were conflated")


@dataclass(frozen=True)
class ContinuousStepParameterProvenancePolicyV1(_ProtocolArtifact):
    parameter_classes: tuple[str, ...]
    screening_implicit_promotion_prohibited: bool
    final_recalibration_task: str
    deterministic_project_artifacts_required: bool
    agent_allowed_actions: tuple[str, ...]
    agent_prohibited_actions: tuple[str, ...]
    labels_or_test_performance_used: bool
    agent_number_authority: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_parameter_provenance_policy_v1"

    ARTIFACT_TYPE = "continuous_step_parameter_provenance_policy_v1"
    TUPLE_FIELDS = frozenset({"parameter_classes", "agent_allowed_actions", "agent_prohibited_actions"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        _require_exact_tuple(self.parameter_classes, ("feasibility_screening", "final_calibration", "runtime"), "parameter_classes")
        if not self.screening_implicit_promotion_prohibited or not self.deterministic_project_artifacts_required:
            raise ContinuousStepProtocolError("parameter provenance separation changed")
        if self.labels_or_test_performance_used or self.agent_number_authority:
            raise ContinuousStepProtocolError("Agent gained numerical authority")


@dataclass(frozen=True)
class ContinuousStepRuleMigrationPlanV1(_ProtocolArtifact):
    plan_status: str
    additive_version_required: bool
    trigger_fields: tuple[str, ...]
    expected_effect_fields: tuple[str, ...]
    preserved_contracts: tuple[str, ...]
    rule_v1_modified: bool
    rule_v2_created: bool
    route_continuous_rules_through_rule_v1: bool
    independent_schema_and_parser_required: bool
    task032_hash_preservation_required: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_rule_migration_plan_v1"

    ARTIFACT_TYPE = "continuous_step_rule_migration_plan_v1"
    TUPLE_FIELDS = frozenset({"trigger_fields", "expected_effect_fields", "preserved_contracts"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.plan_status != "migration_plan_only" or not self.additive_version_required:
            raise ContinuousStepProtocolError("Rule v2 boundary changed")
        if self.rule_v1_modified or self.rule_v2_created or self.route_continuous_rules_through_rule_v1:
            raise ContinuousStepProtocolError("Rule v1 isolation failed")
        if not self.independent_schema_and_parser_required or not self.task032_hash_preservation_required:
            raise ContinuousStepProtocolError("future additive migration guards missing")


@dataclass(frozen=True)
class ContinuousStepVerifierMigrationPlanV1(_ProtocolArtifact):
    plan_status: str
    ordered_future_checks: tuple[str, ...]
    validity_excludes: tuple[str, ...]
    verifier_v1_modified: bool
    implementation_created: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_verifier_migration_plan_v1"

    ARTIFACT_TYPE = "continuous_step_verifier_migration_plan_v1"
    TUPLE_FIELDS = frozenset({"ordered_future_checks", "validity_excludes"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.plan_status != "migration_plan_only" or len(self.ordered_future_checks) != 20:
            raise ContinuousStepProtocolError("future verifier plan must contain twenty checks")
        if self.verifier_v1_modified or self.implementation_created:
            raise ContinuousStepProtocolError("Verifier v1 changed during planning")


@dataclass(frozen=True)
class ContinuousStepRuntimeMigrationPlanV1(_ProtocolArtifact):
    plan_status: str
    required_trace_fields: tuple[str, ...]
    abstention_reasons: tuple[str, ...]
    deterministic_trace_required: bool
    llm_free_runtime_required: bool
    explanation_prohibited_inventions: tuple[str, ...]
    runtime_v1_modified: bool
    runtime_implementation_created: bool
    rule_execution_performed: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_runtime_migration_plan_v1"

    ARTIFACT_TYPE = "continuous_step_runtime_migration_plan_v1"
    TUPLE_FIELDS = frozenset({"required_trace_fields", "abstention_reasons", "explanation_prohibited_inventions"})

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.plan_status != "migration_plan_only" or not self.deterministic_trace_required or not self.llm_free_runtime_required:
            raise ContinuousStepProtocolError("runtime planning boundary changed")
        if self.runtime_v1_modified or self.runtime_implementation_created or self.rule_execution_performed:
            raise ContinuousStepProtocolError("runtime implementation or execution is prohibited")


@dataclass(frozen=True)
class ContinuousStepProtocolBundleV1(_ProtocolArtifact):
    task_id: str
    status: str
    br0_commit: str
    br0_decision_hash: str
    br0_readiness_hash: str
    relation_family: ContinuousStepRelationFamilyV1
    trigger_policy: ContinuousStepTriggerPolicyV1
    response_policy: ContinuousStepResponsePolicyV1
    feasibility_policy: ContinuousStepFeasibilityPolicyV1
    process_selection_policy: ContinuousStepProcessSelectionPolicyV1
    unsupported_policy: ContinuousStepUnsupportedPolicyV1
    parameter_provenance_policy: ContinuousStepParameterProvenancePolicyV1
    rule_migration_plan: ContinuousStepRuleMigrationPlanV1
    verifier_migration_plan: ContinuousStepVerifierMigrationPlanV1
    runtime_migration_plan: ContinuousStepRuntimeMigrationPlanV1
    validity_authority_granted: bool
    runtime_authority_granted: bool
    process_selection_granted: bool
    process_selected: bool
    task039c_authorized: bool
    real_data_accessed: bool
    next_task: str
    creation_metadata: CreationMetadataV1
    schema_version: str = V6_FOUNDATION_SCHEMA_VERSION
    artifact_type: str = "continuous_step_protocol_bundle_v1"

    ARTIFACT_TYPE = "continuous_step_protocol_bundle_v1"

    def __post_init__(self) -> None:
        self._validate_artifact_identity()
        if self.task_id != "TASK-039BR1" or self.status != "passed_continuous_step_relation_protocol_freeze":
            raise ContinuousStepProtocolError("bundle task status is invalid")
        if self.br0_commit != BR0_COMMIT or self.br0_decision_hash != BR0_DECISION_HASH or self.br0_readiness_hash != BR0_READINESS_HASH:
            raise ContinuousStepProtocolError("BR0 lineage mismatch")
        if any((self.validity_authority_granted, self.runtime_authority_granted, self.process_selection_granted, self.process_selected, self.task039c_authorized, self.real_data_accessed)):
            raise ContinuousStepProtocolError("BR1 bundle crossed its authority boundary")
        if self.next_task != "TASK-039BR2":
            raise ContinuousStepProtocolError("next task must be TASK-039BR2")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ContinuousStepProtocolBundleV1":
        allowed = frozenset(item.name for item in fields(cls)) | {"artifact_hash"}
        try:
            reject_unknown_fields(data, allowed, cls.ARTIFACT_TYPE)
        except V6FoundationError as exc:
            raise ContinuousStepProtocolError(str(exc)) from exc
        nested = {
            "relation_family": ContinuousStepRelationFamilyV1,
            "trigger_policy": ContinuousStepTriggerPolicyV1,
            "response_policy": ContinuousStepResponsePolicyV1,
            "feasibility_policy": ContinuousStepFeasibilityPolicyV1,
            "process_selection_policy": ContinuousStepProcessSelectionPolicyV1,
            "unsupported_policy": ContinuousStepUnsupportedPolicyV1,
            "parameter_provenance_policy": ContinuousStepParameterProvenancePolicyV1,
            "rule_migration_plan": ContinuousStepRuleMigrationPlanV1,
            "verifier_migration_plan": ContinuousStepVerifierMigrationPlanV1,
            "runtime_migration_plan": ContinuousStepRuntimeMigrationPlanV1,
        }
        kwargs = {item.name: data[item.name] for item in fields(cls)}
        for name, artifact_cls in nested.items():
            kwargs[name] = artifact_cls.from_dict(kwargs[name])
        kwargs["creation_metadata"] = CreationMetadataV1.from_dict(kwargs["creation_metadata"])
        result = cls(**kwargs)
        if data.get("artifact_hash") is not None and data["artifact_hash"] != result.artifact_hash:
            raise ContinuousStepProtocolError("artifact_hash does not match content")
        return result


class SourceScreeningParametersV1(NamedTuple):
    status: str
    source_noise_scale: float
    nontrivial_amplitude_count: int
    source_step_threshold: float | None
    source_stability_tolerance: float | None


class SustainedStepEventV1(NamedTuple):
    event_index: int
    direction: str
    pre_level: float
    post_level: float
    step_amplitude: float
    pre_stability_fraction: float
    post_stability_fraction: float


class StepCandidateEvaluationV1(NamedTuple):
    status: str
    event: SustainedStepEventV1 | None


class TargetResponseEvaluationV1(NamedTuple):
    right_censored: bool
    target_response: float | None
    direction_matches: bool | None


class ProcessSelectionDecisionV1(NamedTuple):
    status: str
    selected_process: str | None
    reason: str


def _finite_sequence(values: Sequence[float], field_name: str) -> tuple[float, ...]:
    result = tuple(float(item) for item in values)
    if any(not math.isfinite(item) for item in result):
        raise ContinuousStepProtocolError(f"{field_name} must contain finite values")
    return result


def _mad(values: Sequence[float]) -> float:
    if not values:
        raise ContinuousStepProtocolError("MAD requires at least one value")
    center = statistics.median(values)
    return float(statistics.median(abs(item - center) for item in values))


def _q75_linear(values: Sequence[float]) -> float:
    ordered = sorted(float(item) for item in values)
    if not ordered:
        raise ContinuousStepProtocolError("Q75 requires values")
    position = 0.75 * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def robust_one_step_scale_v1(
    values: Sequence[float], *, numeric_epsilon: float = NUMERIC_EPSILON
) -> float:
    """Return the frozen 1.4826*MAD one-step scale for synthetic inputs."""

    sequence = _finite_sequence(values, "values")
    if len(sequence) < 2:
        raise ContinuousStepProtocolError("source scale requires two samples")
    epsilon = require_finite(numeric_epsilon, "numeric_epsilon")
    if epsilon <= 0:
        raise ContinuousStepProtocolError("numeric_epsilon must be positive")
    changes = tuple(sequence[index] - sequence[index - 1] for index in range(1, len(sequence)))
    return max(1.4826 * _mad(changes), epsilon)


def _pre_post_levels(
    values: tuple[float, ...], event_index: int, *, pre_window: int = 5, post_window: int = 5
) -> tuple[float, float] | None:
    if event_index < pre_window or event_index + post_window > len(values):
        return None
    return (
        float(statistics.median(values[event_index - pre_window : event_index])),
        float(statistics.median(values[event_index : event_index + post_window])),
    )


def derive_source_screening_parameters_v1(
    values: Sequence[float],
) -> SourceScreeningParametersV1:
    """Derive fit-only source screening parameters using the frozen formulas."""

    sequence = _finite_sequence(values, "source values")
    noise = robust_one_step_scale_v1(sequence)
    amplitudes: list[float] = []
    for event_index in range(5, len(sequence) - 5 + 1):
        levels = _pre_post_levels(sequence, event_index)
        assert levels is not None
        amplitude = abs(levels[1] - levels[0])
        if amplitude > noise:
            amplitudes.append(amplitude)
    if len(amplitudes) < 20:
        return SourceScreeningParametersV1(
            SourceEventStatusV1.INSUFFICIENT_NONTRIVIAL_AMPLITUDES.value,
            noise,
            len(amplitudes),
            None,
            None,
        )
    threshold = max(5.0 * noise, _q75_linear(amplitudes))
    tolerance = max(3.0 * noise, 0.10 * threshold)
    return SourceScreeningParametersV1(
        SourceEventStatusV1.SUPPORTED.value,
        noise,
        len(amplitudes),
        threshold,
        tolerance,
    )


def evaluate_step_candidate_v1(
    values: Sequence[float],
    event_index: int,
    *,
    source_step_threshold: float,
    source_stability_tolerance: float,
) -> StepCandidateEvaluationV1:
    sequence = _finite_sequence(values, "source values")
    levels = _pre_post_levels(sequence, event_index)
    if levels is None:
        return StepCandidateEvaluationV1(SourceEventStatusV1.CROSS_FILE_UNAVAILABLE.value, None)
    threshold = require_finite(source_step_threshold, "source_step_threshold")
    tolerance = require_finite(source_stability_tolerance, "source_stability_tolerance")
    if threshold <= 0 or tolerance < 0:
        raise ContinuousStepProtocolError("threshold and tolerance must be bounded")
    pre_level, post_level = levels
    amplitude = post_level - pre_level
    if amplitude == 0 or abs(amplitude) < threshold:
        return StepCandidateEvaluationV1(SourceEventStatusV1.INSUFFICIENT_FIT_EVENTS.value, None)
    pre = sequence[event_index - 5 : event_index]
    post = sequence[event_index : event_index + 5]
    pre_fraction = sum(abs(item - pre_level) <= tolerance for item in pre) / 5.0
    post_fraction = sum(abs(item - post_level) <= tolerance for item in post) / 5.0
    if pre_fraction < 0.8:
        return StepCandidateEvaluationV1(SourceEventStatusV1.UNSTABLE_PRE_LEVEL.value, None)
    if post_fraction < 0.8:
        return StepCandidateEvaluationV1(SourceEventStatusV1.UNSTABLE_POST_LEVEL.value, None)
    direction = StepDirectionV1.STEP_UP.value if amplitude > 0 else StepDirectionV1.STEP_DOWN.value
    return StepCandidateEvaluationV1(
        SourceEventStatusV1.SUPPORTED.value,
        SustainedStepEventV1(event_index, direction, pre_level, post_level, amplitude, pre_fraction, post_fraction),
    )


def cluster_step_events_v1(
    events: Sequence[SustainedStepEventV1], *, refractory_seconds: int = 10
) -> tuple[SustainedStepEventV1, ...]:
    """Single-link cluster source events and retain largest amplitude, then earliest."""

    if refractory_seconds != 10:
        raise ContinuousStepProtocolError("source refractory period is frozen at 10")
    ordered = sorted(events, key=lambda item: item.event_index)
    if not ordered:
        return ()
    clusters: list[list[SustainedStepEventV1]] = [[ordered[0]]]
    for event in ordered[1:]:
        if event.event_index - clusters[-1][-1].event_index <= refractory_seconds:
            clusters[-1].append(event)
        else:
            clusters.append([event])
    retained = [
        min(cluster, key=lambda item: (-abs(item.step_amplitude), item.event_index))
        for cluster in clusters
    ]
    return tuple(retained)


def extract_sustained_step_events_v1(
    values: Sequence[float],
    *,
    source_step_threshold: float,
    source_stability_tolerance: float,
) -> tuple[SustainedStepEventV1, ...]:
    sequence = _finite_sequence(values, "source values")
    events: list[SustainedStepEventV1] = []
    for event_index in range(5, len(sequence) - 5 + 1):
        result = evaluate_step_candidate_v1(
            sequence,
            event_index,
            source_step_threshold=source_step_threshold,
            source_stability_tolerance=source_stability_tolerance,
        )
        if result.event is not None:
            events.append(result.event)
    return cluster_step_events_v1(events)


def classify_event_isolation_v1(
    source_events: Mapping[str, Sequence[SustainedStepEventV1]],
    *,
    isolation_radius_seconds: int = 2,
) -> dict[str, tuple[tuple[SustainedStepEventV1, bool], ...]]:
    if isolation_radius_seconds != 2:
        raise ContinuousStepProtocolError("isolation radius is frozen at two seconds")
    result: dict[str, tuple[tuple[SustainedStepEventV1, bool], ...]] = {}
    for source, events in source_events.items():
        classified = []
        for event in events:
            isolated = not any(
                abs(event.event_index - other.event_index) <= isolation_radius_seconds
                for other_source, other_events in source_events.items()
                if other_source != source
                for other in other_events
            )
            classified.append((event, isolated))
        result[source] = tuple(classified)
    return result


def evaluate_target_response_v1(
    values: Sequence[float],
    *,
    event_index: int,
    horizon_seconds: int,
    target_noise_scale: float,
    target_direction: str,
) -> TargetResponseEvaluationV1:
    sequence = _finite_sequence(values, "target values")
    if horizon_seconds not in {1, 5, 10, 30, 60}:
        raise ContinuousStepProtocolError("response horizon is not preregistered")
    if target_direction not in {item.value for item in TargetDirectionV1}:
        raise ContinuousStepProtocolError("target direction must be explicit")
    if event_index < 5 or event_index + horizon_seconds + 3 > len(sequence):
        return TargetResponseEvaluationV1(True, None, None)
    noise = require_finite(target_noise_scale, "target_noise_scale")
    if noise <= 0:
        raise ContinuousStepProtocolError("target_noise_scale must be positive")
    baseline = float(statistics.median(sequence[event_index - 5 : event_index]))
    response_level = float(statistics.median(sequence[event_index + horizon_seconds : event_index + horizon_seconds + 3]))
    response = response_level - baseline
    matches = response > noise if target_direction == "increase" else response < -noise
    return TargetResponseEvaluationV1(False, response, matches)


def fit_support_gate_v1(
    *,
    total_isolated_events: int,
    train1_isolated_events: int,
    train2_isolated_events: int,
    fit_directional_consistency: float,
    train1_directional_consistency: float,
    train2_directional_consistency: float,
    fit_robust_effect_ratio: float,
    direction_agrees_across_files: bool,
) -> bool:
    return (
        total_isolated_events >= 20
        and train1_isolated_events >= 5
        and train2_isolated_events >= 5
        and fit_directional_consistency >= 0.70
        and train1_directional_consistency >= 0.60
        and train2_directional_consistency >= 0.60
        and fit_robust_effect_ratio >= 2.0
        and direction_agrees_across_files
    )


def calibration_confirmation_gate_v1(
    *,
    train3_isolated_events: int,
    source_direction_unchanged: bool,
    target_direction_unchanged: bool,
    train3_directional_consistency: float,
    train3_robust_effect_ratio: float,
    fit_parameters_reused_without_retuning: bool,
) -> bool:
    return (
        train3_isolated_events >= 5
        and source_direction_unchanged
        and target_direction_unchanged
        and train3_directional_consistency >= 0.60
        and train3_robust_effect_ratio >= 1.0
        and fit_parameters_reused_without_retuning
    )


def process_feasibility_gate_v1(metrics: Mapping[str, Any]) -> bool:
    required_files = tuple(metrics.get("normal_candidate_fit_files", ()))
    return (
        int(metrics.get("documented_sources_with_valid_fit_thresholds", 0)) >= 2
        and int(metrics.get("eligible_continuous_targets", 0)) >= 3
        and int(metrics.get("calibration_confirmed_directional_pairs", 0)) >= 3
        and int(metrics.get("distinct_confirmed_sources", 0)) >= 2
        and int(metrics.get("distinct_confirmed_targets", 0)) >= 2
        and float(metrics.get("fit_to_calibration_transfer_rate", 0.0)) >= 0.50
        and required_files == ("hai-train1.csv", "hai-train2.csv")
        and metrics.get("normal_relation_calibration_file") == "hai-train3.csv"
        and metrics.get("normal_guard_feature_values_accessed") is False
        and int(metrics.get("prohibited_data_access_count", 1)) == 0
    )


_MAXIMIZE_PROCESS_METRICS = (
    "distinct_confirmed_sources",
    "distinct_confirmed_targets",
    "calibration_confirmed_directional_pairs",
    "fit_to_calibration_transfer_rate",
    "median_calibration_isolated_event_support",
    "manual_metadata_coverage",
)
_MINIMIZE_PROCESS_METRICS = (
    "metadata_unresolved_ratio",
    "non_isolated_source_event_ratio",
    "missing_or_nonfinite_rate",
)


def _dominates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    no_worse = all(float(left[key]) >= float(right[key]) for key in _MAXIMIZE_PROCESS_METRICS) and all(
        float(left[key]) <= float(right[key]) for key in _MINIMIZE_PROCESS_METRICS
    )
    strictly_better = sum(float(left[key]) > float(right[key]) for key in _MAXIMIZE_PROCESS_METRICS) + sum(
        float(left[key]) < float(right[key]) for key in _MINIMIZE_PROCESS_METRICS
    )
    return no_worse and strictly_better >= 2


def select_process_v1(
    p1_metrics: Mapping[str, Any], p3_metrics: Mapping[str, Any]
) -> ProcessSelectionDecisionV1:
    p1_feasible = process_feasibility_gate_v1(p1_metrics)
    p3_feasible = process_feasibility_gate_v1(p3_metrics)
    if p1_feasible and not p3_feasible:
        return ProcessSelectionDecisionV1(ProcessOutcomeV1.SELECTED.value, "P1", "only_P1_feasible")
    if p3_feasible and not p1_feasible:
        return ProcessSelectionDecisionV1(ProcessOutcomeV1.SELECTED.value, "P3", "only_P3_feasible")
    if not p1_feasible and not p3_feasible:
        return ProcessSelectionDecisionV1(ProcessOutcomeV1.INFEASIBLE.value, None, "blocked_no_feasible_continuous_step_process")
    p1_dominates = _dominates(p1_metrics, p3_metrics)
    p3_dominates = _dominates(p3_metrics, p1_metrics)
    if p1_dominates == p3_dominates:
        return ProcessSelectionDecisionV1(ProcessOutcomeV1.SELECTION_INDETERMINATE.value, None, "blocked_continuous_process_selection_indeterminate")
    selected = "P1" if p1_dominates else "P3"
    return ProcessSelectionDecisionV1(ProcessOutcomeV1.SELECTED.value, selected, "pareto_dominance")


def default_protocol_config_content_v1() -> dict[str, Any]:
    """Return the unhashed TASK-039BR1 protocol configuration."""

    return {
        "schema_version": "1.0.0",
        "artifact_type": "task039br1_continuous_step_protocol_config",
        "task_id": "TASK-039BR1",
        "br0_commit": BR0_COMMIT,
        "br0_decision_hash": BR0_DECISION_HASH,
        "br0_readiness_hash": BR0_READINESS_HASH,
        "relation_family_id": FAMILY_ID,
        "source_roles": ["control_command", "actuator_state", "actuator_feedback"],
        "source_eligibility": {
            "observed_domain": "continuous",
            "manual_review_required": True,
            "metadata_confidence": "sufficient_under_frozen_metadata_policy",
            "finite_nonconstant_repeated_changes_train1_train2_train3_required": True,
            "data_behavior_grants_control_semantics": False,
            "official_graph_grants_source_eligibility": False,
            "discrete_sources_routed_to_family": False,
        },
        "setpoints_excluded": True,
        "source_trigger": {
            "sampling_interval_seconds": 1.0,
            "pre_window_seconds": 5,
            "post_hold_window_seconds": 5,
            "minimum_stability_fraction": 0.8,
            "source_refractory_seconds": 10,
            "cross_source_isolation_radius_seconds": 2,
            "numeric_epsilon": NUMERIC_EPSILON,
        },
        "source_scale_strategy": {
            "fit_role_only": "normal_candidate_fit",
            "minimum_nontrivial_amplitudes": 20,
            "noise_scale": "max(1.4826*MAD(dx),numeric_epsilon)",
            "q75_method": "linear_interpolation_index_0.75_times_n_minus_1",
            "step_threshold": "max(5*source_noise_scale,Q75(A_positive))",
            "stability_tolerance": "max(3*source_noise_scale,0.10*source_step_threshold)",
        },
        "target_response": {
            "pre_window_seconds": 5,
            "response_window_seconds": 3,
            "horizons_seconds": [1, 5, 10, 30, 60],
            "noise_scale": "max(1.4826*MAD(one_step_target_changes),numeric_epsilon)",
        },
        "fit_gate": {"total_isolated": 20, "per_file_isolated": 5, "consistency": 0.70, "per_file_consistency": 0.60, "robust_effect_ratio": 2.0},
        "calibration_gate": {"isolated": 5, "consistency": 0.60, "robust_effect_ratio": 1.0, "retuning": False},
        "process_gate": {"valid_sources": 2, "eligible_targets": 3, "confirmed_pairs": 3, "distinct_sources": 2, "distinct_targets": 2, "transfer_rate": 0.50},
        "directional_families": ["step_up->target_increase", "step_up->target_decrease", "step_down->target_increase", "step_down->target_decrease"],
        "unsupported_state_registries": {
            "source_event": [item.value for item in SourceEventStatusV1],
            "source_target": [item.value for item in ScreeningStatusV1],
            "process": [item.value for item in ProcessOutcomeV1],
        },
        "pareto_weighted_score": False,
        "numerical_provenance": {"agent_number_authority": False, "implicit_screening_parameter_promotion": False},
        "migration_boundaries": {"rule_v1_modified": False, "rule_v2_created": False, "verifier_v1_modified": False, "runtime_v1_modified": False},
        "real_data_policy": {"real_hai_feature_access": False, "attack_or_test_access": False, "process_selection": False, "task039c_authorized": False},
    }


def build_default_protocol_bundle_v1(
    *, config_hash: str, created_at: str = "2026-08-03T00:00:00+09:00"
) -> ContinuousStepProtocolBundleV1:
    metadata = CreationMetadataV1(created_at=created_at, created_by="TASK-039BR1", code_commit=BR0_COMMIT, config_hash=config_hash)
    relation = ContinuousStepRelationFamilyV1(
        family_id=FAMILY_ID, family_kind="delayed_response", authority_status="preregistered_experimental_protocol",
        source_cardinality=1, target_cardinality=1, source_target_must_differ=True, trigger_type="sustained_continuous_step",
        source_step_directions=("step_up", "step_down"), target_directions=("increase", "decrease"),
        directional_families=("step_up->target_increase", "step_up->target_decrease", "step_down->target_increase", "step_down->target_decrease"),
        violation_semantics="missing_expected_response", runtime_outputs=("binary_anomaly", "abstain"),
        supported_claims=("normal_data_step_conditioned_association", "typical_delayed_response", "expected_response_direction", "normal_support_and_transfer"),
        prohibited_claims=("physical_causality", "root_cause", "universal_invariant", "complete_process_model", "attack_mechanism"),
        rule_v1_compatible=False, requires_versioned_rule_semantics=True, creation_metadata=metadata,
    )
    trigger = ContinuousStepTriggerPolicyV1(
        sampling_interval_seconds=1.0, pre_window_seconds=5, post_hold_window_seconds=5, minimum_stability_fraction=0.8,
        source_refractory_seconds=10, cross_source_isolation_radius_seconds=2, numeric_epsilon=NUMERIC_EPSILON,
        source_roles=("control_command", "actuator_state", "actuator_feedback"), observed_domain="continuous",
        manual_review_required=True, metadata_confidence_policy="sufficient_under_frozen_metadata_policy",
        finite_nonconstant_repeated_changes_all_fit_and_calibration_required=True, setpoints_excluded=True,
        discrete_sources_routed_to_family=False, data_behavior_grants_control_semantics=False,
        official_graph_grants_source_eligibility=False, cross_file_or_split_events_allowed=False,
        candidate_fit_files=("hai-train1.csv", "hai-train2.csv"), source_noise_scale_formula="max(1.4826*MAD(dx),numeric_epsilon)",
        pre_level_formula="median(x[t-5:t])", post_level_formula="median(x[t:t+5])", step_amplitude_formula="post_level-pre_level",
        minimum_nontrivial_amplitudes=20, q75_method="linear_interpolation_index_0.75_times_n_minus_1",
        source_step_threshold_formula="max(5*source_noise_scale,Q75(A_positive))",
        source_stability_tolerance_formula="max(3*source_noise_scale,0.10*source_step_threshold)",
        cluster_retention_policy="largest_absolute_amplitude_within_10_seconds", exact_amplitude_tie_policy="earliest_timestamp",
        directions_retained_separately=True, calibration_or_target_feedback_used=False, final_rule_parameter_authority=False, creation_metadata=metadata,
    )
    response = ContinuousStepResponsePolicyV1(
        target_observed_domain="continuous", target_pre_window_seconds=5, target_response_window_seconds=3, response_horizons_seconds=(1, 5, 10, 30, 60),
        target_baseline_formula="median(y[t-5:t])", target_response_formula="median(y[t+h:t+h+3])-target_baseline",
        target_noise_scale_formula="max(1.4826*MAD(one_step_target_changes),numeric_epsilon)", target_noise_fit_role="normal_candidate_fit",
        increase_evidence_rule="target_response>target_noise_scale", decrease_evidence_rule="target_response<-target_noise_scale",
        right_censor_incomplete_windows=True, preserve_response_direction=True, absolute_response_only_prohibited=True, creation_metadata=metadata,
    )
    feasibility = ContinuousStepFeasibilityPolicyV1(
        candidate_fit_files=("hai-train1.csv", "hai-train2.csv"), calibration_file="hai-train3.csv", normal_guard_values_prohibited=True,
        screening_dimensions=("source", "source_step_direction", "target", "target_response_direction", "response_horizon"),
        required_aggregate_statistics=("usable_isolated_event_count", "right_censored_count", "median_target_response", "directional_consistency", "robust_effect_ratio", "per_file_support"),
        ranking_order=("highest_directional_consistency", "highest_robust_effect_ratio", "shortest_horizon", "lexicographic_exact_tie_only"),
        fit_total_isolated_events_minimum=20, fit_per_file_isolated_events_minimum=5, fit_directional_consistency_minimum=0.70,
        fit_per_file_directional_consistency_minimum=0.60, fit_robust_effect_ratio_minimum=2.0, fit_direction_agreement_required=True,
        calibration_isolated_events_minimum=5, calibration_directional_consistency_minimum=0.60, calibration_robust_effect_ratio_minimum=1.0,
        frozen_fit_fields_on_calibration=("source_step_threshold", "source_stability_tolerance", "target_response_direction", "response_horizon"),
        multiple_horizons_do_not_inflate_pairs=True, unconditioned_screening_feasibility_only=True, final_operating_regime_binding_required=True,
        weighted_score_used=False, real_data_executed=False, creation_metadata=metadata,
    )
    selection = ContinuousStepProcessSelectionPolicyV1(
        compared_processes=("P1", "P3"), source_threshold_count_minimum=2, eligible_target_count_minimum=3,
        confirmed_directional_pair_count_minimum=3, distinct_confirmed_source_count_minimum=2, distinct_confirmed_target_count_minimum=2,
        transfer_rate_minimum=0.50, required_fit_files=("hai-train1.csv", "hai-train2.csv"), required_calibration_file="hai-train3.csv",
        normal_guard_values_prohibited=True, prohibited_access_count_maximum=0, maximize_metrics=_MAXIMIZE_PROCESS_METRICS,
        minimize_metrics=_MINIMIZE_PROCESS_METRICS, strict_improvement_metric_minimum=2, weighted_score_used=False,
        prohibited_selection_bases=("total_variable_count", "BR0_candidate_count", "official_graph_availability", "attack_count", "detector_performance", "implementation_convenience", "process_identifier"),
        neither_feasible_status="blocked_no_feasible_continuous_step_process", non_dominance_status="blocked_continuous_process_selection_indeterminate", creation_metadata=metadata,
    )
    unsupported = ContinuousStepUnsupportedPolicyV1(
        source_event_statuses=tuple(item.value for item in SourceEventStatusV1), source_target_statuses=tuple(item.value for item in ScreeningStatusV1),
        process_outcomes=tuple(item.value for item in ProcessOutcomeV1),
        future_runtime_abstention_reasons=("insufficient_pre_window", "incomplete_post_hold_window", "incomplete_target_response_window", "nonfinite_source_window", "nonfinite_target_window", "outside_authorized_operating_regime", "file_or_split_boundary"),
        invalid_rule_is_abstention=False, parameter_binding_failure_is_abstention=False, isolation_is_runtime_abstention_rule=False, no_rule_created_in_br1=False, creation_metadata=metadata,
    )
    provenance = ContinuousStepParameterProvenancePolicyV1(
        parameter_classes=("feasibility_screening", "final_calibration", "runtime"), screening_implicit_promotion_prohibited=True,
        final_recalibration_task="TASK-039D_or_versioned_successor", deterministic_project_artifacts_required=True,
        agent_allowed_actions=("select_approved_parameter_reference", "select_supported_directional_relation", "select_closed_relation_family", "request_verifier_guided_repair", "return_no_rule"),
        agent_prohibited_actions=("invent_source_step_threshold", "invent_stability_tolerance", "invent_lag", "invent_target_response_threshold", "rewrite_parameter_value", "choose_number_from_raw_samples", "use_labels_or_test_performance"),
        labels_or_test_performance_used=False, agent_number_authority=False, creation_metadata=metadata,
    )
    rule_plan = ContinuousStepRuleMigrationPlanV1(
        plan_status="migration_plan_only", additive_version_required=True,
        trigger_fields=("trigger_type=sustained_continuous_step", "variable", "step_direction", "step_threshold_parameter_ref", "pre_window_parameter_ref", "post_hold_parameter_ref", "stability_tolerance_parameter_ref", "refractory_parameter_ref"),
        expected_effect_fields=("effect_type=delayed_change", "direction", "target_variables=exactly_one", "response_threshold_parameter_ref", "lag_parameter_ref", "response_window_parameter_ref"),
        preserved_contracts=("one_source", "one_target", "missing_expected_response", "binary_anomaly", "abstention", "normal_reference_binding", "evidence_binding", "graph_edge_binding", "complexity_limit", "review_history", "deterministic_verifier_authority", "llm_free_runtime"),
        rule_v1_modified=False, rule_v2_created=False, route_continuous_rules_through_rule_v1=False, independent_schema_and_parser_required=True,
        task032_hash_preservation_required=True, creation_metadata=metadata,
    )
    verifier_plan = ContinuousStepVerifierMigrationPlanV1(
        plan_status="migration_plan_only",
        ordered_future_checks=("schema_and_version", "source_and_target_cardinality", "documented_continuous_source_semantics", "trigger_type", "explicit_source_step_direction", "complete_trigger_parameter_references", "source_parameter_provenance", "fit_only_source_threshold_derivation", "no_calibration_guard_test_trigger_influence", "target_response_direction", "target_parameter_provenance", "lag_and_response_window_consistency", "evidence_and_graph_binding", "normal_reference_binding", "normal_only_construction_evidence", "prohibited_causal_claims", "complexity", "abstention_policy", "no_validity_or_runtime_preclaim", "accepted_rule_hash_binding"),
        validity_excludes=("normal_false_fire_assessment", "inner_utility", "detector_FN_recovery", "deployment_selection"), verifier_v1_modified=False, implementation_created=False, creation_metadata=metadata,
    )
    runtime_plan = ContinuousStepRuntimeMigrationPlanV1(
        plan_status="migration_plan_only",
        required_trace_fields=("source_variable", "source_step_direction", "pre_level_aggregate", "post_level_aggregate", "observed_step_amplitude", "step_threshold_parameter_reference", "step_threshold", "stability_result", "event_time", "target_variable", "expected_target_direction", "lag_window", "observed_target_response", "response_threshold_parameter_reference", "response_threshold", "violation_result", "abstention_reason"),
        abstention_reasons=unsupported.future_runtime_abstention_reasons, deterministic_trace_required=True, llm_free_runtime_required=True,
        explanation_prohibited_inventions=("causes", "attack_identities", "hidden_physical_mechanisms", "unsupported_variables", "unobserved_numeric_values"),
        runtime_v1_modified=False, runtime_implementation_created=False, rule_execution_performed=False, creation_metadata=metadata,
    )
    return ContinuousStepProtocolBundleV1(
        task_id="TASK-039BR1", status="passed_continuous_step_relation_protocol_freeze", br0_commit=BR0_COMMIT,
        br0_decision_hash=BR0_DECISION_HASH, br0_readiness_hash=BR0_READINESS_HASH, relation_family=relation,
        trigger_policy=trigger, response_policy=response, feasibility_policy=feasibility, process_selection_policy=selection,
        unsupported_policy=unsupported, parameter_provenance_policy=provenance, rule_migration_plan=rule_plan,
        verifier_migration_plan=verifier_plan, runtime_migration_plan=runtime_plan, validity_authority_granted=False,
        runtime_authority_granted=False, process_selection_granted=False, process_selected=False,
        task039c_authorized=False, real_data_accessed=False,
        next_task="TASK-039BR2", creation_metadata=metadata,
    )


__all__ = [
    "BR0_COMMIT", "BR0_DECISION_HASH", "BR0_READINESS_HASH", "ContinuousStepFeasibilityPolicyV1",
    "ContinuousStepParameterProvenancePolicyV1", "ContinuousStepProcessSelectionPolicyV1",
    "ContinuousStepProtocolBundleV1", "ContinuousStepProtocolError", "ContinuousStepRelationFamilyV1",
    "ContinuousStepResponsePolicyV1", "ContinuousStepRuleMigrationPlanV1", "ContinuousStepRuntimeMigrationPlanV1",
    "ContinuousStepTriggerPolicyV1", "ContinuousStepUnsupportedPolicyV1", "ContinuousStepVerifierMigrationPlanV1",
    "ProcessOutcomeV1", "ScreeningStatusV1", "SourceEventStatusV1", "StepDirectionV1", "TargetDirectionV1",
    "build_default_protocol_bundle_v1", "calibration_confirmation_gate_v1", "classify_event_isolation_v1",
    "cluster_step_events_v1", "default_protocol_config_content_v1", "derive_source_screening_parameters_v1",
    "evaluate_step_candidate_v1", "evaluate_target_response_v1", "extract_sustained_step_events_v1",
    "fit_support_gate_v1", "process_feasibility_gate_v1", "robust_one_step_scale_v1", "select_process_v1",
]
