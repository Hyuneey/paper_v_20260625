"""Future metric schemas and qualified ARGOS validity conclusions for TASK-038A."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping


class AgentValiditySchemaError(ValueError):
    """Raised when a future validity record omits a predeclared dimension."""


class ValidityConclusion(str, Enum):
    STRONGLY_SUPPORTED = "strongly_supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"


REPAIR_METRIC_FIELDS = (
    "initial_runtime_failed_rule_count",
    "repair_calls",
    "repair_response_count",
    "repair_static_valid_count",
    "repair_executable_count",
    "repair_recovery_rate",
    "target_failure_recovered",
    "contrast_failure_recovered",
    "output_contract_failure_recovered",
    "mean_input_tokens",
    "mean_output_tokens",
    "total_tokens",
    "estimated_provider_cost",
    "mean_runtime_seconds",
)
REVIEW_DELTA_FIELDS = (
    "inner_precision_delta",
    "inner_recall_delta",
    "inner_point_f1_delta",
    "inner_event_f1_delta",
    "inner_FP_per_10000_delta",
    "reviewed_rule_static_failure_rate",
    "reviewed_rule_runtime_failure_rate",
    "reviewed_rule_regression_rate",
    "no_review_needed_rate",
    "mean_review_calls",
    "mean_input_tokens",
    "mean_output_tokens",
    "total_tokens",
    "estimated_provider_cost",
)
OUTER_COMPARISONS = ("A1_minus_A0", "A2_minus_A0", "A3_minus_A0", "A3_minus_A1", "A3_minus_A2")
OUTER_METRICS = (
    "precision",
    "recall",
    "point_f1",
    "event_f1",
    "FP_per_10000_normal",
    "FN_recovery",
    "FP_removal",
    "TP_removal",
    "true_anomaly_event_removal",
)
VALIDITY_DIMENSIONS = (
    "operational_validity",
    "incremental_review_value",
    "generalization",
    "detector_complementarity",
    "efficiency",
    "safety_and_reproducibility",
)


@dataclass(frozen=True)
class MethodologicalValidityRecord:
    conclusion: ValidityConclusion
    operational_validity: str
    incremental_review_value: str
    generalization: str
    detector_complementarity: str
    efficiency: str
    safety_and_reproducibility: str
    sealed_test_confirmed: bool
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["conclusion"] = self.conclusion.value
        value["rationale"] = list(self.rationale)
        return value


def future_metric_schema() -> dict[str, Any]:
    return {
        "repair_operability_fields": list(REPAIR_METRIC_FIELDS),
        "review_performance_fields": list(REVIEW_DELTA_FIELDS),
        "outer_comparisons": list(OUTER_COMPARISONS),
        "outer_metric_fields": list(OUTER_METRICS),
        "generalization_gap": [
            "inner_improvement",
            "outer_improvement",
            "inner_minus_outer_improvement",
        ],
        "validity_dimensions": list(VALIDITY_DIMENSIONS),
        "conclusion_categories": [item.value for item in ValidityConclusion],
    }


def validate_validity_record(record: Mapping[str, Any]) -> None:
    if record.get("conclusion") not in {
        item.value for item in ValidityConclusion
    }:
        raise AgentValiditySchemaError("TASK038A_VALIDITY_CONCLUSION_INVALID")
    missing = [field for field in VALIDITY_DIMENSIONS if field not in record]
    if missing:
        raise AgentValiditySchemaError("TASK038A_VALIDITY_DIMENSION_MISSING")
    if record["conclusion"] == ValidityConclusion.STRONGLY_SUPPORTED.value and not record.get(
        "sealed_test_confirmed"
    ):
        raise AgentValiditySchemaError("TASK038A_STRONG_REQUIRES_SEALED_TEST")
