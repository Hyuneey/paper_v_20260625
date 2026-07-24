import numpy as np

from experiments.argos_reproduction.task038e_branch_aggregator import (
    compose_branch_arms,
    compose_direction,
)


def test_fn_max_and_fp_min_truth_tables() -> None:
    d = np.array([0, 0, 1, 1])
    r = np.array([0, 1, 0, 1])
    assert compose_direction(d, r, "FN").tolist() == [0, 1, 1, 1]
    assert compose_direction(d, r, "FP").tolist() == [0, 0, 0, 1]


def test_full_aggregator_applies_fp_before_fn() -> None:
    arms = compose_branch_arms(
        np.array([1, 1, 0]), np.array([1, 0, 1]), np.array([0, 1, 1])
    )
    assert arms["detector_plus_FP"].tolist() == [0, 1, 0]
    assert arms["full_aggregator"].tolist() == [1, 1, 1]
