"""Compute frozen inner-only TASK-038C Review triggers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.direct_event_metrics import (
    binary_vector,
    direct_pa_free_metrics,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_file,
)
from experiments.argos_reproduction.review_parent_prediction_freeze import (
    verify_parent_prediction_freeze,
)
from experiments.argos_reproduction.review_parent_registry import (
    detector_prediction_path,
    inner_labels_path,
    inner_values_path,
    prediction_path,
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.review_regression_evidence import (
    freeze_regression_evidence,
)
from experiments.argos_reproduction.review_regression_samples import (
    compose_direction,
)


def _load_binary(path: Path) -> np.ndarray:
    return binary_vector(np.load(path, allow_pickle=False), path.stem)


def _metric_projection(metrics: Mapping[str, Any]) -> dict[str, float]:
    return {
        "precision": float(metrics["precision"]),
        "recall": float(metrics["recall"]),
        "point_f1": float(metrics["point_f1"]),
        "event_f1": float(metrics["event_f1"]),
        "fp_per_10000": float(
            metrics["false_positive_points_per_10000_normal_points"]
        ),
    }


def compute_review_triggers(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    manifest = verify_parent_prediction_freeze(config)
    detector_manifest = verify_hashed_report(
        ROOT / str(config["sources"]["task037b_detector_manifest"]),
        str(config["source_hashes"]["task037b_detector_manifest"]),
    )
    threshold = verify_hashed_report(
        ROOT / str(config["sources"]["task037b_threshold_freeze"]),
        str(config["source_hashes"]["task037b_threshold_freeze"]),
    )
    detector_by_key = {
        (row["detector_variant"], row["kpi_id"]): row
        for row in detector_manifest["records"]
    }
    label_hash_by_key = {
        (row["detector_variant"], row["kpi_id"]): row["inner_label_hash"]
        for row in threshold["records"]
    }
    private_root = ROOT / str(config["private_roots"]["task038c"])
    records: list[dict[str, Any]] = []
    for row in sorted(
        manifest["records"],
        key=lambda item: (
            0 if item["branch_id"] == "A2" else 1,
            item["initial_slot_id"],
        ),
    ):
        key = (row["detector_variant"], row["kpi_id"])
        detector_record = detector_by_key[key]
        detector_path = detector_prediction_path(config, *key)
        if sha256_file(detector_path) != detector_record["inner_prediction_hash"]:
            raise RuntimeError("TASK038C_DETECTOR_PREDICTION_HASH_MISMATCH")
        detector = _load_binary(detector_path)
        parent_path = prediction_path(config, row)
        parent = _load_binary(parent_path)
        label_path = inner_labels_path(config, str(row["kpi_id"]))
        labels = _load_binary(label_path)
        if (
            hashlib.sha256(labels.tobytes()).hexdigest()
            != label_hash_by_key[key]
        ):
            raise RuntimeError("TASK038C_INNER_LABEL_HASH_MISMATCH")
        if not (detector.shape == parent.shape == labels.shape):
            raise RuntimeError("TASK038C_INNER_LENGTH_MISMATCH")
        combined = np.asarray(
            compose_direction(detector, parent, str(row["direction"])),
            dtype=np.int8,
        )
        detector_metrics = direct_pa_free_metrics(labels, detector)
        parent_metrics = direct_pa_free_metrics(labels, combined)
        required = float(parent_metrics["point_f1"]) < float(
            detector_metrics["point_f1"]
        )
        branch_key = f"{row['branch_id']}-{row['initial_slot_id']}"
        combined_path = private_root / "triggers" / branch_key / "combined.npy"
        combined_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(combined_path, combined, allow_pickle=False)
        regression_path = (
            private_root
            / "regression_evidence"
            / f"{branch_key}.private.json"
        )
        if required:
            values = np.asarray(
                np.load(
                    inner_values_path(config, str(row["kpi_id"])),
                    allow_pickle=False,
                ),
                dtype=np.float64,
            ).reshape(-1)
            samples, evidence_hash = freeze_regression_evidence(
                output_path=regression_path,
                values=values,
                labels=labels,
                detector_predictions=detector,
                rule_predictions=parent,
                direction=str(row["direction"]),
            )
        else:
            samples = ()
            evidence_hash = hashlib.sha256(b"no_review_needed").hexdigest()
        records.append(
            {
                **row,
                "branch_key": branch_key,
                "detector_prediction_hash": detector_record[
                    "inner_prediction_hash"
                ],
                "inner_label_hash": label_hash_by_key[key],
                "parent_combined_prediction_hash": sha256_file(combined_path),
                "detector_metrics": _metric_projection(detector_metrics),
                "parent_combined_metrics": _metric_projection(parent_metrics),
                "review_trigger": (
                    "review_required" if required else "no_review_needed"
                ),
                "regression_window_count": len(samples),
                "regression_evidence_hash": evidence_hash,
            }
        )
    review_required = sum(
        row["review_trigger"] == "review_required" for row in records
    )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "review_trigger_report",
        "status": "triggers_frozen",
        "parent_prediction_manifest_hash": manifest["report_hash"],
        "total_branch_parents": len(records),
        "review_required_count": review_required,
        "no_review_needed_count": len(records) - review_required,
        "A2_review_required_count": sum(
            row["branch_id"] == "A2"
            and row["review_trigger"] == "review_required"
            for row in records
        ),
        "A3_review_required_count": sum(
            row["branch_id"] == "A3"
            and row["review_trigger"] == "review_required"
            for row in records
        ),
        "point_adjustment": False,
        "trigger_metric": "direct_PA_free_point_F1",
        "outer_access": False,
        "sealed_test_access": False,
        "raw_regression_evidence_tracked": False,
        "records": records,
    }
    return write_hashed_report(ROOT / str(config["reports"]["trigger"]), report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    report = compute_review_triggers((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "parents": report["total_branch_parents"],
                "review_required": report["review_required_count"],
                "no_review_needed": report["no_review_needed_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
