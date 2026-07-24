"""Run the frozen no-op-aware TASK-038D inner selection protocol."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.aggregator_contribution_accounting import (
    fn_direction_contribution,
    fp_direction_contribution,
)
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
from experiments.argos_reproduction.branch_prediction_freeze import (
    verify_prediction_freeze,
)
from experiments.argos_reproduction.direct_event_metrics import direct_pa_free_metrics
from experiments.argos_reproduction.directional_rule_selection import (
    selection_protocol_hash,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.paper_aligned_aggregator import (
    fn_compensation,
    fp_correction,
)
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)


NO_OP_ID = "NO_OP"


def _scientific_key(record: Mapping[str, Any], direction: str) -> tuple[Any, ...]:
    metrics = record["combined_metrics"]
    contribution = record["directional_contribution_counts"]
    if direction == "FN":
        return (
            -float(metrics["point_f1"]),
            -float(metrics["event_f1"]),
            -int(contribution["FN_points_recovered"]),
            float(contribution["added_FP_per_10000_normal_points"]),
            int(contribution["added_false_alarm_events"]),
        )
    if direction == "FP":
        return (
            -float(metrics["point_f1"]),
            -float(metrics["event_f1"]),
            -int(contribution["FP_points_removed"]),
            int(contribution["true_positive_points_removed"]),
            int(contribution["true_anomaly_events_removed"]),
        )
    raise BranchRegistryError("TASK038D_DIRECTION_INVALID")


def selection_order(record: Mapping[str, Any], direction: str) -> tuple[Any, ...]:
    return (
        *_scientific_key(record, direction),
        str(record.get("rule_hash") or "~NO_OP"),
        str(record.get("initial_slot_id") or "~NO_OP"),
    )


def select_candidate(
    candidates: Sequence[Mapping[str, Any]], direction: str
) -> Mapping[str, Any]:
    noops = [row for row in candidates if row["candidate_type"] == "no_op"]
    if len(noops) != 1:
        raise BranchRegistryError("TASK038D_EXPLICIT_NOOP_REQUIRED")
    best = min(candidates, key=lambda row: selection_order(row, direction))
    noop = noops[0]
    if _scientific_key(best, direction) == _scientific_key(noop, direction):
        return noop
    return best


def candidate_metrics(
    *,
    direction: str,
    detector: np.ndarray,
    truth: np.ndarray,
    candidate: Mapping[str, Any] | None,
    prediction: np.ndarray | None,
) -> dict[str, Any]:
    if candidate is None:
        combined = detector.copy()
    elif direction == "FN":
        combined = fn_compensation(detector, prediction)
    else:
        combined = fp_correction(detector, prediction)
    metrics = direct_pa_free_metrics(truth, combined)
    contribution = (
        fn_direction_contribution(truth, detector, combined)
        if direction == "FN"
        else fp_direction_contribution(truth, detector, combined)
    )
    return {
        "candidate_type": "no_op" if candidate is None else "branch_rule",
        "initial_slot_id": None if candidate is None else candidate["initial_slot_id"],
        "rule_hash": None if candidate is None else candidate["output_rule_hash"],
        "output_origin": None if candidate is None else candidate["output_origin"],
        "candidate_record": candidate,
        "combined_metrics": metrics,
        "directional_contribution_counts": contribution,
        "combined_prediction_hash": sha256_json(combined.tolist()),
        "_combined": combined,
    }


def _protocol_hash(config: Mapping[str, Any]) -> str:
    task037e = read_json(ROOT / str(config["sources"]["task037e_config"]))
    return selection_protocol_hash(task037e)


def _load_labels(
    config: Mapping[str, Any],
    prediction_freeze: Mapping[str, Any],
) -> dict[str, np.ndarray]:
    if (
        prediction_freeze["status"] != "frozen_before_inner_label_access"
        or not prediction_freeze["all_candidate_predictions_frozen_before_labels"]
    ):
        raise BranchRegistryError("TASK038D_LABEL_GUARD_FAILED")
    expected = {
        row["kpi_id"]: row["inner_label_hash"]
        for row in prediction_freeze["detector_records"]
    }
    if len(expected) != 10:
        raise BranchRegistryError("TASK038D_LABEL_LINEAGE_INCOMPLETE")
    return {
        kpi_id: verify_label_hash(label_path(config, kpi_id), digest)
        for kpi_id, digest in sorted(expected.items())
    }


def _assert_a0_reproduction(
    config: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    protocol_hash: str,
) -> dict[str, Any]:
    expected: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for source, hash_name in (
        ("task037e_fn_selection", "task037e_fn_selection"),
        ("task037e_fp_selection", "task037e_fp_selection"),
    ):
        report = verify_hashed_report(
            ROOT / str(config["sources"][source]),
            str(config["source_hashes"][hash_name]),
        )
        for row in report["records"]:
            expected[(row["detector_variant"], row["kpi_id"], row["direction"])] = row
    comparisons: list[dict[str, Any]] = []
    for row in records:
        key = (row["detector_variant"], row["kpi_id"], row["direction"])
        frozen = expected[key]
        selected_type = (
            "executable_rule"
            if row["selected_candidate_type"] == "branch_rule"
            else "no_op"
        )
        matched = (
            selected_type == frozen["selected_candidate_type"]
            and row["selected_rule_hash_or_null"] == frozen["selected_rule_hash"]
            and row["selected_initial_slot_id_or_null"] == frozen["selected_slot_id"]
            and protocol_hash == frozen["selection_protocol_hash"]
        )
        comparisons.append(
            {
                "detector_variant": key[0],
                "kpi_id": key[1],
                "direction": key[2],
                "selected_candidate_type_matches": selected_type
                == frozen["selected_candidate_type"],
                "selected_rule_hash_matches": row["selected_rule_hash_or_null"]
                == frozen["selected_rule_hash"],
                "selected_slot_id_matches": row["selected_initial_slot_id_or_null"]
                == frozen["selected_slot_id"],
                "selection_protocol_hash_matches": protocol_hash
                == frozen["selection_protocol_hash"],
                "exact_match": matched,
            }
        )
    exact = len(comparisons) == 40 and all(row["exact_match"] for row in comparisons)
    if not exact:
        raise BranchRegistryError("TASK038D_A0_SELECTION_REPRODUCTION_FAILED")
    return {
        "schema_version": "1.0",
        "task_id": "TASK-038D",
        "artifact_type": "A0_selection_reproduction_report",
        "status": "exact_reproduction_passed",
        "selection_unit_count": 40,
        "exact_match_count": 40,
        "A0_exact_selection_reproduction": True,
        "A0_FN_rule_selected_count": sum(
            row["direction"] == "FN"
            and row["selected_candidate_type"] == "branch_rule"
            for row in records
        ),
        "A0_FN_no_op_count": sum(
            row["direction"] == "FN"
            and row["selected_candidate_type"] == "no_op"
            for row in records
        ),
        "A0_FP_rule_selected_count": sum(
            row["direction"] == "FP"
            and row["selected_candidate_type"] == "branch_rule"
            for row in records
        ),
        "A0_FP_no_op_count": sum(
            row["direction"] == "FP"
            and row["selected_candidate_type"] == "no_op"
            for row in records
        ),
        "outer_access": False,
        "sealed_test_access": False,
        "records": comparisons,
    }


def run_branch_selection(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    freeze = verify_prediction_freeze(config)
    registry = verify_hashed_report(ROOT / str(config["reports"]["branch_registry"]))
    labels = _load_labels(config, freeze)
    protocol_hash = _protocol_hash(config)
    candidates_by_unit: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in registry["records"]:
        candidates_by_unit[
            (
                row["branch_id"],
                row["detector_variant"],
                row["kpi_id"],
                row["direction"],
            )
        ].append(row)
    detector_refs = {
        (row["detector_variant"], row["kpi_id"]): row
        for row in freeze["detector_records"]
    }
    records: list[dict[str, Any]] = []
    private_candidates: list[dict[str, Any]] = []
    for branch in ("A0", "A1", "A2", "A3"):
        for variant, kpi_id in sorted(detector_refs):
            detector = load_binary(detector_prediction_path(config, variant, kpi_id))
            truth = labels[kpi_id]
            if detector.shape != truth.shape:
                raise BranchRegistryError("TASK038D_DETECTOR_LABEL_LENGTH_MISMATCH")
            for direction in ("FN", "FP"):
                unit = candidates_by_unit.get((branch, variant, kpi_id, direction), [])
                metrics = [
                    candidate_metrics(
                        direction=direction,
                        detector=detector,
                        truth=truth,
                        candidate=None,
                        prediction=None,
                    )
                ]
                for candidate in unit:
                    _, path = candidate_prediction_reference(config, candidate)
                    prediction = load_binary(path)
                    if prediction.shape != detector.shape:
                        raise BranchRegistryError("TASK038D_CANDIDATE_LENGTH_MISMATCH")
                    metrics.append(
                        candidate_metrics(
                            direction=direction,
                            detector=detector,
                            truth=truth,
                            candidate=candidate,
                            prediction=prediction,
                        )
                    )
                selected = select_candidate(metrics, direction)
                candidate = selected["candidate_record"]
                records.append(
                    {
                        "branch_id": branch,
                        "detector_variant": variant,
                        "kpi_id": kpi_id,
                        "direction": direction,
                        "candidate_record_count": len(unit),
                        "available_candidate_count": len(unit),
                        "unavailable_candidate_count": 0,
                        "explicit_no_op_present": True,
                        "selected_candidate_type": selected["candidate_type"],
                        "selected_output_origin": selected["output_origin"],
                        "selected_initial_slot_id_or_null": selected["initial_slot_id"],
                        "selected_initial_rule_hash_or_null": None
                        if candidate is None
                        else candidate["initial_rule_hash"],
                        "selected_parent_rule_hash_or_null": None
                        if candidate is None
                        else candidate["parent_rule_hash"],
                        "selected_rule_hash_or_null": selected["rule_hash"],
                        "selected_inner_metrics": selected["combined_metrics"],
                        "selected_directional_contribution": selected[
                            "directional_contribution_counts"
                        ],
                        "selected_prediction_hash": selected[
                            "combined_prediction_hash"
                        ],
                        "selection_protocol_hash": protocol_hash,
                    }
                )
                private_candidates.append(
                    {
                        "branch_id": branch,
                        "detector_variant": variant,
                        "kpi_id": kpi_id,
                        "direction": direction,
                        "candidates": [
                            {key: value for key, value in item.items() if not key.startswith("_") and key != "candidate_record"}
                            for item in metrics
                        ],
                    }
                )
        if branch == "A0":
            a0 = _assert_a0_reproduction(config, records, protocol_hash)
            write_hashed_report(
                ROOT / str(config["reports"]["a0_reproduction"]), a0
            )
    if len(records) != int(config["counts"]["selection_units"]):
        raise BranchRegistryError("TASK038D_SELECTION_UNIT_COUNT_MISMATCH")
    private = {
        "schema_version": "1.0",
        "artifact_type": "task038d_private_candidate_metrics",
        "candidate_prediction_manifest_hash": freeze["report_hash"],
        "records": private_candidates,
    }
    private["report_hash"] = sha256_json(private)
    write_json(
        ROOT
        / str(config["private_roots"]["task038d"])
        / "selection_metrics"
        / "candidate_metrics.private.json",
        private,
    )
    summary: dict[str, Any] = {}
    for branch in ("A0", "A1", "A2", "A3"):
        rows = [row for row in records if row["branch_id"] == branch]
        summary[branch] = {
            "FN_rule_selected_count": sum(
                row["direction"] == "FN"
                and row["selected_candidate_type"] == "branch_rule"
                for row in rows
            ),
            "FN_no_op_count": sum(
                row["direction"] == "FN"
                and row["selected_candidate_type"] == "no_op"
                for row in rows
            ),
            "FP_rule_selected_count": sum(
                row["direction"] == "FP"
                and row["selected_candidate_type"] == "branch_rule"
                for row in rows
            ),
            "FP_no_op_count": sum(
                row["direction"] == "FP"
                and row["selected_candidate_type"] == "no_op"
                for row in rows
            ),
        }
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038D",
        "artifact_type": "branch_selection_freeze",
        "status": "passed_four_branch_selection_freeze",
        "candidate_prediction_manifest_hash": freeze["report_hash"],
        "selection_protocol_hash": protocol_hash,
        "selection_unit_count": len(records),
        "branch_summaries": summary,
        "A0_exact_selection_reproduction": True,
        "all_selection_units_terminal": True,
        "FN_FP_selected_independently": True,
        "explicit_no_op_present": True,
        "joint_pair_search": False,
        "provider_calls": 0,
        "agent_calls": 0,
        "outer_access": False,
        "sealed_test_access": False,
        "records": records,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["selection_freeze"]), report
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038d_branch_selection.json",
    )
    args = parser.parse_args()
    report = run_branch_selection((ROOT / args.config).resolve())
    print(json.dumps(report["branch_summaries"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
