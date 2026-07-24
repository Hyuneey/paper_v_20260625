from experiments.argos_reproduction.branch_directional_selection import (
    select_candidate,
)


def _row(rule: str | None, f1: float, event: float, recovered: int) -> dict:
    return {
        "candidate_type": "no_op" if rule is None else "branch_rule",
        "rule_hash": rule,
        "initial_slot_id": rule,
        "combined_metrics": {"point_f1": f1, "event_f1": event},
        "directional_contribution_counts": {
            "FN_points_recovered": recovered,
            "added_FP_per_10000_normal_points": 0.0,
            "added_false_alarm_events": 0,
        },
    }


def test_fn_ranking_uses_frozen_order() -> None:
    assert select_candidate([_row(None, 0.5, 0.5, 0), _row("a", 0.6, 0.1, 1)], "FN")["rule_hash"] == "a"
