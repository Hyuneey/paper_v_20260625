import numpy as np

from experiments.argos_reproduction.detector_error_support_audit import GenerationErrorCell
from experiments.argos_reproduction.error_conditioned_target_selection import (
    enumerate_distinct_targets,
    evenly_distributed_targets,
)


def _cell() -> GenerationErrorCell:
    values = np.linspace(0.0, 1.0, 5000)
    labels = np.zeros(5000, dtype=np.int8)
    predictions = np.zeros(5000, dtype=np.int8)
    labels[[1000, 2500, 4000]] = 1
    return GenerationErrorCell(
        "LSTMADalpha",
        "K1",
        "split",
        values,
        labels,
        predictions,
        "prediction",
        "threshold",
        "segments",
        {"FN": ((1000, 1001), (2500, 2501), (4000, 4001)), "FP": (), "TP": (), "TN": ((0, 5000),)},
    )


def test_fn_targets_are_distinct_deterministic_and_intersect_errors() -> None:
    candidates = enumerate_distinct_targets(_cell(), "FN", 1000)
    selected = evenly_distributed_targets(candidates, 3)
    assert len(selected) == 3
    assert len({item["hash"] for item in selected}) == 3
    assert [item["hash"] for item in selected] == [
        item["hash"] for item in evenly_distributed_targets(candidates, 3)
    ]
    assert all(np.any(item["labels"] == 1) for item in selected)


def test_fp_target_rejects_chunk_containing_anomaly() -> None:
    cell = _cell()
    labels = cell.labels.copy()
    labels[1700] = 1
    predictions = cell.predictions.copy()
    predictions[1600] = 1
    fp = GenerationErrorCell(
        cell.variant,
        cell.kpi_id,
        cell.split_manifest_hash,
        cell.values,
        labels,
        predictions,
        cell.prediction_hash,
        cell.threshold_hash,
        cell.segment_manifest_hash,
        {**cell.segments, "FP": ((1600, 1601),)},
    )
    assert enumerate_distinct_targets(fp, "FP", 1000) == ()
