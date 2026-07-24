"""Build the frozen TASK-038C A2/A3 Review parent registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)


class ReviewParentRegistryError(RuntimeError):
    """Raised when the frozen Review parent population is inconsistent."""


def verify_hashed_report(path: Path, expected: str | None = None) -> dict[str, Any]:
    payload = read_json(path)
    observed = payload.get("report_hash")
    material = {key: value for key, value in payload.items() if key != "report_hash"}
    if observed != sha256_json(material) or (expected is not None and observed != expected):
        raise ReviewParentRegistryError("TASK038C_LINEAGE_REPORT_HASH_MISMATCH")
    return payload


def write_hashed_report(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    payload["report_hash"] = sha256_json(payload)
    write_json(path, payload)
    return payload


def verify_commit_ancestor(commit: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ReviewParentRegistryError("TASK038C_REQUIRED_COMMIT_NOT_ANCESTOR")


def verify_upstream_checkout(commit: str) -> None:
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT / 'external' / 'argos'}",
            "-C",
            str(ROOT / "external" / "argos"),
            "rev-parse",
            "HEAD",
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode or result.stdout.strip() != commit:
        raise ReviewParentRegistryError("TASK038C_ARGOS_COMMIT_MISMATCH")


def load_config(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    for key, commit in config["lineage"].items():
        if key == "argos_commit":
            verify_upstream_checkout(str(commit))
            continue
        verify_commit_ancestor(str(commit))
    return config


def parent_rule_path(
    config: Mapping[str, Any], record: Mapping[str, Any]
) -> Path:
    if record["parent_type"] == "repaired_executable":
        return (
            ROOT
            / str(config["private_roots"]["task038b"])
            / "repaired_rules"
            / f"{record['parent_rule_hash']}.py"
        )
    return (
        ROOT
        / str(config["private_roots"]["task037d"])
        / "quarantine"
        / str(record["direction"]).lower()
        / f"{record['parent_rule_hash']}.py"
    )


def inner_values_path(config: Mapping[str, Any], kpi_id: str) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task035b"])
        / "inner"
        / "per_kpi_values"
        / f"{kpi_id}.npy"
    )


def inner_labels_path(config: Mapping[str, Any], kpi_id: str) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task035b"])
        / "inner"
        / "per_kpi_labels"
        / f"{kpi_id}.npy"
    )


def detector_prediction_path(
    config: Mapping[str, Any], variant: str, kpi_id: str
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task037b"])
        / "detectors"
        / variant
        / kpi_id
        / "20260723"
        / "predictions"
        / "inner_prediction.npy"
    )


def initial_prediction_path(
    config: Mapping[str, Any], slot_id: str
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task037e"])
        / "inner"
        / "rule_predictions"
        / slot_id
        / "replay_1"
        / "output_labels.npy"
    )


def repaired_prediction_path(
    config: Mapping[str, Any], slot_id: str
) -> Path:
    return (
        ROOT
        / str(config["private_roots"]["task038c"])
        / "parent_inner_predictions"
        / slot_id
        / "replay_1"
        / "output_labels.npy"
    )


def prediction_path(
    config: Mapping[str, Any], record: Mapping[str, Any]
) -> Path:
    if record["parent_type"] == "repaired_executable":
        return repaired_prediction_path(config, str(record["initial_slot_id"]))
    return initial_prediction_path(config, str(record["initial_slot_id"]))


def build_parent_registry(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    sources = config["sources"]
    hashes = config["source_hashes"]
    initial = verify_hashed_report(
        ROOT / str(sources["task038a_initial_registry"]),
        str(hashes["task038a_initial_registry"]),
    )
    verify_hashed_report(
        ROOT / str(sources["task038a_branch_registry"]),
        str(hashes["task038a_branch_registry"]),
    )
    branch_update = verify_hashed_report(
        ROOT / str(sources["task038b_branch_update"]),
        str(hashes["task038b_branch_update"]),
    )
    runtime = verify_hashed_report(ROOT / str(sources["task038b_runtime"]))
    if len(initial["records"]) != 96:
        raise ReviewParentRegistryError("TASK038C_INITIAL_COUNT_MISMATCH")
    repaired_by_slot = {
        row["initial_slot_id"]: row
        for row in runtime["records"]
        if row["terminal_status"] == "repaired_executable"
    }
    update_by_slot = {row["initial_slot_id"]: row for row in branch_update["records"]}
    if len(repaired_by_slot) != 13 or len(update_by_slot) != 13:
        raise ReviewParentRegistryError("TASK038C_REPAIRED_COUNT_MISMATCH")
    records: list[dict[str, Any]] = []
    for initial_row in sorted(initial["records"], key=lambda row: row["initial_slot_id"]):
        base = {
            "initial_slot_id": initial_row["initial_slot_id"],
            "initial_rule_hash": initial_row["initial_rule_hash"],
            "detector_variant": initial_row["detector_variant"],
            "kpi_id": initial_row["kpi_id"],
            "direction": initial_row["direction"],
            "target_chunk_hash": initial_row["target_chunk_hash"],
            "contrast_chunk_hash": initial_row["contrast_chunk_hash"],
            "split_manifest_hash": initial_row["split_manifest_hash"],
            "repair_reuse_key": initial_row["repair_reuse_key"],
        }
        if initial_row["initial_executable"]:
            records.append(
                {
                    **base,
                    "branch_id": "A2",
                    "parent_type": "initial_executable",
                    "parent_rule_hash": initial_row["initial_rule_hash"],
                    "review_eligible": True,
                    "terminal_state": "parent_ready",
                }
            )
        else:
            records.append(
                {
                    **base,
                    "branch_id": "A2",
                    "parent_type": "initial_nonexecutable",
                    "parent_rule_hash": None,
                    "review_eligible": False,
                    "terminal_state": "review_not_applicable_non_executable",
                }
            )
        if initial_row["initial_executable"]:
            parent_type = "repair_identity"
            parent_hash = initial_row["initial_rule_hash"]
            repair_key = None
        else:
            repaired = repaired_by_slot.get(initial_row["initial_slot_id"])
            update = update_by_slot.get(initial_row["initial_slot_id"])
            if (
                repaired is None
                or update is None
                or update["A3_parent_rule_hash_or_null"]
                != repaired["repaired_rule_hash"]
                or not update["Repair_shared_between_A1_A3"]
            ):
                raise ReviewParentRegistryError("TASK038C_REPAIR_LINEAGE_MISMATCH")
            parent_type = "repaired_executable"
            parent_hash = repaired["repaired_rule_hash"]
            repair_key = initial_row["repair_reuse_key"]
        records.append(
            {
                **base,
                "branch_id": "A3",
                "parent_type": parent_type,
                "parent_rule_hash": parent_hash,
                "repair_reuse_key": repair_key,
                "review_eligible": True,
                "terminal_state": "parent_ready",
            }
        )
    executable = [row for row in records if row["review_eligible"]]
    counts = config["counts"]
    observed = {
        "A2_executable_parent_count": sum(
            row["branch_id"] == "A2" and row["review_eligible"] for row in records
        ),
        "A2_nonapplicable_count": sum(
            row["branch_id"] == "A2" and not row["review_eligible"] for row in records
        ),
        "A3_initial_identity_parent_count": sum(
            row["branch_id"] == "A3" and row["parent_type"] == "repair_identity"
            for row in records
        ),
        "A3_repaired_parent_count": sum(
            row["branch_id"] == "A3"
            and row["parent_type"] == "repaired_executable"
            for row in records
        ),
        "A3_executable_parent_count": sum(
            row["branch_id"] == "A3" and row["review_eligible"] for row in records
        ),
        "total_executable_review_branch_parents": len(executable),
    }
    expected = {
        "A2_executable_parent_count": counts["A2_executable_parents"],
        "A2_nonapplicable_count": counts["A2_nonapplicable"],
        "A3_initial_identity_parent_count": counts["initial_executable"],
        "A3_repaired_parent_count": counts["repaired_executable"],
        "A3_executable_parent_count": counts["A3_executable_parents"],
        "total_executable_review_branch_parents": counts[
            "logical_executable_parents"
        ],
    }
    if observed != expected or len(records) != int(counts["all_branch_records"]):
        raise ReviewParentRegistryError("TASK038C_PARENT_REGISTRY_MISMATCH")
    for row in executable:
        path = parent_rule_path(config, row)
        if not path.is_file() or sha256_file(path) != row["parent_rule_hash"]:
            raise ReviewParentRegistryError("TASK038C_PARENT_RULE_HASH_MISMATCH")
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "review_parent_registry",
        "status": "parent_registry_frozen",
        **observed,
        "all_branch_record_count": len(records),
        "four_branch_design": "component_wise_ablation_with_structural_nonapplicability",
        "outer_access": False,
        "sealed_test_access": False,
        "raw_rule_source_tracked": False,
        "records": records,
    }
    return write_hashed_report(ROOT / str(config["reports"]["parent_registry"]), report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    report = build_parent_registry((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "all_records": report["all_branch_record_count"],
                "executable_parents": report[
                    "total_executable_review_branch_parents"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
