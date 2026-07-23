"""Independent no-op-aware FN and FP inner selection for TASK-037E."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.aggregator_contribution_accounting import (
    fn_direction_contribution,
    fp_direction_contribution,
)
from experiments.argos_reproduction.direct_event_metrics import direct_pa_free_metrics
from experiments.argos_reproduction.error_rule_full_inner_runtime import (
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.paper_aligned_aggregator import (
    fn_compensation,
    fp_correction,
    prediction_degeneracy,
)


class DirectionalSelectionError(RuntimeError):
    """Raised when TASK-037E selection violates its frozen boundary."""


NO_OP_ID = "NO_OP"


def selection_protocol_hash(config: Mapping[str, Any]) -> str:
    return sha256_json(config["selection_policy"])


def fn_selection_order(record: Mapping[str, Any]) -> tuple[Any, ...]:
    metrics = record["combined_metrics"]
    contribution = record["directional_contribution_counts"]
    return (
        -float(metrics["point_f1"]),
        -float(metrics["event_f1"]),
        -int(contribution["FN_points_recovered"]),
        float(contribution["added_FP_per_10000_normal_points"]),
        int(contribution["added_false_alarm_events"]),
        str(record["candidate_id"]),
    )


def fp_selection_order(record: Mapping[str, Any]) -> tuple[Any, ...]:
    metrics = record["combined_metrics"]
    contribution = record["directional_contribution_counts"]
    return (
        -float(metrics["point_f1"]),
        -float(metrics["event_f1"]),
        -int(contribution["FP_points_removed"]),
        int(contribution["true_positive_points_removed"]),
        int(contribution["true_anomaly_events_removed"]),
        str(record["candidate_id"]),
    )


def _metric_tie_key(record: Mapping[str, Any], direction: str) -> tuple[Any, ...]:
    order = fn_selection_order(record) if direction == "FN" else fp_selection_order(record)
    return order[:-1]


def select_direction_candidate(
    candidates: Sequence[Mapping[str, Any]], direction: str
) -> Mapping[str, Any]:
    if direction not in ("FN", "FP"):
        raise DirectionalSelectionError("TASK037E_DIRECTION_INVALID")
    if sum(item["candidate_type"] == "no_op" for item in candidates) != 1:
        raise DirectionalSelectionError("TASK037E_NOOP_CANDIDATE_REQUIRED")
    ordered = sorted(
        candidates,
        key=fn_selection_order if direction == "FN" else fp_selection_order,
    )
    best = ordered[0]
    noop = next(item for item in candidates if item["candidate_type"] == "no_op")
    return noop if _metric_tie_key(best, direction) == _metric_tie_key(noop, direction) else best


def _private_prediction_path(
    config: Mapping[str, Any], slot_id: str, split: str
) -> Path:
    return (
        ROOT
        / config["private_roots"]["task037e"]
        / split
        / "rule_predictions"
        / slot_id
        / "replay_1"
        / "output_labels.npy"
    )


def _detector_prediction_path(
    config: Mapping[str, Any], variant: str, kpi_id: str, split: str
) -> Path:
    if split not in ("inner", "outer"):
        raise DirectionalSelectionError("TASK037E_DETECTOR_SPLIT_NOT_ALLOWED")
    return (
        ROOT
        / config["private_roots"]["task037b"]
        / "detectors"
        / variant
        / kpi_id
        / "20260723"
        / "predictions"
        / f"{split}_prediction.npy"
    )


def _label_path(config: Mapping[str, Any], kpi_id: str, split: str) -> Path:
    if split not in ("inner", "outer"):
        raise DirectionalSelectionError("TASK037E_LABEL_SPLIT_NOT_ALLOWED")
    return (
        ROOT
        / config["private_roots"]["task035b"]
        / split
        / "per_kpi_labels"
        / f"{kpi_id}.npy"
    )


def _load_binary(path: Path) -> np.ndarray:
    value = np.asarray(np.load(path, allow_pickle=False))
    if value.ndim != 1 or not np.all(np.isfinite(value)) or not np.all(np.isin(value, (0, 1))):
        raise DirectionalSelectionError("TASK037E_BINARY_ARTIFACT_INVALID")
    return value.astype(np.int8, copy=True)


def _verify_complete_inner_freeze(
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]]]:
    manifest = verify_hashed_report(ROOT / config["reports"]["inner_predictions"])
    if (
        manifest["record_count"] != int(config["expected_executable_rule_count"])
        or not manifest["all_83_inner_rule_attempts_have_terminal_status"]
        or manifest["status"] != "frozen_before_inner_label_access"
    ):
        raise DirectionalSelectionError("TASK037E_INNER_PREDICTION_FREEZE_INCOMPLETE")
    for record in manifest["records"]:
        if not record["deterministic_replay_passed"]:
            continue
        prediction = _private_prediction_path(config, record["slot_id"], "inner")
        if not prediction.is_file() or sha256_file(prediction) != record["inner_prediction_hash"]:
            raise DirectionalSelectionError("TASK037E_INNER_PREDICTION_HASH_MISMATCH")
    detector_manifest = verify_hashed_report(
        ROOT / config["sources"]["task037b_detector_manifest"]
    )
    detector_records = {
        (item["detector_variant"], item["kpi_id"]): item
        for item in detector_manifest["records"]
    }
    if len(detector_records) != 20:
        raise DirectionalSelectionError("TASK037E_DETECTOR_UNIT_COUNT_MISMATCH")
    for key, item in detector_records.items():
        path = _detector_prediction_path(config, key[0], key[1], "inner")
        if not path.is_file() or sha256_file(path) != item["inner_prediction_hash"]:
            raise DirectionalSelectionError("TASK037E_DETECTOR_INNER_HASH_MISMATCH")
    return manifest, detector_records


def load_inner_labels_after_freeze(
    config: Mapping[str, Any],
    manifest: Mapping[str, Any],
    detector_records: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, np.ndarray]:
    if (
        manifest.get("status") != "frozen_before_inner_label_access"
        or manifest.get("record_count") != int(config["expected_executable_rule_count"])
    ):
        raise DirectionalSelectionError("TASK037E_LABEL_GUARD_FAILED")
    threshold = verify_hashed_report(ROOT / config["sources"]["task037b_threshold_freeze"])
    label_hashes = {item["kpi_id"]: item["inner_label_hash"] for item in threshold["records"]}
    if len(label_hashes) != 10 or len(detector_records) != 20:
        raise DirectionalSelectionError("TASK037E_INNER_LABEL_LINEAGE_INCOMPLETE")
    labels: dict[str, np.ndarray] = {}
    for kpi_id, expected_hash in sorted(label_hashes.items()):
        path = _label_path(config, kpi_id, "inner")
        value = _load_binary(path)
        if hashlib.sha256(value.tobytes()).hexdigest() != expected_hash:
            raise DirectionalSelectionError("TASK037E_INNER_LABEL_HASH_MISMATCH")
        labels[kpi_id] = value
    return labels


def _candidate_record(
    *,
    direction: str,
    detector: np.ndarray,
    truth: np.ndarray,
    rule: np.ndarray | None,
    candidate_id: str,
    slot_id: str | None,
    rule_hash: str | None,
) -> dict[str, Any]:
    combined = (
        detector.copy()
        if rule is None
        else (
            fn_compensation(detector, rule)
            if direction == "FN"
            else fp_correction(detector, rule)
        )
    )
    metrics = direct_pa_free_metrics(truth, combined)
    metrics["combined_FP_per_10000"] = metrics[
        "false_positive_points_per_10000_normal_points"
    ]
    contribution = (
        fn_direction_contribution(truth, detector, combined)
        if direction == "FN"
        else fp_direction_contribution(truth, detector, combined)
    )
    return {
        "candidate_id": candidate_id,
        "candidate_type": "no_op" if rule is None else "executable_rule",
        "rule_hash": rule_hash,
        "slot_id": slot_id,
        "combined_metrics": metrics,
        "directional_contribution_counts": contribution,
        "prediction_hash": sha256_json(combined.tolist()),
        "degeneracy": prediction_degeneracy(combined, detector=detector),
    }


def run_directional_selection(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    manifest, detector_records = _verify_complete_inner_freeze(config)
    labels = load_inner_labels_after_freeze(config, manifest, detector_records)
    candidates_by_unit: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for record in manifest["records"]:
        if record["deterministic_replay_passed"]:
            key = (record["detector_variant"], record["kpi_id"], record["direction"])
            candidates_by_unit.setdefault(key, []).append(record)
    selected_by_direction: dict[str, list[dict[str, Any]]] = {"FN": [], "FP": []}
    private_candidates: list[dict[str, Any]] = []
    protocol_hash = selection_protocol_hash(config)
    for (variant, kpi_id), detector_record in sorted(detector_records.items()):
        detector = _load_binary(_detector_prediction_path(config, variant, kpi_id, "inner"))
        truth = labels[kpi_id]
        if detector.shape != truth.shape:
            raise DirectionalSelectionError("TASK037E_INNER_LENGTH_MISMATCH")
        detector_metrics = direct_pa_free_metrics(truth, detector)
        for direction in ("FN", "FP"):
            unit_records = candidates_by_unit.get((variant, kpi_id, direction), [])
            candidate_metrics = [
                _candidate_record(
                    direction=direction,
                    detector=detector,
                    truth=truth,
                    rule=None,
                    candidate_id=NO_OP_ID,
                    slot_id=None,
                    rule_hash=None,
                )
            ]
            for record in unit_records:
                rule_prediction = _load_binary(
                    _private_prediction_path(config, record["slot_id"], "inner")
                )
                candidate_metrics.append(
                    _candidate_record(
                        direction=direction,
                        detector=detector,
                        truth=truth,
                        rule=rule_prediction,
                        candidate_id=record["rule_sha256"],
                        slot_id=record["slot_id"],
                        rule_hash=record["rule_sha256"],
                    )
                )
            selected = select_direction_candidate(candidate_metrics, direction)
            tracked = {
                "detector_variant": variant,
                "kpi_id": kpi_id,
                "direction": direction,
                "candidate_rule_count": len(unit_records),
                "eligible_rule_count": len(unit_records),
                "selected_candidate_type": selected["candidate_type"],
                "selected_rule_hash": selected["rule_hash"],
                "selected_slot_id": selected["slot_id"],
                "inner_detector_metrics": detector_metrics,
                "inner_combined_metrics": selected["combined_metrics"],
                "directional_contribution_counts": selected[
                    "directional_contribution_counts"
                ],
                "selected_rule_degeneracy": selected["degeneracy"],
                "selection_protocol_hash": protocol_hash,
            }
            selected_by_direction[direction].append(tracked)
            private_candidates.append(
                {
                    "detector_variant": variant,
                    "kpi_id": kpi_id,
                    "direction": direction,
                    "candidates": candidate_metrics,
                    "selected_candidate_id": selected["candidate_id"],
                }
            )
    private_report = {
        "schema_version": "1.0",
        "artifact_type": "task037e_private_candidate_metrics",
        "inner_prediction_manifest_hash": manifest["report_hash"],
        "records": private_candidates,
    }
    private_report["report_hash"] = sha256_json(private_report)
    write_json(
        ROOT
        / config["private_roots"]["task037e"]
        / "inner"
        / "candidate_metrics.private.json",
        private_report,
    )
    reports: dict[str, Any] = {}
    for direction in ("FN", "FP"):
        records = selected_by_direction[direction]
        report = {
            "schema_version": "1.0",
            "task_id": "TASK-037E",
            "artifact_type": f"{direction.lower()}_selection_freeze",
            "status": "selection_frozen_before_outer_access",
            "direction": direction,
            "selection_unit_count": len(records),
            "records": records,
            "selection_protocol_hash": protocol_hash,
            "inner_prediction_manifest_hash": manifest["report_hash"],
            "rule_selected_count": sum(
                item["selected_candidate_type"] == "executable_rule" for item in records
            ),
            "no_op_selected_count": sum(
                item["selected_candidate_type"] == "no_op" for item in records
            ),
            "FN_FP_selected_independently": True,
            "joint_pair_search_performed": False,
            "outer_metrics_seen": False,
            "test_accessed": False,
            "outer_exposure_limitation": config["outer_exposure_limitation"],
        }
        reports[direction] = write_hashed_report(
            ROOT
            / config["reports"][
                "fn_selection" if direction == "FN" else "fp_selection"
            ],
            report,
        )
    lines = [
        "# TASK-037E Inner Selection Report",
        "",
        "FN and FP rules were selected independently on the frozen inner partition.",
        "Every detector/KPI/direction unit included a no-op candidate.",
        "",
        f"- FN rule selected: {reports['FN']['rule_selected_count']}",
        f"- FN no-op selected: {reports['FN']['no_op_selected_count']}",
        f"- FP rule selected: {reports['FP']['rule_selected_count']}",
        f"- FP no-op selected: {reports['FP']['no_op_selected_count']}",
        "- Joint FN/FP pair search: not performed",
        "- Outer metrics seen during selection: false",
        "- Sealed-test access: false",
        "",
        config["outer_exposure_limitation"],
        "",
    ]
    (ROOT / config["reports"]["selection_markdown"]).write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037e_error_conditioned_aggregator.json",
    )
    args = parser.parse_args()
    reports = run_directional_selection((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                direction: {
                    "rule": report["rule_selected_count"],
                    "no_op": report["no_op_selected_count"],
                }
                for direction, report in reports.items()
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
