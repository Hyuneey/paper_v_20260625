"""Pure TASK-038A branch-state rules for the four ARGOS component arms."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping


class AgentBranchStateError(ValueError):
    """Raised when a logical branch violates the frozen factorial design."""


class BranchId(str, Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"


REPAIRABLE_RUNTIME_STATUSES = frozenset(
    {"target_runtime_failed", "contrast_runtime_failed", "output_contract_failed"}
)


@dataclass(frozen=True)
class BranchPlan:
    branch_id: BranchId
    agent_actions: tuple[str, ...]
    planned_state: str
    output_rule_hash: str | None
    repair_reuse_key: str | None
    review_input_kind: str | None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["branch_id"] = self.branch_id.value
        value["agent_actions"] = list(self.agent_actions)
        return value


def repair_trigger(initial_runtime_status: str, *, static_valid: bool) -> bool:
    return static_valid and initial_runtime_status in REPAIRABLE_RUNTIME_STATUSES


def review_trigger(
    *,
    executable: bool,
    combined_point_f1: float | None,
    detector_point_f1: float | None,
) -> str:
    if not executable:
        return "review_not_applicable_non_executable"
    if combined_point_f1 is None or detector_point_f1 is None:
        raise AgentBranchStateError("TASK038A_REVIEW_METRICS_REQUIRED")
    return (
        "no_review_needed"
        if combined_point_f1 >= detector_point_f1
        else "review_provider_call_required"
    )


def branch_plan(initial: Mapping[str, Any], branch_id: str) -> BranchPlan:
    try:
        branch = BranchId(branch_id)
    except ValueError as exc:
        raise AgentBranchStateError("TASK038A_UNKNOWN_BRANCH") from exc
    executable = bool(initial["initial_executable"])
    initial_hash = str(initial["initial_rule_hash"])
    repair_key = (
        f"REPAIR-{initial['initial_slot_id']}"
        if repair_trigger(
            str(initial["initial_runtime_status"]),
            static_valid=bool(initial["initial_static_valid"]),
        )
        else None
    )
    if branch is BranchId.A0:
        return BranchPlan(
            branch,
            (),
            "identity_initially_executable"
            if executable
            else "terminal_non_executable",
            initial_hash if executable else None,
            None,
            None,
        )
    if branch is BranchId.A1:
        return BranchPlan(
            branch,
            () if executable else ("repair",),
            "identity_initially_executable"
            if executable
            else "pending_task038b_repair",
            initial_hash if executable else None,
            repair_key,
            None,
        )
    if branch is BranchId.A2:
        return BranchPlan(
            branch,
            ("review_trigger",) if executable else (),
            "pending_task038c_review_trigger"
            if executable
            else "review_not_applicable_non_executable",
            initial_hash if executable else None,
            None,
            "initial_rule" if executable else None,
        )
    return BranchPlan(
        branch,
        ("repair", "review_trigger")
        if not executable
        else ("repair_identity", "review_trigger"),
        "pending_task038b_repair_then_task038c_review"
        if not executable
        else "pending_task038c_review_trigger",
        initial_hash if executable else None,
        repair_key,
        "repaired_rule" if not executable else "initial_rule",
    )


def reviewed_output_rule(
    *, pre_review_hash: str, reviewed_hash: str | None, reviewed_valid: bool
) -> str | None:
    """Return the actual Review output; never silently restore the input rule."""
    if reviewed_valid:
        if not reviewed_hash:
            raise AgentBranchStateError("TASK038A_REVIEWED_HASH_REQUIRED")
        return reviewed_hash
    return None
