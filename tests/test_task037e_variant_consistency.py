from __future__ import annotations

from experiments.argos_reproduction.aggregator_variant_consistency import (
    build_aggregator_variant_consistency,
)


def test_variants_are_reported_without_winner_selection() -> None:
    metrics = {
        variant: {
            "kpi": {
                "detector_only": {"point_f1": 0.5},
                "full_aggregator": {"point_f1": value},
            }
        }
        for variant, value in (("LSTMADalpha", 0.6), ("LSTMADbeta", 0.4))
    }
    records = build_aggregator_variant_consistency(
        metrics,
        kpi_ids=["kpi"],
        arms=["full_aggregator"],
        metric_fields=["point_f1"],
    )
    assert records[0]["direction_consistency"] == "mixed"
    assert "winner" not in records[0]
