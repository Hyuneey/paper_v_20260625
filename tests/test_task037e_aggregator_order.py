from __future__ import annotations

import numpy as np

from experiments.argos_reproduction.paper_aligned_aggregator import (
    fn_compensation,
    fp_correction,
    frozen_aggregator_order,
    full_aggregator,
)


def test_directional_binary_truth_tables() -> None:
    detector = np.array([0, 0, 1, 1], dtype=np.int8)
    rule = np.array([0, 1, 0, 1], dtype=np.int8)
    assert fn_compensation(detector, rule).tolist() == [0, 1, 1, 1]
    assert fp_correction(detector, rule).tolist() == [0, 0, 0, 1]


def test_full_aggregator_applies_fp_then_fn() -> None:
    detector = np.array([1], dtype=np.int8)
    fp_rule = np.array([0], dtype=np.int8)
    fn_rule = np.array([1], dtype=np.int8)
    result = full_aggregator(detector, fp_rule=fp_rule, fn_rule=fn_rule)
    reversed_result = fp_correction(
        fn_compensation(detector, fn_rule), fp_rule
    )
    assert result.tolist() == [1]
    assert reversed_result.tolist() == [0]
    assert frozen_aggregator_order() == ("fp_correction", "fn_compensation")


def test_noop_directions_are_identity() -> None:
    detector = np.array([0, 1, 0], dtype=np.int8)
    assert np.array_equal(
        full_aggregator(detector, fp_rule=None, fn_rule=None), detector
    )
