"""Directional and full-Aggregator contribution accounting for TASK-037E."""

from __future__ import annotations

from typing import Any

import numpy as np

from experiments.argos_reproduction.direct_event_metrics import (
    binary_vector,
    contiguous_events,
    direct_pa_free_metrics,
    intervals_overlap,
)


def _ratio(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _truth_events_touched(mask: np.ndarray, truth: np.ndarray) -> int:
    return sum(
        any(intervals_overlap(mask_event, truth_event) for mask_event in contiguous_events(mask))
        for truth_event in contiguous_events(truth)
    )


def fn_direction_contribution(
    truth: object, detector: object, combined: object
) -> dict[str, Any]:
    y = binary_vector(truth, "truth")
    d = binary_vector(detector, "detector")
    c = binary_vector(combined, "combined")
    before = direct_pa_free_metrics(y, d)
    after = direct_pa_free_metrics(y, c)
    additions = (d == 0) & (c == 1)
    added_tp = additions & (y == 1)
    added_fp = additions & (y == 0)
    recovered = int(before["false_negative"] - after["false_negative"])
    events_recovered = int(before["event_false_negative"] - after["event_false_negative"])
    return {
        "detector_FN_points_before": int(before["false_negative"]),
        "detector_FN_points_after": int(after["false_negative"]),
        "FN_points_recovered": recovered,
        "FN_recovery_rate": _ratio(recovered, int(before["false_negative"])),
        "detector_missed_events_before": int(before["event_false_negative"]),
        "detector_missed_events_after": int(after["event_false_negative"]),
        "events_recovered": events_recovered,
        "event_recovery_rate": _ratio(events_recovered, int(before["event_false_negative"])),
        "added_true_positive_points": int(np.sum(added_tp)),
        "added_false_positive_points": int(np.sum(added_fp)),
        "added_FP_per_10000_normal_points": (
            float(np.sum(added_fp)) / float(np.sum(y == 0)) * 10000
            if np.sum(y == 0)
            else 0.0
        ),
        "added_true_events": _truth_events_touched(added_tp.astype(np.int8), y),
        "added_false_alarm_events": len(contiguous_events(added_fp.astype(np.int8))),
    }


def fp_direction_contribution(
    truth: object, detector: object, combined: object
) -> dict[str, Any]:
    y = binary_vector(truth, "truth")
    d = binary_vector(detector, "detector")
    c = binary_vector(combined, "combined")
    before = direct_pa_free_metrics(y, d)
    after = direct_pa_free_metrics(y, c)
    removals = (d == 1) & (c == 0)
    removed_fp = removals & (y == 0)
    removed_tp = removals & (y == 1)
    fp_removed = int(before["false_positive"] - after["false_positive"])
    alarm_removed = int(before["event_false_positive"] - after["event_false_positive"])
    return {
        "detector_FP_points_before": int(before["false_positive"]),
        "detector_FP_points_after": int(after["false_positive"]),
        "FP_points_removed": fp_removed,
        "FP_removal_rate": _ratio(fp_removed, int(before["false_positive"])),
        "false_alarm_events_before": int(before["event_false_positive"]),
        "false_alarm_events_after": int(after["event_false_positive"]),
        "false_alarm_events_removed": alarm_removed,
        "true_positive_points_removed": int(np.sum(removed_tp)),
        "true_anomaly_events_removed": _truth_events_touched(removed_tp.astype(np.int8), y),
        "removed_false_positive_points": int(np.sum(removed_fp)),
    }


def full_aggregator_contribution(
    truth: object,
    detector: object,
    after_fp: object,
    full: object,
) -> dict[str, Any]:
    y = binary_vector(truth, "truth")
    d = binary_vector(detector, "detector")
    fp = binary_vector(after_fp, "after_fp")
    final = binary_vector(full, "full")
    before = direct_pa_free_metrics(y, d)
    after = direct_pa_free_metrics(y, final)
    overridden = (d == 1) & (fp == 0) & (final == 1)
    additions = (fp == 0) & (final == 1)
    return {
        "net_TP_delta": int(after["true_positive"] - before["true_positive"]),
        "net_FP_delta": int(after["false_positive"] - before["false_positive"]),
        "net_FN_delta": int(after["false_negative"] - before["false_negative"]),
        "net_TN_delta": int(after["true_negative"] - before["true_negative"]),
        "point_F1_delta": float(after["point_f1"] - before["point_f1"]),
        "event_F1_delta": float(after["event_f1"] - before["event_f1"]),
        "precision_delta": float(after["precision"] - before["precision"]),
        "recall_delta": float(after["recall"] - before["recall"]),
        "FP_per_10000_delta": float(
            after["false_positive_points_per_10000_normal_points"]
            - before["false_positive_points_per_10000_normal_points"]
        ),
        "FP_correction_changes_overridden_by_FN": int(np.sum(overridden)),
        "FN_additions_after_FP_correction": int(np.sum(additions)),
    }
