"""Frozen TASK-035B inner metrics and arm-selection algorithms."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.direct_event_metrics import compose_or, contiguous_events, direct_pa_free_metrics, intervals_overlap
from experiments.argos_reproduction.balanced_rule_panel import select_balanced_panel
from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, git_clean_commit, read_json, sha256_file, sha256_json, write_json
from experiments.argos_reproduction.multi_rule_full_window_runtime import deterministic_replay_matches, execute_full_window_rule, load_private_prediction
from experiments.argos_reproduction.multi_rule_runtime import inspect_image, isolation_probe
from experiments.argos_reproduction.multi_rule_validation_common import frozen_executable_cohort, save_values_only_split, verified_report
from experiments.argos_reproduction.rule_prediction_diversity import diversity_diagnostics


NEAR_ALL_POSITIVE_RATE = 0.95


def rule_metric_order(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        -float(record["point_f1"]),
        -float(record["recall"]),
        -float(record["precision"]),
        int(record["false_positive"]),
        str(record["rule_sha256"]),
    )


def classify_rule(metrics: Mapping[str, Any]) -> str:
    rate = float(metrics["predicted_positive_rate"])
    if int(metrics["predicted_positive_count"]) == 0:
        return "all_zero_rule"
    if rate == 1.0:
        return "all_one_rule"
    if rate >= NEAR_ALL_POSITIVE_RATE:
        return "near_all_positive_rule"
    return "nondegenerate_rule"


def _covered_truth_events(truth: np.ndarray, prediction: np.ndarray) -> set[int]:
    predicted_events = contiguous_events(prediction)
    return {
        index
        for index, event in enumerate(contiguous_events(truth))
        if any(intervals_overlap(event, predicted) for predicted in predicted_events)
    }


def select_frozen_arms(
    records: Sequence[Mapping[str, Any]],
    predictions: Mapping[str, np.ndarray],
    ground_truth: np.ndarray,
) -> dict[str, Any]:
    if len(records) != 10 or len({str(item["rule_sha256"]) for item in records}) != 10:
        raise ValueError("TASK035B_SELECTION_REQUIRES_TEN_DISTINCT_RULES")
    enriched = []
    for source in records:
        rule_hash = str(source["rule_sha256"])
        enriched.append({**dict(source), **direct_pa_free_metrics(ground_truth, predictions[rule_hash])})
    ranked = sorted(enriched, key=rule_metric_order)
    best_hash = str(ranked[0]["rule_sha256"])
    top_three = [str(item["rule_sha256"]) for item in ranked[:3]]
    selected = [best_hash]
    current = predictions[best_hash]
    covered = _covered_truth_events(ground_truth, current)
    steps = [{"rule_sha256": best_hash, "newly_covered_events": len(covered), **{
        "composed_recall": direct_pa_free_metrics(ground_truth, current)["recall"],
        "composed_f1": direct_pa_free_metrics(ground_truth, current)["point_f1"],
        "incremental_false_positives": direct_pa_free_metrics(ground_truth, current)["false_positive"],
    }}]
    while len(selected) < 3:
        options = []
        current_fp = int(direct_pa_free_metrics(ground_truth, current)["false_positive"])
        for item in enriched:
            rule_hash = str(item["rule_sha256"])
            if rule_hash in selected:
                continue
            composed = compose_or([current, predictions[rule_hash]])
            metrics = direct_pa_free_metrics(ground_truth, composed)
            newly = len(_covered_truth_events(ground_truth, composed) - covered)
            incremental_fp = int(metrics["false_positive"]) - current_fp
            options.append(((-newly, -metrics["recall"], -metrics["point_f1"], incremental_fp, rule_hash), rule_hash, composed, metrics, newly, incremental_fp))
        _, chosen, current, metrics, newly, incremental_fp = min(options, key=lambda item: item[0])
        selected.append(chosen)
        covered = _covered_truth_events(ground_truth, current)
        steps.append({"rule_sha256": chosen, "newly_covered_events": newly, "composed_recall": metrics["recall"], "composed_f1": metrics["point_f1"], "incremental_false_positives": incremental_fp})
    all_hashes = sorted(str(item["rule_sha256"]) for item in records)
    return {
        "best_1": {"rule_hashes": [best_hash]},
        "top_3_or": {"rule_hashes": top_three},
        "coverage_3_or": {"rule_hashes": selected, "selection_steps": steps},
        "all_10_or": {"rule_hashes": all_hashes},
    }


def compose_frozen_arm(arm: Mapping[str, Any], predictions: Mapping[str, np.ndarray]) -> np.ndarray:
    hashes = [str(value) for value in arm["rule_hashes"]]
    return compose_or([predictions[value] for value in hashes])


def _load_inner_labels_after_panel_freeze(config: Mapping[str, Any]) -> dict[str, np.ndarray]:
    manifest = verified_report(REPO_ROOT / config["sources"]["kpi_manifest"])
    labels: dict[str, np.ndarray] = {}
    private = REPO_ROOT / config["private_root"] / "inner" / "per_kpi_labels"
    private.mkdir(parents=True, exist_ok=True)
    for entry in manifest["per_kpi"]:
        kpi_id = entry["kpi_id"]
        start, end = map(int, entry["inner_selection_range"])
        source = REPO_ROOT / config["sources"]["cohort_private_root"] / f"{kpi_id}.npz"
        with np.load(source, allow_pickle=False) as data:
            value = np.asarray(data["labels"][start:end], dtype=np.int8)
        np.save(private / f"{kpi_id}.npy", value, allow_pickle=False)
        labels[kpi_id] = value
    return labels


def _tracked_rule(item: Mapping[str, Any], prediction_hash: str | None = None) -> dict[str, Any]:
    result = {key: item[key] for key in ("rule_sha256", "kpi_id", "anchor_id", "generation_cohort", "replicate_id", "original_slot_id")}
    if prediction_hash is not None:
        result["inner_runtime_prediction_hash"] = prediction_hash
    return result


def _write_hashed_report(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    report["report_hash"] = sha256_json(report)
    write_json(path, report)
    return report


def run_inner(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    code_commit = git_clean_commit()
    rules = frozen_executable_cohort(config)
    by_kpi: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rule in rules:
        by_kpi[rule["kpi_id"]].append(rule)
    if len(by_kpi) != 10:
        raise ValueError("TASK035B_COHORT_KPI_COUNT_MISMATCH")
    anchor_report = verified_report(REPO_ROOT / config["sources"]["anchor_manifest"])
    anchor_order_by_kpi: dict[str, list[str]] = defaultdict(list)
    for item in sorted(anchor_report["anchors"], key=lambda value: int(value["anchor_rank"])):
        anchor_order_by_kpi[item["kpi_id"]].append(item["anchor_id"])
    values_paths, value_metadata = save_values_only_split(config, "inner")
    image = inspect_image(config)
    probe = isolation_probe(config, image["image_id"])
    if probe["status"] != "passed":
        raise ValueError("TASK035B_ISOLATION_PROBE_FAILED")
    private_root = REPO_ROOT / config["private_root"] / "inner"
    full_results: list[dict[str, Any]] = []
    eligible: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, rule in enumerate(rules, 1):
        output = private_root / "per_rule_predictions" / rule["rule_sha256"] / "gate"
        runtime = execute_full_window_rule(config, image, run_id=f"inner-gate-{index}", rule_path=rule["_rule_path"], rule_sha256=rule["rule_sha256"], values_path=values_paths[rule["kpi_id"]], output_directory=output)
        tracked = {**_tracked_rule(rule), **runtime}
        full_results.append(tracked)
        if runtime["runtime_status"] == "executable_rule":
            eligible[rule["kpi_id"]].append(rule)
    per_kpi_yield = {kpi: sum(item["runtime_status"] == "executable_rule" for item in full_results if item["kpi_id"] == kpi) for kpi in sorted(by_kpi)}
    runtime_report = _write_hashed_report(REPO_ROOT / config["reports"]["full_inner_runtime"], {
        "schema_version": "1.0", "task_id": "TASK-035B", "artifact_type": "full_inner_runtime_report",
        "execution_code_commit": code_commit, "image": image, "isolation": probe, "frozen_cohort_count": len(rules),
        "per_kpi_full_inner_executable": per_kpi_yield,
        "full_inner_executable_rules": sum(per_kpi_yield.values()),
        "minimum_required_per_kpi": 10, "labels_loaded": False, "outer_accessed": False, "test_accessed": False,
        "rules": full_results,
    })
    if any(count < 10 for count in per_kpi_yield.values()):
        return {"status": "insufficient_full_window_rule_yield", "runtime_report": runtime_report}
    panel: dict[str, list[dict[str, Any]]] = {}
    for kpi in sorted(eligible):
        panel[kpi] = select_balanced_panel(eligible[kpi], anchor_order_by_kpi[kpi], panel_size=10)
    panel_protocol_hash = sha256_json({"algorithm": "anchor_round_robin", "panel_size": 10, "anchor_order": anchor_order_by_kpi})
    replay_predictions: dict[str, dict[str, np.ndarray]] = defaultdict(dict)
    panel_rows = []
    for kpi in sorted(panel):
        selected_rows = []
        for rule in panel[kpi]:
            runs = []
            for replay in (1, 2):
                output = private_root / "primary_panel_predictions" / rule["rule_sha256"] / f"replay_{replay}"
                runs.append(execute_full_window_rule(config, image, run_id=f"inner-panel-{rule['rule_sha256']}-{replay}", rule_path=rule["_rule_path"], rule_sha256=rule["rule_sha256"], values_path=values_paths[kpi], output_directory=output))
            if runs[0]["runtime_status"] != "executable_rule" or not deterministic_replay_matches(runs[0], runs[1]):
                raise ValueError("TASK035B_INNER_PREDICTION_NONDETERMINISTIC")
            replay_predictions[kpi][rule["rule_sha256"]] = load_private_prediction(private_root / "primary_panel_predictions" / rule["rule_sha256"] / "replay_1")
            selected_rows.append(_tracked_rule(rule, runs[0]["prediction_sha256"]))
        panel_rows.append({"kpi_id": kpi, "eligible_full_inner_rule_count": len(eligible[kpi]), "selected_rule_count": 10, "represented_anchor_count": len({item["anchor_id"] for item in panel[kpi]}), "selected_rules": selected_rows})
    panel_freeze = _write_hashed_report(REPO_ROOT / config["reports"]["primary_panel_freeze"], {
        "schema_version": "1.0", "task_id": "TASK-035B", "artifact_type": "primary_panel_freeze",
        "panel_id": "PANEL-TASK035B-BALANCED-100", "panel_protocol_hash": panel_protocol_hash,
        "creation_code_commit": code_commit, "labels_loaded_during_panel_selection": False,
        "per_kpi": panel_rows, "total_selected_rules": 100,
    })
    labels = _load_inner_labels_after_panel_freeze(config)
    individual_rows = []
    selection_rows = []
    diversity_rows = []
    cohort_metrics: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for kpi in sorted(panel):
        metrics_by_hash: dict[str, dict[str, Any]] = {}
        for rule in panel[kpi]:
            metrics = direct_pa_free_metrics(labels[kpi], replay_predictions[kpi][rule["rule_sha256"]])
            row = {"kpi_id": kpi, **_tracked_rule(rule), **metrics, "degeneracy_class": classify_rule(metrics)}
            metrics_by_hash[rule["rule_sha256"]] = row
            individual_rows.append(row)
            cohort_metrics[rule["generation_cohort"]].append(row)
        diversity_rows.append({"kpi_id": kpi, **diversity_diagnostics(panel[kpi], replay_predictions[kpi], labels[kpi])})
        selection_rows.append({"kpi_id": kpi, **select_frozen_arms(panel[kpi], replay_predictions[kpi], labels[kpi])})
    supplementary = {}
    for cohort, rows in sorted(cohort_metrics.items()):
        supplementary[cohort] = {
            "rule_count": len(rows),
            "median_point_f1": float(np.median([row["point_f1"] for row in rows])),
            "median_point_recall": float(np.median([row["recall"] for row in rows])),
            "median_event_recall": float(np.median([row["event_recall"] for row in rows])),
            "all_zero_fraction": sum(row["degeneracy_class"] == "all_zero_rule" for row in rows) / len(rows),
            "near_all_positive_fraction": sum(row["degeneracy_class"] in {"all_one_rule", "near_all_positive_rule"} for row in rows) / len(rows),
        }
    _write_hashed_report(REPO_ROOT / config["reports"]["inner_rule_metrics"], {"schema_version": "1.0", "task_id": "TASK-035B", "artifact_type": "inner_rule_metrics", "panel_id": panel_freeze["panel_id"], "metric_protocol": "direct_binary_pa_free", "rules": individual_rows, "supplementary_generation_diagnostics": supplementary, "outer_metrics_seen": False, "test_metrics_seen": False})
    _write_hashed_report(REPO_ROOT / config["reports"]["diversity"], {"schema_version": "1.0", "task_id": "TASK-035B", "artifact_type": "prediction_diversity_report", "per_kpi": diversity_rows, "split": "inner_selection", "performance_selection_used": False})
    inner_report = _write_hashed_report(REPO_ROOT / config["reports"]["inner_selection"], {"schema_version": "1.0", "task_id": "TASK-035B", "artifact_type": "inner_selection_report", "per_kpi": selection_rows, "selection_split": "inner_selection", "outer_metrics_seen": False, "test_metrics_seen": False})
    selection_freeze = _write_hashed_report(REPO_ROOT / config["reports"]["selection_freeze"], {"schema_version": "1.0", "task_id": "TASK-035B", "artifact_type": "selection_freeze", "panel_id": panel_freeze["panel_id"], "selection_protocol_hash": sha256_json({"best": "f1_recall_precision_fp_hash", "top3": "ranked_or", "coverage3": "greedy_event_coverage", "all10": "or"}), "creation_code_commit": code_commit, "per_kpi": selection_rows, "selection_split": "inner_selection", "outer_metrics_seen": False, "test_metrics_seen": False})
    private_manifest = {"panel_report_hash": panel_freeze["report_hash"], "selection_report_hash": selection_freeze["report_hash"], "rule_count": 100}
    write_json(REPO_ROOT / config["private_root"] / "manifests" / "selection_freeze.private.json", private_manifest)
    return {"status": "inner_selection_frozen", "panel_hash": panel_freeze["report_hash"], "selection_hash": selection_freeze["report_hash"], "inner_report_hash": inner_report["report_hash"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task035b_multi_rule_validation.json")
    args = parser.parse_args()
    result = run_inner((REPO_ROOT / args.config).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "inner_selection_frozen" else 2


if __name__ == "__main__":
    raise SystemExit(main())
