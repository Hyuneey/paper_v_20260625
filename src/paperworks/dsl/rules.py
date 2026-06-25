"""Versioned AST, schema validation, and deterministic evaluation for rules."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol, Sequence

from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.metadata import MetadataRegistry, ValueType, VariableMetadata, VariableRole
from paperworks.profiling import CalibrationRecord


DSL_SCHEMA_VERSION = "1.0"
RELATION_TYPE = "binary_actuator_to_continuous_sensor"
RULE_FAMILY = "changed_to_increase_within_response_missing"

_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_PROHIBITED_PAYLOAD_PATTERNS = (
    "__",
    "exec",
    "eval",
    "compile",
    "import",
    "lambda",
    "open(",
    "os.",
    "subprocess",
    "system(",
    "powershell",
    "cmd.exe",
    "python -",
    "python.exe",
    "`",
    "$(",
    "|",
    ";",
)


class RuleDslError(ValueError):
    """Raised when a serialized rule cannot be parsed as the safe DSL."""


@dataclass(frozen=True)
class SchemaIssue:
    code: str
    message: str
    path: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CalibrationValueRef:
    parameter_name: str
    calibration_record_id: str
    field_name: str
    resolved_value: float
    unit: str

    def __post_init__(self) -> None:
        if not self.parameter_name:
            raise RuleDslError("parameter_name is required")
        if not _HASH_RE.match(self.calibration_record_id):
            raise RuleDslError("calibration_record_id must be a 64-character hex hash")
        if self.field_name != "value":
            raise RuleDslError("only CalibrationRecord.value references are supported")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CalibrationValueRef":
        _reject_unknown_keys(
            data,
            {"parameter_name", "calibration_record_id", "field_name", "resolved_value", "unit"},
            "calibration_reference",
        )
        return cls(
            parameter_name=str(data["parameter_name"]),
            calibration_record_id=str(data["calibration_record_id"]),
            field_name=str(data["field_name"]),
            resolved_value=float(data["resolved_value"]),
            unit=str(data["unit"]),
        )


@dataclass(frozen=True)
class ChangedToPredicate:
    variable: str
    from_state: float
    to_state: float
    predicate: str = "changed_to"

    def __post_init__(self) -> None:
        if self.predicate != "changed_to":
            raise RuleDslError("trigger predicate must be changed_to")
        _validate_identifier(self.variable, "trigger.variable")

    def to_dict(self) -> dict[str, Any]:
        return {
            "predicate": self.predicate,
            "variable": self.variable,
            "from_state": self.from_state,
            "to_state": self.to_state,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ChangedToPredicate":
        _reject_unknown_keys(data, {"predicate", "variable", "from_state", "to_state"}, "trigger_predicate")
        return cls(
            predicate=str(data["predicate"]),
            variable=str(data["variable"]),
            from_state=float(data["from_state"]),
            to_state=float(data["to_state"]),
        )


@dataclass(frozen=True)
class IncreaseWithinPredicate:
    variable: str
    min_magnitude: CalibrationValueRef
    max_delay_seconds: CalibrationValueRef
    predicate: str = "increase_within"

    def __post_init__(self) -> None:
        if self.predicate != "increase_within":
            raise RuleDslError("expected response predicate must be increase_within")
        _validate_identifier(self.variable, "expected_response.variable")

    def to_dict(self) -> dict[str, Any]:
        return {
            "predicate": self.predicate,
            "variable": self.variable,
            "min_magnitude": self.min_magnitude.to_dict(),
            "max_delay_seconds": self.max_delay_seconds.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "IncreaseWithinPredicate":
        _reject_unknown_keys(
            data,
            {"predicate", "variable", "min_magnitude", "max_delay_seconds"},
            "expected_response",
        )
        return cls(
            predicate=str(data["predicate"]),
            variable=str(data["variable"]),
            min_magnitude=CalibrationValueRef.from_dict(data["min_magnitude"]),
            max_delay_seconds=CalibrationValueRef.from_dict(data["max_delay_seconds"]),
        )


@dataclass(frozen=True)
class ResponseMissingPredicate:
    expected_response: IncreaseWithinPredicate
    predicate: str = "response_missing"

    def __post_init__(self) -> None:
        if self.predicate != "response_missing":
            raise RuleDslError("anomaly predicate must be response_missing")

    def to_dict(self) -> dict[str, Any]:
        return {
            "predicate": self.predicate,
            "expected_response": self.expected_response.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ResponseMissingPredicate":
        _reject_unknown_keys(data, {"predicate", "expected_response"}, "response_predicate")
        return cls(
            predicate=str(data["predicate"]),
            expected_response=IncreaseWithinPredicate.from_dict(data["expected_response"]),
        )


@dataclass(frozen=True)
class PlannerProvenance:
    planner_type: str
    planner_version: str
    source_artifact_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.planner_type not in {"deterministic_template", "llm_json_dsl"}:
            raise RuleDslError("unsupported planner_type")
        if not self.planner_version:
            raise RuleDslError("planner_version is required")
        for artifact_id in self.source_artifact_ids:
            if not _HASH_RE.match(artifact_id):
                raise RuleDslError("source_artifact_ids must be 64-character hex hashes")

    def to_dict(self) -> dict[str, Any]:
        return {
            "planner_type": self.planner_type,
            "planner_version": self.planner_version,
            "source_artifact_ids": list(self.source_artifact_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PlannerProvenance":
        _reject_unknown_keys(data, {"planner_type", "planner_version", "source_artifact_ids"}, "planner_provenance")
        return cls(
            planner_type=str(data["planner_type"]),
            planner_version=str(data["planner_version"]),
            source_artifact_ids=tuple(str(item) for item in data["source_artifact_ids"]),
        )


@dataclass(frozen=True)
class RuleAst:
    rule_id: str
    schema_version: str
    source: str
    target: str
    relation_type: str
    trigger_predicate: ChangedToPredicate
    response_predicate: ResponseMissingPredicate
    calibration_references: Mapping[str, CalibrationValueRef]
    candidate_pair_artifact_id: str
    metadata_artifact_id: str
    planner_provenance: PlannerProvenance
    description_template: str
    rule_family: str = RULE_FAMILY

    def __post_init__(self) -> None:
        if self.schema_version != DSL_SCHEMA_VERSION:
            raise RuleDslError(f"unsupported DSL schema_version: {self.schema_version}")
        _validate_identifier(self.source, "source")
        _validate_identifier(self.target, "target")
        if self.source == self.target:
            raise RuleDslError("source and target must differ")
        if self.relation_type != RELATION_TYPE:
            raise RuleDslError("unsupported relation_type")
        if self.rule_family != RULE_FAMILY:
            raise RuleDslError("unsupported rule_family")
        if not _HASH_RE.match(self.candidate_pair_artifact_id):
            raise RuleDslError("candidate_pair_artifact_id must be a 64-character hex hash")
        if not _HASH_RE.match(self.metadata_artifact_id):
            raise RuleDslError("metadata_artifact_id must be a 64-character hex hash")
        if set(self.calibration_references) != {"max_response_delay_seconds", "min_response_magnitude"}:
            raise RuleDslError("rule requires delay and magnitude calibration references")
        if self.trigger_predicate.variable != self.source:
            raise RuleDslError("trigger variable must equal rule source")
        if self.response_predicate.expected_response.variable != self.target:
            raise RuleDslError("response variable must equal rule target")
        if (
            self.response_predicate.expected_response.max_delay_seconds
            != self.calibration_references["max_response_delay_seconds"]
        ):
            raise RuleDslError("response delay reference must match calibration_references")
        if self.response_predicate.expected_response.min_magnitude != self.calibration_references["min_response_magnitude"]:
            raise RuleDslError("response magnitude reference must match calibration_references")
        _reject_prohibited_payload(self.description_template, "description_template")

    @property
    def deterministic_id(self) -> str:
        return stable_hash(self.to_dict(include_rule_id=False))

    def to_dict(self, *, include_rule_id: bool = True) -> dict[str, Any]:
        data = {
            "schema_version": self.schema_version,
            "rule_family": self.rule_family,
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "trigger_predicate": self.trigger_predicate.to_dict(),
            "response_predicate": self.response_predicate.to_dict(),
            "calibration_references": {
                key: self.calibration_references[key].to_dict() for key in sorted(self.calibration_references)
            },
            "candidate_pair_artifact_id": self.candidate_pair_artifact_id,
            "metadata_artifact_id": self.metadata_artifact_id,
            "planner_provenance": self.planner_provenance.to_dict(),
            "description_template": self.description_template,
        }
        if include_rule_id:
            return {"rule_id": self.rule_id, **data}
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RuleAst":
        _reject_unknown_keys(
            data,
            {
                "rule_id",
                "schema_version",
                "rule_family",
                "source",
                "target",
                "relation_type",
                "trigger_predicate",
                "response_predicate",
                "calibration_references",
                "candidate_pair_artifact_id",
                "metadata_artifact_id",
                "planner_provenance",
                "description_template",
            },
            "rule",
        )
        references = {
            str(key): CalibrationValueRef.from_dict(value)
            for key, value in data["calibration_references"].items()
        }
        return cls(
            rule_id=str(data["rule_id"]),
            schema_version=str(data["schema_version"]),
            rule_family=str(data.get("rule_family", RULE_FAMILY)),
            source=str(data["source"]),
            target=str(data["target"]),
            relation_type=str(data["relation_type"]),
            trigger_predicate=ChangedToPredicate.from_dict(data["trigger_predicate"]),
            response_predicate=ResponseMissingPredicate.from_dict(data["response_predicate"]),
            calibration_references=references,
            candidate_pair_artifact_id=str(data["candidate_pair_artifact_id"]),
            metadata_artifact_id=str(data["metadata_artifact_id"]),
            planner_provenance=PlannerProvenance.from_dict(data["planner_provenance"]),
            description_template=str(data["description_template"]),
        )


@dataclass(frozen=True)
class TimeSeriesWindow:
    series: Mapping[str, Sequence[float]]
    sampling_period_seconds: float
    timestamps_seconds: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if self.sampling_period_seconds <= 0.0:
            raise RuleDslError("sampling_period_seconds must be positive")
        lengths = {len(values) for values in self.series.values()}
        if len(lengths) != 1:
            raise RuleDslError("all window series must have equal lengths")
        if not lengths or next(iter(lengths)) < 2:
            raise RuleDslError("window must contain at least two samples")
        if self.timestamps_seconds is not None and len(self.timestamps_seconds) != next(iter(lengths)):
            raise RuleDslError("timestamps must match series length")


@dataclass(frozen=True)
class RuleEvaluation:
    rule_id: str
    anomaly: bool
    trigger_count: int
    missing_response_count: int
    matched_response_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuleEvaluator(Protocol):
    def evaluate(self, rule: RuleAst, window: TimeSeriesWindow) -> RuleEvaluation:
        """Evaluate a parsed AST over a time-series window."""


class MinimalRuleEvaluator:
    """Deterministic evaluator for the initial response-missing rule family."""

    def evaluate(self, rule: RuleAst, window: TimeSeriesWindow) -> RuleEvaluation:
        if rule.source not in window.series or rule.target not in window.series:
            raise RuleDslError("window must include rule source and target")

        source_values = tuple(float(item) for item in window.series[rule.source])
        target_values = tuple(float(item) for item in window.series[rule.target])
        timestamps = _window_timestamps(window)
        min_magnitude = rule.calibration_references["min_response_magnitude"].resolved_value
        max_delay = rule.calibration_references["max_response_delay_seconds"].resolved_value

        trigger_count = 0
        missing_response_count = 0
        matched_response_count = 0
        trigger = rule.trigger_predicate

        for index in range(1, len(source_values)):
            if source_values[index - 1] != trigger.from_state or source_values[index] != trigger.to_state:
                continue
            trigger_count += 1
            baseline = target_values[index - 1]
            matched = False
            for candidate_index in range(index, len(target_values)):
                delay = timestamps[candidate_index] - timestamps[index]
                if delay > max_delay:
                    break
                if target_values[candidate_index] - baseline >= min_magnitude:
                    matched = True
                    break
            if matched:
                matched_response_count += 1
            else:
                missing_response_count += 1

        return RuleEvaluation(
            rule_id=rule.rule_id,
            anomaly=missing_response_count > 0,
            trigger_count=trigger_count,
            missing_response_count=missing_response_count,
            matched_response_count=matched_response_count,
        )


class RuleSchemaRegistry:
    """Compatibility and syntax validator for planner and verifier use."""

    def __init__(
        self,
        *,
        metadata: MetadataRegistry,
        calibration_records: Mapping[str, CalibrationRecord] | None = None,
    ) -> None:
        self._metadata = metadata
        self._calibration_records = dict(calibration_records or {})

    def allowed_families(self, source_meta: VariableMetadata, target_meta: VariableMetadata) -> tuple[str, ...]:
        if (
            source_meta.role == VariableRole.ACTUATOR
            and source_meta.value_type == ValueType.BINARY
            and target_meta.role == VariableRole.SENSOR
            and target_meta.value_type == ValueType.CONTINUOUS
        ):
            return (RULE_FAMILY,)
        return ()

    def metadata_for(self, name: str) -> VariableMetadata:
        return self._metadata.get(name)

    def calibration_record_for(self, calibration_record_id: str) -> CalibrationRecord | None:
        return self._calibration_records.get(calibration_record_id)

    def validate(self, rule: RuleAst) -> list[SchemaIssue]:
        issues: list[SchemaIssue] = []
        source_meta = _metadata_or_issue(self._metadata, rule.source, issues, "source")
        target_meta = _metadata_or_issue(self._metadata, rule.target, issues, "target")

        if source_meta is not None and target_meta is not None:
            if rule.rule_family not in self.allowed_families(source_meta, target_meta):
                issues.append(
                    SchemaIssue(
                        code="TYPE_MISMATCH",
                        message="rule family is not allowed for source/target metadata types",
                        path="rule_family",
                    )
                )

        if rule.trigger_predicate.variable != rule.source:
            issues.append(SchemaIssue("EXTRA_VARIABLE", "trigger variable must equal source", "trigger_predicate.variable"))
        if rule.response_predicate.expected_response.variable != rule.target:
            issues.append(
                SchemaIssue("EXTRA_VARIABLE", "response variable must equal target", "response_predicate.expected_response.variable")
            )
        if (
            rule.response_predicate.expected_response.max_delay_seconds
            != rule.calibration_references["max_response_delay_seconds"]
        ):
            issues.append(
                SchemaIssue(
                    "CALIBRATION_MISMATCH",
                    "response delay reference must match rule calibration reference",
                    "response_predicate.expected_response.max_delay_seconds",
                )
            )
        if rule.response_predicate.expected_response.min_magnitude != rule.calibration_references["min_response_magnitude"]:
            issues.append(
                SchemaIssue(
                    "CALIBRATION_MISMATCH",
                    "response magnitude reference must match rule calibration reference",
                    "response_predicate.expected_response.min_magnitude",
                )
            )

        for key, reference in sorted(rule.calibration_references.items()):
            if key != reference.parameter_name:
                issues.append(SchemaIssue("CALIBRATION_MISMATCH", "reference key must match parameter_name", key))
            record = self._calibration_records.get(reference.calibration_record_id)
            if record is None:
                issues.append(
                    SchemaIssue("CALIBRATION_MISSING", "calibration record id was not supplied", f"calibration_references.{key}")
                )
                continue
            if record.parameter_name != reference.parameter_name:
                issues.append(
                    SchemaIssue("CALIBRATION_MISMATCH", "calibration parameter name changed", f"calibration_references.{key}")
                )
            if record.unit != reference.unit:
                issues.append(SchemaIssue("CALIBRATION_MISMATCH", "calibration unit changed", f"calibration_references.{key}"))
            if record.value != reference.resolved_value:
                issues.append(
                    SchemaIssue("NUMERIC_PARAMETER_MUTATED", "resolved numeric value differs from calibration record", key)
                )

        return issues


def parse_rule_json(text: str) -> RuleAst:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise RuleDslError("rule JSON must contain an object")
    _scan_payload(payload, "rule")
    return RuleAst.from_dict(payload)


def serialize_rule_json(rule: RuleAst) -> str:
    return json.dumps(rule.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def format_rule(rule: RuleAst) -> str:
    delay = rule.calibration_references["max_response_delay_seconds"].resolved_value
    magnitude = rule.calibration_references["min_response_magnitude"].resolved_value
    return (
        f"IF {rule.source} changed from {rule.trigger_predicate.from_state:g} "
        f"to {rule.trigger_predicate.to_state:g} AND {rule.target} fails to increase "
        f"by at least {magnitude:g} within {delay:g} seconds THEN anomaly"
    )


def _metadata_or_issue(
    metadata: MetadataRegistry,
    name: str,
    issues: list[SchemaIssue],
    path: str,
) -> VariableMetadata | None:
    try:
        return metadata.get(name)
    except Exception:
        issues.append(SchemaIssue("VARIABLE_NOT_FOUND", f"metadata not found for {name}", path))
        return None


def _window_timestamps(window: TimeSeriesWindow) -> tuple[float, ...]:
    first_series = next(iter(window.series.values()))
    if window.timestamps_seconds is not None:
        return tuple(float(item) for item in window.timestamps_seconds)
    return tuple(index * window.sampling_period_seconds for index in range(len(first_series)))


def _validate_identifier(value: str, path: str) -> None:
    if not _IDENTIFIER_RE.match(value):
        raise RuleDslError(f"invalid identifier at {path}: {value!r}")
    _reject_prohibited_payload(value, path)


def _reject_unknown_keys(data: Mapping[str, Any], allowed: set[str], path: str) -> None:
    extra = sorted(set(data) - allowed)
    if extra:
        raise RuleDslError(f"unsupported fields at {path}: {extra}")


def _scan_payload(value: Any, path: str) -> None:
    if isinstance(value, str):
        _reject_prohibited_payload(value, path)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _reject_prohibited_payload(str(key), path)
            _scan_payload(item, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for index, item in enumerate(value):
            _scan_payload(item, f"{path}[{index}]")


def _reject_prohibited_payload(value: str, path: str) -> None:
    lowered = value.lower()
    for pattern in _PROHIBITED_PAYLOAD_PATTERNS:
        if pattern in lowered:
            raise RuleDslError(f"prohibited payload at {path}")
