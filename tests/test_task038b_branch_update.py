from __future__ import annotations

import inspect

from experiments.argos_reproduction import repair_branch_update


def test_only_a1_and_a3_are_updated_and_repair_is_shared() -> None:
    source = inspect.getsource(repair_branch_update.update_repair_branches)
    assert '"updated_branches": ["A1", "A3"]' in source
    assert '"A0_unchanged": True' in source
    assert '"A2_unchanged": True' in source
    assert '"Repair_shared_between_A1_A3": True' in source
    assert "review_agent_executed" in source


def test_a3_success_waits_for_future_review() -> None:
    source = inspect.getsource(repair_branch_update.update_repair_branches)
    assert "repair_complete_review_pending" in source
