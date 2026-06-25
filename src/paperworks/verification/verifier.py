"""Deterministic verification for parsed DSL rules."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from paperworks.data import SplitRole, assert_split_permitted
from paperworks.data.contracts import SCHEMA_VERSION, stable_hash
from paperworks.dsl import MinimalRuleEvaluator, RuleAst, RuleEvaluation, RuleSchemaRegistry, SchemaIssue, TimeSeriesWindow, parse_rule_json


class VerificationError(ValueError):
    """Raised when verifier inputs are structurally invalid."""


@dataclass(frozen=True)
class VerificationConfig:
    max_normal_false_fire_rate: float
    min_validation_coverage: float
    firing_overlap_jaccard_threshold: float
    min_calibration_support_count: int
    parameter_neighborhood_relative_tolerance: float = 0.0
    config_version: str = "1.0"

    def __post_init__(self) -> None:
        for name, value in (
            ("max_normal_false_fire_rate", self.max_normal_false_fire_rate),
            ("min_validation_coverage", self.min_validation_coverage),
            ("firing_overlap_jaccard_threshold", self.firing_overlap_jaccard_threshold),
            ("parameter_neighborhood_relative_tolerance", self.parameter_neighborhood_relative_tolerance),
        ):
            if value < 0.0 or value > 1.0:
                raise VerificationError(f"{name} must be in [0, 1]")
        if self.min_calibration_support_count <= 0:
            raise VerificationError("min_calibration_support_count must be positive")

    @property
    def config_hash(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationDataset:
    split_role: SplitRole
    windows: tuple[TimeSeriesWindow, ...]
    dataset_name: str = "synthetic"
    data_fingerprint: str = ""
    split_id: str | None = None

    def __post_init__(self) -> None:
        if self.split_role == SplitRole.TEST:
            raise VerificationError("test split is prohibited for rule verification")
        if self.data_fingerprint and len(self.data_fingerprint) != 64:
            raise VerificationError("data_fingerprint must be empty or a 64-character hash")
        if self.split_id is not None and len(self.split_id) != 64:
            raise VerificationError("split_id must be a 64-character hash")


@dataclass(frozen=True)
class FeedbackIssue:
    code: str
    message: str
    suggested_action: str
    path: str | None = None
    observed: float | None = None
    limit: float | None = None
    duplicate_rule_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "suggested_action": self.suggested_action,
            "path": self.path,
            "observed": self.observed,
            "limit": self.limit,
            "duplicate_rule_id": self.duplicate_rule_id,
        }


@dataclass(frozen=True)
class VerificationReport:
    rule_id: str
    status: str
    issues: tuple[FeedbackIssue, ...]
    metrics: Mapping[str, float | int]
    duplicate_references: tuple[str, ...]
    config_hash: str
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "verification_report"

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise VerificationError(f"unsupported schema_version: {self.schema_version}")
        if self.artifact_type != "verification_report":
            raise VerificationError("artifact_type must be verification_report")
        if self.status not in {"passed", "rejected"}:
            raise VerificationError("status must be passed or rejected")
        if self.status == "passed" and self.issues:
            raise VerificationError("passed reports must not contain issues")
        if len(self.config_hash) != 64:
            raise VerificationError("config_hash must be a 64-character hash")

    @property
    def report_id(self) -> str:
        return stable_hash(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_type": self.artifact_type,
            "rule_id": self.rule_id,
            "status": self.status,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": dict(sorted(self.metrics.items())),
            "duplicate_references": list(self.duplicate_references),
            "config_hash": self.config_hash,
        }


def verify_rule_json(
    rule_json: str,
    *,
    registry: RuleSchemaRegistry,
    normal_dataset: VerificationDataset,
    validation_dataset: VerificationDataset,
    existing_rules: Sequence[RuleAst] = (),
    config: VerificationConfig,
) -> VerificationReport:
    """Parse and verify a serialized rule without executing arbitrary code."""

    try:
        rule = parse_rule_json(rule_json)
    except Exception as exc:
        return VerificationReport(
            rule_id="unparsed",
            status="rejected",
            issues=(
                FeedbackIssue(
                    code="DSL_SCHEMA_INVALID",
                    message=str(exc),
                    suggested_action="regenerate_valid_json_dsl",
                    path="rule_json",
                ),
            ),
            metrics={},
            duplicate_references=(),
            config_hash=config.config_hash,
        )
    return verify_rule(
        rule,
        registry=registry,
        normal_dataset=normal_dataset,
        validation_dataset=validation_dataset,
        existing_rules=existing_rules,
        config=config,
    )


def verify_rule(
    rule: RuleAst,
    *,
    registry: RuleSchemaRegistry,
    normal_dataset: VerificationDataset,
    validation_dataset: VerificationDataset,
    existing_rules: Sequence[RuleAst] = (),
    config: VerificationConfig,
) -> VerificationReport:
    """Run deterministic schema, provenance, empirical, and duplicate checks."""

    _assert_verification_splits(normal_dataset, validation_dataset)
    issues: list[FeedbackIssue] = []
    duplicate_references: list[str] = []

    issues.extend(_schema_issues(registry.validate(rule)))
    issues.extend(_calibration_support_issues(rule, registry, config))

    evaluator = MinimalRuleEvaluator()
    normal_evaluations = _evaluate_windows(rule, normal_dataset.windows, evaluator)
    validation_evaluations = _evaluate_windows(rule, validation_dataset.windows, evaluator)
    metrics = _metrics(normal_evaluations, validation_evaluations)

    if metrics["normal_false_fire_rate"] > config.max_normal_false_fire_rate:
        issues.append(
            FeedbackIssue(
                code="NORMAL_FP_TOO_HIGH",
                message="normal false firing exceeds configured limit",
                suggested_action="narrow_trigger_or_strengthen_condition",
                observed=float(metrics["normal_false_fire_rate"]),
                limit=config.max_normal_false_fire_rate,
            )
        )
    if metrics["validation_coverage"] < config.min_validation_coverage:
        issues.append(
            FeedbackIssue(
                code="VALIDATION_COVERAGE_TOO_LOW",
                message="validation firing coverage is below configured limit",
                suggested_action="broaden_condition_or_review_candidate_pair",
                observed=float(metrics["validation_coverage"]),
                limit=config.min_validation_coverage,
            )
        )

    for existing in existing_rules:
        structural_issue = _structural_duplicate_issue(rule, existing, config)
        if structural_issue is not None:
            issues.append(structural_issue)
            duplicate_references.append(existing.rule_id)
            continue
        overlap = _firing_jaccard(
            _firing_vector(validation_evaluations),
            _firing_vector(_evaluate_windows(existing, validation_dataset.windows, evaluator)),
        )
        if overlap >= config.firing_overlap_jaccard_threshold:
            issues.append(
                FeedbackIssue(
                    code="FIRING_OVERLAP_DUPLICATE",
                    message="validation firing overlap exceeds configured duplicate threshold",
                    suggested_action="deduplicate_or_select_more_specific_rule",
                    observed=overlap,
                    limit=config.firing_overlap_jaccard_threshold,
                    duplicate_rule_id=existing.rule_id,
                )
            )
            duplicate_references.append(existing.rule_id)

    unique_duplicates = tuple(sorted(set(duplicate_references)))
    return VerificationReport(
        rule_id=rule.rule_id,
        status="rejected" if issues else "passed",
        issues=tuple(issues),
        metrics=metrics,
        duplicate_references=unique_duplicates,
        config_hash=config.config_hash,
    )


def _assert_verification_splits(normal_dataset: VerificationDataset, validation_dataset: VerificationDataset) -> None:
    assert_split_permitted(normal_dataset.split_role, "profile_relation")
    assert_split_permitted(validation_dataset.split_role, "verify_rule")


def _schema_issues(issues: Sequence[SchemaIssue]) -> tuple[FeedbackIssue, ...]:
    return tuple(
        FeedbackIssue(
            code=issue.code,
            message=issue.message,
            suggested_action=_suggested_action(issue.code),
            path=issue.path,
        )
        for issue in issues
    )


def _calibration_support_issues(
    rule: RuleAst,
    registry: RuleSchemaRegistry,
    config: VerificationConfig,
) -> tuple[FeedbackIssue, ...]:
    issues: list[FeedbackIssue] = []
    for parameter_name, reference in sorted(rule.calibration_references.items()):
        record = registry.calibration_record_for(reference.calibration_record_id)
        if record is None:
            continue
        if record.normal_support_count < config.min_calibration_support_count:
            issues.append(
                FeedbackIssue(
                    code="INSUFFICIENT_NORMAL_SUPPORT",
                    message=f"calibration support too low for {parameter_name}",
                    suggested_action="collect_more_normal_support_or_drop_rule",
                    path=f"calibration_references.{parameter_name}",
                    observed=float(record.normal_support_count),
                    limit=float(config.min_calibration_support_count),
                )
            )
    return tuple(issues)


def _evaluate_windows(
    rule: RuleAst,
    windows: Sequence[TimeSeriesWindow],
    evaluator: MinimalRuleEvaluator,
) -> tuple[RuleEvaluation, ...]:
    return tuple(evaluator.evaluate(rule, window) for window in windows)


def _metrics(
    normal_evaluations: Sequence[RuleEvaluation],
    validation_evaluations: Sequence[RuleEvaluation],
) -> dict[str, float | int]:
    normal_count = len(normal_evaluations)
    validation_count = len(validation_evaluations)
    normal_fire_count = sum(1 for evaluation in normal_evaluations if evaluation.anomaly)
    validation_fire_count = sum(1 for evaluation in validation_evaluations if evaluation.anomaly)
    return {
        "normal_window_count": normal_count,
        "normal_false_fire_count": normal_fire_count,
        "normal_false_fire_rate": normal_fire_count / normal_count if normal_count else 0.0,
        "validation_window_count": validation_count,
        "validation_fire_count": validation_fire_count,
        "validation_coverage": validation_fire_count / validation_count if validation_count else 0.0,
    }


def _structural_duplicate_issue(
    rule: RuleAst,
    existing: RuleAst,
    config: VerificationConfig,
) -> FeedbackIssue | None:
    if _structural_signature(rule) == _structural_signature(existing):
        return FeedbackIssue(
            code="STRUCTURAL_DUPLICATE",
            message="rule has identical structural signature",
            suggested_action="deduplicate_rule",
            duplicate_rule_id=existing.rule_id,
        )
    if _same_pair_family(rule, existing) and _parameters_within_neighborhood(rule, existing, config):
        return FeedbackIssue(
            code="STRUCTURAL_DUPLICATE",
            message="rule has same pair/family and parameter-neighborhood duplicate",
            suggested_action="deduplicate_or_keep_best_supported_rule",
            duplicate_rule_id=existing.rule_id,
        )
    return None


def _structural_signature(rule: RuleAst) -> str:
    return stable_hash(
        {
            "source": rule.source,
            "target": rule.target,
            "relation_type": rule.relation_type,
            "rule_family": rule.rule_family,
            "trigger_predicate": rule.trigger_predicate.to_dict(),
            "response_predicate": rule.response_predicate.to_dict(),
        }
    )


def _same_pair_family(left: RuleAst, right: RuleAst) -> bool:
    return (
        left.source == right.source
        and left.target == right.target
        and left.relation_type == right.relation_type
        and left.rule_family == right.rule_family
    )


def _parameters_within_neighborhood(left: RuleAst, right: RuleAst, config: VerificationConfig) -> bool:
    for parameter_name in ("max_response_delay_seconds", "min_response_magnitude"):
        left_value = left.calibration_references[parameter_name].resolved_value
        right_value = right.calibration_references[parameter_name].resolved_value
        scale = max(abs(left_value), abs(right_value), 1.0)
        if abs(left_value - right_value) / scale > config.parameter_neighborhood_relative_tolerance:
            return False
    return True


def _firing_vector(evaluations: Sequence[RuleEvaluation]) -> tuple[bool, ...]:
    return tuple(evaluation.anomaly for evaluation in evaluations)


def _firing_jaccard(left: Sequence[bool], right: Sequence[bool]) -> float:
    if len(left) != len(right):
        raise VerificationError("duplicate firing vectors must be aligned")
    union = sum(1 for l_value, r_value in zip(left, right) if l_value or r_value)
    if union == 0:
        return 0.0
    intersection = sum(1 for l_value, r_value in zip(left, right) if l_value and r_value)
    return intersection / union


def _suggested_action(code: str) -> str:
    return {
        "DSL_SCHEMA_INVALID": "regenerate_valid_json_dsl",
        "VARIABLE_NOT_FOUND": "use_only_candidate_pair_variables",
        "TYPE_MISMATCH": "select_compatible_rule_family",
        "CALIBRATION_MISSING": "attach_required_calibration_record",
        "CALIBRATION_MISMATCH": "restore_calibrated_parameter_reference",
        "NUMERIC_PARAMETER_MUTATED": "restore_calibrated_numeric_value",
    }.get(code, "review_rule")
