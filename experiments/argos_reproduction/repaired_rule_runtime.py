"""Replay static-valid repaired rules twice on target and contrast values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.multi_rule_runtime import (
    inspect_image,
    isolation_probe,
)
from experiments.argos_reproduction.repair_failure_replay import (
    _write_values_only,
    execute_container_once,
    load_repair_population,
    verify_report_hash,
)


def _terminal_from_static(record: Mapping[str, Any]) -> str:
    terminal = str(record["terminal_status"])
    if terminal == "repaired_static_invalid":
        return "repaired_static_invalid"
    return terminal


def _replay_valid(runs: list[dict[str, Any]]) -> bool:
    return bool(
        len(runs) == 2
        and all(item["status"] == "valid" for item in runs)
        and runs[0]["output_hash"] == runs[1]["output_hash"]
        and runs[0]["output_count"] == runs[1]["output_count"]
        and runs[0]["predicted_positive_count"]
        == runs[1]["predicted_positive_count"]
    )


def _runtime_failure(runs: list[dict[str, Any]], fixture: str) -> str:
    if any(
        item.get("failure_category") == "output_contract_failure" for item in runs
    ):
        return "repaired_output_contract_failed"
    if all(item["status"] == "valid" for item in runs):
        return "repaired_nondeterministic"
    return (
        "repaired_target_runtime_failed"
        if fixture == "target"
        else "repaired_contrast_runtime_failed"
    )


def _degeneracy(output_path: Path) -> dict[str, Any]:
    prediction = np.asarray(np.load(output_path, allow_pickle=False)).reshape(-1)
    rate = float(np.mean(prediction == 1)) if len(prediction) else 0.0
    return {
        "all_zero": bool(len(prediction) == 0 or np.all(prediction == 0)),
        "all_one": bool(len(prediction) > 0 and np.all(prediction == 1)),
        "near_all_positive": rate >= 0.95,
        "near_all_negative": rate <= 0.05,
        "predicted_positive_rate": rate,
    }


def _summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_1_status": runs[0]["status"],
        "run_2_status": runs[1]["status"],
        "run_1_output_hash": runs[0].get("output_hash"),
        "run_2_output_hash": runs[1].get("output_hash"),
        "output_count": runs[0].get("output_count"),
        "prediction_hash_replay": (
            runs[0].get("output_hash") is not None
            and runs[0].get("output_hash") == runs[1].get("output_hash")
        ),
        "predicted_positive_count_replay": (
            runs[0].get("predicted_positive_count") is not None
            and runs[0].get("predicted_positive_count")
            == runs[1].get("predicted_positive_count")
        ),
        "input_hash": runs[0].get("input_hash"),
    }


def run_repaired_rules(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    population = load_repair_population(config)
    replay_raw = read_json(ROOT / str(config["reports"]["failure_replay"]))
    replay = verify_report_hash(
        ROOT / str(config["reports"]["failure_replay"]),
        str(replay_raw["report_hash"]),
    )
    replay_by_slot = {item["initial_slot_id"]: item for item in replay["records"]}
    static_raw = read_json(ROOT / str(config["reports"]["static"]))
    static = verify_report_hash(
        ROOT / str(config["reports"]["static"]),
        str(static_raw["report_hash"]),
    )
    static_by_slot = {item["initial_slot_id"]: item for item in static["records"]}
    image = inspect_image(config)
    if image["image_id"] != config["image"]["expected_image_id"]:
        raise RuntimeError("TASK038B_RUNTIME_IMAGE_MISMATCH")
    isolation = isolation_probe(config, image["image_id"])
    if isolation["status"] != "passed":
        raise RuntimeError("TASK038B_ISOLATION_PROBE_FAILED")
    source_root = ROOT / str(config["sources"]["task037d_private_root"])
    private_root = ROOT / str(config["private_root"])
    records: list[dict[str, Any]] = []
    for initial in population:
        slot_id = initial["initial_slot_id"]
        base = {
            key: initial[key]
            for key in (
                "initial_slot_id",
                "initial_rule_hash",
                "detector_variant",
                "kpi_id",
                "direction",
                "initial_runtime_status",
                "repair_reuse_key",
            )
        }
        replay_record = replay_by_slot[slot_id]
        if not replay_record["failure_reproducible"]:
            records.append(
                {
                    **base,
                    "repaired_rule_hash": None,
                    "terminal_status": "blocked_nonreproducible_initial_failure",
                    "runtime_attempted": False,
                }
            )
            continue
        static_record = static_by_slot[slot_id]
        if static_record["static_status"] != "static_valid":
            records.append(
                {
                    **base,
                    "repaired_rule_hash": static_record.get("repaired_rule_hash"),
                    "terminal_status": _terminal_from_static(static_record),
                    "runtime_attempted": False,
                }
            )
            continue
        repaired_hash = str(static_record["repaired_rule_hash"])
        rule_path = private_root / "repaired_rules" / f"{repaired_hash}.py"
        slot_runtime_root = private_root / "runtime" / slot_id
        fixture_runs: dict[str, list[dict[str, Any]]] = {}
        terminal: str | None = None
        for fixture in ("target", "contrast"):
            source = (
                source_root / "targets" / f"{fixture}_chunks" / f"{slot_id}.npz"
            )
            values_path = slot_runtime_root / fixture / "input_values.npy"
            _write_values_only(
                source, values_path, str(initial[f"{fixture}_chunk_hash"])
            )
            runs = [
                execute_container_once(
                    config,
                    image_id=image["image_id"],
                    rule_path=rule_path,
                    rule_hash=repaired_hash,
                    values_path=values_path,
                    output_dir=slot_runtime_root / fixture / f"run_{run_index}",
                    name_parts=(slot_id, repaired_hash, fixture, str(run_index)),
                    failure_stage=fixture,
                )
                for run_index in (1, 2)
            ]
            fixture_runs[fixture] = runs
            if terminal is None and not _replay_valid(runs):
                terminal = _runtime_failure(runs, fixture)
        if terminal is None:
            terminal = "repaired_executable"
        target_runs = fixture_runs.get("target")
        contrast_runs = fixture_runs.get("contrast")
        degeneracy: dict[str, Any] | None = None
        if terminal == "repaired_executable" and target_runs and contrast_runs:
            target_degeneracy = _degeneracy(
                slot_runtime_root / "target" / "run_1" / "output_labels.npy"
            )
            contrast_degeneracy = _degeneracy(
                slot_runtime_root / "contrast" / "run_1" / "output_labels.npy"
            )
            degeneracy = {
                "target": target_degeneracy,
                "contrast": contrast_degeneracy,
                "target_and_contrast_identical": (
                    target_runs[0]["output_hash"]
                    == contrast_runs[0]["output_hash"]
                ),
            }
        records.append(
            {
                **base,
                "repaired_rule_hash": repaired_hash,
                "terminal_status": terminal,
                "runtime_attempted": True,
                "target_runtime": _summary(target_runs) if target_runs else None,
                "contrast_runtime": (
                    _summary(contrast_runs) if contrast_runs else None
                ),
                "degeneracy": degeneracy,
            }
        )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038B",
        "artifact_type": "repaired_rule_runtime_report",
        "frozen_repair_population": 13,
        "terminal_record_count": len(records),
        "repaired_executable_count": sum(
            item["terminal_status"] == "repaired_executable" for item in records
        ),
        "deterministic_replay_count": sum(
            item["terminal_status"] == "repaired_executable" for item in records
        ),
        "image": image,
        "isolation": isolation,
        "labels_mounted": False,
        "detector_predictions_mounted": False,
        "inner_access": False,
        "outer_access": False,
        "sealed_test_access": False,
        "host_generated_code_execution": False,
        "raw_predictions_tracked": False,
        "records": records,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["runtime"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038b_repair_execution.json",
    )
    args = parser.parse_args()
    report = run_repaired_rules((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "terminal_record_count": report["terminal_record_count"],
                "repaired_executable_count": report["repaired_executable_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
