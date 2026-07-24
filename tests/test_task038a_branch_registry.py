from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from experiments.argos_reproduction.agent_factorial_registry import (
    build_branch_registry,
    build_initial_rule_registry,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads(
    (
        ROOT / "configs/argos_reproduction/task038a_agent_factorial_protocol.json"
    ).read_text(encoding="utf-8")
)


def test_exactly_four_balanced_branches_per_initial_slot() -> None:
    initial = build_initial_rule_registry(CONFIG)
    initial["report_hash"] = "synthetic-in-memory-registry"
    branches = build_branch_registry(CONFIG, initial)
    assert branches["branch_count"] == 384
    assert Counter(row["branch_id"] for row in branches["records"]) == Counter(
        {"A0": 96, "A1": 96, "A2": 96, "A3": 96}
    )
    grouped: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for row in branches["records"]:
        grouped[row["initial_slot_id"]].append(row)
    assert len(grouped) == 96
    assert all({row["branch_id"] for row in rows} == {"A0", "A1", "A2", "A3"} for rows in grouped.values())


def test_branch_identity_and_repair_reuse_are_lineage_preserving() -> None:
    initial = build_initial_rule_registry(CONFIG)
    initial["report_hash"] = "synthetic-in-memory-registry"
    branches = build_branch_registry(CONFIG, initial)
    by_slot: defaultdict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    for row in branches["records"]:
        by_slot[row["initial_slot_id"]][row["branch_id"]] = row
        assert row["parent_rule_hash"] == row["initial_rule_hash"]
    failed = [
        rows
        for rows in by_slot.values()
        if rows["A0"]["planned_state"] == "terminal_non_executable"
    ]
    assert len(failed) == 13
    assert all(
        rows["A1"]["repair_reuse_key"] == rows["A3"]["repair_reuse_key"]
        for rows in failed
    )
    executable = [
        rows
        for rows in by_slot.values()
        if rows["A0"]["planned_state"] == "identity_initially_executable"
    ]
    assert len(executable) == 83
    assert all(rows["A1"]["agent_actions"] == [] for rows in executable)
    assert all(
        rows["A2"]["planned_state"] == "review_not_applicable_non_executable"
        for rows in failed
    )
