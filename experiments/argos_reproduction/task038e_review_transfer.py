"""Review parent-versus-revision transfer classifications."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


def transfer_classification(inner_delta: float, outer_delta: float) -> str:
    if inner_delta > 0 and outer_delta > 0:
        return "positive_transfer"
    if inner_delta > 0 and outer_delta == 0:
        return "no_transfer"
    if inner_delta > 0 and outer_delta < 0:
        return "negative_transfer"
    if inner_delta < 0 and outer_delta > 0:
        return "inner_regression_outer_recovery"
    if inner_delta == 0 and outer_delta == 0:
        return "same"
    return "other_mixed_transfer"


def review_summary(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(records)
    inner = np.asarray([float(row["inner_F1_delta"]) for row in records])
    outer = np.asarray([float(row["outer_F1_delta"]) for row in records])
    correlation = (
        float(np.corrcoef(inner, outer)[0, 1])
        if total > 1 and np.std(inner) > 0 and np.std(outer) > 0
        else 0.0
    )
    count = lambda name: sum(
        row["transfer_classification"] == name for row in records
    )
    return {
        "reviewed_executable_count": total,
        "positive_transfer_count": count("positive_transfer"),
        "no_transfer_count": count("no_transfer"),
        "negative_transfer_count": count("negative_transfer"),
        "inner_regression_outer_recovery_count": count(
            "inner_regression_outer_recovery"
        ),
        "positive_transfer_rate": count("positive_transfer") / total if total else 0.0,
        "negative_transfer_rate": count("negative_transfer") / total if total else 0.0,
        "mean_inner_F1_delta": float(np.mean(inner)) if total else 0.0,
        "mean_outer_F1_delta": float(np.mean(outer)) if total else 0.0,
        "median_inner_F1_delta": float(np.median(inner)) if total else 0.0,
        "median_outer_F1_delta": float(np.median(outer)) if total else 0.0,
        "inner_outer_delta_correlation": correlation,
    }
