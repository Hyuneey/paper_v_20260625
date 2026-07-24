"""Compute label-free structural drift diagnostics for Repair revisions."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.repair_failure_replay import (
    load_repair_population,
    verify_report_hash,
)


def _import_set(tree: ast.AST) -> tuple[str, ...]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
    return tuple(sorted(names))


def structural_summary(source: str) -> dict[str, Any]:
    tree = ast.parse(source)
    numeric = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ]
    function = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "inference"
    ]
    signature = bool(
        len(function) == 1
        and len(function[0].args.args) == 1
        and function[0].args.args[0].arg == "sample"
        and not function[0].args.vararg
        and not function[0].args.kwarg
        and not function[0].args.kwonlyargs
    )
    return {
        "source_length": len(source),
        "ast_node_count": sum(1 for _ in ast.walk(tree)),
        "numeric_literals": tuple(numeric),
        "comparison_operator_count": sum(
            len(node.ops) for node in ast.walk(tree) if isinstance(node, ast.Compare)
        ),
        "control_flow_node_count": sum(
            isinstance(node, (ast.If, ast.For, ast.While, ast.Try))
            for node in ast.walk(tree)
        ),
        "import_set": _import_set(tree),
        "function_signature_preserved": signature,
    }


def compute_semantic_drift(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    population = load_repair_population(config)
    runtime_raw = read_json(ROOT / str(config["reports"]["runtime"]))
    runtime = verify_report_hash(
        ROOT / str(config["reports"]["runtime"]),
        str(runtime_raw["report_hash"]),
    )
    runtime_by_slot = {item["initial_slot_id"]: item for item in runtime["records"]}
    task037d_runtime = read_json(ROOT / str(config["sources"]["task037d_runtime"]))
    original_runtime_by_slot = {
        item["slot_id"]: item for item in task037d_runtime["slots"]
    }
    source_root = ROOT / str(config["sources"]["task037d_private_root"])
    private_root = ROOT / str(config["private_root"])
    records: list[dict[str, Any]] = []
    for initial in population:
        slot_id = initial["initial_slot_id"]
        repaired = runtime_by_slot[slot_id]
        repaired_hash = repaired.get("repaired_rule_hash")
        if not repaired_hash:
            records.append(
                {
                    "initial_slot_id": slot_id,
                    "initial_rule_hash": initial["initial_rule_hash"],
                    "repaired_rule_hash": None,
                    "structural_diagnostics_available": False,
                    "nonfailing_fixture_available": False,
                }
            )
            continue
        original_path = (
            source_root
            / "quarantine"
            / str(initial["direction"]).lower()
            / f"{initial['initial_rule_hash']}.py"
        )
        repaired_path = private_root / "repaired_rules" / f"{repaired_hash}.py"
        if sha256_file(original_path) != initial["initial_rule_hash"]:
            raise RuntimeError("TASK038B_ORIGINAL_RULE_HASH_MISMATCH")
        if sha256_file(repaired_path) != repaired_hash:
            raise RuntimeError("TASK038B_REPAIRED_RULE_HASH_MISMATCH")
        try:
            before = structural_summary(original_path.read_text(encoding="utf-8"))
            after = structural_summary(repaired_path.read_text(encoding="utf-8"))
        except SyntaxError:
            records.append(
                {
                    "initial_slot_id": slot_id,
                    "initial_rule_hash": initial["initial_rule_hash"],
                    "repaired_rule_hash": repaired_hash,
                    "structural_diagnostics_available": False,
                    "nonfailing_fixture_available": False,
                }
            )
            continue
        nonfailing_available = False
        original_prediction_hash: str | None = None
        repaired_prediction_hash: str | None = None
        prediction_preserved: bool | None = None
        changed_point_count: int | None = None
        original_record = original_runtime_by_slot[slot_id]
        if (
            initial["initial_runtime_status"] == "contrast_runtime_failed"
            and original_record.get("target_runtime", {}).get("status") == "valid"
            and repaired.get("target_runtime")
        ):
            original_output = (
                source_root
                / "runtime"
                / slot_id
                / "target"
                / "output_labels.npy"
            )
            repaired_output = (
                private_root
                / "runtime"
                / slot_id
                / "target"
                / "run_1"
                / "output_labels.npy"
            )
            if original_output.is_file() and repaired_output.is_file():
                original_values = np.load(original_output, allow_pickle=False)
                repaired_values = np.load(repaired_output, allow_pickle=False)
                nonfailing_available = True
                original_prediction_hash = sha256_file(original_output)
                repaired_prediction_hash = sha256_file(repaired_output)
                prediction_preserved = bool(
                    original_values.shape == repaired_values.shape
                    and np.array_equal(original_values, repaired_values)
                )
                changed_point_count = (
                    int(np.sum(original_values != repaired_values))
                    if original_values.shape == repaired_values.shape
                    else None
                )
        records.append(
            {
                "initial_slot_id": slot_id,
                "initial_rule_hash": initial["initial_rule_hash"],
                "repaired_rule_hash": repaired_hash,
                "structural_diagnostics_available": True,
                "source_length_delta": after["source_length"]
                - before["source_length"],
                "AST_node_count_delta": after["ast_node_count"]
                - before["ast_node_count"],
                "numeric_literal_count_before": len(before["numeric_literals"]),
                "numeric_literal_count_after": len(after["numeric_literals"]),
                "numeric_literals_changed": before["numeric_literals"]
                != after["numeric_literals"],
                "comparison_operator_count_delta": after[
                    "comparison_operator_count"
                ]
                - before["comparison_operator_count"],
                "control_flow_node_count_delta": after[
                    "control_flow_node_count"
                ]
                - before["control_flow_node_count"],
                "import_set_changed": before["import_set"] != after["import_set"],
                "function_signature_preserved": after[
                    "function_signature_preserved"
                ],
                "nonfailing_fixture_available": nonfailing_available,
                "original_nonfailing_prediction_hash": original_prediction_hash,
                "repaired_nonfailing_prediction_hash": repaired_prediction_hash,
                "prediction_preserved": prediction_preserved,
                "changed_point_count": changed_point_count,
            }
        )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038B",
        "artifact_type": "repair_semantic_drift_report",
        "diagnostic_scope": "label_free_structural_only",
        "semantic_equivalence_claimed": False,
        "rejection_based_on_drift": False,
        "raw_rule_source_tracked": False,
        "records": records,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["semantic_drift"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038b_repair_execution.json",
    )
    args = parser.parse_args()
    report = compute_semantic_drift((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "records": len(report["records"]),
                "semantic_equivalence_claimed": report[
                    "semantic_equivalence_claimed"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
