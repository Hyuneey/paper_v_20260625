import numpy as np

from experiments.argos_reproduction.detector_error_support_audit import GenerationErrorCell
from experiments.argos_reproduction.error_conditioned_target_selection import (
    enumerate_distinct_targets,
)
from experiments.argos_reproduction.error_contrast_matching import (
    contrast_pool,
    match_contrast,
)


def _cell() -> GenerationErrorCell:
    values = np.sin(np.arange(5000) / 100)
    labels = np.zeros(5000, dtype=np.int8)
    predictions = np.zeros(5000, dtype=np.int8)
    labels[2000:2010] = 1
    labels[3000:3010] = 1
    predictions[3000:3010] = 1
    return GenerationErrorCell(
        "LSTMADalpha", "K1", "split", values, labels, predictions, "p", "t", "s",
        {"FN": ((2000, 2010),), "FP": (), "TP": ((3000, 3010),), "TN": ((0, 2000), (2010, 3000), (3010, 5000))},
    )


def test_fn_contrasts_are_pure_tn_and_matching_is_deterministic() -> None:
    cell = _cell()
    target = enumerate_distinct_targets(cell, "FN", 1000)[0]
    pool = contrast_pool(cell, "FN", 1000)
    assert pool
    assert all(np.all(cell.labels[item["start"]:item["end"]] == 0) for item in pool)
    assert match_contrast(target, pool)["hash"] == match_contrast(target, tuple(reversed(pool)))["hash"]


def test_fp_contrasts_contain_true_positive_support() -> None:
    cell = _cell()
    pool = contrast_pool(cell, "FP", 1000)
    assert len(pool) == 1
    item = pool[0]
    assert np.any(
        (cell.labels[item["start"]:item["end"]] == 1)
        & (cell.predictions[item["start"]:item["end"]] == 1)
    )
