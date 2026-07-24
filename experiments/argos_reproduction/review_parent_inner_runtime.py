"""Freeze TASK-038C parent predictions before inner-label access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.error_rule_full_inner_runtime import (
    verify_hashed_report as verify_task037e_report,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_file,
)
from experiments.argos_reproduction.multi_rule_full_window_runtime import (
    deterministic_replay_matches,
    execute_full_window_rule,
)
from experiments.argos_reproduction.multi_rule_runtime import (
    inspect_image,
    isolation_probe,
)
from experiments.argos_reproduction.review_parent_registry import (
    ReviewParentRegistryError,
    build_parent_registry,
    initial_prediction_path,
    inner_values_path,
    parent_rule_path,
    repaired_prediction_path,
    verify_hashed_report,
    write_hashed_report,
)


def _repaired_output_root(config: dict[str, Any], slot_id: str, replay: int) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task038c"])
        / "parent_inner_predictions"
        / slot_id
        / f"replay_{replay}"
    )


def freeze_parent_predictions(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    registry = build_parent_registry(config_path)
    source_manifest = verify_task037e_report(
        ROOT / str(config["sources"]["task037e_inner_predictions"])
    )
    if (
        source_manifest["report_hash"]
        != config["source_hashes"]["task037e_inner_prediction_manifest"]
        or source_manifest["record_count"] != 83
    ):
        raise ReviewParentRegistryError("TASK038C_TASK037E_INNER_LINEAGE_MISMATCH")
    source_by_slot = {row["slot_id"]: row for row in source_manifest["records"]}
    executable = [row for row in registry["records"] if row["review_eligible"]]
    unique: dict[str, dict[str, Any]] = {}
    for row in executable:
        unique.setdefault(str(row["parent_rule_hash"]), row)
    if len(unique) != int(config["counts"]["unique_parent_rules"]):
        raise ReviewParentRegistryError("TASK038C_UNIQUE_PARENT_COUNT_MISMATCH")
    image = inspect_image(config)
    if (
        image["image_id"] != config["image"]["expected_image_id"]
        or image["image_digest"] != config["image"]["expected_image_digest"]
    ):
        raise ReviewParentRegistryError("TASK038C_RUNTIME_IMAGE_MISMATCH")
    isolation = isolation_probe(config, image["image_id"])
    if isolation["status"] != "passed":
        raise ReviewParentRegistryError("TASK038C_ISOLATION_PROBE_FAILED")
    unique_results: dict[str, dict[str, Any]] = {}
    for parent_hash, row in sorted(unique.items()):
        slot_id = str(row["initial_slot_id"])
        if row["parent_type"] != "repaired_executable":
            source = source_by_slot.get(slot_id)
            path = initial_prediction_path(config, slot_id)
            if (
                source is None
                or not source["deterministic_replay_passed"]
                or not path.is_file()
                or sha256_file(path) != source["inner_prediction_hash"]
            ):
                raise ReviewParentRegistryError(
                    "TASK038C_INITIAL_PARENT_PREDICTION_HASH_MISMATCH"
                )
            unique_results[parent_hash] = {
                "initial_slot_id": slot_id,
                "parent_rule_hash": parent_hash,
                "parent_type": row["parent_type"],
                "inner_input_hash": source["inner_input_hash"],
                "parent_prediction_hash": source["inner_prediction_hash"],
                "prediction_length": source["prediction_length"],
                "predicted_positive_count": source["predicted_positive_count"],
                "prediction_source": "reused_TASK037E",
                "deterministic_replay_passed": True,
            }
            continue
        rule = parent_rule_path(config, row)
        values = inner_values_path(config, str(row["kpi_id"]))
        runs = [
            execute_full_window_rule(
                config,
                image,
                run_id=f"task038c:parent:{slot_id}:{replay}",
                rule_path=rule,
                rule_sha256=parent_hash,
                values_path=values,
                output_directory=_repaired_output_root(config, slot_id, replay),
            )
            for replay in (1, 2)
        ]
        passed = (
            all(run["runtime_status"] == "executable_rule" for run in runs)
            and deterministic_replay_matches(runs[0], runs[1])
        )
        unique_results[parent_hash] = {
            "initial_slot_id": slot_id,
            "parent_rule_hash": parent_hash,
            "parent_type": row["parent_type"],
            "inner_input_hash": runs[0].get("input_sha256"),
            "parent_prediction_hash": (
                runs[0].get("prediction_sha256") if passed else None
            ),
            "prediction_length": runs[0].get("output_count"),
            "predicted_positive_count": runs[0].get("predicted_positive_count"),
            "prediction_source": "new_repaired_rule_replay",
            "deterministic_replay_passed": passed,
            "replay_1_status": runs[0].get("runtime_status"),
            "replay_2_status": runs[1].get("runtime_status"),
        }
    logical_records: list[dict[str, Any]] = []
    for row in executable:
        result = unique_results[str(row["parent_rule_hash"])]
        logical_records.append(
            {
                "branch_id": row["branch_id"],
                "initial_slot_id": row["initial_slot_id"],
                "detector_variant": row["detector_variant"],
                "kpi_id": row["kpi_id"],
                "direction": row["direction"],
                "parent_type": row["parent_type"],
                "parent_rule_hash": row["parent_rule_hash"],
                "inner_input_hash": result["inner_input_hash"],
                "parent_prediction_hash": result["parent_prediction_hash"],
                "prediction_length": result["prediction_length"],
                "predicted_positive_count": result["predicted_positive_count"],
                "prediction_source": result["prediction_source"],
                "deterministic_replay_passed": result[
                    "deterministic_replay_passed"
                ],
            }
        )
    complete = (
        len(logical_records) == int(config["counts"]["logical_executable_parents"])
        and all(row["deterministic_replay_passed"] for row in logical_records)
    )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "review_parent_prediction_manifest",
        "status": (
            "frozen_before_inner_label_access"
            if complete
            else "failed_parent_inner_prediction_freeze"
        ),
        "parent_registry_hash": registry["report_hash"],
        "source_TASK037E_manifest_hash": source_manifest["report_hash"],
        "unique_parent_rule_count": len(unique_results),
        "logical_parent_record_count": len(logical_records),
        "reused_TASK037E_count": sum(
            row["prediction_source"] == "reused_TASK037E"
            for row in unique_results.values()
        ),
        "new_repaired_rule_replay_count": sum(
            row["prediction_source"] == "new_repaired_rule_replay"
            for row in unique_results.values()
        ),
        "all_parent_predictions_frozen_before_label_access": complete,
        "labels_loaded_during_freeze": False,
        "detector_predictions_mounted": False,
        "outer_access": False,
        "sealed_test_access": False,
        "image": image,
        "isolation": isolation,
        "unique_parent_records": list(unique_results.values()),
        "records": logical_records,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["parent_predictions"]), report
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    report = freeze_parent_predictions((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "status": report["status"],
                "unique_parents": report["unique_parent_rule_count"],
                "logical_parents": report["logical_parent_record_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "frozen_before_inner_label_access" else 2


if __name__ == "__main__":
    raise SystemExit(main())
