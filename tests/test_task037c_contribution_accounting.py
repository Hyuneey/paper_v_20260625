from __future__ import annotations

from experiments.argos_reproduction.diagnostic_binary_fusion import fuse_binary
from experiments.argos_reproduction.fusion_contribution_accounting import (
    disagreement_accounting,
    fn_contribution,
    fp_contribution,
)


def test_disagreement_regions_and_fn_costs_are_reported_together() -> None:
    truth = [0, 1, 1, 0, 0, 1, 0, 0]
    detector = [0, 0, 1, 1, 0, 0, 0, 0]
    rule = [0, 1, 0, 1, 1, 0, 0, 0]
    fusion = fuse_binary(detector, rule, "fn_union_max")
    result = fn_contribution(truth, detector, rule, fusion)
    assert result["detector_fn_points_recovered"] == 1
    assert result["added_true_positives"] == 1
    assert result["added_false_positives"] == 1
    assert result["agreement_regions"]["d0_r1"]["point_count"] == 2
    assert result["recall_delta_vs_detector"] > 0


def test_fp_removal_reports_lost_true_positives() -> None:
    truth = [0, 1, 1, 0, 0, 1, 0, 0]
    detector = [0, 1, 1, 1, 1, 1, 0, 0]
    rule = [0, 1, 0, 0, 1, 0, 0, 0]
    fusion = fuse_binary(detector, rule, "fp_intersection_min")
    result = fp_contribution(truth, detector, rule, fusion)
    assert result["detector_fp_points_removed"] == 1
    assert result["removed_false_positives"] == 1
    assert result["removed_true_positives"] == 2
    assert result["recall_delta_vs_detector"] < 0


def test_event_accounting_is_local_to_one_vector() -> None:
    result = disagreement_accounting(
        [1, 1, 0, 1, 1],
        [0, 0, 0, 0, 0],
        [1, 1, 0, 1, 1],
    )
    assert result["rule_additions"]["added_anomaly_events"] == 2
