from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from experiments.argos_reproduction import directional_rule_selection as selection
from experiments.argos_reproduction.directional_rule_selection import (
    fn_selection_order,
    fp_selection_order,
    load_inner_labels_after_freeze,
    select_direction_candidate,
)


def _candidate(
    candidate_id: str,
    *,
    point_f1: float,
    event_f1: float,
    recovered: int = 0,
    removed: int = 0,
    fp_per_10000: float = 0.0,
    false_alarm_events: int = 0,
    tp_removed: int = 0,
    events_removed: int = 0,
    no_op: bool = False,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "candidate_type": "no_op" if no_op else "executable_rule",
        "combined_metrics": {
            "point_f1": point_f1,
            "event_f1": event_f1,
            "false_positive_points_per_10000_normal_points": fp_per_10000,
        },
        "directional_contribution_counts": {
            "FN_points_recovered": recovered,
            "added_FP_per_10000_normal_points": fp_per_10000,
            "added_false_alarm_events": false_alarm_events,
            "FP_points_removed": removed,
            "true_positive_points_removed": tp_removed,
            "true_anomaly_events_removed": events_removed,
        },
    }


def test_fn_ranking_matches_dec069() -> None:
    noop = _candidate("NO_OP", point_f1=0.5, event_f1=0.5, no_op=True)
    better = _candidate(
        "bbb", point_f1=0.6, event_f1=0.4, recovered=2, fp_per_10000=3.0
    )
    tied_better_hash = _candidate(
        "aaa", point_f1=0.6, event_f1=0.4, recovered=2, fp_per_10000=3.0
    )
    assert fn_selection_order(tied_better_hash) < fn_selection_order(better)
    assert select_direction_candidate([noop, better, tied_better_hash], "FN")[
        "candidate_id"
    ] == "aaa"


def test_fp_ranking_matches_dec069() -> None:
    noop = _candidate("NO_OP", point_f1=0.4, event_f1=0.4, no_op=True)
    loses_tp = _candidate(
        "aaa", point_f1=0.6, event_f1=0.5, removed=5, tp_removed=2
    )
    retains_tp = _candidate(
        "bbb", point_f1=0.6, event_f1=0.5, removed=5, tp_removed=1
    )
    assert fp_selection_order(retains_tp) < fp_selection_order(loses_tp)
    assert select_direction_candidate([noop, loses_tp, retains_tp], "FP")[
        "candidate_id"
    ] == "bbb"


def test_selection_source_has_no_joint_pair_search() -> None:
    source = open(
        "experiments/argos_reproduction/directional_rule_selection.py",
        encoding="utf-8",
    ).read()
    assert "joint_pair_search_performed" in source
    assert '"FN_FP_selected_independently": True' in source
    assert "top_3" not in source
    assert "majority" not in source


def test_inner_label_lineage_uses_normalized_array_bytes(
    tmp_path: Path, monkeypatch
) -> None:
    labels = np.asarray([0, 1, 1, 0], dtype=np.int8)
    label_path = tmp_path / "inner.npy"
    np.save(label_path, labels, allow_pickle=False)
    expected_hash = hashlib.sha256(labels.tobytes()).hexdigest()

    monkeypatch.setattr(
        selection,
        "verify_hashed_report",
        lambda _path: {
            "records": [
                {"kpi_id": f"KPI-{index}", "inner_label_hash": expected_hash}
                for index in range(10)
            ]
        },
    )
    monkeypatch.setattr(selection, "_label_path", lambda *_args: label_path)

    loaded = load_inner_labels_after_freeze(
        {"expected_executable_rule_count": 83, "sources": {"task037b_threshold_freeze": "x"}},
        {"status": "frozen_before_inner_label_access", "record_count": 83},
        {
            (variant, f"KPI-{index}"): {}
            for variant in ("LSTMADalpha", "LSTMADbeta")
            for index in range(10)
        },
    )
    assert np.array_equal(loaded["KPI-1"], labels)
