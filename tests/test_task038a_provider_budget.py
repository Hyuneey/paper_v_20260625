from __future__ import annotations

import json
from pathlib import Path

from experiments.argos_reproduction.agent_call_budget import build_call_budget
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
PROVIDER = json.loads(
    (
        ROOT / "configs/argos_reproduction/task038a_agent_provider_policy.json"
    ).read_text(encoding="utf-8")
)


def test_frozen_provider_budget_is_bounded_and_not_authorized() -> None:
    initial = build_initial_rule_registry(CONFIG)
    initial["report_hash"] = "in-memory-initial"
    branches = build_branch_registry(CONFIG, initial)
    branches["report_hash"] = "in-memory-branches"
    budget = build_call_budget(CONFIG, PROVIDER, initial, branches)
    assert budget["components"] == {
        "repair_unique": 13,
        "review_A2_ceiling": 83,
        "review_A3_initial_executable_ceiling": 83,
        "review_A3_repaired_ceiling": 13,
    }
    assert budget["maximum_unique_primary_study_calls"] == 192
    assert budget["repair_reused_between_A1_and_A3"] is True
    assert budget["real_provider_calls"] == 0
    assert budget["real_provider_execution_authorized"] is False
    assert budget["automatic_retry"] is False
    assert budget["manual_retry"] is False
    assert budget["replacement_generation"] is False
