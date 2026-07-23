from __future__ import annotations

import numpy as np
import pytest

from experiments.argos_reproduction.diagnostic_binary_fusion import (
    DiagnosticFusionError,
    frozen_fusion_arm_ids,
    fuse_binary,
)


def test_complete_frozen_matrix_has_exactly_sixteen_arms() -> None:
    arms = frozen_fusion_arm_ids()
    assert len(arms) == 16
    assert len(set(arms)) == 16


def test_fn_union_max_truth_table() -> None:
    detector = np.array([0, 0, 1, 1], dtype=np.int8)
    rule = np.array([0, 1, 0, 1], dtype=np.int8)
    assert fuse_binary(detector, rule, "fn_union_max").tolist() == [0, 1, 1, 1]


def test_fp_intersection_min_truth_table() -> None:
    detector = np.array([0, 0, 1, 1], dtype=np.int8)
    rule = np.array([0, 1, 0, 1], dtype=np.int8)
    assert fuse_binary(detector, rule, "fp_intersection_min").tolist() == [0, 0, 0, 1]


def test_fusion_rejects_nonbinary_and_length_mismatch() -> None:
    with pytest.raises(DiagnosticFusionError, match="BINARY_INVALID"):
        fuse_binary([0, 2], [0, 1], "fn_union_max")
    with pytest.raises(DiagnosticFusionError, match="LENGTH_MISMATCH"):
        fuse_binary([0], [0, 1], "fp_intersection_min")
