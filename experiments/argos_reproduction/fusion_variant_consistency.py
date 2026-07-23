"""Non-selective alpha/beta directional consistency diagnostics."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.diagnostic_binary_fusion import (
    FUSION_OPERATORS,
    RULE_ARMS,
)


def direction_classification(alpha_delta: float, beta_delta: float) -> str:
    if alpha_delta > 0 and beta_delta > 0:
        return "same_positive"
    if alpha_delta < 0 and beta_delta < 0:
        return "same_negative"
    if alpha_delta == 0 and beta_delta == 0:
        return "both_zero"
    return "mixed"


def build_variant_consistency(
    fusion_metrics: Mapping[tuple[str, str, str], Mapping[str, Mapping[str, float]]],
    detector_metrics: Mapping[str, Mapping[str, Mapping[str, float]]],
    *,
    kpi_ids: Sequence[str],
    metric_fields: Sequence[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for rule_arm in RULE_ARMS:
        for operator in FUSION_OPERATORS:
            for metric in metric_fields:
                alpha_deltas = [
                    float(
                        fusion_metrics[("LSTMADalpha", rule_arm, operator)][kpi][metric]
                        - detector_metrics["LSTMADalpha"][kpi][metric]
                    )
                    for kpi in kpi_ids
                ]
                beta_deltas = [
                    float(
                        fusion_metrics[("LSTMADbeta", rule_arm, operator)][kpi][metric]
                        - detector_metrics["LSTMADbeta"][kpi][metric]
                    )
                    for kpi in kpi_ids
                ]
                per_kpi = [
                    {
                        "kpi_id": kpi,
                        "alpha_delta": alpha,
                        "beta_delta": beta,
                        "direction_consistency": direction_classification(alpha, beta),
                    }
                    for kpi, alpha, beta in zip(kpi_ids, alpha_deltas, beta_deltas)
                ]
                counts = {
                    label: sum(item["direction_consistency"] == label for item in per_kpi)
                    for label in ("same_positive", "same_negative", "mixed", "both_zero")
                }
                alpha_macro = float(np.mean(alpha_deltas))
                beta_macro = float(np.mean(beta_deltas))
                records.append(
                    {
                        "rule_arm": rule_arm,
                        "operator": operator,
                        "metric": metric,
                        "alpha_delta_vs_alpha_detector": alpha_macro,
                        "beta_delta_vs_beta_detector": beta_macro,
                        "direction_consistency": direction_classification(
                            alpha_macro, beta_macro
                        ),
                        "kpi_sign_consistency_counts": counts,
                        "per_kpi": per_kpi,
                    }
                )
    return records
