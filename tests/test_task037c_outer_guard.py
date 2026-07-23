from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from experiments.argos_reproduction.expanded_kpi_cohort import sha256_json
from experiments.argos_reproduction.frozen_prediction_loader import (
    FrozenPredictionInputs,
)
from experiments.argos_reproduction.fusion_outer_validation import (
    FusionOuterValidationError,
    _load_labels_after_complete_freeze,
)


def _inputs() -> FrozenPredictionInputs:
    detector = {("outer", "LSTMADalpha", "K1"): np.array([0, 1], dtype=np.int8)}
    detector[("outer", "LSTMADbeta", "K1")] = np.array([0, 1], dtype=np.int8)
    return FrozenPredictionInputs(
        kpi_ids=("K1",),
        split_hashes={"K1": "h"},
        detector_predictions=detector,
        rule_predictions={},
        detector_hashes={},
        rule_hashes={},
        source_records=(),
        inner_rule_recovery={},
    )


def test_outer_labels_fail_before_complete_prediction_freeze(tmp_path: Path) -> None:
    root = tmp_path / "task035b"
    label_path = root / "outer/per_kpi_labels/K1.npy"
    label_path.parent.mkdir(parents=True)
    np.save(label_path, np.array([0, 1], dtype=np.int8), allow_pickle=False)
    freeze = {
        "record_count": 319,
        "all_predictions_frozen_before_labels": True,
    }
    freeze["freeze_hash"] = sha256_json(freeze)
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
    config = {"sources": {"task035b_private_root": str(root)}}
    with pytest.raises(FusionOuterValidationError, match="LABEL_ACCESS_BEFORE_FREEZE"):
        _load_labels_after_complete_freeze(config, _inputs(), freeze_path, "outer")


def test_runner_source_freezes_predictions_before_loading_labels() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "experiments/argos_reproduction/fusion_outer_validation.py"
    ).read_text(encoding="utf-8")
    freeze_position = source.index("_materialize_prediction_freeze(")
    label_position = source.index("_load_labels_after_complete_freeze(")
    assert freeze_position < label_position
