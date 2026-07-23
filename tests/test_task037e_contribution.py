from __future__ import annotations

import numpy as np

from experiments.argos_reproduction.aggregator_contribution_accounting import (
    fn_direction_contribution,
    fp_direction_contribution,
    full_aggregator_contribution,
)


def test_fn_and_fp_costs_are_counted_together() -> None:
    truth = np.array([1, 0, 1, 0], dtype=np.int8)
    detector = np.array([0, 0, 1, 1], dtype=np.int8)
    fn_combined = np.array([1, 1, 1, 1], dtype=np.int8)
    fp_combined = np.array([0, 0, 0, 0], dtype=np.int8)
    fn = fn_direction_contribution(truth, detector, fn_combined)
    fp = fp_direction_contribution(truth, detector, fp_combined)
    assert fn["FN_points_recovered"] == 1
    assert fn["added_false_positive_points"] == 1
    assert fp["FP_points_removed"] == 1
    assert fp["true_positive_points_removed"] == 1


def test_full_accounting_records_fp_changes_overridden_by_fn() -> None:
    truth = np.array([1, 0], dtype=np.int8)
    detector = np.array([1, 1], dtype=np.int8)
    after_fp = np.array([0, 0], dtype=np.int8)
    full = np.array([1, 0], dtype=np.int8)
    record = full_aggregator_contribution(truth, detector, after_fp, full)
    assert record["FP_correction_changes_overridden_by_FN"] == 1
    assert record["FN_additions_after_FP_correction"] == 1
