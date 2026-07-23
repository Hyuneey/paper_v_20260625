"""Co-primary alpha/beta direction consistency for TASK-037E."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.fusion_variant_consistency import (
    direction_classification,
)


def build_aggregator_variant_consistency(
    metrics: Mapping[str, Mapping[str, Mapping[str, float]]],
    *,
    kpi_ids: Sequence[str],
    arms: Sequence[str],
    metric_fields: Sequence[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for arm in arms:
        for field in metric_fields:
            alpha = [
                float(metrics["LSTMADalpha"][kpi][arm][field])
                - float(metrics["LSTMADalpha"][kpi]["detector_only"][field])
                for kpi in kpi_ids
            ]
            beta = [
                float(metrics["LSTMADbeta"][kpi][arm][field])
                - float(metrics["LSTMADbeta"][kpi]["detector_only"][field])
                for kpi in kpi_ids
            ]
            per_kpi = [
                {
                    "kpi_id": kpi,
                    "alpha_delta": a,
                    "beta_delta": b,
                    "direction_consistency": direction_classification(a, b),
                }
                for kpi, a, b in zip(kpi_ids, alpha, beta)
            ]
            records.append(
                {
                    "arm": arm,
                    "metric": field,
                    "alpha_delta_vs_alpha_detector": float(np.mean(alpha)),
                    "beta_delta_vs_beta_detector": float(np.mean(beta)),
                    "direction_consistency": direction_classification(
                        float(np.mean(alpha)), float(np.mean(beta))
                    ),
                    "kpi_sign_consistency_counts": {
                        value: sum(
                            item["direction_consistency"] == value for item in per_kpi
                        )
                        for value in ("same_positive", "same_negative", "mixed", "both_zero")
                    },
                    "per_kpi": per_kpi,
                }
            )
    return records
