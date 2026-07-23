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
