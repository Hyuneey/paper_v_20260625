"""Trusted array-only PA-free validation diagnostics for TASK-034."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np


class KpiValidationMetricError(ValueError):
    pass


def _binary_vector(value: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 1 or not np.all(np.isfinite(array)) or not np.all(np.isin(array, [0, 1])):
        raise KpiValidationMetricError(f"TASK034_{name.upper()}_BINARY_VECTOR_INVALID")
    return array.astype(np.int8, copy=True)


def direct_binary_validation_diagnostics(
    ground_truth_labels: np.ndarray, rule_prediction_labels: np.ndarray
) -> dict[str, Any]:
    truth = _binary_vector(ground_truth_labels, "ground_truth")
    prediction = _binary_vector(rule_prediction_labels, "prediction")
    if truth.shape != prediction.shape:
        raise KpiValidationMetricError("TASK034_METRIC_LENGTH_MISMATCH")
    tp = int(np.sum((truth == 1) & (prediction == 1)))
    fp = int(np.sum((truth == 0) & (prediction == 1)))
    tn = int(np.sum((truth == 0) & (prediction == 0)))
    fn = int(np.sum((truth == 1) & (prediction == 0)))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    point_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "metric_group": "direct_binary_validation_diagnostics",
        "point_adjustment": "disabled",
        "threshold_optimization": "none",
        "zero_division": 0.0,
        "confusion_counts": {
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn,
        },
        "precision": precision,
        "recall": recall,
        "point_f1": point_f1,
        "validation_positive_count": int(np.sum(truth == 1)),
        "validation_negative_count": int(np.sum(truth == 0)),
        "predicted_positive_count": int(np.sum(prediction == 1)),
        "predicted_negative_count": int(np.sum(prediction == 0)),
    }


def metric_protocol_hash() -> str:
    policy = {
        "name": "task034_direct_binary_validation_diagnostics_v1",
        "inputs": "binary arrays only",
        "point_adjustment": False,
        "threshold_optimization": False,
        "zero_division": 0.0,
    }
    encoded = json.dumps(policy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
