"""Run TASK-037D static-valid rules on values-only target and contrast chunks."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Any, Mapping

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
from experiments.argos_reproduction.multi_rule_runtime import (
    host_command,
    inspect_image,
    isolation_arguments,
    isolation_probe,
    runtime_prefix,
    windows_to_wsl,
    _wait_command,
)


class ErrorConditionedRuntimeError(RuntimeError):
    """Raised when isolated runtime lineage or execution fails closed."""


def _values_only(source: Path, target: Path) -> str:
    with np.load(source, allow_pickle=False) as payload:
        values = np.asarray(payload["values"], dtype=np.float64).reshape(-1, 1)
    if values.ndim != 2 or values.shape[1] != 1 or not np.all(np.isfinite(values)):
        raise ErrorConditionedRuntimeError("TASK037D_RUNTIME_VALUES_INVALID")
    target.parent.mkdir(parents=True, exist_ok=True)
    np.save(target, values, allow_pickle=False)
    return sha256_file(target)


def execute_values(
    config: Mapping[str, Any],
    image: Mapping[str, str],
    slot: Mapping[str, Any],
    rule_hash: str,
    input_kind: str,
) -> dict[str, Any]:
    private_root = ROOT / str(config["private_root"])
    rule = (
        private_root
        / "quarantine"
        / str(slot["direction"]).lower()
        / f"{rule_hash}.py"
    )
    if sha256_file(rule) != rule_hash:
        raise ErrorConditionedRuntimeError("TASK037D_RULE_HASH_MISMATCH")
    source = private_root / "targets" / f"{input_kind}_chunks" / f"{slot['slot_id']}.npz"
    output = private_root / "runtime" / slot["slot_id"] / input_kind
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    values_path = output / "input_values.npy"
    input_hash = _values_only(source, values_path)
    name = (
        "task037d-"
        + hashlib.sha256(f"{slot['slot_id']}:{input_kind}".encode()).hexdigest()[:20]
    )
    command = runtime_prefix(config) + [
        "run",
        "--detach",
        "--name",
        name,
        *isolation_arguments(config),
        "--mount",
        f"type=bind,src={windows_to_wsl(rule)},dst=/rule/generated_rule.py,ro",
        "--mount",
        f"type=bind,src={windows_to_wsl(values_path)},dst=/input/input_values.npy,ro",
        "--mount",
        f"type=bind,src={windows_to_wsl(output)},dst=/output,rw",
        image["image_id"],
        "--rule",
        "/rule/generated_rule.py",
        "--values",
        "/input/input_values.npy",
        "--output",
        "/output",
        "--rule-hash",
        rule_hash,
        "--input-hash",
        input_hash,
    ]
    started = time.monotonic()
    launch = host_command(command, timeout=30)
    stderr = launch.stderr
    timed_out = False
    exit_code: int | None = None
    stdout = ""
    try:
        if launch.returncode != 0:
            return {
                "status": "process_failed",
                "exit_code": launch.returncode,
                "timed_out": False,
                "stderr_hash": hashlib.sha256(stderr.encode()).hexdigest(),
            }
        waited = host_command(
            _wait_command(config, name),
            timeout=int(config["isolation"]["timeout_seconds"]) + 30,
        )
        timed_out = waited.returncode == 124
        if not timed_out:
            try:
                exit_code = int(waited.stdout.strip().splitlines()[-1])
            except (IndexError, ValueError):
                exit_code = None
            logs = host_command(runtime_prefix(config) + ["logs", name], timeout=30)
            stdout = logs.stdout
            stderr += logs.stderr
    finally:
        host_command(runtime_prefix(config) + ["rm", "-f", name], timeout=30)
    if timed_out or exit_code != 0:
        return {
            "status": "process_failed",
            "exit_code": exit_code,
            "timed_out": timed_out,
            "stderr_hash": hashlib.sha256(stderr.encode()).hexdigest(),
        }
    lines = [line for line in stdout.splitlines() if line.strip().startswith("{")]
    if len(lines) != 1:
        return {"status": "process_failed", "exit_code": exit_code, "timed_out": False}
    metadata = json.loads(lines[0])
    valid = bool(
        metadata["output_shape_valid"]
        and metadata["output_binary_domain_valid"]
        and metadata["output_finite"]
        and metadata["output_count"] == metadata["input_count"]
    )
    return {
        "status": "valid" if valid else "output_contract_failed",
        "exit_code": exit_code,
        "timed_out": False,
        "duration_bucket": (
            "under_5_seconds" if time.monotonic() - started < 5 else "5_seconds_or_more"
        ),
        "input_hash": input_hash,
        "output_hash": metadata.get("output_sha256"),
        "output_count": metadata.get("output_count"),
        "shape_valid": metadata.get("output_shape_valid"),
        "binary_domain_valid": metadata.get("output_binary_domain_valid"),
        "finite": metadata.get("output_finite"),
    }


def _adequacy(
    config: Mapping[str, Any],
    support: Mapping[str, Any],
    requests: Mapping[str, Any],
    provider: Mapping[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        grouped[(item["detector_variant"], item["kpi_id"], item["direction"])].append(item)
    eligible = [item for item in support["cells"] if item["support_state"] == "eligible"]
    cell_rows: list[dict[str, Any]] = []
    for cell in eligible:
        key = (cell["detector_variant"], cell["kpi_id"], cell["direction"])
        items = grouped.get(key, [])
        executable = sum(item["terminal_status"] == "executable_rule" for item in items)
        cell_rows.append(
            {
                "detector_variant": key[0],
                "kpi_id": key[1],
                "direction": key[2],
                "registered_slot_count": len(items),
                "executable_rule_count": executable,
                "has_one_executable": executable >= 1,
                "has_two_executable": executable >= 2,
            }
        )
    executable_total = sum(
        item["terminal_status"] == "executable_rule" for item in results
    )
    yield_value = executable_total / len(results) if results else 0.0
    one_fraction = (
        sum(item["has_one_executable"] for item in cell_rows) / len(cell_rows)
        if cell_rows
        else 1.0
    )
    multi = [item for item in cell_rows if item["registered_slot_count"] >= 2]
    two_fraction = (
        sum(item["has_two_executable"] for item in multi) / len(multi) if multi else 1.0
    )
    fn_executable = sum(
        item["terminal_status"] == "executable_rule" and item["direction"] == "FN"
        for item in results
    )
    fp_executable = sum(
        item["terminal_status"] == "executable_rule" and item["direction"] == "FP"
        for item in results
    )
    thresholds = config["adequacy"]
    if provider["unattempted_after_global_block"]:
        status = "blocked_provider_global"
    elif one_fraction < float(thresholds["minimum_eligible_cells_with_one_executable_fraction"]):
        status = "insufficient_rule_yield"
    elif two_fraction < float(thresholds["minimum_multi_slot_cells_with_two_executable_fraction"]):
        status = "insufficient_rule_yield"
    elif yield_value < float(thresholds["minimum_overall_executable_rule_yield"]):
        status = "insufficient_rule_yield"
    elif any(item["direction"] == "FN" for item in eligible) and fn_executable == 0:
        status = "insufficient_FN_support"
    elif any(item["direction"] == "FP" for item in eligible) and fp_executable == 0:
        status = "insufficient_FP_support"
    else:
        status = "passed_error_conditioned_rule_cohort"
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-037D",
        "artifact_type": "error_conditioned_cohort_adequacy",
        "status": status,
        "registered_slot_count": requests["registered_slot_count"],
        "terminal_slot_count": len(results),
        "all_registered_slots_have_terminal_status": len(results)
        == requests["registered_slot_count"],
        "executable_rule_count": executable_total,
        "overall_executable_rule_yield": yield_value,
        "eligible_cell_count": len(cell_rows),
        "eligible_cells_with_one_executable_fraction": one_fraction,
        "multi_slot_cell_count": len(multi),
        "multi_slot_cells_with_two_executable_fraction": two_fraction,
        "FN_executable_rules": fn_executable,
        "FP_executable_rules": fp_executable,
        "cell_results": cell_rows,
        "thresholds": thresholds,
        "provider_retries": 0,
        "replacement_calls": 0,
        "inner_evaluation": False,
        "outer_evaluation": False,
        "fusion_execution": False,
        "test_access": False,
    }
    report["report_hash"] = sha256_json(report)
    return report


def run_error_conditioned_runtime(
    config_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_json(config_path)
    support = read_json(ROOT / str(config["reports"]["support"]))
    requests = read_json(ROOT / str(config["reports"]["requests"]))
    provider = read_json(ROOT / str(config["reports"]["provider"]))
    static = read_json(ROOT / str(config["reports"]["static"]))
    image = inspect_image(config)
    probe = isolation_probe(config, image["image_id"])
    if probe["status"] != "passed":
        raise ErrorConditionedRuntimeError("TASK037D_ISOLATION_PROBE_FAILED")
    slot_by_id = {item["slot_id"]: item for item in requests["slots"]}
    results: list[dict[str, Any]] = []
    for audit in static["slots"]:
        slot = slot_by_id[audit["slot_id"]]
        base = {
            key: slot[key]
            for key in ("slot_id", "detector_variant", "kpi_id", "direction")
        }
        if audit.get("static_status") != "static_valid":
            results.append(
                {
                    **base,
                    "terminal_status": audit["terminal_status"],
                    "runtime_attempted": False,
                }
            )
            continue
        target = execute_values(config, image, slot, audit["rule_sha256"], "target")
        if target["status"] == "process_failed":
            terminal = "target_runtime_failed"
            contrast: dict[str, Any] | None = None
        elif target["status"] == "output_contract_failed":
            terminal = "output_contract_failed"
            contrast = None
        else:
            contrast = execute_values(
                config, image, slot, audit["rule_sha256"], "contrast"
            )
            if contrast["status"] == "process_failed":
                terminal = "contrast_runtime_failed"
            elif contrast["status"] == "output_contract_failed":
                terminal = "output_contract_failed"
            else:
                terminal = "executable_rule"
        results.append(
            {
                **base,
                "rule_sha256": audit["rule_sha256"],
                "terminal_status": terminal,
                "runtime_attempted": True,
                "target_runtime": target,
                "contrast_runtime": contrast,
            }
        )
    runtime_report = {
        "schema_version": "1.0",
        "task_id": "TASK-037D",
        "artifact_type": "error_conditioned_runtime_report",
        "image": image,
        "isolation": probe,
        "registered_slot_count": len(results),
        "runtime_executable": sum(
            item["terminal_status"] == "executable_rule" for item in results
        ),
        "slots": results,
        "labels_mounted": False,
        "detector_predictions_mounted": False,
        "performance_metrics_computed": False,
        "raw_outputs_tracked": False,
    }
    runtime_report["report_hash"] = sha256_json(runtime_report)
    write_json(ROOT / str(config["reports"]["runtime"]), runtime_report)
    adequacy = _adequacy(config, support, requests, provider, results)
    write_json(ROOT / str(config["reports"]["adequacy"]), adequacy)
    return runtime_report, adequacy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037d_error_conditioned_rules.json",
    )
    args = parser.parse_args()
    runtime, adequacy = run_error_conditioned_runtime((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "runtime_executable": runtime["runtime_executable"],
                "status": adequacy["status"],
            },
            sort_keys=True,
        )
    )
    return 0 if adequacy["status"] == "passed_error_conditioned_rule_cohort" else 2


if __name__ == "__main__":
    raise SystemExit(main())
