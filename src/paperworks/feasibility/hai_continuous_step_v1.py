"""TASK-039BR2 normal-only continuous-step feasibility execution.

The module binds the frozen BR0 eligibility ledgers to the BR1 protocol.  It
keeps calculations file-local, derives every screening scale from train1 and
train2 only, applies train3 without retuning, and exposes only aggregate public
records.  It does not create rules, parameters with runtime authority, or
detector evidence.
"""

from __future__ import annotations

import csv
import bisect
import json
import math
import statistics
from dataclasses import dataclass, fields
from enum import Enum
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar, Mapping, NamedTuple, Sequence, TypeVar

from paperworks.data.contracts_v2 import (
    AggregationDescriptionV2,
    CreationMetadataV2,
    DataViewKindV2,
    DataViewManifestV2,
    DatasetManifestV2,
    ProvenanceStatusV2,
    RawRangeV2,
    SealedAccessStatusV2,
    SplitManifestV2,
    SplitRoleV2,
)
from paperworks.data.hai_provenance_v1 import streaming_sha256
from paperworks.data.splits_v2 import validate_split_collection_v2
from paperworks.v6.common import (
    CreationMetadataV1,
    V6_FOUNDATION_SCHEMA_VERSION,
    freeze_json,
    reject_unknown_fields,
    require_finite,
    require_sha256,
    stable_hash_v1,
    thaw_json,
)
from paperworks.v6.continuous_step_protocol_v1 import (
    FAMILY_ID,
    SourceEventStatusV1,
    SustainedStepEventV1,
    TargetResponseEvaluationV1,
    calibration_confirmation_gate_v1,
    cluster_step_events_v1,
    fit_support_gate_v1,
    process_feasibility_gate_v1,
    select_process_v1,
)


SCHEMA_VERSION = V6_FOUNDATION_SCHEMA_VERSION
DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
TASK039A_PROVENANCE_HASH = "f1d16091935a264b4e81ed73a2f984b49360e3ff86d404ba3029de539c20c4ef"
TASK039AR_EQUIVALENCE_HASH = "7917f8736c119e774a945096f41f8abc18bce30267dd9e754c5a20157a5bf7a8"
BR0_DECISION_HASH = "3eceafb47742af9fc1be5dba82f148d33e31ba3095ba4b8a2d513ab9d4632a7b"
BR0_READINESS_HASH = "c1968c53d605756cd9d16f72306c730fcf6a9b3ceaf61368eba78157bb84f7a2"
BR0_SOURCE_LEDGER_HASH = "3df659ddfa0971933643f54aa203b207679ec0bedc4ed3b58268ce9cd7b52d4a"
BR0_MORPHOLOGY_LEDGER_HASH = "3cef789579ca54b4b829a381db7763feb3b1c4ee5b53e6ca61015f5d5aec25a3"
BR1_PROTOCOL_BUNDLE_HASH = "5e57e1103b95d8cb24bf55f9ff85a989773dbe05816479dc79c493de044a7bbd"
BR1_CONFIG_HASH = "8a82c7fc0924cd4bc40c83e783eb51f43edf8b0a3ac3948bf4042b93e5370573"

FIT_FILES = ("hai-23.05/hai-train1.csv", "hai-23.05/hai-train2.csv")
CALIBRATION_FILE = "hai-23.05/hai-train3.csv"
NORMAL_GUARD_FILE = "hai-23.05/hai-train4.csv"
FIT_FILE_NAMES = ("hai-train1.csv", "hai-train2.csv")
CALIBRATION_FILE_NAME = "hai-train3.csv"
AUTHORIZED_VALUE_FILES = FIT_FILES + (CALIBRATION_FILE,)
ALL_NORMAL_FILES = AUTHORIZED_VALUE_FILES + (NORMAL_GUARD_FILE,)
RESPONSE_HORIZONS = (1, 5, 10, 30, 60)
APPROVED_SOURCE_ROLES = frozenset(
    {"control_command", "actuator_state", "actuator_feedback"}
)
_PROHIBITED_PATH_TOKENS = (
    "hai-test",
    "label-test",
    "summary_label",
    "custody",
    "attack",
    "private_argos",
)


class HAIContinuousStepError(ValueError):
    """Raised when BR2 execution violates a frozen contract or data boundary."""


class SourceScreeningStatusV1(str, Enum):
    SUPPORTED = "supported"
    INSUFFICIENT_NONTRIVIAL_AMPLITUDES = "insufficient_nontrivial_amplitudes"
    INVALID_SOURCE = "invalid_source"


class TargetScaleStatusV1(str, Enum):
    SUPPORTED = "supported"
    INVALID_TARGET = "invalid_target"


class DirectionalFitStatusV1(str, Enum):
    FIT_SUPPORTED = "fit_supported"
    FIT_UNSUPPORTED = "fit_unsupported"
    DIRECTION_UNSTABLE = "direction_unstable"
    INVALID_TARGET = "invalid_target"


class ConfirmationStatusV1(str, Enum):
    CALIBRATION_CONFIRMED = "calibration_confirmed"
    CALIBRATION_CONFLICT = "calibration_conflict"


def _json_value(value: Any) -> Any:
    if isinstance(value, (CreationMetadataV1, CreationMetadataV2)):
        return value.to_dict()
    if isinstance(value, _ExecutionArtifact):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


ArtifactT = TypeVar("ArtifactT", bound="_ExecutionArtifact")


class _ExecutionArtifact:
    ARTIFACT_TYPE: ClassVar[str]
    TUPLE_FIELDS: ClassVar[frozenset[str]] = frozenset()
    MAPPING_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def _validate_identity(self) -> None:
        if getattr(self, "schema_version") != SCHEMA_VERSION:
            raise HAIContinuousStepError("schema_version must be 1.0.0")
        if getattr(self, "artifact_type") != self.ARTIFACT_TYPE:
            raise HAIContinuousStepError("artifact_type does not match contract")

    def _content_dict(self) -> dict[str, Any]:
        return {item.name: _json_value(getattr(self, item.name)) for item in fields(self)}

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
        except ValueError as exc:
            raise HAIContinuousStepError(str(exc)) from exc
        kwargs = {item.name: data[item.name] for item in fields(cls)}
        for name in cls.TUPLE_FIELDS:
            kwargs[name] = tuple(kwargs[name])
        for name in cls.MAPPING_FIELDS:
            kwargs[name] = dict(kwargs[name])
        if "creation_metadata" in kwargs:
            kwargs["creation_metadata"] = CreationMetadataV1.from_dict(
                kwargs["creation_metadata"]
            )
        result = cls(**kwargs)
        if data.get("artifact_hash") not in {None, result.artifact_hash}:
            raise HAIContinuousStepError("artifact_hash does not match content")
        return result


def _require_process(process_id: str) -> None:
    if process_id not in {"P1", "P3"}:
        raise HAIContinuousStepError("process_id must be P1 or P3")


def _require_nonnegative(value: int, field_name: str) -> None:
    if isinstance(value, bool) or int(value) < 0:
        raise HAIContinuousStepError(f"{field_name} must be non-negative")


def _require_ratio(value: float, field_name: str) -> None:
    number = require_finite(value, field_name)
    if not 0.0 <= number <= 1.0:
        raise HAIContinuousStepError(f"{field_name} must be in [0, 1]")


@dataclass(frozen=True)
class ContinuousSourceScreeningRecordV1(_ExecutionArtifact):
    process_id: str
    variable_name: str
    metadata_record_hash: str
    morphology_record_hash: str
    fit_files: tuple[str, ...]
    source_noise_scale: float | None
    nontrivial_amplitude_count: int
    source_step_threshold: float | None
    source_stability_tolerance: float | None
    q75_method: str
    status: str
    parameter_class: str
    fit_only: bool
    calibration_or_target_feedback_used: bool
    final_parameter_authority: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "continuous_source_screening_record_v1"

    ARTIFACT_TYPE = "continuous_source_screening_record_v1"
    TUPLE_FIELDS = frozenset({"fit_files"})

    def __post_init__(self) -> None:
        self._validate_identity()
        _require_process(self.process_id)
        if not self.variable_name.startswith(f"{self.process_id}_"):
            raise HAIContinuousStepError("source variable is outside process scope")
        require_sha256(self.metadata_record_hash, "metadata_record_hash")
        require_sha256(self.morphology_record_hash, "morphology_record_hash")
        if self.fit_files != FIT_FILES:
            raise HAIContinuousStepError("source scale must use train1 and train2")
        _require_nonnegative(self.nontrivial_amplitude_count, "nontrivial_amplitude_count")
        if self.q75_method != "linear_interpolation_index_0.75_times_n_minus_1":
            raise HAIContinuousStepError("Q75 method changed")
        if self.status not in {item.value for item in SourceScreeningStatusV1}:
            raise HAIContinuousStepError("unknown source screening status")
        supported = self.status == SourceScreeningStatusV1.SUPPORTED.value
        values = (
            self.source_noise_scale,
            self.source_step_threshold,
            self.source_stability_tolerance,
        )
        if supported:
            if any(value is None or require_finite(value, "source parameter") <= 0 for value in values):
                raise HAIContinuousStepError("supported source requires positive parameters")
            if self.nontrivial_amplitude_count < 20:
                raise HAIContinuousStepError("supported source requires 20 amplitudes")
        elif any(value is not None for value in values[1:]):
            raise HAIContinuousStepError("unsupported source cannot expose a threshold")
        if (
            self.parameter_class != "feasibility_screening"
            or not self.fit_only
            or self.calibration_or_target_feedback_used
            or self.final_parameter_authority
        ):
            raise HAIContinuousStepError("source parameter authority boundary changed")


