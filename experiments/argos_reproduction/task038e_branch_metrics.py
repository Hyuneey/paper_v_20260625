"""Compute TASK-038E metrics only after the complete outer prediction freeze."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.branch_candidate_predictions import load_binary
from experiments.argos_reproduction.direct_event_metrics import (
    direct_pa_free_metrics,
    metric_distribution,
)
from experiments.argos_reproduction.expanded_kpi_cohort import sha256_file
from experiments.argos_reproduction.multi_rule_outer_validation import (
    direct_pa_free_metrics_from_counts,
)
from experiments.argos_reproduction.review_parent_registry import (
    ROOT,
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.task038e_bootstrap import (
    COMPARISONS,
    FIELDS,
    branch_bootstrap,
)
from experiments.argos_reproduction.task038e_branch_aggregator import (
    ARMS,
    branch_arm_path,
    detector_prediction_path,
    outer_labels_path,
    repair_combined_path,
    review_combined_path,
)
from experiments.argos_reproduction.task038e_contribution_accounting import (
    fn_direction_contribution,
    fp_direction_contribution,
    full_aggregator_contribution,
)
from experiments.argos_reproduction.task038e_generalization_gap import (
    generalization_record,
)
from experiments.argos_reproduction.task038e_outer_prediction_freeze import (
    verify_prediction_freeze,
)
from experiments.argos_reproduction.task038e_outer_registry import (
    load_config,
    source_report,
)
from experiments.argos_reproduction.task038e_repair_utility import (
    utility_classification,
)
from experiments.argos_reproduction.task038e_review_transfer import (
    review_summary,
    transfer_classification,
)
from experiments.argos_reproduction.task038e_variant_consistency import (
    build_variant_consistency,
)


PRIMARY_FIELDS = (
    "precision",
    "recall",
    "point_f1",
    "event_precision",
    "event_recall",
    "event_f1",
    "false_positive_points_per_10000_normal_points",
    "false_alarm_events_per_10000_points",
)


class BranchMetricError(RuntimeError):
    """Raised when frozen outer predictions cannot enter the metric stage."""


def _fp_safety_classifications(
    fp_removed: int,
    tp_removed: int,
    true_events_removed: int,
    point_f1_delta: float,
) -> list[str]:
    categories: list[str] = []
    if fp_removed == 0:
        categories.append("ineffective_FP_correction")
    if fp_removed > 0 and tp_removed == 0 and true_events_removed == 0:
        categories.append("safe_FP_correction")
    if fp_removed > 0 and tp_removed > 0:
        categories.append("costly_FP_correction")
    if point_f1_delta < 0 or true_events_removed > 0:
        categories.append("harmful_FP_correction")
    return categories


def _summary(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    macro = {
        field: float(np.mean([float(row[field]) for row in records]))
        for field in PRIMARY_FIELDS
    }
    point = {
        key: int(sum(int(row[key]) for row in records))
        for key in ("true_positive", "false_positive", "true_negative", "false_negative")
    }
    event = {
        key: int(sum(int(row[key]) for row in records))
        for key in ("event_true_positive", "event_false_positive", "event_false_negative")
    }
    micro = direct_pa_free_metrics_from_counts(point, event)
    count = sum(point.values())
    micro["false_alarm_events_per_10000_points"] = (
        event["event_false_positive"] / count * 10000 if count else 0.0
    )
    return {
        "macro": macro,
        "micro": {**point, **event, **micro},
        "distribution": {
            field: metric_distribution(records, field) for field in PRIMARY_FIELDS
        },
    }


def _load_labels(
    config: Mapping[str, Any], freeze: Mapping[str, Any]
) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    if not freeze["all_outer_predictions_frozen_before_labels"]:
        raise BranchMetricError("TASK038E_OUTER_LABEL_GUARD_FAILED")
    source = source_report(config, "task037e_outer_metrics")
    labels: dict[str, np.ndarray] = {}
    for kpi_id, expected in source["outer_label_hashes"].items():
        path = outer_labels_path(config, kpi_id)
        if sha256_file(path) != expected:
            raise BranchMetricError("TASK038E_OUTER_LABEL_HASH_MISMATCH")
        labels[kpi_id] = load_binary(path)
    if len(labels) != 10:
        raise BranchMetricError("TASK038E_OUTER_LABEL_COUNT_MISMATCH")
    return labels, source["outer_label_hashes"]


def _verify_freeze_paths(
    config: Mapping[str, Any], freeze: Mapping[str, Any]
) -> None:
    for row in freeze["branch_arm_records"]:
        path = branch_arm_path(
            config,
            row["branch_id"],
            row["detector_variant"],
            row["kpi_id"],
            row["arm"],
        )
        if sha256_file(path) != row["outer_prediction_hash"]:
            raise BranchMetricError("TASK038E_BRANCH_PREDICTION_HASH_MISMATCH")
    for row in freeze["review_transfer_records"]:
        for role, field in (
            ("parent", "parent_combined_prediction_hash"),
            ("reviewed", "reviewed_combined_prediction_hash"),
        ):
            if (
                sha256_file(
                    review_combined_path(
                        config, row["logical_record_id"], role
                    )
                )
                != row[field]
            ):
                raise BranchMetricError("TASK038E_REVIEW_PREDICTION_HASH_MISMATCH")
    for row in freeze["repair_utility_records"]:
        if (
            sha256_file(repair_combined_path(config, row["logical_record_id"]))
            != row["combined_prediction_hash"]
        ):
            raise BranchMetricError("TASK038E_REPAIR_PREDICTION_HASH_MISMATCH")


def _branch_metrics(
    config: Mapping[str, Any],
    freeze: Mapping[str, Any],
    labels: Mapping[str, np.ndarray],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in freeze["branch_arm_records"]:
        prediction = load_binary(
            branch_arm_path(
                config,
                row["branch_id"],
                row["detector_variant"],
                row["kpi_id"],
                row["arm"],
            )
        )
        truth = labels[row["kpi_id"]]
        if prediction.shape != truth.shape:
            raise BranchMetricError("TASK038E_BRANCH_METRIC_LENGTH_MISMATCH")
        records.append(
            {
                "branch_id": row["branch_id"],
                "detector_variant": row["detector_variant"],
                "kpi_id": row["kpi_id"],
                "arm": row["arm"],
                **direct_pa_free_metrics(truth, prediction),
            }
        )
    summaries: dict[str, Any] = {}
    for branch in ("A0", "A1", "A2", "A3"):
        summaries[branch] = {}
        for variant in ("LSTMADalpha", "LSTMADbeta"):
            summaries[branch][variant] = {}
            for arm in ARMS:
                rows = [
                    row
                    for row in records
                    if row["branch_id"] == branch
                    and row["detector_variant"] == variant
                    and row["arm"] == arm
                ]
                if len(rows) != 10:
                    raise BranchMetricError("TASK038E_BRANCH_KPI_COVERAGE_INCOMPLETE")
                summaries[branch][variant][arm] = _summary(rows)
    return records, summaries


def _a0_reproduction(
    config: Mapping[str, Any],
    freeze: Mapping[str, Any],
    branch_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    old_predictions = source_report(config, "task037e_outer_predictions")
    old_metrics = source_report(config, "task037e_outer_metrics")
    old_prediction_by_key = {
        (row["detector_variant"], row["kpi_id"]): row
        for row in old_predictions["records"]
    }
    old_metric_by_key = {
        (variant, kpi, arm): metrics
        for variant, block in old_metrics["per_variant"].items()
        for kpi, arms in block["per_kpi"].items()
        for arm, metrics in arms.items()
    }
    field_for_arm = {
        "detector_only": "detector_copy_hash",
        "detector_plus_FN": "detector_plus_FN_hash",
        "detector_plus_FP": "detector_plus_FP_hash",
        "full_aggregator": "full_aggregator_hash",
    }
    freeze_by_key = {
        (row["detector_variant"], row["kpi_id"], row["arm"]): row
        for row in freeze["branch_arm_records"]
        if row["branch_id"] == "A0"
    }
    comparisons: list[dict[str, Any]] = []
    metric_fields = (
        "true_positive",
        "false_positive",
        "true_negative",
        "false_negative",
        "precision",
        "recall",
        "point_f1",
        "event_f1",
        "false_positive_points_per_10000_normal_points",
    )
    for row in branch_records:
        if row["branch_id"] != "A0":
            continue
        key = (row["detector_variant"], row["kpi_id"], row["arm"])
        old_prediction = old_prediction_by_key[key[:2]]
        old_metric = old_metric_by_key[
            (
                key[0],
                key[1],
                key[2]
                .replace("detector_plus_FN", "detector_plus_fn")
                .replace("detector_plus_FP", "detector_plus_fp"),
            )
        ]
        prediction_match = (
            freeze_by_key[key]["outer_prediction_hash"]
            == old_prediction[field_for_arm[key[2]]]
        )
        metric_match = all(row[field] == old_metric[field] for field in metric_fields)
        comparisons.append(
            {
                "detector_variant": key[0],
                "kpi_id": key[1],
                "arm": key[2],
                "prediction_hash_matches": prediction_match,
                "metrics_match": metric_match,
                "exact_match": prediction_match and metric_match,
            }
        )
    exact = len(comparisons) == 80 and all(row["exact_match"] for row in comparisons)
    if not exact:
        raise BranchMetricError("TASK038E_A0_OUTER_REPRODUCTION_FAILED")
    return {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "A0_outer_reproduction_report",
        "status": "exact_reproduction_passed",
        "A0_exact_outer_reproduction": True,
        "comparison_record_count": 80,
        "exact_match_count": 80,
        "records": comparisons,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }


def _contributions(
    config: Mapping[str, Any],
    labels: Mapping[str, np.ndarray],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str, str], dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for branch in ("A0", "A1", "A2", "A3"):
        for variant in ("LSTMADalpha", "LSTMADbeta"):
            for kpi_id in sorted(labels):
                truth = labels[kpi_id]
                values = {
                    arm: load_binary(
                        branch_arm_path(config, branch, variant, kpi_id, arm)
                    )
                    for arm in ARMS
                }
                record = {
                    "branch_id": branch,
                    "detector_variant": variant,
                    "kpi_id": kpi_id,
                    "D_plus_FN": fn_direction_contribution(
                        truth, values["detector_only"], values["detector_plus_FN"]
                    ),
                    "D_plus_FP": fp_direction_contribution(
                        truth, values["detector_only"], values["detector_plus_FP"]
                    ),
                    "Full_vs_D": full_aggregator_contribution(
                        truth,
                        values["detector_only"],
                        values["detector_plus_FP"],
                        values["full_aggregator"],
                    ),
                }
                records.append(record)
                lookup[(branch, variant, kpi_id)] = record
    return records, lookup


def _review_transfer(
    config: Mapping[str, Any],
    freeze: Mapping[str, Any],
    labels: Mapping[str, np.ndarray],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    registry = verify_hashed_report(ROOT / str(config["reports"]["outer_registry"]))
    logical = {
        row["logical_record_id"]: row
        for row in registry["records"]
        if row["evidence_block"] == "review_transfer"
    }
    effects = source_report(config, "task038c_effect")
    effect_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in effects["records"]
        if row["terminal_state"] == "reviewed_executable"
    }
    records: list[dict[str, Any]] = []
    for frozen in freeze["review_transfer_records"]:
        row = logical[frozen["logical_record_id"]]
        effect = effect_by_key[(row["branch_id"], row["initial_slot_id"])]
        parent = direct_pa_free_metrics(
            labels[row["kpi_id"]],
            load_binary(
                review_combined_path(config, row["logical_record_id"], "parent")
            ),
        )
        reviewed = direct_pa_free_metrics(
            labels[row["kpi_id"]],
            load_binary(
                review_combined_path(config, row["logical_record_id"], "reviewed")
            ),
        )
        outer_delta = float(reviewed["point_f1"]) - float(parent["point_f1"])
        records.append(
            {
                "branch_id": row["branch_id"],
                "initial_slot_id": row["initial_slot_id"],
                "detector_variant": row["detector_variant"],
                "kpi_id": row["kpi_id"],
                "direction": row["direction"],
                "parent_rule_hash": row["parent_rule_hash"],
                "reviewed_rule_hash": row["reviewed_rule_hash"],
                "inner_parent_F1": row["inner_parent_combined_F1"],
                "inner_reviewed_F1": row["inner_reviewed_combined_F1"],
                "inner_F1_delta": row["inner_F1_delta"],
                "outer_parent_F1": parent["point_f1"],
                "outer_reviewed_F1": reviewed["point_f1"],
                "outer_F1_delta": outer_delta,
                "inner_precision_delta": effect["metric_deltas"]["precision_delta"],
                "outer_precision_delta": float(reviewed["precision"])
                - float(parent["precision"]),
                "inner_recall_delta": effect["metric_deltas"]["recall_delta"],
                "outer_recall_delta": float(reviewed["recall"])
                - float(parent["recall"]),
                "inner_FP_per_10000_delta": effect["metric_deltas"][
                    "FP_per_10000_delta"
                ],
                "outer_FP_per_10000_delta": float(
                    reviewed["false_positive_points_per_10000_normal_points"]
                )
                - float(parent["false_positive_points_per_10000_normal_points"]),
                "selected_in_TASK038D": row["selected_in_TASK038D"],
                "transfer_classification": transfer_classification(
                    float(row["inner_F1_delta"]), outer_delta
                ),
            }
        )
    summaries = {
        branch: {
            "all": review_summary(
                [row for row in records if row["branch_id"] == branch]
            ),
            "selected": review_summary(
                [
                    row
                    for row in records
                    if row["branch_id"] == branch and row["selected_in_TASK038D"]
                ]
            ),
            "not_selected": review_summary(
                [
                    row
                    for row in records
                    if row["branch_id"] == branch
                    and not row["selected_in_TASK038D"]
                ]
            ),
        }
        for branch in ("A2", "A3")
    }
    return records, summaries


def _repair_utility(
    config: Mapping[str, Any],
    freeze: Mapping[str, Any],
    labels: Mapping[str, np.ndarray],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    registry = verify_hashed_report(ROOT / str(config["reports"]["outer_registry"]))
    logical = {
        row["logical_record_id"]: row
        for row in registry["records"]
        if row["evidence_block"] == "repair_utility"
    }
    records: list[dict[str, Any]] = []
    for frozen in freeze["repair_utility_records"]:
        row = logical[frozen["logical_record_id"]]
        truth = labels[row["kpi_id"]]
        detector = load_binary(
            detector_prediction_path(
                config, row["detector_variant"], row["kpi_id"]
            )
        )
        combined = load_binary(
            repair_combined_path(config, row["logical_record_id"])
        )
        detector_metric = direct_pa_free_metrics(truth, detector)
        combined_metric = direct_pa_free_metrics(truth, combined)
        contribution = (
            fn_direction_contribution(truth, detector, combined)
            if row["direction"] == "FN"
            else fp_direction_contribution(truth, detector, combined)
        )
        classification = utility_classification(
            float(combined_metric["point_f1"]),
            float(detector_metric["point_f1"]),
        )
        records.append(
            {
                "initial_slot_id": row["initial_slot_id"],
                "detector_variant": row["detector_variant"],
                "kpi_id": row["kpi_id"],
                "direction": row["direction"],
                "repaired_rule_hash": row["repaired_rule_hash"],
                "selected_in_A1": row["selected_in_A1"],
                "selected_or_reviewed_in_A3": row["selected_or_reviewed_in_A3"],
                "outer_combined_precision": combined_metric["precision"],
                "outer_combined_recall": combined_metric["recall"],
                "outer_combined_point_F1": combined_metric["point_f1"],
                "outer_combined_event_F1": combined_metric["event_f1"],
                "outer_combined_FP_per_10000": combined_metric[
                    "false_positive_points_per_10000_normal_points"
                ],
                "detector_outer_point_F1": detector_metric["point_f1"],
                "point_F1_delta_vs_detector": float(combined_metric["point_f1"])
                - float(detector_metric["point_f1"]),
                "directional_benefit_and_cost": contribution,
                "classification": classification,
            }
        )
    summary = {
        "repaired_rule_count": len(records),
        "outer_useful_count": sum(
            row["classification"] == "outer_useful" for row in records
        ),
        "outer_equal_count": sum(
            row["classification"] == "outer_equal" for row in records
        ),
        "outer_regressive_count": sum(
            row["classification"] == "outer_regressive" for row in records
        ),
        "selected_A1_useful_count": sum(
            row["selected_in_A1"] and row["classification"] == "outer_useful"
            for row in records
        ),
        "selected_A1_regressive_count": sum(
            row["selected_in_A1"] and row["classification"] == "outer_regressive"
            for row in records
        ),
    }
    return records, summary


def _macro_full_maps(
    records: Sequence[Mapping[str, Any]],
    summaries: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    macro = {
        variant: {
            branch: summaries[branch][variant]["full_aggregator"]["macro"]
            for branch in ("A0", "A1", "A2", "A3")
        }
        for variant in ("LSTMADalpha", "LSTMADbeta")
    }
    per_kpi = {
        variant: {
            kpi: {
                branch: next(
                    row
                    for row in records
                    if row["branch_id"] == branch
                    and row["detector_variant"] == variant
                    and row["kpi_id"] == kpi
                    and row["arm"] == "full_aggregator"
                )
                for branch in ("A0", "A1", "A2", "A3")
            }
            for kpi in sorted(
                {
                    row["kpi_id"]
                    for row in records
                    if row["detector_variant"] == variant
                }
            )
        }
        for variant in ("LSTMADalpha", "LSTMADbeta")
    }
    return macro, per_kpi


def _comparison_records(
    macro: Mapping[str, Any], per_kpi: Mapping[str, Any]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for variant in ("LSTMADalpha", "LSTMADbeta"):
        for left, right in COMPARISONS:
            kpis = sorted(per_kpi[variant])
            records.append(
                {
                    "detector_variant": variant,
                    "comparison": f"{left}_minus_{right}",
                    "macro_differences": {
                        field: float(macro[variant][left][field])
                        - float(macro[variant][right][field])
                        for field in FIELDS
                    },
                    "KPI_win_tie_loss": {
                        field: {
                            "wins": sum(
                                float(per_kpi[variant][kpi][left][field])
                                > float(per_kpi[variant][kpi][right][field])
                                for kpi in kpis
                            ),
                            "ties": sum(
                                float(per_kpi[variant][kpi][left][field])
                                == float(per_kpi[variant][kpi][right][field])
                                for kpi in kpis
                            ),
                            "losses": sum(
                                float(per_kpi[variant][kpi][left][field])
                                < float(per_kpi[variant][kpi][right][field])
                                for kpi in kpis
                            ),
                        }
                        for field in FIELDS
                    },
                }
            )
    return records


def run_branch_metrics(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    freeze = verify_prediction_freeze(config)
    _verify_freeze_paths(config, freeze)
    labels, label_hashes = _load_labels(config, freeze)
    branch_records, summaries = _branch_metrics(config, freeze, labels)
    a0 = _a0_reproduction(config, freeze, branch_records)
    write_hashed_report(ROOT / str(config["reports"]["a0_reproduction"]), a0)
    macro, per_kpi = _macro_full_maps(branch_records, summaries)
    comparisons = _comparison_records(macro, per_kpi)
    branch_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "four_branch_outer_report",
        "status": "passed_four_branch_outer_comparison",
        "prediction_freeze_hash": freeze["report_hash"],
        "logical_branch_arm_predictions": len(branch_records),
        "per_branch_variant_arm": summaries,
        "full_aggregator_comparisons": comparisons,
        "outer_label_hashes": label_hashes,
        "point_adjustment": False,
        "threshold_optimization": False,
        "AUROC_AUPRC_computed_for_binary_arms": False,
        "outer_reselection": False,
        "detector_variant_selection": False,
        "sealed_test_access": False,
        "records": branch_records,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    branch_report = write_hashed_report(
        ROOT / str(config["reports"]["branch_outer"]), branch_report
    )

    contribution_records, contribution_lookup = _contributions(config, labels)
    selection_change = source_report(config, "task038d_change")
    repair_changes: list[dict[str, Any]] = []
    metric_lookup = {
        (row["branch_id"], row["detector_variant"], row["kpi_id"], row["arm"]): row
        for row in branch_records
    }
    selection = source_report(config, "task038d_selection")
    selection_lookup = {
        (row["branch_id"], row["detector_variant"], row["kpi_id"], row["direction"]): row
        for row in selection["records"]
    }
    for row in selection_change["records"]:
        if row["branch_id"] != "A1" or row["change_category"] in ("same_rule", "same_no_op"):
            continue
        arm = "detector_plus_FN" if row["direction"] == "FN" else "detector_plus_FP"
        key = (row["detector_variant"], row["kpi_id"])
        a1_selection = selection_lookup[("A1", *key, row["direction"])]
        repair_changes.append(
            {
                "detector_variant": key[0],
                "kpi_id": key[1],
                "direction": row["direction"],
                "A0_selected_rule_or_noop": row["A0_selected_rule_hash_or_null"],
                "A1_selected_rule": row["branch_selected_rule_hash_or_null"],
                "A1_selected_origin": a1_selection["selected_output_origin"],
                "outer_A0_directional_F1": metric_lookup[
                    ("A0", *key, arm)
                ]["point_f1"],
                "outer_A1_directional_F1": metric_lookup[
                    ("A1", *key, arm)
                ]["point_f1"],
                "outer_delta": float(metric_lookup[("A1", *key, arm)]["point_f1"])
                - float(metric_lookup[("A0", *key, arm)]["point_f1"]),
                "A0_full_F1": metric_lookup[
                    ("A0", *key, "full_aggregator")
                ]["point_f1"],
                "A1_full_F1": metric_lookup[
                    ("A1", *key, "full_aggregator")
                ]["point_f1"],
                "full_delta": float(
                    metric_lookup[("A1", *key, "full_aggregator")]["point_f1"]
                )
                - float(
                    metric_lookup[("A0", *key, "full_aggregator")]["point_f1"]
                ),
                "directional_contribution": contribution_lookup[
                    ("A1", key[0], key[1])
                ]["D_plus_FN" if row["direction"] == "FN" else "D_plus_FP"],
            }
        )
    contribution_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "branch_contribution_report",
        "status": "complete",
        "records": contribution_records,
        "A1_selection_changes": repair_changes,
        "benefits_and_costs_reported_together": True,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(
        ROOT / str(config["reports"]["contribution"]), contribution_report
    )

    review_records, review_summaries = _review_transfer(
        config, freeze, labels
    )
    selected_review = [
        row for row in review_records if row["selected_in_TASK038D"]
    ]
    review_survival = {
        "selected_reviewed_rules": len(selected_review),
        "selected_reviewed_positive_transfer": sum(
            row["transfer_classification"] == "positive_transfer"
            for row in selected_review
        ),
        "selected_reviewed_negative_transfer": sum(
            row["transfer_classification"] == "negative_transfer"
            for row in selected_review
        ),
    }
    review_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "review_outer_transfer_report",
        "status": "complete",
        "reviewed_executable_count": len(review_records),
        "branch_summaries": review_summaries,
        "selected_review_survival": review_survival,
        "causal_interpretation": False,
        "records": review_records,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(
        ROOT / str(config["reports"]["review_transfer"]), review_report
    )

    repair_records, repair_summary = _repair_utility(config, freeze, labels)
    repair_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "repair_outer_utility_report",
        "status": "complete",
        "summary": repair_summary,
        "execution_recovery_treated_as_performance_improvement": False,
        "records": repair_records,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(
        ROOT / str(config["reports"]["repair_utility"]), repair_report
    )

    registry = verify_hashed_report(ROOT / str(config["reports"]["outer_registry"]))
    branch_logical = {
        (
            row["branch_id"],
            row["detector_variant"],
            row["kpi_id"],
            row["direction"],
        ): row
        for row in registry["records"]
        if row["evidence_block"] == "branch_selected"
    }
    fp_records: list[dict[str, Any]] = []
    for branch in ("A2", "A3"):
        for variant in ("LSTMADalpha", "LSTMADbeta"):
            for kpi_id in sorted(labels):
                selected_fp = branch_logical[(branch, variant, kpi_id, "FP")]
                if not selected_fp["outer_execution_required"]:
                    continue
                contribution = contribution_lookup[(branch, variant, kpi_id)][
                    "D_plus_FP"
                ]
                detector_metric = metric_lookup[
                    (branch, variant, kpi_id, "detector_only")
                ]
                fp_metric = metric_lookup[
                    (branch, variant, kpi_id, "detector_plus_FP")
                ]
                delta = float(fp_metric["point_f1"]) - float(
                    detector_metric["point_f1"]
                )
                categories = _fp_safety_classifications(
                    int(contribution["FP_points_removed"]),
                    int(contribution["true_positive_points_removed"]),
                    int(contribution["true_anomaly_events_removed"]),
                    delta,
                )
                fp_records.append(
                    {
                        "branch_id": branch,
                        "detector_variant": variant,
                        "kpi_id": kpi_id,
                        "reviewed_rule": str(
                            selected_fp["selected_output_origin"] or ""
                        ).startswith("reviewed_"),
                        "outer_FP_points_removed": contribution[
                            "FP_points_removed"
                        ],
                        "outer_true_positive_points_removed": contribution[
                            "true_positive_points_removed"
                        ],
                        "outer_false_alarm_events_removed": contribution[
                            "false_alarm_events_removed"
                        ],
                        "outer_true_anomaly_events_removed": contribution[
                            "true_anomaly_events_removed"
                        ],
                        "outer_precision_delta": float(fp_metric["precision"])
                        - float(detector_metric["precision"]),
                        "outer_recall_delta": float(fp_metric["recall"])
                        - float(detector_metric["recall"]),
                        "outer_point_F1_delta": delta,
                        "classifications": categories,
                    }
                )
    fp_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "review_FP_safety_report",
        "status": "complete",
        "selected_FP_rule_count": len(fp_records),
        "harmful_FP_rules_removed_after_observation": 0,
        "records": fp_records,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(ROOT / str(config["reports"]["fp_safety"]), fp_report)

    inner = source_report(config, "task038d_inner_diagnostics")
    inner_records = inner["records"]
    gap_records: list[dict[str, Any]] = []
    arm_map = {
        "D_plus_FN": "detector_plus_FN",
        "D_plus_FP": "detector_plus_FP",
        "Full": "full_aggregator",
    }
    for branch in ("A0", "A1", "A2", "A3"):
        for variant in ("LSTMADalpha", "LSTMADbeta"):
            for inner_arm, outer_arm in arm_map.items():
                inner_f1 = float(
                    np.mean(
                        [
                            row["metrics"]["point_f1"]
                            for row in inner_records
                            if row["branch_id"] == branch
                            and row["detector_variant"] == variant
                            and row["arm"] == inner_arm
                        ]
                    )
                )
                a0_inner = float(
                    np.mean(
                        [
                            row["metrics"]["point_f1"]
                            for row in inner_records
                            if row["branch_id"] == "A0"
                            and row["detector_variant"] == variant
                            and row["arm"] == inner_arm
                        ]
                    )
                )
                gap_records.append(
                    generalization_record(
                        branch=branch,
                        variant=variant,
                        arm=outer_arm,
                        inner_f1=inner_f1,
                        outer_f1=summaries[branch][variant][outer_arm]["macro"][
                            "point_f1"
                        ],
                        a0_inner_f1=a0_inner,
                        a0_outer_f1=summaries["A0"][variant][outer_arm]["macro"][
                            "point_f1"
                        ],
                    )
                )
    gap_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "inner_outer_generalization_gap_report",
        "status": "complete",
        "formal_overfitting_diagnosis": False,
        "records": gap_records,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(
        ROOT / str(config["reports"]["generalization_gap"]), gap_report
    )

    variant_records = build_variant_consistency(macro, per_kpi)
    variant_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "branch_variant_consistency_report",
        "status": "complete",
        "detector_variant_selection": False,
        "records": variant_records,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(
        ROOT / str(config["reports"]["variant_consistency"]), variant_report
    )

    bootstrap_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "branch_paired_bootstrap_report",
        "status": "complete",
        "policy": config["bootstrap"],
        "comparisons": {
            variant: branch_bootstrap(
                per_kpi[variant],
                seed=int(config["bootstrap"]["seed"]),
                resamples=int(config["bootstrap"]["resamples"]),
            )
            for variant in ("LSTMADalpha", "LSTMADbeta")
        },
        "formal_significance_claim": False,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(
        ROOT / str(config["reports"]["bootstrap"]), bootstrap_report
    )

    repair_usage = source_report(config, "task038b_operability")["usage"]
    review_provider = source_report(config, "task038c_provider")
    total_tokens = int(repair_usage["total_tokens"]) + int(
        review_provider["total_tokens"]
    )
    cost_records = []
    for variant in ("LSTMADalpha", "LSTMADbeta"):
        gain = float(macro[variant]["A3"]["point_f1"]) - float(
            macro[variant]["A0"]["point_f1"]
        )
        cost_records.append(
            {
                "detector_variant": variant,
                "A3_minus_A0_full_macro_point_F1": gain,
                "outer_point_F1_gain_per_unique_agent_call": gain / 90,
                "outer_point_F1_gain_per_100k_tokens": gain
                / total_tokens
                * 100000,
            }
        )
    cost_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "agent_cost_report",
        "status": "complete",
        "branch_logical_cost": {
            "A0": {"provider_calls": 0},
            "A1": {"Repair_calls_available_to_branch": 13},
            "A2": {"Review_calls": 36},
            "A3": {"shared_Repair_calls": 13, "Review_calls": 41},
        },
        "unique_Repair_calls": 13,
        "unique_Review_calls": 77,
        "total_unique_agent_calls": 90,
        "Repair_tokens": repair_usage["total_tokens"],
        "Review_tokens": review_provider["total_tokens"],
        "total_provider_tokens": total_tokens,
        "shared_Repair_calls_double_counted": False,
        "estimated_provider_cost": "not_computed_unfrozen_pricing",
        "gain_ratios": cost_records,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(
        ROOT / str(config["reports"]["agent_cost"]), cost_report
    )
    return branch_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038e_outer_branch_comparison.json",
    )
    args = parser.parse_args()
    report = run_branch_metrics((ROOT / args.config).resolve())
    print(json.dumps({"status": report["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
