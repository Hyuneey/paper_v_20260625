"""Prediction diversity diagnostics for a frozen TASK-035B panel."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.direct_event_metrics import binary_vector, contiguous_events, intervals_overlap, metric_distribution


def prediction_jaccard(left: object, right: object) -> float:
    a = binary_vector(left, "jaccard_left")
    b = binary_vector(right, "jaccard_right")
    if a.shape != b.shape:
        raise ValueError("TASK035B_JACCARD_LENGTH_MISMATCH")
    union = int(np.sum((a == 1) | (b == 1)))
    return float(np.sum((a == 1) & (b == 1)) / union) if union else 1.0


def _summary(values: Sequence[float]) -> dict[str, float | None]:
    if not values:
        return {"median": None, "interquartile_range": None, "minimum": None, "maximum": None}
    return metric_distribution([{"value": value} for value in values], "value")


def diversity_diagnostics(
    records: Sequence[Mapping[str, Any]],
    predictions: Mapping[str, np.ndarray],
    ground_truth: object,
) -> dict[str, Any]:
    truth = binary_vector(ground_truth, "diversity_truth")
    ordered = sorted((dict(record) for record in records), key=lambda item: item["rule_sha256"])
    pair_values: list[float] = []
    same_anchor: list[float] = []
    different_anchor: list[float] = []
    for left, right in combinations(ordered, 2):
        value = prediction_jaccard(predictions[left["rule_sha256"]], predictions[right["rule_sha256"]])
        pair_values.append(value)
        (same_anchor if left["anchor_id"] == right["anchor_id"] else different_anchor).append(value)
    matrix = np.stack([binary_vector(predictions[item["rule_sha256"]], "diversity_prediction") for item in ordered])
    point_coverage = np.sum(matrix, axis=0)
    truth_events = contiguous_events(truth)
    unique_points: dict[str, int] = {}
    unique_events: dict[str, int] = {}
    for row_index, item in enumerate(ordered):
        vector = matrix[row_index]
        unique_points[item["rule_sha256"]] = int(np.sum((truth == 1) & (vector == 1) & (point_coverage == 1)))
        detected_by_rule = []
        rule_events = contiguous_events(vector)
        for truth_event in truth_events:
            detected_by_rule.append(any(intervals_overlap(event, truth_event) for event in rule_events))
        unique_events[item["rule_sha256"]] = sum(
            detected and sum(
                any(intervals_overlap(event, truth_event) for event in contiguous_events(matrix[other_index]))
                for other_index in range(len(ordered))
            ) == 1
            for truth_event, detected in zip(truth_events, detected_by_rule)
        )
    return {
        "pairwise_prediction_jaccard": _summary(pair_values),
        "same_anchor_pair_jaccard": _summary(same_anchor),
        "different_anchor_pair_jaccard": _summary(different_anchor),
        "unique_true_positive_points_per_rule": unique_points,
        "unique_ground_truth_events_per_rule": unique_events,
    }
