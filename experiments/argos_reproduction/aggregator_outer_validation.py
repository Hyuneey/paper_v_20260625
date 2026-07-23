"""Freeze TASK-037E outer Aggregator predictions, then compute one-way metrics."""

from __future__ import annotations

import argparse
from collections import defaultdict
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
    full_aggregator_contribution,
)
from experiments.argos_reproduction.aggregator_variant_consistency import (
    build_aggregator_variant_consistency,
)
from experiments.argos_reproduction.direct_event_metrics import (
    direct_pa_free_metrics,
    metric_distribution,
)
from experiments.argos_reproduction.directional_rule_selection import (
    _detector_prediction_path,
    _label_path,
    _load_binary,
)
from experiments.argos_reproduction.error_rule_full_inner_runtime import (
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_file,
)
from experiments.argos_reproduction.multi_rule_outer_validation import (
    direct_pa_free_metrics_from_counts,
)
from experiments.argos_reproduction.paired_kpi_bootstrap import (
    paired_percentile_bootstrap,
)
from experiments.argos_reproduction.paper_aligned_aggregator import (
    fn_compensation,
    fp_correction,
    frozen_aggregator_order,
    full_aggregator,
    prediction_degeneracy,
)
from experiments.argos_reproduction.selected_rule_outer_runtime import (
    outer_rule_prediction_path,
)


class AggregatorOuterValidationError(RuntimeError):
    """Raised when TASK-037E prediction freeze or metric guards fail."""


ARMS = ("detector_only", "detector_plus_fn", "detector_plus_fp", "full_aggregator")
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
BOOTSTRAP_FIELDS = (
    "precision",
    "recall",
    "point_f1",
    "event_f1",
    "false_positive_points_per_10000_normal_points",
)


def _save_prediction(path: Path, prediction: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, prediction.astype(np.int8, copy=False), allow_pickle=False)
    return sha256_file(path)


def _aggregator_prediction_path(
    config: Mapping[str, Any], variant: str, kpi_id: str, arm: str
) -> Path:
    return (
        ROOT
        / config["private_roots"]["task037e"]
        / "outer"
        / "aggregator_predictions"
        / variant
        / kpi_id
        / f"{arm}.npy"
    )


def _selection_maps(
    config: Mapping[str, Any],
) -> tuple[dict[tuple[str, str], Mapping[str, Any]], dict[tuple[str, str], Mapping[str, Any]]]:
    fn = verify_hashed_report(ROOT / config["reports"]["fn_selection"])
    fp = verify_hashed_report(ROOT / config["reports"]["fp_selection"])
    if fn["selection_unit_count"] != 20 or fp["selection_unit_count"] != 20:
        raise AggregatorOuterValidationError("TASK037E_SELECTION_INCOMPLETE")
    return (
        {(item["detector_variant"], item["kpi_id"]): item for item in fn["records"]},
        {(item["detector_variant"], item["kpi_id"]): item for item in fp["records"]},
    )


