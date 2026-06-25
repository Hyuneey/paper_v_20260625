"""Evaluation harness interfaces and metrics."""

from paperworks.evaluation.harness import (
    EvaluationConfig,
    EvaluationError,
    EvaluationMetric,
    EvaluationProtocol,
    EvaluationReport,
    SealedTestAudit,
    assert_final_test_access_allowed,
    compute_auprc,
    compute_auroc,
    compute_pa_free_point_metrics,
    compute_point_adjusted_supplement,
    compute_range_iou,
    evaluate_point_predictions,
    validate_artifact_provenance,
    validate_config_frozen,
)

__all__ = [
    "EvaluationConfig",
    "EvaluationError",
    "EvaluationMetric",
    "EvaluationProtocol",
    "EvaluationReport",
    "SealedTestAudit",
    "assert_final_test_access_allowed",
    "compute_auprc",
    "compute_auroc",
    "compute_pa_free_point_metrics",
    "compute_point_adjusted_supplement",
    "compute_range_iou",
    "evaluate_point_predictions",
    "validate_artifact_provenance",
    "validate_config_frozen",
]
