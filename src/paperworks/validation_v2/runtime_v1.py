"""Deterministic Formal V4 runtime for prospective VALIDATION V2 artifacts.

This module is intentionally separate from the immutable PILOT V1 COMMON-42
runtime.  The single-window entry replays the V2 authority before every window.
The prepared batch entry replays it before the first window, keeps immutable
descriptor/numeric lookups, and replays all bound bytes again at finalization.
No label or provider input is accepted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
import statistics
from types import MappingProxyType
from typing import Any, Mapping

from .formal_v4_authority_v1 import (
    V4_NUMERIC_ROLES,
    FormalV4AuthorityError,
    FormalV4AuthorizedRuntimeV1,
    FormalV4ExecutionContextV1,
    FormalV4RuleDescriptorV1,
    canonical_document_hash_v1,
    load_formal_v4_numeric_value_map_v1,
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
FORMAL_V4_PREPARED_RUNTIME_VERSION = "VALIDATION_V2_FORMAL_V4_PREPARED_RUNTIME_V1"
_PREPARED_RUNTIME_CAPABILITY = object()


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


@dataclass(frozen=True)
class FormalV4PreparedParametersV1:
    source_pre_count: int
    source_post_count: int
    target_baseline_count: int
    target_response_count: int
    minimum_source_stability_fraction: float
    source_step_threshold: float
    source_stability_tolerance: float
    target_noise_scale: float
    source_refractory_seconds: float
    cross_source_isolation_radius_seconds: float


@dataclass
class _PreparedRuntimeStateV1:
    active: bool = True
    evaluated_window_count: int = 0


@dataclass(frozen=True)
class FormalV4PreparedRuntimeSessionV1:
    bundle: FormalV4AuthorizedRuntimeV1
    execution_context: FormalV4ExecutionContextV1
    preparation_hash: str
    descriptor_count: int
    numeric_cache_document_loads: int
    descriptor_by_relation: Mapping[str, FormalV4RuleDescriptorV1] = field(
        repr=False, compare=False
    )
    parameters_by_relation: Mapping[str, FormalV4PreparedParametersV1] = field(
        repr=False, compare=False
    )
    repository_root: Path = field(repr=False, compare=False)
    _state: _PreparedRuntimeStateV1 = field(repr=False, compare=False)
    _capability: object | None = field(default=None, repr=False, compare=False)

    @property
    def runtime_prepared(self) -> bool:
        return self._capability is _PREPARED_RUNTIME_CAPABILITY and self._state.active


@dataclass(frozen=True)
class FormalV4PreparedRuntimeFinalizationReceiptV1:
    preparation_hash: str
    authorization_hash: str
    descriptor_set_hash: str
    descriptor_count: int
    evaluated_window_count: int
    numeric_cache_document_loads: int
    start_authority_replay_completed: bool
    end_authority_replay_completed: bool
    bound_bytes_unchanged: bool
    test1_label_accesses: int
    test2_accesses: int
    heldout_accesses: int
    provider_calls: int
    receipt_hash: str

    def body_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": "validation_v2_formal_v4_prepared_runtime_finalization_v1",
            "authorization_hash": self.authorization_hash,
            "bound_bytes_unchanged": self.bound_bytes_unchanged,
            "descriptor_count": self.descriptor_count,
            "descriptor_set_hash": self.descriptor_set_hash,
            "end_authority_replay_completed": self.end_authority_replay_completed,
            "evaluated_window_count": self.evaluated_window_count,
            "heldout_accesses": self.heldout_accesses,
            "numeric_cache_document_loads": self.numeric_cache_document_loads,
            "preparation_hash": self.preparation_hash,
            "provider_calls": self.provider_calls,
            "runtime_version": FORMAL_V4_PREPARED_RUNTIME_VERSION,
            "schema_version": "1.0.0",
            "start_authority_replay_completed": self.start_authority_replay_completed,
            "test1_label_accesses": self.test1_label_accesses,
            "test2_accesses": self.test2_accesses,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body_dict(), "receipt_hash": self.receipt_hash}


def validate_formal_v4_prepared_runtime_finalization_receipt_v1(
    receipt: FormalV4PreparedRuntimeFinalizationReceiptV1,
) -> str:
    """Replay a public-safe prepared-session finalization receipt."""

    if type(receipt) is not FormalV4PreparedRuntimeFinalizationReceiptV1:
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_RECEIPT_TYPE_INVALID", "receipt type differs"
        )
    if receipt.receipt_hash != canonical_document_hash_v1(receipt.body_dict()):
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_RECEIPT_HASH_MISMATCH", "receipt hash differs"
        )
    if (
        receipt.descriptor_count <= 0
        or receipt.evaluated_window_count < 0
        or receipt.numeric_cache_document_loads != 1
        or not receipt.start_authority_replay_completed
        or not receipt.end_authority_replay_completed
        or not receipt.bound_bytes_unchanged
        or receipt.test1_label_accesses != 0
        or receipt.test2_accesses != 0
        or receipt.heldout_accesses != 0
        or receipt.provider_calls != 0
    ):
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_RECEIPT_INVARIANT_FAILED",
            "finalization receipt safety invariant differs",
        )
    return receipt.receipt_hash


def _exact_positive_count(value: float, role: str) -> int:
    if value <= 0.0 or not value.is_integer():
        raise FormalV4AuthorityError("V4_RUNTIME_WINDOW_PARAMETER_INVALID", f"{role} must be positive integer-valued float")
    return int(value)


def _prepare_parameters_v1(
    authorized_values: tuple[tuple[str, str, float], ...],
) -> FormalV4PreparedParametersV1:
    values = {role: value for role, _reference_id, value in authorized_values}
    if tuple(values) != V4_NUMERIC_ROLES:
        raise FormalV4AuthorityError(
            "V4_RUNTIME_NUMERIC_COVERAGE_MISMATCH",
            "all numeric roles are required in order",
        )
    pre_count = _exact_positive_count(
        values["source_pre_window_seconds"], "source_pre_window_seconds"
    )
    post_count = _exact_positive_count(
        values["source_post_window_seconds"], "source_post_window_seconds"
    )
    baseline_count = _exact_positive_count(
        values["target_baseline_window_seconds"], "target_baseline_window_seconds"
    )
    response_count = _exact_positive_count(
        values["target_response_window_seconds"], "target_response_window_seconds"
    )
    minimum_stability = values["minimum_source_stability_fraction"]
    if not 0.0 <= minimum_stability <= 1.0:
        raise FormalV4AuthorityError(
            "V4_RUNTIME_STABILITY_FRACTION_INVALID",
            "minimum stability must be in [0,1]",
        )
    threshold = values["source_step_threshold"]
    tolerance = values["source_stability_tolerance"]
    noise = values["target_noise_scale"]
    refractory = values["source_refractory_seconds"]
    isolation = values["cross_source_isolation_radius_seconds"]
    if (
        threshold <= 0.0
        or tolerance < 0.0
        or noise <= 0.0
        or refractory < 0.0
        or isolation < 0.0
    ):
        raise FormalV4AuthorityError(
            "V4_RUNTIME_PARAMETER_DOMAIN_INVALID",
            "numeric parameter domain differs",
        )
    return FormalV4PreparedParametersV1(
        source_pre_count=pre_count,
        source_post_count=post_count,
        target_baseline_count=baseline_count,
        target_response_count=response_count,
        minimum_source_stability_fraction=minimum_stability,
        source_step_threshold=threshold,
        source_stability_tolerance=tolerance,
        target_noise_scale=noise,
        source_refractory_seconds=refractory,
        cross_source_isolation_radius_seconds=isolation,
    )


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


def _execute_with_prepared_parameters_v1(
    *,
    bundle: FormalV4AuthorizedRuntimeV1,
    descriptor: FormalV4RuleDescriptorV1,
    parameters: FormalV4PreparedParametersV1,
    window: FormalV4ObservationWindowV1,
) -> FormalV4RuntimeTraceV1:
    if type(window) is not FormalV4ObservationWindowV1:
        raise FormalV4AuthorityError("V4_RUNTIME_WINDOW_TYPE_INVALID", "window type differs")
    if (
        window.feature_contract_hash != bundle.authority.feature_contract_binding.content_sha256
        or window.file_contract_hash != bundle.authority.file_contract_binding.content_sha256
        or window.sampling_contract_hash != bundle.authority.sampling_contract_binding.content_sha256
    ):
        raise FormalV4AuthorityError("V4_RUNTIME_WINDOW_CONTRACT_MISMATCH", "window provenance differs")
    if window.target_response_start_index != window.event_index + descriptor.selected_horizon_seconds:
        raise FormalV4AuthorityError("V4_RUNTIME_HORIZON_COORDINATE_MISMATCH", "target response start does not replay horizon")
    if (
        len(window.source_pre_values) != parameters.source_pre_count
        or len(window.source_post_values) != parameters.source_post_count
    ):
        return _trace(bundle=bundle, descriptor=descriptor, window=window, outcome="ABSTAIN", reason="incomplete_source_window")
    pre_level = float(statistics.median(window.source_pre_values))
    post_level = float(statistics.median(window.source_post_values))
    amplitude = post_level - pre_level
    pre_fraction = sum(
        abs(value - pre_level) <= parameters.source_stability_tolerance
        for value in window.source_pre_values
    ) / parameters.source_pre_count
    post_fraction = sum(
        abs(value - post_level) <= parameters.source_stability_tolerance
        for value in window.source_post_values
    ) / parameters.source_post_count
    observed_direction = "step_up" if amplitude > 0.0 else "step_down"
    refractory_ok = (
        window.seconds_since_previous_source_trigger is None
        or window.seconds_since_previous_source_trigger
        >= parameters.source_refractory_seconds
    )
    isolation_ok = (
        window.seconds_to_nearest_other_source_trigger is None
        or window.seconds_to_nearest_other_source_trigger
        >= parameters.cross_source_isolation_radius_seconds
    )
    source_triggered = (
        amplitude != 0.0
        and abs(amplitude) >= parameters.source_step_threshold
        and pre_fraction >= parameters.minimum_source_stability_fraction
        and post_fraction >= parameters.minimum_source_stability_fraction
        and observed_direction == descriptor.source_direction
        and refractory_ok
        and isolation_ok
    )
    if not source_triggered:
        return _trace(bundle=bundle, descriptor=descriptor, window=window, outcome="ABSTAIN", reason="source_not_triggered")
    if (
        not window.future_window_complete
        or len(window.target_baseline_values) != parameters.target_baseline_count
        or len(window.target_response_values) != parameters.target_response_count
    ):
        return _trace(bundle=bundle, descriptor=descriptor, window=window, outcome="ABSTAIN", reason="incomplete_target_response_window")

    baseline = float(statistics.median(window.target_baseline_values))
    response_delta = float(statistics.median(window.target_response_values)) - baseline
    response_matched = (
        response_delta > parameters.target_noise_scale
        if descriptor.target_direction == "increase"
        else response_delta < -parameters.target_noise_scale
    )
    return _trace(
        bundle=bundle,
        descriptor=descriptor,
        window=window,
        outcome="PASS" if response_matched else "FAIL",
        reason="expected_response_observed" if response_matched else "expected_response_not_observed",
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
    matches = tuple(
        item for item in bundle.authority.descriptors
        if item.relation_id == window.relation_id
    )
    if len(matches) != 1:
        raise FormalV4AuthorityError(
            "V4_RUNTIME_RELATION_NOT_AUTHORIZED", "relation is outside portfolio"
        )
    descriptor = matches[0]
    authorized_values = load_formal_v4_numeric_values_v1(
        descriptor=descriptor,
        numeric_authority_binding=bundle.authority.numeric_authority_binding,
        repository_root=repository_root,
    )
    return _execute_with_prepared_parameters_v1(
        bundle=bundle,
        descriptor=descriptor,
        parameters=_prepare_parameters_v1(authorized_values),
        window=window,
    )


def prepare_formal_v4_runtime_session_v1(
    bundle: FormalV4AuthorizedRuntimeV1,
    *,
    execution_context: FormalV4ExecutionContextV1,
    repository_root: Path,
) -> FormalV4PreparedRuntimeSessionV1:
    """Replay authority once and prepare immutable O(1) runtime lookups."""

    authorization_hash = validate_formal_v4_runtime_authorization_v1(
        bundle,
        execution_context=execution_context,
        repository_root=repository_root,
    )
    descriptors = tuple(bundle.authority.descriptors)
    numeric_rows = load_formal_v4_numeric_value_map_v1(
        descriptors=descriptors,
        numeric_authority_binding=bundle.authority.numeric_authority_binding,
        repository_root=repository_root,
    )
    if tuple(item.relation_id for item in descriptors) != tuple(
        relation_id for relation_id, _values in numeric_rows
    ):
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_NUMERIC_ORDER_MISMATCH",
            "prepared numeric map differs from descriptor order",
        )
    descriptor_map = MappingProxyType({item.relation_id: item for item in descriptors})
    parameter_map = MappingProxyType({
        relation_id: _prepare_parameters_v1(values)
        for relation_id, values in numeric_rows
    })
    if len(descriptor_map) != len(descriptors) or set(descriptor_map) != set(parameter_map):
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_COVERAGE_MISMATCH",
            "prepared lookup coverage differs from authority",
        )
    preparation_payload = {
        "artifact_type": "validation_v2_formal_v4_prepared_runtime_session_v1",
        "authorization_hash": authorization_hash,
        "descriptor_count": len(descriptors),
        "descriptor_set_hash": bundle.authority.descriptor_set_hash,
        "execution_context_hash": execution_context.context_hash,
        "numeric_authority_hash": bundle.authority.numeric_authority_binding.content_sha256,
        "numeric_cache_document_loads": 1,
        "runtime_version": FORMAL_V4_PREPARED_RUNTIME_VERSION,
        "schema_version": "1.0.0",
        "start_authority_replay_completed": True,
    }
    return FormalV4PreparedRuntimeSessionV1(
        bundle=bundle,
        execution_context=execution_context,
        preparation_hash=canonical_document_hash_v1(preparation_payload),
        descriptor_count=len(descriptors),
        numeric_cache_document_loads=1,
        descriptor_by_relation=descriptor_map,
        parameters_by_relation=parameter_map,
        repository_root=repository_root.resolve(strict=True),
        _state=_PreparedRuntimeStateV1(),
        _capability=_PREPARED_RUNTIME_CAPABILITY,
    )


def execute_prepared_formal_v4_rule_v1(
    session: FormalV4PreparedRuntimeSessionV1,
    *,
    window: FormalV4ObservationWindowV1,
) -> FormalV4RuntimeTraceV1:
    """Evaluate one provisional window without repeated bound-file I/O.

    A trace from this low-level entry is not releasable until the matching
    session finalization receipt has passed.  Scientific runners should prefer
    :func:`execute_formal_v4_batch_v1`, which withholds all traces until then.
    """

    if type(session) is not FormalV4PreparedRuntimeSessionV1 or not session.runtime_prepared:
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_CAPABILITY_MISSING",
            "prepared runtime session is missing, forged, or finalized",
        )
    if type(window) is not FormalV4ObservationWindowV1:
        raise FormalV4AuthorityError("V4_RUNTIME_WINDOW_TYPE_INVALID", "window type differs")
    descriptor = session.descriptor_by_relation.get(window.relation_id)
    parameters = session.parameters_by_relation.get(window.relation_id)
    if descriptor is None or parameters is None:
        raise FormalV4AuthorityError(
            "V4_RUNTIME_RELATION_NOT_AUTHORIZED", "relation is outside portfolio"
        )
    trace = _execute_with_prepared_parameters_v1(
        bundle=session.bundle,
        descriptor=descriptor,
        parameters=parameters,
        window=window,
    )
    session._state.evaluated_window_count += 1
    return trace


def finalize_formal_v4_runtime_session_v1(
    session: FormalV4PreparedRuntimeSessionV1,
) -> FormalV4PreparedRuntimeFinalizationReceiptV1:
    """Close the session and replay every bound artifact before returning a receipt."""

    if type(session) is not FormalV4PreparedRuntimeSessionV1:
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_SESSION_TYPE_INVALID", "prepared session type differs"
        )
    if session._capability is not _PREPARED_RUNTIME_CAPABILITY or not session._state.active:
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_ALREADY_FINALIZED",
            "prepared runtime session is forged or already finalized",
        )
    session._state.active = False
    observed_authorization_hash = validate_formal_v4_runtime_authorization_v1(
        session.bundle,
        execution_context=session.execution_context,
        repository_root=session.repository_root,
    )
    if observed_authorization_hash != session.bundle.receipt.authorization_hash:
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_AUTHORITY_CHANGED", "runtime authority changed"
        )
    provisional = FormalV4PreparedRuntimeFinalizationReceiptV1(
        preparation_hash=session.preparation_hash,
        authorization_hash=observed_authorization_hash,
        descriptor_set_hash=session.bundle.authority.descriptor_set_hash,
        descriptor_count=session.descriptor_count,
        evaluated_window_count=session._state.evaluated_window_count,
        numeric_cache_document_loads=session.numeric_cache_document_loads,
        start_authority_replay_completed=True,
        end_authority_replay_completed=True,
        bound_bytes_unchanged=True,
        test1_label_accesses=0,
        test2_accesses=0,
        heldout_accesses=0,
        provider_calls=0,
        receipt_hash="",
    )
    receipt = FormalV4PreparedRuntimeFinalizationReceiptV1(
        **{
            **provisional.__dict__,
            "receipt_hash": canonical_document_hash_v1(provisional.body_dict()),
        }
    )
    validate_formal_v4_prepared_runtime_finalization_receipt_v1(receipt)
    return receipt


def execute_formal_v4_batch_v1(
    bundle: FormalV4AuthorizedRuntimeV1,
    *,
    execution_context: FormalV4ExecutionContextV1,
    repository_root: Path,
    windows: tuple[FormalV4ObservationWindowV1, ...],
) -> tuple[
    tuple[FormalV4RuntimeTraceV1, ...],
    FormalV4PreparedRuntimeFinalizationReceiptV1,
]:
    """Evaluate a closed window batch and release traces only after end replay."""

    if type(windows) is not tuple:
        raise FormalV4AuthorityError(
            "V4_PREPARED_RUNTIME_WINDOW_BATCH_INVALID",
            "window batch must be an exact tuple",
        )
    session = prepare_formal_v4_runtime_session_v1(
        bundle,
        execution_context=execution_context,
        repository_root=repository_root,
    )
    traces: list[FormalV4RuntimeTraceV1] = []
    try:
        for window in windows:
            traces.append(execute_prepared_formal_v4_rule_v1(session, window=window))
        receipt = finalize_formal_v4_runtime_session_v1(session)
    except Exception:
        session._state.active = False
        raise
    return tuple(traces), receipt
