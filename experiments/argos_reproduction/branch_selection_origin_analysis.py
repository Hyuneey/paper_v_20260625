"""Summarize selected rule origins and Repair/Review selection survival."""

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


def build_origin_report(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    registry = verify_hashed_report(ROOT / str(config["reports"]["branch_registry"]))
    selection = verify_hashed_report(ROOT / str(config["reports"]["selection_freeze"]))
    effects = verify_hashed_report(
        ROOT / str(config["sources"]["task038c_effect"]),
        str(config["source_hashes"]["task038c_effect"]),
    )
    effect_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in effects["records"]
    }
    by_branch = {
        branch: [row for row in registry["records"] if row["branch_id"] == branch]
        for branch in ("A0", "A1", "A2", "A3")
    }
    summary: dict[str, Any] = {}
    for branch in ("A0", "A1", "A2", "A3"):
        selected = [
            row
            for row in selection["records"]
            if row["branch_id"] == branch
            and row["selected_candidate_type"] == "branch_rule"
        ]
        origins = [row["selected_output_origin"] for row in selected]
        candidates = by_branch[branch]
        summary[branch] = {
            "selected_initial_rules": sum(
                origin in ("initial_rule", "repair_identity") for origin in origins
            ),
            "selected_repaired_rules": sum(origin == "repaired_rule" for origin in origins),
            "selected_reviewed_initial_rules": sum(
                origin == "reviewed_initial_rule" for origin in origins
            ),
            "selected_reviewed_repaired_rules": sum(
                origin == "reviewed_repaired_rule" for origin in origins
            ),
            "selected_no_review_needed_identities": sum(
                origin.startswith("no_review_needed_") for origin in origins
            ),
            "selected_no_ops": sum(
                row["branch_id"] == branch
                and row["selected_candidate_type"] == "no_op"
                for row in selection["records"]
            ),
            "repaired_candidates_available": sum(
                row["output_origin"] == "repaired_rule" for row in candidates
            ),
            "repaired_candidates_selected": sum(
                origin == "repaired_rule" for origin in origins
            ),
            "reviewed_candidates_available": sum(
                row["output_origin"].startswith("reviewed_") for row in candidates
            ),
            "reviewed_candidates_selected": sum(
                origin.startswith("reviewed_") for origin in origins
            ),
            "no_review_identity_candidates_available": sum(
                row["output_origin"].startswith("no_review_needed_")
                for row in candidates
            ),
            "no_review_identity_candidates_selected": sum(
                origin.startswith("no_review_needed_") for origin in origins
            ),
        }
        summary[branch]["repaired_candidates_rejected"] = (
            summary[branch]["repaired_candidates_available"]
            - summary[branch]["repaired_candidates_selected"]
        )
        summary[branch]["reviewed_candidates_rejected"] = (
            summary[branch]["reviewed_candidates_available"]
            - summary[branch]["reviewed_candidates_selected"]
        )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038D",
        "artifact_type": "selection_origin_report",
        "status": "complete",
        "selection_freeze_hash": selection["report_hash"],
        "branch_summaries": summary,
        "repair_survival": {
            "A1_repaired_rule_selected_count": summary["A1"][
                "selected_repaired_rules"
            ],
            "A3_repaired_or_reviewed_repaired_selected_count": summary["A3"][
                "selected_reviewed_repaired_rules"
            ]
            + sum(
                row["selected_output_origin"]
                == "no_review_needed_repaired_identity"
                for row in selection["records"]
                if row["branch_id"] == "A3"
            ),
        },
        "review_survival": {
            "A2_reviewed_rule_selected_count": summary["A2"][
                "reviewed_candidates_selected"
            ],
            "A3_reviewed_rule_selected_count": summary["A3"][
                "reviewed_candidates_selected"
            ],
        },
        "review_rejection": {
            "reviewed_rule_available_but_not_selected": sum(
                summary[branch]["reviewed_candidates_rejected"]
                for branch in ("A2", "A3")
            ),
            "reviewed_rule_selected_despite_inner_regression": sum(
                row["selected_output_origin"] in (
                    "reviewed_initial_rule",
                    "reviewed_repaired_rule",
                )
                and effect_by_key[
                    (row["branch_id"], row["selected_initial_slot_id_or_null"])
                ]["outcome"]
                == "regressed"
                for row in selection["records"]
                if row["branch_id"] in ("A2", "A3")
                and row["selected_initial_slot_id_or_null"] is not None
                and (
                    row["branch_id"], row["selected_initial_slot_id_or_null"]
                )
                in effect_by_key
            ),
        },
        "outer_access": False,
        "sealed_test_access": False,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["selection_origin"]), report
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task038d_branch_selection.json")
    args = parser.parse_args()
    report = build_origin_report((ROOT / args.config).resolve())
    print(json.dumps(report["branch_summaries"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
