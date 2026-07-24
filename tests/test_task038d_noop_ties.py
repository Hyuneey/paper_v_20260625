from experiments.argos_reproduction.branch_directional_selection import select_candidate


def _row(rule: str | None, direction: str) -> dict:
    contribution = (
        {"FN_points_recovered": 0, "added_FP_per_10000_normal_points": 0.0, "added_false_alarm_events": 0}
        if direction == "FN"
        else {"FP_points_removed": 0, "true_positive_points_removed": 0, "true_anomaly_events_removed": 0}
    )
    return {
        "candidate_type": "no_op" if rule is None else "branch_rule",
        "rule_hash": rule,
        "initial_slot_id": rule,
        "combined_metrics": {"point_f1": 0.5, "event_f1": 0.5},
        "directional_contribution_counts": contribution,
    }


def test_complete_scientific_tie_selects_noop() -> None:
    for direction in ("FN", "FP"):
        assert select_candidate([_row("000", direction), _row(None, direction)], direction)["candidate_type"] == "no_op"