@dataclass(frozen=True)
class ContinuousSourceEventSummaryV1(_ExecutionArtifact):
    process_id: str
    source_variable: str
    source_screening_ref: str
    relative_file: str
    step_direction: str
    total_clustered_events: int
    isolated_events: int
    non_isolated_events: int
    isolation_ratio: float
    event_indices_publicly_exposed: bool
    raw_values_included: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "continuous_source_event_summary_v1"

    ARTIFACT_TYPE = "continuous_source_event_summary_v1"

    def __post_init__(self) -> None:
        self._validate_identity()
        _require_process(self.process_id)
        require_sha256(self.source_screening_ref, "source_screening_ref")
        if self.relative_file not in AUTHORIZED_VALUE_FILES:
            raise HAIContinuousStepError("event summary uses unauthorized file")
        if self.step_direction not in {"step_up", "step_down"}:
            raise HAIContinuousStepError("step direction must be explicit")
        for name in ("total_clustered_events", "isolated_events", "non_isolated_events"):
            _require_nonnegative(getattr(self, name), name)
        if self.total_clustered_events != self.isolated_events + self.non_isolated_events:
            raise HAIContinuousStepError("event counts are inconsistent")
        _require_ratio(self.isolation_ratio, "isolation_ratio")
        expected = self.isolated_events / self.total_clustered_events if self.total_clustered_events else 0.0
        if not math.isclose(self.isolation_ratio, expected, rel_tol=0.0, abs_tol=1e-15):
            raise HAIContinuousStepError("isolation ratio is inconsistent")
        if self.event_indices_publicly_exposed or self.raw_values_included:
            raise HAIContinuousStepError("public event summary crossed its boundary")


@dataclass(frozen=True)
class ContinuousTargetScaleRecordV1(_ExecutionArtifact):
    process_id: str
    target_variable: str
    metadata_record_hash: str
    fit_files: tuple[str, ...]
    target_noise_scale: float | None
    status: str
    parameter_class: str
    fit_only: bool
    calibration_values_used: bool
    final_parameter_authority: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "continuous_target_scale_record_v1"

    ARTIFACT_TYPE = "continuous_target_scale_record_v1"
    TUPLE_FIELDS = frozenset({"fit_files"})

    def __post_init__(self) -> None:
        self._validate_identity()
        _require_process(self.process_id)
        require_sha256(self.metadata_record_hash, "metadata_record_hash")
        if self.fit_files != FIT_FILES:
            raise HAIContinuousStepError("target scale must use train1 and train2")
        if self.status not in {item.value for item in TargetScaleStatusV1}:
            raise HAIContinuousStepError("unknown target-scale status")
        if self.status == TargetScaleStatusV1.SUPPORTED.value:
            if self.target_noise_scale is None or require_finite(self.target_noise_scale, "target_noise_scale") <= 0:
                raise HAIContinuousStepError("supported target requires a positive scale")
        elif self.target_noise_scale is not None:
            raise HAIContinuousStepError("invalid target cannot expose a scale")
        if (
            self.parameter_class != "feasibility_screening"
            or not self.fit_only
            or self.calibration_values_used
            or self.final_parameter_authority
        ):
            raise HAIContinuousStepError("target scale authority boundary changed")


@dataclass(frozen=True)
class ContinuousDirectionalFitRecordV1(_ExecutionArtifact):
    process_id: str
    source_variable: str
    source_step_direction: str
    target_variable: str
    target_response_direction: str | None
    selected_horizon_seconds: int | None
    train1_usable_isolated_events: int
    train2_usable_isolated_events: int
    pooled_usable_isolated_events: int
    train1_right_censored: int
    train2_right_censored: int
    train1_directional_consistency: float
    train2_directional_consistency: float
    pooled_directional_consistency: float
    pooled_median_target_response: float
    pooled_robust_effect_ratio: float
    direction_agrees_across_files: bool
    selected_by_frozen_ranking: bool
    lower_ranked_fallback_used: bool
    status: str
    source_screening_ref: str
    target_scale_ref: str
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "continuous_directional_fit_record_v1"

    ARTIFACT_TYPE = "continuous_directional_fit_record_v1"

    def __post_init__(self) -> None:
        self._validate_identity()
        _require_process(self.process_id)
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise HAIContinuousStepError("source step direction is invalid")
        if self.target_response_direction not in {None, "increase", "decrease"}:
            raise HAIContinuousStepError("target direction is invalid")
        if self.selected_horizon_seconds not in {None, *RESPONSE_HORIZONS}:
            raise HAIContinuousStepError("selected horizon is invalid")
        if (self.target_response_direction is None) != (self.selected_horizon_seconds is None):
            raise HAIContinuousStepError("direction and horizon must both be selected or absent")
        for name in (
            "train1_usable_isolated_events",
            "train2_usable_isolated_events",
            "pooled_usable_isolated_events",
            "train1_right_censored",
            "train2_right_censored",
        ):
            _require_nonnegative(getattr(self, name), name)
        if self.pooled_usable_isolated_events != self.train1_usable_isolated_events + self.train2_usable_isolated_events:
            raise HAIContinuousStepError("pooled fit support is inconsistent")
        for name in (
            "train1_directional_consistency",
            "train2_directional_consistency",
            "pooled_directional_consistency",
        ):
            _require_ratio(getattr(self, name), name)
        require_finite(self.pooled_median_target_response, "pooled_median_target_response")
        if require_finite(self.pooled_robust_effect_ratio, "pooled_robust_effect_ratio") < 0:
            raise HAIContinuousStepError("robust effect ratio must be non-negative")
        if self.status not in {item.value for item in DirectionalFitStatusV1}:
            raise HAIContinuousStepError("unknown fit status")
        if self.lower_ranked_fallback_used:
            raise HAIContinuousStepError("lower-ranked fallback is prohibited")
        require_sha256(self.source_screening_ref, "source_screening_ref")
        require_sha256(self.target_scale_ref, "target_scale_ref")


@dataclass(frozen=True)
class ContinuousCalibrationConfirmationRecordV1(_ExecutionArtifact):
    process_id: str
    fit_record_ref: str
    source_variable: str
    source_step_direction: str
    target_variable: str
    target_response_direction: str
    selected_horizon_seconds: int
    train3_usable_isolated_events: int
    train3_right_censored: int
    train3_directional_consistency: float
    train3_opposite_direction_consistency: float
    train3_robust_effect_ratio: float
    target_direction_unchanged: bool
    fit_parameters_reused_without_retuning: bool
    source_threshold_ref: str
    target_scale_ref: str
    status: str
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "continuous_calibration_confirmation_record_v1"

    ARTIFACT_TYPE = "continuous_calibration_confirmation_record_v1"

    def __post_init__(self) -> None:
        self._validate_identity()
        _require_process(self.process_id)
        for name in ("fit_record_ref", "source_threshold_ref", "target_scale_ref"):
            require_sha256(getattr(self, name), name)
        if self.source_step_direction not in {"step_up", "step_down"}:
            raise HAIContinuousStepError("source step direction is invalid")
        if self.target_response_direction not in {"increase", "decrease"}:
            raise HAIContinuousStepError("target direction is invalid")
        if self.selected_horizon_seconds not in RESPONSE_HORIZONS:
            raise HAIContinuousStepError("selected horizon is invalid")
        _require_nonnegative(self.train3_usable_isolated_events, "train3_usable_isolated_events")
        _require_nonnegative(self.train3_right_censored, "train3_right_censored")
        _require_ratio(self.train3_directional_consistency, "train3_directional_consistency")
        _require_ratio(self.train3_opposite_direction_consistency, "train3_opposite_direction_consistency")
        if require_finite(self.train3_robust_effect_ratio, "train3_robust_effect_ratio") < 0:
            raise HAIContinuousStepError("train3 robust effect ratio must be non-negative")
        if self.status not in {item.value for item in ConfirmationStatusV1}:
            raise HAIContinuousStepError("unknown confirmation status")
        if not self.fit_parameters_reused_without_retuning:
            raise HAIContinuousStepError("train3 parameter retuning is prohibited")


@dataclass(frozen=True)
class HAIContinuousProcessFeasibilityV1(_ExecutionArtifact):
    process_id: str
    process_name: str
    documented_sources_with_valid_fit_thresholds: int
    eligible_continuous_targets: int
    calibration_confirmed_directional_pairs: int
    distinct_confirmed_sources: int
    distinct_confirmed_targets: int
    fit_supported_directional_pairs: int
    fit_to_calibration_transfer_rate: float
    normal_candidate_fit_files: tuple[str, ...]
    normal_relation_calibration_file: str
    normal_guard_feature_values_accessed: bool
    prohibited_data_access_count: int
    median_calibration_isolated_event_support: float
    manual_metadata_coverage: float
    metadata_unresolved_ratio: float
    non_isolated_source_event_ratio: float
    missing_or_nonfinite_rate: float
    source_status_counts: Mapping[str, Any]
    fit_status_counts: Mapping[str, Any]
    calibration_status_counts: Mapping[str, Any]
    private_source_parameter_ledger_hash: str
    private_event_ledger_hash: str
    private_relation_ledger_hash: str
    feasibility_gate_passed: bool
    process_outcome: str
    weighted_score_used: bool
    official_graph_used_for_scoring: bool
    attack_information_used: bool
    raw_values_included: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_continuous_process_feasibility_v1"

    ARTIFACT_TYPE = "hai_continuous_process_feasibility_v1"
    TUPLE_FIELDS = frozenset({"normal_candidate_fit_files"})
    MAPPING_FIELDS = frozenset(
        {"source_status_counts", "fit_status_counts", "calibration_status_counts"}
    )

    def __post_init__(self) -> None:
        self._validate_identity()
        _require_process(self.process_id)
        for name in (
            "documented_sources_with_valid_fit_thresholds",
            "eligible_continuous_targets",
            "calibration_confirmed_directional_pairs",
            "distinct_confirmed_sources",
            "distinct_confirmed_targets",
            "fit_supported_directional_pairs",
            "prohibited_data_access_count",
        ):
            _require_nonnegative(getattr(self, name), name)
        for name in (
            "fit_to_calibration_transfer_rate",
            "manual_metadata_coverage",
            "metadata_unresolved_ratio",
            "non_isolated_source_event_ratio",
            "missing_or_nonfinite_rate",
        ):
            _require_ratio(getattr(self, name), name)
        if require_finite(self.median_calibration_isolated_event_support, "median_calibration_isolated_event_support") < 0:
            raise HAIContinuousStepError("median support must be non-negative")
        if self.normal_candidate_fit_files != FIT_FILE_NAMES or self.normal_relation_calibration_file != CALIBRATION_FILE_NAME:
            raise HAIContinuousStepError("process files do not match the frozen policy")
        for name in (
            "private_source_parameter_ledger_hash",
            "private_event_ledger_hash",
            "private_relation_ledger_hash",
        ):
            require_sha256(getattr(self, name), name)
        for name in self.MAPPING_FIELDS:
            object.__setattr__(self, name, freeze_json(getattr(self, name)))
        expected_gate = process_feasibility_gate_v1(self.metric_mapping())
        if expected_gate != self.feasibility_gate_passed:
            raise HAIContinuousStepError("process feasibility gate was not applied exactly")
        if self.process_outcome != ("feasible" if expected_gate else "infeasible"):
            raise HAIContinuousStepError("process outcome is inconsistent")
        if self.weighted_score_used or self.official_graph_used_for_scoring or self.attack_information_used or self.raw_values_included:
            raise HAIContinuousStepError("process feasibility crossed a claim boundary")

    def metric_mapping(self) -> dict[str, Any]:
        return {
            "documented_sources_with_valid_fit_thresholds": self.documented_sources_with_valid_fit_thresholds,
            "eligible_continuous_targets": self.eligible_continuous_targets,
            "calibration_confirmed_directional_pairs": self.calibration_confirmed_directional_pairs,
            "distinct_confirmed_sources": self.distinct_confirmed_sources,
            "distinct_confirmed_targets": self.distinct_confirmed_targets,
            "fit_to_calibration_transfer_rate": self.fit_to_calibration_transfer_rate,
            "normal_candidate_fit_files": self.normal_candidate_fit_files,
            "normal_relation_calibration_file": self.normal_relation_calibration_file,
            "normal_guard_feature_values_accessed": self.normal_guard_feature_values_accessed,
            "prohibited_data_access_count": self.prohibited_data_access_count,
            "median_calibration_isolated_event_support": self.median_calibration_isolated_event_support,
            "manual_metadata_coverage": self.manual_metadata_coverage,
            "metadata_unresolved_ratio": self.metadata_unresolved_ratio,
            "non_isolated_source_event_ratio": self.non_isolated_source_event_ratio,
            "missing_or_nonfinite_rate": self.missing_or_nonfinite_rate,
        }


