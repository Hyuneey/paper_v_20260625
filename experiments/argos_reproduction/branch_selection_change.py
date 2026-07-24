"""Compare A1/A2/A3 inner selections with the reproduced A0 baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.argos_reproduction.branch_output_registry import ROOT, load_config
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)


def _category(a0: dict[str, Any], branch: dict[str, Any]) -> str:
    a0_rule = a0["selected_candidate_type"] == "branch_rule"
    branch_rule = branch["selected_candidate_type"] == "branch_rule"
    if not a0_rule and not branch_rule:
        return "same_no_op"
    if a0_rule and branch_rule:
        if a0["selected_rule_hash_or_null"] == branch["selected_rule_hash_or_null"]:
            return "same_rule"
        return "A0_rule_to_branch_rule"
    if a0_rule:
        return "A0_rule_to_no_op"
    return "A0_no_op_to_branch_rule"


def build_change_report(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    selection = verify_hashed_report(ROOT / str(config["reports"]["selection_freeze"]))
    by_key = {
        (
            row["branch_id"],
            row["detector_variant"],
            row["kpi_id"],
            row["direction"],
        ): row
        for row in selection["records"]
    }
    records: list[dict[str, Any]] = []
    for branch in ("A1", "A2", "A3"):
        for variant, kpi_id, direction in sorted(
            {
                (row["detector_variant"], row["kpi_id"], row["direction"])
                for row in selection["records"]
                if row["branch_id"] == "A0"
            }
        ):
            a0 = by_key[("A0", variant, kpi_id, direction)]
            current = by_key[(branch, variant, kpi_id, direction)]
            records.append(
                {
                    "branch_id": branch,
                    "detector_variant": variant,
                    "kpi_id": kpi_id,
                    "direction": direction,
                    "change_category": _category(a0, current),
                    "A0_selected_rule_hash_or_null": a0[
                        "selected_rule_hash_or_null"
                    ],
                    "branch_selected_rule_hash_or_null": current[
                        "selected_rule_hash_or_null"
                    ],
                }
            )
    summaries: dict[str, Any] = {}
    for branch in ("A1", "A2", "A3"):
        summaries[branch] = {}
        for direction in ("FN", "FP"):
            rows = [
                row
                for row in records
                if row["branch_id"] == branch and row["direction"] == direction
            ]
            unchanged = {"same_rule", "same_no_op"}
            summaries[branch][direction] = {
                "selection_changed_count": sum(
                    row["change_category"] not in unchanged for row in rows
                ),
                "selection_unchanged_count": sum(
                    row["change_category"] in unchanged for row in rows
                ),
                "A0_no_op_replaced_count": sum(
                    row["change_category"] == "A0_no_op_to_branch_rule"
                    for row in rows
                ),
                "A0_rule_removed_count": sum(
                    row["change_category"] == "A0_rule_to_no_op" for row in rows
                ),
            }
    stochastic = verify_hashed_report(
        ROOT / str(config["sources"]["task038c_stochastic"]),
        str(config["source_hashes"]["task038c_stochastic"]),
    )
    selected_slots = {
        (row["branch_id"], row["selected_initial_slot_id_or_null"])
        for row in selection["records"]
        if row["selected_initial_slot_id_or_null"] is not None
    }
    paired = []
    for row in stochastic["records"]:
        slot = row["initial_slot_id"]
        a2 = ("A2", slot) in selected_slots
        a3 = ("A3", slot) in selected_slots
        paired.append(
            {
                "initial_slot_id": slot,
                "A2_output_rule_hash": row["A2_reviewed_rule_hash"],
                "A3_output_rule_hash": row["A3_reviewed_rule_hash"],
                "A2_selected_in_unit": a2,
                "A3_selected_in_unit": a3,
                "selection_outcome_same": a2 == a3,
            }
        )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038D",
        "artifact_type": "selection_change_report",
        "status": "complete",
        "selection_freeze_hash": selection["report_hash"],
        "branch_direction_summaries": summaries,
        "stochastic_selection_stability": {
            "paired_review_slots": len(paired),
            "both_selected": sum(row["A2_selected_in_unit"] and row["A3_selected_in_unit"] for row in paired),
            "A2_only_selected": sum(row["A2_selected_in_unit"] and not row["A3_selected_in_unit"] for row in paired),
            "A3_only_selected": sum(not row["A2_selected_in_unit"] and row["A3_selected_in_unit"] for row in paired),
            "neither_selected": sum(not row["A2_selected_in_unit"] and not row["A3_selected_in_unit"] for row in paired),
            "interpreted_as_repair_effect": False,
            "records": paired,
        },
        "outer_improvement_claimed": False,
        "outer_access": False,
        "sealed_test_access": False,
        "records": records,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["selection_change"]), report
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task038d_branch_selection.json")
    args = parser.parse_args()
    report = build_change_report((ROOT / args.config).resolve())
    print(json.dumps(report["branch_direction_summaries"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
