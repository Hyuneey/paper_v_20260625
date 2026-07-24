"""Execute each deduplicated TASK-038E physical rule unit exactly once."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping

from experiments.argos_reproduction.expanded_kpi_cohort import (
    git_clean_commit,
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
    ROOT,
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.task038e_branch_aggregator import (
    outer_values_path,
)
from experiments.argos_reproduction.task038e_execution_dedup import (
    existing_outer_prediction_path,
    physical_prediction_path,
    rule_path,
    runtime_hash,
)
from experiments.argos_reproduction.task038e_outer_registry import load_config


class OuterRuntimeError(RuntimeError):
    """Raised when TASK-038E outer execution violates its frozen registry."""


def _committed(path: Path) -> bool:
    relative = path.resolve().relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout == path.read_bytes()


def _copy_reuse(
    config: Mapping[str, Any], row: Mapping[str, Any]
) -> tuple[str, int, int]:
    source = existing_outer_prediction_path(
        config, str(row["reused_source_slot_id_or_null"])
    )
    if sha256_file(source) != row["reused_prediction_hash_or_null"]:
        raise OuterRuntimeError("TASK038E_REUSE_HASH_MISMATCH")
    for replay in (1, 2):
        target = physical_prediction_path(
            config, row["physical_execution_unit_id"], replay
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha256_file(target) != row["reused_prediction_hash_or_null"]:
            raise OuterRuntimeError("TASK038E_REUSE_COPY_HASH_MISMATCH")
    import numpy as np

    output = np.asarray(np.load(source, allow_pickle=False), dtype=np.int8)
    return str(row["reused_prediction_hash_or_null"]), len(output), int(output.sum())


def run_outer_physical_units(config_path: Path) -> dict[str, Any]:
    execution_commit = git_clean_commit()
    config = load_config(config_path)
    manifest_path = ROOT / str(config["reports"]["physical_manifest"])
    registry_path = ROOT / str(config["reports"]["outer_registry"])
    manifest = verify_hashed_report(manifest_path)
    registry = verify_hashed_report(registry_path)
    if (
        not _committed(manifest_path)
        or not _committed(registry_path)
        or manifest["status"] != "frozen_before_outer_value_access"
        or manifest["runtime_hash"] != runtime_hash(config)
    ):
        raise OuterRuntimeError("TASK038E_OUTER_REGISTRY_NOT_COMMITTED")
    image = inspect_image(config)
    if (
        image["image_id"] != config["image"]["expected_image_id"]
        or image["image_digest"] != config["image"]["expected_image_digest"]
    ):
        raise OuterRuntimeError("TASK038E_RUNTIME_IMAGE_MISMATCH")
    isolation = isolation_probe(config, image["image_id"])
    if isolation["status"] != "passed":
        raise OuterRuntimeError("TASK038E_ISOLATION_PROBE_FAILED")
    selected_physical = {
        row["physical_execution_unit_id"]
        for row in manifest["logical_to_physical"]
        if row["logical_record_id"].startswith("BRANCH-")
    }
    records: list[dict[str, Any]] = []
    for row in manifest["records"]:
        unit_id = row["physical_execution_unit_id"]
        values = outer_values_path(config, row["kpi_id"])
        if sha256_file(values) != row["outer_input_hash"]:
            raise OuterRuntimeError("TASK038E_OUTER_INPUT_HASH_MISMATCH")
        base = {
            key: row[key]
            for key in (
                "physical_execution_unit_id",
                "rule_hash",
                "detector_variant",
                "kpi_id",
                "direction",
                "outer_input_hash",
                "runtime_hash",
                "source_kind",
                "reuse_status",
            )
        }
        if row["reuse_status"] == "exact_TASK037E_reuse":
            prediction_hash, length, positive = _copy_reuse(config, row)
            records.append(
                {
                    **base,
                    "terminal_status": "reused_exact_prediction",
                    "runtime_attempted": False,
                    "deterministic_replay_passed": True,
                    "outer_prediction_hash": prediction_hash,
                    "prediction_length": length,
                    "predicted_positive_count": positive,
                    "replay_1_status": "reused_exact",
                    "replay_2_status": "reused_exact",
                    "labels_mounted": False,
                }
            )
            continue
        rule = rule_path(
            config, row["source_kind"], row["rule_hash"], row["direction"]
        )
        first = execute_full_window_rule(
            config,
            image,
            run_id=f"task038e:{unit_id}:1",
            rule_path=rule,
            rule_sha256=row["rule_hash"],
            values_path=values,
            output_directory=physical_prediction_path(config, unit_id, 1).parent,
        )
        second = execute_full_window_rule(
            config,
            image,
            run_id=f"task038e:{unit_id}:2",
            rule_path=rule,
            rule_sha256=row["rule_hash"],
            values_path=values,
            output_directory=physical_prediction_path(config, unit_id, 2).parent,
        )
        replay = (
            first["runtime_status"] == "executable_rule"
            and second["runtime_status"] == "executable_rule"
            and deterministic_replay_matches(first, second)
        )
        terminal = (
            "selected_rule_outer_executable"
            if replay
            else (
                "selected_rule_outer_runtime_failed"
                if unit_id in selected_physical
                else "diagnostic_rule_outer_runtime_failed"
            )
        )
        records.append(
            {
                **base,
                "terminal_status": terminal,
                "runtime_attempted": True,
                "deterministic_replay_passed": replay,
                "outer_prediction_hash": first.get("prediction_sha256")
                if replay
                else None,
                "prediction_length": first.get("output_count"),
                "predicted_positive_count": first.get("predicted_positive_count"),
                "replay_1_status": first.get("runtime_status"),
                "replay_2_status": second.get("runtime_status"),
                "labels_mounted": False,
            }
        )
    counts = Counter(row["terminal_status"] for row in records)
    failures = sum(
        not row["deterministic_replay_passed"] for row in records
    )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "outer_physical_runtime_report",
        "status": (
            "all_physical_predictions_frozen"
            if failures == 0
            else "selected_rule_outer_runtime_failure"
        ),
        "execution_commit": execution_commit,
        "outer_execution_registry_hash": registry["report_hash"],
        "physical_execution_manifest_hash": manifest["report_hash"],
        "physical_execution_unit_count": len(records),
        "terminal_status_counts": dict(sorted(counts.items())),
        "deterministic_prediction_count": len(records) - failures,
        "selected_rule_substitution": False,
        "duplicate_physical_execution_performed": False,
        "outer_labels_loaded_during_runtime": False,
        "provider_calls": 0,
        "agent_calls": 0,
        "sealed_test_access": False,
        "image": image,
        "isolation": isolation,
        "raw_predictions_tracked": False,
        "records": records,
    }
    return write_hashed_report(
        ROOT / str(config["reports"]["outer_runtime"]), report
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038e_outer_branch_comparison.json",
    )
    args = parser.parse_args()
    report = run_outer_physical_units((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "status": report["status"],
                "units": report["physical_execution_unit_count"],
                "counts": report["terminal_status_counts"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "all_physical_predictions_frozen" else 2


if __name__ == "__main__":
    raise SystemExit(main())
