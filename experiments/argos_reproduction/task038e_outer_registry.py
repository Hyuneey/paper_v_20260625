"""Freeze TASK-038E logical and deduplicated physical outer registries."""

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
    read_json,
    sha256_file,
)
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.task038e_execution_dedup import (
    existing_outer_prediction_path,
    physical_key,
    physical_unit_id,
    runtime_hash,
    source_kind_from_origin,
    verify_rule_source,
)


class OuterRegistryError(RuntimeError):
    """Raised when TASK-038E cannot freeze exact outer execution lineage."""


def load_config(path: Path) -> dict[str, Any]:
    config = read_json(path)
    for commit in config["lineage"].values():
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", str(commit), "HEAD"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise OuterRegistryError("TASK038E_REQUIRED_COMMIT_NOT_ANCESTOR")
    for key, source in config["source_files"].items():
        if sha256_file(ROOT / str(source)) != config["source_hashes"][key]:
            raise OuterRegistryError("TASK038E_RUNTIME_SOURCE_HASH_MISMATCH")
    return config


def source_report(config: Mapping[str, Any], key: str) -> dict[str, Any]:
    return verify_hashed_report(
        ROOT / str(config["sources"][key]),
        str(config["source_hashes"][key]),
    )


def _outer_inputs(config: Mapping[str, Any]) -> dict[str, str]:
    runtime = source_report(config, "task037e_outer_runtime")
    result: dict[str, str] = {}
    for row in runtime["records"]:
        value = row.get("outer_input_hash")
        if value:
            prior = result.setdefault(row["kpi_id"], value)
            if prior != value:
                raise OuterRegistryError("TASK038E_OUTER_INPUT_HASH_CONFLICT")
    if len(result) != 10:
        raise OuterRegistryError("TASK038E_OUTER_INPUT_LINEAGE_INCOMPLETE")
    return result


