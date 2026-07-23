"""Pure binary semantics for the TASK-037E paper-aligned Aggregator."""

from __future__ import annotations

from typing import Any

import numpy as np

from experiments.argos_reproduction.direct_event_metrics import binary_vector


class PaperAlignedAggregatorError(ValueError):
    """Raised when a binary input violates the frozen Aggregator contract."""


def fn_compensation(detector: object, fn_rule: object) -> np.ndarray:
    detector_vector = binary_vector(detector, "detector")
    rule_vector = binary_vector(fn_rule, "fn_rule")
    if detector_vector.shape != rule_vector.shape:
        raise PaperAlignedAggregatorError("TASK037E_FN_LENGTH_MISMATCH")
    return np.maximum(detector_vector, rule_vector).astype(np.int8, copy=False)


def fp_correction(detector: object, fp_rule: object) -> np.ndarray:
    detector_vector = binary_vector(detector, "detector")
    rule_vector = binary_vector(fp_rule, "fp_rule")
    if detector_vector.shape != rule_vector.shape:
        raise PaperAlignedAggregatorError("TASK037E_FP_LENGTH_MISMATCH")
    return np.minimum(detector_vector, rule_vector).astype(np.int8, copy=False)


def full_aggregator(
    detector: object,
    *,
    fp_rule: object | None,
    fn_rule: object | None,
) -> np.ndarray:
    detector_vector = binary_vector(detector, "detector")
    after_fp = (
        detector_vector.copy()
        if fp_rule is None
        else fp_correction(detector_vector, fp_rule)
    )
    return after_fp if fn_rule is None else fn_compensation(after_fp, fn_rule)


def frozen_aggregator_order() -> tuple[str, str]:
    return ("fp_correction", "fn_compensation")


def prediction_degeneracy(
    prediction: object,
    *,
    detector: object | None = None,
) -> dict[str, Any]:
    vector = binary_vector(prediction, "prediction")
    rate = float(np.mean(vector)) if len(vector) else 0.0
    return {
        "all_zero": bool(len(vector) == 0 or np.all(vector == 0)),
        "all_one": bool(len(vector) > 0 and np.all(vector == 1)),
        "near_all_positive": rate >= 0.95,
        "identical_to_detector": (
            False
            if detector is None
            else bool(np.array_equal(vector, binary_vector(detector, "detector")))
        ),
        "predicted_positive_rate": rate,
    }