@dataclass(frozen=True)
class HAIContinuousProcessSelectionResultV1(_ExecutionArtifact):
    selection_status: str
    selected_process_id: str | None
    excluded_process_id: str | None
    selection_reason: str
    p1_feasibility_report_hash: str
    p3_feasibility_report_hash: str
    selection_policy_hash: str
    pareto_metrics: Mapping[str, Any]
    weighted_score_used: bool
    process_selected: bool
    task039c_authorized: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_continuous_process_selection_result_v1"

    ARTIFACT_TYPE = "hai_continuous_process_selection_result_v1"
    MAPPING_FIELDS = frozenset({"pareto_metrics"})

    def __post_init__(self) -> None:
        self._validate_identity()
        for name in ("p1_feasibility_report_hash", "p3_feasibility_report_hash", "selection_policy_hash"):
            require_sha256(getattr(self, name), name)
        if self.selection_status not in {
            "selected",
            "blocked_no_feasible_continuous_step_process",
            "blocked_continuous_process_selection_indeterminate",
        }:
            raise HAIContinuousStepError("selection status is invalid")
        selected = self.selection_status == "selected"
        if selected:
            _require_process(str(self.selected_process_id))
            if self.excluded_process_id not in {"P1", "P3"} or self.excluded_process_id == self.selected_process_id:
                raise HAIContinuousStepError("selected and excluded processes are invalid")
        elif self.selected_process_id is not None or self.excluded_process_id is not None:
            raise HAIContinuousStepError("blocked selection cannot name a process")
        if self.process_selected != selected or self.task039c_authorized != selected:
            raise HAIContinuousStepError("selection authority boundary is inconsistent")
        if self.weighted_score_used:
            raise HAIContinuousStepError("weighted process score is prohibited")
        object.__setattr__(self, "pareto_metrics", freeze_json(self.pareto_metrics))


@dataclass(frozen=True)
class HAIContinuousProcessFreezeV1(_ExecutionArtifact):
    dataset_manifest_id: str
    br0_decision_hash: str
    br1_protocol_bundle_hash: str
    execution_code_commit: str
    selected_process_id: str
    selected_process_name: str
    excluded_process_id: str
    selection_reason: str
    selection_policy_hash: str
    p1_feasibility_report_hash: str
    p3_feasibility_report_hash: str
    selected_private_relation_ledger_hash: str
    selected_source_parameter_ledger_hash: str
    normal_candidate_fit_split_id: str
    normal_relation_calibration_split_id: str
    normal_guard_split_id: str
    canonical_rule_view_id: str
    candidate_learning_view_id: str
    gdn_view_status: str
    rule_v2_status: str
    task039c_authorized: bool
    claim_boundary: tuple[str, ...]
    validity_authority_granted: bool
    runtime_authority_granted: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "hai_continuous_process_freeze_v1"

    ARTIFACT_TYPE = "hai_continuous_process_freeze_v1"
    TUPLE_FIELDS = frozenset({"claim_boundary"})

    def __post_init__(self) -> None:
        self._validate_identity()
        _require_process(self.selected_process_id)
        if self.excluded_process_id not in {"P1", "P3"} or self.excluded_process_id == self.selected_process_id:
            raise HAIContinuousStepError("process freeze is not single-process")
        for name in (
            "dataset_manifest_id",
            "br0_decision_hash",
            "br1_protocol_bundle_hash",
            "selection_policy_hash",
            "p1_feasibility_report_hash",
            "p3_feasibility_report_hash",
            "selected_private_relation_ledger_hash",
            "selected_source_parameter_ledger_hash",
            "normal_candidate_fit_split_id",
            "normal_relation_calibration_split_id",
            "normal_guard_split_id",
            "canonical_rule_view_id",
            "candidate_learning_view_id",
        ):
            require_sha256(getattr(self, name), name)
        if self.dataset_manifest_id != DATASET_MANIFEST_ID or self.br0_decision_hash != BR0_DECISION_HASH or self.br1_protocol_bundle_hash != BR1_PROTOCOL_BUNDLE_HASH:
            raise HAIContinuousStepError("process freeze lineage mismatch")
        if self.gdn_view_status != "pending_production_backend" or self.rule_v2_status != "not_created":
            raise HAIContinuousStepError("process freeze overclaims implementation readiness")
        if not self.task039c_authorized or self.validity_authority_granted or self.runtime_authority_granted:
            raise HAIContinuousStepError("process freeze authority boundary is invalid")


@dataclass(frozen=True)
class TASK039BR2ExecutionInterpretationV1(_ExecutionArtifact):
    br1_protocol_bundle_hash: str
    relation_family: str
    direction_agreement_rule: str
    exact_directional_tie_rejected: bool
    ranking_order: tuple[str, ...]
    lower_ranked_fallback_prohibited: bool
    file_local_calculation_required: bool
    train3_retuning_prohibited: bool
    material_ambiguities_remaining: tuple[str, ...]
    real_data_accessed_when_frozen: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "task039br2_execution_interpretation_v1"

    ARTIFACT_TYPE = "task039br2_execution_interpretation_v1"
    TUPLE_FIELDS = frozenset({"ranking_order", "material_ambiguities_remaining"})

    def __post_init__(self) -> None:
        self._validate_identity()
        if self.br1_protocol_bundle_hash != BR1_PROTOCOL_BUNDLE_HASH or self.relation_family != FAMILY_ID:
            raise HAIContinuousStepError("execution interpretation lineage mismatch")
        if self.direction_agreement_rule != "selected_consistency_strictly_greater_than_opposite_in_train1_and_train2":
            raise HAIContinuousStepError("direction-agreement interpretation changed")
        if not all(
            (
                self.exact_directional_tie_rejected,
                self.lower_ranked_fallback_prohibited,
                self.file_local_calculation_required,
                self.train3_retuning_prohibited,
            )
        ):
            raise HAIContinuousStepError("execution interpretation weakened")
        if self.material_ambiguities_remaining or self.real_data_accessed_when_frozen:
            raise HAIContinuousStepError("execution interpretation was not frozen before data")


@dataclass(frozen=True)
class TASK039BR2DataAccessAuditV1(_ExecutionArtifact):
    authorized_feature_value_files: tuple[str, ...]
    opened_feature_value_files: tuple[str, ...]
    authorized_process_columns_hash: str
    test_feature_values_accessed: bool
    label_values_accessed: bool
    attack_summary_accessed: bool
    private_custody_accessed: bool
    normal_guard_feature_values_accessed: bool
    p2_p4_feature_values_accessed: bool
    prohibited_data_access_count: int
    raw_rows_persisted: bool
    raw_windows_persisted: bool
    event_timestamps_publicly_exposed: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "task039br2_data_access_audit_v1"

    ARTIFACT_TYPE = "task039br2_data_access_audit_v1"
    TUPLE_FIELDS = frozenset({"authorized_feature_value_files", "opened_feature_value_files"})

    def __post_init__(self) -> None:
        self._validate_identity()
        if self.authorized_feature_value_files != AUTHORIZED_VALUE_FILES:
            raise HAIContinuousStepError("authorized value file set changed")
        if tuple(sorted(self.opened_feature_value_files)) != tuple(sorted(AUTHORIZED_VALUE_FILES)):
            raise HAIContinuousStepError("real execution did not use exactly train1-train3")
        require_sha256(self.authorized_process_columns_hash, "authorized_process_columns_hash")
        if any(
            (
                self.test_feature_values_accessed,
                self.label_values_accessed,
                self.attack_summary_accessed,
                self.private_custody_accessed,
                self.normal_guard_feature_values_accessed,
                self.p2_p4_feature_values_accessed,
                self.raw_rows_persisted,
                self.raw_windows_persisted,
                self.event_timestamps_publicly_exposed,
            )
        ) or self.prohibited_data_access_count != 0:
            raise HAIContinuousStepError("data-access boundary was violated")


