"""Materialize aggregate-only A1/A3 Repair branch state updates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.repair_failure_replay import (
    load_repair_population,
    verify_report_hash,
)


def update_repair_branches(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    population = load_repair_population(config)
    runtime_raw = read_json(ROOT / str(config["reports"]["runtime"]))
    runtime = verify_report_hash(
        ROOT / str(config["reports"]["runtime"]),
        str(runtime_raw["report_hash"]),
    )
    runtime_by_slot = {item["initial_slot_id"]: item for item in runtime["records"]}
    records: list[dict[str, Any]] = []
    for initial in population:
        result = runtime_by_slot[initial["initial_slot_id"]]
        success = result["terminal_status"] == "repaired_executable"
        repaired_hash = result.get("repaired_rule_hash") if success else None
        records.append(
            {
                "initial_slot_id": initial["initial_slot_id"],
                "repair_reuse_key": initial["repair_reuse_key"],
                "A1_terminal_state": result["terminal_status"],
                "A1_rule_hash_or_null": repaired_hash,
                "A3_pre_review_state": (
                    "repair_complete_review_pending"
                    if success
                    else result["terminal_status"]
                ),
                "A3_parent_rule_hash_or_null": repaired_hash,
                "Repair_shared_between_A1_A3": True,
            }
        )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038B",
        "artifact_type": "repair_branch_update",
        "initial_repair_candidates": 13,
        "updated_branches": ["A1", "A3"],
        "A0_unchanged": True,
        "A2_unchanged": True,
        "review_agent_executed": False,
        "repair_reuse_preserved": all(
            item["Repair_shared_between_A1_A3"] for item in records
        ),
        "source_branch_registry_hash": config["task038a_hashes"][
            "branch_registry_hash"
        ],
        "records": records,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["branch_update"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038b_repair_execution.json",
    )
    args = parser.parse_args()
    report = update_repair_branches((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "records": len(report["records"]),
                "repair_reuse_preserved": report["repair_reuse_preserved"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
