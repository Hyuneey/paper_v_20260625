from __future__ import annotations

from experiments.argos_reproduction.diagnostic_binary_fusion import (
    FUSION_OPERATORS,
    RULE_ARMS,
)
from experiments.argos_reproduction.fusion_variant_consistency import (
    build_variant_consistency,
    direction_classification,
)


def test_direction_classification() -> None:
    assert direction_classification(1.0, 2.0) == "same_positive"
    assert direction_classification(-1.0, -2.0) == "same_negative"
    assert direction_classification(0.0, 0.0) == "both_zero"
    assert direction_classification(1.0, -1.0) == "mixed"


def test_consistency_reports_every_rule_operator_without_selection() -> None:
    kpis = ("K1", "K2")
    detectors = {
        variant: {kpi: {"recall": 0.5} for kpi in kpis}
        for variant in ("LSTMADalpha", "LSTMADbeta")
    }
    fusion = {}
    for variant in detectors:
        for arm in RULE_ARMS:
            for operator in FUSION_OPERATORS:
                fusion[(variant, arm, operator)] = {
                    kpi: {"recall": 0.6 if operator == "fn_union_max" else 0.4}
                    for kpi in kpis
                }
    records = build_variant_consistency(
        fusion, detectors, kpi_ids=kpis, metric_fields=("recall",)
    )
    assert len(records) == 8
    assert {row["direction_consistency"] for row in records} == {
        "same_positive",
        "same_negative",
    }
