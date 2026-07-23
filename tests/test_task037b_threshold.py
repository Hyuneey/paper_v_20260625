import numpy as np

from experiments.argos_reproduction.lstm_detector_threshold import (
    binary_predictions,
    select_inner_threshold,
    threshold_protocol_hash,
)


def test_threshold_uses_inner_direct_outputs_and_highest_threshold_tie():
    scores = np.array([0.0, 1.0, 2.0, 3.0])
    labels = np.array([0, 0, 1, 1])
    result = select_inner_threshold(scores, labels)
    assert result["selected_threshold"] == 2.0
    assert result["selected_f1"] == 1.0
    assert result["threshold_protocol_hash"] == threshold_protocol_hash()
    assert binary_predictions(scores, 2.0).tolist() == [0, 0, 1, 1]


def test_threshold_selection_is_deterministic():
    first = select_inner_threshold([0.0, 1.0, 1.0], [0, 1, 0])
    second = select_inner_threshold([0.0, 1.0, 1.0], [0, 1, 0])
    assert first == second


def test_cumulative_threshold_search_matches_brute_force_point_f1():
    scores = np.array([0.2, 0.8, 0.2, 0.5, 0.9, 0.5])
    labels = np.array([0, 1, 1, 0, 1, 0])
    selected = select_inner_threshold(scores, labels)
    brute = []
    for threshold in np.unique(scores):
        prediction = binary_predictions(scores, float(threshold))
        tp = int(np.sum((labels == 1) & (prediction == 1)))
        fp = int(np.sum((labels == 0) & (prediction == 1)))
        fn = int(np.sum((labels == 1) & (prediction == 0)))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        brute.append((f1, float(threshold)))
    assert selected["selected_threshold"] == max(brute)[1]
