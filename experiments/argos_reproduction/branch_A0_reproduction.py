"""Verify the committed TASK-038D A0 reproduction control."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from experiments.argos_reproduction.branch_output_registry import (
    BranchRegistryError,
    ROOT,
)
from experiments.argos_reproduction.review_parent_registry import verify_hashed_report


def verify_a0_reproduction(config: Mapping[str, Any]) -> dict[str, Any]:
    report = verify_hashed_report(ROOT / str(config["reports"]["a0_reproduction"]))
    if (
        report["status"] != "exact_reproduction_passed"
        or not report["A0_exact_selection_reproduction"]
        or report["exact_match_count"] != 40
        or (
            report["A0_FN_rule_selected_count"],
            report["A0_FN_no_op_count"],
            report["A0_FP_rule_selected_count"],
            report["A0_FP_no_op_count"],
        )
        != (19, 1, 2, 18)
    ):
        raise BranchRegistryError("TASK038D_A0_SELECTION_REPRODUCTION_FAILED")
    return report