@dataclass(frozen=True)
class TASK039BR2ExecutionReceiptV1(_ExecutionArtifact):
    task_id: str
    status: str
    execution_code_commit: str
    config_hash: str
    dataset_manifest_id: str
    br0_decision_hash: str
    br0_readiness_hash: str
    br1_protocol_bundle_hash: str
    execution_interpretation_ref: str
    p1_feasibility_ref: str
    p3_feasibility_ref: str
    process_selection_ref: str
    data_access_audit_ref: str
    private_ledger_hashes: tuple[str, ...]
    selected_process_id: str | None
    process_freeze_ref: str | None
    real_data_accessed: bool
    normal_only_data_used: bool
    final_parameters_created: bool
    rule_v2_created: bool
    detector_executed: bool
    provider_calls: int
    agent_calls: int
    task039c_authorized: bool
    creation_metadata: CreationMetadataV1
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "task039br2_execution_receipt_v1"

    ARTIFACT_TYPE = "task039br2_execution_receipt_v1"
    TUPLE_FIELDS = frozenset({"private_ledger_hashes"})

    def __post_init__(self) -> None:
        self._validate_identity()
        if self.task_id != "TASK-039BR2":
            raise HAIContinuousStepError("task receipt identity mismatch")
        if self.status not in {
            "passed_hai_2305_continuous_step_single_process_freeze",
            "blocked_no_feasible_continuous_step_process",
            "blocked_continuous_process_selection_indeterminate",
        }:
            raise HAIContinuousStepError("execution receipt status is invalid")
        for name in (
            "config_hash",
            "dataset_manifest_id",
            "br0_decision_hash",
            "br0_readiness_hash",
            "br1_protocol_bundle_hash",
            "execution_interpretation_ref",
            "p1_feasibility_ref",
            "p3_feasibility_ref",
            "process_selection_ref",
            "data_access_audit_ref",
        ):
            require_sha256(getattr(self, name), name)
        for index, value in enumerate(self.private_ledger_hashes):
            require_sha256(value, f"private_ledger_hashes[{index}]")
        selected = self.status == "passed_hai_2305_continuous_step_single_process_freeze"
        if selected:
            _require_process(str(self.selected_process_id))
            if self.process_freeze_ref is None:
                raise HAIContinuousStepError("passing receipt requires process freeze")
            require_sha256(self.process_freeze_ref, "process_freeze_ref")
        elif self.selected_process_id is not None or self.process_freeze_ref is not None:
            raise HAIContinuousStepError("blocked receipt cannot contain a process freeze")
        if (
            not self.real_data_accessed
            or not self.normal_only_data_used
            or self.final_parameters_created
            or self.rule_v2_created
            or self.detector_executed
            or self.provider_calls != 0
            or self.agent_calls != 0
            or self.task039c_authorized != selected
        ):
            raise HAIContinuousStepError("execution receipt authority boundary is invalid")


class SourceScreeningParametersV1(NamedTuple):
    source_noise_scale: float
    nontrivial_amplitude_count: int
    source_step_threshold: float
    source_stability_tolerance: float


class SourceScreeningDiagnosticsV1(NamedTuple):
    source_noise_scale: float
    nontrivial_amplitude_count: int
    source_step_threshold: float | None
    source_stability_tolerance: float | None


class DirectionCandidateV1(NamedTuple):
    target_direction: str
    horizon_seconds: int
    train1_responses: tuple[float, ...]
    train2_responses: tuple[float, ...]
    train1_right_censored: int
    train2_right_censored: int
    train1_consistency: float
    train2_consistency: float
    pooled_consistency: float
    pooled_median_response: float
    pooled_robust_effect_ratio: float
    direction_agrees: bool


def _finite_values(values: Sequence[float], field_name: str) -> tuple[float, ...]:
    result = tuple(float(item) for item in values)
    if not result or any(not math.isfinite(item) for item in result):
        raise HAIContinuousStepError(f"{field_name} must contain finite values")
    return result


def _mad(values: Sequence[float]) -> float:
    median = float(statistics.median(values))
    return float(statistics.median(abs(item - median) for item in values))


def _q75_linear(values: Sequence[float]) -> float:
    ordered = sorted(float(item) for item in values)
    position = 0.75 * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def derive_multifile_robust_scale_v1(
    file_sequences: Mapping[str, Sequence[float]],
) -> float:
    """Derive a pooled fit scale from within-file differences only."""

    if not file_sequences:
        raise HAIContinuousStepError("at least one file-local sequence is required")
    differences: list[float] = []
    for file_name, values in file_sequences.items():
        sequence = _finite_values(values, file_name)
        differences.extend(right - left for left, right in zip(sequence, sequence[1:]))
    if not differences:
        raise HAIContinuousStepError("file-local sequences are too short")
    return max(1.4826 * _mad(differences), 1e-12)


def derive_multifile_source_screening_parameters_v1(
    file_sequences: Mapping[str, Sequence[float]],
) -> SourceScreeningParametersV1 | None:
    """Derive BR1 source parameters without cross-file windows or differences."""

    diagnostics = derive_multifile_source_screening_diagnostics_v1(file_sequences)
    if diagnostics.source_step_threshold is None:
        return None
    return SourceScreeningParametersV1(
        diagnostics.source_noise_scale,
        diagnostics.nontrivial_amplitude_count,
        diagnostics.source_step_threshold,
        float(diagnostics.source_stability_tolerance),
    )


def derive_multifile_source_screening_diagnostics_v1(
    file_sequences: Mapping[str, Sequence[float]],
) -> SourceScreeningDiagnosticsV1:
    """Return the complete support count even when threshold derivation is unsupported."""

    if tuple(file_sequences) != FIT_FILES:
        raise HAIContinuousStepError("source screening requires ordered train1 and train2")
    scale = derive_multifile_robust_scale_v1(file_sequences)
    amplitudes: list[float] = []
    for file_name, values in file_sequences.items():
        sequence = _finite_values(values, file_name)
        for index in range(5, len(sequence) - 5 + 1):
            pre_level = float(statistics.median(sequence[index - 5 : index]))
            post_level = float(statistics.median(sequence[index : index + 5]))
            amplitude = abs(post_level - pre_level)
            if amplitude > scale:
                amplitudes.append(amplitude)
    if len(amplitudes) < 20:
        return SourceScreeningDiagnosticsV1(scale, len(amplitudes), None, None)
    threshold = max(5.0 * scale, _q75_linear(amplitudes))
    tolerance = max(3.0 * scale, 0.10 * threshold)
    return SourceScreeningDiagnosticsV1(scale, len(amplitudes), threshold, tolerance)


def extract_multifile_events_v1(
    file_sequences: Mapping[str, Sequence[float]],
    *,
    source_step_threshold: float,
    source_stability_tolerance: float,
) -> dict[str, tuple[SustainedStepEventV1, ...]]:
    return {
        file_name: extract_sustained_step_events_file_local_v1(
            values,
            source_step_threshold=source_step_threshold,
            source_stability_tolerance=source_stability_tolerance,
        )
        for file_name, values in file_sequences.items()
    }


def extract_sustained_step_events_file_local_v1(
    values: Sequence[float],
    *,
    source_step_threshold: float,
    source_stability_tolerance: float,
) -> tuple[SustainedStepEventV1, ...]:
    """Apply the BR1 event formula after one bounded sequence validation."""

    sequence = _finite_values(values, "source values")
    threshold = require_finite(source_step_threshold, "source_step_threshold")
    tolerance = require_finite(source_stability_tolerance, "source_stability_tolerance")
    if threshold <= 0 or tolerance < 0:
        raise HAIContinuousStepError("threshold and tolerance must be bounded")
    events: list[SustainedStepEventV1] = []
    for event_index in range(5, len(sequence) - 5 + 1):
        pre = sequence[event_index - 5 : event_index]
        post = sequence[event_index : event_index + 5]
        pre_level = float(statistics.median(pre))
        post_level = float(statistics.median(post))
        amplitude = post_level - pre_level
        if amplitude == 0 or abs(amplitude) < threshold:
            continue
        pre_fraction = sum(abs(item - pre_level) <= tolerance for item in pre) / 5.0
        if pre_fraction < 0.8:
            continue
        post_fraction = sum(abs(item - post_level) <= tolerance for item in post) / 5.0
        if post_fraction < 0.8:
            continue
        events.append(
            SustainedStepEventV1(
                event_index,
                "step_up" if amplitude > 0 else "step_down",
                pre_level,
                post_level,
                amplitude,
                pre_fraction,
                post_fraction,
            )
        )
    return cluster_step_events_v1(events)


def classify_multisource_isolation_v1(
    source_events: Mapping[str, Mapping[str, Sequence[SustainedStepEventV1]]],
) -> dict[str, dict[str, tuple[tuple[SustainedStepEventV1, bool], ...]]]:
    file_names = tuple(next(iter(source_events.values())).keys()) if source_events else ()
    result: dict[str, dict[str, tuple[tuple[SustainedStepEventV1, bool], ...]]] = {
        source: {} for source in source_events
    }
    for file_name in file_names:
        by_source = {source: tuple(files[file_name]) for source, files in source_events.items()}
        indexes = {
            source: tuple(sorted(event.event_index for event in events))
            for source, events in by_source.items()
        }
        for source, events in by_source.items():
            classified: list[tuple[SustainedStepEventV1, bool]] = []
            other_indexes = [
                value
                for other_source, values in indexes.items()
                if other_source != source
                for value in values
            ]
            other_indexes.sort()
            for event in events:
                left = bisect.bisect_left(other_indexes, event.event_index - 2)
                isolated = left == len(other_indexes) or other_indexes[left] > event.event_index + 2
                classified.append((event, isolated))
            result[source][file_name] = tuple(classified)
    return result


def evaluate_target_response_file_local_v1(
    values: Sequence[float],
    *,
    event_index: int,
    horizon_seconds: int,
    target_noise_scale: float,
    target_direction: str,
) -> TargetResponseEvaluationV1:
    """Apply the BR1 target formula without copying the full sequence per event."""

    if horizon_seconds not in RESPONSE_HORIZONS:
        raise HAIContinuousStepError("response horizon is not preregistered")
    if target_direction not in {"increase", "decrease"}:
        raise HAIContinuousStepError("target direction must be explicit")
    if event_index < 5 or event_index + horizon_seconds + 3 > len(values):
        return TargetResponseEvaluationV1(True, None, None)
    noise = require_finite(target_noise_scale, "target_noise_scale")
    if noise <= 0:
        raise HAIContinuousStepError("target_noise_scale must be positive")
    baseline_values = values[event_index - 5 : event_index]
    response_values = values[event_index + horizon_seconds : event_index + horizon_seconds + 3]
    if any(not math.isfinite(float(item)) for item in (*baseline_values, *response_values)):
        raise HAIContinuousStepError("target response window must contain finite values")
    baseline = float(statistics.median(baseline_values))
    response_level = float(statistics.median(response_values))
    response = response_level - baseline
    matches = response > noise if target_direction == "increase" else response < -noise
    return TargetResponseEvaluationV1(False, response, matches)


