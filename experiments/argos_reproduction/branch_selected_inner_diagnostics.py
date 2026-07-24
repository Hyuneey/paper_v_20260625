"""Compute non-selecting inner diagnostics for frozen TASK-038D selections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.branch_candidate_predictions import (
    candidate_prediction_reference,
    detector_prediction_path,
    label_path,
    load_binary,
    verify_label_hash,
)
from experiments.argos_reproduction.branch_output_registry import (
    BranchRegistryError,
    ROOT,
    load_config,
)
from experiments.argos_reproduction.direct_event_metrics import direct_pa_free_metrics
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)


def _aggregate(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    metric_names = (
        "precision",
        "recall",
        "point_f1",
        "event_precision",
        "event_recall",
        "event_f1",
        "false_positive_points_per_10000_normal_points",
        "false_alarm_events_per_10000_points",
    )
    macro = {
        name: float(np.mean([float(row[name]) for row in records]))
        for name in metric_names
    }
    counts = {
        name: sum(int(row[name]) for row in records)
        for name in (
            "true_positive",
            "false_positive",
            "true_negative",
            "false_negative",
            "event_true_positive",
            "event_false_positive",
            "event_false_negative",
        )
    }
    tp, fp, fn = counts["true_positive"], counts["false_positive"], counts["false_negative"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    micro_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    counts["precision"] = precision
    counts["recall"] = recall
    counts["point_f1"] = micro_f1
    return {"macro": macro, "micro": counts}


def build_inner_diagnostics(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    selection = verify_hashed_report(ROOT / str(config["reports"]["selection_freeze"]))
    registry = verify_hashed_report(ROOT / str(config["reports"]["branch_registry"]))
    freeze = verify_hashed_report(ROOT / str(config["reports"]["candidate_predictions"]))
    registry_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in registry["records"]
    }
    detector_refs = {
        (row["detector_variant"], row["kpi_id"]): row
        for row in freeze["detector_records"]
    }
    selected = {
        (
            row["branch_id"],
            row["detector_variant"],
            row["kpi_id"],
            row["direction"],
        ): row
        for row in selection["records"]
    }
    records: list[dict[str, Any]] = []
    for branch in ("A0", "A1", "A2", "A3"):
        for variant, kpi_id in sorted(detector_refs):
            ref = detector_refs[(variant, kpi_id)]
            detector = load_binary(detector_prediction_path(config, variant, kpi_id))
            truth = verify_label_hash(label_path(config, kpi_id), ref["inner_label_hash"])
            fn_row = selected[(branch, variant, kpi_id, "FN")]
            fp_row = selected[(branch, variant, kpi_id, "FP")]
            fn = np.zeros_like(detector)
            fp = np.ones_like(detector)
            if fn_row["selected_initial_slot_id_or_null"] is not None:
                candidate = registry_by_key[
                    (branch, fn_row["selected_initial_slot_id_or_null"])
                ]
                fn = load_binary(candidate_prediction_reference(config, candidate)[1])
            if fp_row["selected_initial_slot_id_or_null"] is not None:
                candidate = registry_by_key[
                    (branch, fp_row["selected_initial_slot_id_or_null"])
                ]
                fp = load_binary(candidate_prediction_reference(config, candidate)[1])
            arms = {
                "detector_only": detector,
                "D_plus_FN": np.maximum(detector, fn),
                "D_plus_FP": np.minimum(detector, fp),
                "Full": np.maximum(np.minimum(detector, fp), fn),
            }
            for arm, prediction in arms.items():
                records.append(
                    {
                        "branch_id": branch,
                        "detector_variant": variant,
                        "kpi_id": kpi_id,
                        "arm": arm,
                        "metrics": direct_pa_free_metrics(truth, prediction),
                    }
                )
    summaries: dict[str, Any] = {}
    for branch in ("A0", "A1", "A2", "A3"):
        summaries[branch] = {}
        for arm in ("detector_only", "D_plus_FN", "D_plus_FP", "Full"):
            rows = [
                row["metrics"]
                for row in records
                if row["branch_id"] == branch and row["arm"] == arm
            ]
            summaries[branch][arm] = _aggregate(rows)
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038D",
        "artifact_type": "inner_selected_arm_diagnostics",
        "status": "selection_split_diagnostics_only",
        "selection_freeze_hash": selection["report_hash"],
        "diagnostics_used_for_selection": False,
        "joint_pair_search": False,
        "outer_generalization_evidence": False,
        "outer_access": False,
        "sealed_test_access": False,
        "branch_arm_summaries": summaries,
        "records": records,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["inner_diagnostics"]), report
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task038d_branch_selection.json")
    args = parser.parse_args()
    report = build_inner_diagnostics((ROOT / args.config).resolve())
    print(json.dumps({"status": report["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
