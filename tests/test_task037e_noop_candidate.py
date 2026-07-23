from __future__ import annotations

from experiments.argos_reproduction.directional_rule_selection import (
    select_direction_candidate,
)


def _candidate(candidate_id: str, *, no_op: bool = False) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "candidate_type": "no_op" if no_op else "executable_rule",
        "combined_metrics": {
            "point_f1": 0.5,
            "event_f1": 0.4,
            "false_positive_points_per_10000_normal_points": 0.0,
        },
        "directional_contribution_counts": {
            "FN_points_recovered": 0,
            "added_FP_per_10000_normal_points": 0.0,
            "added_false_alarm_events": 0,
            "FP_points_removed": 0,
            "true_positive_points_removed": 0,
            "true_anomaly_events_removed": 0,
        },
    }


def test_noop_wins_exact_complete_fn_tie() -> None:
    noop = _candidate("NO_OP", no_op=True)
    rule = _candidate("0000")
    assert select_direction_candidate([rule, noop], "FN")["candidate_type"] == "no_op"


def test_noop_wins_exact_complete_fp_tie() -> None:
    noop = _candidate("NO_OP", no_op=True)
    rule = _candidate("0000")
    assert select_direction_candidate([rule, noop], "FP")["candidate_type"] == "no_op"
