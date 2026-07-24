from experiments.argos_reproduction.branch_directional_selection import (
    select_candidate,
)


def _row(rule: str | None, removed: int, tp_removed: int) -> dict:
    return {
        "candidate_type": "no_op" if rule is None else "branch_rule",
        "rule_hash": rule,
        "initial_slot_id": rule,
        "combined_metrics": {"point_f1": 0.5, "event_f1": 0.5},
        "directional_contribution_counts": {
            "FP_points_removed": removed,
            "true_positive_points_removed": tp_removed,
            "true_anomaly_events_removed": 0,
        },
    }


def test_fp_ranking_prefers_more_fp_removal_then_fewer_tp_removals() -> None:
    winner = select_candidate([_row(None, 0, 0), _row("a", 2, 1), _row("b", 2, 2)], "FP")
    assert winner["rule_hash"] == "a"
