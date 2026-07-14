"""Direct PA-free point and one-to-one event metrics for TASK-035B."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


class DirectMetricError(ValueError):
    pass


def binary_vector(value: object, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 1 or not np.all(np.isfinite(array)) or not np.all(np.isin(array, (0, 1))):
        raise DirectMetricError(f"TASK035B_{name.upper()}_BINARY_VECTOR_INVALID")
    return array.astype(np.int8, copy=True)


def contiguous_events(labels: object) -> list[tuple[int, int]]:
    vector = binary_vector(labels, "event_labels")
    events: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(vector.tolist()):
        if value == 1 and start is None:
            start = index
        elif value == 0 and start is not None:
            events.append((start, index))
            start = None
    if start is not None:
        events.append((start, len(vector)))
    return events


def intervals_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return max(left[0], right[0]) < min(left[1], right[1])


def maximum_overlap_matching(
    predicted_events: Sequence[tuple[int, int]],
    ground_truth_events: Sequence[tuple[int, int]],
) -> list[tuple[int, int]]:
    adjacency = [
        [truth_index for truth_index, truth in enumerate(ground_truth_events) if intervals_overlap(prediction, truth)]
        for prediction in predicted_events
    ]
    truth_to_prediction: dict[int, int] = {}

    def augment(prediction_index: int, seen: set[int]) -> bool:
        for truth_index in adjacency[prediction_index]:
            if truth_index in seen:
                continue
            seen.add(truth_index)
            if truth_index not in truth_to_prediction or augment(truth_to_prediction[truth_index], seen):
                truth_to_prediction[truth_index] = prediction_index
                return True
        return False

    for prediction_index in range(len(predicted_events)):
        augment(prediction_index, set())
    return sorted((prediction_index, truth_index) for truth_index, prediction_index in truth_to_prediction.items())


def direct_pa_free_metrics(ground_truth: object, prediction: object) -> dict[str, Any]:
    truth = binary_vector(ground_truth, "ground_truth")
    predicted = binary_vector(prediction, "prediction")
    if truth.shape != predicted.shape:
        raise DirectMetricError("TASK035B_METRIC_LENGTH_MISMATCH")
    tp = int(np.sum((truth == 1) & (predicted == 1)))
    fp = int(np.sum((truth == 0) & (predicted == 1)))
    tn = int(np.sum((truth == 0) & (predicted == 0)))
    fn = int(np.sum((truth == 1) & (predicted == 0)))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    point_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    truth_events = contiguous_events(truth)
    prediction_events = contiguous_events(predicted)
    matching = maximum_overlap_matching(prediction_events, truth_events)
    event_tp = len(matching)
    event_fp = len(prediction_events) - event_tp
    event_fn = len(truth_events) - event_tp
    event_precision = event_tp / (event_tp + event_fp) if event_tp + event_fp else 0.0
    event_recall = event_tp / (event_tp + event_fn) if event_tp + event_fn else 0.0
    event_f1 = 2 * event_precision * event_recall / (event_precision + event_recall) if event_precision + event_recall else 0.0
    normal_points = tn + fp
    predicted_positive_count = int(np.sum(predicted))
    return {
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": precision,
        "recall": recall,
        "point_f1": point_f1,
        "predicted_positive_count": predicted_positive_count,
        "predicted_positive_rate": predicted_positive_count / len(predicted) if len(predicted) else 0.0,
        "false_positive_points_per_10000_normal_points": fp / normal_points * 10000 if normal_points else 0.0,
        "event_true_positive": event_tp,
        "event_false_positive": event_fp,
        "event_false_negative": event_fn,
        "event_precision": event_precision,
        "event_recall": event_recall,
        "event_f1": event_f1,
        "ground_truth_event_count": len(truth_events),
        "predicted_event_count": len(prediction_events),
        "matched_event_count": event_tp,
        "false_alarm_events_per_10000_points": event_fp / len(predicted) * 10000 if len(predicted) else 0.0,
        "point_adjustment": False,
        "threshold_optimization": False,
    }


def compose_or(predictions: Sequence[object]) -> np.ndarray:
    if not predictions:
        raise DirectMetricError("TASK035B_OR_REQUIRES_PREDICTION")
    vectors = [binary_vector(value, "composition") for value in predictions]
    if len({vector.shape for vector in vectors}) != 1:
        raise DirectMetricError("TASK035B_OR_LENGTH_MISMATCH")
    return np.maximum.reduce(vectors).astype(np.int8, copy=False)


def metric_distribution(records: Sequence[Mapping[str, Any]], field: str) -> dict[str, float]:
    values = np.asarray([float(record[field]) for record in records], dtype=np.float64)
    if len(values) == 0:
        raise DirectMetricError("TASK035B_DISTRIBUTION_EMPTY")
    return {
        "median": float(np.median(values)),
        "interquartile_range": float(np.percentile(values, 75) - np.percentile(values, 25)),
        "minimum": float(np.min(values)),
        "maximum": float(np.max(values)),
    }
