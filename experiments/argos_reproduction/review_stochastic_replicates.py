"""Describe A2/A3 Review generation variability for shared initial parents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import read_json
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)


def compute_stochastic_replicates(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    manifest = verify_hashed_report(ROOT / str(config["reports"]["call_manifest"]))
    effects = verify_hashed_report(ROOT / str(config["reports"]["effect"]))
    slots = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in manifest["slots"]
    }
    effect_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in effects["records"]
    }
    common_ids = sorted(
        initial_slot_id
        for branch, initial_slot_id in slots
        if branch == "A2" and ("A3", initial_slot_id) in slots
    )
    records: list[dict[str, Any]] = []
    for slot_id in common_ids:
        a2_slot = slots[("A2", slot_id)]
        a3_slot = slots[("A3", slot_id)]
        a2 = effect_by_key[("A2", slot_id)]
        a3 = effect_by_key[("A3", slot_id)]
        a2_f1 = (
            a2["post_metrics"]["point_f1"] if a2["post_metrics"] is not None else None
        )
        a3_f1 = (
            a3["post_metrics"]["point_f1"] if a3["post_metrics"] is not None else None
        )
        difference = (
            abs(float(a2_f1) - float(a3_f1))
            if a2_f1 is not None and a3_f1 is not None
            else None
        )
        records.append(
            {
                "initial_slot_id": slot_id,
                "same_parent_rule_hash": a2_slot["parent_rule_hash"]
                == a3_slot["parent_rule_hash"],
                "same_prompt_payload_hash": a2_slot["prompt_payload_hash"]
                == a3_slot["prompt_payload_hash"],
                "different_branch_request_hash": a2_slot["branch_request_hash"]
                != a3_slot["branch_request_hash"],
                "A2_response_hash": a2["response_hash"],
                "A3_response_hash": a3["response_hash"],
                "A2_reviewed_rule_hash": a2["reviewed_rule_hash"],
                "A3_reviewed_rule_hash": a3["reviewed_rule_hash"],
                "reviewed_rule_hash_equal": a2["reviewed_rule_hash"]
                is not None
                and a2["reviewed_rule_hash"] == a3["reviewed_rule_hash"],
                "A2_post_inner_F1": a2_f1,
                "A3_post_inner_F1": a3_f1,
                "absolute_F1_difference": difference,
            }
        )
    valid = [row for row in records if row["absolute_F1_difference"] is not None]
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "review_stochastic_replicate_report",
        "interpretation": "independent_Review_generation_variability_not_Repair_effect",
        "paired_review_call_count": len(records),
        "identical_response_rate": (
            sum(
                row["A2_response_hash"] is not None
                and row["A2_response_hash"] == row["A3_response_hash"]
                for row in records
            )
            / len(records)
            if records
            else 0.0
        ),
        "identical_rule_rate": (
            sum(row["reviewed_rule_hash_equal"] for row in records) / len(records)
            if records
            else 0.0
        ),
        "median_absolute_F1_difference": (
            float(np.median([row["absolute_F1_difference"] for row in valid]))
            if valid
            else None
        ),
        "A2_better_count": sum(
            row["A2_post_inner_F1"] is not None
            and row["A3_post_inner_F1"] is not None
            and row["A2_post_inner_F1"] > row["A3_post_inner_F1"]
            for row in records
        ),
        "A3_better_count": sum(
            row["A2_post_inner_F1"] is not None
            and row["A3_post_inner_F1"] is not None
            and row["A3_post_inner_F1"] > row["A2_post_inner_F1"]
            for row in records
        ),
        "tie_count": sum(
            row["A2_post_inner_F1"] is not None
            and row["A2_post_inner_F1"] == row["A3_post_inner_F1"]
            for row in records
        ),
        "outer_access": False,
        "sealed_test_access": False,
        "records": records,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["stochastic"]), report
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    report = compute_stochastic_replicates((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "paired_review_calls": report["paired_review_call_count"],
                "identical_rule_rate": report["identical_rule_rate"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
