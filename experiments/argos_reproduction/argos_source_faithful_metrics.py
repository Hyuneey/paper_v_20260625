"""Source-faithful ARGOS smoothing and validation-label metric searches."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

import numpy as np


EPS = 1e-15
SOURCE_COMMIT = "6b24161ff08de069840a1fb4fbaecf7bf8e393f1"
SOURCE_BLOBS = {
    "common/common.py": "2c1bd7546df4c547770b6055eea49ea169ea64a4",
    "eval_metrics/point_f1.py": "a96440baf55a0859a7d08831eeaee6871d170bf1",
    "eval_metrics/point_f1pa.py": "ec4b57072086fb907b23b6cce73cb50585c17c42",
    "eval_metrics/event_f1pa.py": "ef7c77ab087500b70ada062f81d75d0125258348",
    "agent/review_agent.py": "83936fdfc2875d245f79cd556b9ded96c6d1af25",
}


class ArgosMetricFidelityError(ValueError):
    pass


def _vectors(scores: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    score_array = np.asarray(scores, dtype=float)
    label_array = np.asarray(labels)
    if score_array.ndim != 1 or label_array.ndim != 1 or score_array.shape != label_array.shape:
        raise ArgosMetricFidelityError("TASK034_METRIC_VECTOR_INVALID")
    if not np.all(np.isfinite(score_array)) or not np.all(np.isin(label_array, [0, 1])):
        raise ArgosMetricFidelityError("TASK034_METRIC_DOMAIN_INVALID")
    return score_array.copy(), label_array.astype(np.int8, copy=True)


def smooth_labels(labels: np.ndarray, window_size: int = 3) -> np.ndarray:
    """Exact loop structure from pinned ``common/common.py``."""
    values = np.asarray(labels)
    if values.ndim != 1 or window_size <= 0:
        raise ArgosMetricFidelityError("TASK034_SMOOTH_INPUT_INVALID")
    new_labels = np.zeros_like(values, dtype=float)
    for i in range(len(values)):
        start = max(0, i - window_size // 2)
        end = min(len(values), i + window_size // 2 + 1)
        mean_value = np.mean(values[start:end])
        for j in range(start, end):
            new_labels[j] += mean_value
    return new_labels


def _metric(name: str, precision: float, recall: float, f1: float, threshold: float) -> dict[str, Any]:
    return {
        "name": name,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "threshold": float(threshold),
    }


def point_f1(scores: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    """Equivalent to sklearn precision_recall_curve plus pinned nanargmax selection."""
    values, truth = _vectors(scores, labels)
    thresholds = np.unique(values)
    precision: list[float] = []
    recall: list[float] = []
    positives = int(np.sum(truth == 1))
    for threshold in thresholds:
        predicted = values >= threshold
        tp = int(np.sum(predicted & (truth == 1)))
        fp = int(np.sum(predicted & (truth == 0)))
        precision.append(tp / (tp + fp) if tp + fp else 0.0)
        recall.append(tp / positives if positives else 0.0)
    precision.append(1.0)
    recall.append(0.0)
    p = np.asarray(precision, dtype=float)
    r = np.asarray(recall, dtype=float)
    denominator = p + r
    all_f1 = np.divide(2 * p * r, denominator, out=np.zeros_like(denominator), where=denominator != 0)
    best = int(np.nanargmax(all_f1))
    # Pinned PointF1 does not retain sklearn's threshold and emits F1Class default -1.
    return _metric("point-wise f1", p[best], r[best], all_f1[best], -1.0)


def _point_adjusted_search(scores: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    values, truth = _vectors(scores, labels)
    total_anomaly = int(np.sum(truth > 0.5))
    search_set: list[tuple[float, int, bool]] = []
    flag = 0
    current_length = 0
    current_max = 0.0
    for index in range(len(truth)):
        if truth[index] > 0.5:
            if flag == 1:
                current_length += 1
                current_max = values[index] if values[index] > current_max else current_max
            else:
                flag = 1
                current_length = 1
                current_max = values[index]
        else:
            if flag == 1:
                flag = 0
                search_set.append((current_max, current_length, True))
                search_set.append((values[index], 1, False))
                current_max = 0.0
            else:
                search_set.append((values[index], 1, False))
    if flag == 1:
        search_set.append((current_max, current_length, True))
    search_set.sort(key=lambda item: item[0], reverse=True)
    best_f1 = threshold = predicted_count = true_positive = 0.0
    best_predicted = best_true_positive = 0.0
    for score, weight, anomaly in search_set:
        predicted_count += weight
        if anomaly:
            true_positive += weight
        precision = true_positive / (predicted_count + EPS)
        recall = true_positive / (total_anomaly + EPS)
        f1 = 2 * precision * recall / (precision + recall + EPS)
        if f1 > best_f1:
            best_f1 = f1
            threshold = score
            best_predicted = predicted_count
            best_true_positive = true_positive
    precision = best_true_positive / (best_predicted + EPS)
    recall = best_true_positive / (total_anomaly + EPS)
    return _metric("best f1 under pa", precision, recall, best_f1, threshold)


def _event_adjusted_search(scores: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    values, truth = _vectors(scores, labels)
    weight: Callable[[int], int] = lambda _: 1
    total_anomaly = 0
    anomaly_flag = 0
    start = 0
    for index in range(len(truth)):
        if truth[index] > 0.5 and anomaly_flag == 0:
            anomaly_flag = 1
            start = index
        elif truth[index] <= 0.5 and anomaly_flag == 1:
            anomaly_flag = 0
            total_anomaly += weight(index - start)
        if anomaly_flag == 1 and index == len(truth) - 1:
            anomaly_flag = 0
            total_anomaly += weight(index + 1 - start)
    search_set: list[tuple[Any, ...]] = []
    flag = 0
    current_length = 0
    current_max = 0.0
    start = 0
    for index in range(len(truth)):
        if truth[index] > 0.5:
            if flag == 1:
                current_length += 1
                current_max = values[index] if values[index] > current_max else current_max
            else:
                flag = 1
                current_length = 1
                current_max = values[index]
                start = index
        else:
            if flag == 1:
                flag = 0
                search_set.append((current_max, weight(current_length), True, start, start + current_length))
                search_set.append((values[index], 1, False))
                current_max = 0.0
            else:
                search_set.append((values[index], 1, False))
    if flag == 1:
        search_set.append((current_max, weight(current_length), True, start, start + current_length))
    search_set.sort(key=lambda item: item[0], reverse=True)
    best_f1 = threshold = predicted_count = true_positive = 0.0
    best_predicted = best_true_positive = 0.0
    for item in search_set:
        predicted_count += item[1]
        if item[2]:
            true_positive += item[1]
        precision = true_positive / (predicted_count + EPS)
        recall = true_positive / (total_anomaly + EPS)
        f1 = 2 * precision * recall / (precision + recall + EPS)
        if f1 > best_f1:
            best_f1 = f1
            threshold = item[0]
            best_predicted = predicted_count
            best_true_positive = true_positive
    precision = best_true_positive / (best_predicted + EPS)
    recall = best_true_positive / (total_anomaly + EPS)
    return _metric("event-based f1 under pa with mode squeeze", precision, recall, best_f1, threshold)


def argos_label_aware_validation_diagnostics(
    binary_predictions: np.ndarray, validation_labels: np.ndarray
) -> dict[str, Any]:
    predictions, labels = _vectors(binary_predictions, validation_labels)
    scores = smooth_labels(predictions, window_size=3)
    return {
        "metric_group": "argos_label_aware_validation_diagnostics",
        "supplementary_only": True,
        "selection_split": "validation",
        "smoothing_window": 3,
        "score_source": "smooth_labels_window_3",
        "source_commit": SOURCE_COMMIT,
        "source_blobs": dict(SOURCE_BLOBS),
        "tie_breaking_policy": (
            "stable descending score order; strict f1 improvement retains the first encountered optimum"
        ),
        "point_f1": point_f1(scores, labels),
        "point_f1_pa": _point_adjusted_search(scores, labels),
        "event_f1_pa": _event_adjusted_search(scores, labels),
        "smoothed_scores": scores,
    }


def source_faithful_metric_protocol_hash() -> str:
    policy = {
        "version": "task034_argos_source_faithful_v1",
        "source_commit": SOURCE_COMMIT,
        "source_blobs": SOURCE_BLOBS,
        "smoothing_window": 3,
        "event_mode": "squeeze",
        "point_f1_threshold_retention": -1.0,
        "tie_breaking": "stable_sort_then_strict_improvement",
    }
    return hashlib.sha256(
        json.dumps(policy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def verify_frozen_synthetic_fidelity() -> dict[str, Any]:
    """Verify frozen source-derived expectations before private KPI metrics."""
    predictions = np.asarray([0, 0, 1, 0, 0], dtype=np.int8)
    labels = np.asarray([0, 0, 1, 0, 0], dtype=np.int8)
    expected_scores = np.asarray([1 / 3, 2 / 3, 1.0, 2 / 3, 1 / 3], dtype=float)
    result = argos_label_aware_validation_diagnostics(predictions, labels)
    checks = {
        "smooth_labels": bool(np.allclose(result["smoothed_scores"], expected_scores)),
        "point_f1": bool(np.isclose(result["point_f1"]["f1"], 1.0)),
        "point_f1_pa": bool(np.isclose(result["point_f1_pa"]["f1"], 1.0)),
        "event_f1_pa": bool(np.isclose(result["event_f1_pa"]["f1"], 1.0)),
        "event_threshold": bool(np.isclose(result["event_f1_pa"]["threshold"], 1.0)),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "fixture_id": "task034_metric_fidelity_single_event_v1",
        "checks": checks,
        "expected_values_frozen": True,
        "source_commit": SOURCE_COMMIT,
        "source_blobs": dict(SOURCE_BLOBS),
    }