def direction_agrees_strict_v1(
    *,
    selected_train1: float,
    opposite_train1: float,
    selected_train2: float,
    opposite_train2: float,
) -> bool:
    """Reject equality; selected direction must win in both fit files."""

    return selected_train1 > opposite_train1 and selected_train2 > opposite_train2


def _direction_stats(responses: Sequence[float], noise: float, direction: str) -> tuple[int, float]:
    if direction == "increase":
        matches = sum(item > noise for item in responses)
    elif direction == "decrease":
        matches = sum(item < -noise for item in responses)
    else:
        raise HAIContinuousStepError("target direction is invalid")
    return matches, matches / len(responses) if responses else 0.0


def evaluate_direction_candidate_v1(
    *,
    target_by_file: Mapping[str, Sequence[float]],
    isolated_events_by_file: Mapping[str, Sequence[SustainedStepEventV1]],
    source_step_direction: str,
    target_direction: str,
    horizon_seconds: int,
    target_noise_scale: float,
) -> DirectionCandidateV1:
    responses_by_file: dict[str, tuple[float, ...]] = {}
    censored_by_file: dict[str, int] = {}
    consistency_by_file: dict[str, float] = {}
    opposite_by_file: dict[str, float] = {}
    for file_name in FIT_FILES:
        responses: list[float] = []
        censored = 0
        for event in isolated_events_by_file[file_name]:
            if event.direction != source_step_direction:
                continue
            evaluation = evaluate_target_response_file_local_v1(
                target_by_file[file_name],
                event_index=event.event_index,
                horizon_seconds=horizon_seconds,
                target_noise_scale=target_noise_scale,
                target_direction=target_direction,
            )
            if evaluation.right_censored:
                censored += 1
            elif evaluation.target_response is not None:
                responses.append(evaluation.target_response)
        responses_by_file[file_name] = tuple(responses)
        censored_by_file[file_name] = censored
        _, consistency_by_file[file_name] = _direction_stats(responses, target_noise_scale, target_direction)
        opposite = "decrease" if target_direction == "increase" else "increase"
        _, opposite_by_file[file_name] = _direction_stats(responses, target_noise_scale, opposite)
    pooled = responses_by_file[FIT_FILES[0]] + responses_by_file[FIT_FILES[1]]
    _, pooled_consistency = _direction_stats(pooled, target_noise_scale, target_direction)
    median_response = float(statistics.median(pooled)) if pooled else 0.0
    robust_effect = abs(median_response) / target_noise_scale
    agrees = direction_agrees_strict_v1(
        selected_train1=consistency_by_file[FIT_FILES[0]],
        opposite_train1=opposite_by_file[FIT_FILES[0]],
        selected_train2=consistency_by_file[FIT_FILES[1]],
        opposite_train2=opposite_by_file[FIT_FILES[1]],
    )
    return DirectionCandidateV1(
        target_direction,
        horizon_seconds,
        responses_by_file[FIT_FILES[0]],
        responses_by_file[FIT_FILES[1]],
        censored_by_file[FIT_FILES[0]],
        censored_by_file[FIT_FILES[1]],
        consistency_by_file[FIT_FILES[0]],
        consistency_by_file[FIT_FILES[1]],
        pooled_consistency,
        median_response,
        robust_effect,
        agrees,
    )


def select_direction_candidate_v1(
    candidates: Sequence[DirectionCandidateV1],
) -> DirectionCandidateV1 | None:
    eligible = [item for item in candidates if item.direction_agrees]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda item: (
            -item.pooled_consistency,
            -item.pooled_robust_effect_ratio,
            item.horizon_seconds,
            item.target_direction,
        ),
    )


def fit_candidate_passes_v1(candidate: DirectionCandidateV1) -> bool:
    return fit_support_gate_v1(
        total_isolated_events=len(candidate.train1_responses) + len(candidate.train2_responses),
        train1_isolated_events=len(candidate.train1_responses),
        train2_isolated_events=len(candidate.train2_responses),
        fit_directional_consistency=candidate.pooled_consistency,
        train1_directional_consistency=candidate.train1_consistency,
        train2_directional_consistency=candidate.train2_consistency,
        fit_robust_effect_ratio=candidate.pooled_robust_effect_ratio,
        direction_agrees_across_files=candidate.direction_agrees,
    )


def calibration_confirmation_values_v1(
    *,
    target_values: Sequence[float],
    isolated_events: Sequence[SustainedStepEventV1],
    source_step_direction: str,
    target_direction: str,
    horizon_seconds: int,
    target_noise_scale: float,
) -> tuple[int, int, float, float, float, bool, bool]:
    responses: list[float] = []
    censored = 0
    for event in isolated_events:
        if event.direction != source_step_direction:
            continue
        evaluation = evaluate_target_response_file_local_v1(
            target_values,
            event_index=event.event_index,
            horizon_seconds=horizon_seconds,
            target_noise_scale=target_noise_scale,
            target_direction=target_direction,
        )
        if evaluation.right_censored:
            censored += 1
        elif evaluation.target_response is not None:
            responses.append(evaluation.target_response)
    _, selected_consistency = _direction_stats(responses, target_noise_scale, target_direction)
    opposite = "decrease" if target_direction == "increase" else "increase"
    _, opposite_consistency = _direction_stats(responses, target_noise_scale, opposite)
    median_response = float(statistics.median(responses)) if responses else 0.0
    robust_effect = abs(median_response) / target_noise_scale
    unchanged = selected_consistency > opposite_consistency
    confirmed = calibration_confirmation_gate_v1(
        train3_isolated_events=len(responses),
        source_direction_unchanged=True,
        target_direction_unchanged=unchanged,
        train3_directional_consistency=selected_consistency,
        train3_robust_effect_ratio=robust_effect,
        fit_parameters_reused_without_retuning=True,
    )
    return (
        len(responses),
        censored,
        selected_consistency,
        opposite_consistency,
        robust_effect,
        unchanged,
        confirmed,
    )


def transfer_rate_v1(fit_supported: int, confirmed: int) -> float:
    _require_nonnegative(fit_supported, "fit_supported")
    _require_nonnegative(confirmed, "confirmed")
    if confirmed > fit_supported:
        raise HAIContinuousStepError("confirmed count exceeds fit-supported count")
    return confirmed / fit_supported if fit_supported else 0.0


def deduplicate_directional_relations_v1(
    records: Sequence[ContinuousCalibrationConfirmationRecordV1],
) -> tuple[ContinuousCalibrationConfirmationRecordV1, ...]:
    seen: set[tuple[str, str, str, str]] = set()
    result = []
    for record in records:
        identity = (
            record.source_variable,
            record.source_step_direction,
            record.target_variable,
            record.target_response_direction,
        )
        if identity not in seen:
            seen.add(identity)
            result.append(record)
    return tuple(result)


@dataclass
class TASK039BR2DataAccessLedger:
    """Fail-closed path and column ledger for real BR2 execution."""

    authorized_columns: Mapping[str, tuple[str, ...]]
    opened_value_files: set[str]
    prohibited_data_access_count: int = 0
    normal_guard_feature_values_accessed: bool = False
    p2_p4_feature_values_accessed: bool = False

    def __init__(self, authorized_columns: Mapping[str, Sequence[str]]) -> None:
        normalized = {
            process: tuple(str(item) for item in values)
            for process, values in authorized_columns.items()
        }
        if set(normalized) != {"P1", "P3"}:
            raise HAIContinuousStepError("authorized column scopes must be P1 and P3")
        for process, values in normalized.items():
            if not values or any(not item.startswith(f"{process}_") for item in values):
                raise HAIContinuousStepError("authorized process columns are invalid")
        self.authorized_columns = normalized
        self.opened_value_files = set()
        self.prohibited_data_access_count = 0
        self.normal_guard_feature_values_accessed = False
        self.p2_p4_feature_values_accessed = False

    def authorize_value_file(self, relative_path: str) -> None:
        candidate = PurePosixPath(relative_path)
        lowered = relative_path.lower()
        if (
            candidate.is_absolute()
            or ".." in candidate.parts
            or any(token in lowered for token in _PROHIBITED_PATH_TOKENS)
            or relative_path not in AUTHORIZED_VALUE_FILES
        ):
            self.prohibited_data_access_count += 1
            if "train4" in lowered:
                self.normal_guard_feature_values_accessed = True
            raise HAIContinuousStepError("TASK039BR2_PROHIBITED_DATA_ACCESS")
        self.opened_value_files.add(relative_path)

    def authorize_columns(self, columns: Sequence[str]) -> None:
        allowed = {"timestamp"}
        allowed.update(item for values in self.authorized_columns.values() for item in values)
        for value in columns:
            if value not in allowed:
                self.prohibited_data_access_count += 1
                if value.startswith(("P2_", "P4_")):
                    self.p2_p4_feature_values_accessed = True
                raise HAIContinuousStepError("TASK039BR2_PROHIBITED_DATA_ACCESS")

    @property
    def authorized_columns_hash(self) -> str:
        return stable_hash_v1(
            {key: list(values) for key, values in sorted(self.authorized_columns.items())}
        )


@dataclass(frozen=True)
class VerifiedNormalFileV1:
    relative_path: str
    sha256: str
    byte_size: int
    row_count: int
    header_hash: str
    values_opened: bool


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HAIContinuousStepError(f"cannot load JSON input: {path.name}") from exc


def verify_self_hash_v1(document: Mapping[str, Any], field_name: str = "artifact_hash") -> str:
    expected = document.get(field_name)
    require_sha256(str(expected), field_name)
    content = {key: value for key, value in document.items() if key != field_name}
    if stable_hash_v1(content) != expected:
        raise HAIContinuousStepError(f"{field_name} does not match content")
    return str(expected)


