from pathlib import Path

import pytest

from experiments.argos_reproduction.lstm_detector_outer_validation import (
    average_precision,
    detector_metrics,
    roc_auc,
)


ROOT = Path(__file__).resolve().parents[1]


def test_auc_and_auprc_use_frozen_scores_without_threshold_search():
    labels = [0, 0, 1, 1]
    scores = [0.1, 0.2, 0.8, 0.9]
    assert roc_auc(labels, scores) == 1.0
    assert average_precision(labels, scores) == 1.0
    metrics = detector_metrics(labels, [0, 0, 1, 1], scores)
    assert metrics["score_threshold_optimized_on_outer"] is False


def test_values_only_container_wrapper_has_no_label_mount():
    source = (ROOT / "experiments/argos_reproduction/lstm_detector_scoring.py").read_text()
    assert "labels.npy" not in source
    assert "TestLabels" not in source
    assert "labels_mounted\": False" in source
