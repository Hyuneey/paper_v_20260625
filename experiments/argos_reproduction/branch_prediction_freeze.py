"""Freeze all TASK-038D candidate prediction references before label access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from experiments.argos_reproduction.branch_candidate_predictions import (
    candidate_prediction_reference,
    verify_detector_references,
)
from experiments.argos_reproduction.branch_output_registry import (
    BranchRegistryError,
    ROOT,
    load_config,
)
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)


def freeze_candidate_predictions(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    registry = verify_hashed_report(ROOT / str(config["reports"]["branch_registry"]))
    if (
        registry["status"] != "branch_outputs_frozen_before_inner_label_access"
        or registry["labels_loaded"]
        or registry["total_branch_executable_output_records"]
        != int(config["counts"]["branch_executable_outputs"])
    ):
        raise BranchRegistryError("TASK038D_BRANCH_REGISTRY_NOT_FROZEN")
    records = [
        candidate_prediction_reference(config, row)[0]
        for row in registry["records"]
    ]
    detector_records = verify_detector_references(config)
    if len(records) != int(config["counts"]["branch_executable_outputs"]):
        raise BranchRegistryError("TASK038D_CANDIDATE_PREDICTION_COUNT_MISMATCH")
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038D",
        "artifact_type": "candidate_prediction_manifest",
        "status": "frozen_before_inner_label_access",
        "branch_output_registry_hash": registry["report_hash"],
        "candidate_prediction_record_count": len(records),
        "detector_prediction_record_count": len(detector_records),
        "all_candidate_predictions_frozen_before_labels": True,
        "labels_loaded_during_freeze": False,
        "prediction_recovery_attempted": False,
        "prediction_recovery_hash_mismatch_count": 0,
        "raw_predictions_tracked": False,
        "outer_access": False,
        "sealed_test_access": False,
        "detector_records": detector_records,
        "records": records,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["candidate_predictions"]), report
    )


def verify_prediction_freeze(config: Mapping[str, Any]) -> dict[str, Any]:
    report = verify_hashed_report(ROOT / str(config["reports"]["candidate_predictions"]))
    if (
        report["status"] != "frozen_before_inner_label_access"
        or not report["all_candidate_predictions_frozen_before_labels"]
        or report["candidate_prediction_record_count"]
        != int(config["counts"]["branch_executable_outputs"])
    ):
        raise BranchRegistryError("TASK038D_CANDIDATE_FREEZE_INCOMPLETE")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038d_branch_selection.json",
    )
    args = parser.parse_args()
    report = freeze_candidate_predictions((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "candidate_predictions": report["candidate_prediction_record_count"],
                "detectors": report["detector_prediction_record_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