def validate_frozen_inputs_v1(
    *,
    config: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    br0_decision: Mapping[str, Any],
    br0_readiness: Mapping[str, Any],
    br1_bundle: Mapping[str, Any],
    source_exclusion_ledger: Mapping[str, Any],
    morphology_ledger: Mapping[str, Any],
) -> None:
    if verify_self_hash_v1(dataset_manifest) != DATASET_MANIFEST_ID:
        raise HAIContinuousStepError("blocked_frozen_artifact_identity_mismatch")
    expected = (
        (br0_decision, BR0_DECISION_HASH),
        (br0_readiness, BR0_READINESS_HASH),
        (br1_bundle, BR1_PROTOCOL_BUNDLE_HASH),
        (source_exclusion_ledger, BR0_SOURCE_LEDGER_HASH),
        (morphology_ledger, BR0_MORPHOLOGY_LEDGER_HASH),
    )
    if any(verify_self_hash_v1(document) != digest for document, digest in expected):
        raise HAIContinuousStepError("blocked_frozen_artifact_identity_mismatch")
    if config.get("config_hash") is None:
        raise HAIContinuousStepError("config_hash is missing")
    config_content = {key: value for key, value in config.items() if key != "config_hash"}
    if stable_hash_v1(config_content) != config["config_hash"]:
        raise HAIContinuousStepError("config_hash does not match content")
    frozen = config.get("frozen_lineage", {})
    required = {
        "dataset_manifest_id": DATASET_MANIFEST_ID,
        "br0_decision_hash": BR0_DECISION_HASH,
        "br0_readiness_hash": BR0_READINESS_HASH,
        "br0_source_exclusion_ledger_hash": BR0_SOURCE_LEDGER_HASH,
        "br0_morphology_ledger_hash": BR0_MORPHOLOGY_LEDGER_HASH,
        "br1_protocol_bundle_hash": BR1_PROTOCOL_BUNDLE_HASH,
        "br1_config_hash": BR1_CONFIG_HASH,
    }
    if frozen != required or br1_bundle.get("relation_family", {}).get("family_id") != FAMILY_ID:
        raise HAIContinuousStepError("blocked_frozen_artifact_identity_mismatch")


def validate_frozen_eligibility_v1(
    *,
    config: Mapping[str, Any],
    source_exclusion_ledger: Mapping[str, Any],
    morphology_ledger: Mapping[str, Any],
) -> dict[str, dict[str, tuple[Mapping[str, Any], ...]]]:
    exclusions = {
        item["variable_name"]: item for item in source_exclusion_ledger.get("records", ())
    }
    morphologies = {
        item["variable_name"]: item for item in morphology_ledger.get("records", ())
    }
    result: dict[str, dict[str, tuple[Mapping[str, Any], ...]]] = {}
    for process in ("P1", "P3"):
        declared = config.get("frozen_eligibility", {}).get(process, {})
        sources = tuple(declared.get("sources", ()))
        targets = tuple(declared.get("targets", ()))
        expected_counts = (12, 12) if process == "P1" else (2, 3)
        if (len(sources), len(targets)) != expected_counts:
            raise HAIContinuousStepError("blocked_frozen_eligibility_inputs_unavailable")
        for source in sources:
            name = source.get("variable_name")
            morphology = morphologies.get(name)
            metadata = exclusions.get(name)
            summaries = tuple(morphology.get("file_summaries", ())) if morphology else ()
            if (
                metadata is None
                or morphology is None
                or source.get("semantic_role") not in APPROVED_SOURCE_ROLES
                or morphology.get("documented_semantic_role") != source.get("semantic_role")
                or source.get("metadata_record_hash") != metadata.get("artifact_hash")
                or source.get("morphology_record_hash") != morphology.get("artifact_hash")
                or len(summaries) != 3
                or not all(item.get("repeated_bounded_changes") is True for item in summaries)
                or metadata.get("review_status") != "reviewed"
                or metadata.get("metadata_confidence") == "insufficient"
            ):
                raise HAIContinuousStepError("blocked_frozen_eligibility_inputs_unavailable")
        for target in targets:
            metadata = exclusions.get(target.get("variable_name"))
            if (
                metadata is None
                or target.get("metadata_record_hash") != metadata.get("artifact_hash")
                or metadata.get("documented_semantic_role") != "process_sensor"
                or metadata.get("observed_domain") != "continuous"
                or metadata.get("review_status") != "reviewed"
                or metadata.get("metadata_confidence") == "insufficient"
            ):
                raise HAIContinuousStepError("blocked_frozen_eligibility_inputs_unavailable")
        result[process] = {"sources": sources, "targets": targets}
    return result


def verify_normal_file_records_v1(
    *,
    data_root: Path,
    manifest: DatasetManifestV2,
    csv_report: Mapping[str, Any],
) -> tuple[VerifiedNormalFileV1, ...]:
    """Verify train1-3 on disk and train4 through frozen public records only."""

    manifest_files = {item.relative_local_path: item for item in manifest.files}
    structure = {item["relative_path"]: item for item in csv_report.get("records", ())}
    records: list[VerifiedNormalFileV1] = []
    for relative in ALL_NORMAL_FILES:
        source = manifest_files.get(relative)
        public = structure.get(relative)
        if (
            source is None
            or public is None
            or source.row_count is None
            or source.byte_size is None
            or source.sha256 != public.get("file_sha256")
            or source.byte_size != public.get("byte_size")
            or source.row_count != public.get("row_count")
            or public.get("nominal_timestamp_delta_seconds") != 1.0
            or public.get("normal_file_status") != "normal_only_verified"
        ):
            raise HAIContinuousStepError("failed_hai_normal_file_identity")
        if relative == NORMAL_GUARD_FILE:
            records.append(
                VerifiedNormalFileV1(
                    relative,
                    source.sha256,
                    source.byte_size,
                    source.row_count,
                    manifest.feature_names_hash or "",
                    False,
                )
            )
            continue
        local = data_root / PurePosixPath(relative).name
        if not local.is_file() or local.stat().st_size != source.byte_size or streaming_sha256(local) != source.sha256:
            raise HAIContinuousStepError("failed_hai_normal_file_identity")
        records.append(
            VerifiedNormalFileV1(
                relative,
                source.sha256,
                source.byte_size,
                source.row_count,
                manifest.feature_names_hash or "",
                True,
            )
        )
    if manifest.manifest_id != DATASET_MANIFEST_ID or manifest.nominal_sampling_interval_seconds != 1.0:
        raise HAIContinuousStepError("failed_hai_normal_file_identity")
    return tuple(records)


def read_authorized_columns_v1(
    *,
    data_root: Path,
    relative_path: str,
    columns: Sequence[str],
    ledger: TASK039BR2DataAccessLedger,
) -> tuple[dict[str, tuple[float, ...]], int, int, tuple[str, ...]]:
    """Read only authorized numeric fields from one verified CSV."""

    ledger.authorize_value_file(relative_path)
    ledger.authorize_columns(columns)
    path = data_root / PurePosixPath(relative_path).name
    values = {name: [] for name in columns}
    missing_or_nonfinite = 0
    total_cells = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = tuple(next(reader))
        except StopIteration as exc:
            raise HAIContinuousStepError("authorized CSV is empty") from exc
        if len(header) != len(set(header)) or any(name not in header for name in columns):
            raise HAIContinuousStepError("authorized columns are missing or ambiguous")
        indexes = {name: header.index(name) for name in columns}
        for row in reader:
            if len(row) != len(header):
                raise HAIContinuousStepError("authorized CSV contains malformed rows")
            for name, index in indexes.items():
                total_cells += 1
                try:
                    value = float(row[index])
                except ValueError:
                    value = math.nan
                if not math.isfinite(value):
                    missing_or_nonfinite += 1
                values[name].append(value)
    return (
        {name: tuple(items) for name, items in values.items()},
        missing_or_nonfinite,
        total_cells,
        header,
    )


