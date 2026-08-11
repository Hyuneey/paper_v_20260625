"""Synthetic-only preparation for future TASK-039D2 confirmation.

The D0 confirmation policy is the semantic authority.  This module supplies
immutable adapters and an arm-blind execution path for synthetic train3-like
values.  It contains no real-data loader and grants no TASK-039D2 authority.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.profiling.task039d1_execution_optimization_v1 import (
    classify_all_source_isolation_indexed_v1,
    extract_sustained_step_events_linear_v1,
)
from paperworks.profiling.task039d1_fit_v1 import optimized_target_response_v1
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
from paperworks.v6.continuous_step_protocol_v1 import SustainedStepEventV1
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCE_ROLES,
    FROZEN_SOURCES,
    FROZEN_TARGETS,
    HORIZONS,
    train3_confirmation_gate_v1,
)


TASK_ID = "TASK-039D2-PREP"
BRANCH = "task-039d2-synthetic-prep"
BASE_COMMIT = "360cf4b84ed2c18e026186be00f2312508a8fb85"
PREPARATION_STATUS = "passed_task039d2_synthetic_preparation"
CONFIRMATION_POLICY_HASH = (
    "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27"
)
D2_REAL_EXECUTION_AUTHORIZED = False

SOURCE_DIRECTIONS = ("step_up", "step_down")
TARGET_DIRECTIONS = ("increase", "decrease")
SOURCE_PARAMETER_STATUSES = ("supported", "insufficient_nontrivial_amplitudes")
PARAMETER_CLASS = "normal_relation_profile_fit_derived"

SYNTHETIC_CASES = (
    "confirmed_relation",
    "insufficient_train3_support",
    "exact_5_response_boundary",
    "consistency_exactly_0_60",
    "consistency_just_below_0_60",
    "effect_exactly_1_0",
    "effect_just_below_1_0",
    "selected_consistency_greater_than_opposite",
    "selected_opposite_equality_fails",
    "opposite_greater_fails",
    "right_censoring",
    "step_up",
    "step_down",
    "target_increase",
    "target_decrease",
    "all_12_source_isolation",
    "inclusive_plus_minus_2_boundary",
    "immutable_selected_horizon",
    "immutable_target_direction",
)

NO_RETUNING_CHECKS = (
    "source_noise_scale",
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "source_step_direction",
    "target_response_direction",
    "selected_horizon",
    "pre_window",
    "post_window",
    "response_window",
    "refractory_period",
    "isolation_radius",
    "alternative_horizon_search",
    "opposite_direction_search",
    "lower_ranked_fallback",
)


class TASK039D2PreparationError(V6FoundationError):
    """Raised when a D2-preparation contract or guard fails closed."""


def _require_nonnegative_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TASK039D2PreparationError(f"{field_name} must be a non-negative integer")


def _require_probability(value: float, field_name: str) -> float:
    result = require_finite(value, field_name)
    if result < 0.0 or result > 1.0:
        raise TASK039D2PreparationError(f"{field_name} must be between zero and one")
    return result


def _self_hashed(content: Mapping[str, Any]) -> dict[str, Any]:
    payload = thaw_json(freeze_json(content))
    return {**payload, "artifact_hash": stable_hash_v1(payload)}


@dataclass(frozen=True)
class FrozenConfirmationControlsV1:
    """Closed D0 execution constants; construction with any change fails."""

    pre_window_seconds: int = 5
    post_window_seconds: int = 5
    response_window_seconds: int = 3
    refractory_period_seconds: int = 10
    isolation_radius_seconds: int = 2
    usable_response_minimum: int = 5
    directional_consistency_minimum: float = 0.60
    robust_effect_ratio_minimum: float = 1.0
    alternative_horizon_search: bool = False
    opposite_direction_search: bool = False
    lower_ranked_fallback: bool = False
    retuning_allowed: bool = False

    def __post_init__(self) -> None:
        expected = {
            "pre_window_seconds": 5,
            "post_window_seconds": 5,
            "response_window_seconds": 3,
            "refractory_period_seconds": 10,
            "isolation_radius_seconds": 2,
            "usable_response_minimum": 5,
            "directional_consistency_minimum": 0.60,
            "robust_effect_ratio_minimum": 1.0,
            "alternative_horizon_search": False,
            "opposite_direction_search": False,
            "lower_ranked_fallback": False,
            "retuning_allowed": False,
        }
        for field_name, frozen_value in expected.items():
            if getattr(self, field_name) != frozen_value:
                raise TASK039D2PreparationError(
                    f"retuning is prohibited: {field_name} is frozen by D0"
                )


FROZEN_CONFIRMATION_CONTROLS = FrozenConfirmationControlsV1()


@dataclass(frozen=True)
class D1ParameterLedgerBindingsV1:
    """Hash-only binding to the private D1 source and target ledgers."""

    source_parameter_ledger_hash: str
    target_parameter_ledger_hash: str

    def __post_init__(self) -> None:
        require_sha256(self.source_parameter_ledger_hash, "source_parameter_ledger_hash")
        require_sha256(self.target_parameter_ledger_hash, "target_parameter_ledger_hash")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content())

    def _content(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "d1_parameter_ledger_bindings_v1",
            "source_parameter_ledger_hash": self.source_parameter_ledger_hash,
            "target_parameter_ledger_hash": self.target_parameter_ledger_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._content(), "artifact_hash": self.artifact_hash}


@dataclass(frozen=True)
class D1SourceParameterRecordV1:
    """Immutable wrapper around one exact D1 source-parameter record."""

    source: str
    semantic_role: str
    source_noise_scale: float
    nontrivial_amplitude_count: int
    source_step_threshold: float | None
    source_stability_tolerance: float | None
    parameter_status: str
    fit_file_bindings: tuple[str, str]
    d1_parameter_record_hash: str
    source_parameter_ledger_hash: str

    def __post_init__(self) -> None:
        if self.source not in FROZEN_SOURCES:
            raise TASK039D2PreparationError("source is outside the frozen 12-source identity set")
        if self.semantic_role != FROZEN_SOURCE_ROLES[self.source]:
            raise TASK039D2PreparationError("source semantic role does not match D0")
        noise = require_finite(self.source_noise_scale, "source_noise_scale")
        if noise < 0.0:
            raise TASK039D2PreparationError("source_noise_scale must be non-negative")
        _require_nonnegative_int(self.nontrivial_amplitude_count, "nontrivial_amplitude_count")
        if self.parameter_status not in SOURCE_PARAMETER_STATUSES:
            raise TASK039D2PreparationError("unknown D1 source parameter status")
        if self.parameter_status == "supported":
            threshold = require_finite(self.source_step_threshold, "source_step_threshold")
            tolerance = require_finite(
                self.source_stability_tolerance, "source_stability_tolerance"
            )
            if threshold <= 0.0 or tolerance < 0.0:
                raise TASK039D2PreparationError("supported source parameters are invalid")
        elif self.source_step_threshold is not None or self.source_stability_tolerance is not None:
            raise TASK039D2PreparationError("unsupported source must not invent fit parameters")
        if len(self.fit_file_bindings) != 2:
            raise TASK039D2PreparationError("D1 source record must bind exactly two fit files")
        for index, digest in enumerate(self.fit_file_bindings):
            require_sha256(digest, f"fit_file_bindings[{index}]")
        require_sha256(self.d1_parameter_record_hash, "d1_parameter_record_hash")
        require_sha256(self.source_parameter_ledger_hash, "source_parameter_ledger_hash")
        if stable_hash_v1(self._d1_content()) != self.d1_parameter_record_hash:
            raise TASK039D2PreparationError("D1 source parameter record hash mismatch")

    def _d1_content(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039d1_source_parameter_record_v1",
            "source": self.source,
            "semantic_role": self.semantic_role,
            "source_noise_scale": self.source_noise_scale,
            "nontrivial_amplitude_count": self.nontrivial_amplitude_count,
            "source_step_threshold": self.source_step_threshold,
            "source_stability_tolerance": self.source_stability_tolerance,
            "parameter_status": self.parameter_status,
            "parameter_class": PARAMETER_CLASS,
            "fit_file_bindings": list(self.fit_file_bindings),
        }


@dataclass(frozen=True)
class D1TargetParameterRecordV1:
    """Immutable wrapper around one exact D1 target-parameter record."""

    target: str
    target_noise_scale: float
    fit_file_bindings: tuple[str, str]
    d1_parameter_record_hash: str
    target_parameter_ledger_hash: str

    def __post_init__(self) -> None:
        if self.target not in FROZEN_TARGETS:
            raise TASK039D2PreparationError("target is outside the frozen 12-target identity set")
        scale = require_finite(self.target_noise_scale, "target_noise_scale")
        if scale <= 0.0:
            raise TASK039D2PreparationError("target_noise_scale must be positive")
        if len(self.fit_file_bindings) != 2:
            raise TASK039D2PreparationError("D1 target record must bind exactly two fit files")
        for index, digest in enumerate(self.fit_file_bindings):
            require_sha256(digest, f"fit_file_bindings[{index}]")
        require_sha256(self.d1_parameter_record_hash, "d1_parameter_record_hash")
        require_sha256(self.target_parameter_ledger_hash, "target_parameter_ledger_hash")
        if stable_hash_v1(self._d1_content()) != self.d1_parameter_record_hash:
            raise TASK039D2PreparationError("D1 target parameter record hash mismatch")

    def _d1_content(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039d1_target_parameter_record_v1",
            "target": self.target,
            "target_noise_scale": self.target_noise_scale,
            "parameter_class": PARAMETER_CLASS,
            "fit_file_bindings": list(self.fit_file_bindings),
        }


@dataclass(frozen=True)
class ConfirmableDirectionalRelationV1:
    """Arm-blind D1-derived identity and parameter references for future D2."""

    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    d1_selected_horizon_seconds: int
    source_noise_scale_reference: str
    source_threshold_reference: str
    source_stability_tolerance_reference: str
    target_scale_reference: str
    d1_directional_record_hash: str

    def __post_init__(self) -> None:
        if self.source not in FROZEN_SOURCES:
            raise TASK039D2PreparationError("relation source is outside the D0 identity set")
        if self.source_step_direction not in SOURCE_DIRECTIONS:
            raise TASK039D2PreparationError("source step direction is not frozen")
        if self.target not in FROZEN_TARGETS:
            raise TASK039D2PreparationError("relation target is outside the D0 identity set")
        if self.target_response_direction not in TARGET_DIRECTIONS:
            raise TASK039D2PreparationError("target response direction is not frozen")
        if self.d1_selected_horizon_seconds not in HORIZONS:
            raise TASK039D2PreparationError("selected horizon is not a frozen D0 horizon")
        for field_name in (
            "source_noise_scale_reference",
            "source_threshold_reference",
            "source_stability_tolerance_reference",
            "target_scale_reference",
            "d1_directional_record_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content())

    def _content(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "confirmable_directional_relation_v1",
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "d1_selected_horizon_seconds": self.d1_selected_horizon_seconds,
            "source_noise_scale_reference": self.source_noise_scale_reference,
            "source_threshold_reference": self.source_threshold_reference,
            "source_stability_tolerance_reference": self.source_stability_tolerance_reference,
            "target_scale_reference": self.target_scale_reference,
            "d1_directional_record_hash": self.d1_directional_record_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._content(), "artifact_hash": self.artifact_hash}


@dataclass(frozen=True)
class SyntheticTrain3ValueMapV1:
    """Explicitly synthetic, path-free train3-like values."""

    fixture_id: str
    values: Mapping[str, Sequence[float]]
    synthetic_only: bool = True

    def __post_init__(self) -> None:
        if not self.fixture_id.startswith("synthetic_"):
            raise TASK039D2PreparationError("fixture_id must be clearly marked synthetic")
        if self.synthetic_only is not True:
            raise TASK039D2PreparationError("TASK-039D2-PREP accepts synthetic values only")
        normalized: dict[str, tuple[float, ...]] = {}
        lengths: set[int] = set()
        for name, values in self.values.items():
            if not isinstance(name, str) or not name:
                raise TASK039D2PreparationError("synthetic value names must be non-empty strings")
            sequence = tuple(float(item) for item in values)
            if any(not math.isfinite(item) for item in sequence):
                raise TASK039D2PreparationError("synthetic values must be finite")
            if len(sequence) < 10:
                raise TASK039D2PreparationError("synthetic sequences are too short")
            normalized[name] = sequence
            lengths.add(len(sequence))
        if len(lengths) != 1:
            raise TASK039D2PreparationError("synthetic sequences must share one timeline")
        object.__setattr__(self, "values", freeze_json(normalized))


@dataclass(frozen=True)
class TASK039D2ConfirmationResultV1:
    """Immutable single-relation synthetic confirmation result."""

    relation_binding_hash: str
    d1_directional_record_hash: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_horizon_seconds: int
    parameter_ledger_bindings_hash: str
    usable_response_count: int
    right_censored_count: int
    selected_directional_consistency: float
    opposite_directional_consistency: float
    median_target_response: float | None
    robust_effect_ratio: float
    source_direction_unchanged: bool
    target_direction_unchanged: bool
    fit_parameters_reused_without_retuning: bool
    status: str

    def __post_init__(self) -> None:
        require_sha256(self.relation_binding_hash, "relation_binding_hash")
        require_sha256(self.d1_directional_record_hash, "d1_directional_record_hash")
        require_sha256(self.parameter_ledger_bindings_hash, "parameter_ledger_bindings_hash")
        _require_nonnegative_int(self.usable_response_count, "usable_response_count")
        _require_nonnegative_int(self.right_censored_count, "right_censored_count")
        _require_probability(
            self.selected_directional_consistency, "selected_directional_consistency"
        )
        _require_probability(
            self.opposite_directional_consistency, "opposite_directional_consistency"
        )
        if self.median_target_response is not None:
            require_finite(self.median_target_response, "median_target_response")
        effect = require_finite(self.robust_effect_ratio, "robust_effect_ratio")
        if effect < 0.0:
            raise TASK039D2PreparationError("robust_effect_ratio must be non-negative")
        if self.status not in {"calibration_confirmed", "calibration_conflict"}:
            raise TASK039D2PreparationError("unknown confirmation outcome")

    def _content(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039d2_confirmation_result_v1",
            "task_id": TASK_ID,
            "execution_mode": "synthetic_only_preparation",
            "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            "relation_binding_hash": self.relation_binding_hash,
            "d1_directional_record_hash": self.d1_directional_record_hash,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "parameter_ledger_bindings_hash": self.parameter_ledger_bindings_hash,
            "usable_response_count": self.usable_response_count,
            "right_censored_count": self.right_censored_count,
            "selected_directional_consistency": self.selected_directional_consistency,
            "opposite_directional_consistency": self.opposite_directional_consistency,
            "median_target_response": self.median_target_response,
            "robust_effect_ratio": self.robust_effect_ratio,
            "source_direction_unchanged": self.source_direction_unchanged,
            "target_direction_unchanged": self.target_direction_unchanged,
            "fit_parameters_reused_without_retuning": self.fit_parameters_reused_without_retuning,
            "alternative_horizon_search_performed": False,
            "opposite_direction_search_performed": False,
            "lower_ranked_fallback_used": False,
            "candidate_arm_provenance_visible": False,
            "method_provenance_joined": False,
            "status": self.status,
            "d2_real_execution_authorized": False,
            "rule_v2_authorized": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self._content())

    def to_dict(self) -> dict[str, Any]:
        return {**self._content(), "artifact_hash": self.artifact_hash}


def extract_train3_source_events_v1(
    value_map: SyntheticTrain3ValueMapV1,
    source_parameters: Mapping[str, D1SourceParameterRecordV1],
) -> dict[str, tuple[SustainedStepEventV1, ...]]:
    """Extract every frozen source once using only immutable D1 parameters."""

    if set(source_parameters) != set(FROZEN_SOURCES):
        raise TASK039D2PreparationError("event extraction requires all 12 source records")
    if not set(FROZEN_SOURCES).issubset(value_map.values):
        raise TASK039D2PreparationError("synthetic map is missing one or more frozen sources")
    extracted: dict[str, tuple[SustainedStepEventV1, ...]] = {}
    for source in FROZEN_SOURCES:
        parameter = source_parameters[source]
        if parameter.source != source:
            raise TASK039D2PreparationError("source parameter mapping identity mismatch")
        if parameter.parameter_status != "supported":
            extracted[source] = ()
            continue
        assert parameter.source_step_threshold is not None
        assert parameter.source_stability_tolerance is not None
        extracted[source] = extract_sustained_step_events_linear_v1(
            value_map.values[source],
            source_step_threshold=parameter.source_step_threshold,
            source_stability_tolerance=parameter.source_stability_tolerance,
        )
    return extracted


def classify_train3_all_source_isolation_v1(
    source_events: Mapping[str, Sequence[SustainedStepEventV1]],
) -> dict[str, tuple[tuple[SustainedStepEventV1, bool], ...]]:
    """Apply the indexed all-12-source inclusive +/-2 isolation contract."""

    return classify_all_source_isolation_indexed_v1(source_events)


def evaluate_train3_target_response_window_v1(
    values: Sequence[float], *, event_index: int, selected_horizon_seconds: int
) -> tuple[bool, float | None]:
    """Use the unchanged optimized three-sample response-window evaluation."""

    return optimized_target_response_v1(
        values,
        event_index=event_index,
        horizon_seconds=selected_horizon_seconds,
    )


def apply_exact_confirmation_gate_v1(
    *,
    usable_responses: int,
    source_direction_unchanged: bool,
    selected_consistency: float,
    opposite_consistency: float,
    robust_effect_ratio: float,
    fit_parameters_reused_without_retuning: bool,
) -> bool:
    """Validate metrics, then delegate the decision to the frozen D0 wrapper."""

    _require_nonnegative_int(usable_responses, "usable_responses")
    _require_probability(selected_consistency, "selected_consistency")
    _require_probability(opposite_consistency, "opposite_consistency")
    effect = require_finite(robust_effect_ratio, "robust_effect_ratio")
    if effect < 0.0:
        raise TASK039D2PreparationError("robust_effect_ratio must be non-negative")
    return train3_confirmation_gate_v1(
        usable_responses=usable_responses,
        source_direction_unchanged=source_direction_unchanged,
        selected_consistency=selected_consistency,
        opposite_consistency=opposite_consistency,
        robust_effect_ratio=effect,
        fit_parameters_reused_without_retuning=fit_parameters_reused_without_retuning,
    )


def _validated_inputs(
    *,
    relations: Sequence[ConfirmableDirectionalRelationV1],
    source_parameter_records: Sequence[D1SourceParameterRecordV1],
    target_parameter_records: Sequence[D1TargetParameterRecordV1],
    parameter_ledger_bindings: D1ParameterLedgerBindingsV1,
    value_map: SyntheticTrain3ValueMapV1,
) -> tuple[
    tuple[ConfirmableDirectionalRelationV1, ...],
    dict[str, D1SourceParameterRecordV1],
    dict[str, D1TargetParameterRecordV1],
]:
    relation_items = tuple(relations)
    source_by_name = {item.source: item for item in source_parameter_records}
    target_by_name = {item.target: item for item in target_parameter_records}
    if len(source_by_name) != len(tuple(source_parameter_records)):
        raise TASK039D2PreparationError("duplicate source parameter records are prohibited")
    if len(target_by_name) != len(tuple(target_parameter_records)):
        raise TASK039D2PreparationError("duplicate target parameter records are prohibited")
    if set(source_by_name) != set(FROZEN_SOURCES):
        raise TASK039D2PreparationError("all 12 D1 source parameter records are required")
    relation_targets = {item.target for item in relation_items}
    if set(target_by_name) != relation_targets:
        raise TASK039D2PreparationError("target records must exactly match confirmation targets")
    expected_value_names = set(FROZEN_SOURCES) | relation_targets
    if set(value_map.values) != expected_value_names:
        raise TASK039D2PreparationError(
            "synthetic map must contain exactly all 12 sources and confirmation targets"
        )
    identities: set[tuple[str, str, str]] = set()
    for source in FROZEN_SOURCES:
        record = source_by_name[source]
        if record.source_parameter_ledger_hash != (
            parameter_ledger_bindings.source_parameter_ledger_hash
        ):
            raise TASK039D2PreparationError("source record is not bound to the frozen D1 ledger")
    for target, record in target_by_name.items():
        if record.target_parameter_ledger_hash != (
            parameter_ledger_bindings.target_parameter_ledger_hash
        ):
            raise TASK039D2PreparationError("target record is not bound to the frozen D1 ledger")
        if record.target != target:
            raise TASK039D2PreparationError("target parameter mapping identity mismatch")
    for relation in relation_items:
        identity = (relation.source, relation.target, relation.source_step_direction)
        if identity in identities:
            raise TASK039D2PreparationError("duplicate confirmable relation identity")
        identities.add(identity)
        source_record = source_by_name[relation.source]
        target_record = target_by_name[relation.target]
        if source_record.parameter_status != "supported":
            raise TASK039D2PreparationError("confirmable relation requires supported D1 parameters")
        source_refs = {
            relation.source_noise_scale_reference,
            relation.source_threshold_reference,
            relation.source_stability_tolerance_reference,
        }
        if source_refs != {source_record.d1_parameter_record_hash}:
            raise TASK039D2PreparationError("relation source parameter references do not match D1")
        if relation.target_scale_reference != target_record.d1_parameter_record_hash:
            raise TASK039D2PreparationError("relation target scale reference does not match D1")
    return relation_items, source_by_name, target_by_name


def confirm_synthetic_relations_v1(
    *,
    relations: Sequence[ConfirmableDirectionalRelationV1],
    source_parameter_records: Sequence[D1SourceParameterRecordV1],
    target_parameter_records: Sequence[D1TargetParameterRecordV1],
    parameter_ledger_bindings: D1ParameterLedgerBindingsV1,
    value_map: SyntheticTrain3ValueMapV1,
) -> tuple[TASK039D2ConfirmationResultV1, ...]:
    """Confirm fixed D1 relations once on an explicitly synthetic value map."""

    relation_items, source_by_name, target_by_name = _validated_inputs(
        relations=relations,
        source_parameter_records=source_parameter_records,
        target_parameter_records=target_parameter_records,
        parameter_ledger_bindings=parameter_ledger_bindings,
        value_map=value_map,
    )
    source_events = extract_train3_source_events_v1(value_map, source_by_name)
    isolated_events = classify_train3_all_source_isolation_v1(source_events)
    results: list[TASK039D2ConfirmationResultV1] = []
    for relation in relation_items:
        selected_events = (
            event
            for event, isolated in isolated_events[relation.source]
            if isolated and event.direction == relation.source_step_direction
        )
        responses: list[float] = []
        right_censored_count = 0
        for event in selected_events:
            right_censored, response = evaluate_train3_target_response_window_v1(
                value_map.values[relation.target],
                event_index=event.event_index,
                selected_horizon_seconds=relation.d1_selected_horizon_seconds,
            )
            if right_censored:
                right_censored_count += 1
            else:
                assert response is not None
                responses.append(response)
        scale = target_by_name[relation.target].target_noise_scale
        increase_matches = sum(response > scale for response in responses)
        decrease_matches = sum(response < -scale for response in responses)
        if relation.target_response_direction == "increase":
            selected_matches, opposite_matches = increase_matches, decrease_matches
        else:
            selected_matches, opposite_matches = decrease_matches, increase_matches
        usable = len(responses)
        selected_consistency = selected_matches / usable if usable else 0.0
        opposite_consistency = opposite_matches / usable if usable else 0.0
        median_response = float(statistics.median(responses)) if responses else None
        robust_effect_ratio = (
            abs(median_response) / scale if median_response is not None else 0.0
        )
        target_direction_unchanged = selected_consistency > opposite_consistency
        confirmed = apply_exact_confirmation_gate_v1(
            usable_responses=usable,
            source_direction_unchanged=True,
            selected_consistency=selected_consistency,
            opposite_consistency=opposite_consistency,
            robust_effect_ratio=robust_effect_ratio,
            fit_parameters_reused_without_retuning=True,
        )
        results.append(
            TASK039D2ConfirmationResultV1(
                relation_binding_hash=relation.artifact_hash,
                d1_directional_record_hash=relation.d1_directional_record_hash,
                source=relation.source,
                source_step_direction=relation.source_step_direction,
                target=relation.target,
                target_response_direction=relation.target_response_direction,
                selected_horizon_seconds=relation.d1_selected_horizon_seconds,
                parameter_ledger_bindings_hash=parameter_ledger_bindings.artifact_hash,
                usable_response_count=usable,
                right_censored_count=right_censored_count,
                selected_directional_consistency=selected_consistency,
                opposite_directional_consistency=opposite_consistency,
                median_target_response=median_response,
                robust_effect_ratio=robust_effect_ratio,
                source_direction_unchanged=True,
                target_direction_unchanged=target_direction_unchanged,
                fit_parameters_reused_without_retuning=True,
                status=("calibration_confirmed" if confirmed else "calibration_conflict"),
            )
        )
    return tuple(results)


_AUTHORIZATION_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_type",
        "task_id",
        "authorization_scope",
        "confirmation_policy_hash",
        "train3_file_hash",
        "d1_parameter_ledger_bindings_hash",
        "real_hai_train3_access_authorized",
        "d1_private_ledger_access_authorized",
        "train1_train2_access_authorized",
        "train4_test_label_attack_access_authorized",
        "rule_v2_authorized",
        "artifact_hash",
    }
)


@dataclass(frozen=True)
class TASK039D2AuthorizationV1:
    """Validator for a future external authorization artifact; no instance exists here."""

    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        reject_unknown_fields(self.payload, _AUTHORIZATION_FIELDS, "task039d2_authorization_v1")
        if set(self.payload) != set(_AUTHORIZATION_FIELDS):
            raise TASK039D2PreparationError("future D2 authorization fields are incomplete")
        value = thaw_json(self.payload)
        if value["schema_version"] != V6_FOUNDATION_SCHEMA_VERSION:
            raise TASK039D2PreparationError("future D2 authorization schema is unsupported")
        if value["artifact_type"] != "task039d2_authorization_v1":
            raise TASK039D2PreparationError("future D2 authorization type is invalid")
        if value["task_id"] != "TASK-039D2":
            raise TASK039D2PreparationError("future D2 task identity is invalid")
        if value["authorization_scope"] != "one_way_train3_confirmation":
            raise TASK039D2PreparationError("future D2 scope is invalid")
        if value["confirmation_policy_hash"] != CONFIRMATION_POLICY_HASH:
            raise TASK039D2PreparationError("future D2 policy binding is invalid")
        require_sha256(value["train3_file_hash"], "train3_file_hash")
        require_sha256(
            value["d1_parameter_ledger_bindings_hash"],
            "d1_parameter_ledger_bindings_hash",
        )
        if not value["real_hai_train3_access_authorized"]:
            raise TASK039D2PreparationError("future D2 authorization does not permit train3")
        if not value["d1_private_ledger_access_authorized"]:
            raise TASK039D2PreparationError("future D2 authorization lacks D1 ledger custody")
        if value["train1_train2_access_authorized"]:
            raise TASK039D2PreparationError("future D2 authorization must remain one-way")
        if value["train4_test_label_attack_access_authorized"]:
            raise TASK039D2PreparationError("future D2 authorization exceeds train3 scope")
        if value["rule_v2_authorized"]:
            raise TASK039D2PreparationError("future D2 authorization cannot grant Rule v2")
        supplied_hash = value["artifact_hash"]
        require_sha256(supplied_hash, "artifact_hash")
        content = {key: item for key, item in value.items() if key != "artifact_hash"}
        if stable_hash_v1(content) != supplied_hash:
            raise TASK039D2PreparationError("future D2 authorization hash mismatch")
        object.__setattr__(self, "payload", freeze_json(value))


def require_real_execution_authorization_v1(
    authorization: TASK039D2AuthorizationV1 | None,
) -> TASK039D2AuthorizationV1:
    """Fail before any path operation when future D2 authority is absent."""

    if authorization is None:
        raise TASK039D2PreparationError("blocked_task039d2_authorization_absent")
    if not isinstance(authorization, TASK039D2AuthorizationV1):
        raise TASK039D2PreparationError("blocked_task039d2_authorization_invalid")
    return authorization


def run_future_real_confirmation_from_file_v1(
    train3_path: Path,
    *,
    authorization: TASK039D2AuthorizationV1 | None = None,
) -> None:
    """Guarded future entry point; this preparation branch has no real runner."""

    require_real_execution_authorization_v1(authorization)
    _ = train3_path
    raise TASK039D2PreparationError("blocked_task039d2_real_runner_not_implemented")


def build_synthetic_preparation_execution_receipt_v1() -> dict[str, Any]:
    """Build a public, self-hashed receipt containing no scientific results."""

    return _self_hashed(
        {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039d2_execution_receipt_v1",
            "task_id": TASK_ID,
            "status": PREPARATION_STATUS,
            "base_commit": BASE_COMMIT,
            "branch": BRANCH,
            "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            "execution_mode": "synthetic_only_preparation",
            "synthetic_cases": list(SYNTHETIC_CASES),
            "no_retuning_checks": list(NO_RETUNING_CHECKS),
            "arm_blindness_passed": True,
            "optimized_event_extraction_reused": True,
            "indexed_all_source_isolation_reused": True,
            "optimized_target_response_reused": True,
            "d1_optimized_implementation_modified": False,
            "real_hai_files_accessed": False,
            "d1_private_ledgers_accessed": False,
            "d2_authorization_present": False,
            "real_d2_execution_possible": False,
            "method_provenance_joined": False,
            "rule_v2_authorized": False,
            "claim_boundary": (
                "Implementation and synthetic semantic preparation only; not a D2 "
                "scientific confirmation result or execution authority."
            ),
        }
    )


__all__ = [
    "BASE_COMMIT",
    "BRANCH",
    "CONFIRMATION_POLICY_HASH",
    "D2_REAL_EXECUTION_AUTHORIZED",
    "D1ParameterLedgerBindingsV1",
    "D1SourceParameterRecordV1",
    "D1TargetParameterRecordV1",
    "ConfirmableDirectionalRelationV1",
    "FROZEN_CONFIRMATION_CONTROLS",
    "FrozenConfirmationControlsV1",
    "NO_RETUNING_CHECKS",
    "PREPARATION_STATUS",
    "SOURCE_DIRECTIONS",
    "SYNTHETIC_CASES",
    "SyntheticTrain3ValueMapV1",
    "TARGET_DIRECTIONS",
    "TASK039D2AuthorizationV1",
    "TASK039D2ConfirmationResultV1",
    "TASK039D2PreparationError",
    "apply_exact_confirmation_gate_v1",
    "build_synthetic_preparation_execution_receipt_v1",
    "classify_train3_all_source_isolation_v1",
    "confirm_synthetic_relations_v1",
    "evaluate_train3_target_response_window_v1",
    "extract_train3_source_events_v1",
    "require_real_execution_authorization_v1",
    "run_future_real_confirmation_from_file_v1",
]
