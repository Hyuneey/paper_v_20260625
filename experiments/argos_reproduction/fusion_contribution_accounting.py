"""Directional detector-rule contribution accounting for TASK-037C."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from experiments.argos_reproduction.diagnostic_binary_fusion import binary_vector
from experiments.argos_reproduction.direct_event_metrics import (
    contiguous_events,
    direct_pa_free_metrics,
    intervals_overlap,
)


class FusionContributionError(ValueError):
    """Raised when contribution inputs violate the frozen contract."""


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _truth_events_touched(mask: np.ndarray, truth: np.ndarray) -> int:
    mask_events = contiguous_events(mask)
    truth_events = contiguous_events(truth)
    return sum(
        any(intervals_overlap(mask_event, truth_event) for mask_event in mask_events)
        for truth_event in truth_events
    )


def disagreement_accounting(
    ground_truth: object,
    detector: object,
    rule: object,
) -> dict[str, Any]:
    truth = binary_vector(ground_truth, "ground_truth")
    detector_vector = binary_vector(detector, "detector")
    rule_vector = binary_vector(rule, "rule")
    if truth.shape != detector_vector.shape or truth.shape != rule_vector.shape:
        raise FusionContributionError("TASK037C_DISAGREEMENT_LENGTH_MISMATCH")

    regions = {
        "d0_r0": (detector_vector == 0) & (rule_vector == 0),
        "d0_r1": (detector_vector == 0) & (rule_vector == 1),
        "d1_r0": (detector_vector == 1) & (rule_vector == 0),
        "d1_r1": (detector_vector == 1) & (rule_vector == 1),
    }
    additions_tp = regions["d0_r1"] & (truth == 1)
    additions_fp = regions["d0_r1"] & (truth == 0)
    removals_fp = regions["d1_r0"] & (truth == 0)
    removals_tp = regions["d1_r0"] & (truth == 1)

    return {
        "agreement_regions": {
            name: {
                "point_count": int(np.sum(mask)),
                "ground_truth_positive_count": int(np.sum(mask & (truth == 1))),
                "ground_truth_negative_count": int(np.sum(mask & (truth == 0))),
            }
            for name, mask in regions.items()
        },
        "rule_additions": {
            "added_true_positives": int(np.sum(additions_tp)),
            "added_false_positives": int(np.sum(additions_fp)),
            "added_anomaly_events": _truth_events_touched(additions_tp, truth),
            "added_false_alarm_events": len(contiguous_events(additions_fp.astype(np.int8))),
        },
        "rule_removals": {
            "removed_false_positives": int(np.sum(removals_fp)),
            "removed_true_positives": int(np.sum(removals_tp)),
            "removed_false_alarm_events": len(contiguous_events(removals_fp.astype(np.int8))),
            "removed_true_anomaly_events": _truth_events_touched(removals_tp, truth),
        },
    }


def fn_contribution(
    ground_truth: object,
    detector: object,
    rule: object,
    fusion: object,
) -> dict[str, Any]:
    detector_metrics = direct_pa_free_metrics(ground_truth, detector)
    fusion_metrics = direct_pa_free_metrics(ground_truth, fusion)
    disagreement = disagreement_accounting(ground_truth, detector, rule)
    additions = disagreement["rule_additions"]
    fn_before = int(detector_metrics["false_negative"])
    fn_after = int(fusion_metrics["false_negative"])
    events_before = int(detector_metrics["event_false_negative"])
    events_after = int(fusion_metrics["event_false_negative"])
    return {
        **disagreement,
        "detector_false_negatives_before": fn_before,
        "detector_false_negatives_after": fn_after,
        "detector_fn_points_recovered": fn_before - fn_after,
        "detector_fn_recovery_rate": _safe_ratio(fn_before - fn_after, fn_before),
        "detector_missed_events_before": events_before,
        "detector_missed_events_after": events_after,
        "detector_events_recovered": events_before - events_after,
        "detector_event_recovery_rate": _safe_ratio(events_before - events_after, events_before),
        "added_true_positives": additions["added_true_positives"],
        "added_false_positives": additions["added_false_positives"],
        "added_tp_to_added_fp_ratio": _safe_ratio(
            additions["added_true_positives"], additions["added_false_positives"]
        ),
        **_metric_deltas(fusion_metrics, detector_metrics),
    }


def fp_contribution(
    ground_truth: object,
    detector: object,
    rule: object,
    fusion: object,
) -> dict[str, Any]:
    detector_metrics = direct_pa_free_metrics(ground_truth, detector)
    fusion_metrics = direct_pa_free_metrics(ground_truth, fusion)
    disagreement = disagreement_accounting(ground_truth, detector, rule)
    removals = disagreement["rule_removals"]
    fp_before = int(detector_metrics["false_positive"])
    fp_after = int(fusion_metrics["false_positive"])
    alarms_before = int(detector_metrics["event_false_positive"])
    alarms_after = int(fusion_metrics["event_false_positive"])
    return {
        **disagreement,
        "detector_false_positives_before": fp_before,
        "detector_false_positives_after": fp_after,
        "detector_fp_points_removed": fp_before - fp_after,
        "detector_fp_removal_rate": _safe_ratio(fp_before - fp_after, fp_before),
        "detector_false_alarm_events_before": alarms_before,
        "detector_false_alarm_events_after": alarms_after,
        "detector_false_alarm_events_removed": alarms_before - alarms_after,
        "removed_false_positives": removals["removed_false_positives"],
        "removed_true_positives": removals["removed_true_positives"],
        "removed_fp_to_removed_tp_ratio": _safe_ratio(
            removals["removed_false_positives"], removals["removed_true_positives"]
        ),
        **_metric_deltas(fusion_metrics, detector_metrics),
    }


def _metric_deltas(
    fusion_metrics: Mapping[str, Any],
    detector_metrics: Mapping[str, Any],
) -> dict[str, float]:
    return {
        "precision_delta_vs_detector": float(
            fusion_metrics["precision"] - detector_metrics["precision"]
        ),
        "recall_delta_vs_detector": float(
            fusion_metrics["recall"] - detector_metrics["recall"]
        ),
        "point_f1_delta_vs_detector": float(
            fusion_metrics["point_f1"] - detector_metrics["point_f1"]
        ),
        "event_f1_delta_vs_detector": float(
            fusion_metrics["event_f1"] - detector_metrics["event_f1"]
        ),
        "fp_per_10000_delta_vs_detector": float(
            fusion_metrics["false_positive_points_per_10000_normal_points"]
            - detector_metrics["false_positive_points_per_10000_normal_points"]
        ),
        "false_alarm_event_delta_vs_detector": float(
            fusion_metrics["false_alarm_events_per_10000_points"]
            - detector_metrics["false_alarm_events_per_10000_points"]
        ),
    }