def write_json_v1(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(thaw_json(document), sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def private_ledger_v1(artifact_type: str, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    content = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": artifact_type,
        "records": [dict(item) for item in records],
        "raw_HAI_rows_included": False,
        "attack_information_included": False,
    }
    return {**content, "artifact_hash": stable_hash_v1(content)}


def create_selected_views_v1(
    *,
    process_id: str,
    process_feature_names: Sequence[str],
    execution_code_commit: str,
    config_hash: str,
    created_at: str,
) -> tuple[DataViewManifestV2, DataViewManifestV2]:
    _require_process(process_id)
    if not process_feature_names or any(not item.startswith(f"{process_id}_") for item in process_feature_names):
        raise HAIContinuousStepError("selected process feature scope is invalid")
    metadata = CreationMetadataV2(created_at, "TASK-039BR2", execution_code_commit, config_hash)
    feature_hash = stable_hash_v1({"features": list(process_feature_names)})
    aggregation = AggregationDescriptionV2("none", 1.0, 1.0, True, "No aggregation or downsampling.")
    canonical = DataViewManifestV2(
        DataViewKindV2.CANONICAL_RULE,
        DATASET_MANIFEST_ID,
        (process_id,),
        1.0,
        {
            "column_selection": "verified_selected_process_columns_only",
            "numeric_parsing": "deterministic",
            "interpolation": False,
            "imputation": False,
            "scaling": False,
            "downsampling": False,
        },
        aggregation,
        feature_hash,
        True,
        ProvenanceStatusV2.VERIFIED,
        metadata,
    )
    candidate = DataViewManifestV2(
        DataViewKindV2.CANDIDATE_LEARNING,
        DATASET_MANIFEST_ID,
        (process_id,),
        1.0,
        {
            "normalization": "not_fitted_in_TASK-039BR2",
            "normalization_fit_role": "normal_candidate_fit_only",
            "interpolation": False,
            "imputation": False,
            "downsampling": False,
        },
        aggregation,
        feature_hash,
        False,
        ProvenanceStatusV2.VERIFIED,
        metadata,
    )
    return canonical, candidate


def create_selected_splits_v1(
    *,
    process_id: str,
    canonical_view_id: str,
    row_counts: Mapping[str, int],
    execution_code_commit: str,
    config_hash: str,
    created_at: str,
) -> tuple[SplitManifestV2, SplitManifestV2, SplitManifestV2]:
    _require_process(process_id)
    if set(row_counts) != set(ALL_NORMAL_FILES):
        raise HAIContinuousStepError("split row-count inventory is incomplete")
    metadata = CreationMetadataV2(created_at, "TASK-039BR2", execution_code_commit, config_hash)
    starts: dict[str, int] = {}
    cursor = 0
    for relative in ALL_NORMAL_FILES:
        starts[relative] = cursor
        cursor += int(row_counts[relative]) + 120
    common = dict(
        dataset_manifest_id=DATASET_MANIFEST_ID,
        data_view_id=canonical_view_id,
        event_ids=None,
        purge_gap_samples=120,
        process_scope=(process_id,),
        seed=None,
        provenance_status=ProvenanceStatusV2.VERIFIED,
        sealed_access_status=SealedAccessStatusV2.NOT_APPLICABLE,
        split_before_windowing=True,
        creation_metadata=metadata,
    )
    fit = SplitManifestV2(
        role=SplitRoleV2.NORMAL_CANDIDATE_FIT,
        raw_ranges=tuple(RawRangeV2(starts[name], starts[name] + row_counts[name]) for name in FIT_FILES),
        creation_policy="file_level_train1_train2_before_windowing",
        **common,
    )
    calibration = SplitManifestV2(
        role=SplitRoleV2.NORMAL_RELATION_CALIBRATION,
        raw_ranges=(RawRangeV2(starts[CALIBRATION_FILE], starts[CALIBRATION_FILE] + row_counts[CALIBRATION_FILE]),),
        creation_policy="file_level_train3_before_windowing_without_retuning",
        **common,
    )
    guard = SplitManifestV2(
        role=SplitRoleV2.NORMAL_GUARD,
        raw_ranges=(RawRangeV2(starts[NORMAL_GUARD_FILE], starts[NORMAL_GUARD_FILE] + row_counts[NORMAL_GUARD_FILE]),),
        creation_policy="file_level_train4_reserved_without_feature_value_access",
        **common,
    )
    validate_split_collection_v2((fit, calibration, guard), window_size=61, maximum_required_lag=60)
    return fit, calibration, guard


def assert_public_payload_safe_v1(document: Mapping[str, Any]) -> None:
    def inspect(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                lowered_key = str(key).lower()
                if lowered_key in {
                    "event_index",
                    "event_timestamp",
                    "raw_row",
                    "raw_window",
                    "attack_start",
                    "attack_end",
                    "target_controller",
                    "credential",
                    "signed_url",
                    "authorization_header",
                }:
                    raise HAIContinuousStepError("failed_public_output_boundary")
                if lowered_key == "event_timestamps_publicly_exposed" and item is not False:
                    raise HAIContinuousStepError("failed_public_output_boundary")
                inspect(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                inspect(item)

    inspect(document)
    text = json.dumps(thaw_json(document), sort_keys=True, ensure_ascii=True).lower()
    prohibited = (
        "event_index",
        "raw_row",
        "raw_window",
        "attack_start",
        "attack_end",
        "target_controller",
        "credential",
        "signed_url",
        "authorization_header",
        "c:\\\\users\\\\",
    )
    if any(token in text for token in prohibited):
        raise HAIContinuousStepError("failed_public_output_boundary")


class ProcessExecutionResultV1(NamedTuple):
    feasibility: HAIContinuousProcessFeasibilityV1
    source_ledger: Mapping[str, Any]
    event_ledger: Mapping[str, Any]
    relation_ledger: Mapping[str, Any]
    process_feature_names: tuple[str, ...]
    row_counts: Mapping[str, int]


def _count_by_status(records: Sequence[_ExecutionArtifact]) -> dict[str, int]:
    result: dict[str, int] = {}
    for record in records:
        status = str(getattr(record, "status"))
        result[status] = result.get(status, 0) + 1
    return dict(sorted(result.items()))


def _event_private_dict(event: SustainedStepEventV1, isolated: bool) -> dict[str, Any]:
    return {
        "event_index": event.event_index,
        "step_direction": event.direction,
        "pre_level": event.pre_level,
        "post_level": event.post_level,
        "step_amplitude": event.step_amplitude,
        "pre_stability_fraction": event.pre_stability_fraction,
        "post_stability_fraction": event.post_stability_fraction,
        "isolated": isolated,
    }


def execute_process_v1(
    *,
    process_id: str,
    process_name: str,
    eligibility: Mapping[str, Sequence[Mapping[str, Any]]],
    data_root: Path,
    verified_files: Sequence[VerifiedNormalFileV1],
    ledger: TASK039BR2DataAccessLedger,
    creation_metadata: CreationMetadataV1,
) -> ProcessExecutionResultV1:
    """Execute the frozen protocol for one process and return sanitized metrics."""

    _require_process(process_id)
    sources = tuple(eligibility["sources"])
    targets = tuple(eligibility["targets"])
    source_names = tuple(str(item["variable_name"]) for item in sources)
    target_names = tuple(str(item["variable_name"]) for item in targets)
    selected_columns = source_names + target_names
    by_file: dict[str, dict[str, tuple[float, ...]]] = {}
    missing_nonfinite = 0
    total_cells = 0
    headers: list[tuple[str, ...]] = []
    row_counts = {item.relative_path: item.row_count for item in verified_files}
    for relative in AUTHORIZED_VALUE_FILES:
        values, missing, total, header = read_authorized_columns_v1(
            data_root=data_root,
            relative_path=relative,
            columns=selected_columns,
            ledger=ledger,
        )
        expected_rows = row_counts[relative]
        if any(len(sequence) != expected_rows for sequence in values.values()):
            raise HAIContinuousStepError("failed_hai_normal_file_identity")
        by_file[relative] = values
        missing_nonfinite += missing
        total_cells += total
        headers.append(header)
    if any(header != headers[0] for header in headers[1:]):
        raise HAIContinuousStepError("failed_hai_normal_file_identity")
    feature_names = [
        value
        for value in headers[0]
        if value.strip().lower()
        not in {
            "timestamp",
            "time",
            "datetime",
            "date_time",
            "label",
            "attack",
            "anomaly",
            "is_attack",
        }
    ]
    observed_header_hash = sha256(
        json.dumps(feature_names, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    if observed_header_hash != verified_files[0].header_hash:
        raise HAIContinuousStepError("failed_hai_normal_file_identity")
    process_feature_names = tuple(name for name in headers[0] if name.startswith(f"{process_id}_"))

    source_records: list[ContinuousSourceScreeningRecordV1] = []
    events_by_source: dict[str, dict[str, tuple[SustainedStepEventV1, ...]]] = {}
    for source in sources:
        name = str(source["variable_name"])
        fit_sequences = {file_name: by_file[file_name][name] for file_name in FIT_FILES}
        finite = all(math.isfinite(value) for sequence in fit_sequences.values() for value in sequence)
        diagnostics = derive_multifile_source_screening_diagnostics_v1(fit_sequences) if finite else None
        if not finite:
            status = SourceScreeningStatusV1.INVALID_SOURCE.value
            noise = None
            count = 0
            threshold = tolerance = None
        elif diagnostics.source_step_threshold is None:
            status = SourceScreeningStatusV1.INSUFFICIENT_NONTRIVIAL_AMPLITUDES.value
            noise = diagnostics.source_noise_scale
            count = diagnostics.nontrivial_amplitude_count
            threshold = tolerance = None
        else:
            status = SourceScreeningStatusV1.SUPPORTED.value
            noise = diagnostics.source_noise_scale
            count = diagnostics.nontrivial_amplitude_count
            threshold = diagnostics.source_step_threshold
            tolerance = diagnostics.source_stability_tolerance
        record = ContinuousSourceScreeningRecordV1(
            process_id,
            name,
            str(source["metadata_record_hash"]),
            str(source["morphology_record_hash"]),
            FIT_FILES,
            noise,
            count,
            threshold,
            tolerance,
            "linear_interpolation_index_0.75_times_n_minus_1",
            status,
            "feasibility_screening",
            True,
            False,
            False,
            creation_metadata,
        )
        source_records.append(record)
        if status == SourceScreeningStatusV1.SUPPORTED.value:
            events_by_source[name] = extract_multifile_events_v1(
                {file_name: by_file[file_name][name] for file_name in AUTHORIZED_VALUE_FILES},
                source_step_threshold=float(threshold),
                source_stability_tolerance=float(tolerance),
            )
        else:
            events_by_source[name] = {file_name: () for file_name in AUTHORIZED_VALUE_FILES}

    isolated = classify_multisource_isolation_v1(events_by_source)
    event_summaries: list[ContinuousSourceEventSummaryV1] = []
    private_event_records: list[dict[str, Any]] = []
    all_clustered = 0
    all_nonisolated = 0
    for source_record in source_records:
        source = source_record.variable_name
        for file_name in AUTHORIZED_VALUE_FILES:
            classified = isolated[source][file_name]
            all_clustered += len(classified)
            all_nonisolated += sum(not flag for _, flag in classified)
            private_event_records.append(
                {
                    "process_id": process_id,
                    "source_variable": source,
                    "source_screening_ref": source_record.artifact_hash,
                    "relative_file": file_name,
                    "events": [_event_private_dict(event, flag) for event, flag in classified],
                }
            )
            for direction in ("step_up", "step_down"):
                direction_events = [(event, flag) for event, flag in classified if event.direction == direction]
                isolated_count = sum(flag for _, flag in direction_events)
                total = len(direction_events)
                event_summaries.append(
                    ContinuousSourceEventSummaryV1(
                        process_id,
                        source,
                        source_record.artifact_hash,
                        file_name,
                        direction,
                        total,
                        isolated_count,
                        total - isolated_count,
                        isolated_count / total if total else 0.0,
                        False,
                        False,
                        creation_metadata,
                    )
                )

    target_records: list[ContinuousTargetScaleRecordV1] = []
    for target in targets:
        name = str(target["variable_name"])
        fit_sequences = {file_name: by_file[file_name][name] for file_name in FIT_FILES}
        finite = all(math.isfinite(value) for sequence in fit_sequences.values() for value in sequence)
        scale = derive_multifile_robust_scale_v1(fit_sequences) if finite else None
        target_records.append(
            ContinuousTargetScaleRecordV1(
                process_id,
                name,
                str(target["metadata_record_hash"]),
                FIT_FILES,
                scale,
                TargetScaleStatusV1.SUPPORTED.value if finite else TargetScaleStatusV1.INVALID_TARGET.value,
                "feasibility_screening",
                True,
                False,
                False,
                creation_metadata,
            )
        )

    fit_records: list[ContinuousDirectionalFitRecordV1] = []
    confirmations: list[ContinuousCalibrationConfirmationRecordV1] = []
    source_by_name = {item.variable_name: item for item in source_records}
    target_by_name = {item.target_variable: item for item in target_records}
    for source_name in source_names:
        source_record = source_by_name[source_name]
        isolated_by_file = {
            file_name: tuple(event for event, flag in isolated[source_name][file_name] if flag)
            for file_name in AUTHORIZED_VALUE_FILES
        }
        for source_direction in ("step_up", "step_down"):
            for target_name in target_names:
                target_record = target_by_name[target_name]
                if (
                    source_record.status != SourceScreeningStatusV1.SUPPORTED.value
                    or target_record.status != TargetScaleStatusV1.SUPPORTED.value
                ):
                    fit_record = ContinuousDirectionalFitRecordV1(
                        process_id,
                        source_name,
                        source_direction,
                        target_name,
                        None,
                        None,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        False,
                        False,
                        False,
                        (
                            DirectionalFitStatusV1.INVALID_TARGET.value
                            if target_record.status == TargetScaleStatusV1.INVALID_TARGET.value
                            else DirectionalFitStatusV1.FIT_UNSUPPORTED.value
                        ),
                        source_record.artifact_hash,
                        target_record.artifact_hash,
                        creation_metadata,
                    )
                    fit_records.append(fit_record)
                    continue
                candidates = [
                    evaluate_direction_candidate_v1(
                        target_by_file={file_name: by_file[file_name][target_name] for file_name in FIT_FILES},
                        isolated_events_by_file={file_name: isolated_by_file[file_name] for file_name in FIT_FILES},
                        source_step_direction=source_direction,
                        target_direction=direction,
                        horizon_seconds=horizon,
                        target_noise_scale=float(target_record.target_noise_scale),
                    )
                    for direction in ("increase", "decrease")
                    for horizon in RESPONSE_HORIZONS
                ]
                selected = select_direction_candidate_v1(candidates)
                if selected is None:
                    fit_record = ContinuousDirectionalFitRecordV1(
                        process_id,
                        source_name,
                        source_direction,
                        target_name,
                        None,
                        None,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        False,
                        False,
                        False,
                        DirectionalFitStatusV1.DIRECTION_UNSTABLE.value,
                        source_record.artifact_hash,
                        target_record.artifact_hash,
                        creation_metadata,
                    )
                    fit_records.append(fit_record)
                    continue
                passed = fit_candidate_passes_v1(selected)
                fit_record = ContinuousDirectionalFitRecordV1(
                    process_id,
                    source_name,
                    source_direction,
                    target_name,
                    selected.target_direction,
                    selected.horizon_seconds,
                    len(selected.train1_responses),
                    len(selected.train2_responses),
                    len(selected.train1_responses) + len(selected.train2_responses),
                    selected.train1_right_censored,
                    selected.train2_right_censored,
                    selected.train1_consistency,
                    selected.train2_consistency,
                    selected.pooled_consistency,
                    selected.pooled_median_response,
                    selected.pooled_robust_effect_ratio,
                    selected.direction_agrees,
                    True,
                    False,
                    DirectionalFitStatusV1.FIT_SUPPORTED.value if passed else DirectionalFitStatusV1.FIT_UNSUPPORTED.value,
                    source_record.artifact_hash,
                    target_record.artifact_hash,
                    creation_metadata,
                )
                fit_records.append(fit_record)
                if not passed:
                    continue
                confirmation_values = calibration_confirmation_values_v1(
                    target_values=by_file[CALIBRATION_FILE][target_name],
                    isolated_events=isolated_by_file[CALIBRATION_FILE],
                    source_step_direction=source_direction,
                    target_direction=str(selected.target_direction),
                    horizon_seconds=selected.horizon_seconds,
                    target_noise_scale=float(target_record.target_noise_scale),
                )
                usable, censored, consistency, opposite, effect, unchanged, confirmed = confirmation_values
                confirmations.append(
                    ContinuousCalibrationConfirmationRecordV1(
                        process_id,
                        fit_record.artifact_hash,
                        source_name,
                        source_direction,
                        target_name,
                        str(selected.target_direction),
                        selected.horizon_seconds,
                        usable,
                        censored,
                        consistency,
                        opposite,
                        effect,
                        unchanged,
                        True,
                        source_record.artifact_hash,
                        target_record.artifact_hash,
                        ConfirmationStatusV1.CALIBRATION_CONFIRMED.value if confirmed else ConfirmationStatusV1.CALIBRATION_CONFLICT.value,
                        creation_metadata,
                    )
                )

    source_ledger = private_ledger_v1(
        f"task039br2_{process_id.lower()}_source_parameter_ledger_v1",
        [item.to_dict() for item in source_records] + [item.to_dict() for item in target_records],
    )
    event_ledger = private_ledger_v1(
        f"task039br2_{process_id.lower()}_event_ledger_v1",
        private_event_records + [item.to_dict() for item in event_summaries],
    )
    relation_ledger = private_ledger_v1(
        f"task039br2_{process_id.lower()}_relation_ledger_v1",
        [item.to_dict() for item in fit_records] + [item.to_dict() for item in confirmations],
    )
    fit_supported = [item for item in fit_records if item.status == DirectionalFitStatusV1.FIT_SUPPORTED.value]
    confirmed = deduplicate_directional_relations_v1(
        [item for item in confirmations if item.status == ConfirmationStatusV1.CALIBRATION_CONFIRMED.value]
    )
    transfer = transfer_rate_v1(len(fit_supported), len(confirmed))
    confirmed_sources = {item.source_variable for item in confirmed}
    confirmed_targets = {item.target_variable for item in confirmed}
    valid_sources = sum(item.status == SourceScreeningStatusV1.SUPPORTED.value for item in source_records)
    median_support = float(statistics.median(item.train3_usable_isolated_events for item in confirmed)) if confirmed else 0.0
    metadata_unresolved_ratio = 1.0 / 37.0 if process_id == "P1" else 0.0
    metrics = {
        "documented_sources_with_valid_fit_thresholds": valid_sources,
        "eligible_continuous_targets": len(targets),
        "calibration_confirmed_directional_pairs": len(confirmed),
        "distinct_confirmed_sources": len(confirmed_sources),
        "distinct_confirmed_targets": len(confirmed_targets),
        "fit_to_calibration_transfer_rate": transfer,
        "normal_candidate_fit_files": FIT_FILE_NAMES,
        "normal_relation_calibration_file": CALIBRATION_FILE_NAME,
        "normal_guard_feature_values_accessed": ledger.normal_guard_feature_values_accessed,
        "prohibited_data_access_count": ledger.prohibited_data_access_count,
        "median_calibration_isolated_event_support": median_support,
        "manual_metadata_coverage": 1.0,
        "metadata_unresolved_ratio": metadata_unresolved_ratio,
        "non_isolated_source_event_ratio": all_nonisolated / all_clustered if all_clustered else 0.0,
        "missing_or_nonfinite_rate": missing_nonfinite / total_cells if total_cells else 0.0,
    }
    gate = process_feasibility_gate_v1(metrics)
    feasibility = HAIContinuousProcessFeasibilityV1(
        process_id,
        process_name,
        valid_sources,
        len(targets),
        len(confirmed),
        len(confirmed_sources),
        len(confirmed_targets),
        len(fit_supported),
        transfer,
        FIT_FILE_NAMES,
        CALIBRATION_FILE_NAME,
        ledger.normal_guard_feature_values_accessed,
        ledger.prohibited_data_access_count,
        median_support,
        1.0,
        metadata_unresolved_ratio,
        metrics["non_isolated_source_event_ratio"],
        metrics["missing_or_nonfinite_rate"],
        _count_by_status(source_records),
        _count_by_status(fit_records),
        _count_by_status(confirmations),
        str(source_ledger["artifact_hash"]),
        str(event_ledger["artifact_hash"]),
        str(relation_ledger["artifact_hash"]),
        gate,
        "feasible" if gate else "infeasible",
        False,
        False,
        False,
        False,
        creation_metadata,
    )
    return ProcessExecutionResultV1(
        feasibility,
        source_ledger,
        event_ledger,
        relation_ledger,
        process_feature_names,
        row_counts,
    )


def build_process_selection_v1(
    *,
    p1: HAIContinuousProcessFeasibilityV1,
    p3: HAIContinuousProcessFeasibilityV1,
    selection_policy_hash: str,
    creation_metadata: CreationMetadataV1,
) -> HAIContinuousProcessSelectionResultV1:
    decision = select_process_v1(p1.metric_mapping(), p3.metric_mapping())
    if decision.status == "selected":
        status = "selected"
        selected = decision.selected_process
        excluded = "P3" if selected == "P1" else "P1"
    elif decision.reason == "blocked_no_feasible_continuous_step_process":
        status = decision.reason
        selected = excluded = None
    else:
        status = "blocked_continuous_process_selection_indeterminate"
        selected = excluded = None
    core = (
        "distinct_confirmed_sources",
        "distinct_confirmed_targets",
        "calibration_confirmed_directional_pairs",
        "fit_to_calibration_transfer_rate",
        "median_calibration_isolated_event_support",
        "manual_metadata_coverage",
        "metadata_unresolved_ratio",
        "non_isolated_source_event_ratio",
        "missing_or_nonfinite_rate",
    )
    return HAIContinuousProcessSelectionResultV1(
        status,
        selected,
        excluded,
        decision.reason,
        p1.artifact_hash,
        p3.artifact_hash,
        selection_policy_hash,
        {
            "P1": {key: p1.metric_mapping()[key] for key in core},
            "P3": {key: p3.metric_mapping()[key] for key in core},
        },
        False,
        selected is not None,
        selected is not None,
        creation_metadata,
    )
