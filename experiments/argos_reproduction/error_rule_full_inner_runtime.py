"""Freeze and replay all TASK-037D executable rules on values-only inner windows."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    git_clean_commit,
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.multi_rule_full_window_runtime import (
    deterministic_replay_matches,
    execute_full_window_rule,
)
from experiments.argos_reproduction.multi_rule_runtime import (
    inspect_image,
    isolation_probe,
)


class ErrorRuleInnerRuntimeError(RuntimeError):
    """Raised when TASK-037E inner lineage or execution fails closed."""


def verify_hashed_report(path: Path) -> dict[str, Any]:
    report = read_json(path)
    expected = report.get("report_hash")
    actual = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if expected != actual:
        raise ErrorRuleInnerRuntimeError("TASK037E_SOURCE_REPORT_HASH_MISMATCH")
    return report


def write_hashed_report(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    report["report_hash"] = sha256_json(report)
    write_json(path, report)
    return report


def _git_blob_matches_head(path: Path) -> bool:
    relative = path.resolve().relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout == path.read_bytes()


def build_candidate_registry(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    runtime = verify_hashed_report(ROOT / config["sources"]["task037d_runtime_report"])
    static = verify_hashed_report(ROOT / config["sources"]["task037d_static_report"])
    adequacy = verify_hashed_report(ROOT / config["sources"]["task037d_adequacy_report"])
    if runtime.get("runtime_executable") != config["expected_executable_rule_count"]:
        raise ErrorRuleInnerRuntimeError("TASK037E_EXECUTABLE_COUNT_MISMATCH")
    static_by_slot = {item["slot_id"]: item for item in static["slots"]}
    records: list[dict[str, Any]] = []
    for slot in runtime["slots"]:
        if slot["terminal_status"] != "executable_rule":
            continue
        audit = static_by_slot.get(slot["slot_id"])
        if not audit or audit.get("static_status") != "static_valid":
            raise ErrorRuleInnerRuntimeError("TASK037E_STATIC_RUNTIME_LINEAGE_MISMATCH")
        records.append(
            {
                "slot_id": slot["slot_id"],
                "detector_variant": slot["detector_variant"],
                "kpi_id": slot["kpi_id"],
                "direction": slot["direction"],
                "rule_sha256": slot["rule_sha256"],
                "task037d_terminal_status": slot["terminal_status"],
            }
        )
    records.sort(
        key=lambda item: (
            item["detector_variant"],
            item["kpi_id"],
            item["direction"],
            item["rule_sha256"],
            item["slot_id"],
        )
    )
    if len(records) != int(config["expected_executable_rule_count"]):
        raise ErrorRuleInnerRuntimeError("TASK037E_CANDIDATE_REGISTRY_COUNT_MISMATCH")
    if len({item["slot_id"] for item in records}) != len(records):
        raise ErrorRuleInnerRuntimeError("TASK037E_DUPLICATE_SLOT")
    registry = {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "error_rule_candidate_registry",
        "status": "frozen_before_inner_execution",
        "expected_rule_count": int(config["expected_executable_rule_count"]),
        "records": records,
        "source_report_hashes": {
            "task037d_runtime": runtime["report_hash"],
            "task037d_static": static["report_hash"],
            "task037d_adequacy": adequacy["report_hash"],
        },
        "inner_values_accessed": False,
        "inner_labels_accessed": False,
        "outer_accessed": False,
        "test_accessed": False,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    return write_hashed_report(ROOT / config["candidate_registry"], registry)


def verify_candidate_registry(config: Mapping[str, Any]) -> dict[str, Any]:
    path = ROOT / config["candidate_registry"]
    registry = verify_hashed_report(path)
    if not _git_blob_matches_head(path):
        raise ErrorRuleInnerRuntimeError("TASK037E_CANDIDATE_REGISTRY_NOT_COMMITTED")
    if registry["expected_rule_count"] != int(config["expected_executable_rule_count"]):
        raise ErrorRuleInnerRuntimeError("TASK037E_CANDIDATE_REGISTRY_COUNT_MISMATCH")
    if len(registry["records"]) != registry["expected_rule_count"]:
        raise ErrorRuleInnerRuntimeError("TASK037E_CANDIDATE_REGISTRY_INCOMPLETE")
    return registry


def rule_path(config: Mapping[str, Any], candidate: Mapping[str, Any]) -> Path:
    return (
        ROOT
        / config["private_roots"]["task037d"]
        / "quarantine"
        / str(candidate["direction"]).lower()
        / f"{candidate['rule_sha256']}.py"
    )


def split_values_path(
    config: Mapping[str, Any], kpi_id: str, split: str
) -> Path:
    if split not in ("inner", "outer"):
        raise ErrorRuleInnerRuntimeError("TASK037E_SPLIT_NOT_ALLOWED")
    return (
        ROOT
        / config["private_roots"]["task035b"]
        / split
        / "per_kpi_values"
        / f"{kpi_id}.npy"
    )


def _inner_output_directory(
    config: Mapping[str, Any], slot_id: str, replay: int
) -> Path:
    return (
        ROOT
        / config["private_roots"]["task037e"]
        / "inner"
        / "rule_predictions"
        / slot_id
        / f"replay_{replay}"
    )


def run_inner_rule_replay(config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    execution_commit = git_clean_commit()
    config = read_json(config_path)
    registry = verify_candidate_registry(config)
    image = inspect_image(config)
    if (
        image["image_id"] != config["image"]["expected_image_id"]
        or image["image_digest"] != config["image"]["expected_image_digest"]
    ):
        raise ErrorRuleInnerRuntimeError("TASK037E_RUNTIME_IMAGE_MISMATCH")
    probe = isolation_probe(config, image["image_id"])
    if probe["status"] != "passed":
        raise ErrorRuleInnerRuntimeError("TASK037E_ISOLATION_PROBE_FAILED")
    records: list[dict[str, Any]] = []
    for candidate in registry["records"]:
        rule = rule_path(config, candidate)
        if not rule.is_file() or sha256_file(rule) != candidate["rule_sha256"]:
            raise ErrorRuleInnerRuntimeError("TASK037E_RULE_ARTIFACT_HASH_MISMATCH")
        values = split_values_path(config, candidate["kpi_id"], "inner")
        if not values.is_file():
            raise ErrorRuleInnerRuntimeError("TASK037E_INNER_VALUES_MISSING")
        first = execute_full_window_rule(
            config,
            image,
            run_id=f"task037e:inner:{candidate['slot_id']}:1",
            rule_path=rule,
            rule_sha256=candidate["rule_sha256"],
            values_path=values,
            output_directory=_inner_output_directory(config, candidate["slot_id"], 1),
        )
        second = execute_full_window_rule(
            config,
            image,
            run_id=f"task037e:inner:{candidate['slot_id']}:2",
            rule_path=rule,
            rule_sha256=candidate["rule_sha256"],
            values_path=values,
            output_directory=_inner_output_directory(config, candidate["slot_id"], 2),
        )
        replay_passed = (
            first["runtime_status"] == "executable_rule"
            and second["runtime_status"] == "executable_rule"
            and deterministic_replay_matches(first, second)
        )
        terminal = (
            "inner_rule_executable"
            if replay_passed
            else (
                "deterministic_inner_replay_failure"
                if first.get("runtime_status") == "executable_rule"
                and second.get("runtime_status") == "executable_rule"
                else "failed_inner_prediction_contract"
            )
        )
        records.append(
            {
                **candidate,
                "inner_input_hash": first.get("input_sha256"),
                "inner_prediction_hash": (
                    first.get("prediction_sha256") if replay_passed else None
                ),
                "prediction_length": first.get("output_count"),
                "predicted_positive_count": first.get("predicted_positive_count"),
                "deterministic_replay_passed": replay_passed,
                "terminal_status": terminal,
                "replay_1_status": first.get("runtime_status"),
                "replay_2_status": second.get("runtime_status"),
                "labels_mounted": False,
            }
        )
    counts = Counter(item["terminal_status"] for item in records)
    complete = len(records) == int(config["expected_executable_rule_count"])
    manifest = {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "inner_rule_prediction_manifest",
        "status": "frozen_before_inner_label_access" if complete else "incomplete",
        "candidate_registry_hash": registry["report_hash"],
        "execution_code_commit": execution_commit,
        "record_count": len(records),
        "records": records,
        "all_83_inner_rule_attempts_have_terminal_status": complete,
        "labels_loaded_during_runtime": False,
        "outer_accessed": False,
        "test_accessed": False,
        "raw_predictions_tracked": False,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(ROOT / config["reports"]["inner_predictions"], manifest)
    runtime_report = {
        "schema_version": "1.0",
        "task_id": "TASK-037E",
        "artifact_type": "inner_rule_runtime_report",
        "status": (
            "inner_predictions_frozen"
            if complete and counts.get("deterministic_inner_replay_failure", 0) == 0
            else "deterministic_inner_replay_failure"
        ),
        "execution_code_commit": execution_commit,
        "image": image,
        "isolation": probe,
        "candidate_count": len(records),
        "terminal_status_counts": dict(sorted(counts.items())),
        "deterministic_replay_passed_count": sum(
            item["deterministic_replay_passed"] for item in records
        ),
        "labels_mounted": False,
        "inner_labels_accessed": False,
        "outer_accessed": False,
        "test_accessed": False,
        "provider_calls": 0,
        "agent_calls": 0,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    write_hashed_report(ROOT / config["reports"]["inner_runtime"], runtime_report)
    return runtime_report, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037e_error_conditioned_aggregator.json",
    )
    parser.add_argument("--freeze-candidates", action="store_true")
    args = parser.parse_args()
    config_path = (ROOT / args.config).resolve()
    if args.freeze_candidates:
        registry = build_candidate_registry(config_path)
        print(json.dumps({"candidate_count": len(registry["records"])}, sort_keys=True))
        return 0
    runtime, manifest = run_inner_rule_replay(config_path)
    print(
        json.dumps(
            {
                "status": runtime["status"],
                "records": manifest["record_count"],
                "deterministic": runtime["deterministic_replay_passed_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if runtime["status"] == "inner_predictions_frozen" else 2


if __name__ == "__main__":
    raise SystemExit(main())
