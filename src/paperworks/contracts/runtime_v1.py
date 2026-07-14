"""Authorized deterministic runtime for the delayed-response MVP."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from paperworks.contracts.artifact_hashing import (
    ContractArtifactHashError,
    canonical_contract_artifact_sha256,
    verify_contract_artifact_hash,
    with_computed_artifact_hash,
)
from paperworks.contracts.graph_v1 import SamplingIntervalV1
from paperworks.contracts.runtime_authority import (
    RuntimeAuthorizationBundleV1,
    RuntimeAuthorizationError,
    verify_runtime_authorization_bundle,
)
from paperworks.contracts.schema_registry import SchemaRegistry, load_schema_registry


RUNTIME_VERSION = "task032e-runtime-1.0.0"
_TIME_FACTORS = {"milliseconds": 0.001, "seconds": 1.0, "minutes": 60.0}
_TRACE_OPERATORS = (
    "regime_check",
    "trigger_check",
    "lag_check",
    "window_check",
    "relation_check",
    "tolerance_check",
    "persistence_check",
    "abstention_check",
    "output",
)
_ABSTENTION_REASONS = frozenset({
    "regime_mismatch",
    "missing_input",
    "multiple_triggers",
    "missing_pre_trigger_baseline",
    "insufficient_post_trigger_coverage",
    "parameter_uncertainty",
    "input_variable_mismatch",
})


class RuntimeWindowModelError(ValueError):
    def __init__(self, issue_code: str, field_path: str, message: str) -> None:
        super().__init__(f"{issue_code} at {field_path}: {message}")
        self.issue_code = issue_code
        self.field_path = field_path
        self.message = message


class RuntimeV1Error(ValueError):
    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


@dataclass(frozen=True)
class DelayedResponseRuntimeWindowV1:
    input_window_id: str
    dataset_version: str
    subsystem: str
    operating_regime: str
    source_variable: str
    target_variable: str
    sampling_interval: SamplingIntervalV1
    start_offset: int
    end_offset: int
    offset_unit: str
    source_values: tuple[int | bool, ...]
    target_values: tuple[int | float | None, ...]
    created_at: str


@dataclass(frozen=True)
class RuntimeTraceStepV1:
    step: int
    operator: str
    result: str
    parameter_refs: tuple[str, ...]
    variable_refs: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeParameterValueV1:
    parameter_id: str
    parameter_hash: str
    value: int | float
    unit: str


@dataclass(frozen=True)
class RuntimeTraceV1:
    schema_version: str
    execution_id: str
    artifact_hash: str
    rule_id: str
    rule_hash: str
    verifier_result_ref: str
    input_window_id: str
    status: str
    trigger_satisfied: bool
    expected_effect_satisfied: bool | None
    violation_detected: bool
    violation_score: int | float
    abstained: bool
    satisfaction_trace: tuple[RuntimeTraceStepV1, ...]
    parameter_values_used: tuple[RuntimeParameterValueV1, ...]
    input_output_alignment_preserved: bool
    created_at: str


@dataclass(frozen=True)
class RuntimeExecutionOutcomeV1:
    authorization_id: str
    input_window_hash: str
    trace: RuntimeTraceV1
    trigger_index: int | None
    response_index: int | None
    abstention_reason: str | None
    runtime_version: str


def parse_runtime_window(document: Mapping[str, object]) -> DelayedResponseRuntimeWindowV1:
    snapshot = copy.deepcopy(dict(document))
    required = {
        "input_window_id", "dataset_version", "subsystem", "operating_regime",
        "source_variable", "target_variable", "sampling_interval", "start_offset",
        "end_offset", "offset_unit", "source_values", "target_values", "created_at",
    }
    if set(snapshot) != required:
        _window_fail("RUNTIME_WINDOW_FIELDS", "/", "window fields must match the closed model")
    try:
        interval = snapshot["sampling_interval"]
        if not isinstance(interval, Mapping) or set(interval) != {"value", "unit"}:
            _window_fail("RUNTIME_WINDOW_SAMPLING", "/sampling_interval", "sampling interval is invalid")
        interval_value = interval["value"]
        if isinstance(interval_value, bool) or not isinstance(interval_value, (int, float)):
            _window_fail("RUNTIME_WINDOW_SAMPLING", "/sampling_interval/value", "sampling interval must be numeric")
        source = snapshot["source_values"]
        target = snapshot["target_values"]
        if not isinstance(source, list) or not isinstance(target, list):
            _window_fail("RUNTIME_WINDOW_ARRAY_TYPE", "/source_values", "values must be arrays")
        if isinstance(snapshot["start_offset"], bool) or not isinstance(snapshot["start_offset"], int):
            _window_fail("RUNTIME_WINDOW_OFFSET_TYPE", "/start_offset", "start offset must be an integer")
        if isinstance(snapshot["end_offset"], bool) or not isinstance(snapshot["end_offset"], int):
            _window_fail("RUNTIME_WINDOW_OFFSET_TYPE", "/end_offset", "end offset must be an integer")
        window = DelayedResponseRuntimeWindowV1(
            input_window_id=str(snapshot["input_window_id"]),
            dataset_version=str(snapshot["dataset_version"]),
            subsystem=str(snapshot["subsystem"]),
            operating_regime=str(snapshot["operating_regime"]),
            source_variable=str(snapshot["source_variable"]),
            target_variable=str(snapshot["target_variable"]),
            sampling_interval=SamplingIntervalV1(interval_value, str(interval["unit"])),
            start_offset=snapshot["start_offset"],
            end_offset=snapshot["end_offset"],
            offset_unit=str(snapshot["offset_unit"]),
            source_values=tuple(source),
            target_values=tuple(target),
            created_at=str(snapshot["created_at"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, RuntimeWindowModelError):
            raise
        _window_fail("RUNTIME_WINDOW_TYPE", "/", "window field type is invalid")
    _validate_runtime_window(window)
    return window


def load_runtime_window(path: str | Path) -> DelayedResponseRuntimeWindowV1:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeWindowModelError("RUNTIME_WINDOW_JSON", "/", "window is not readable UTF-8 JSON") from exc
    if not isinstance(document, dict):
        _window_fail("RUNTIME_WINDOW_JSON", "/", "window must be a JSON object")
    return parse_runtime_window(document)


def runtime_window_to_dict(window: DelayedResponseRuntimeWindowV1) -> dict[str, Any]:
    return {
        "input_window_id": window.input_window_id,
        "dataset_version": window.dataset_version,
        "subsystem": window.subsystem,
        "operating_regime": window.operating_regime,
        "source_variable": window.source_variable,
        "target_variable": window.target_variable,
        "sampling_interval": {"value": window.sampling_interval.value, "unit": window.sampling_interval.unit},
        "start_offset": window.start_offset,
        "end_offset": window.end_offset,
        "offset_unit": window.offset_unit,
        "source_values": list(window.source_values),
        "target_values": list(window.target_values),
        "created_at": window.created_at,
    }


def canonical_runtime_window_bytes(window: DelayedResponseRuntimeWindowV1 | Mapping[str, Any]) -> bytes:
    document = runtime_window_to_dict(window) if isinstance(window, DelayedResponseRuntimeWindowV1) else copy.deepcopy(dict(window))
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def canonical_runtime_window_sha256(window: DelayedResponseRuntimeWindowV1 | Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_runtime_window_bytes(window)).hexdigest()


def parse_runtime_trace(
    document: Mapping[str, object], *, registry: SchemaRegistry | None = None
) -> RuntimeTraceV1:
    snapshot = copy.deepcopy(dict(document))
    report = (registry or load_schema_registry()).validate_artifact("runtime_trace", snapshot)
    if report.status != "valid":
        issue = report.issues[0] if report.issues else None
        raise RuntimeV1Error("RUNTIME_TRACE_STRUCTURAL_INVALID", issue.issue_code if issue else "registry error")
    try:
        verify_contract_artifact_hash(snapshot)
    except ContractArtifactHashError as exc:
        raise RuntimeV1Error(exc.issue_code, exc.message) from exc
    trace = _typed_runtime_trace(snapshot)
    if len(trace.satisfaction_trace) != 9 or tuple(item.operator for item in trace.satisfaction_trace) != _TRACE_OPERATORS:
        raise RuntimeV1Error("RUNTIME_TRACE_STEP_ORDER", "trace must contain the nine ordered MVP steps")
    if tuple(item.step for item in trace.satisfaction_trace) != tuple(range(1, 10)):
        raise RuntimeV1Error("RUNTIME_TRACE_STEP_NUMBER", "trace step numbers are invalid")
    if tuple(item.parameter_id for item in trace.parameter_values_used) != tuple(sorted(item.parameter_id for item in trace.parameter_values_used)):
        raise RuntimeV1Error("RUNTIME_TRACE_PARAMETER_ORDER", "parameter values must be sorted")
    parameter_ids = tuple(item.parameter_id for item in trace.parameter_values_used)
    if len(parameter_ids) != len(set(parameter_ids)):
        raise RuntimeV1Error("RUNTIME_TRACE_PARAMETER_DUPLICATE", "parameter values must be unique")
    if trace.abstained != (trace.status == "abstained"):
        raise RuntimeV1Error("RUNTIME_TRACE_STATUS_INCONSISTENT", "abstention status is inconsistent")
    if trace.abstained and (trace.violation_detected or trace.violation_score != 0):
        raise RuntimeV1Error("RUNTIME_TRACE_ABSTENTION_INCONSISTENT", "abstention cannot be an anomaly")
    if trace.violation_score not in {0, 0.0, 1, 1.0}:
        raise RuntimeV1Error("RUNTIME_TRACE_SCORE_UNSUPPORTED", "MVP violation score must be binary")
    return trace


def runtime_trace_to_dict(trace: RuntimeTraceV1) -> dict[str, Any]:
    return {
        "schema_version": trace.schema_version,
        "execution_id": trace.execution_id,
        "artifact_hash": trace.artifact_hash,
        "rule_id": trace.rule_id,
        "rule_hash": trace.rule_hash,
        "verifier_result_ref": trace.verifier_result_ref,
        "input_window_id": trace.input_window_id,
        "status": trace.status,
        "trigger_satisfied": trace.trigger_satisfied,
        "expected_effect_satisfied": trace.expected_effect_satisfied,
        "violation_detected": trace.violation_detected,
        "violation_score": trace.violation_score,
        "abstained": trace.abstained,
        "satisfaction_trace": [
            {"step": item.step, "operator": item.operator, "result": item.result,
             "parameter_refs": list(item.parameter_refs), "variable_refs": list(item.variable_refs)}
            for item in trace.satisfaction_trace
        ],
        "parameter_values_used": [
            {"parameter_id": item.parameter_id, "parameter_hash": item.parameter_hash,
             "value": item.value, "unit": item.unit}
            for item in trace.parameter_values_used
        ],
        "input_output_alignment_preserved": trace.input_output_alignment_preserved,
        "created_at": trace.created_at,
    }


def serialize_runtime_trace(trace: RuntimeTraceV1) -> str:
    return json.dumps(runtime_trace_to_dict(trace), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def canonical_runtime_trace_sha256(trace: RuntimeTraceV1) -> str:
    return canonical_contract_artifact_sha256(runtime_trace_to_dict(trace))


def execute_delayed_response_rule(
    authorization: RuntimeAuthorizationBundleV1,
    window: DelayedResponseRuntimeWindowV1,
    *,
    runtime_version: str = RUNTIME_VERSION,
) -> RuntimeExecutionOutcomeV1:
    if not isinstance(authorization, RuntimeAuthorizationBundleV1) or not authorization.runtime_authorized:
        raise RuntimeV1Error("RUNTIME_NOT_AUTHORIZED", "an authorized runtime bundle is required")
    _validate_authorization_for_execution(authorization)
    if not isinstance(window, DelayedResponseRuntimeWindowV1):
        raise RuntimeV1Error("RUNTIME_WINDOW_REQUIRED", "a typed runtime window is required")
    window_hash = canonical_runtime_window_sha256(window)
    execution_id = _execution_id(authorization.receipt.authorization_hash, window_hash, runtime_version, window.created_at)
    rule = authorization.accepted_rule
    parameters = authorization.artifacts.parameter_by_id

    mismatch = (
        window.dataset_version != rule.dataset_version
        or window.subsystem != rule.subsystem
        or window.operating_regime != rule.operating_regime.regime_id
    )
    if mismatch:
        return _abstained_outcome(authorization, window, window_hash, execution_id, runtime_version, "regime_mismatch", "regime_check", False)
    if window.source_variable != rule.source_variables[0] or window.target_variable != rule.target_variables[0]:
        return _abstained_outcome(authorization, window, window_hash, execution_id, runtime_version, "input_variable_mismatch", "trigger_check", False)
    if any(value is None for value in window.target_values):
        return _abstained_outcome(authorization, window, window_hash, execution_id, runtime_version, "missing_input", "relation_check", False)
    if rule.abstention_policy.abstain_on_parameter_uncertainty and any(
        item.uncertainty.status != "bounded" for item in authorization.artifacts.parameters
    ):
        return _abstained_outcome(authorization, window, window_hash, execution_id, runtime_version, "parameter_uncertainty", "tolerance_check", False)

    state = rule.trigger.state_value
    transitions = [index for index in range(1, len(window.source_values)) if window.source_values[index - 1] != state and window.source_values[index] == state]
    if window.source_values[0] == state:
        return _abstained_outcome(authorization, window, window_hash, execution_id, runtime_version, "missing_pre_trigger_baseline", "trigger_check", True, trigger_index=0)
    if len(transitions) > 1:
        return _abstained_outcome(authorization, window, window_hash, execution_id, runtime_version, "multiple_triggers", "trigger_check", True)
    if not transitions:
        return _evaluated_outcome(authorization, window, window_hash, execution_id, runtime_version, None, None)

    trigger_index = transitions[0]
    baseline = window.target_values[trigger_index - 1]
    if baseline is None:
        return _abstained_outcome(authorization, window, window_hash, execution_id, runtime_version, "missing_pre_trigger_baseline", "relation_check", True, trigger_index=trigger_index)
    sampling_seconds = _time_to_seconds(window.sampling_interval.value, window.sampling_interval.unit)
    lag_min_seconds = _time_to_seconds(rule.lag.minimum, rule.lag.unit)
    lag_max_seconds = _time_to_seconds(rule.lag.maximum, rule.lag.unit)
    window_seconds = _time_to_seconds(rule.window.length, rule.window.unit)
    duration = parameters[rule.window.parameter_ref]
    persistence_seconds = _time_to_seconds(duration.value, duration.unit)
    required_seconds = max(lag_max_seconds, window_seconds, persistence_seconds)
    available_seconds = (len(window.source_values) - 1 - trigger_index) * sampling_seconds
    if available_seconds < required_seconds:
        return _abstained_outcome(authorization, window, window_hash, execution_id, runtime_version, "insufficient_post_trigger_coverage", "window_check", True, trigger_index=trigger_index)

    tolerance = float(parameters[rule.tolerance_ref].value)
    response_index = None
    for index in range(trigger_index, len(window.target_values)):
        elapsed = (index - trigger_index) * sampling_seconds
        if lag_min_seconds <= elapsed <= lag_max_seconds and float(window.target_values[index]) - float(baseline) >= tolerance:
            response_index = index
            break
    return _evaluated_outcome(authorization, window, window_hash, execution_id, runtime_version, trigger_index, response_index)


def _evaluated_outcome(
    authorization: RuntimeAuthorizationBundleV1,
    window: DelayedResponseRuntimeWindowV1,
    window_hash: str,
    execution_id: str,
    runtime_version: str,
    trigger_index: int | None,
    response_index: int | None,
) -> RuntimeExecutionOutcomeV1:
    trigger = trigger_index is not None
    response = response_index is not None if trigger else None
    violation = trigger and not bool(response)
    results = {operator: "satisfied" for operator in _TRACE_OPERATORS}
    if not trigger:
        results["trigger_check"] = "violated"
        for operator in ("lag_check", "window_check", "relation_check", "tolerance_check", "persistence_check"):
            results[operator] = "not_applicable"
    elif response:
        results["relation_check"] = "satisfied"
        results["tolerance_check"] = "satisfied"
    else:
        results["relation_check"] = "violated"
        results["tolerance_check"] = "violated"
        results["output"] = "violated"
    trace = _make_trace(
        authorization, window, execution_id, "evaluated", trigger, response,
        violation, 1.0 if violation else 0.0, False, results,
    )
    return RuntimeExecutionOutcomeV1(
        authorization.receipt.authorization_id, window_hash, trace, trigger_index,
        response_index, None, runtime_version,
    )


def _abstained_outcome(
    authorization: RuntimeAuthorizationBundleV1,
    window: DelayedResponseRuntimeWindowV1,
    window_hash: str,
    execution_id: str,
    runtime_version: str,
    reason: str,
    blocking_operator: str,
    trigger_satisfied: bool,
    *,
    trigger_index: int | None = None,
) -> RuntimeExecutionOutcomeV1:
    if reason not in _ABSTENTION_REASONS:
        raise RuntimeV1Error("RUNTIME_ABSTENTION_REASON", "abstention reason is not registered")
    results = {operator: "not_applicable" for operator in _TRACE_OPERATORS}
    results[blocking_operator] = "abstained"
    results["abstention_check"] = "abstained"
    results["output"] = "not_applicable"
    if blocking_operator != "regime_check":
        results["regime_check"] = "satisfied"
    trace = _make_trace(
        authorization, window, execution_id, "abstained", trigger_satisfied,
        None, False, 0.0, True, results,
    )
    return RuntimeExecutionOutcomeV1(
        authorization.receipt.authorization_id, window_hash, trace, trigger_index,
        None, reason, runtime_version,
    )


def _make_trace(
    authorization: RuntimeAuthorizationBundleV1,
    window: DelayedResponseRuntimeWindowV1,
    execution_id: str,
    status: str,
    trigger_satisfied: bool,
    expected_effect_satisfied: bool | None,
    violation_detected: bool,
    violation_score: float,
    abstained: bool,
    results: Mapping[str, str],
) -> RuntimeTraceV1:
    rule = authorization.accepted_rule
    params = authorization.artifacts.parameter_by_id
    step_refs = {
        "regime_check": ((), rule.source_variables + rule.target_variables),
        "trigger_check": ((), rule.source_variables),
        "lag_check": ((rule.lag.parameter_ref,), rule.source_variables + rule.target_variables),
        "window_check": ((rule.window.parameter_ref,), rule.source_variables + rule.target_variables),
        "relation_check": ((rule.lag.parameter_ref, rule.tolerance_ref), rule.source_variables + rule.target_variables),
        "tolerance_check": ((rule.tolerance_ref,), rule.target_variables),
        "persistence_check": ((rule.persistence.duration_parameter_ref,) if rule.persistence.duration_parameter_ref else (), rule.source_variables + rule.target_variables),
        "abstention_check": ((), rule.source_variables + rule.target_variables),
        "output": ((), rule.source_variables + rule.target_variables),
    }
    document = {
        "schema_version": "1.0.0",
        "execution_id": execution_id,
        "artifact_hash": "0" * 64,
        "rule_id": rule.rule_id,
        "rule_hash": rule.verified_rule_hash,
        "verifier_result_ref": authorization.verifier_result.verifier_result_id,
        "input_window_id": window.input_window_id,
        "status": status,
        "trigger_satisfied": trigger_satisfied,
        "expected_effect_satisfied": expected_effect_satisfied,
        "violation_detected": violation_detected,
        "violation_score": violation_score,
        "abstained": abstained,
        "satisfaction_trace": [
            {"step": index, "operator": operator, "result": results[operator],
             "parameter_refs": list(step_refs[operator][0]), "variable_refs": list(step_refs[operator][1])}
            for index, operator in enumerate(_TRACE_OPERATORS, start=1)
        ],
        "parameter_values_used": [
            {"parameter_id": parameter_id, "parameter_hash": params[parameter_id].artifact_hash,
             "value": params[parameter_id].value, "unit": params[parameter_id].unit}
            for parameter_id in sorted(rule.parameter_refs)
        ],
        "input_output_alignment_preserved": True,
        "created_at": window.created_at,
    }
    return parse_runtime_trace(with_computed_artifact_hash(document))


def _typed_runtime_trace(item: Mapping[str, Any]) -> RuntimeTraceV1:
    return RuntimeTraceV1(
        schema_version=str(item["schema_version"]), execution_id=str(item["execution_id"]),
        artifact_hash=str(item["artifact_hash"]), rule_id=str(item["rule_id"]),
        rule_hash=str(item["rule_hash"]), verifier_result_ref=str(item["verifier_result_ref"]),
        input_window_id=str(item["input_window_id"]), status=str(item["status"]),
        trigger_satisfied=bool(item["trigger_satisfied"]), expected_effect_satisfied=item["expected_effect_satisfied"],
        violation_detected=bool(item["violation_detected"]), violation_score=item["violation_score"],
        abstained=bool(item["abstained"]),
        satisfaction_trace=tuple(RuntimeTraceStepV1(
            int(step["step"]), str(step["operator"]), str(step["result"]),
            tuple(step["parameter_refs"]), tuple(step["variable_refs"]),
        ) for step in item["satisfaction_trace"]),
        parameter_values_used=tuple(RuntimeParameterValueV1(
            str(value["parameter_id"]), str(value["parameter_hash"]), value["value"], str(value["unit"]),
        ) for value in item["parameter_values_used"]),
        input_output_alignment_preserved=bool(item["input_output_alignment_preserved"]),
        created_at=str(item["created_at"]),
    )


def _validate_runtime_window(window: DelayedResponseRuntimeWindowV1) -> None:
    if re.fullmatch(r"WIN-[A-Z0-9-]{3,64}", window.input_window_id) is None:
        _window_fail("RUNTIME_WINDOW_ID", "/input_window_id", "window ID is invalid")
    if any(not value for value in (window.dataset_version, window.subsystem, window.operating_regime)):
        _window_fail("RUNTIME_WINDOW_CONTEXT", "/dataset_version", "window context fields are required")
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", window.source_variable) is None or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", window.target_variable) is None:
        _window_fail("RUNTIME_WINDOW_VARIABLE", "/source_variable", "variable names are invalid")
    if len(window.source_values) != len(window.target_values) or len(window.source_values) < 2:
        _window_fail("RUNTIME_WINDOW_LENGTH", "/source_values", "arrays must have equal length of at least two")
    if window.sampling_interval.value <= 0 or window.sampling_interval.unit not in _TIME_FACTORS:
        _window_fail("RUNTIME_WINDOW_SAMPLING", "/sampling_interval", "sampling interval must be positive and time-based")
    if window.offset_unit not in {"samples", "milliseconds", "seconds"}:
        _window_fail("RUNTIME_WINDOW_OFFSET_UNIT", "/offset_unit", "offset unit is unsupported")
    if window.offset_unit == "samples" and window.end_offset - window.start_offset + 1 != len(window.source_values):
        _window_fail("RUNTIME_WINDOW_OFFSET_LENGTH", "/end_offset", "sample offsets do not match array length")
    if any(not (isinstance(value, (bool, int)) and value in {0, 1, False, True}) for value in window.source_values):
        _window_fail("RUNTIME_WINDOW_SOURCE_BINARY", "/source_values", "source values must be binary")
    for value in window.target_values:
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))):
            _window_fail("RUNTIME_WINDOW_TARGET_FINITE", "/target_values", "target values must be finite numbers or null")
    try:
        parsed = datetime.fromisoformat(window.created_at.replace("Z", "+00:00"))
        if parsed.utcoffset() is None:
            raise ValueError("timezone is required")
    except ValueError:
        _window_fail("RUNTIME_WINDOW_CREATED_AT", "/created_at", "created_at must be RFC3339-compatible")


def _validate_authorization_for_execution(bundle: RuntimeAuthorizationBundleV1) -> None:
    try:
        verify_runtime_authorization_bundle(bundle)
    except RuntimeAuthorizationError as exc:
        raise RuntimeV1Error(exc.issue_code, exc.message) from exc


def _execution_id(authorization_hash: str, window_hash: str, runtime_version: str, created_at: str) -> str:
    binding = {"authorization_hash": authorization_hash, "input_window_hash": window_hash,
               "runtime_version": runtime_version, "created_at": created_at}
    payload = json.dumps(binding, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return f"EXEC-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20].upper()}"


def _time_to_seconds(value: int | float, unit: str) -> float:
    try:
        return float(value) * _TIME_FACTORS[unit]
    except KeyError as exc:
        raise RuntimeV1Error("RUNTIME_TIME_UNIT", "unsupported time unit") from exc


def _window_fail(code: str, path: str, message: str) -> None:
    raise RuntimeWindowModelError(code, path, message)
