"""Reconstruct the 357 immutable TASK-038D branch output records."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import read_json
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)


class BranchRegistryError(RuntimeError):
    """Raised when frozen branch lineage cannot produce the exact registry."""


def load_config(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    for commit in config["lineage"].values():
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", str(commit), "HEAD"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise BranchRegistryError("TASK038D_REQUIRED_COMMIT_NOT_ANCESTOR")
    return config


def _report(
    config: Mapping[str, Any], source: str, hash_name: str
) -> dict[str, Any]:
    return verify_hashed_report(
        ROOT / str(config["sources"][source]),
        str(config["source_hashes"][hash_name]),
    )


def _base(initial: Mapping[str, Any], branch: str) -> dict[str, Any]:
    return {
        "branch_id": branch,
        "initial_slot_id": initial["initial_slot_id"],
        "detector_variant": initial["detector_variant"],
        "kpi_id": initial["kpi_id"],
        "direction": initial["direction"],
        "initial_rule_hash": initial["initial_rule_hash"],
    }


def build_branch_output_registry(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    initial = _report(config, "task038a_initial_registry", "task038a_initial_registry")
    repair = _report(config, "task038b_runtime", "task038b_runtime")
    repair_update = _report(
        config, "task038b_branch_update", "task038b_branch_update"
    )
    branch_update = _report(
        config, "task038c_branch_update", "task038c_branch_update"
    )
    parent_registry = _report(
        config, "task038c_parent_registry", "task038c_parent_registry"
    )
    repaired = {row["initial_slot_id"]: row for row in repair["records"]}
    repair_updates = {
        row["initial_slot_id"]: row for row in repair_update["records"]
    }
    review_updates = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in branch_update["records"]
    }
    parents = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in parent_registry["records"]
    }
    records: list[dict[str, Any]] = []
    for row in sorted(initial["records"], key=lambda item: item["initial_slot_id"]):
        slot = row["initial_slot_id"]
        if row["initial_executable"]:
            records.append(
                {
                    **_base(row, "A0"),
                    "output_origin": "initial_rule",
                    "parent_rule_hash": row["initial_rule_hash"],
                    "output_rule_hash": row["initial_rule_hash"],
                    "repair_reuse_key_or_null": None,
                    "Review_call_slot_id_or_null": None,
                    "terminal_branch_state": "initial_executable",
                }
            )
            records.append(
                {
                    **_base(row, "A1"),
                    "output_origin": "repair_identity",
                    "parent_rule_hash": row["initial_rule_hash"],
                    "output_rule_hash": row["initial_rule_hash"],
                    "repair_reuse_key_or_null": None,
                    "Review_call_slot_id_or_null": None,
                    "terminal_branch_state": "repair_identity",
                }
            )
        else:
            repaired_row = repaired.get(slot)
            update_row = repair_updates.get(slot)
            if (
                repaired_row is None
                or update_row is None
                or repaired_row["terminal_status"] != "repaired_executable"
                or update_row["A1_rule_hash_or_null"]
                != repaired_row["repaired_rule_hash"]
            ):
                raise BranchRegistryError("TASK038D_REPAIR_LINEAGE_MISMATCH")
            records.append(
                {
                    **_base(row, "A1"),
                    "output_origin": "repaired_rule",
                    "parent_rule_hash": row["initial_rule_hash"],
                    "output_rule_hash": repaired_row["repaired_rule_hash"],
                    "repair_reuse_key_or_null": row["repair_reuse_key"],
                    "Review_call_slot_id_or_null": None,
                    "terminal_branch_state": "repaired_executable",
                }
            )
        for branch in ("A2", "A3"):
            update = review_updates[(branch, slot)]
            state = update["terminal_state"]
            if state not in ("no_review_needed_identity", "reviewed_executable"):
                continue
            parent = parents[(branch, slot)]
            reviewed = state == "reviewed_executable"
            repaired_parent = parent["parent_type"] == "repaired_executable"
            if reviewed:
                origin = (
                    "reviewed_repaired_rule"
                    if repaired_parent
                    else "reviewed_initial_rule"
                )
                call_id = f"REVIEW-{branch}-{slot}"
            else:
                origin = (
                    "no_review_needed_repaired_identity"
                    if repaired_parent
                    else "no_review_needed_initial_identity"
                )
                call_id = None
            records.append(
                {
                    **_base(row, branch),
                    "output_origin": origin,
                    "parent_rule_hash": update["parent_rule_hash"],
                    "output_rule_hash": update["output_rule_hash_or_null"],
                    "repair_reuse_key_or_null": update["repair_reuse_key"],
                    "Review_call_slot_id_or_null": call_id,
                    "terminal_branch_state": state,
                }
            )
    observed = Counter(row["branch_id"] for row in records)
    expected = {key: int(config["counts"][key]) for key in ("A0", "A1", "A2", "A3")}
    if dict(observed) != expected or len(records) != int(
        config["counts"]["branch_executable_outputs"]
    ):
        raise BranchRegistryError("TASK038D_BRANCH_OUTPUT_REGISTRY_MISMATCH")
    units = {
        (
            row["branch_id"],
            row["detector_variant"],
            row["kpi_id"],
            row["direction"],
        )
        for row in records
    }
    if len(units) > int(config["counts"]["selection_units"]):
        raise BranchRegistryError("TASK038D_SELECTION_UNIT_OVERFLOW")
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038D",
        "artifact_type": "branch_output_registry",
        "status": "branch_outputs_frozen_before_inner_label_access",
        "branch_output_counts": expected,
        "total_branch_executable_output_records": len(records),
        "selection_unit_keys_with_rules": len(units),
        "invalid_review_fallback_performed": False,
        "labels_loaded": False,
        "outer_access": False,
        "sealed_test_access": False,
        "raw_rule_source_tracked": False,
        "records": records,
    }
    return write_hashed_report(ROOT / str(config["reports"]["branch_registry"]), report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038d_branch_selection.json",
    )
    args = parser.parse_args()
    report = build_branch_output_registry((ROOT / args.config).resolve())
    print(json.dumps(report["branch_output_counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
