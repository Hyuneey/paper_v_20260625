"""Compute paired inner-only Review effects and descriptive uncertainty."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.direct_event_metrics import (
    binary_vector,
    direct_pa_free_metrics,
)
from experiments.argos_reproduction.expanded_kpi_cohort import read_json
from experiments.argos_reproduction.repair_operability_metrics import wilson_interval
from experiments.argos_reproduction.repair_semantic_drift import structural_summary
from experiments.argos_reproduction.review_parent_registry import (
    detector_prediction_path,
    inner_labels_path,
    parent_rule_path,
    prediction_path,
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.review_regression_samples import compose_direction


def _load_binary(path: Path) -> np.ndarray:
    return binary_vector(np.load(path, allow_pickle=False), path.stem)


def _reviewed_prediction_path(config: Mapping[str, Any], call_id: str) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task038c"])
        / "reviewed_inner_predictions"
        / call_id
        / "replay_1"
        / "output_labels.npy"
    )


def _distribution(values: Sequence[float]) -> dict[str, float | None]:
    if not values:
        return {
            "mean": None,
            "median": None,
            "interquartile_range": None,
            "minimum": None,
            "maximum": None,
        }
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "interquartile_range": float(
            np.percentile(array, 75) - np.percentile(array, 25)
        ),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
    }


def _wilson(success: int, total: int) -> dict[str, Any]:
    lower, upper = wilson_interval(success, total)
    return {
        "successes": success,
        "denominator": total,
        "rate": success / total if total else 0.0,
        "method": "Wilson score interval",
        "confidence_level": 0.95,
        "lower": lower,
        "upper": upper,
        "formal_population_inference": False,
    }


def _contribution(
    direction: str,
    detector: np.ndarray,
    combined: np.ndarray,
    truth: np.ndarray,
) -> dict[str, int]:
    detector_metrics = direct_pa_free_metrics(truth, detector)
    combined_metrics = direct_pa_free_metrics(truth, combined)
    if direction == "FN":
        return {
            "detector_FN_points": detector_metrics["false_negative"],
            "FN_points_recovered": detector_metrics["false_negative"]
            - combined_metrics["false_negative"],
            "added_true_positive_points": combined_metrics["true_positive"]
            - detector_metrics["true_positive"],
            "added_false_positive_points": combined_metrics["false_positive"]
            - detector_metrics["false_positive"],
            "missed_events_recovered": detector_metrics["event_false_negative"]
            - combined_metrics["event_false_negative"],
            "added_false_alarm_events": combined_metrics["event_false_positive"]
            - detector_metrics["event_false_positive"],
        }
    return {
        "detector_FP_points": detector_metrics["false_positive"],
        "FP_points_removed": detector_metrics["false_positive"]
        - combined_metrics["false_positive"],
        "true_positive_points_removed": detector_metrics["true_positive"]
        - combined_metrics["true_positive"],
        "false_alarm_events_removed": detector_metrics["event_false_positive"]
        - combined_metrics["event_false_positive"],
        "true_anomaly_events_removed": detector_metrics["matched_event_count"]
        - combined_metrics["matched_event_count"],
    }


def _structural_drift(
    config: Mapping[str, Any],
    trigger_row: Mapping[str, Any],
    reviewed_hash: str,
) -> dict[str, Any]:
    before = structural_summary(
        parent_rule_path(config, trigger_row).read_text(encoding="utf-8")
    )
    reviewed_path = (
        ROOT
        / str(config["private_roots"]["task038c"])
        / "reviewed_rules"
        / f"{reviewed_hash}.py"
    )
    after = structural_summary(reviewed_path.read_text(encoding="utf-8"))
    return {
        "source_length_delta": after["source_length"] - before["source_length"],
        "AST_node_count_delta": after["ast_node_count"] - before["ast_node_count"],
        "numeric_literal_count_before": len(before["numeric_literals"]),
        "numeric_literal_count_after": len(after["numeric_literals"]),
        "numeric_literals_changed": before["numeric_literals"]
        != after["numeric_literals"],
        "comparison_operator_count_delta": after["comparison_operator_count"]
        - before["comparison_operator_count"],
        "control_flow_node_count_delta": after["control_flow_node_count"]
        - before["control_flow_node_count"],
        "import_set_changed": before["import_set"] != after["import_set"],
        "function_signature_preserved": after["function_signature_preserved"],
    }


def _changed(left: Path, right: Path) -> int | None:
    if not left.is_file() or not right.is_file():
        return None
    before = _load_binary(left)
    after = _load_binary(right)
    if before.shape != after.shape:
        return None
    return int(np.sum(before != after))


def _parent_generation_path(
    config: Mapping[str, Any],
    row: Mapping[str, Any],
    fixture: str,
) -> Path:
    if row["parent_type"] == "repaired_executable":
        return (
            ROOT
            / str(config["private_roots"]["task038b"])
            / "runtime"
            / str(row["initial_slot_id"])
            / fixture
            / "run_1"
            / "output_labels.npy"
        )
    return (
        ROOT
        / str(config["private_roots"]["task037d"])
        / "runtime"
        / str(row["initial_slot_id"])
        / fixture
        / "output_labels.npy"
    )


def _reviewed_generation_path(
    config: Mapping[str, Any], call_id: str, fixture: str
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task038c"])
        / "generation_runtime"
        / call_id
        / fixture
        / "run_1"
        / "output_labels.npy"
    )


def _provider_usage(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    def total(field: str) -> int:
        return sum(int((row.get("usage") or {}).get(field, 0) or 0) for row in rows)

    calls = len(rows)
    input_tokens = total("input_tokens")
    output_tokens = total("output_tokens")
    return {
        "calls": calls,
        "input_tokens_total": input_tokens,
        "cached_input_tokens_total": sum(
            int(
                ((row.get("usage") or {}).get("input_tokens_details") or {}).get(
                    "cached_tokens", 0
                )
                or 0
            )
            for row in rows
        ),
        "output_tokens_total": output_tokens,
        "reasoning_tokens_total": sum(
            int(
                ((row.get("usage") or {}).get("output_tokens_details") or {}).get(
                    "reasoning_tokens", 0
                )
                or 0
            )
            for row in rows
        ),
        "total_tokens": total("total_tokens"),
        "mean_input_tokens_per_call": input_tokens / calls if calls else 0.0,
        "mean_output_tokens_per_call": output_tokens / calls if calls else 0.0,
        "estimated_provider_cost": "not_computed_unfrozen_pricing",
    }


def _summarize_branch(
    records: list[dict[str, Any]],
    branch: str,
    *,
    trigger_rows: Sequence[Mapping[str, Any]],
    provider_rows: Sequence[Mapping[str, Any]],
    static_rows: Sequence[Mapping[str, Any]],
    runtime_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = [row for row in records if row["branch_id"] == branch]
    parents = [row for row in trigger_rows if row["branch_id"] == branch]
    branch_provider = [row for row in provider_rows if row["branch_id"] == branch]
    branch_static = [row for row in static_rows if row["branch_id"] == branch]
    branch_runtime = [row for row in runtime_rows if row["branch_id"] == branch]
    total = len(rows)
    executable = sum(row["outcome"] != "invalid_or_nonexecutable_revision" for row in rows)
    improved = sum(row["outcome"] == "improved" for row in rows)
    equal = sum(row["outcome"] == "equal" for row in rows)
    regressed = sum(row["outcome"] == "regressed" for row in rows)
    invalid = total - executable
    baseline = sum(row.get("detector_baseline_reached") is True for row in rows)
    deltas = [
        row["metric_deltas"]
        for row in rows
        if row["outcome"] != "invalid_or_nonexecutable_revision"
    ]
    improvement_rate = improved / total if total else 0.0
    executable_rate = executable / total if total else 0.0
    label = (
        "substantial_inner_review_signal"
        if improvement_rate >= 0.5 and executable_rate >= 0.8
        else (
            "limited_inner_review_signal"
            if improvement_rate > 0
            else "no_observed_inner_review_signal"
        )
    )
    return {
        "executable_branch_parent_count": len(parents),
        "review_required_count": sum(
            row["review_trigger"] == "review_required" for row in parents
        ),
        "no_review_needed_count": sum(
            row["review_trigger"] == "no_review_needed" for row in parents
        ),
        "review_trigger_rate": total / len(parents) if parents else 0.0,
        "calls_attempted": total,
        "responses_captured": sum(
            row["capture_status"] == "provider_response_captured"
            for row in branch_provider
        ),
        "rules_extracted": sum(
            row["extraction_status"] == "extracted_single_rule"
            for row in branch_static
        ),
        "static_valid_revisions": sum(
            row["static_status"] == "static_valid" for row in branch_static
        ),
        "generation_runtime_valid": sum(
            row["generation_target_runtime"]["run_1_status"] == "valid"
            and row["generation_target_runtime"]["run_2_status"] == "valid"
            and row["generation_contrast_runtime"]["run_1_status"] == "valid"
            and row["generation_contrast_runtime"]["run_2_status"] == "valid"
            for row in branch_runtime
            if row.get("generation_target_runtime") is not None
            and row.get("generation_contrast_runtime") is not None
        ),
        "inner_runtime_valid": sum(
            row["terminal_status"] == "reviewed_executable"
            for row in branch_runtime
        ),
        "reviewed_executable_count": executable,
        "reviewed_executable_and_inner_F1_improved": improved,
        "reviewed_executable_and_inner_F1_equal": equal,
        "reviewed_executable_and_inner_F1_regressed": regressed,
        "invalid_or_nonexecutable_revision": invalid,
        "reviewed_executable_rate": _wilson(executable, total),
        "improvement_success_rate": _wilson(improved, total),
        "nonregression_success_rate": _wilson(improved + equal, total),
        "detector_baseline_reached_rate": _wilson(baseline, total),
        "harmful_or_invalid_rate": (regressed + invalid) / total if total else 0.0,
        "inner_review_signal": label,
        "provider_usage": _provider_usage(branch_provider),
        "conditional_metric_delta_distributions": {
            field: _distribution([float(delta[field]) for delta in deltas])
            for field in (
                "precision_delta",
                "recall_delta",
                "point_F1_delta",
                "event_F1_delta",
                "FP_per_10000_delta",
                "false_alarm_event_delta",
            )
        },
    }


def compute_review_effects(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    trigger = verify_hashed_report(ROOT / str(config["reports"]["trigger"]))
    runtime = verify_hashed_report(ROOT / str(config["reports"]["runtime"]))
    predictions = verify_hashed_report(
        ROOT / str(config["reports"]["reviewed_predictions"])
    )
    provider = verify_hashed_report(ROOT / str(config["reports"]["provider"]))
    static = verify_hashed_report(ROOT / str(config["reports"]["static"]))
    runtime_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in runtime["records"]
    }
    provider_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in provider["slots"]
    }
    effect_records: list[dict[str, Any]] = []
    for parent in trigger["records"]:
        if parent["review_trigger"] != "review_required":
            continue
        key = (parent["branch_id"], parent["initial_slot_id"])
        runtime_row = runtime_by_key[key]
        call_id = runtime_row["review_call_slot_id"]
        base = {
            "review_call_slot_id": call_id,
            "branch_id": parent["branch_id"],
            "initial_slot_id": parent["initial_slot_id"],
            "detector_variant": parent["detector_variant"],
            "kpi_id": parent["kpi_id"],
            "direction": parent["direction"],
            "parent_type": parent["parent_type"],
            "parent_rule_hash": parent["parent_rule_hash"],
            "reviewed_rule_hash": runtime_row.get("reviewed_rule_hash"),
            "response_hash": provider_by_key[key].get("response_hash"),
            "terminal_state": runtime_row["terminal_status"],
        }
        if runtime_row["terminal_status"] != "reviewed_executable":
            effect_records.append(
                {
                    **base,
                    "outcome": "invalid_or_nonexecutable_revision",
                    "detector_baseline_reached": False,
                    "pre_metrics": parent["parent_combined_metrics"],
                    "post_metrics": None,
                    "metric_deltas": None,
                    "structural_drift": None,
                    "prediction_drift": None,
                }
            )
            continue
        detector = _load_binary(
            detector_prediction_path(
                config, parent["detector_variant"], parent["kpi_id"]
            )
        )
        labels = _load_binary(inner_labels_path(config, parent["kpi_id"]))
        parent_prediction = _load_binary(prediction_path(config, parent))
        reviewed_prediction = _load_binary(
            _reviewed_prediction_path(config, call_id)
        )
        parent_combined = np.asarray(
            compose_direction(detector, parent_prediction, parent["direction"]),
            dtype=np.int8,
        )
        reviewed_combined = np.asarray(
            compose_direction(detector, reviewed_prediction, parent["direction"]),
            dtype=np.int8,
        )
        pre = direct_pa_free_metrics(labels, parent_combined)
        post = direct_pa_free_metrics(labels, reviewed_combined)
        delta = float(post["point_f1"]) - float(pre["point_f1"])
        outcome = "improved" if delta > 0 else ("regressed" if delta < 0 else "equal")
        metric_deltas = {
            "precision_delta": float(post["precision"]) - float(pre["precision"]),
            "recall_delta": float(post["recall"]) - float(pre["recall"]),
            "point_F1_delta": delta,
            "event_F1_delta": float(post["event_f1"]) - float(pre["event_f1"]),
            "FP_per_10000_delta": float(
                post["false_positive_points_per_10000_normal_points"]
            )
            - float(pre["false_positive_points_per_10000_normal_points"]),
            "false_alarm_event_delta": float(
                post["false_alarm_events_per_10000_points"]
            )
            - float(pre["false_alarm_events_per_10000_points"]),
        }
        reviewed_hash = str(runtime_row["reviewed_rule_hash"])
        effect_records.append(
            {
                **base,
                "outcome": outcome,
                "detector_baseline_reached": float(post["point_f1"])
                >= float(parent["detector_metrics"]["point_f1"]),
                "pre_metrics": pre,
                "post_metrics": post,
                "metric_deltas": metric_deltas,
                "pre_directional_contribution": _contribution(
                    parent["direction"], detector, parent_combined, labels
                ),
                "post_directional_contribution": _contribution(
                    parent["direction"], detector, reviewed_combined, labels
                ),
                "structural_drift": _structural_drift(
                    config, parent, reviewed_hash
                ),
                "prediction_drift": {
                    "parent_vs_reviewed_target_changed_points": _changed(
                        _parent_generation_path(config, parent, "target"),
                        _reviewed_generation_path(config, call_id, "target"),
                    ),
                    "parent_vs_reviewed_contrast_changed_points": _changed(
                        _parent_generation_path(config, parent, "contrast"),
                        _reviewed_generation_path(config, call_id, "contrast"),
                    ),
                    "parent_vs_reviewed_inner_changed_points": int(
                        np.sum(parent_prediction != reviewed_prediction)
                    ),
                },
            }
        )
    branch_summaries = {
        branch: _summarize_branch(
            effect_records,
            branch,
            trigger_rows=trigger["records"],
            provider_rows=provider["slots"],
            static_rows=static["records"],
            runtime_rows=runtime["records"],
        )
        for branch in ("A2", "A3")
    }
    post_repair = [
        row
        for row in trigger["records"]
        if row["branch_id"] == "A3"
        and row["parent_type"] == "repaired_executable"
    ]
    post_repair_effect = {
        row["initial_slot_id"]: row
        for row in effect_records
        if row["branch_id"] == "A3"
        and row["parent_type"] == "repaired_executable"
    }
    subgroup = {
        "repaired_parent_count": len(post_repair),
        "review_required_count": sum(
            row["review_trigger"] == "review_required" for row in post_repair
        ),
        "no_review_needed_count": sum(
            row["review_trigger"] == "no_review_needed" for row in post_repair
        ),
        "reviewed_executable_count": sum(
            row["outcome"] != "invalid_or_nonexecutable_revision"
            for row in post_repair_effect.values()
        ),
        "post_repair_review_improved_count": sum(
            row["outcome"] == "improved" for row in post_repair_effect.values()
        ),
        "post_repair_review_regressed_count": sum(
            row["outcome"] == "regressed" for row in post_repair_effect.values()
        ),
        "post_repair_review_invalid_count": sum(
            row["outcome"] == "invalid_or_nonexecutable_revision"
            for row in post_repair_effect.values()
        ),
    }
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "review_effect_report",
        "status": "inner_effects_complete",
        "reviewed_prediction_manifest_hash": predictions["report_hash"],
        "A2": branch_summaries["A2"],
        "A3": branch_summaries["A3"],
        "post_repair_review_subgroup": subgroup,
        "conditional_on_executable_metrics": True,
        "point_adjustment": False,
        "outer_access": False,
        "sealed_test_access": False,
        "outer_generalization_claimed": False,
        "semantic_equivalence_claimed": False,
        "raw_predictions_tracked": False,
        "records": effect_records,
    }
    return write_hashed_report(ROOT / str(config["reports"]["effect"]), report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    report = compute_review_effects((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                branch: report[branch]["inner_review_signal"]
                for branch in ("A2", "A3")
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