def _selected_lookup(selection: Mapping[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (
            row["branch_id"],
            row["selected_initial_slot_id_or_null"],
            row["selected_rule_hash_or_null"],
        )
        for row in selection["records"]
        if row["selected_candidate_type"] == "branch_rule"
    }


def build_outer_registry(config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_config(config_path)
    selection = source_report(config, "task038d_selection")
    source_report(config, "task038d_origin")
    source_report(config, "task038d_change")
    candidates = source_report(config, "task038d_candidates")
    branch_registry = source_report(config, "task038d_branch_registry")
    reviewed = source_report(config, "task038c_reviewed_predictions")
    parents = source_report(config, "task038c_parent_predictions")
    effects = source_report(config, "task038c_effect")
    repaired = source_report(config, "task038b_runtime")
    previous_runtime = source_report(config, "task037e_outer_runtime")
    source_report(config, "task037b_detector_manifest")
    if (
        selection["selection_unit_count"] != 160
        or not selection["all_selection_units_terminal"]
        or selection["status"] != "passed_four_branch_selection_freeze"
    ):
        raise OuterRegistryError("TASK038E_TASK038D_SELECTION_INCOMPLETE")
    expected_summary = {
        "A0": (19, 1, 2, 18),
        "A1": (20, 0, 2, 18),
        "A2": (20, 0, 10, 10),
        "A3": (20, 0, 9, 11),
    }
    for branch, expected in expected_summary.items():
        summary = selection["branch_summaries"][branch]
        observed = (
            summary["FN_rule_selected_count"],
            summary["FN_no_op_count"],
            summary["FP_rule_selected_count"],
            summary["FP_no_op_count"],
        )
        if observed != expected:
            raise OuterRegistryError("TASK038E_SELECTION_COUNT_MISMATCH")
    input_hashes = _outer_inputs(config)
    candidate_by_key = {
        (row["branch_id"], row["initial_slot_id"], row["output_rule_hash"]): row
        for row in candidates["records"]
    }
    branch_by_key = {
        (row["branch_id"], row["initial_slot_id"], row["output_rule_hash"]): row
        for row in branch_registry["records"]
    }
    selected = _selected_lookup(selection)
    logical: list[dict[str, Any]] = []
    for row in selection["records"]:
        key = (
            row["branch_id"],
            row["selected_initial_slot_id_or_null"],
            row["selected_rule_hash_or_null"],
        )
        candidate = candidate_by_key.get(key)
        logical.append(
            {
                "evidence_block": "branch_selected",
                "logical_record_id": (
                    f"BRANCH-{row['branch_id']}-{row['detector_variant']}-"
                    f"{row['kpi_id']}-{row['direction']}"
                ),
                "branch_id": row["branch_id"],
                "detector_variant": row["detector_variant"],
                "kpi_id": row["kpi_id"],
                "direction": row["direction"],
                "selected_candidate_type": row["selected_candidate_type"],
                "selected_output_origin": row["selected_output_origin"],
                "selected_initial_slot_id": row["selected_initial_slot_id_or_null"],
                "selected_rule_hash": row["selected_rule_hash_or_null"],
                "selected_parent_rule_hash_or_null": row[
                    "selected_parent_rule_hash_or_null"
                ],
                "selected_inner_prediction_hash": (
                    candidate["inner_prediction_hash"] if candidate else None
                ),
                "selection_freeze_hash": selection["report_hash"],
                "outer_execution_required": row["selected_candidate_type"]
                == "branch_rule",
            }
        )
    parent_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in parents["records"]
    }
    effect_by_key = {
        (row["branch_id"], row["initial_slot_id"]): row
        for row in effects["records"]
        if row["terminal_state"] == "reviewed_executable"
    }
    for row in reviewed["records"]:
        key = (row["branch_id"], row["initial_slot_id"])
        parent = parent_by_key[key]
        effect = effect_by_key[key]
        logical.append(
            {
                "evidence_block": "review_transfer",
                "logical_record_id": f"REVIEW-{row['branch_id']}-{row['initial_slot_id']}",
                "branch_id": row["branch_id"],
                "initial_slot_id": row["initial_slot_id"],
                "detector_variant": row["detector_variant"],
                "kpi_id": row["kpi_id"],
                "direction": row["direction"],
                "parent_type": parent["parent_type"],
                "parent_rule_hash": row["parent_rule_hash"],
                "reviewed_rule_hash": row["reviewed_rule_hash"],
                "parent_inner_prediction_hash": parent["parent_prediction_hash"],
                "reviewed_inner_prediction_hash": row["reviewed_prediction_hash"],
                "inner_parent_combined_F1": effect["pre_metrics"]["point_f1"],
                "inner_reviewed_combined_F1": effect["post_metrics"]["point_f1"],
                "inner_F1_delta": effect["metric_deltas"]["point_F1_delta"],
                "selected_in_TASK038D": (
                    row["branch_id"],
                    row["initial_slot_id"],
                    row["reviewed_rule_hash"],
                )
                in selected,
            }
        )
    a1_selected_slots = {
        row["selected_initial_slot_id_or_null"]
        for row in selection["records"]
        if row["branch_id"] == "A1"
        and row["selected_candidate_type"] == "branch_rule"
    }
    a3_selected_slots = {
        row["selected_initial_slot_id_or_null"]
        for row in selection["records"]
        if row["branch_id"] == "A3"
        and row["selected_candidate_type"] == "branch_rule"
    }
    for row in repaired["records"]:
        if row["terminal_status"] != "repaired_executable":
            continue
        logical.append(
            {
                "evidence_block": "repair_utility",
                "logical_record_id": f"REPAIR-{row['initial_slot_id']}",
                "initial_slot_id": row["initial_slot_id"],
                "detector_variant": row["detector_variant"],
                "kpi_id": row["kpi_id"],
                "direction": row["direction"],
                "initial_rule_hash": row["initial_rule_hash"],
                "repaired_rule_hash": row["repaired_rule_hash"],
                "repair_reuse_key": row["repair_reuse_key"],
                "selected_in_A1": row["initial_slot_id"] in a1_selected_slots,
                "selected_or_reviewed_in_A3": row["initial_slot_id"]
                in a3_selected_slots,
            }
        )
    counts = Counter(row["evidence_block"] for row in logical)
    if counts != {
        "branch_selected": 160,
        "review_transfer": 76,
        "repair_utility": 13,
    }:
        raise OuterRegistryError("TASK038E_LOGICAL_REGISTRY_COUNT_MISMATCH")
    registry = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "outer_execution_registry",
        "status": "frozen_before_outer_value_access",
        "selection_freeze_hash": selection["report_hash"],
        "evidence_block_counts": dict(sorted(counts.items())),
        "logical_record_count": len(logical),
        "logical_branch_arm_count_after_composition": 320,
        "outer_values_accessed": False,
        "outer_labels_accessed": False,
        "provider_calls": 0,
        "agent_calls": 0,
        "sealed_test_access": False,
        "raw_rule_source_tracked": False,
        "records": logical,
        "outer_exposure_limitation": config["outer_exposure_limitation"],
    }
    registry = write_hashed_report(
        ROOT / str(config["reports"]["outer_registry"]), registry
    )

    frozen_runtime = runtime_hash(config)
    prior_by_key: dict[tuple[str, str, str, str, str], Mapping[str, Any]] = {}
    for row in previous_runtime["records"]:
        if row.get("outer_prediction_hash"):
            prior_by_key[
                (
                    row["selected_rule_hash"],
                    row["detector_variant"],
                    row["kpi_id"],
                    row["direction"],
                    row["outer_input_hash"],
                )
            ] = row
    units: dict[str, dict[str, Any]] = {}

    def register(
        *,
        logical_id: str,
        rule_hash: str,
        source_kind: str,
        variant: str,
        kpi_id: str,
        direction: str,
    ) -> str:
        verify_rule_source(config, source_kind, rule_hash, direction)
        key = physical_key(
            rule_hash=rule_hash,
            detector_variant=variant,
            kpi_id=kpi_id,
            direction=direction,
            outer_input_hash=input_hashes[kpi_id],
            frozen_runtime_hash=frozen_runtime,
        )
        unit_id = physical_unit_id(key)
        prior = prior_by_key.get(
            (rule_hash, variant, kpi_id, direction, input_hashes[kpi_id])
        )
        if unit_id not in units:
            reuse_hash = None
            reuse_slot = None
            if prior is not None:
                path = existing_outer_prediction_path(
                    config, str(prior["selected_slot_id"])
                )
                if (
                    not path.is_file()
                    or sha256_file(path) != prior["outer_prediction_hash"]
                ):
                    raise OuterRegistryError("TASK038E_REUSE_HASH_MISMATCH")
                reuse_hash = prior["outer_prediction_hash"]
                reuse_slot = prior["selected_slot_id"]
            units[unit_id] = {
                "physical_execution_unit_id": unit_id,
                **key,
                "source_kind": source_kind,
                "reuse_status": (
                    "exact_TASK037E_reuse" if prior is not None else "new_execution"
                ),
                "reused_prediction_hash_or_null": reuse_hash,
                "reused_source_slot_id_or_null": reuse_slot,
                "logical_reference_count": 0,
                "logical_record_ids": [],
            }
        unit = units[unit_id]
        if unit["source_kind"] != source_kind:
            raise OuterRegistryError("TASK038E_PHYSICAL_SOURCE_CONFLICT")
        unit["logical_reference_count"] += 1
        unit["logical_record_ids"].append(logical_id)
        return unit_id

    mappings: list[dict[str, str]] = []
    branch_lineage = {
        (row["branch_id"], row["initial_slot_id"], row["output_rule_hash"]): row
        for row in branch_registry["records"]
    }
    for row in logical:
        block = row["evidence_block"]
        if block == "branch_selected":
            if not row["outer_execution_required"]:
                continue
            lineage = branch_lineage[
                (
                    row["branch_id"],
                    row["selected_initial_slot_id"],
                    row["selected_rule_hash"],
                )
            ]
            entries = [
                (
                    "selected",
                    row["selected_rule_hash"],
                    source_kind_from_origin(lineage["output_origin"]),
                )
            ]
        elif block == "review_transfer":
            entries = [
                (
                    "parent",
                    row["parent_rule_hash"],
                    "repaired" if row["parent_type"] == "repaired_executable" else "initial",
                ),
                ("reviewed", row["reviewed_rule_hash"], "reviewed"),
            ]
        else:
            entries = [("repaired", row["repaired_rule_hash"], "repaired")]
        for role, rule_hash, source_kind in entries:
            unit_id = register(
                logical_id=f"{row['logical_record_id']}:{role}",
                rule_hash=rule_hash,
                source_kind=source_kind,
                variant=row["detector_variant"],
                kpi_id=row["kpi_id"],
                direction=row["direction"],
            )
            mappings.append(
                {
                    "logical_record_id": row["logical_record_id"],
                    "prediction_role": role,
                    "physical_execution_unit_id": unit_id,
                }
            )
    physical_records = sorted(
        units.values(), key=lambda row: row["physical_execution_unit_id"]
    )
    manifest = {
        "schema_version": "1.0",
        "task_id": "TASK-038E",
        "artifact_type": "physical_execution_manifest",
        "status": "frozen_before_outer_value_access",
        "outer_execution_registry_hash": registry["report_hash"],
        "runtime_hash": frozen_runtime,
        "physical_execution_unit_count": len(physical_records),
        "new_execution_unit_count": sum(
            row["reuse_status"] == "new_execution" for row in physical_records
        ),
        "exact_reuse_unit_count": sum(
            row["reuse_status"] == "exact_TASK037E_reuse"
            for row in physical_records
        ),
        "logical_mapping_count": len(mappings),
        "duplicate_physical_execution_performed": False,
        "outer_values_accessed": False,
        "outer_labels_accessed": False,
        "records": physical_records,
        "logical_to_physical": mappings,
    }
    manifest = write_hashed_report(
        ROOT / str(config["reports"]["physical_manifest"]), manifest
    )
    return registry, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038e_outer_branch_comparison.json",
    )
    args = parser.parse_args()
    registry, manifest = build_outer_registry((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "logical": registry["logical_record_count"],
                "physical": manifest["physical_execution_unit_count"],
                "new": manifest["new_execution_unit_count"],
                "reuse": manifest["exact_reuse_unit_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
