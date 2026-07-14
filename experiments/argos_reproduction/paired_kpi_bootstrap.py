"""Deterministic paired KPI bootstrap for TASK-035B."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


def paired_percentile_bootstrap(
    left: Sequence[float],
    right: Sequence[float],
    *,
    seed: int = 20260715,
    resamples: int = 10000,
    confidence_level: float = 0.95,
) -> dict[str, Any]:
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    if a.ndim != 1 or b.ndim != 1 or a.shape != b.shape or len(a) == 0 or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("TASK035B_BOOTSTRAP_INPUT_INVALID")
    if resamples <= 0 or not 0 < confidence_level < 1:
        raise ValueError("TASK035B_BOOTSTRAP_POLICY_INVALID")
    differences = a - b
    generator = np.random.default_rng(seed)
    indices = generator.integers(0, len(differences), size=(resamples, len(differences)))
    sampled = np.mean(differences[indices], axis=1)
    alpha = (1.0 - confidence_level) / 2.0
    return {
        "observed_macro_difference": float(np.mean(differences)),
        "lower_95_percentile": float(np.quantile(sampled, alpha)),
        "upper_95_percentile": float(np.quantile(sampled, 1.0 - alpha)),
        "kpi_win_count": int(np.sum(differences > 0)),
        "kpi_tie_count": int(np.sum(differences == 0)),
        "kpi_loss_count": int(np.sum(differences < 0)),
        "bootstrap_seed": seed,
        "bootstrap_resamples": resamples,
        "confidence_level": confidence_level,
        "method": "percentile_paired_bootstrap",
    }


def bootstrap_comparisons(
    per_kpi: Mapping[str, Mapping[str, Mapping[str, float]]],
    comparisons: Sequence[tuple[str, str]],
    metrics: Sequence[str],
    *,
    seed: int = 20260715,
    resamples: int = 10000,
) -> dict[str, Any]:
    kpis = sorted(per_kpi)
    result: dict[str, Any] = {}
    for left, right in comparisons:
        key = f"{left}_minus_{right}"
        result[key] = {}
        for metric in metrics:
            result[key][metric] = paired_percentile_bootstrap(
                [float(per_kpi[kpi][left][metric]) for kpi in kpis],
                [float(per_kpi[kpi][right][metric]) for kpi in kpis],
                seed=seed,
                resamples=resamples,
            )
    return result
