"""Freeze all branch, Review-transfer, and Repair-utility outer predictions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from experiments.argos_reproduction.branch_candidate_predictions import load_binary
from experiments.argos_reproduction.expanded_kpi_cohort import sha256_file
from experiments.argos_reproduction.review_parent_registry import (
    ROOT,
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.task038e_branch_aggregator import (
    ARMS,
    branch_arm_path,
    compose_branch_arms,
    compose_direction,
    detector_prediction_path,
    repair_combined_path,
    review_combined_path,
)
from experiments.argos_reproduction.task038e_execution_dedup import (
    physical_prediction_path,
)
from experiments.argos_reproduction.task038e_outer_registry import (
    load_config,
    source_report,
)


class PredictionFreezeError(RuntimeError):
    """Raised when TASK-038E prediction construction is incomplete."""


def _save(path: Path, value: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, value.astype(np.int8, copy=False), allow_pickle=False)
    return sha256_file(path)


def freeze_outer_predictions(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    registry = verify_hashed_report(ROOT / str(config["reports"]["outer_registry"]))
    physical = verify_hashed_report(ROOT / str(config["reports"]["physical_manifest"]))
    runtime = verify_hashed_report(ROOT / str(config["reports"]["outer_runtime"]))
    detector_manifest = source_report(config, "task037b_detector_manifest")
    if (
        runtime["status"] != "all_physical_predictions_frozen"
        or runtime["physical_execution_unit_count"]
        != physical["physical_execution_unit_count"]
    ):
        raise PredictionFreezeError("TASK038E_PHYSICAL_RUNTIME_INCOMPLETE")
    detector_by_key = {
        (row["detector_variant"], row["kpi_id"]): row
        for row in detector_manifest["records"]
    }
    runtime_by_id = {
        row["physical_execution_unit_id"]: row for row in runtime["records"]
    }
    mapping = {
        (row["logical_record_id"], row["prediction_role"]): row[
            "physical_execution_unit_id"
        ]
        for row in physical["logical_to_physical"]
    }

    def prediction(logical_id: str, role: str) -> np.ndarray:
        unit_id = mapping[(logical_id, role)]
        row = runtime_by_id[unit_id]
        path = physical_prediction_path(config, unit_id)
        if sha256_file(path) != row["outer_prediction_hash"]:
            raise PredictionFreezeError("TASK038E_PHYSICAL_PREDICTION_HASH_MISMATCH")
        return load_binary(path)

    branch_selected = {
        (
            row["branch_id"],
            row["detector_variant"],
            row["kpi_id"],
            row["direction"],
        ): row
        for row in registry["records"]
        if row["evidence_block"] == "branch_selected"
    }
    branch_records: list[dict[str, Any]] = []
    for branch in ("A0", "A1", "A2", "A3"):
        for variant, kpi_id in sorted(detector_by_key):
            detector_row = detector_by_key[(variant, kpi_id)]
            detector_path = detector_prediction_path(config, variant, kpi_id)
            if sha256_file(detector_path) != detector_row["outer_prediction_hash"]:
                raise PredictionFreezeError("TASK038E_DETECTOR_OUTER_HASH_MISMATCH")
            detector = load_binary(detector_path)
            fn_record = branch_selected[(branch, variant, kpi_id, "FN")]
            fp_record = branch_selected[(branch, variant, kpi_id, "FP")]
            fn_rule = (
                prediction(fn_record["logical_record_id"], "selected")
                if fn_record["outer_execution_required"]
                else None
            )
            fp_rule = (
                prediction(fp_record["logical_record_id"], "selected")
                if fp_record["outer_execution_required"]
                else None
            )
            arms = compose_branch_arms(detector, fn_rule, fp_rule)
            for arm in ARMS:
                path = branch_arm_path(config, branch, variant, kpi_id, arm)
                digest = _save(path, arms[arm])
                branch_records.append(
                    {
                        "branch_id": branch,
                        "detector_variant": variant,
                        "kpi_id": kpi_id,
                        "arm": arm,
                        "outer_prediction_hash": digest,
                        "prediction_length": len(arms[arm]),
                        "predicted_positive_count": int(arms[arm].sum()),
                        "selected_FN_rule_hash_or_null": fn_record[
                            "selected_rule_hash"
                        ],
                        "selected_FP_rule_hash_or_null": fp_record[
                            "selected_rule_hash"
                        ],
                    }
                )
    review_records: list[dict[str, Any]] = []
    repair_records: list[dict[str, Any]] = []
    for row in registry["records"]:
        if row["evidence_block"] == "branch_selected":
            continue
        detector = load_binary(
            detector_prediction_path(
                config, row["detector_variant"], row["kpi_id"]
            )
        )
        if row["evidence_block"] == "review_transfer":
            parent_rule = prediction(row["logical_record_id"], "parent")
            reviewed_rule = prediction(row["logical_record_id"], "reviewed")
            parent_combined = compose_direction(
                detector, parent_rule, row["direction"]
            )
            reviewed_combined = compose_direction(
                detector, reviewed_rule, row["direction"]
            )
            parent_hash = _save(
                review_combined_path(config, row["logical_record_id"], "parent"),
                parent_combined,
            )
            reviewed_hash = _save(
                review_combined_path(config, row["logical_record_id"], "reviewed"),
                reviewed_combined,
            )
            review_records.append(
                {
                    "logical_record_id": row["logical_record_id"],
                    "branch_id": row["branch_id"],
                    "initial_slot_id": row["initial_slot_id"],
                    "detector_variant": row["detector_variant"],
                    "kpi_id": row["kpi_id"],
                    "direction": row["direction"],
                    "parent_rule_prediction_hash": runtime_by_id[
                        mapping[(row["logical_record_id"], "parent")]
                    ]["outer_prediction_hash"],
                    "reviewed_rule_prediction_hash": runtime_by_id[
                        mapping[(row["logical_record_id"], "reviewed")]
                    ]["outer_prediction_hash"],
                    "parent_combined_prediction_hash": parent_hash,
                    "reviewed_combined_prediction_hash": reviewed_hash,
                    "parent_predicted_positive_count": int(parent_combined.sum()),
                    "reviewed_predicted_positive_count": int(
                        reviewed_combined.sum()
                    ),
                    "selected_in_TASK038D": row["selected_in_TASK038D"],
                }
            )
        else:
            repaired_rule = prediction(row["logical_record_id"], "repaired")
            combined = compose_direction(detector, repaired_rule, row["direction"])
            digest = _save(
                repair_combined_path(config, row["logical_record_id"]), combined
            )
            repair_records.append(
                {
                    "logical_record_id": row["logical_record_id"],
                    "initial_slot_id": row["initial_slot_id"],
                    "detector_variant": row["detector_variant"],
                    "kpi_id": row["kpi_id"],
                    "direction": row["direction"],
                    "repaired_rule_prediction_hash": runtime_by_id[
                        mapping[(row["logical_record_id"], "repaired")]
                    ]["outer_prediction_hash"],
                    "combined_prediction_hash": digest,
                    "predicted_positive_count": int(combined.sum()),
                    "selected_in_A1": row["selected_in_A1"],
                    "selected_or_reviewed_in_A3": row[
                        "selected_or_reviewed_in_A3"
                    ],
                }
            )
    if (
        len(branch_records) != 320
        or len(review_records) != 76
        or len(repair_records) != 13
    ):
        raise PredictionFreezeError("TASK038E_PREDICTION_MATRIX_INCOMPLETE")
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "outer_prediction_freeze",
        "status": "all_outer_predictions_frozen_before_labels",
        "outer_execution_registry_hash": registry["report_hash"],
        "physical_execution_manifest_hash": physical["report_hash"],
        "outer_runtime_report_hash": runtime["report_hash"],
        "logical_branch_arm_predictions": len(branch_records),
        "review_transfer_pairs": len(review_records),
        "repair_utility_rules": len(repair_records),
        "all_outer_predictions_frozen_before_labels": True,
        "outer_labels_loaded": False,
        "selected_rule_substitution": False,
        "outer_reselection": False,
        "provider_calls": 0,
        "agent_calls": 0,
        "sealed_test_access": False,
        "raw_predictions_tracked": False,
        "branch_arm_records": branch_records,
        "review_transfer_records": review_records,
        "repair_utility_records": repair_records,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["prediction_freeze"]), report
    )


def verify_prediction_freeze(config: Mapping[str, Any]) -> dict[str, Any]:
    report = verify_hashed_report(ROOT / str(config["reports"]["prediction_freeze"]))
    if (
        report["status"] != "all_outer_predictions_frozen_before_labels"
        or not report["all_outer_predictions_frozen_before_labels"]
        or report["logical_branch_arm_predictions"] != 320
        or report["review_transfer_pairs"] != 76
        or report["repair_utility_rules"] != 13
    ):
        raise PredictionFreezeError("TASK038E_OUTER_LABEL_GUARD_FAILED")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038e_outer_branch_comparison.json",
    )
    args = parser.parse_args()
    report = freeze_outer_predictions((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "branch_arms": report["logical_branch_arm_predictions"],
                "review_pairs": report["review_transfer_pairs"],
                "repair_rules": report["repair_utility_rules"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
