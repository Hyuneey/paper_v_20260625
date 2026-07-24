"""Deterministic paired KPI bootstrap for TASK-038E branch comparisons."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from experiments.argos_reproduction.paired_kpi_bootstrap import (
    paired_percentile_bootstrap,
)


COMPARISONS = (
    ("A1", "A0"),
    ("A2", "A0"),
    ("A3", "A0"),
    ("A3", "A1"),
    ("A3", "A2"),
)

FIELDS = (
    "precision",
    "recall",
    "point_f1",
    "event_f1",
    "false_positive_points_per_10000_normal_points",
)


def branch_bootstrap(
    per_kpi: Mapping[str, Mapping[str, Mapping[str, float]]],
    *,
    seed: int = 20260726,
    resamples: int = 10000,
) -> dict[str, Any]:
    kpis = sorted(per_kpi)
    result: dict[str, Any] = {}
    for left, right in COMPARISONS:
        result[f"{left}_minus_{right}"] = {
            field: paired_percentile_bootstrap(
                [float(per_kpi[kpi][left][field]) for kpi in kpis],
                [float(per_kpi[kpi][right][field]) for kpi in kpis],
                seed=seed,
                resamples=resamples,
            )
            for field in FIELDS
        }
    return result
