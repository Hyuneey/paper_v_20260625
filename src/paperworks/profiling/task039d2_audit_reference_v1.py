"""Independent synthetic reference mathematics for TASK-039D2 audit preparation.

This module reconstructs the frozen D0/BR1 confirmation semantics directly.
It does not import or call the TASK-039D2 confirmation engine, open files, or
grant any real-data or construction authority.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, Mapping, NamedTuple, Sequence

from paperworks.v6.common import (
    V6_FOUNDATION_SCHEMA_VERSION,
    V6FoundationError,
    freeze_json,
    require_finite,
    require_sha256,
    stable_hash_v1,
)
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCE_ROLES,
    FROZEN_SOURCES,
    FROZEN_TARGETS,
    HORIZONS,
)


TASK_ID = "TASK-039D2-AUDIT-PREP"
BASE_COMMIT = "301fb636b6944e2d2d86be4646605a3d38585165"
BRANCH = "task-039d2-audit-prep"
PREPARATION_STATUS = "passed_task039d2_audit_preparation"
CONFIRMATION_POLICY_HASH = (
    "83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27"
)
METHOD_COMPARISON_POLICY_HASH = (
    "0ccc7a97a5e9b3fe1e5a8a54828ec8f8f7e6482c62eb63f7df62d804c8cae39e"
)

EXPECTED_D2_DIRECTIONAL_INPUT_COUNT = 45
EXPECTED_D2_SUPPORTED_PAIR_COUNT = 25
D2_AUDIT_REAL_EXECUTION_AUTHORIZED = False
D1_PRIVATE_LEDGER_ACCESS_AUTHORIZED = False
D2_RESULT_AUDITED = False
RULE_V2_AUTHORIZED = False

SOURCE_DIRECTIONS = ("step_up", "step_down")
TARGET_DIRECTIONS = ("increase", "decrease")
SOURCE_PARAMETER_STATUSES = ("supported", "insufficient_nontrivial_amplitudes")
PARAMETER_CLASS = "normal_relation_profile_fit_derived"


class TASK039D2AuditPreparationError(V6FoundationError):
    """Raised when an audit-preparation boundary or invariant fails closed."""


def _nonnegative_integer(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TASK039D2AuditPreparationError(
            f"{field_name} must be a non-negative integer"
        )


def _probability(value: float, field_name: str) -> float:
    result = require_finite(value, field_name)
    if not 0.0 <= result <= 1.0:
        raise TASK039D2AuditPreparationError(
            f"{field_name} must be between zero and one"
        )
    return result


@dataclass(frozen=True)
class AuditFrozenConfirmationPolicyV1:
    """Audit-side copy of constants already frozen by D0/BR1."""

    pre_window_seconds: int = 5
    post_window_seconds: int = 5
    minimum_stability_fraction: float = 0.80
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
        expected: Mapping[str, Any] = {
            "pre_window_seconds": 5,
            "post_window_seconds": 5,
            "minimum_stability_fraction": 0.80,
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
                raise TASK039D2AuditPreparationError(
                    f"audit retuning is prohibited: {field_name} differs from D0"
                )


FROZEN_AUDIT_POLICY = AuditFrozenConfirmationPolicyV1()


class AuditStepEventV1(NamedTuple):
    event_index: int
    direction: str
    pre_level: float
    post_level: float
    step_amplitude: float
    pre_stability_fraction: float
    post_stability_fraction: float


@dataclass(frozen=True)
class AuditD1SourceParameterV1:
    """Exact-hash wrapper for a D1-shaped source parameter record."""

    source: str
    semantic_role: str
    source_noise_scale: float
    nontrivial_amplitude_count: int
    source_step_threshold: float | None
    source_stability_tolerance: float | None
    parameter_status: str
    fit_file_bindings: tuple[str, str]
    d1_record_hash: str
    d1_source_ledger_hash: str

    def __post_init__(self) -> None:
        if self.source not in FROZEN_SOURCES:
            raise TASK039D2AuditPreparationError("source is outside the frozen identity set")
        if self.semantic_role != FROZEN_SOURCE_ROLES[self.source]:
            raise TASK039D2AuditPreparationError("source semantic role mismatch")
        noise = require_finite(self.source_noise_scale, "source_noise_scale")
        if noise < 0.0:
            raise TASK039D2AuditPreparationError("source noise scale must be non-negative")
        _nonnegative_integer(
            self.nontrivial_amplitude_count, "nontrivial_amplitude_count"
        )
        if self.parameter_status not in SOURCE_PARAMETER_STATUSES:
            raise TASK039D2AuditPreparationError("unknown D1 source parameter status")
        if self.parameter_status == "supported":
            threshold = require_finite(
                self.source_step_threshold, "source_step_threshold"
            )
            tolerance = require_finite(
                self.source_stability_tolerance, "source_stability_tolerance"
            )
            if threshold <= 0.0 or tolerance < 0.0:
                raise TASK039D2AuditPreparationError(
                    "supported D1 source parameters are invalid"
                )
        elif (
            self.source_step_threshold is not None
            or self.source_stability_tolerance is not None
        ):
            raise TASK039D2AuditPreparationError(
                "unsupported D1 source cannot carry derived thresholds"
            )
        if len(self.fit_file_bindings) != 2:
            raise TASK039D2AuditPreparationError(
                "D1 source record must bind exactly two fit files"
            )
        for index, digest in enumerate(self.fit_file_bindings):
            require_sha256(digest, f"fit_file_bindings[{index}]")
        require_sha256(self.d1_record_hash, "d1_record_hash")
        require_sha256(self.d1_source_ledger_hash, "d1_source_ledger_hash")
        if stable_hash_v1(self._d1_content()) != self.d1_record_hash:
            raise TASK039D2AuditPreparationError("D1 source record hash mismatch")

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
class AuditD1TargetParameterV1:
    """Exact-hash wrapper for a D1-shaped target parameter record."""

    target: str
    target_noise_scale: float
    fit_file_bindings: tuple[str, str]
    d1_record_hash: str
    d1_target_ledger_hash: str

    def __post_init__(self) -> None:
        if self.target not in FROZEN_TARGETS:
            raise TASK039D2AuditPreparationError("target is outside the frozen identity set")
        scale = require_finite(self.target_noise_scale, "target_noise_scale")
        if scale <= 0.0:
            raise TASK039D2AuditPreparationError("target noise scale must be positive")
        if len(self.fit_file_bindings) != 2:
            raise TASK039D2AuditPreparationError(
                "D1 target record must bind exactly two fit files"
            )
        for index, digest in enumerate(self.fit_file_bindings):
            require_sha256(digest, f"fit_file_bindings[{index}]")
        require_sha256(self.d1_record_hash, "d1_record_hash")
        require_sha256(self.d1_target_ledger_hash, "d1_target_ledger_hash")
        if stable_hash_v1(self._d1_content()) != self.d1_record_hash:
            raise TASK039D2AuditPreparationError("D1 target record hash mismatch")

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
class AuditDirectionalInputV1:
    """One immutable, fit-supported D1 direction supplied to future D2 audit."""

    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_horizon_seconds: int
    d1_source_parameter_record_hash: str
    d1_target_parameter_record_hash: str
    d1_directional_record_hash: str

    def __post_init__(self) -> None:
        if self.source not in FROZEN_SOURCES:
            raise TASK039D2AuditPreparationError("directional input source is not frozen")
        if self.target not in FROZEN_TARGETS:
            raise TASK039D2AuditPreparationError("directional input target is not frozen")
        if self.source_step_direction not in SOURCE_DIRECTIONS:
            raise TASK039D2AuditPreparationError("source direction is not frozen")
        if self.target_response_direction not in TARGET_DIRECTIONS:
            raise TASK039D2AuditPreparationError("target direction is not frozen")
        if self.selected_horizon_seconds not in HORIZONS:
            raise TASK039D2AuditPreparationError("selected horizon is not frozen")
        for field_name in (
            "d1_source_parameter_record_hash",
            "d1_target_parameter_record_hash",
            "d1_directional_record_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)

    @property
    def identity(self) -> tuple[str, str, str]:
        return self.source, self.target, self.source_step_direction

    @property
    def binding_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "d1_source_parameter_record_hash": self.d1_source_parameter_record_hash,
            "d1_target_parameter_record_hash": self.d1_target_parameter_record_hash,
            "d1_directional_record_hash": self.d1_directional_record_hash,
        }


@dataclass(frozen=True)
class D2DirectionalInputSetV1:
    """Closed future-audit input contract for the exact 45 D2 directions."""

    directional_inputs: tuple[AuditDirectionalInputV1, ...]
    source_parameters: tuple[AuditD1SourceParameterV1, ...]
    target_parameters: tuple[AuditD1TargetParameterV1, ...]
    d1_source_ledger_hash: str
    d1_target_ledger_hash: str
    d1_directional_ledger_hash: str

    def __post_init__(self) -> None:
        for field_name in (
            "d1_source_ledger_hash",
            "d1_target_ledger_hash",
            "d1_directional_ledger_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        if len(self.directional_inputs) != EXPECTED_D2_DIRECTIONAL_INPUT_COUNT:
            raise TASK039D2AuditPreparationError(
                "future D2 audit requires exactly 45 directional inputs"
            )
        source_by_name = {item.source: item for item in self.source_parameters}
        target_by_name = {item.target: item for item in self.target_parameters}
        if len(source_by_name) != len(self.source_parameters):
            raise TASK039D2AuditPreparationError("duplicate D1 source parameter records")
        if len(target_by_name) != len(self.target_parameters):
            raise TASK039D2AuditPreparationError("duplicate D1 target parameter records")
        if set(source_by_name) != set(FROZEN_SOURCES):
            raise TASK039D2AuditPreparationError("all 12 D1 source records are required")
        if set(target_by_name) != set(FROZEN_TARGETS):
            raise TASK039D2AuditPreparationError("all 12 D1 target records are required")
        identities: set[tuple[str, str, str]] = set()
        directional_hashes: set[str] = set()
        pair_identities: set[tuple[str, str]] = set()
        for source, record in source_by_name.items():
            if record.d1_source_ledger_hash != self.d1_source_ledger_hash:
                raise TASK039D2AuditPreparationError(
                    "D1 source record ledger binding mismatch"
                )
            if record.source != source:
                raise TASK039D2AuditPreparationError("D1 source mapping mismatch")
        for target, record in target_by_name.items():
            if record.d1_target_ledger_hash != self.d1_target_ledger_hash:
                raise TASK039D2AuditPreparationError(
                    "D1 target record ledger binding mismatch"
                )
            if record.target != target:
                raise TASK039D2AuditPreparationError("D1 target mapping mismatch")
        for item in self.directional_inputs:
            identity = (item.source, item.target, item.source_step_direction)
            if identity in identities:
                raise TASK039D2AuditPreparationError("duplicate directional input identity")
            if item.d1_directional_record_hash in directional_hashes:
                raise TASK039D2AuditPreparationError("duplicate D1 directional record hash")
            identities.add(identity)
            directional_hashes.add(item.d1_directional_record_hash)
            pair_identities.add((item.source, item.target))
            source_record = source_by_name[item.source]
            target_record = target_by_name[item.target]
            if source_record.parameter_status != "supported":
                raise TASK039D2AuditPreparationError(
                    "D2 directional input must be D1 fit-supported"
                )
            if item.d1_source_parameter_record_hash != source_record.d1_record_hash:
                raise TASK039D2AuditPreparationError(
                    "directional input source record hash mismatch"
                )
            if item.d1_target_parameter_record_hash != target_record.d1_record_hash:
                raise TASK039D2AuditPreparationError(
                    "directional input target record hash mismatch"
                )
        if len(pair_identities) != EXPECTED_D2_SUPPORTED_PAIR_COUNT:
            raise TASK039D2AuditPreparationError(
                "future D2 audit requires exactly 25 supported pair contexts"
            )

    @property
    def binding_hash(self) -> str:
        return stable_hash_v1(
            {
                "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
                "d1_source_ledger_hash": self.d1_source_ledger_hash,
                "d1_target_ledger_hash": self.d1_target_ledger_hash,
                "d1_directional_ledger_hash": self.d1_directional_ledger_hash,
                "directional_input_hashes": [
                    item.binding_hash for item in self.directional_inputs
                ],
            }
        )


@dataclass(frozen=True)
class SyntheticAuditValueMapV1:
    """Explicitly synthetic, path-free values for all 12 sources and targets."""

    fixture_id: str
    values: Mapping[str, Sequence[float]]
    synthetic_only: bool = True

    def __post_init__(self) -> None:
        if not self.fixture_id.startswith("synthetic_audit_"):
            raise TASK039D2AuditPreparationError(
                "audit fixture must be clearly marked synthetic"
            )
        if self.synthetic_only is not True:
            raise TASK039D2AuditPreparationError(
                "audit preparation accepts synthetic values only"
            )
        if set(self.values) != set(FROZEN_SOURCES) | set(FROZEN_TARGETS):
            raise TASK039D2AuditPreparationError(
                "synthetic audit map requires exactly the frozen 24 variables"
            )
        normalized: dict[str, tuple[float, ...]] = {}
        lengths: set[int] = set()
        for name, raw_values in self.values.items():
            values = tuple(float(item) for item in raw_values)
            if len(values) < 10 or any(not math.isfinite(item) for item in values):
                raise TASK039D2AuditPreparationError(
                    "synthetic audit values must be finite and at least 10 samples"
                )
            normalized[name] = values
            lengths.add(len(values))
        if len(lengths) != 1:
            raise TASK039D2AuditPreparationError(
                "synthetic audit values must share one timeline"
            )
        object.__setattr__(self, "values", freeze_json(normalized))


@dataclass(frozen=True)
class SyntheticDirectionalAuditReplayV1:
    """Ephemeral synthetic replay fact, never a D2 scientific audit result."""

    input_binding_hash: str
    d1_source_parameter_record_hash: str
    d1_target_parameter_record_hash: str
    d1_directional_record_hash: str
    source: str
    source_step_direction: str
    target: str
    target_response_direction: str
    selected_horizon_seconds: int
    usable_response_count: int
    right_censored_count: int
    selected_consistency: float
    opposite_consistency: float
    median_target_response: float | None
    robust_effect_ratio: float
    status: str

    def __post_init__(self) -> None:
        for field_name in (
            "input_binding_hash",
            "d1_source_parameter_record_hash",
            "d1_target_parameter_record_hash",
            "d1_directional_record_hash",
        ):
            require_sha256(getattr(self, field_name), field_name)
        _nonnegative_integer(self.usable_response_count, "usable_response_count")
        _nonnegative_integer(self.right_censored_count, "right_censored_count")
        _probability(self.selected_consistency, "selected_consistency")
        _probability(self.opposite_consistency, "opposite_consistency")
        if self.median_target_response is not None:
            require_finite(self.median_target_response, "median_target_response")
        effect = require_finite(self.robust_effect_ratio, "robust_effect_ratio")
        if effect < 0.0:
            raise TASK039D2AuditPreparationError("robust effect must be non-negative")
        if self.status not in {"calibration_confirmed", "calibration_conflict"}:
            raise TASK039D2AuditPreparationError("unknown confirmation status")

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": V6_FOUNDATION_SCHEMA_VERSION,
            "artifact_type": "task039d2_audit_synthetic_direction_replay_v1",
            "task_id": TASK_ID,
            "confirmation_policy_hash": CONFIRMATION_POLICY_HASH,
            "synthetic_only": True,
            "input_binding_hash": self.input_binding_hash,
            "d1_source_parameter_record_hash": self.d1_source_parameter_record_hash,
            "d1_target_parameter_record_hash": self.d1_target_parameter_record_hash,
            "d1_directional_record_hash": self.d1_directional_record_hash,
            "source": self.source,
            "source_step_direction": self.source_step_direction,
            "target": self.target,
            "target_response_direction": self.target_response_direction,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "usable_response_count": self.usable_response_count,
            "right_censored_count": self.right_censored_count,
            "selected_consistency": self.selected_consistency,
            "opposite_consistency": self.opposite_consistency,
            "median_target_response": self.median_target_response,
            "robust_effect_ratio": self.robust_effect_ratio,
            "fit_parameters_reused_without_retuning": True,
            "alternative_horizon_search_performed": False,
            "opposite_direction_search_performed": False,
            "lower_ranked_fallback_used": False,
            "provenance_visible_during_replay": False,
            "status": self.status,
            "d2_result_audited": False,
            "rule_v2_authorized": False,
        }


def reconstruct_source_events_reference_v1(
    values: Sequence[float],
    *,
    source_step_threshold: float,
    source_stability_tolerance: float,
) -> tuple[AuditStepEventV1, ...]:
    """Independently reconstruct the frozen 5/5 step and clustering formula."""

    sequence = tuple(float(item) for item in values)
    if any(not math.isfinite(item) for item in sequence):
        raise TASK039D2AuditPreparationError("source values must be finite")
    threshold = require_finite(source_step_threshold, "source_step_threshold")
    tolerance = require_finite(
        source_stability_tolerance, "source_stability_tolerance"
    )
    if threshold <= 0.0 or tolerance < 0.0:
        raise TASK039D2AuditPreparationError("source parameters are invalid")
    events: list[AuditStepEventV1] = []
    for event_index in range(5, len(sequence) - 5 + 1):
        pre = sequence[event_index - 5 : event_index]
        post = sequence[event_index : event_index + 5]
        pre_level = float(statistics.median(pre))
        post_level = float(statistics.median(post))
        amplitude = post_level - pre_level
        if amplitude == 0.0 or abs(amplitude) < threshold:
            continue
        pre_fraction = sum(abs(item - pre_level) <= tolerance for item in pre) / 5.0
        post_fraction = sum(abs(item - post_level) <= tolerance for item in post) / 5.0
        if pre_fraction < 0.80 or post_fraction < 0.80:
            continue
        events.append(
            AuditStepEventV1(
                event_index=event_index,
                direction="step_up" if amplitude > 0.0 else "step_down",
                pre_level=pre_level,
                post_level=post_level,
                step_amplitude=amplitude,
                pre_stability_fraction=pre_fraction,
                post_stability_fraction=post_fraction,
            )
        )
    ordered = sorted(events, key=lambda item: item.event_index)
    if not ordered:
        return ()
    clusters: list[list[AuditStepEventV1]] = [[ordered[0]]]
    for item in ordered[1:]:
        if item.event_index - clusters[-1][-1].event_index <= 10:
            clusters[-1].append(item)
        else:
            clusters.append([item])
    return tuple(
        min(cluster, key=lambda item: (-abs(item.step_amplitude), item.event_index))
        for cluster in clusters
    )


def reconstruct_all_source_events_reference_v1(
    value_map: SyntheticAuditValueMapV1,
    source_parameters: Sequence[AuditD1SourceParameterV1],
) -> dict[str, tuple[AuditStepEventV1, ...]]:
    """Apply D1 parameters once to each of the 12 synthetic source streams."""

    source_by_name = {item.source: item for item in source_parameters}
    if len(source_by_name) != 12 or set(source_by_name) != set(FROZEN_SOURCES):
        raise TASK039D2AuditPreparationError("all 12 source parameters are required")
    result: dict[str, tuple[AuditStepEventV1, ...]] = {}
    for source in FROZEN_SOURCES:
        parameters = source_by_name[source]
        if parameters.parameter_status != "supported":
            result[source] = ()
            continue
        assert parameters.source_step_threshold is not None
        assert parameters.source_stability_tolerance is not None
        result[source] = reconstruct_source_events_reference_v1(
            value_map.values[source],
            source_step_threshold=parameters.source_step_threshold,
            source_stability_tolerance=parameters.source_stability_tolerance,
        )
    return result


def reconstruct_all_source_isolation_reference_v1(
    source_events: Mapping[str, Sequence[AuditStepEventV1]],
) -> dict[str, tuple[tuple[AuditStepEventV1, bool], ...]]:
    """Independent nested oracle for inclusive +/-2 all-source isolation."""

    if set(source_events) != set(FROZEN_SOURCES):
        raise TASK039D2AuditPreparationError("isolation requires all 12 sources")
    result: dict[str, tuple[tuple[AuditStepEventV1, bool], ...]] = {}
    for source in FROZEN_SOURCES:
        classified: list[tuple[AuditStepEventV1, bool]] = []
        for event in source_events[source]:
            isolated = not any(
                abs(event.event_index - other.event_index) <= 2
                for other_source in FROZEN_SOURCES
                if other_source != source
                for other in source_events[other_source]
            )
            classified.append((event, isolated))
        result[source] = tuple(classified)
    return result


def reconstruct_target_response_reference_v1(
    values: Sequence[float], *, event_index: int, selected_horizon_seconds: int
) -> tuple[bool, float | None]:
    """Independently reconstruct the frozen baseline and 3-sample response."""

    sequence = tuple(float(item) for item in values)
    if any(not math.isfinite(item) for item in sequence):
        raise TASK039D2AuditPreparationError("target values must be finite")
    if selected_horizon_seconds not in HORIZONS:
        raise TASK039D2AuditPreparationError("target horizon is not frozen")
    if event_index < 5 or event_index + selected_horizon_seconds + 3 > len(sequence):
        return True, None
    baseline = float(statistics.median(sequence[event_index - 5 : event_index]))
    response_level = float(
        statistics.median(
            sequence[
                event_index + selected_horizon_seconds :
                event_index + selected_horizon_seconds + 3
            ]
        )
    )
    response = response_level - baseline
    if not math.isfinite(response):
        raise TASK039D2AuditPreparationError("target response must be finite")
    return False, response


def reconstruct_confirmation_gate_reference_v1(
    *,
    usable_response_count: int,
    source_direction_unchanged: bool,
    selected_consistency: float,
    opposite_consistency: float,
    robust_effect_ratio: float,
    fit_parameters_reused_without_retuning: bool,
) -> bool:
    """Direct independent statement of the frozen all-conditions D2 gate."""

    _nonnegative_integer(usable_response_count, "usable_response_count")
    selected = _probability(selected_consistency, "selected_consistency")
    opposite = _probability(opposite_consistency, "opposite_consistency")
    effect = require_finite(robust_effect_ratio, "robust_effect_ratio")
    if effect < 0.0:
        raise TASK039D2AuditPreparationError("robust effect must be non-negative")
    return (
        usable_response_count >= 5
        and source_direction_unchanged
        and selected > opposite
        and selected >= 0.60
        and effect >= 1.0
        and fit_parameters_reused_without_retuning
    )


def replay_synthetic_directions_reference_v1(
    *,
    directional_inputs: Sequence[AuditDirectionalInputV1],
    source_parameters: Sequence[AuditD1SourceParameterV1],
    target_parameters: Sequence[AuditD1TargetParameterV1],
    value_map: SyntheticAuditValueMapV1,
) -> tuple[SyntheticDirectionalAuditReplayV1, ...]:
    """Replay fixed synthetic directions with no search, retuning, or provenance."""

    relation_items = tuple(directional_inputs)
    if not relation_items:
        return ()
    source_by_name = {item.source: item for item in source_parameters}
    target_by_name = {item.target: item for item in target_parameters}
    if set(source_by_name) != set(FROZEN_SOURCES):
        raise TASK039D2AuditPreparationError("replay requires all 12 source parameters")
    if set(target_by_name) != set(FROZEN_TARGETS):
        raise TASK039D2AuditPreparationError("replay requires all 12 target parameters")
    for relation in relation_items:
        source_record = source_by_name[relation.source]
        target_record = target_by_name[relation.target]
        if source_record.parameter_status != "supported":
            raise TASK039D2AuditPreparationError(
                "replayed direction must have supported D1 source parameters"
            )
        if relation.d1_source_parameter_record_hash != source_record.d1_record_hash:
            raise TASK039D2AuditPreparationError("source parameter hash mismatch")
        if relation.d1_target_parameter_record_hash != target_record.d1_record_hash:
            raise TASK039D2AuditPreparationError("target parameter hash mismatch")
    events = reconstruct_all_source_events_reference_v1(value_map, source_parameters)
    isolated = reconstruct_all_source_isolation_reference_v1(events)
    replayed: list[SyntheticDirectionalAuditReplayV1] = []
    for relation in relation_items:
        responses: list[float] = []
        censored = 0
        for event, is_isolated in isolated[relation.source]:
            if not is_isolated or event.direction != relation.source_step_direction:
                continue
            right_censored, response = reconstruct_target_response_reference_v1(
                value_map.values[relation.target],
                event_index=event.event_index,
                selected_horizon_seconds=relation.selected_horizon_seconds,
            )
            if right_censored:
                censored += 1
            else:
                assert response is not None
                responses.append(response)
        scale = target_by_name[relation.target].target_noise_scale
        increases = sum(response > scale for response in responses)
        decreases = sum(response < -scale for response in responses)
        if relation.target_response_direction == "increase":
            selected_matches, opposite_matches = increases, decreases
        else:
            selected_matches, opposite_matches = decreases, increases
        usable = len(responses)
        selected_consistency = selected_matches / usable if usable else 0.0
        opposite_consistency = opposite_matches / usable if usable else 0.0
        median_response = float(statistics.median(responses)) if responses else None
        robust_effect_ratio = (
            abs(median_response) / scale if median_response is not None else 0.0
        )
        confirmed = reconstruct_confirmation_gate_reference_v1(
            usable_response_count=usable,
            source_direction_unchanged=True,
            selected_consistency=selected_consistency,
            opposite_consistency=opposite_consistency,
            robust_effect_ratio=robust_effect_ratio,
            fit_parameters_reused_without_retuning=True,
        )
        replayed.append(
            SyntheticDirectionalAuditReplayV1(
                input_binding_hash=relation.binding_hash,
                d1_source_parameter_record_hash=(
                    relation.d1_source_parameter_record_hash
                ),
                d1_target_parameter_record_hash=(
                    relation.d1_target_parameter_record_hash
                ),
                d1_directional_record_hash=relation.d1_directional_record_hash,
                source=relation.source,
                source_step_direction=relation.source_step_direction,
                target=relation.target,
                target_response_direction=relation.target_response_direction,
                selected_horizon_seconds=relation.selected_horizon_seconds,
                usable_response_count=usable,
                right_censored_count=censored,
                selected_consistency=selected_consistency,
                opposite_consistency=opposite_consistency,
                median_target_response=median_response,
                robust_effect_ratio=robust_effect_ratio,
                status=("calibration_confirmed" if confirmed else "calibration_conflict"),
            )
        )
    return tuple(replayed)


__all__ = [
    "AuditD1SourceParameterV1",
    "AuditD1TargetParameterV1",
    "AuditDirectionalInputV1",
    "AuditFrozenConfirmationPolicyV1",
    "AuditStepEventV1",
    "BASE_COMMIT",
    "BRANCH",
    "CONFIRMATION_POLICY_HASH",
    "D1_PRIVATE_LEDGER_ACCESS_AUTHORIZED",
    "D2_AUDIT_REAL_EXECUTION_AUTHORIZED",
    "D2_RESULT_AUDITED",
    "D2DirectionalInputSetV1",
    "EXPECTED_D2_DIRECTIONAL_INPUT_COUNT",
    "EXPECTED_D2_SUPPORTED_PAIR_COUNT",
    "FROZEN_AUDIT_POLICY",
    "METHOD_COMPARISON_POLICY_HASH",
    "PREPARATION_STATUS",
    "RULE_V2_AUTHORIZED",
    "SyntheticAuditValueMapV1",
    "SyntheticDirectionalAuditReplayV1",
    "TASK039D2AuditPreparationError",
    "reconstruct_all_source_events_reference_v1",
    "reconstruct_all_source_isolation_reference_v1",
    "reconstruct_confirmation_gate_reference_v1",
    "reconstruct_source_events_reference_v1",
    "reconstruct_target_response_reference_v1",
    "replay_synthetic_directions_reference_v1",
]
