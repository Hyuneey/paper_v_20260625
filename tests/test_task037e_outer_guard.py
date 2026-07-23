from __future__ import annotations

from pathlib import Path

import pytest

from experiments.argos_reproduction.aggregator_outer_validation import (
    AggregatorOuterValidationError,
    load_outer_labels_after_prediction_freeze,
)
from experiments.argos_reproduction.directional_rule_selection import (
    DirectionalSelectionError,
    _detector_prediction_path,
    _label_path,
)


def test_outer_labels_fail_closed_before_complete_prediction_freeze() -> None:
    config = {
        "expected_executable_rule_count": 83,
        "private_roots": {"task035b": "not-used"},
    }
    with pytest.raises(
        AggregatorOuterValidationError, match="TASK037E_OUTER_LABEL_GUARD_FAILED"
    ):
        load_outer_labels_after_prediction_freeze(
            config,
            {
                "status": "incomplete",
                "record_count": 19,
                "all_outer_aggregator_predictions_frozen_before_labels": False,
            },
        )


def test_outer_runtime_requires_committed_selection_and_forbids_substitution() -> None:
    source = Path(
        "experiments/argos_reproduction/selected_rule_outer_runtime.py"
    ).read_text(encoding="utf-8")
    assert "TASK037E_SELECTION_NOT_COMMITTED" in source
    assert '"selected_rule_substitution_performed": False' in source
    assert source.count("execute_full_window_rule(") == 2
    assert '"labels_mounted": False' in source


def test_test_artifact_paths_fail_closed() -> None:
    config = {"private_roots": {"task035b": "x", "task037b": "y"}}
    with pytest.raises(DirectionalSelectionError, match="LABEL_SPLIT_NOT_ALLOWED"):
        _label_path(config, "kpi", "test")
    with pytest.raises(DirectionalSelectionError, match="DETECTOR_SPLIT_NOT_ALLOWED"):
        _detector_prediction_path(config, "variant", "kpi", "test")
