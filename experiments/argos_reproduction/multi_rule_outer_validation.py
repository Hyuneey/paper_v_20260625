"""Outer-only aggregation helpers for frozen TASK-035B arms."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.direct_event_metrics import direct_pa_free_metrics, metric_distribution
from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, git_clean_commit, read_json, sha256_file, sha256_json, write_json
from experiments.argos_reproduction.multi_rule_full_window_runtime import deterministic_replay_matches, execute_full_window_rule, load_private_prediction
from experiments.argos_reproduction.multi_rule_runtime import inspect_image, isolation_probe
from experiments.argos_reproduction.multi_rule_validation_common import frozen_executable_cohort, save_values_only_split, verified_report
from experiments.argos_reproduction.paired_kpi_bootstrap import bootstrap_comparisons


METRIC_FIELDS = (
    "precision", "recall", "point_f1", "event_precision", "event_recall", "event_f1",
    "false_positive_points_per_10000_normal_points", "false_alarm_events_per_10000_points",
)


def summarize_outer_metrics(per_kpi: Mapping[str, Mapping[str, Mapping[str, Any]]]) -> dict[str, Any]:
    if len(per_kpi) != 10:
        raise ValueError("TASK035B_OUTER_REQUIRES_TEN_KPIS")
    arms = ("best_1", "top_3_or", "coverage_3_or", "all_10_or")
    result: dict[str, Any] = {}
    for arm in arms:
        records = [per_kpi[kpi][arm] for kpi in sorted(per_kpi)]
        point_counts = {name: sum(int(record[name]) for record in records) for name in ("true_positive", "false_positive", "true_negative", "false_negative")}
        event_counts = {name: sum(int(record[name]) for record in records) for name in ("event_true_positive", "event_false_positive", "event_false_negative")}
        micro_point = direct_pa_free_metrics_from_counts(point_counts, event_counts)
        result[arm] = {
            "macro": {field: sum(float(record[field]) for record in records) / len(records) for field in METRIC_FIELDS},
            "micro": {**point_counts, **event_counts, **micro_point},
            "distribution": {field: metric_distribution(records, field) for field in METRIC_FIELDS},
        }
    return result


def direct_pa_free_metrics_from_counts(point: Mapping[str, int], event: Mapping[str, int]) -> dict[str, float]:
    tp, fp, tn, fn = (point[name] for name in ("true_positive", "false_positive", "true_negative", "false_negative"))
    ep, efp, efn = (event[name] for name in ("event_true_positive", "event_false_positive", "event_false_negative"))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    event_precision = ep / (ep + efp) if ep + efp else 0.0
    event_recall = ep / (ep + efn) if ep + efn else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "point_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "event_precision": event_precision,
        "event_recall": event_recall,
        "event_f1": 2 * event_precision * event_recall / (event_precision + event_recall) if event_precision + event_recall else 0.0,
        "false_positive_points_per_10000_normal_points": fp / (fp + tn) * 10000 if fp + tn else 0.0,
    }


def validate_selection_freeze(selection: Mapping[str, Any]) -> None:
    if selection.get("selection_split") != "inner_selection" or selection.get("outer_metrics_seen") is not False or selection.get("test_metrics_seen") is not False:
        raise ValueError("TASK035B_SELECTION_FREEZE_INVALID")
    if len(selection.get("per_kpi", [])) != 10:
        raise ValueError("TASK035B_SELECTION_FREEZE_KPI_COUNT")


def _write_hashed(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    report["report_hash"] = sha256_json(report)
    write_json(path, report)
    return report


def _load_outer_labels_after_prediction_freeze(config: Mapping[str, Any]) -> dict[str, np.ndarray]:
    manifest = verified_report(REPO_ROOT / config["sources"]["kpi_manifest"])
    labels: dict[str, np.ndarray] = {}
    private = REPO_ROOT / config["private_root"] / "outer" / "per_kpi_labels"
    private.mkdir(parents=True, exist_ok=True)
    for entry in manifest["per_kpi"]:
        kpi_id = entry["kpi_id"]
        start, end = map(int, entry["outer_validation_range"])
        source = REPO_ROOT / config["sources"]["cohort_private_root"] / f"{kpi_id}.npz"
        with np.load(source, allow_pickle=False) as data:
            value = np.asarray(data["labels"][start:end], dtype=np.int8)
        np.save(private / f"{kpi_id}.npy", value, allow_pickle=False)
        labels[kpi_id] = value
    return labels


def _compose_hashes(hashes: Sequence[str], predictions: Mapping[str, np.ndarray]) -> np.ndarray:
    arrays = [predictions[value] for value in hashes]
    return np.maximum.reduce(arrays).astype(np.int8)


def run_outer(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    code_commit = git_clean_commit()
    selection = verified_report(REPO_ROOT / config["reports"]["selection_freeze"])
    validate_selection_freeze(selection)
    panel = verified_report(REPO_ROOT / config["reports"]["primary_panel_freeze"])
    rules_by_hash = {item["rule_sha256"]: item for item in frozen_executable_cohort(config)}
    selected_rows = {entry["kpi_id"]: entry["selected_rules"] for entry in panel["per_kpi"]}
    if set(selected_rows) != {entry["kpi_id"] for entry in selection["per_kpi"]}:
        raise ValueError("TASK035B_OUTER_PANEL_SELECTION_KPI_MISMATCH")
    values_paths, value_metadata = save_values_only_split(config, "outer")
    image = inspect_image(config)
    probe = isolation_probe(config, image["image_id"])
    if probe["status"] != "passed":
        raise ValueError("TASK035B_ISOLATION_PROBE_FAILED")
    private_root = REPO_ROOT / config["private_root"] / "outer"
    predictions: dict[str, dict[str, np.ndarray]] = defaultdict(dict)
    runtime_rows = []
    for kpi in sorted(selected_rows):
        for tracked in selected_rows[kpi]:
            rule = rules_by_hash[tracked["rule_sha256"]]
            runs = []
            for replay in (1, 2):
                output = private_root / "per_rule_predictions" / rule["rule_sha256"] / f"replay_{replay}"
                runs.append(execute_full_window_rule(config, image, run_id=f"outer-{rule['rule_sha256']}-{replay}", rule_path=rule["_rule_path"], rule_sha256=rule["rule_sha256"], values_path=values_paths[kpi], output_directory=output))
            if runs[0]["runtime_status"] != "executable_rule" or runs[1]["runtime_status"] != "executable_rule":
                raise ValueError("TASK035B_FAILED_OUTER_RULE_RUNTIME")
            if not deterministic_replay_matches(runs[0], runs[1]):
                raise ValueError("TASK035B_OUTER_PREDICTION_NONDETERMINISTIC")
            predictions[kpi][rule["rule_sha256"]] = load_private_prediction(private_root / "per_rule_predictions" / rule["rule_sha256"] / "replay_1")
            runtime_rows.append({"kpi_id": kpi, "rule_sha256": rule["rule_sha256"], "input_sha256": runs[0]["input_sha256"], "image_id": runs[0]["image_id"], "exit_code": runs[0]["exit_code"], "output_count": runs[0]["output_count"], "prediction_sha256": runs[0]["prediction_sha256"], "predicted_positive_count": runs[0]["predicted_positive_count"], "deterministic_replay": True, "labels_mounted": False})
    arms_by_kpi = {entry["kpi_id"]: {arm: entry[arm] for arm in ("best_1", "top_3_or", "coverage_3_or", "all_10_or")} for entry in selection["per_kpi"]}
    arm_predictions: dict[str, dict[str, np.ndarray]] = defaultdict(dict)
    prediction_freeze_rows = []
    for kpi in sorted(arms_by_kpi):
        arm_rows = []
        for arm, specification in arms_by_kpi[kpi].items():
            vector = _compose_hashes(specification["rule_hashes"], predictions[kpi])
            path = private_root / "frozen_arm_predictions" / kpi / f"{arm}.npy"
            path.parent.mkdir(parents=True, exist_ok=True)
            np.save(path, vector, allow_pickle=False)
            arm_predictions[kpi][arm] = vector
            arm_rows.append({"arm": arm, "rule_hashes": list(specification["rule_hashes"]), "prediction_sha256": sha256_file(path), "output_count": len(vector), "predicted_positive_count": int(np.sum(vector))})
        prediction_freeze_rows.append({"kpi_id": kpi, "arms": arm_rows})
    prediction_freeze = {"selection_freeze_hash": selection["report_hash"], "creation_code_commit": code_commit, "outer_labels_loaded": False, "per_kpi": prediction_freeze_rows}
    prediction_freeze["manifest_hash"] = sha256_json(prediction_freeze)
    write_json(REPO_ROOT / config["private_root"] / "manifests" / "outer_prediction_freeze.private.json", prediction_freeze)
    labels = _load_outer_labels_after_prediction_freeze(config)
    per_kpi: dict[str, dict[str, dict[str, Any]]] = {}
    for kpi in sorted(arm_predictions):
        per_kpi[kpi] = {arm: direct_pa_free_metrics(labels[kpi], vector) for arm, vector in arm_predictions[kpi].items()}
    summaries = summarize_outer_metrics(per_kpi)
    runtime_report = _write_hashed(REPO_ROOT / config["reports"]["outer_runtime"], {"schema_version": "1.0", "task_id": "TASK-035B", "artifact_type": "outer_runtime_report", "execution_code_commit": code_commit, "image": image, "isolation": probe, "primary_panel_rule_count": len(runtime_rows), "deterministic_replay_completed": True, "outer_labels_loaded_during_rule_execution": False, "test_accessed": False, "rules": runtime_rows})
    outer_report = _write_hashed(REPO_ROOT / config["reports"]["outer_validation"], {"schema_version": "1.0", "task_id": "TASK-035B", "artifact_type": "outer_validation_report", "status": "passed_multi_rule_outer_validation", "primary_comparison": "coverage_3_or_minus_best_1", "per_kpi": [{"kpi_id": kpi, "arms": per_kpi[kpi]} for kpi in sorted(per_kpi)], "summaries": summaries, "outer_individual_metrics_computed": False, "outer_selection_performed": False, "point_adjustment": False, "test_values_parsed": False, "test_labels_parsed": False})
    bootstrap = bootstrap_comparisons(per_kpi, (("coverage_3_or", "best_1"), ("top_3_or", "best_1"), ("all_10_or", "best_1"), ("coverage_3_or", "top_3_or")), ("precision", "recall", "point_f1", "event_recall", "false_positive_points_per_10000_normal_points", "false_alarm_events_per_10000_points"), seed=int(config["bootstrap"]["seed"]), resamples=int(config["bootstrap"]["resamples"]))
    bootstrap_report = _write_hashed(REPO_ROOT / config["reports"]["bootstrap"], {"schema_version": "1.0", "task_id": "TASK-035B", "artifact_type": "paired_kpi_bootstrap_report", "kpi_resampling_unit": True, "formal_significance_claim": False, "comparisons": bootstrap})
    return {"status": outer_report["status"], "runtime_report_hash": runtime_report["report_hash"], "outer_report_hash": outer_report["report_hash"], "bootstrap_report_hash": bootstrap_report["report_hash"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task035b_multi_rule_validation.json")
    args = parser.parse_args()
    result = run_outer((REPO_ROOT / args.config).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
