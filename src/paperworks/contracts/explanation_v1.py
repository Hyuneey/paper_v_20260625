"""Deterministic trace-grounded explanation records for TASK-032E."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from paperworks.contracts.artifact_hashing import (
    ContractArtifactHashError,
    canonical_contract_artifact_sha256,
    verify_contract_artifact_hash,
    with_computed_artifact_hash,
)
from paperworks.contracts.runtime_authority import (
    RuntimeAuthorizationBundleV1,
    RuntimeAuthorizationError,
    verify_runtime_authorization_bundle,
)
from paperworks.contracts.runtime_v1 import (
    DelayedResponseRuntimeWindowV1,
    RuntimeExecutionOutcomeV1,
    RuntimeTraceV1,
    RuntimeV1Error,
    canonical_runtime_window_sha256,
    parse_runtime_trace,
    runtime_trace_to_dict,
)
from paperworks.contracts.schema_registry import SchemaRegistry, load_schema_registry


RENDERER_VERSION = "task032e-renderer-1.0.0"


class ExplanationV1Error(ValueError):
    def __init__(self, issue_code: str, message: str) -> None:
        super().__init__(f"{issue_code}: {message}")
        self.issue_code = issue_code
        self.message = message


@dataclass(frozen=True)
class ExplanationTimeIntervalV1:
    input_window_id: str
    start_offset: int
    end_offset: int
    unit: str


@dataclass(frozen=True)
class ExplanationLagV1:
    observed: int | float | None
    expected_minimum: int | float
    expected_maximum: int | float
    unit: str


@dataclass(frozen=True)
class ExplanationResultV1:
    available: bool
    binary_label: int | None
    score: int | float | None
    artifact_ref: str | None
    abstained: bool


@dataclass(frozen=True)
class ExplanationRecordV1:
    schema_version: str
    explanation_id: str
    artifact_hash: str
    execution_id: str
    rule_id: str
    rule_hash: str
    subsystem: str
    time_interval: ExplanationTimeIntervalV1
    source_variables: tuple[str, ...]
    target_variables: tuple[str, ...]
    relation_type: str
    expected_behavior: str
    observed_behavior: str
    violation_type: str
    lag: ExplanationLagV1
    parameter_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    normal_reference_refs: tuple[str, ...]
    graph_edge_refs: tuple[str, ...]
    verifier_result_ref: str
    detector_result: ExplanationResultV1
    rule_result: ExplanationResultV1
    fusion_result: ExplanationResultV1
    natural_language_text: str | None
    renderer_version: str
    causal_claim_made: bool
    root_cause_claim_made: bool


def parse_explanation_record(
    document: Mapping[str, object], *, registry: SchemaRegistry | None = None
) -> ExplanationRecordV1:
    snapshot = copy.deepcopy(dict(document))
    report = (registry or load_schema_registry()).validate_artifact("explanation_record", snapshot)
    if report.status != "valid":
        issue = report.issues[0] if report.issues else None
        raise ExplanationV1Error("EXPLANATION_STRUCTURAL_INVALID", issue.issue_code if issue else "registry error")
    try:
        verify_contract_artifact_hash(snapshot)
    except ContractArtifactHashError as exc:
        raise ExplanationV1Error(exc.issue_code, exc.message) from exc
    record = _typed_explanation(snapshot)
    if record.lag.observed is not None:
        raise ExplanationV1Error("EXPLANATION_OBSERVED_LAG_PROHIBITED", "TASK-032E cannot ground observed numeric lag")
    if record.causal_claim_made or record.root_cause_claim_made:
        raise ExplanationV1Error("EXPLANATION_CLAIM_PROHIBITED", "causal and root-cause claims are prohibited")
    if record.detector_result != ExplanationResultV1(False, None, None, None, False):
        raise ExplanationV1Error("EXPLANATION_DETECTOR_PROHIBITED", "detector result is unavailable in TASK-032E")
    if record.fusion_result != ExplanationResultV1(False, None, None, None, False):
        raise ExplanationV1Error("EXPLANATION_FUSION_PROHIBITED", "fusion result is unavailable in TASK-032E")
    if record.rule_result.abstained and (record.rule_result.binary_label is not None or record.rule_result.score is not None):
        raise ExplanationV1Error("EXPLANATION_RULE_RESULT_INVALID", "abstention cannot contain a rule label or score")
    if not record.rule_result.available or record.rule_result.artifact_ref != record.execution_id:
        raise ExplanationV1Error("EXPLANATION_RULE_RESULT_INVALID", "rule result must bind the execution")
    if not record.rule_result.abstained and (record.rule_result.binary_label is None or record.rule_result.score is None):
        raise ExplanationV1Error("EXPLANATION_RULE_RESULT_INVALID", "evaluated rule result requires label and score")
    return record


def explanation_record_to_dict(record: ExplanationRecordV1) -> dict[str, Any]:
    return {
        "schema_version": record.schema_version,
        "explanation_id": record.explanation_id,
        "artifact_hash": record.artifact_hash,
        "execution_id": record.execution_id,
        "rule_id": record.rule_id,
        "rule_hash": record.rule_hash,
        "subsystem": record.subsystem,
        "time_interval": {
            "input_window_id": record.time_interval.input_window_id,
            "start_offset": record.time_interval.start_offset,
            "end_offset": record.time_interval.end_offset,
            "unit": record.time_interval.unit,
        },
        "source_variables": list(record.source_variables),
        "target_variables": list(record.target_variables),
        "relation_type": record.relation_type,
        "expected_behavior": record.expected_behavior,
        "observed_behavior": record.observed_behavior,
        "violation_type": record.violation_type,
        "lag": {
            "observed": record.lag.observed,
            "expected_minimum": record.lag.expected_minimum,
            "expected_maximum": record.lag.expected_maximum,
            "unit": record.lag.unit,
        },
        "parameter_refs": list(record.parameter_refs),
        "evidence_refs": list(record.evidence_refs),
        "normal_reference_refs": list(record.normal_reference_refs),
        "graph_edge_refs": list(record.graph_edge_refs),
        "verifier_result_ref": record.verifier_result_ref,
        "detector_result": _result_to_dict(record.detector_result),
        "rule_result": _result_to_dict(record.rule_result),
        "fusion_result": _result_to_dict(record.fusion_result),
        "natural_language_text": record.natural_language_text,
        "renderer_version": record.renderer_version,
        "causal_claim_made": record.causal_claim_made,
        "root_cause_claim_made": record.root_cause_claim_made,
    }


def serialize_explanation_record(record: ExplanationRecordV1) -> str:
    return json.dumps(explanation_record_to_dict(record), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def canonical_explanation_record_sha256(record: ExplanationRecordV1) -> str:
    return canonical_contract_artifact_sha256(explanation_record_to_dict(record))


def render_delayed_response_explanation(
    authorization: RuntimeAuthorizationBundleV1,
    execution: RuntimeExecutionOutcomeV1,
    window: DelayedResponseRuntimeWindowV1,
    *,
    renderer_version: str = RENDERER_VERSION,
) -> ExplanationRecordV1:
    if not isinstance(authorization, RuntimeAuthorizationBundleV1) or not authorization.runtime_authorized:
        raise ExplanationV1Error("EXPLANATION_RUNTIME_NOT_AUTHORIZED", "authorized runtime bundle is required")
    try:
        verify_runtime_authorization_bundle(authorization)
    except RuntimeAuthorizationError as exc:
        raise ExplanationV1Error(
            "EXPLANATION_AUTHORIZATION_INVALID",
            "runtime authorization failed binding revalidation",
        ) from exc
    if execution.authorization_id != authorization.receipt.authorization_id:
        raise ExplanationV1Error(
            "EXPLANATION_AUTHORIZATION_ID_MISMATCH",
            "execution authorization ID differs from the bound receipt",
        )
    try:
        trace = parse_runtime_trace(runtime_trace_to_dict(execution.trace))
    except RuntimeV1Error as exc:
        raise ExplanationV1Error("EXPLANATION_TRACE_INVALID", "runtime trace failed structural or hash validation") from exc
    rule = authorization.accepted_rule
    result = authorization.verifier_result
    if not (
        trace.rule_id == rule.rule_id
        and trace.rule_hash == rule.verified_rule_hash
        and trace.verifier_result_ref == result.verifier_result_id
        and trace.input_window_id == window.input_window_id
        and execution.input_window_hash == canonical_runtime_window_sha256(window)
    ):
        raise ExplanationV1Error("EXPLANATION_TRACE_BINDING_MISMATCH", "trace does not bind the rule, verifier, or window")
    if tuple(sorted(rule.graph_edge_refs)) != tuple(sorted(result.verified_graph_edges)):
        raise ExplanationV1Error("EXPLANATION_GRAPH_BINDING_MISMATCH", "graph references differ")
    if tuple(sorted(rule.evidence_refs)) != tuple(sorted(result.verified_evidence)):
        raise ExplanationV1Error("EXPLANATION_EVIDENCE_BINDING_MISMATCH", "evidence references differ")
    if tuple(sorted(rule.normal_reference_refs)) != tuple(sorted(result.verified_normal_references)):
        raise ExplanationV1Error("EXPLANATION_NORMAL_BINDING_MISMATCH", "normal references differ")
    trace_parameters = tuple(sorted((item.parameter_id, item.parameter_hash) for item in trace.parameter_values_used))
    if trace_parameters != authorization.receipt.parameter_hashes:
        raise ExplanationV1Error("EXPLANATION_PARAMETER_BINDING_MISMATCH", "trace parameter hashes differ")

    expected = (
        f"After {rule.source_variables[0]} changes to {rule.trigger.state_value}, "
        f"{rule.target_variables[0]} is expected to increase by the approved tolerance "
        "within the approved lag interval."
    )
    if trace.abstained:
        observed = "The rule abstained because the runtime evidence was insufficient or incompatible."
    elif not trace.trigger_satisfied:
        observed = "The trigger condition was not observed."
    elif trace.expected_effect_satisfied:
        observed = "The expected delayed response was observed."
    else:
        observed = "The expected delayed response was not observed."
    unavailable = {"available": False, "binary_label": None, "score": None, "artifact_ref": None, "abstained": False}
    if trace.abstained:
        rule_result = {"available": True, "binary_label": None, "score": None, "artifact_ref": trace.execution_id, "abstained": True}
    else:
        rule_result = {"available": True, "binary_label": 1 if trace.violation_detected else 0,
                       "score": trace.violation_score, "artifact_ref": trace.execution_id, "abstained": False}
    id_binding = {
        "authorization_hash": authorization.receipt.authorization_hash,
        "runtime_trace_hash": trace.artifact_hash,
        "input_window_hash": execution.input_window_hash,
        "renderer_version": renderer_version,
    }
    payload = json.dumps(id_binding, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    explanation_id = f"EXPLAIN-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20].upper()}"
    document = {
        "schema_version": "1.0.0",
        "explanation_id": explanation_id,
        "artifact_hash": "0" * 64,
        "execution_id": trace.execution_id,
        "rule_id": rule.rule_id,
        "rule_hash": rule.verified_rule_hash,
        "subsystem": rule.subsystem,
        "time_interval": {"input_window_id": window.input_window_id, "start_offset": window.start_offset,
                          "end_offset": window.end_offset, "unit": window.offset_unit},
        "source_variables": list(rule.source_variables),
        "target_variables": list(rule.target_variables),
        "relation_type": rule.relation_type,
        "expected_behavior": expected,
        "observed_behavior": observed,
        "violation_type": rule.output_semantics.violation_direction,
        "lag": {"observed": None, "expected_minimum": rule.lag.minimum,
                "expected_maximum": rule.lag.maximum, "unit": rule.lag.unit},
        "parameter_refs": list(rule.parameter_refs),
        "evidence_refs": list(rule.evidence_refs),
        "normal_reference_refs": list(rule.normal_reference_refs),
        "graph_edge_refs": list(rule.graph_edge_refs),
        "verifier_result_ref": result.verifier_result_id,
        "detector_result": unavailable,
        "rule_result": rule_result,
        "fusion_result": unavailable,
        "natural_language_text": f"{expected} {observed}",
        "renderer_version": renderer_version,
        "causal_claim_made": False,
        "root_cause_claim_made": False,
    }
    return parse_explanation_record(with_computed_artifact_hash(document))


def _typed_explanation(item: Mapping[str, Any]) -> ExplanationRecordV1:
    interval, lag = item["time_interval"], item["lag"]
    return ExplanationRecordV1(
        schema_version=str(item["schema_version"]), explanation_id=str(item["explanation_id"]),
        artifact_hash=str(item["artifact_hash"]), execution_id=str(item["execution_id"]),
        rule_id=str(item["rule_id"]), rule_hash=str(item["rule_hash"]), subsystem=str(item["subsystem"]),
        time_interval=ExplanationTimeIntervalV1(str(interval["input_window_id"]), int(interval["start_offset"]), int(interval["end_offset"]), str(interval["unit"])),
        source_variables=tuple(item["source_variables"]), target_variables=tuple(item["target_variables"]),
        relation_type=str(item["relation_type"]), expected_behavior=str(item["expected_behavior"]),
        observed_behavior=str(item["observed_behavior"]), violation_type=str(item["violation_type"]),
        lag=ExplanationLagV1(lag["observed"], lag["expected_minimum"], lag["expected_maximum"], str(lag["unit"])),
        parameter_refs=tuple(item["parameter_refs"]), evidence_refs=tuple(item["evidence_refs"]),
        normal_reference_refs=tuple(item["normal_reference_refs"]), graph_edge_refs=tuple(item["graph_edge_refs"]),
        verifier_result_ref=str(item["verifier_result_ref"]), detector_result=_typed_result(item["detector_result"]),
        rule_result=_typed_result(item["rule_result"]), fusion_result=_typed_result(item["fusion_result"]),
        natural_language_text=item["natural_language_text"], renderer_version=str(item["renderer_version"]),
        causal_claim_made=bool(item["causal_claim_made"]), root_cause_claim_made=bool(item["root_cause_claim_made"]),
    )


def _typed_result(item: Mapping[str, Any]) -> ExplanationResultV1:
    return ExplanationResultV1(bool(item["available"]), item["binary_label"], item["score"], item["artifact_ref"], bool(item["abstained"]))


def _result_to_dict(result: ExplanationResultV1) -> dict[str, Any]:
    return {"available": result.available, "binary_label": result.binary_label, "score": result.score,
            "artifact_ref": result.artifact_ref, "abstained": result.abstained}
