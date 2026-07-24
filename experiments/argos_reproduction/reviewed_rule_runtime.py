"""Replay static-valid Review revisions on generation and full inner values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import read_json
from experiments.argos_reproduction.multi_rule_full_window_runtime import (
    deterministic_replay_matches,
    execute_full_window_rule,
)
from experiments.argos_reproduction.multi_rule_runtime import (
    inspect_image,
    isolation_probe,
)
from experiments.argos_reproduction.repair_failure_replay import (
    _write_values_only,
    execute_container_once,
)
from experiments.argos_reproduction.repaired_rule_runtime import (
    _replay_valid,
    _summary,
)
from experiments.argos_reproduction.review_parent_registry import (
    inner_values_path,
    verify_hashed_report,
    write_hashed_report,
)


def _generation_failure(runs: list[dict[str, Any]], fixture: str) -> str:
    if all(run["status"] == "valid" for run in runs):
        return "reviewed_inner_nondeterministic"
    return (
        "reviewed_generation_target_runtime_failed"
        if fixture == "target"
        else "reviewed_generation_contrast_runtime_failed"
    )


def _static_terminal(record: Mapping[str, Any]) -> str:
    terminal = str(record["terminal_status"])
    if terminal == "reviewed_static_invalid":
        return "reviewed_static_invalid"
    return terminal


def run_reviewed_rules(config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_json(config_path)
    static = verify_hashed_report(ROOT / str(config["reports"]["static"]))
    trigger = verify_hashed_report(ROOT / str(config["reports"]["trigger"]))
    parent_registry = verify_hashed_report(
        ROOT / str(config["reports"]["parent_registry"])
    )
    trigger_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in trigger["records"]
    }
    parent_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in parent_registry["records"]
    }
    image = inspect_image(config)
    if (
        image["image_id"] != config["image"]["expected_image_id"]
        or image["image_digest"] != config["image"]["expected_image_digest"]
    ):
        raise RuntimeError("TASK038C_RUNTIME_IMAGE_MISMATCH")
    isolation = isolation_probe(config, image["image_id"])
    if isolation["status"] != "passed":
        raise RuntimeError("TASK038C_ISOLATION_PROBE_FAILED")
    private_root = ROOT / str(config["private_roots"]["task038c"])
    task037d_root = ROOT / str(config["private_roots"]["task037d"])
    runtime_records: list[dict[str, Any]] = []
    prediction_records: list[dict[str, Any]] = []
    for static_row in static["records"]:
        base = {
            key: static_row[key]
            for key in (
                "review_call_slot_id",
                "branch_id",
                "initial_slot_id",
                "detector_variant",
                "kpi_id",
                "direction",
                "parent_rule_hash",
            )
        }
        if static_row["static_status"] != "static_valid":
            runtime_records.append(
                {
                    **base,
                    "reviewed_rule_hash": static_row.get("reviewed_rule_hash"),
                    "terminal_status": _static_terminal(static_row),
                    "runtime_attempted": False,
                }
            )
            continue
        trigger_row = trigger_by_key[
            (static_row["branch_id"], static_row["initial_slot_id"])
        ]
        if trigger_row["review_trigger"] != "review_required":
            raise RuntimeError("TASK038C_RUNTIME_UNTRIGGERED_REVIEW_SLOT")
        parent_row = parent_by_key[
            (static_row["branch_id"], static_row["initial_slot_id"])
        ]
        if parent_row["parent_rule_hash"] != static_row["parent_rule_hash"]:
            raise RuntimeError("TASK038C_RUNTIME_PARENT_LINEAGE_MISMATCH")
        reviewed_hash = str(static_row["reviewed_rule_hash"])
        rule_path = private_root / "reviewed_rules" / f"{reviewed_hash}.py"
        call_root = (
            private_root / "generation_runtime" / static_row["review_call_slot_id"]
        )
        generation: dict[str, list[dict[str, Any]]] = {}
        terminal: str | None = None
        for fixture in ("target", "contrast"):
            source = (
                task037d_root
                / "targets"
                / f"{fixture}_chunks"
                / f"{static_row['initial_slot_id']}.npz"
            )
            values_path = call_root / fixture / "input_values.npy"
            _write_values_only(
                source,
                values_path,
                str(parent_row[f"{fixture}_chunk_hash"]),
            )
            runs = [
                execute_container_once(
                    config,
                    image_id=image["image_id"],
                    rule_path=rule_path,
                    rule_hash=reviewed_hash,
                    values_path=values_path,
                    output_dir=call_root / fixture / f"run_{replay}",
                    name_parts=(
                        static_row["review_call_slot_id"],
                        fixture,
                        str(replay),
                    ),
                    failure_stage=fixture,
                )
                for replay in (1, 2)
            ]
            generation[fixture] = runs
            if terminal is None and not _replay_valid(runs):
                terminal = _generation_failure(runs, fixture)
        inner_runs: list[dict[str, Any]] = []
        if terminal is None:
            values = inner_values_path(config, str(static_row["kpi_id"]))
            inner_runs = [
                execute_full_window_rule(
                    config,
                    image,
                    run_id=(
                        f"task038c:reviewed:{static_row['review_call_slot_id']}:{replay}"
                    ),
                    rule_path=rule_path,
                    rule_sha256=reviewed_hash,
                    values_path=values,
                    output_directory=(
                        private_root
                        / "reviewed_inner_predictions"
                        / static_row["review_call_slot_id"]
                        / f"replay_{replay}"
                    ),
                )
                for replay in (1, 2)
            ]
            if not all(
                run["runtime_status"] == "executable_rule" for run in inner_runs
            ):
                terminal = "reviewed_inner_runtime_failed"
            elif not deterministic_replay_matches(inner_runs[0], inner_runs[1]):
                terminal = "reviewed_inner_nondeterministic"
        if terminal is None:
            terminal = "reviewed_executable"
        runtime_records.append(
            {
                **base,
                "reviewed_rule_hash": reviewed_hash,
                "terminal_status": terminal,
                "runtime_attempted": True,
                "generation_target_runtime": _summary(generation["target"]),
                "generation_contrast_runtime": _summary(generation["contrast"]),
                "inner_runtime": (
                    {
                        "run_1_status": inner_runs[0]["runtime_status"],
                        "run_2_status": inner_runs[1]["runtime_status"],
                        "run_1_prediction_hash": inner_runs[0].get(
                            "prediction_sha256"
                        ),
                        "run_2_prediction_hash": inner_runs[1].get(
                            "prediction_sha256"
                        ),
                        "prediction_length": inner_runs[0].get("output_count"),
                        "predicted_positive_count": inner_runs[0].get(
                            "predicted_positive_count"
                        ),
                        "inner_input_hash": inner_runs[0].get("input_sha256"),
                    }
                    if inner_runs
                    else None
                ),
            }
        )
        if terminal == "reviewed_executable":
            prediction_records.append(
                {
                    **base,
                    "reviewed_rule_hash": reviewed_hash,
                    "inner_input_hash": inner_runs[0]["input_sha256"],
                    "reviewed_prediction_hash": inner_runs[0][
                        "prediction_sha256"
                    ],
                    "prediction_length": inner_runs[0]["output_count"],
                    "predicted_positive_count": inner_runs[0][
                        "predicted_positive_count"
                    ],
                    "generation_target_runtime_passed": True,
                    "generation_contrast_runtime_passed": True,
                    "inner_replay_passed": True,
                }
            )
    runtime_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "reviewed_rule_runtime_report",
        "review_call_count": len(static["records"]),
        "terminal_record_count": len(runtime_records),
        "reviewed_executable_count": sum(
            row["terminal_status"] == "reviewed_executable"
            for row in runtime_records
        ),
        "image": image,
        "isolation": isolation,
        "labels_mounted": False,
        "detector_predictions_mounted": False,
        "outer_access": False,
        "sealed_test_access": False,
        "host_generated_code_execution": False,
        "repair_agent_calls": 0,
        "raw_predictions_tracked": False,
        "records": runtime_records,
    }
    runtime_report = write_hashed_report(
        ROOT / str(config["reports"]["runtime"]), runtime_report
    )
    prediction_report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "reviewed_prediction_manifest",
        "status": "frozen_before_post_review_metrics",
        "runtime_report_hash": runtime_report["report_hash"],
        "reviewed_executable_count": len(prediction_records),
        "post_review_metrics_computed_during_freeze": False,
        "outer_access": False,
        "sealed_test_access": False,
        "raw_predictions_tracked": False,
        "records": prediction_records,
    }
    prediction_report = write_hashed_report(
        ROOT / str(config["reports"]["reviewed_predictions"]),
        prediction_report,
    )
    return runtime_report, prediction_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    runtime, predictions = run_reviewed_rules((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "terminal_records": runtime["terminal_record_count"],
                "reviewed_executable": predictions["reviewed_executable_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
