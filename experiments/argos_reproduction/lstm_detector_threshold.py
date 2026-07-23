"""Inner-only direct PA-free threshold selection for TASK-037B."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np

from experiments.argos_reproduction.direct_event_metrics import direct_pa_free_metrics


class DetectorThresholdError(ValueError):
    pass


THRESHOLD_PROTOCOL = {
    "score_split": "inner",
    "selection_metric": "direct_PA_free_point_F1",
    "candidate_thresholds": "unique_finite_inner_scores",
    "comparison_operator": ">=",
    "point_adjustment": False,
    "tie_breaking": ["maximum_point_F1", "highest_threshold", "stable_original_order"],
}


def threshold_protocol_hash() -> str:
    encoded = json.dumps(
        THRESHOLD_PROTOCOL, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def binary_predictions(scores: object, threshold: float) -> np.ndarray:
    array = np.asarray(scores, dtype=np.float64)
    if array.ndim != 1 or not np.all(np.isfinite(array)) or not np.isfinite(threshold):
        raise DetectorThresholdError("TASK037B_SCORE_OR_THRESHOLD_INVALID")
    return (array >= float(threshold)).astype(np.int8)


def select_inner_threshold(scores: object, labels: object) -> dict[str, Any]:
    score_array = np.asarray(scores, dtype=np.float64)
    label_array = np.asarray(labels)
    if score_array.ndim != 1 or not np.all(np.isfinite(score_array)):
        raise DetectorThresholdError("TASK037B_INNER_SCORE_INVALID")
    if label_array.ndim != 1 or len(label_array) != len(score_array):
        raise DetectorThresholdError("TASK037B_INNER_LABEL_LENGTH_INVALID")
    if not np.all(np.isin(label_array, (0, 1))):
        raise DetectorThresholdError("TASK037B_INNER_LABEL_DOMAIN_INVALID")
    candidates = np.unique(score_array)
    if len(candidates) == 0:
        raise DetectorThresholdError("TASK037B_THRESHOLD_CANDIDATES_EMPTY")
    order = np.argsort(-score_array, kind="mergesort")
    sorted_scores = score_array[order]
    sorted_labels = label_array[order].astype(np.int8, copy=False)
    total_positive = int(np.sum(sorted_labels == 1))
    tp = 0
    fp = 0
    best_key: tuple[float, float, int] | None = None
    selected_threshold = float(sorted_scores[0])
    start = 0
    group_order = 0
    while start < len(sorted_scores):
        end = start + 1
        while end < len(sorted_scores) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        group = sorted_labels[start:end]
        tp += int(np.sum(group == 1))
        fp += int(np.sum(group == 0))
        fn = total_positive - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        threshold = float(sorted_scores[start])
        key = (f1, threshold, -group_order)
        if best_key is None or key > best_key:
            best_key = key
            selected_threshold = threshold
        start = end
        group_order += 1
    metrics = direct_pa_free_metrics(
        label_array, binary_predictions(score_array, selected_threshold)
    )
    return {
        "candidate_threshold_count": int(len(candidates)),
        "selected_threshold": selected_threshold,
        "selected_confusion_counts": {
            key: int(metrics[key])
            for key in ("true_positive", "false_positive", "true_negative", "false_negative")
        },
        "selected_precision": float(metrics["precision"]),
        "selected_recall": float(metrics["recall"]),
        "selected_f1": float(metrics["point_f1"]),
        "threshold_protocol_hash": threshold_protocol_hash(),
        "point_adjustment": False,
    }
