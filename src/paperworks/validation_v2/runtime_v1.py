"""Deterministic Formal V4 runtime for prospective VALIDATION V2 artifacts.

This module is intentionally separate from the immutable PILOT V1 COMMON-42
runtime.  Every public execution entry replays the V2 authority and the actual
repository-bound execution context before observing a synthetic or scientific
window.  No label or provider input is accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import statistics
from typing import Any

from .formal_v4_authority_v1 import (
    V4_NUMERIC_ROLES,
    FormalV4AuthorityError,
    FormalV4AuthorizedRuntimeV1,
    FormalV4ExecutionContextV1,
    FormalV4RuleDescriptorV1,
    canonical_document_hash_v1,
    load_formal_v4_numeric_values_v1,
    validate_formal_v4_runtime_authorization_v1,
)
from .runtime_policy_v1 import (
    FORMAL_V4_RESPONSE_POLICY,
    FORMAL_V4_RESPONSE_POLICY_HASH,
    FORMAL_V4_TRACE_CONTRACT,
    FORMAL_V4_TRACE_CONTRACT_HASH,
    FORMAL_V4_TRIGGER_POLICY,
    FORMAL_V4_TRIGGER_POLICY_HASH,
)


FORMAL_V4_RUNTIME_VERSION = "VALIDATION_V2_FORMAL_V4_RUNTIME_V1"


@dataclass(frozen=True)
class FormalV4ObservationWindowV1:
    opportunity_id: str
    relation_id: str
    feature_contract_hash: str
    file_contract_hash: str
    sampling_contract_hash: str
    event_index: int
    target_response_start_index: int
    source_pre_values: tuple[float, ...]
    source_post_values: tuple[float, ...]
    target_baseline_values: tuple[float, ...]
    target_response_values: tuple[float, ...]
    seconds_since_previous_source_trigger: float | None
    seconds_to_nearest_other_source_trigger: float | None
    future_window_complete: bool

    def __post_init__(self) -> None:
        if type(self.opportunity_id) is not str or not self.opportunity_id:
            raise FormalV4AuthorityError("V4_RUNTIME_OPPORTUNITY_ID_INVALID", "opportunity ID differs")
        if type(self.relation_id) is not str or not self.relation_id:
            raise FormalV4AuthorityError("V4_RUNTIME_RELATION_ID_INVALID", "relation ID differs")
        for name in ("feature_contract_hash", "file_contract_hash", "sampling_contract_hash"):
            value = getattr(self, name)
            if type(value) is not str or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise FormalV4AuthorityError("V4_RUNTIME_CONTRACT_HASH_INVALID", f"{name} differs")
        if type(self.event_index) is not int or self.event_index < 0:
            raise FormalV4AuthorityError("V4_RUNTIME_EVENT_INDEX_INVALID", "event index differs")
        if type(self.target_response_start_index) is not int or self.target_response_start_index < 0:
            raise FormalV4AuthorityError("V4_RUNTIME_RESPONSE_INDEX_INVALID", "response start index differs")
        for name in (
            "source_pre_values",
            "source_post_values",
            "target_baseline_values",
            "target_response_values",
        ):
            values = getattr(self, name)
            if type(values) is not tuple:
                raise FormalV4AuthorityError("V4_RUNTIME_WINDOW_TYPE_INVALID", f"{name} must be exact tuple")
            if any(type(value) is not float or not math.isfinite(value) for value in values):
                raise FormalV4AuthorityError("V4_RUNTIME_WINDOW_VALUE_INVALID", f"{name} contains invalid value")
        for name in (
            "seconds_since_previous_source_trigger",
            "seconds_to_nearest_other_source_trigger",
        ):
            value = getattr(self, name)
            if value is not None and (type(value) is not float or not math.isfinite(value) or value < 0.0):
                raise FormalV4AuthorityError("V4_RUNTIME_DISTANCE_INVALID", f"{name} differs")
        if type(self.future_window_complete) is not bool:
            raise FormalV4AuthorityError("V4_RUNTIME_FUTURE_FLAG_INVALID", "future flag must be exact bool")


@dataclass(frozen=True)
class FormalV4RuntimeTraceV1:
    opportunity_id: str
    relation_id: str
    descriptor_hash: str
    authorization_hash: str
    execution_context_hash: str
    final_outcome: str
    reason: str
    alarm_emitted: bool
    trace_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "alarm_emitted": self.alarm_emitted,
            "authorization_hash": self.authorization_hash,
            "descriptor_hash": self.descriptor_hash,
            "execution_context_hash": self.execution_context_hash,
            "final_outcome": self.final_outcome,
            "opportunity_id": self.opportunity_id,
            "reason": self.reason,
            "relation_id": self.relation_id,
            "trace_hash": self.trace_hash,
        }


def _exact_positive_count(value: float, role: str) -> int:
    if value <= 0.0 or not value.is_integer():
        raise FormalV4AuthorityError("V4_RUNTIME_WINDOW_PARAMETER_INVALID", f"{role} must be positive integer-valued float")
    return int(value)


def _trace(
    *,
    bundle: FormalV4AuthorizedRuntimeV1,
    descriptor: FormalV4RuleDescriptorV1,
    window: FormalV4ObservationWindowV1,
    outcome: str,
    reason: str,
) -> FormalV4RuntimeTraceV1:
    payload = {
        "alarm_emitted": outcome == "FAIL",
        "authorization_hash": bundle.receipt.authorization_hash,
        "descriptor_hash": descriptor.descriptor_hash,
        "execution_context_hash": bundle.execution_context.context_hash,
        "final_outcome": outcome,
        "opportunity_id": window.opportunity_id,
        "reason": reason,
        "relation_id": descriptor.relation_id,
        "runtime_version": FORMAL_V4_RUNTIME_VERSION,
    }
    return FormalV4RuntimeTraceV1(
        opportunity_id=window.opportunity_id,
        relation_id=descriptor.relation_id,
        descriptor_hash=descriptor.descriptor_hash,
        authorization_hash=bundle.receipt.authorization_hash,
        execution_context_hash=bundle.execution_context.context_hash,
        final_outcome=outcome,
        reason=reason,
        alarm_emitted=outcome == "FAIL",
        trace_hash=canonical_document_hash_v1(payload),
    )


def execute_formal_v4_rule_v1(
    bundle: FormalV4AuthorizedRuntimeV1,
    *,
    execution_context: FormalV4ExecutionContextV1,
    repository_root: Path,
    window: FormalV4ObservationWindowV1,
) -> FormalV4RuntimeTraceV1:
    """Evaluate one exact V2 descriptor after full execution-context replay."""

    validate_formal_v4_runtime_authorization_v1(
        bundle,
        execution_context=execution_context,
        repository_root=repository_root,
    )
    if type(window) is not FormalV4ObservationWindowV1:
        raise FormalV4AuthorityError("V4_RUNTIME_WINDOW_TYPE_INVALID", "window type differs")
    matches = [item for item in bundle.authority.descriptors if item.relation_id == window.relation_id]
    if len(matches) != 1:
        raise FormalV4AuthorityError("V4_RUNTIME_RELATION_NOT_AUTHORIZED", "relation is outside portfolio")
    descriptor = matches[0]
    if (
        window.feature_contract_hash != bundle.authority.feature_contract_binding.content_sha256
        or window.file_contract_hash != bundle.authority.file_contract_binding.content_sha256
        or window.sampling_contract_hash != bundle.authority.sampling_contract_binding.content_sha256
    ):
        raise FormalV4AuthorityError("V4_RUNTIME_WINDOW_CONTRACT_MISMATCH", "window provenance differs")
    if window.target_response_start_index != window.event_index + descriptor.selected_horizon_seconds:
        raise FormalV4AuthorityError("V4_RUNTIME_HORIZON_COORDINATE_MISMATCH", "target response start does not replay horizon")
    authorized_values = load_formal_v4_numeric_values_v1(
        descriptor=descriptor,
        numeric_authority_binding=bundle.authority.numeric_authority_binding,
        repository_root=repository_root,
    )
    values = {role: value for role, _reference_id, value in authorized_values}
    if tuple(values) != V4_NUMERIC_ROLES:
        raise FormalV4AuthorityError("V4_RUNTIME_NUMERIC_COVERAGE_MISMATCH", "all numeric roles are required in order")

    pre_count = _exact_positive_count(values["source_pre_window_seconds"], "source_pre_window_seconds")
    post_count = _exact_positive_count(values["source_post_window_seconds"], "source_post_window_seconds")
    baseline_count = _exact_positive_count(values["target_baseline_window_seconds"], "target_baseline_window_seconds")
    response_count = _exact_positive_count(values["target_response_window_seconds"], "target_response_window_seconds")
    minimum_stability = values["minimum_source_stability_fraction"]
    if not 0.0 <= minimum_stability <= 1.0:
        raise FormalV4AuthorityError("V4_RUNTIME_STABILITY_FRACTION_INVALID", "minimum stability must be in [0,1]")
    threshold = values["source_step_threshold"]
    tolerance = values["source_stability_tolerance"]
    noise = values["target_noise_scale"]
    refractory = values["source_refractory_seconds"]
    isolation = values["cross_source_isolation_radius_seconds"]
    if threshold <= 0.0 or tolerance < 0.0 or noise <= 0.0 or refractory < 0.0 or isolation < 0.0:
        raise FormalV4AuthorityError("V4_RUNTIME_PARAMETER_DOMAIN_INVALID", "numeric parameter domain differs")

    if len(window.source_pre_values) != pre_count or len(window.source_post_values) != post_count:
        return _trace(bundle=bundle, descriptor=descriptor, window=window, outcome="ABSTAIN", reason="incomplete_source_window")
    pre_level = float(statistics.median(window.source_pre_values))
    post_level = float(statistics.median(window.source_post_values))
    amplitude = post_level - pre_level
    pre_fraction = sum(abs(value - pre_level) <= tolerance for value in window.source_pre_values) / pre_count
    post_fraction = sum(abs(value - post_level) <= tolerance for value in window.source_post_values) / post_count
    observed_direction = "step_up" if amplitude > 0.0 else "step_down"
    refractory_ok = window.seconds_since_previous_source_trigger is None or window.seconds_since_previous_source_trigger >= refractory
    isolation_ok = window.seconds_to_nearest_other_source_trigger is None or window.seconds_to_nearest_other_source_trigger >= isolation
    source_triggered = (
        amplitude != 0.0
        and abs(amplitude) >= threshold
        and pre_fraction >= minimum_stability
        and post_fraction >= minimum_stability
        and observed_direction == descriptor.source_direction
        and refractory_ok
        and isolation_ok
    )
    if not source_triggered:
        return _trace(bundle=bundle, descriptor=descriptor, window=window, outcome="ABSTAIN", reason="source_not_triggered")
    if (
        not window.future_window_complete
        or len(window.target_baseline_values) != baseline_count
        or len(window.target_response_values) != response_count
    ):
        return _trace(bundle=bundle, descriptor=descriptor, window=window, outcome="ABSTAIN", reason="incomplete_target_response_window")

    baseline = float(statistics.median(window.target_baseline_values))
    response_delta = float(statistics.median(window.target_response_values)) - baseline
    response_matched = response_delta > noise if descriptor.target_direction == "increase" else response_delta < -noise
    return _trace(
        bundle=bundle,
        descriptor=descriptor,
        window=window,
        outcome="PASS" if response_matched else "FAIL",
        reason="expected_response_observed" if response_matched else "expected_response_not_observed",
    )