def freeze_outer_aggregator_predictions(
    config: Mapping[str, Any],
) -> dict[str, Any]:
    runtime = verify_hashed_report(ROOT / config["reports"]["outer_runtime"])
    if runtime["status"] != "selected_outer_predictions_frozen":
        raise AggregatorOuterValidationError("TASK037E_SELECTED_OUTER_RUNTIME_INCOMPLETE")
    runtime_by_unit = {
        (item["detector_variant"], item["kpi_id"], item["direction"]): item
        for item in runtime["records"]
    }
    fn_map, fp_map = _selection_maps(config)
    detector_manifest = verify_hashed_report(
        ROOT / config["sources"]["task037b_detector_manifest"]
    )
    detector_records = {
        (item["detector_variant"], item["kpi_id"]): item
        for item in detector_manifest["records"]
    }
    records: list[dict[str, Any]] = []
    for key, detector_record in sorted(detector_records.items()):
        variant, kpi_id = key
        detector_path = _detector_prediction_path(config, variant, kpi_id, "outer")
        if sha256_file(detector_path) != detector_record["outer_prediction_hash"]:
            raise AggregatorOuterValidationError("TASK037E_DETECTOR_OUTER_HASH_MISMATCH")
        detector = _load_binary(detector_path)
        fn_selection = fn_map[key]
        fp_selection = fp_map[key]
        fn_runtime = runtime_by_unit[(variant, kpi_id, "FN")]
        fp_runtime = runtime_by_unit[(variant, kpi_id, "FP")]
        fn_rule = None
        if fn_selection["selected_candidate_type"] == "executable_rule":
            fn_path = outer_rule_prediction_path(config, fn_selection["selected_slot_id"])
            if sha256_file(fn_path) != fn_runtime["outer_prediction_hash"]:
                raise AggregatorOuterValidationError("TASK037E_FN_OUTER_HASH_MISMATCH")
            fn_rule = _load_binary(fn_path)
        fp_rule = None
        if fp_selection["selected_candidate_type"] == "executable_rule":
            fp_path = outer_rule_prediction_path(config, fp_selection["selected_slot_id"])
            if sha256_file(fp_path) != fp_runtime["outer_prediction_hash"]:
                raise AggregatorOuterValidationError("TASK037E_FP_OUTER_HASH_MISMATCH")
            fp_rule = _load_binary(fp_path)
        d_fn = detector.copy() if fn_rule is None else fn_compensation(detector, fn_rule)
        d_fp = detector.copy() if fp_rule is None else fp_correction(detector, fp_rule)
        full = full_aggregator(detector, fp_rule=fp_rule, fn_rule=fn_rule)
        arm_values = {
            "detector_only": detector,
            "detector_plus_fn": d_fn,
            "detector_plus_fp": d_fp,
            "full_aggregator": full,
        }
        hashes = {
            arm: _save_prediction(
                _aggregator_prediction_path(config, variant, kpi_id, arm), value
            )
            for arm, value in arm_values.items()
        }
        records.append(
            {
                "detector_variant": variant,
                "kpi_id": kpi_id,
                "detector_prediction_hash": detector_record["outer_prediction_hash"],
                "selected_FN_rule_hash_or_noop": fn_selection["selected_rule_hash"],
                "selected_FN_prediction_hash_or_identity": (
                    fn_runtime.get("outer_prediction_hash")
                    if fn_rule is not None
                    else "identity"
                ),
                "selected_FP_rule_hash_or_noop": fp_selection["selected_rule_hash"],
                "selected_FP_prediction_hash_or_identity": (
                    fp_runtime.get("outer_prediction_hash")
                    if fp_rule is not None
                    else "identity"
                ),
                "detector_plus_FN_hash": hashes["detector_plus_fn"],
                "detector_plus_FP_hash": hashes["detector_plus_fp"],
                "full_aggregator_hash": hashes["full_aggregator"],
                "detector_copy_hash": hashes["detector_only"],
                "point_count": int(len(detector)),
                "predicted_positive_count_per_arm": {
                    arm: int(np.sum(value)) for arm, value in arm_values.items()
                },
                "FN_noop": fn_rule is None,
                "FP_noop": fp_rule is None,
            }
        )
    if len(records) != 20:
        raise AggregatorOuterValidationError("TASK037E_AGGREGATOR_MATRIX_INCOMPLETE")
    manifest = {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "outer_aggregator_prediction_manifest",
        "status": "all_outer_predictions_frozen_before_labels",
        "aggregator_order": list(frozen_aggregator_order()),
        "record_count": len(records),
        "records": records,
        "all_outer_aggregator_predictions_frozen_before_labels": True,
        "outer_labels_loaded": False,
        "test_accessed": False,
        "raw_predictions_tracked": False,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    return write_hashed_report(ROOT / config["reports"]["outer_predictions"], manifest)


def load_outer_labels_after_prediction_freeze(
    config: Mapping[str, Any], manifest: Mapping[str, Any]
) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    if (
        manifest.get("status") != "all_outer_predictions_frozen_before_labels"
        or manifest.get("record_count") != 20
        or not manifest.get("all_outer_aggregator_predictions_frozen_before_labels")
    ):
        raise AggregatorOuterValidationError("TASK037E_OUTER_LABEL_GUARD_FAILED")
    for record in manifest["records"]:
        for arm, field in (
            ("detector_only", "detector_copy_hash"),
            ("detector_plus_fn", "detector_plus_FN_hash"),
            ("detector_plus_fp", "detector_plus_FP_hash"),
            ("full_aggregator", "full_aggregator_hash"),
        ):
            path = _aggregator_prediction_path(
                config, record["detector_variant"], record["kpi_id"], arm
            )
            if sha256_file(path) != record[field]:
                raise AggregatorOuterValidationError("TASK037E_OUTER_FREEZE_HASH_MISMATCH")
    kpis = sorted({item["kpi_id"] for item in manifest["records"]})
    labels: dict[str, np.ndarray] = {}
    hashes: dict[str, str] = {}
    for kpi_id in kpis:
        path = _label_path(config, kpi_id, "outer")
        labels[kpi_id] = _load_binary(path)
        hashes[kpi_id] = sha256_file(path)
    return labels, hashes


def _summary(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    macro = {
        field: float(np.mean([float(item[field]) for item in records]))
        for field in PRIMARY_FIELDS
    }
    point = {
        key: int(sum(int(item[key]) for item in records))
        for key in ("true_positive", "false_positive", "true_negative", "false_negative")
    }
    event = {
        key: int(sum(int(item[key]) for item in records))
        for key in ("event_true_positive", "event_false_positive", "event_false_negative")
    }
    micro = direct_pa_free_metrics_from_counts(point, event)
    point_count = sum(
        int(item["true_positive"])
        + int(item["false_positive"])
        + int(item["true_negative"])
        + int(item["false_negative"])
        for item in records
    )
    micro["false_alarm_events_per_10000_points"] = (
        event["event_false_positive"] / point_count * 10000 if point_count else 0.0
    )
    return {
        "macro": macro,
        "micro": {**point, **event, **micro},
        "distribution": {
            field: metric_distribution(records, field) for field in PRIMARY_FIELDS
        },
    }


def _mean_numeric(records: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    keys = sorted(
        key
        for key in records[0]
        if isinstance(records[0][key], (int, float)) and not isinstance(records[0][key], bool)
    )
    return {
        key: float(np.mean([float(item[key]) for item in records])) for key in keys
    }


def _bootstrap_report(
    config: Mapping[str, Any],
    metrics: Mapping[str, Mapping[str, Mapping[str, Mapping[str, Any]]]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for variant in config["detector_variants"]:
        result[variant] = {}
        kpis = sorted(metrics[variant])
        for arm in ("detector_plus_fn", "detector_plus_fp", "full_aggregator"):
            result[variant][f"{arm}_minus_detector_only"] = {
                field: paired_percentile_bootstrap(
                    [float(metrics[variant][kpi][arm][field]) for kpi in kpis],
                    [
                        float(metrics[variant][kpi]["detector_only"][field])
                        for kpi in kpis
                    ],
                    seed=int(config["bootstrap"]["seed"]),
                    resamples=int(config["bootstrap"]["resamples"]),
                    confidence_level=float(config["bootstrap"]["confidence_level"]),
                )
                for field in BOOTSTRAP_FIELDS
            }
    return {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "aggregator_paired_bootstrap_report",
        "status": "complete",
        "comparisons": result,
        "policy": config["bootstrap"],
        "formal_significance_claim": False,
        "test_accessed": False,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }


def _generic_comparison(
    config: Mapping[str, Any],
    summaries: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    generic = verify_hashed_report(ROOT / config["sources"]["task037c_outer_report"])
    lookup = {
        (item["detector_variant"], item["rule_arm"], item["operator"]): item["summary"]["macro"]
        for item in generic["fusion_arms"]
    }
    records: list[dict[str, Any]] = []
    for variant in config["detector_variants"]:
        records.append(
            {
                "detector_variant": variant,
                "generic_best_1_max": lookup[(variant, "best_1", "fn_union_max")],
                "generic_top_3_max": lookup[(variant, "top_3_or", "fn_union_max")],
                "error_conditioned_D_plus_FN": summaries[variant]["detector_plus_fn"]["macro"],
                "error_conditioned_full_aggregator": summaries[variant]["full_aggregator"]["macro"],
                "generic_best_1_min": lookup[(variant, "best_1", "fp_intersection_min")],
                "generic_top_3_min": lookup[(variant, "top_3_or", "fp_intersection_min")],
                "error_conditioned_D_plus_FP": summaries[variant]["detector_plus_fp"]["macro"],
            }
        )
    return {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "generic_vs_error_conditioned_comparison",
        "status": "descriptive_follow_up_only",
        "records": records,
        "generic_arm_reselection_performed": False,
        "headline_winner_selected": False,
        "same_outer_partition_previously_exposed": True,
        "test_accessed": False,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }


def run_aggregator_outer_validation(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    manifest = freeze_outer_aggregator_predictions(config)
    labels, label_hashes = load_outer_labels_after_prediction_freeze(config, manifest)
    metrics: dict[str, dict[str, dict[str, dict[str, Any]]]] = defaultdict(dict)
    contributions: list[dict[str, Any]] = []
    per_variant_arm: dict[str, dict[str, list[dict[str, Any]]]] = {
        variant: {arm: [] for arm in ARMS} for variant in config["detector_variants"]
    }
    for record in manifest["records"]:
        variant = record["detector_variant"]
        kpi_id = record["kpi_id"]
        truth = labels[kpi_id]
        arm_values = {
            arm: _load_binary(_aggregator_prediction_path(config, variant, kpi_id, arm))
            for arm in ARMS
        }
        if any(value.shape != truth.shape for value in arm_values.values()):
            raise AggregatorOuterValidationError("TASK037E_OUTER_METRIC_LENGTH_MISMATCH")
        unit_metrics: dict[str, dict[str, Any]] = {}
        for arm, prediction in arm_values.items():
            metric = {
                "kpi_id": kpi_id,
                **direct_pa_free_metrics(truth, prediction),
                "degeneracy": prediction_degeneracy(
                    prediction, detector=arm_values["detector_only"]
                ),
            }
            unit_metrics[arm] = metric
            per_variant_arm[variant][arm].append(metric)
        metrics[variant][kpi_id] = unit_metrics
        contributions.append(
            {
                "detector_variant": variant,
                "kpi_id": kpi_id,
                "D_plus_FN": fn_direction_contribution(
                    truth, arm_values["detector_only"], arm_values["detector_plus_fn"]
                ),
                "D_plus_FP": fp_direction_contribution(
                    truth, arm_values["detector_only"], arm_values["detector_plus_fp"]
                ),
                "Full_vs_D": full_aggregator_contribution(
                    truth,
                    arm_values["detector_only"],
                    arm_values["detector_plus_fp"],
                    arm_values["full_aggregator"],
                ),
            }
        )
    summaries = {
        variant: {
            arm: _summary(per_variant_arm[variant][arm]) for arm in ARMS
        }
        for variant in config["detector_variants"]
    }
    outer_report = {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "full_aggregator_outer_validation_report",
        "status": "passed_error_conditioned_full_aggregator_outer_validation",
        "experiment_description": "Paper-aligned one-shot detector-error-conditioned FN/FP rule selection and follow-up outer Aggregator validation.",
        "aggregator_order": list(frozen_aggregator_order()),
        "arms": list(ARMS),
        "per_variant": {
            variant: {
                "per_kpi": {
                    kpi: metrics[variant][kpi] for kpi in sorted(metrics[variant])
                },
                "summaries": summaries[variant],
            }
            for variant in config["detector_variants"]
        },
        "outer_label_hashes": label_hashes,
        "outer_prediction_manifest_hash": manifest["report_hash"],
        "point_adjustment": False,
        "threshold_optimization": False,
        "AUROC_AUPRC_computed_for_binary_aggregator": False,
        "detector_variant_selection_performed": False,
        "outer_based_reselection_performed": False,
        "test_accessed": False,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(ROOT / config["reports"]["outer_aggregator"], outer_report)
    contribution_report = {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "aggregator_contribution_report",
        "status": "complete",
        "records": contributions,
        "per_variant_macro": {
            variant: {
                section: _mean_numeric(
                    [
                        item[section]
                        for item in contributions
                        if item["detector_variant"] == variant
                    ]
                )
                for section in ("D_plus_FN", "D_plus_FP", "Full_vs_D")
            }
            for variant in config["detector_variants"]
        },
        "benefits_and_costs_reported_together": True,
        "test_accessed": False,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(ROOT / config["reports"]["contribution"], contribution_report)
    bootstrap_report = _bootstrap_report(config, metrics)
    write_hashed_report(ROOT / config["reports"]["bootstrap"], bootstrap_report)
    consistency_report = {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "aggregator_variant_consistency_report",
        "status": "complete",
        "records": build_aggregator_variant_consistency(
            metrics,
            kpi_ids=sorted(labels),
            arms=("detector_plus_fn", "detector_plus_fp", "full_aggregator"),
            metric_fields=BOOTSTRAP_FIELDS,
        ),
        "detector_variant_selection_performed": False,
        "test_accessed": False,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(ROOT / config["reports"]["variant_consistency"], consistency_report)
    generic_report = _generic_comparison(config, summaries)
    write_hashed_report(ROOT / config["reports"]["generic_comparison"], generic_report)
    return outer_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037e_error_conditioned_aggregator.json",
    )
    args = parser.parse_args()
    report = run_aggregator_outer_validation((ROOT / args.config).resolve())
    print(json.dumps({"status": report["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
