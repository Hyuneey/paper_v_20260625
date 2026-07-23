"""Exact binary max/min fusion primitives for TASK-037C."""

from __future__ import annotations

from typing import Any

import numpy as np


DETECTOR_VARIANTS = ("LSTMADalpha", "LSTMADbeta")
RULE_ARMS = ("best_1", "top_3_or", "coverage_3_or", "all_10_or")
FUSION_OPERATORS = ("fn_union_max", "fp_intersection_min")


class DiagnosticFusionError(ValueError):
    """Raised when a frozen binary fusion contract is violated."""


def binary_vector(value: object, name: str = "prediction") -> np.ndarray:
    array = np.asarray(value)
    if (
        array.ndim != 1
        or not np.all(np.isfinite(array))
        or not np.all(np.isin(array, (0, 1)))
    ):
        raise DiagnosticFusionError(f"TASK037C_{name.upper()}_BINARY_INVALID")
    return array.astype(np.int8, copy=True)


def fuse_binary(detector: object, rule: object, operator: str) -> np.ndarray:
    detector_vector = binary_vector(detector, "detector")
    rule_vector = binary_vector(rule, "rule")
    if detector_vector.shape != rule_vector.shape:
        raise DiagnosticFusionError("TASK037C_FUSION_LENGTH_MISMATCH")
    if operator == "fn_union_max":
        return np.maximum(detector_vector, rule_vector).astype(np.int8, copy=False)
    if operator == "fp_intersection_min":
        return np.minimum(detector_vector, rule_vector).astype(np.int8, copy=False)
    raise DiagnosticFusionError("TASK037C_OPERATOR_UNSUPPORTED")


def frozen_fusion_arm_ids() -> tuple[str, ...]:
    return tuple(
        f"{variant}__{rule_arm}__{operator}"
        for variant in DETECTOR_VARIANTS
        for rule_arm in RULE_ARMS
        for operator in FUSION_OPERATORS
    )


def degeneracy_flags(
    fusion: object,
    detector: object,
    rule: object,
    *,
    near_all_positive_rate: float = 0.95,
) -> dict[str, Any]:
    fused = binary_vector(fusion, "fusion")
    detector_vector = binary_vector(detector, "detector")
    rule_vector = binary_vector(rule, "rule")
    if fused.shape != detector_vector.shape or fused.shape != rule_vector.shape:
        raise DiagnosticFusionError("TASK037C_DEGENERACY_LENGTH_MISMATCH")
    positive_rate = float(np.mean(fused)) if len(fused) else 0.0
    return {
        "all_zero": bool(np.all(fused == 0)),
        "all_one": bool(len(fused) > 0 and np.all(fused == 1)),
        "near_all_positive": bool(positive_rate >= near_all_positive_rate),
        "identical_to_detector": bool(np.array_equal(fused, detector_vector)),
        "identical_to_rule": bool(np.array_equal(fused, rule_vector)),
        "predicted_positive_rate": positive_rate,
    }
