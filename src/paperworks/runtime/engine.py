"""Deterministic runtime engine for verified DSL rule libraries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from paperworks.data import DataViewManifest, DataViewName
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.dsl import RuleAst, RuleSchemaRegistry, format_rule


class RuntimeRuleEngineError(ValueError):
    """Raised when runtime inputs violate the deterministic execution contract."""


@dataclass(frozen=True)
class RuntimeConfig:
    severity_mode: str = "binary"
    binary_severity: float = 1.0
    merge_adjacent_intervals: bool = True
    config_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.severity_mode != "binary":
            raise RuntimeRuleEngineError("only binary severity mode is supported")
        if self.binary_severity <= 0.0:
            raise RuntimeRuleEngineError("binary_severity must be positive")

    @property
    def config_hash(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimeSeriesBatch:
    series: Mapping[str, Sequence[float]]
    data_view: DataViewManifest
    timestamps_seconds: tuple[float, ...] | None = None
    batch_id: str = "unspecified"
    data_fingerprint: str = ""

    def __post_init__(self) -> None:
        if self.data_view.name != DataViewName.CANONICAL_RULE:
            raise RuntimeRuleEngineError("runtime requires canonical rule view")
        if (self.data_view.source_view or self.data_view.name.value) != "canonical_rule_view":
            raise RuntimeRuleEngineError("runtime requires source_view=canonical_rule_view")
        lengths = {len(values) for values in self.series.values()}
        if len(lengths) != 1:
            raise RuntimeRuleEngineError("all batch series must have equal lengths")
        if not lengths or next(iter(lengths)) < 2:
            raise RuntimeRuleEngineError("batch must contain at least two samples")
        if self.timestamps_seconds is not None and len(self.timestamps_seconds) != next(iter(lengths)):
            raise RuntimeRuleEngineError("timestamps must match batch length")
        if self.data_fingerprint and len(self.data_fingerprint) != 64:
            raise RuntimeRuleEngineError("data_fingerprint must be empty or a 64-character hash")

    @property
    def length(self) -> int:
        return len(next(iter(self.series.values())))

    @property
    def timestamps(self) -> tuple[float, ...]:
        if self.timestamps_seconds is not None:
            return self.timestamps_seconds
        return tuple(index * self.data_view.sampling_period_seconds for index in range(self.length))


@dataclass(frozen=True)
class VerifiedRuleLibrary:
    rules: tuple[RuleAst, ...]
    verification_report_ids: Mapping[str, str]
    library_id: str | None = None
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "verified_rule_library"

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise RuntimeRuleEngineError(f"unsupported schema_version: {self.schema_version}")
        if self.artifact_type != "verified_rule_library":
            raise RuntimeRuleEngineError("artifact_type must be verified_rule_library")
        rule_ids = {rule.rule_id for rule in self.rules}
        if len(rule_ids) != len(self.rules):
            raise RuntimeRuleEngineError("verified rule library contains duplicate rule_id values")
        if rule_ids != set(self.verification_report_ids):
            raise RuntimeRuleEngineError("verification_report_ids must cover every rule exactly")
        for report_id in self.verification_report_ids.values():
            if len(report_id) != 64:
                raise RuntimeRuleEngineError("verification report ids must be 64-character hashes")

    @property
    def resolved_library_id(self) -> str:
        if self.library_id is not None:
            return self.library_id
        return stable_hash(self.to_dict(include_library_id=False))

    def to_dict(self, *, include_library_id: bool = True) -> dict[str, Any]:
        data = {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "rules": [rule.to_dict() for rule in self.rules],
            "verification_report_ids": dict(sorted(self.verification_report_ids.items())),
        }
        if include_library_id:
            data["library_id"] = self.library_id
        return data


@dataclass(frozen=True)
class RuntimeFiringRecord:
    rule_id: str
    source: str
    target: str
    trigger_index: int
    alarm_start_index: int
    alarm_end_index: int
    alarm_start_seconds: float
    alarm_end_seconds: float
    severity: float
    observed_delta: float
    required_magnitude: float
    required_delay_seconds: float
    verification_report_id: str
    candidate_provenance: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidate_provenance"] = list(self.candidate_provenance)
        return data


@dataclass(frozen=True)
class AlarmInterval:
    alarm_start_seconds: float
    alarm_end_seconds: float
    severity: float
    rule_ids: tuple[str, ...]
    firing_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "alarm_start_seconds": self.alarm_start_seconds,
            "alarm_end_seconds": self.alarm_end_seconds,
            "severity": self.severity,
            "rule_ids": list(self.rule_ids),
            "firing_count": self.firing_count,
        }


@dataclass(frozen=True)
class RuntimeExplanation:
    alarm_start: float
    alarm_end: float
    rule_id: str
    variables: tuple[str, str]
    expected_relation: str
    observed_violation: str
    calibration_basis: Mapping[str, str]
    candidate_provenance: tuple[str, ...]
    source_view: str
    sampling_period_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "alarm_start": self.alarm_start,
            "alarm_end": self.alarm_end,
            "rule_id": self.rule_id,
            "variables": list(self.variables),
            "expected_relation": self.expected_relation,
            "observed_violation": self.observed_violation,
            "calibration_basis": dict(sorted(self.calibration_basis.items())),
            "candidate_provenance": list(self.candidate_provenance),
            "source_view": self.source_view,
            "sampling_period_seconds": self.sampling_period_seconds,
        }


@dataclass(frozen=True)
class RuntimeEvaluation:
    library_id: str
    batch_id: str
    source_view: str
    sampling_period_seconds: float
    firing_records: tuple[RuntimeFiringRecord, ...]
    alarm_intervals: tuple[AlarmInterval, ...]
    explanations: tuple[RuntimeExplanation, ...]
    aggregate_rule_score: float
    runtime_statistics: Mapping[str, int | float]
    config_hash: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "runtime_evaluation"

    @property
    def evaluation_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "library_id": self.library_id,
            "batch_id": self.batch_id,
            "source_view": self.source_view,
            "sampling_period_seconds": self.sampling_period_seconds,
            "firing_records": [record.to_dict() for record in self.firing_records],
            "alarm_intervals": [interval.to_dict() for interval in self.alarm_intervals],
            "explanations": [explanation.to_dict() for explanation in self.explanations],
            "aggregate_rule_score": self.aggregate_rule_score,
            "runtime_statistics": dict(sorted(self.runtime_statistics.items())),
            "config_hash": self.config_hash,
        }


class RuntimeRuleEngine:
    """LLM-free runtime executor for verified DSL rules."""

    def __init__(self, *, registry: RuleSchemaRegistry, config: RuntimeConfig | None = None) -> None:
        self._registry = registry
        self._config = config or RuntimeConfig()
        self._library: VerifiedRuleLibrary | None = None

    def load_library(self, library: VerifiedRuleLibrary) -> None:
        for rule in library.rules:
            issues = self._registry.validate(rule)
            if issues:
                codes = ", ".join(issue.code for issue in issues)
                raise RuntimeRuleEngineError(f"unverified or invalid rule cannot be loaded: {codes}")
        self._library = library

    def evaluate(self, data: TimeSeriesBatch) -> RuntimeEvaluation:
        if self._library is None:
            raise RuntimeRuleEngineError("verified rule library has not been loaded")
        records: list[RuntimeFiringRecord] = []
        explanations: list[RuntimeExplanation] = []
        for rule in self._library.rules:
            rule_records = _evaluate_rule(rule, data, self._library, self._config)
            records.extend(rule_records)
            explanations.extend(_explanation(rule, data, record) for record in rule_records)

        sorted_records = tuple(sorted(records, key=lambda item: (item.alarm_start_seconds, item.rule_id, item.trigger_index)))
        alarm_intervals = _merge_alarm_intervals(sorted_records, data.data_view.sampling_period_seconds, self._config)
        aggregate_score = max((record.severity for record in sorted_records), default=0.0)
        return RuntimeEvaluation(
            library_id=self._library.resolved_library_id,
            batch_id=data.batch_id,
            source_view=data.data_view.source_view or data.data_view.name.value,
            sampling_period_seconds=data.data_view.sampling_period_seconds,
            firing_records=sorted_records,
            alarm_intervals=alarm_intervals,
            explanations=tuple(sorted(explanations, key=lambda item: (item.alarm_start, item.rule_id))),
            aggregate_rule_score=aggregate_score,
            runtime_statistics={
                "rule_count": len(self._library.rules),
                "sample_count": data.length,
                "firing_count": len(sorted_records),
                "alarm_interval_count": len(alarm_intervals),
            },
            config_hash=self._config.config_hash,
        )


def _evaluate_rule(
    rule: RuleAst,
    data: TimeSeriesBatch,
    library: VerifiedRuleLibrary,
    config: RuntimeConfig,
) -> tuple[RuntimeFiringRecord, ...]:
    if rule.source not in data.series or rule.target not in data.series:
        raise RuntimeRuleEngineError("runtime batch missing rule variables")
    source_values = tuple(float(item) for item in data.series[rule.source])
    target_values = tuple(float(item) for item in data.series[rule.target])
    timestamps = data.timestamps
    trigger = rule.trigger_predicate
    required_delay = rule.calibration_references["max_response_delay_seconds"].resolved_value
    required_magnitude = rule.calibration_references["min_response_magnitude"].resolved_value
    records: list[RuntimeFiringRecord] = []

    for index in range(1, len(source_values)):
        if source_values[index - 1] != trigger.from_state or source_values[index] != trigger.to_state:
            continue
        baseline = target_values[index - 1]
        deadline = timestamps[index] + required_delay
        matched = False
        max_observed_delta = target_values[index] - baseline
        end_index = index
        for candidate_index in range(index, len(target_values)):
            if timestamps[candidate_index] > deadline:
                break
            end_index = candidate_index
            delta = target_values[candidate_index] - baseline
            max_observed_delta = max(max_observed_delta, delta)
            if delta >= required_magnitude:
                matched = True
                break
        if matched:
            continue
        records.append(
            RuntimeFiringRecord(
                rule_id=rule.rule_id,
                source=rule.source,
                target=rule.target,
                trigger_index=index,
                alarm_start_index=index,
                alarm_end_index=end_index,
                alarm_start_seconds=timestamps[index],
                alarm_end_seconds=timestamps[end_index],
                severity=config.binary_severity,
                observed_delta=max_observed_delta,
                required_magnitude=required_magnitude,
                required_delay_seconds=required_delay,
                verification_report_id=library.verification_report_ids[rule.rule_id],
                candidate_provenance=rule.planner_provenance.source_artifact_ids,
            )
        )
    return tuple(records)


def _merge_alarm_intervals(
    records: Sequence[RuntimeFiringRecord],
    sampling_period_seconds: float,
    config: RuntimeConfig,
) -> tuple[AlarmInterval, ...]:
    if not records:
        return ()
    intervals: list[AlarmInterval] = []
    current_start = records[0].alarm_start_seconds
    current_end = records[0].alarm_end_seconds
    current_severity = records[0].severity
    rule_ids = {records[0].rule_id}
    firing_count = 1
    for record in records[1:]:
        merge_gap = sampling_period_seconds if config.merge_adjacent_intervals else 0.0
        if record.alarm_start_seconds <= current_end + merge_gap:
            current_end = max(current_end, record.alarm_end_seconds)
            current_severity = max(current_severity, record.severity)
            rule_ids.add(record.rule_id)
            firing_count += 1
            continue
        intervals.append(
            AlarmInterval(
                alarm_start_seconds=current_start,
                alarm_end_seconds=current_end,
                severity=current_severity,
                rule_ids=tuple(sorted(rule_ids)),
                firing_count=firing_count,
            )
        )
        current_start = record.alarm_start_seconds
        current_end = record.alarm_end_seconds
        current_severity = record.severity
        rule_ids = {record.rule_id}
        firing_count = 1
    intervals.append(
        AlarmInterval(
            alarm_start_seconds=current_start,
            alarm_end_seconds=current_end,
            severity=current_severity,
            rule_ids=tuple(sorted(rule_ids)),
            firing_count=firing_count,
        )
    )
    return tuple(intervals)


def _explanation(rule: RuleAst, data: TimeSeriesBatch, record: RuntimeFiringRecord) -> RuntimeExplanation:
    calibration_basis = {
        name: reference.calibration_record_id for name, reference in sorted(rule.calibration_references.items())
    }
    return RuntimeExplanation(
        alarm_start=record.alarm_start_seconds,
        alarm_end=record.alarm_end_seconds,
        rule_id=rule.rule_id,
        variables=(rule.source, rule.target),
        expected_relation=format_rule(rule),
        observed_violation=(
            f"{rule.target} increased by {record.observed_delta:g}, "
            f"below required {record.required_magnitude:g} within {record.required_delay_seconds:g} seconds"
        ),
        calibration_basis=calibration_basis,
        candidate_provenance=record.candidate_provenance,
        source_view=data.data_view.source_view or data.data_view.name.value,
        sampling_period_seconds=data.data_view.sampling_period_seconds,
    )
