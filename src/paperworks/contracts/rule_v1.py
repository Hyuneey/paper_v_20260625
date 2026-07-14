"""Immutable delayed-response rule documents with canonical serialization."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, TypeAlias, cast

from paperworks.contracts.schema_registry import SchemaRegistry, load_schema_registry


JsonScalar: TypeAlias = str | int | float | bool | None
Number: TypeAlias = int | float
RULE_V1_SCHEMA_VERSION = "1.0.0"
RULE_V1_ARTIFACT_TYPE = "rule_dsl"


class RuleV1ModelError(ValueError):
    """Deterministic, sanitized rule-document parsing failure."""

    def __init__(self, issue_code: str, field_path: str, message: str, structural_report_hash: str) -> None:
        super().__init__(f"{issue_code} at {field_path}: {message}")
        self.issue_code = issue_code
        self.field_path = field_path
        self.message = message
        self.structural_report_hash = structural_report_hash

    def to_dict(self) -> dict[str, str]:
        return {
            "issue_code": self.issue_code,
            "field_path": self.field_path,
            "message": self.message,
            "structural_report_hash": self.structural_report_hash,
        }


@dataclass(frozen=True)
class OperatingRegimeSpec:
    regime_id: str
    condition_refs: tuple[str, ...]


@dataclass(frozen=True)
class TriggerSpec:
    trigger_type: str
    variable: str
    state_value: JsonScalar
    threshold_parameter_ref: str | None
    range_parameter_ref: str | None
    duration_parameter_ref: str | None


@dataclass(frozen=True)
class ExpectedEffectSpec:
    effect_type: str
    direction: str
    target_variables: tuple[str, ...]
    parameter_refs: tuple[str, ...]


@dataclass(frozen=True)
class LagSpec:
    lag_type: str
    minimum: Number
    maximum: Number
    unit: str
    parameter_ref: str


@dataclass(frozen=True)
class WindowSpec:
    window_type: str
    length: Number
    unit: str
    alignment: str
    parameter_ref: str


@dataclass(frozen=True)
class PersistenceSpec:
    enabled: bool
    duration_parameter_ref: str | None


@dataclass(frozen=True)
class OutputSemanticsSpec:
    output_type: str
    violation_direction: str


@dataclass(frozen=True)
class SeverityPolicySpec:
    policy_id: str
    levels: tuple[str, ...]
    parameter_ref: str


@dataclass(frozen=True)
class AbstentionPolicySpec:
    policy_id: str
    abstain_on_missing_inputs: bool
    abstain_on_regime_mismatch: bool
    abstain_on_parameter_uncertainty: bool


@dataclass(frozen=True)
class ComplexitySpec:
    operator_count: int
    variable_count: int
    max_depth: int


@dataclass(frozen=True)
class RuleProvenanceSpec:
    created_by: str
    planner_version: str
    candidate_hash: str
    created_at: str


@dataclass(frozen=True)
class ReviewHistoryEntry:
    iteration: int
    verifier_result_ref: str
    changed_fields: tuple[str, ...]
    candidate_hash: str


@dataclass(frozen=True)
class DelayedResponseRuleV1:
    schema_version: str
    rule_id: str
    rule_version: str
    status: str
    subsystem: str
    dataset_version: str
    source_variables: tuple[str, ...]
    target_variables: tuple[str, ...]
    operating_regime: OperatingRegimeSpec
    trigger: TriggerSpec
    relation_type: str
    expected_effect: ExpectedEffectSpec
    lag: LagSpec
    window: WindowSpec
    persistence: PersistenceSpec
    parameter_refs: tuple[str, ...]
    tolerance_ref: str
    normal_reference_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    graph_edge_refs: tuple[str, ...]
    output_semantics: OutputSemanticsSpec
    severity_policy: SeverityPolicySpec
    abstention_policy: AbstentionPolicySpec
    complexity: ComplexitySpec
    provenance: RuleProvenanceSpec
    review_history: tuple[ReviewHistoryEntry, ...]
    verified_rule_hash: str | None

    @property
    def runtime_authorized(self) -> bool:
        """Parsing never grants runtime authority; this field is not serialized."""

        return False


def parse_delayed_response_rule(
    document: Mapping[str, object],
    *,
    registry: SchemaRegistry | None = None,
) -> DelayedResponseRuleV1:
    """Structurally validate, then parse one bounded delayed-response document."""

    snapshot = copy.deepcopy(dict(document))
    active_registry = registry or load_schema_registry()
    structural_report = active_registry.validate_artifact(RULE_V1_ARTIFACT_TYPE, snapshot)
    report_hash = _structural_report_hash(structural_report.to_dict())
    if structural_report.status != "valid":
        first_issue = structural_report.issues[0] if structural_report.issues else None
        field_path = first_issue.instance_path if first_issue is not None else "/"
        reason = first_issue.issue_code if first_issue is not None else "REGISTRY_ERROR"
        raise RuleV1ModelError(
            "RULE_V1_STRUCTURAL_INVALID",
            field_path,
            f"rule document failed structural validation ({reason})",
            report_hash,
        )

    rule = _typed_rule(snapshot)
    _validate_mvp(rule, report_hash)
    return rule


def load_delayed_response_rule(
    path: str | Path,
    *,
    registry: SchemaRegistry | None = None,
) -> DelayedResponseRuleV1:
    """Load a UTF-8 JSON object and parse it without modifying the file."""

    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuleV1ModelError(
            "RULE_V1_STRUCTURAL_INVALID",
            "/",
            "rule document is not readable UTF-8 JSON",
            _unparsed_report_hash("unreadable_json"),
        ) from exc
    if not isinstance(document, dict):
        raise RuleV1ModelError(
            "RULE_V1_STRUCTURAL_INVALID",
            "/",
            "rule document must contain a JSON object",
            _unparsed_report_hash("non_object_json"),
        )
    return parse_delayed_response_rule(document, registry=registry)


def delayed_response_rule_to_dict(rule: DelayedResponseRuleV1) -> dict[str, Any]:
    """Return a new schema-only JSON dictionary."""

    return {
        "schema_version": rule.schema_version,
        "rule_id": rule.rule_id,
        "rule_version": rule.rule_version,
        "status": rule.status,
        "subsystem": rule.subsystem,
        "dataset_version": rule.dataset_version,
        "source_variables": list(rule.source_variables),
        "target_variables": list(rule.target_variables),
        "operating_regime": {
            "regime_id": rule.operating_regime.regime_id,
            "condition_refs": list(rule.operating_regime.condition_refs),
        },
        "trigger": {
            "trigger_type": rule.trigger.trigger_type,
            "variable": rule.trigger.variable,
            "state_value": rule.trigger.state_value,
            "threshold_parameter_ref": rule.trigger.threshold_parameter_ref,
            "range_parameter_ref": rule.trigger.range_parameter_ref,
            "duration_parameter_ref": rule.trigger.duration_parameter_ref,
        },
        "relation_type": rule.relation_type,
        "expected_effect": {
            "effect_type": rule.expected_effect.effect_type,
            "direction": rule.expected_effect.direction,
            "target_variables": list(rule.expected_effect.target_variables),
            "parameter_refs": list(rule.expected_effect.parameter_refs),
        },
        "lag": {
            "lag_type": rule.lag.lag_type,
            "minimum": rule.lag.minimum,
            "maximum": rule.lag.maximum,
            "unit": rule.lag.unit,
            "parameter_ref": rule.lag.parameter_ref,
        },
        "window": {
            "window_type": rule.window.window_type,
            "length": rule.window.length,
            "unit": rule.window.unit,
            "alignment": rule.window.alignment,
            "parameter_ref": rule.window.parameter_ref,
        },
        "persistence": {
            "enabled": rule.persistence.enabled,
            "duration_parameter_ref": rule.persistence.duration_parameter_ref,
        },
        "parameter_refs": list(rule.parameter_refs),
        "tolerance_ref": rule.tolerance_ref,
        "normal_reference_refs": list(rule.normal_reference_refs),
        "evidence_refs": list(rule.evidence_refs),
        "graph_edge_refs": list(rule.graph_edge_refs),
        "output_semantics": {
            "output_type": rule.output_semantics.output_type,
            "violation_direction": rule.output_semantics.violation_direction,
        },
        "severity_policy": {
            "policy_id": rule.severity_policy.policy_id,
            "levels": list(rule.severity_policy.levels),
            "parameter_ref": rule.severity_policy.parameter_ref,
        },
        "abstention_policy": {
            "policy_id": rule.abstention_policy.policy_id,
            "abstain_on_missing_inputs": rule.abstention_policy.abstain_on_missing_inputs,
            "abstain_on_regime_mismatch": rule.abstention_policy.abstain_on_regime_mismatch,
            "abstain_on_parameter_uncertainty": rule.abstention_policy.abstain_on_parameter_uncertainty,
        },
        "complexity": {
            "operator_count": rule.complexity.operator_count,
            "variable_count": rule.complexity.variable_count,
            "max_depth": rule.complexity.max_depth,
        },
        "provenance": {
            "created_by": rule.provenance.created_by,
            "planner_version": rule.provenance.planner_version,
            "candidate_hash": rule.provenance.candidate_hash,
            "created_at": rule.provenance.created_at,
        },
        "review_history": [
            {
                "iteration": entry.iteration,
                "verifier_result_ref": entry.verifier_result_ref,
                "changed_fields": list(entry.changed_fields),
                "candidate_hash": entry.candidate_hash,
            }
            for entry in rule.review_history
        ],
        "verified_rule_hash": rule.verified_rule_hash,
    }


def serialize_delayed_response_rule(rule: DelayedResponseRuleV1) -> str:
    """Serialize with the frozen compact canonical JSON policy."""

    return canonical_rule_document_bytes(rule).decode("utf-8")


def canonical_rule_document_bytes(rule: DelayedResponseRuleV1) -> bytes:
    """Return canonical transport bytes; these bytes grant no rule authority."""

    text = json.dumps(
        delayed_response_rule_to_dict(rule),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return text.encode("utf-8")


def canonical_rule_document_sha256(rule: DelayedResponseRuleV1) -> str:
    """Hash canonical document bytes for transport, never for verifier approval."""

    return hashlib.sha256(canonical_rule_document_bytes(rule)).hexdigest()


def _typed_rule(document: Mapping[str, Any]) -> DelayedResponseRuleV1:
    regime = cast(Mapping[str, Any], document["operating_regime"])
    trigger = cast(Mapping[str, Any], document["trigger"])
    effect = cast(Mapping[str, Any], document["expected_effect"])
    lag = cast(Mapping[str, Any], document["lag"])
    window = cast(Mapping[str, Any], document["window"])
    persistence = cast(Mapping[str, Any], document["persistence"])
    output = cast(Mapping[str, Any], document["output_semantics"])
    severity = cast(Mapping[str, Any], document["severity_policy"])
    abstention = cast(Mapping[str, Any], document["abstention_policy"])
    complexity = cast(Mapping[str, Any], document["complexity"])
    provenance = cast(Mapping[str, Any], document["provenance"])
    history = cast(list[Mapping[str, Any]], document["review_history"])
    return DelayedResponseRuleV1(
        schema_version=cast(str, document["schema_version"]),
        rule_id=cast(str, document["rule_id"]),
        rule_version=cast(str, document["rule_version"]),
        status=cast(str, document["status"]),
        subsystem=cast(str, document["subsystem"]),
        dataset_version=cast(str, document["dataset_version"]),
        source_variables=tuple(cast(list[str], document["source_variables"])),
        target_variables=tuple(cast(list[str], document["target_variables"])),
        operating_regime=OperatingRegimeSpec(
            regime_id=cast(str, regime["regime_id"]),
            condition_refs=tuple(cast(list[str], regime["condition_refs"])),
        ),
        trigger=TriggerSpec(
            trigger_type=cast(str, trigger["trigger_type"]),
            variable=cast(str, trigger["variable"]),
            state_value=cast(JsonScalar, trigger["state_value"]),
            threshold_parameter_ref=cast(str | None, trigger["threshold_parameter_ref"]),
            range_parameter_ref=cast(str | None, trigger["range_parameter_ref"]),
            duration_parameter_ref=cast(str | None, trigger["duration_parameter_ref"]),
        ),
        relation_type=cast(str, document["relation_type"]),
        expected_effect=ExpectedEffectSpec(
            effect_type=cast(str, effect["effect_type"]),
            direction=cast(str, effect["direction"]),
            target_variables=tuple(cast(list[str], effect["target_variables"])),
            parameter_refs=tuple(cast(list[str], effect["parameter_refs"])),
        ),
        lag=LagSpec(
            lag_type=cast(str, lag["lag_type"]),
            minimum=cast(Number, lag["minimum"]),
            maximum=cast(Number, lag["maximum"]),
            unit=cast(str, lag["unit"]),
            parameter_ref=cast(str, lag["parameter_ref"]),
        ),
        window=WindowSpec(
            window_type=cast(str, window["window_type"]),
            length=cast(Number, window["length"]),
            unit=cast(str, window["unit"]),
            alignment=cast(str, window["alignment"]),
            parameter_ref=cast(str, window["parameter_ref"]),
        ),
        persistence=PersistenceSpec(
            enabled=cast(bool, persistence["enabled"]),
            duration_parameter_ref=cast(str | None, persistence["duration_parameter_ref"]),
        ),
        parameter_refs=tuple(cast(list[str], document["parameter_refs"])),
        tolerance_ref=cast(str, document["tolerance_ref"]),
        normal_reference_refs=tuple(cast(list[str], document["normal_reference_refs"])),
        evidence_refs=tuple(cast(list[str], document["evidence_refs"])),
        graph_edge_refs=tuple(cast(list[str], document["graph_edge_refs"])),
        output_semantics=OutputSemanticsSpec(
            output_type=cast(str, output["output_type"]),
            violation_direction=cast(str, output["violation_direction"]),
        ),
        severity_policy=SeverityPolicySpec(
            policy_id=cast(str, severity["policy_id"]),
            levels=tuple(cast(list[str], severity["levels"])),
            parameter_ref=cast(str, severity["parameter_ref"]),
        ),
        abstention_policy=AbstentionPolicySpec(
            policy_id=cast(str, abstention["policy_id"]),
            abstain_on_missing_inputs=cast(bool, abstention["abstain_on_missing_inputs"]),
            abstain_on_regime_mismatch=cast(bool, abstention["abstain_on_regime_mismatch"]),
            abstain_on_parameter_uncertainty=cast(bool, abstention["abstain_on_parameter_uncertainty"]),
        ),
        complexity=ComplexitySpec(
            operator_count=cast(int, complexity["operator_count"]),
            variable_count=cast(int, complexity["variable_count"]),
            max_depth=cast(int, complexity["max_depth"]),
        ),
        provenance=RuleProvenanceSpec(
            created_by=cast(str, provenance["created_by"]),
            planner_version=cast(str, provenance["planner_version"]),
            candidate_hash=cast(str, provenance["candidate_hash"]),
            created_at=cast(str, provenance["created_at"]),
        ),
        review_history=tuple(
            ReviewHistoryEntry(
                iteration=cast(int, item["iteration"]),
                verifier_result_ref=cast(str, item["verifier_result_ref"]),
                changed_fields=tuple(cast(list[str], item["changed_fields"])),
                candidate_hash=cast(str, item["candidate_hash"]),
            )
            for item in history
        ),
        verified_rule_hash=cast(str | None, document["verified_rule_hash"]),
    )


def _validate_mvp(rule: DelayedResponseRuleV1, report_hash: str) -> None:
    if rule.relation_type != "delayed_response":
        _fail("RULE_V1_UNSUPPORTED_RELATION", "/relation_type", "only delayed_response is supported", report_hash)
    if len(rule.source_variables) != 1:
        _fail("RULE_V1_SOURCE_CARDINALITY", "/source_variables", "exactly one source is required", report_hash)
    if len(rule.target_variables) != 1:
        _fail("RULE_V1_TARGET_CARDINALITY", "/target_variables", "exactly one target is required", report_hash)
    if rule.source_variables[0] == rule.target_variables[0]:
        _fail("RULE_V1_SELF_RELATION", "/target_variables/0", "source and target must differ", report_hash)
    if rule.trigger.trigger_type != "state_changes_to":
        _fail("RULE_V1_TRIGGER_TYPE", "/trigger/trigger_type", "unsupported trigger type", report_hash)
    if rule.trigger.variable != rule.source_variables[0]:
        _fail("RULE_V1_TRIGGER_SOURCE_MISMATCH", "/trigger/variable", "trigger must use the source variable", report_hash)
    if rule.trigger.state_value is None:
        _fail("RULE_V1_TRIGGER_STATE_MISSING", "/trigger/state_value", "state value is required", report_hash)
    if any(
        item is not None
        for item in (
            rule.trigger.threshold_parameter_ref,
            rule.trigger.range_parameter_ref,
            rule.trigger.duration_parameter_ref,
        )
    ):
        _fail(
            "RULE_V1_TRIGGER_PARAMETER_REFERENCE",
            "/trigger",
            "state_changes_to does not use trigger parameter references in this MVP",
            report_hash,
        )
    if rule.expected_effect.effect_type != "delayed_change":
        _fail("RULE_V1_EFFECT_TYPE", "/expected_effect/effect_type", "unsupported expected effect", report_hash)
    if rule.expected_effect.direction != "increase":
        _fail("RULE_V1_EFFECT_DIRECTION", "/expected_effect/direction", "effect direction must be increase", report_hash)
    if rule.expected_effect.target_variables != rule.target_variables:
        _fail(
            "RULE_V1_EFFECT_TARGET_MISMATCH",
            "/expected_effect/target_variables",
            "effect targets must equal rule targets",
            report_hash,
        )
    if rule.output_semantics.output_type != "binary_anomaly":
        _fail("RULE_V1_OUTPUT_TYPE", "/output_semantics/output_type", "output must be binary_anomaly", report_hash)
    if rule.output_semantics.violation_direction != "missing_expected_response":
        _fail(
            "RULE_V1_VIOLATION_DIRECTION",
            "/output_semantics/violation_direction",
            "violation must be missing_expected_response",
            report_hash,
        )
    if rule.lag.lag_type not in {"fixed", "interval"}:
        _fail("RULE_V1_LAG_TYPE", "/lag/lag_type", "unsupported lag type", report_hash)
    if rule.lag.minimum > rule.lag.maximum:
        _fail("RULE_V1_LAG_ORDER", "/lag", "lag minimum must not exceed maximum", report_hash)
    if rule.lag.lag_type == "fixed" and rule.lag.minimum != rule.lag.maximum:
        _fail("RULE_V1_FIXED_LAG_MISMATCH", "/lag", "fixed lag bounds must be equal", report_hash)
    if rule.lag.lag_type == "interval" and rule.lag.minimum == rule.lag.maximum:
        _fail("RULE_V1_INTERVAL_LAG_EMPTY", "/lag", "interval lag bounds must differ", report_hash)
    if rule.window.window_type not in {"event_relative", "persistence"}:
        _fail("RULE_V1_WINDOW_TYPE", "/window/window_type", "unsupported window type", report_hash)
    if rule.persistence.enabled != (rule.persistence.duration_parameter_ref is not None):
        _fail(
            "RULE_V1_PERSISTENCE_REFERENCE",
            "/persistence/duration_parameter_ref",
            "persistence enabled state and duration reference disagree",
            report_hash,
        )
    missing_refs = _collected_parameter_refs(rule) - set(rule.parameter_refs)
    if missing_refs:
        _fail(
            "RULE_V1_PARAMETER_REFERENCE_MISSING",
            "/parameter_refs",
            "top-level parameter_refs omits a nested reference",
            report_hash,
        )


def _collected_parameter_refs(rule: DelayedResponseRuleV1) -> set[str]:
    refs = set(rule.expected_effect.parameter_refs)
    refs.update((rule.lag.parameter_ref, rule.window.parameter_ref, rule.tolerance_ref, rule.severity_policy.parameter_ref))
    for item in (
        rule.trigger.threshold_parameter_ref,
        rule.trigger.range_parameter_ref,
        rule.trigger.duration_parameter_ref,
        rule.persistence.duration_parameter_ref,
    ):
        if item is not None:
            refs.add(item)
    return refs


def _fail(code: str, path: str, message: str, report_hash: str) -> None:
    raise RuleV1ModelError(code, path, message, report_hash)


def _structural_report_hash(report: Mapping[str, Any]) -> str:
    payload = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _unparsed_report_hash(reason: str) -> str:
    return _structural_report_hash({"status": "invalid", "reason": reason})
