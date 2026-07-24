"""Binary branch composition and private TASK-038E prediction paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np

from experiments.argos_reproduction.direct_event_metrics import binary_vector
from experiments.argos_reproduction.review_parent_registry import ROOT


ARMS = (
    "detector_only",
    "detector_plus_FN",
    "detector_plus_FP",
    "full_aggregator",
)


def compose_direction(
    detector: object, rule: object, direction: str
) -> np.ndarray:
    d = binary_vector(detector, "detector")
    r = binary_vector(rule, "rule")
    if d.shape != r.shape:
        raise ValueError("TASK038E_DIRECTION_LENGTH_MISMATCH")
    if direction == "FN":
        return np.maximum(d, r).astype(np.int8)
    if direction == "FP":
        return np.minimum(d, r).astype(np.int8)
    raise ValueError("TASK038E_DIRECTION_INVALID")


def compose_branch_arms(
    detector: object,
    fn_rule: object | None,
    fp_rule: object | None,
) -> dict[str, np.ndarray]:
    d = binary_vector(detector, "detector")
    fn = np.zeros_like(d) if fn_rule is None else binary_vector(fn_rule, "fn_rule")
    fp = np.ones_like(d) if fp_rule is None else binary_vector(fp_rule, "fp_rule")
    if d.shape != fn.shape or d.shape != fp.shape:
        raise ValueError("TASK038E_AGGREGATOR_LENGTH_MISMATCH")
    after_fp = np.minimum(d, fp)
    return {
        "detector_only": d.copy(),
        "detector_plus_FN": np.maximum(d, fn).astype(np.int8),
        "detector_plus_FP": after_fp.astype(np.int8),
        "full_aggregator": np.maximum(after_fp, fn).astype(np.int8),
    }


def detector_prediction_path(
    config: Mapping[str, Any], variant: str, kpi_id: str
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task037b"])
        / "detectors"
        / variant
        / kpi_id
        / "20260723"
        / "predictions"
        / "outer_prediction.npy"
    )


def outer_values_path(config: Mapping[str, Any], kpi_id: str) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task035b"])
        / "outer"
        / "per_kpi_values"
        / f"{kpi_id}.npy"
    )


def outer_labels_path(config: Mapping[str, Any], kpi_id: str) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task035b"])
        / "outer"
        / "per_kpi_labels"
        / f"{kpi_id}.npy"
    )


def branch_arm_path(
    config: Mapping[str, Any],
    branch: str,
    variant: str,
    kpi_id: str,
    arm: str,
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task038e"])
        / "branch_arm_predictions"
        / branch
        / variant
        / kpi_id
        / f"{arm}.npy"
    )


def review_combined_path(
    config: Mapping[str, Any], logical_id: str, role: str
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task038e"])
        / "review_parent_predictions"
        / logical_id
        / f"{role}_combined.npy"
    )


def repair_combined_path(
    config: Mapping[str, Any], logical_id: str
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task038e"])
        / "repair_predictions"
        / logical_id
        / "combined.npy"
    )
