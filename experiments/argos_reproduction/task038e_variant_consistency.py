"""Describe alpha/beta direction consistency without detector selection."""

from __future__ import annotations

from typing import Any, Mapping

from experiments.argos_reproduction.task038e_bootstrap import COMPARISONS, FIELDS


def direction_label(alpha: float, beta: float, *, tolerance: float = 0.0) -> str:
    def sign(value: float) -> int:
        if value > tolerance:
            return 1
        if value < -tolerance:
            return -1
        return 0

    pair = (sign(alpha), sign(beta))
    if pair == (1, 1):
        return "same_positive"
    if pair == (-1, -1):
        return "same_negative"
    if pair == (0, 0):
        return "both_zero"
    return "mixed"


def build_variant_consistency(
    macro: Mapping[str, Mapping[str, Mapping[str, float]]],
    per_kpi: Mapping[str, Mapping[str, Mapping[str, Mapping[str, float]]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for left, right in COMPARISONS:
        for field in FIELDS:
            alpha = float(macro["LSTMADalpha"][left][field]) - float(
                macro["LSTMADalpha"][right][field]
            )
            beta = float(macro["LSTMADbeta"][left][field]) - float(
                macro["LSTMADbeta"][right][field]
            )
            kpis = sorted(per_kpi["LSTMADalpha"])
            kpi_consistency = {
                kpi: direction_label(
                    float(per_kpi["LSTMADalpha"][kpi][left][field])
                    - float(per_kpi["LSTMADalpha"][kpi][right][field]),
                    float(per_kpi["LSTMADbeta"][kpi][left][field])
                    - float(per_kpi["LSTMADbeta"][kpi][right][field]),
                )
                for kpi in kpis
            }
            records.append(
                {
                    "comparison": f"{left}_minus_{right}",
                    "endpoint": field,
                    "alpha_delta": alpha,
                    "beta_delta": beta,
                    "direction_consistency": direction_label(alpha, beta),
                    "kpi_level_sign_consistency": kpi_consistency,
                }
            )
    return records
