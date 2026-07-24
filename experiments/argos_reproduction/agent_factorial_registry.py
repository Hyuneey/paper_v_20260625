"""Build the frozen 96-slot and 384-branch TASK-038A registries."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.agent_branch_state import (
    BranchId,
    branch_plan,
    repair_trigger,
)
from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_json,
    write_json,
)


class AgentFactorialRegistryError(RuntimeError):
    """Raised when frozen TASK-037D lineage cannot form the factorial registry."""


def verify_hashed_report(path: Path, expected_hash: str) -> dict[str, Any]:
    report = read_json(path)
    stored = report.get("report_hash")
    actual = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    if stored != actual or stored != expected_hash:
        raise AgentFactorialRegistryError("TASK038A_SOURCE_REPORT_HASH_MISMATCH")
    return report


def write_hashed_report(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    payload["report_hash"] = sha256_json(payload)
    write_json(path, payload)
    return payload


def build_initial_rule_registry(config: Mapping[str, Any]) -> dict[str, Any]:
    sources = config["sources"]
    expected = config["source_report_hashes"]
    request = verify_hashed_report(
        ROOT / sources["task037d_request_manifest"],
        expected["task037d_request_manifest"],
    )
    static = verify_hashed_report(
        ROOT / sources["task037d_static_report"],
        expected["task037d_static_report"],
    )
    runtime = verify_hashed_report(
        ROOT / sources["task037d_runtime_report"],
        expected["task037d_runtime_report"],
    )
    adequacy = verify_hashed_report(
        ROOT / sources["task037d_adequacy_report"],
        expected["task037d_adequacy_report"],
    )
    request_by_slot = {row["slot_id"]: row for row in request["slots"]}
    static_by_slot = {row["slot_id"]: row for row in static["slots"]}
    runtime_by_slot = {row["slot_id"]: row for row in runtime["slots"]}
    if not (
        len(request_by_slot)
        == len(static_by_slot)
        == len(runtime_by_slot)
        == int(config["population"]["initial_rule_slots"])
    ):
        raise AgentFactorialRegistryError("TASK038A_INITIAL_SLOT_COUNT_MISMATCH")
    records: list[dict[str, Any]] = []
    for slot_id in sorted(request_by_slot):
        request_row = request_by_slot[slot_id]
        static_row = static_by_slot.get(slot_id)
        runtime_row = runtime_by_slot.get(slot_id)
        if static_row is None or runtime_row is None:
            raise AgentFactorialRegistryError("TASK038A_INITIAL_SLOT_LINEAGE_MISSING")
        common = ("detector_variant", "kpi_id", "direction")
        if any(
            request_row[field] != static_row[field]
            or request_row[field] != runtime_row[field]
            for field in common
        ):
            raise AgentFactorialRegistryError("TASK038A_INITIAL_SLOT_IDENTITY_MISMATCH")
        if static_row.get("static_status") != "static_valid":
            raise AgentFactorialRegistryError("TASK038A_STATIC_VALID_POPULATION_MISMATCH")
        runtime_status = str(runtime_row["terminal_status"])
        executable = runtime_status == "executable_rule"
        record = {
            "initial_slot_id": slot_id,
            "initial_rule_hash": static_row["rule_sha256"],
            "detector_variant": request_row["detector_variant"],
            "kpi_id": request_row["kpi_id"],
            "direction": request_row["direction"],
            "target_chunk_hash": request_row["target_chunk_hash"],
            "contrast_chunk_hash": request_row["contrast_chunk_hash"],
            "split_manifest_hash": request_row["split_manifest_hash"],
            "target_prediction_hash": request_row["target_prediction_hash"],
            "initial_static_valid": True,
            "initial_runtime_status": runtime_status,
            "initial_executable": executable,
            "repair_eligible": repair_trigger(runtime_status, static_valid=True),
            "repair_reuse_key": None if executable else f"REPAIR-{slot_id}",
        }
        records.append(record)
    executable_count = sum(row["initial_executable"] for row in records)
    failed_count = len(records) - executable_count
    if (
        executable_count != int(config["population"]["initial_executable"])
        or failed_count != int(config["population"]["initial_runtime_failed"])
        or sum(row["repair_eligible"] for row in records)
        != int(config["population"]["repair_population"])
    ):
        raise AgentFactorialRegistryError("TASK038A_RUNTIME_POPULATION_MISMATCH")
    return {
        "schema_version": "1.0",
        "task_id": "TASK-038A",
        "artifact_type": "initial_rule_registry",
        "status": "frozen_from_task037d",
        "initial_rule_slots": len(records),
        "initial_static_valid": len(records),
        "initial_executable": executable_count,
        "initial_runtime_failed": failed_count,
        "repair_population": sum(row["repair_eligible"] for row in records),
        "records": records,
        "source_report_hashes": {
            "request": request["report_hash"],
            "static": static["report_hash"],
            "runtime": runtime["report_hash"],
            "adequacy": adequacy["report_hash"],
        },
        "raw_rule_source_included": False,
        "raw_values_included": False,
        "labels_accessed": False,
        "outer_accessed": False,
        "sealed_test_accessed": False,
    }


def build_branch_registry(
    config: Mapping[str, Any], initial_registry: Mapping[str, Any]
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for initial in initial_registry["records"]:
        for branch in BranchId:
            plan = branch_plan(initial, branch.value)
            records.append(
                {
                    "branch_record_id": f"{initial['initial_slot_id']}::{branch.value}",
                    "initial_slot_id": initial["initial_slot_id"],
                    "initial_rule_hash": initial["initial_rule_hash"],
                    "detector_variant": initial["detector_variant"],
                    "kpi_id": initial["kpi_id"],
                    "direction": initial["direction"],
                    "branch_id": branch.value,
                    "parent_rule_hash": initial["initial_rule_hash"],
                    **{
                        key: value
                        for key, value in plan.to_dict().items()
                        if key != "branch_id"
                    },
                    "terminal_status": "protocol_frozen_not_executed",
                }
            )
    expected = int(config["population"]["branch_count"])
    if len(records) != expected:
        raise AgentFactorialRegistryError("TASK038A_BRANCH_COUNT_MISMATCH")
    counts = Counter(row["branch_id"] for row in records)
    if counts != Counter({branch.value: 96 for branch in BranchId}):
        raise AgentFactorialRegistryError("TASK038A_BRANCH_BALANCE_MISMATCH")
    return {
        "schema_version": "1.0",
        "task_id": "TASK-038A",
        "artifact_type": "agent_factorial_branch_registry",
        "status": "frozen_not_executed",
        "branch_count": len(records),
        "branches_per_initial_slot": 4,
        "branch_counts": dict(sorted(counts.items())),
        "initial_registry_hash": initial_registry["report_hash"],
        "records": records,
        "provider_calls_made": 0,
        "inner_labels_accessed": False,
        "outer_accessed": False,
        "sealed_test_accessed": False,
    }


def freeze_registries(config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_json(config_path)
    initial = build_initial_rule_registry(config)
    initial = write_hashed_report(
        ROOT / config["reports"]["initial_registry"], initial
    )
    branches = build_branch_registry(config, initial)
    branches = write_hashed_report(
        ROOT / config["reports"]["branch_registry"], branches
    )
    return initial, branches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038a_agent_factorial_protocol.json",
    )
    args = parser.parse_args()
    initial, branches = freeze_registries((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "initial_rule_slots": initial["initial_rule_slots"],
                "initial_executable": initial["initial_executable"],
                "repair_population": initial["repair_population"],
                "branch_count": branches["branch_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
