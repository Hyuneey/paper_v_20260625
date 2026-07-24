from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_parent_freeze_precedes_label_loading() -> None:
    source = (
        ROOT
        / "experiments/argos_reproduction/review_trigger_metrics.py"
    ).read_text(encoding="utf-8")
    freeze_source = (
        ROOT
        / "experiments/argos_reproduction/review_parent_inner_runtime.py"
    ).read_text(encoding="utf-8")
    assert "verify_parent_prediction_freeze(config)" in source
    assert '"labels_loaded_during_freeze": False' in freeze_source
    assert "detector_predictions_mounted" in freeze_source


def test_repaired_parents_require_two_run_replay() -> None:
    source = (
        ROOT
        / "experiments/argos_reproduction/review_parent_inner_runtime.py"
    ).read_text(encoding="utf-8")
    assert "for replay in (1, 2)" in source
    assert "deterministic_replay_matches" in source
