"""Run the frozen TASK-037C inner/outer diagnostic fusion matrix."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.diagnostic_binary_fusion import (
    DETECTOR_VARIANTS,
    FUSION_OPERATORS,
    RULE_ARMS,
    degeneracy_flags,
    fuse_binary,
)
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
from experiments.argos_reproduction.frozen_prediction_loader import (
    FrozenPredictionInputs,
    load_frozen_predictions,
    verified_report,
    verify_private_manifest,
)
from experiments.argos_reproduction.fusion_contribution_accounting import (
    fn_contribution,
    fp_contribution,
)
from experiments.argos_reproduction.fusion_variant_consistency import (
    build_variant_consistency,
)
from experiments.argos_reproduction.paired_kpi_bootstrap import (
    paired_percentile_bootstrap,
)


class FusionOuterValidationError(RuntimeError):
    """Raised when the diagnostic fusion execution boundary is violated."""


METRIC_FIELDS = (
    "precision",
    "recall",
    "point_f1",
    "event_precision",
    "event_recall",
    "event_f1",
    "false_positive_points_per_10000_normal_points",
    "false_alarm_events_per_10000_points",
    "predicted_positive_rate",
)

BOOTSTRAP_FIELDS = (
    "precision",
    "recall",
    "point_f1",
    "event_f1",
    "false_positive_points_per_10000_normal_points",
)


def _write_hashed_report(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    if "report_hash" in report:
        raise FusionOuterValidationError("TASK037C_REPORT_HASH_PRECLAIMED")
    ensure_report_safe(report)
    report["report_hash"] = sha256_json(report)
    write_json(path, report)
    return report


def ensure_report_safe(report: object) -> None:
    encoded = json.dumps(
        report, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).lower()
    prohibited = (
        "private_argos_reproduction",
        "c:\\users\\",
        "c:/users/",
        "source_values",
        "target_values",
        ".npy",
        "testlabels",
        "best_network",
    )
    if any(token in encoded for token in prohibited):
        raise FusionOuterValidationError("TASK037C_TRACKED_REPORT_PRIVATE_CONTENT")


def _save_prediction(path: Path, prediction: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, prediction.astype(np.int8, copy=False), allow_pickle=False)
    return sha256_file(path)


def _summary(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(records) != 10:
        raise FusionOuterValidationError("TASK037C_SUMMARY_REQUIRES_TEN_KPIS")
    point_names = ("true_positive", "false_positive", "true_negative", "false_negative")
    event_names = ("event_true_positive", "event_false_positive", "event_false_negative")
    point = {name: sum(int(row[name]) for row in records) for name in point_names}
    events = {name: sum(int(row[name]) for row in records) for name in event_names}
    tp, fp, tn, fn = (point[name] for name in point_names)
    etp, efp, efn = (events[name] for name in event_names)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    event_precision = etp / (etp + efp) if etp + efp else 0.0
    event_recall = etp / (etp + efn) if etp + efn else 0.0
    point_count = sum(int(row["point_count"]) for row in records)
    return {
        "macro": {
            field: float(np.mean([float(row[field]) for row in records]))
            for field in METRIC_FIELDS
        },
        "micro": {
            **point,
            **events,
            "precision": precision,
            "recall": recall,
            "point_f1": 2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0,
            "event_precision": event_precision,
            "event_recall": event_recall,
            "event_f1": 2 * event_precision * event_recall
            / (event_precision + event_recall)
            if event_precision + event_recall
            else 0.0,
            "false_positive_points_per_10000_normal_points": fp
            / (fp + tn)
            * 10000
            if fp + tn
            else 0.0,
            "false_alarm_events_per_10000_points": efp / point_count * 10000
            if point_count
            else 0.0,
        },
        "distribution": {
            field: metric_distribution(records, field) for field in METRIC_FIELDS
        },
    }


def _contribution_summary(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    scalar_fields = sorted(
        key
        for key, value in records[0].items()
        if isinstance(value, (int, float)) and key != "point_count"
    )
    return {
        "macro": {
            field: float(np.mean([float(row[field]) for row in records]))
            for field in scalar_fields
        },
        "totals": {
            field: int(sum(int(row[field]) for row in records))
            for field in scalar_fields
            if all(isinstance(row[field], int) for row in records)
        },
    }


def _materialize_prediction_freeze(
    config: Mapping[str, Any],
    inputs: FrozenPredictionInputs,
    execution_commit: str,
) -> tuple[
    dict[tuple[str, str, str, str, str], np.ndarray],
    dict[tuple[str, str, str, str, str], str],
    dict[str, Any],
]:
    private_root = REPO_ROOT / str(config["private_root"])
    if private_root.exists() and any(private_root.iterdir()):
        raise FusionOuterValidationError("TASK037C_PRIVATE_OUTPUT_ALREADY_EXISTS")
    private_root.mkdir(parents=True, exist_ok=True)

    fusion_predictions: dict[tuple[str, str, str, str], np.ndarray] = {}
    fusion_hashes: dict[tuple[str, str, str, str], str] = {}
    records: list[dict[str, Any]] = []
    recovered_rule_hashes: dict[tuple[str, str, str], str] = dict(inputs.rule_hashes)

    for kpi in inputs.kpi_ids:
        for arm in RULE_ARMS:
            inner_rule = inputs.rule_predictions[("inner", kpi, arm)]
            inner_rule_hash = _save_prediction(
                private_root / "inputs/rule_arms/inner" / kpi / f"{arm}.npy",
                inner_rule,
            )
            recovered_rule_hashes[("inner", kpi, arm)] = inner_rule_hash
            for split in ("inner", "outer"):
                rule_prediction = inputs.rule_predictions[(split, kpi, arm)]
                rule_hash = recovered_rule_hashes[(split, kpi, arm)]
                for variant in DETECTOR_VARIANTS:
                    detector_prediction = inputs.detector_predictions[(split, variant, kpi)]
                    detector_hash = inputs.detector_hashes[(split, variant, kpi)]
                    for operator in FUSION_OPERATORS:
                        fusion = fuse_binary(
                            detector_prediction, rule_prediction, operator
                        )
                        key = (split, variant, arm, operator, kpi)
                        path = (
                            private_root
                            / split
                            / "fusion_predictions"
                            / variant
                            / arm
                            / operator
                            / f"{kpi}.npy"
                        )
                        digest = _save_prediction(path, fusion)
                        fusion_predictions[key] = fusion
                        fusion_hashes[key] = digest
                        records.append(
                            {
                                "split": split,
                                "detector_variant": variant,
                                "rule_arm": arm,
                                "operator": operator,
                                "kpi_id": kpi,
                                "split_manifest_hash": inputs.split_hashes[kpi],
                                "detector_prediction_hash": detector_hash,
                                "rule_prediction_hash": rule_hash,
                                "fusion_prediction_hash": digest,
                                "output_count": len(fusion),
                                "frozen_before_labels": True,
                            }
                        )
    if len(records) != 320:
        raise FusionOuterValidationError("TASK037C_PREDICTION_FREEZE_INCOMPLETE")
    freeze = {
        "schema_version": "1.0",
        "task_id": "TASK-037C",
        "stage": "complete_inner_outer_prediction_freeze",
        "execution_commit": execution_commit,
        "all_predictions_frozen_before_labels": True,
        "record_count": len(records),
        "records": records,
    }
    freeze["freeze_hash"] = sha256_json(freeze)
    write_json(private_root / "manifests/fusion_prediction_hashes.private.json", freeze)
    write_json(
        private_root / "manifests/input_hashes.private.json",
        {
            "execution_commit": execution_commit,
            "source_records": list(inputs.source_records),
            "inner_rule_recovery": inputs.inner_rule_recovery,
            "fusion_freeze_hash": freeze["freeze_hash"],
        },
    )
    return fusion_predictions, fusion_hashes, freeze


def _load_labels_after_complete_freeze(
    config: Mapping[str, Any],
    inputs: FrozenPredictionInputs,
    freeze_path: Path,
    split: str,
) -> dict[str, np.ndarray]:
    freeze = read_json(freeze_path)
    verify_private_manifest(freeze, "freeze_hash")
    if (
        freeze.get("record_count") != 320
        or freeze.get("all_predictions_frozen_before_labels") is not True
    ):
        raise FusionOuterValidationError("TASK037C_LABEL_ACCESS_BEFORE_FREEZE")
    if split not in ("inner", "outer"):
        raise FusionOuterValidationError("TASK037C_LABEL_SPLIT_INVALID")
    label_root = (
        REPO_ROOT
        / str(config["sources"]["task035b_private_root"])
        / split
        / "per_kpi_labels"
    )
    labels: dict[str, np.ndarray] = {}
    expected_inner_hashes: dict[str, str] = {}
    if split == "inner" and "detector_threshold_freeze" in config["sources"]:
        threshold = verified_report(
            REPO_ROOT / str(config["sources"]["detector_threshold_freeze"]),
            str(config["report_hashes"]["detector_threshold_freeze"]),
        )
        for row in threshold["records"]:
            kpi = str(row["kpi_id"])
            digest = str(row["inner_label_hash"])
            if kpi in expected_inner_hashes and expected_inner_hashes[kpi] != digest:
                raise FusionOuterValidationError("TASK037C_INNER_LABEL_LINEAGE_CONFLICT")
            expected_inner_hashes[kpi] = digest
    for kpi in inputs.kpi_ids:
        path = label_root / f"{kpi}.npy"
        if not path.is_file():
            raise FusionOuterValidationError("TASK037C_FROZEN_LABEL_MISSING")
        value = np.asarray(np.load(path, allow_pickle=False))
        if (
            value.ndim != 1
            or not np.all(np.isfinite(value))
            or not np.all(np.isin(value, (0, 1)))
        ):
            raise FusionOuterValidationError("TASK037C_FROZEN_LABEL_INVALID")
        value = value.astype(np.int8, copy=False)
        if (
            split == "inner"
            and hashlib.sha256(value.tobytes()).hexdigest()
            != expected_inner_hashes.get(kpi)
        ):
            raise FusionOuterValidationError("TASK037C_INNER_LABEL_HASH_MISMATCH")
        expected_length = len(
            inputs.detector_predictions[(split, DETECTOR_VARIANTS[0], kpi)]
        )
        if len(value) != expected_length:
            raise FusionOuterValidationError("TASK037C_LABEL_LENGTH_MISMATCH")
        labels[kpi] = value.copy()
    return labels


def _metric_record(truth: np.ndarray, prediction: np.ndarray, kpi: str) -> dict[str, Any]:
    return {
        "kpi_id": kpi,
        "point_count": len(prediction),
        **direct_pa_free_metrics(truth, prediction),
    }


def _assert_metric_match(
    actual: Mapping[str, Any],
    expected: Mapping[str, Any],
    fields: Sequence[str],
) -> None:
    for field in fields:
        left = actual[field]
        right = expected[field]
        if isinstance(left, int) and isinstance(right, int):
            if left != right:
                raise FusionOuterValidationError("TASK037C_INHERITED_METRIC_MISMATCH")
        elif not np.isclose(float(left), float(right), rtol=0.0, atol=1e-12):
            raise FusionOuterValidationError("TASK037C_INHERITED_METRIC_MISMATCH")


def _evaluate_split(
    config: Mapping[str, Any],
    inputs: FrozenPredictionInputs,
    fusion_predictions: Mapping[tuple[str, str, str, str, str], np.ndarray],
    labels: Mapping[str, np.ndarray],
    split: str,
) -> tuple[
    dict[str, dict[str, dict[str, Any]]],
    dict[str, dict[str, dict[str, Any]]],
    dict[tuple[str, str, str], dict[str, dict[str, Any]]],
    dict[tuple[str, str, str], dict[str, dict[str, Any]]],
]:
    detector_metrics: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    rule_metrics: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    fusion_metrics: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    contributions: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for kpi in inputs.kpi_ids:
        truth = labels[kpi]
        for variant in DETECTOR_VARIANTS:
            detector_metrics[variant][kpi] = _metric_record(
                truth, inputs.detector_predictions[(split, variant, kpi)], kpi
            )
        for arm in RULE_ARMS:
            rule_metrics[arm][kpi] = _metric_record(
                truth, inputs.rule_predictions[(split, kpi, arm)], kpi
            )
            for variant in DETECTOR_VARIANTS:
                detector = inputs.detector_predictions[(split, variant, kpi)]
                rule = inputs.rule_predictions[(split, kpi, arm)]
                for operator in FUSION_OPERATORS:
                    key = (variant, arm, operator)
                    fusion = fusion_predictions[(split, variant, arm, operator, kpi)]
                    metrics = _metric_record(truth, fusion, kpi)
                    metrics["degeneracy"] = degeneracy_flags(fusion, detector, rule)
                    metrics["point_adjustment"] = False
                    metrics["threshold_optimization"] = False
                    fusion_metrics[key][kpi] = metrics
                    contribution = (
                        fn_contribution(truth, detector, rule, fusion)
                        if operator == "fn_union_max"
                        else fp_contribution(truth, detector, rule, fusion)
                    )
                    contribution["kpi_id"] = kpi
                    contribution["point_count"] = len(fusion)
                    contributions[key][kpi] = contribution
    _verify_inherited_baselines(config, split, inputs, detector_metrics, rule_metrics)
    return detector_metrics, rule_metrics, fusion_metrics, contributions


def _verify_inherited_baselines(
    config: Mapping[str, Any],
    split: str,
    inputs: FrozenPredictionInputs,
    detector_metrics: Mapping[str, Mapping[str, Mapping[str, Any]]],
    rule_metrics: Mapping[str, Mapping[str, Mapping[str, Any]]],
) -> None:
    if split == "inner":
        threshold = verified_report(
            REPO_ROOT / str(config["sources"]["detector_threshold_freeze"]),
            str(config["report_hashes"]["detector_threshold_freeze"]),
        )
        expected = {
            (row["detector_variant"], row["kpi_id"]): row for row in threshold["records"]
        }
        for variant in DETECTOR_VARIANTS:
            for kpi in inputs.kpi_ids:
                actual = detector_metrics[variant][kpi]
                row = expected[(variant, kpi)]
                _assert_metric_match(
                    actual,
                    {
                        **row["selected_confusion_counts"],
                        "precision": row["selected_precision"],
                        "recall": row["selected_recall"],
                        "point_f1": row["selected_f1"],
                    },
                    (
                        "true_positive",
                        "false_positive",
                        "true_negative",
                        "false_negative",
                        "precision",
                        "recall",
                        "point_f1",
                    ),
                )
        return

    detector_report = verified_report(
        REPO_ROOT / str(config["sources"]["task037b_outer_validation"]),
        str(config["report_hashes"]["task037b_outer_validation"]),
    )
    for variant in DETECTOR_VARIANTS:
        expected_rows = {
            row["kpi_id"]: row
            for row in detector_report["per_variant"][variant]["per_kpi"]
        }
        for kpi in inputs.kpi_ids:
            _assert_metric_match(
                detector_metrics[variant][kpi],
                expected_rows[kpi],
                (
                    "true_positive",
                    "false_positive",
                    "true_negative",
                    "false_negative",
                    *METRIC_FIELDS,
                ),
            )
    rule_report = verified_report(
        REPO_ROOT / str(config["sources"]["task035b_outer_validation"]),
        str(config["report_hashes"]["task035b_outer_validation"]),
    )
    expected_rule = {
        row["kpi_id"]: row["arms"] for row in rule_report["per_kpi"]
    }
    for arm in RULE_ARMS:
        for kpi in inputs.kpi_ids:
            _assert_metric_match(
                rule_metrics[arm][kpi],
                expected_rule[kpi][arm],
                (
                    "true_positive",
                    "false_positive",
                    "true_negative",
                    "false_negative",
                    *METRIC_FIELDS,
                ),
            )


def _fusion_arm_report(
    metrics: Mapping[tuple[str, str, str], Mapping[str, Mapping[str, Any]]],
    contributions: Mapping[tuple[str, str, str], Mapping[str, Mapping[str, Any]]],
    kpi_ids: Sequence[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in DETECTOR_VARIANTS:
        for arm in RULE_ARMS:
            for operator in FUSION_OPERATORS:
                key = (variant, arm, operator)
                metric_rows = [metrics[key][kpi] for kpi in kpi_ids]
                contribution_rows = [contributions[key][kpi] for kpi in kpi_ids]
                rows.append(
                    {
                        "detector_variant": variant,
                        "rule_arm": arm,
                        "operator": operator,
                        "per_kpi": metric_rows,
                        "summary": _summary(metric_rows),
                        "contribution_summary": _contribution_summary(contribution_rows),
                        "degenerate_counts": {
                            name: sum(
                                bool(row["degeneracy"][name]) for row in metric_rows
                            )
                            for name in (
                                "all_zero",
                                "all_one",
                                "near_all_positive",
                                "identical_to_detector",
                                "identical_to_rule",
                            )
                        },
                    }
                )
    return rows


def _contribution_report_rows(
    contributions: Mapping[tuple[str, str, str], Mapping[str, Mapping[str, Any]]],
    operator: str,
    kpi_ids: Sequence[str],
) -> list[dict[str, Any]]:
    return [
        {
            "detector_variant": variant,
            "rule_arm": arm,
            "operator": operator,
            "per_kpi": [contributions[(variant, arm, operator)][kpi] for kpi in kpi_ids],
            "summary": _contribution_summary(
                [contributions[(variant, arm, operator)][kpi] for kpi in kpi_ids]
            ),
        }
        for variant in DETECTOR_VARIANTS
        for arm in RULE_ARMS
    ]


def _bootstrap_report(
    config: Mapping[str, Any],
    detector_metrics: Mapping[str, Mapping[str, Mapping[str, Any]]],
    fusion_metrics: Mapping[tuple[str, str, str], Mapping[str, Mapping[str, Any]]],
    kpi_ids: Sequence[str],
) -> list[dict[str, Any]]:
    policy = config["bootstrap"]
    records: list[dict[str, Any]] = []
    for variant in DETECTOR_VARIANTS:
        for arm in RULE_ARMS:
            for operator in FUSION_OPERATORS:
                comparisons = {}
                for field in BOOTSTRAP_FIELDS:
                    comparisons[field] = paired_percentile_bootstrap(
                        [fusion_metrics[(variant, arm, operator)][kpi][field] for kpi in kpi_ids],
                        [detector_metrics[variant][kpi][field] for kpi in kpi_ids],
                        seed=int(policy["seed"]),
                        resamples=int(policy["resamples"]),
                        confidence_level=float(policy["confidence_level"]),
                    )
                records.append(
                    {
                        "detector_variant": variant,
                        "rule_arm": arm,
                        "operator": operator,
                        "baseline": f"{variant}_detector_only",
                        "comparisons": comparisons,
                    }
                )
    return records


def run_task037c(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    execution_commit = git_clean_commit()
    inputs = load_frozen_predictions(config)
    fusion_predictions, fusion_hashes, freeze = _materialize_prediction_freeze(
        config, inputs, execution_commit
    )

    input_report = _write_hashed_report(
        REPO_ROOT / str(config["reports"]["input_manifest"]),
        {
            "schema_version": "1.0",
            "task_id": "TASK-037C",
            "artifact_type": "frozen_fusion_input_manifest",
            "status": "inputs_and_fusion_predictions_frozen",
            "execution_commit": execution_commit,
            "lineage": config["lineage"],
            "source_report_hashes": config["report_hashes"],
            "detector_variants": list(DETECTOR_VARIANTS),
            "rule_arms": list(RULE_ARMS),
            "operators": list(FUSION_OPERATORS),
            "fusion_arm_count": 16,
            "kpi_count": len(inputs.kpi_ids),
            "source_prediction_record_count": len(inputs.source_records),
            "source_prediction_records": list(inputs.source_records),
            "inner_rule_recovery": {
                "status": inputs.inner_rule_recovery["status"],
                "arm_count": inputs.inner_rule_recovery["arm_count"],
                "labels_loaded": False,
                "records": inputs.inner_rule_recovery["records"],
            },
            "fusion_prediction_record_count": freeze["record_count"],
            "fusion_prediction_freeze_hash": freeze["freeze_hash"],
            "fusion_prediction_records": freeze["records"],
            "all_fusion_predictions_frozen_before_labels": True,
            "test_artifacts_accessed": False,
        },
    )

    freeze_path = (
        REPO_ROOT / str(config["private_root"]) / "manifests/fusion_prediction_hashes.private.json"
    )
    inner_labels = _load_labels_after_complete_freeze(
        config, inputs, freeze_path, "inner"
    )
    (
        inner_detector,
        _inner_rule,
        inner_fusion,
        inner_contributions,
    ) = _evaluate_split(
        config, inputs, fusion_predictions, inner_labels, "inner"
    )
    inner_report = _write_hashed_report(
        REPO_ROOT / str(config["reports"]["inner_diagnostic"]),
        {
            "schema_version": "1.0",
            "task_id": "TASK-037C",
            "artifact_type": "inner_diagnostic_fusion_report",
            "status": "complete_diagnostic_only",
            "selection_performed": False,
            "configuration_changed": False,
            "fusion_arms": _fusion_arm_report(
                inner_fusion, inner_contributions, inputs.kpi_ids
            ),
            "point_adjustment": False,
            "test_accessed": False,
        },
    )

    outer_labels = _load_labels_after_complete_freeze(
        config, inputs, freeze_path, "outer"
    )
    (
        outer_detector,
        _outer_rule,
        outer_fusion,
        outer_contributions,
    ) = _evaluate_split(
        config, inputs, fusion_predictions, outer_labels, "outer"
    )
    outer_report = _write_hashed_report(
        REPO_ROOT / str(config["reports"]["outer_fusion"]),
        {
            "schema_version": "1.0",
            "task_id": "TASK-037C",
            "artifact_type": "outer_diagnostic_fusion_report",
            "status": "passed_frozen_diagnostic_fusion",
            "experiment_type": "generic_frozen_rule_diagnostic_fusion",
            "paper_faithful_aggregator_reproduction": False,
            "inherited_detector_baseline_report_hash": config["report_hashes"][
                "task037b_outer_validation"
            ],
            "inherited_rule_baseline_report_hash": config["report_hashes"][
                "task035b_outer_validation"
            ],
            "fusion_arms": _fusion_arm_report(
                outer_fusion, outer_contributions, inputs.kpi_ids
            ),
            "fusion_arm_selection_performed": False,
            "detector_variant_selection_performed": False,
            "AUROC_AUPRC_computed_for_binary_fusion": False,
            "point_adjustment": False,
            "threshold_optimization": False,
            "test_accessed": False,
        },
    )
    fn_report = _write_hashed_report(
        REPO_ROOT / str(config["reports"]["fn_contribution"]),
        {
            "schema_version": "1.0",
            "task_id": "TASK-037C",
            "artifact_type": "fn_union_contribution_report",
            "status": "complete",
            "arms": _contribution_report_rows(
                outer_contributions, "fn_union_max", inputs.kpi_ids
            ),
            "costs_reported_with_recovery": True,
        },
    )
    fp_report = _write_hashed_report(
        REPO_ROOT / str(config["reports"]["fp_contribution"]),
        {
            "schema_version": "1.0",
            "task_id": "TASK-037C",
            "artifact_type": "fp_intersection_contribution_report",
            "status": "complete",
            "arms": _contribution_report_rows(
                outer_contributions, "fp_intersection_min", inputs.kpi_ids
            ),
            "true_positive_removal_cost_reported": True,
        },
    )
    consistency_report = _write_hashed_report(
        REPO_ROOT / str(config["reports"]["variant_consistency"]),
        {
            "schema_version": "1.0",
            "task_id": "TASK-037C",
            "artifact_type": "variant_direction_consistency_report",
            "status": "complete_non_selective",
            "records": build_variant_consistency(
                outer_fusion,
                outer_detector,
                kpi_ids=inputs.kpi_ids,
                metric_fields=(
                    "precision",
                    "recall",
                    "point_f1",
                    "event_f1",
                    "false_positive_points_per_10000_normal_points",
                ),
            ),
            "variant_selection_performed": False,
        },
    )
    bootstrap_report = _write_hashed_report(
        REPO_ROOT / str(config["reports"]["bootstrap"]),
        {
            "schema_version": "1.0",
            "task_id": "TASK-037C",
            "artifact_type": "paired_kpi_fusion_bootstrap_report",
            "status": "complete_descriptive",
            "resampling_unit": "kpi",
            "formal_significance_claim": False,
            "records": _bootstrap_report(
                config, outer_detector, outer_fusion, inputs.kpi_ids
            ),
        },
    )
    report_path = REPO_ROOT / str(config["reports"]["task_report"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            (
                "# TASK-037C Report",
                "",
                "Final status: `passed_frozen_diagnostic_fusion`.",
                "",
                "The complete two-detector by four-rule by two-operator diagnostic",
                "matrix was computed for all ten frozen KPI series. All source and",
                "derived prediction hashes were frozen before label access. No fusion",
                "arm, detector variant, or rule arm was selected.",
                "",
                "TASK-037C uses generic TASK-035B rules with source-faithful binary",
                "max/min composition. It is not the paper-faithful detector-error-",
                "conditioned ARGOS rule-generation or full Aggregator experiment.",
                "",
                "No detector training, threshold selection, rule generation, provider",
                "call, point adjustment, score-level fusion, or sealed-test access",
                "occurred. Metric magnitude was not a completion criterion.",
                "",
            )
        ),
        encoding="utf-8",
        newline="\n",
    )
    return {
        "status": "passed_frozen_diagnostic_fusion",
        "execution_commit": execution_commit,
        "fusion_arm_count": 16,
        "kpi_count": 10,
        "fusion_prediction_count": len(fusion_hashes),
        "input_report_hash": input_report["report_hash"],
        "inner_report_hash": inner_report["report_hash"],
        "outer_report_hash": outer_report["report_hash"],
        "fn_report_hash": fn_report["report_hash"],
        "fp_report_hash": fp_report["report_hash"],
        "variant_report_hash": consistency_report["report_hash"],
        "bootstrap_report_hash": bootstrap_report["report_hash"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037c_diagnostic_fusion.json",
    )
    args = parser.parse_args()
    result = run_task037c((REPO_ROOT / args.config).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed_frozen_diagnostic_fusion" else 2


if __name__ == "__main__":
    raise SystemExit(main())
