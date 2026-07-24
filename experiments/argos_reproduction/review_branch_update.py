"""Materialize TASK-038C A2/A3 terminal branch states without fallback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import read_json
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)


def update_review_branches(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    registry = verify_hashed_report(ROOT / str(config["reports"]["parent_registry"]))
    trigger = verify_hashed_report(ROOT / str(config["reports"]["trigger"]))
    runtime = verify_hashed_report(ROOT / str(config["reports"]["runtime"]))
    trigger_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in trigger["records"]
    }
    runtime_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in runtime["records"]
    }
    records: list[dict[str, Any]] = []
    for parent in registry["records"]:
        base = {
            key: parent[key]
            for key in (
                "branch_id",
                "initial_slot_id",
                "detector_variant",
                "kpi_id",
                "direction",
                "parent_type",
                "parent_rule_hash",
                "repair_reuse_key",
            )
        }
        if not parent["review_eligible"]:
            records.append(
                {
                    **base,
                    "review_trigger": "not_applicable",
                    "terminal_state": "review_not_applicable_non_executable",
                    "output_rule_hash_or_null": None,
                    "harmful_revision_reverted": False,
                }
            )
            continue
        trigger_row = trigger_by_key[
            (parent["branch_id"], parent["initial_slot_id"])
        ]
        if trigger_row["review_trigger"] == "no_review_needed":
            records.append(
                {
                    **base,
                    "review_trigger": "no_review_needed",
                    "terminal_state": "no_review_needed_identity",
                    "output_rule_hash_or_null": parent["parent_rule_hash"],
                    "harmful_revision_reverted": False,
                }
            )
            continue
        runtime_row = runtime_by_key[
            (parent["branch_id"], parent["initial_slot_id"])
        ]
        reviewed_hash = (
            runtime_row["reviewed_rule_hash"]
            if runtime_row["terminal_status"] == "reviewed_executable"
            else None
        )
        records.append(
            {
                **base,
                "review_trigger": "review_required",
                "terminal_state": runtime_row["terminal_status"],
                "output_rule_hash_or_null": reviewed_hash,
                "harmful_revision_reverted": False,
            }
        )
    executable = [row for row in records if row["review_trigger"] != "not_applicable"]
    if (
        len(records) != int(config["counts"]["all_branch_records"])
        or len(executable) != int(config["counts"]["logical_executable_parents"])
        or any(not row["terminal_state"] for row in records)
    ):
        raise RuntimeError("TASK038C_BRANCH_UPDATE_INCOMPLETE")
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "review_branch_update",
        "all_branch_record_count": len(records),
        "executable_review_branch_count": len(executable),
        "A2_nonapplicable_count": sum(
            row["terminal_state"] == "review_not_applicable_non_executable"
            for row in records
        ),
        "A0_unchanged": True,
        "A1_unchanged": True,
        "harmful_revision_revert": False,
        "repair_agent_calls": 0,
        "outer_access": False,
        "sealed_test_access": False,
        "records": records,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["branch_update"]), report
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    report = update_review_branches((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "records": report["all_branch_record_count"],
                "executable_branches": report["executable_review_branch_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
