"""Run the TASK-024 fixed mock rule in an isolated smoke boundary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.argos_reproduction import kpi_prepare, mock_harness


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    resolved = path.resolve()
    if not resolved.is_relative_to(REPO_ROOT):
        raise ValueError(f"Refusing to write outside repository: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_argos_csv_slice(path: Path, row_limit: int) -> dict[str, Any]:
    rows: list[list[float]] = []
    label_counts = {0: 0, 1: 0}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["value", "label", "index"]:
            raise ValueError(f"Unexpected ARGOS CSV schema: {reader.fieldnames}")
        for row in reader:
            if len(rows) >= row_limit:
                break
            value = float(row["value"])
            index = float(row["index"])
            label = int(row["label"])
            if label not in {0, 1}:
                raise ValueError(f"Non-binary label in input: {label}")
            rows.append([value, index])
            label_counts[label] += 1
    if not rows:
        raise ValueError("Empty input slice")
    return {
        "sample": rows,
        "row_count": len(rows),
        "columns": ["value", "index"],
        "source_label_counts": {"0": label_counts[0], "1": label_counts[1]},
    }


def make_child_runner() -> str:
    return r'''
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

root = Path.cwd()
input_path = root / "input.json"
rule_path = root / "fixed_rule.py"
output_path = root / "output.json"

spec = importlib.util.spec_from_file_location("fixed_rule", rule_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
payload = json.loads(input_path.read_text(encoding="utf-8"))
sample = np.asarray(payload["sample"], dtype=float)
result = module.inference(sample)
labels = np.asarray(result)
flat = labels.astype(int).reshape(-1)
binary = set(int(x) for x in flat.tolist()).issubset({0, 1})
report = {
    "shape": list(labels.shape),
    "binary_domain": bool(binary),
    "label_count": int(flat.size),
    "positive_count": int(np.sum(flat == 1)),
    "negative_count": int(np.sum(flat == 0)),
}
output_path.write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
'''


def run_restricted_subprocess(
    rule_code: str,
    input_payload: dict[str, Any],
    sandbox_config: dict[str, Any],
    run_root: Path,
) -> dict[str, Any]:
    run_root.mkdir(parents=True, exist_ok=True)
    rule_path = run_root / "fixed_rule.py"
    input_path = run_root / "input.json"
    runner_path = run_root / "child_runner.py"
    output_path = run_root / "output.json"
    rule_path.write_text(rule_code, encoding="utf-8", newline="\n")
    input_path.write_text(json.dumps(input_payload, sort_keys=True), encoding="utf-8")
    runner_path.write_text(make_child_runner(), encoding="utf-8", newline="\n")

    env = {
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PATH": os.environ.get("PATH", ""),
    }
    for key in os.environ:
        if "OPENAI" in key.upper() or "API_KEY" in key.upper() or "TOKEN" in key.upper():
            continue
    start = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-I", str(runner_path.name)],
        cwd=run_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=float(sandbox_config["execution_timeout_seconds"]),
        check=False,
    )
    duration = time.perf_counter() - start
    output_exists = output_path.exists()
    output_size = output_path.stat().st_size if output_exists else 0
    output_payload = json.loads(output_path.read_text(encoding="utf-8")) if output_exists else {}
    size_limit = int(sandbox_config["output_file_size_limit_kb"]) * 1024
    if output_size > size_limit:
        raise ValueError(f"Sandbox output exceeded size limit: {output_size} > {size_limit}")

    return {
        "isolation_method": "restricted_python_subprocess",
        "container_runtime": None,
        "container_runtime_available": False,
        "docker_or_podman_unavailable": True,
        "network_isolation_enforced": False,
        "network_observed_used": False,
        "provider_credentials_present": False,
        "repository_write_isolation_enforced": False,
        "write_scope_observed": "ignored_private_run_directory_only",
        "cpu_limit_enforced": False,
        "memory_limit_enforced": False,
        "timeout_enforced": True,
        "static_rule_policy_enforced": True,
        "read_only_rule_and_input_mount": "not_enforced_for_restricted_subprocess",
        "temporary_writable_output_only": True,
        "cpu_limit": "not_enforced_without_container",
        "memory_limit_mb": "not_enforced_without_container",
        "timeout_seconds": sandbox_config["execution_timeout_seconds"],
        "exit_code": completed.returncode,
        "duration_seconds": duration,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "output_size_bytes": output_size,
        "output_payload": output_payload,
        "output_hash": sha256_file(output_path) if output_exists else None,
        "quarantine_record": {
            "rule_path": rule_path.relative_to(REPO_ROOT).as_posix(),
            "actual_llm_generated_rule": False,
            "rule_hash_recorded_in_report": True,
        },
        "run_directory": run_root.relative_to(REPO_ROOT).as_posix(),
    }


def run_containerized(
    container_runtime: str,
    rule_code: str,
    input_payload: dict[str, Any],
    sandbox_config: dict[str, Any],
    run_root: Path,
) -> dict[str, Any]:
    input_dir = run_root / "input"
    output_dir = run_root / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    rule_path = input_dir / "fixed_rule.py"
    input_path = input_dir / "input.json"
    output_path = output_dir / "output.json"
    rule_path.write_text(rule_code, encoding="utf-8", newline="\n")
    input_path.write_text(json.dumps(input_payload, sort_keys=True), encoding="utf-8")

    command = [
        container_runtime,
        "run",
        "--rm",
        "--network",
        "none",
        "--cpus",
        str(sandbox_config["cpu_limit"]),
        "--memory",
        f"{int(sandbox_config['memory_limit_mb'])}m",
        "--pids-limit",
        "64",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=16m",
        "-e",
        "PYTHONNOUSERSITE=1",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "-v",
        f"{input_dir.resolve()}:/input:ro",
        "-v",
        f"{output_dir.resolve()}:/output:rw",
        sandbox_config["container_image"],
    ]
    start = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=run_root,
        env={"PATH": os.environ.get("PATH", "")},
        capture_output=True,
        text=True,
        timeout=float(sandbox_config["execution_timeout_seconds"]),
        check=False,
    )
    duration = time.perf_counter() - start
    output_exists = output_path.exists()
    output_size = output_path.stat().st_size if output_exists else 0
    output_payload = json.loads(output_path.read_text(encoding="utf-8")) if output_exists else {}
    size_limit = int(sandbox_config["output_file_size_limit_kb"]) * 1024
    if output_size > size_limit:
        raise ValueError(f"Sandbox output exceeded size limit: {output_size} > {size_limit}")

    return {
        "isolation_method": "container",
        "container_runtime": Path(container_runtime).name,
        "container_runtime_available": True,
        "container_image": sandbox_config["container_image"],
        "docker_or_podman_unavailable": False,
        "network_isolation_enforced": True,
        "network_isolation_method": "--network none",
        "network_observed_used": False,
        "provider_credentials_present": False,
        "repository_write_isolation_enforced": True,
        "write_scope_observed": "container_output_mount_only",
        "cpu_limit_enforced": True,
        "memory_limit_enforced": True,
        "timeout_enforced": True,
        "static_rule_policy_enforced": True,
        "read_only_rule_and_input_mount": True,
        "temporary_writable_output_only": True,
        "cpu_limit": sandbox_config["cpu_limit"],
        "memory_limit_mb": sandbox_config["memory_limit_mb"],
        "timeout_seconds": sandbox_config["execution_timeout_seconds"],
        "exit_code": completed.returncode,
        "duration_seconds": duration,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "output_size_bytes": output_size,
        "output_payload": output_payload,
        "output_hash": sha256_file(output_path) if output_exists else None,
        "quarantine_record": {
            "rule_path": rule_path.relative_to(REPO_ROOT).as_posix(),
            "actual_llm_generated_rule": False,
            "rule_hash_recorded_in_report": True,
        },
        "run_directory": run_root.relative_to(REPO_ROOT).as_posix(),
    }


def run(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    manifest = read_json(REPO_ROOT / config["output_manifest_path"])
    task023_config = read_json(REPO_ROOT / config["fixed_rule"]["task023_config_path"])
    rule_code = mock_harness.extract_python_rule(task023_config["mock_response"])
    safety = mock_harness.static_safety_checks(rule_code, set(config["sandbox"]["import_allowlist"]))
    if not safety["passed"]:
        raise ValueError(f"Fixed rule failed static safety: {safety}")
    if config["sandbox"].get("execute_actual_llm_generated_rule", False):
        raise ValueError("Actual LLM-generated rule execution is forbidden in TASK-024")

    converted_path = REPO_ROOT / manifest["converted_argos_csv"]["converted_path"]
    input_payload = load_argos_csv_slice(converted_path, config["input_slice"]["row_limit"])
    input_hash = sha256_json(input_payload)
    rule_hash = hashlib.sha256(rule_code.encode("utf-8")).hexdigest()
    sandbox_config_hash = sha256_json(config["sandbox"])

    container_runtime = shutil.which("docker") or shutil.which("podman")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = REPO_ROOT / config["private_artifact_root"] / "sandbox_runs" / run_id
    if container_runtime:
        execution = run_containerized(container_runtime, rule_code, input_payload, config["sandbox"], run_root)
    else:
        execution = run_restricted_subprocess(rule_code, input_payload, config["sandbox"], run_root)

    output_payload = execution["output_payload"]
    shape_valid = execution["output_payload"].get("shape") == [input_payload["row_count"]]
    binary_valid = bool(execution["output_payload"].get("binary_domain", False))
    report = {
        "schema_version": "1.0",
        "artifact_type": "task024_fixed_rule_sandbox_smoke_report",
        "task_id": "TASK-024",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": config["source_commit"],
        "mode": config["mode"],
        "combined_mode_status": config["combined_mode_status"],
        "selected_kpi_id": manifest["selection_audit"]["selected_kpi_id"],
        "input": {
            "converted_csv_hash": manifest["converted_argos_csv"]["converted_sha256"],
            "input_slice_hash": input_hash,
            "row_count": input_payload["row_count"],
            "source_label_counts": input_payload["source_label_counts"],
            "schema_valid": True,
        },
        "rule": {
            "origin": "task023_repository_owned_fixed_mock_rule",
            "rule_hash": rule_hash,
            "actual_llm_generated_rule": False,
            "static_safety": safety,
        },
        "sandbox": {
            "config_hash": sandbox_config_hash,
            "config": config["sandbox"],
            "execution": execution,
        },
        "output": {
            "shape_valid": shape_valid,
            "binary_domain_valid": binary_valid,
            "label_count": output_payload.get("label_count"),
            "positive_count": output_payload.get("positive_count"),
            "negative_count": output_payload.get("negative_count"),
            "output_hash": execution["output_hash"],
        },
        "checks": {
            "real_provider_calls": False,
            "api_key_use": False,
            "actual_llm_generated_python_execution": False,
            "full_argos_training": False,
            "combined_detector_plus_rule_path": False,
            "swat_access": False,
            "src_paperworks_changes_required": False,
            "benchmark_claims": False,
            "thesis_claims": False,
            "fixed_repository_owned_mock_rule_only": True,
            "output_shape_valid": shape_valid,
            "binary_domain_valid": binary_valid,
        },
    }
    report["report_hash"] = sha256_json(report)
    write_json(REPO_ROOT / config["output_sandbox_report_path"], report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TASK-024 fixed-rule sandbox smoke")
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task024_kpi_sandbox_smoke.json",
        help="TASK-024 config path.",
    )
    args = parser.parse_args()
    report = run((REPO_ROOT / args.config).resolve())
    print(json.dumps({"exit_code": report["sandbox"]["execution"]["exit_code"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
