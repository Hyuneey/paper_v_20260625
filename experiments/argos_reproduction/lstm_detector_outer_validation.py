"""Frozen-checkpoint outer inference and detector-only metrics for TASK-037B."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.direct_event_metrics import (
    direct_pa_free_metrics,
    metric_distribution,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    REPO_ROOT,
    git_clean_commit,
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.kpi_detector_split_guard import (
    load_frozen_splits,
    load_split_labels_after_freeze,
    materialize_split_values,
)
from experiments.argos_reproduction.lstm_detector_artifacts import (
    build_final_manifest,
    ensure_report_safe,
    private_unit_root,
    save_binary_prediction,
    write_hashed_report,
)
from experiments.argos_reproduction.lstm_detector_scoring import (
    exact_replay,
    inspect_frozen_image,
    load_aligned_score,
    score_execution_unit,
)
from experiments.argos_reproduction.lstm_detector_training import verify_task037a_lineage


class DetectorOuterValidationError(RuntimeError):
    pass


METRIC_FIELDS = (
    "precision", "recall", "point_f1", "event_precision", "event_recall", "event_f1",
    "false_positive_points_per_10000_normal_points", "false_alarm_events_per_10000_points",
    "predicted_positive_rate", "AUROC", "AUPRC",
)


def _verified_report(path: Path) -> dict[str, Any]:
    report = read_json(path)
    subject = dict(report)
    expected = subject.pop("report_hash", None)
    if expected != sha256_json(subject):
        raise DetectorOuterValidationError("TASK037B_FROZEN_REPORT_HASH_MISMATCH")
    return report


def roc_auc(labels: object, scores: object) -> float:
    truth = np.asarray(labels, dtype=np.int8)
    score = np.asarray(scores, dtype=np.float64)
    if truth.ndim != 1 or score.shape != truth.shape or not np.all(np.isfinite(score)):
        raise DetectorOuterValidationError("TASK037B_AUROC_INPUT_INVALID")
    positives = int(np.sum(truth == 1))
    negatives = int(np.sum(truth == 0))
    if positives == 0 or negatives == 0:
        return 0.0
    order = np.argsort(score, kind="mergesort")
    sorted_scores = score[order]
    ranks = np.empty(len(score), dtype=np.float64)
    start = 0
    while start < len(score):
        end = start + 1
        while end < len(score) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    positive_rank_sum = float(np.sum(ranks[truth == 1]))
    return (positive_rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def average_precision(labels: object, scores: object) -> float:
    truth = np.asarray(labels, dtype=np.int8)
    score = np.asarray(scores, dtype=np.float64)
    if truth.ndim != 1 or score.shape != truth.shape or not np.all(np.isfinite(score)):
        raise DetectorOuterValidationError("TASK037B_AUPRC_INPUT_INVALID")
    positives = int(np.sum(truth == 1))
    if positives == 0:
        return 0.0
    order = np.argsort(-score, kind="mergesort")
    sorted_scores = score[order]
    sorted_truth = truth[order]
    tp = 0
    fp = 0
    previous_recall = 0.0
    area = 0.0
    start = 0
    while start < len(score):
        end = start + 1
        while end < len(score) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        group = sorted_truth[start:end]
        tp += int(np.sum(group == 1))
        fp += int(np.sum(group == 0))
        recall = tp / positives
        precision = tp / (tp + fp)
        area += (recall - previous_recall) * precision
        previous_recall = recall
        start = end
    return area


def detector_metrics(labels: object, prediction: object, scores: object) -> dict[str, Any]:
    result = direct_pa_free_metrics(labels, prediction)
    result["AUROC"] = roc_auc(labels, scores)
    result["AUPRC"] = average_precision(labels, scores)
    result["score_threshold_optimized_on_outer"] = False
    return result


def _micro(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    names = ("true_positive", "false_positive", "true_negative", "false_negative")
    event_names = ("event_true_positive", "event_false_positive", "event_false_negative")
    counts = {name: sum(int(item[name]) for item in records) for name in names}
    events = {name: sum(int(item[name]) for item in records) for name in event_names}
    tp, fp, tn, fn = (counts[name] for name in names)
    etp, efp, efn = (events[name] for name in event_names)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    event_precision = etp / (etp + efp) if etp + efp else 0.0
    event_recall = etp / (etp + efn) if etp + efn else 0.0
    total_points = sum(int(item["point_count"]) for item in records)
    return {
        **counts,
        **events,
        "precision": precision,
        "recall": recall,
        "point_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "event_precision": event_precision,
        "event_recall": event_recall,
        "event_f1": 2 * event_precision * event_recall / (event_precision + event_recall)
        if event_precision + event_recall else 0.0,
        "false_positive_points_per_10000_normal_points": fp / (fp + tn) * 10000 if fp + tn else 0.0,
        "false_alarm_events_per_10000_points": efp / total_points * 10000 if total_points else 0.0,
    }


def summarize_variant(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(records) != 10:
        raise DetectorOuterValidationError("TASK037B_VARIANT_REQUIRES_TEN_KPIS")
    return {
        "macro": {field: float(np.mean([float(item[field]) for item in records])) for field in METRIC_FIELDS},
        "micro": _micro(records),
        "distribution": {field: metric_distribution(records, field) for field in METRIC_FIELDS},
    }


def run_outer(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    result_commit = git_clean_commit()
    lineage = verify_task037a_lineage(config)
    image = inspect_frozen_image(config)
    seed = int(config["execution"]["seeds"][0])
    frozen_splits = load_frozen_splits(config)
    threshold_report = _verified_report(REPO_ROOT / str(config["reports"]["threshold_freeze"]))
    artifact_report = _verified_report(REPO_ROOT / str(config["reports"]["artifact_manifest"]))
    if threshold_report["status"] != "frozen" or artifact_report["status"] != "inner_frozen_outer_pending":
        raise DetectorOuterValidationError("TASK037B_INNER_FREEZE_REQUIRED")
    thresholds = {
        (row["detector_variant"], row["kpi_id"]): row for row in threshold_report["records"]
    }
    partial = {
        (row["detector_variant"], row["kpi_id"]): row for row in artifact_report["records"]
    }
    runtime_rows: list[dict[str, Any]] = []
    private_freezes: dict[tuple[str, str], dict[str, Any]] = {}
    for variant in ("LSTMADalpha", "LSTMADbeta"):
        for frozen in frozen_splits:
            key = (variant, frozen.kpi_id)
            if key not in thresholds or key not in partial:
                raise DetectorOuterValidationError("TASK037B_FROZEN_UNIT_MISSING")
            unit_root = private_unit_root(config, variant, frozen.kpi_id, seed)
            if sha256_file(unit_root / "fit/checkpoint/best_network.pth") != partial[key]["checkpoint_hash"]:
                raise DetectorOuterValidationError("TASK037B_CHECKPOINT_HASH_MISMATCH")
            if sha256_file(unit_root / "fit/normalization.json") != partial[key]["normalization_hash"]:
                raise DetectorOuterValidationError("TASK037B_NORMALIZATION_HASH_MISMATCH")
            outer_values = unit_root / "inputs/outer.npy"
            value_meta = materialize_split_values(config, frozen, "outer", outer_values)
            first = score_execution_unit(
                config, image, kpi_id=frozen.kpi_id, variant=variant,
                split="outer", replay=1, values_path=outer_values, unit_root=unit_root,
            )
            second = score_execution_unit(
                config, image, kpi_id=frozen.kpi_id, variant=variant,
                split="outer", replay=2, values_path=outer_values, unit_root=unit_root,
            )
            if first.get("status") != "scored" or second.get("status") != "scored":
                raise DetectorOuterValidationError("TASK037B_FAILED_OUTER_SCORE")
            if not exact_replay(first, second):
                raise DetectorOuterValidationError("TASK037B_OUTER_INFERENCE_NONDETERMINISTIC")
            scores = load_aligned_score(unit_root, "outer")
            prediction_path = unit_root / "predictions/outer_prediction.npy"
            prediction_meta = save_binary_prediction(
                scores, float(thresholds[key]["selected_threshold"]), prediction_path
            )
            freeze = {
                "split": "outer",
                "kpi_id": frozen.kpi_id,
                "variant": variant,
                "score_hash": first["aligned_score_sha256"],
                "prediction_hash": prediction_meta["prediction_hash"],
                "prediction_frozen_before_labels": True,
            }
            private_freezes[key] = freeze
            runtime_rows.append(
                {
                    "detector_variant": variant,
                    "kpi_id": frozen.kpi_id,
                    "seed": seed,
                    "terminal_status": "scored_and_replayed",
                    "checkpoint_hash": partial[key]["checkpoint_hash"],
                    "normalization_hash": partial[key]["normalization_hash"],
                    "input_hash": value_meta["input_hash"],
                    "input_count": value_meta["input_count"],
                    "raw_score_count": first["raw_score_count"],
                    "aligned_score_count": first["aligned_score_count"],
                    "missing_prefix_count": first["missing_prefix_count"],
                    "alignment_policy": first["alignment_policy"],
                    "outer_score_hash": first["aligned_score_sha256"],
                    "outer_prediction_hash": prediction_meta["prediction_hash"],
                    "predicted_positive_count": prediction_meta["predicted_positive_count"],
                    "deterministic_replay": True,
                    "labels_mounted": False,
                    "test_mounted": False,
                }
            )
    prediction_freeze = {
        "schema_version": "1.0",
        "task_id": "TASK-037B",
        "stage": "outer_prediction_freeze",
        "creation_code_commit": result_commit,
        "outer_labels_loaded": False,
        "records": [private_freezes[key] for key in sorted(private_freezes)],
    }
    prediction_freeze["freeze_hash"] = sha256_json(prediction_freeze)
    write_json(
        REPO_ROOT / str(config["private_root"]) / "manifests/outer_prediction_freeze.private.json",
        prediction_freeze,
    )
    per_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    final_manifests: list[dict[str, Any]] = []
    labels_by_kpi: dict[str, np.ndarray] = {}
    for frozen in frozen_splits:
        labels_by_kpi[frozen.kpi_id] = load_split_labels_after_freeze(
            config,
            frozen,
            "outer",
            prediction_freeze=private_freezes[("LSTMADalpha", frozen.kpi_id)],
        )
    for row in runtime_rows:
        variant = row["detector_variant"]
        kpi_id = row["kpi_id"]
        key = (variant, kpi_id)
        unit_root = private_unit_root(config, variant, kpi_id, seed)
        prediction = np.asarray(
            np.load(unit_root / "predictions/outer_prediction.npy", allow_pickle=False), dtype=np.int8
        )
        scores = load_aligned_score(unit_root, "outer")
        metrics = detector_metrics(labels_by_kpi[kpi_id], prediction, scores)
        metrics["kpi_id"] = kpi_id
        metrics["point_count"] = len(prediction)
        per_variant[variant].append(metrics)
        hashes = {
            "checkpoint_hash": partial[key]["checkpoint_hash"],
            "normalization_hash": partial[key]["normalization_hash"],
            "generation_score_hash": partial[key]["generation_score_hash"],
            "inner_score_hash": partial[key]["inner_score_hash"],
            "outer_score_hash": row["outer_score_hash"],
            "generation_prediction_hash": partial[key]["generation_prediction_hash"],
            "inner_prediction_hash": partial[key]["inner_prediction_hash"],
            "outer_prediction_hash": row["outer_prediction_hash"],
            "incorrect_indices_generation_hash": partial[key]["incorrect_indices_generation_hash"],
        }
        final_manifests.append(
            build_final_manifest(
                config,
                variant=variant,
                kpi_id=kpi_id,
                split_manifest_hash=partial[key]["split_manifest_hash"],
                threshold=float(thresholds[key]["selected_threshold"]),
                threshold_protocol_hash=str(thresholds[key]["threshold_protocol_hash"]),
                hashes=hashes,
            )
        )
    summaries = {variant: summarize_variant(sorted(rows, key=lambda item: item["kpi_id"])) for variant, rows in per_variant.items()}
    sensitivity = []
    alpha = {row["kpi_id"]: row for row in per_variant["LSTMADalpha"]}
    beta = {row["kpi_id"]: row for row in per_variant["LSTMADbeta"]}
    for field in METRIC_FIELDS:
        differences = [float(alpha[kpi][field]) - float(beta[kpi][field]) for kpi in sorted(alpha)]
        sensitivity.append(
            {
                "metric": field,
                "alpha_minus_beta_macro_difference": float(np.mean(differences)),
                "median_difference": float(np.median(differences)),
                "minimum_difference": float(np.min(differences)),
                "maximum_difference": float(np.max(differences)),
            }
        )
    common = {
        "schema_version": "1.0",
        "task_id": "TASK-037B",
        "execution_code_commit": result_commit,
        "task037a_lineage": lineage,
        "image": image,
        "variant_selection_performed": False,
        "fusion_performed": False,
        "provider_calls": 0,
        "test_values_accessed": False,
        "test_labels_accessed": False,
    }
    runtime_report = write_hashed_report(
        REPO_ROOT / str(config["reports"]["outer_runtime"]),
        {
            **common,
            "artifact_type": "outer_runtime_report",
            "status": "passed",
            "execution_unit_count": len(runtime_rows),
            "outer_labels_loaded_during_inference": False,
            "deterministic_replay_complete": True,
            "units": runtime_rows,
        },
    )
    validation_report = write_hashed_report(
        REPO_ROOT / str(config["reports"]["outer_validation"]),
        {
            **common,
            "artifact_type": "outer_detector_validation_report",
            "status": "passed_dual_arm_detector_outer_validation",
            "operating_point_split": "inner",
            "outer_threshold_search": False,
            "point_adjustment": False,
            "per_variant": {
                variant: {
                    "per_kpi": sorted(rows, key=lambda item: item["kpi_id"]),
                    "summary": summaries[variant],
                }
                for variant, rows in sorted(per_variant.items())
            },
            "variant_sensitivity": sensitivity,
            "headline_winner_selected": False,
        },
    )
    final_artifact_report = write_hashed_report(
        REPO_ROOT / str(config["reports"]["artifact_manifest"]),
        {
            **common,
            "artifact_type": "detector_artifact_manifest",
            "status": "complete",
            "records": sorted(final_manifests, key=lambda item: (item["detector_variant"], item["kpi_id"])),
            "raw_artifacts_tracked": False,
            "test_artifacts_created": False,
        },
    )
    for report in (runtime_report, validation_report, final_artifact_report):
        ensure_report_safe(report)
    report_md = """# TASK-037B Report

Final status: `passed_dual_arm_detector_outer_validation`.

Both frozen official EasyTSAD variants, `LSTMADalpha` and `LSTMADbeta`, were
fit independently for all ten frozen KPI series. Generation-only fitting and
normalization, inner-only threshold selection, and one-way outer validation
followed the pre-registered protocol. No detector variant was selected.

Outer inference received values only and was replayed exactly from frozen
checkpoints. Direct PA-free point/event metrics, AUROC and AUPRC were computed
after the outer score and prediction freeze. Generation TP/FN/FP/TN segments
were prepared privately but were not used for rule generation.

No provider, ARGOS agent, generated rule, detector-rule fusion, sealed-test
value, sealed-test label, or `TestLabels` artifact was used or created. Metric
magnitude was not a completion criterion.
"""
    (REPO_ROOT / str(config["reports"]["task_report"])).write_text(report_md, encoding="utf-8")
    return {
        "status": validation_report["status"],
        "execution_units": len(runtime_rows),
        "runtime_report_hash": runtime_report["report_hash"],
        "validation_report_hash": validation_report["report_hash"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", default="configs/argos_reproduction/task037b_dual_lstm_detector_validation.json"
    )
    args = parser.parse_args()
    result = run_outer((REPO_ROOT / args.config).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
