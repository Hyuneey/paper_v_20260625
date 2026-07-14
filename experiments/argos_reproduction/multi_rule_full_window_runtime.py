"""Values-only full-window container execution for TASK-035B."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import time
from typing import Any, Mapping

import numpy as np

from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, sha256_file
from experiments.argos_reproduction.multi_rule_runtime import (
    MultiRuleRuntimeError,
    _wait_command,
    host_command,
    isolation_arguments,
    runtime_prefix,
    windows_to_wsl,
)


class FullWindowRuntimeError(RuntimeError):
    pass


def execute_full_window_rule(
    config: Mapping[str, Any],
    image: Mapping[str, str],
    *,
    run_id: str,
    rule_path: Path,
    rule_sha256: str,
    values_path: Path,
    output_directory: Path,
) -> dict[str, Any]:
    if sha256_file(rule_path) != rule_sha256:
        raise FullWindowRuntimeError("TASK035B_RULE_HASH_MISMATCH")
    input_hash = sha256_file(values_path)
    output_directory.mkdir(parents=True, exist_ok=True)
    for child in output_directory.iterdir():
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)
    name = "task035b-" + hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:20]
    command = runtime_prefix(config) + [
        "run", "--detach", "--name", name, *isolation_arguments(config),
        "--mount", f"type=bind,src={windows_to_wsl(rule_path)},dst=/rule/generated_rule.py,ro",
        "--mount", f"type=bind,src={windows_to_wsl(values_path)},dst=/input/input_values.npy,ro",
        "--mount", f"type=bind,src={windows_to_wsl(output_directory)},dst=/output,rw",
        image["image_id"], "--rule", "/rule/generated_rule.py", "--values", "/input/input_values.npy",
        "--output", "/output", "--rule-hash", rule_sha256, "--input-hash", input_hash,
    ]
    started = time.monotonic()
    launch = host_command(command, timeout=30)
    stdout = ""
    stderr = launch.stderr
    timed_out = False
    exit_code: int | None = None
    try:
        if launch.returncode != 0:
            raise FullWindowRuntimeError("TASK035B_CONTAINER_LAUNCH_FAILED")
        waited = host_command(
            _wait_command(config, name), timeout=int(config["isolation"]["timeout_seconds"]) + 30
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
    elapsed = time.monotonic() - started
    base = {
        "rule_sha256": rule_sha256,
        "input_sha256": input_hash,
        "image_id": image["image_id"],
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_bucket": "timeout" if timed_out else ("under_5_seconds" if elapsed < 5 else "5_seconds_or_more"),
        "labels_mounted": False,
        "repository_root_mounted": False,
        "container_removed": True,
    }
    if timed_out or exit_code != 0:
        return {**base, "runtime_status": "runtime_failed", "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()}
    lines = [line for line in stdout.splitlines() if line.strip().startswith("{")]
    if len(lines) != 1:
        return {**base, "runtime_status": "runtime_failed", "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()}
    metadata = json.loads(lines[0])
    prediction_path = output_directory / "output_labels.npy"
    if not prediction_path.is_file() or prediction_path.stat().st_size > int(config["isolation"]["output_limit_bytes"]):
        return {**base, "runtime_status": "output_contract_failed"}
    prediction = np.load(prediction_path, allow_pickle=False)
    valid = (
        prediction.ndim == 1
        and len(prediction) == int(metadata.get("input_count", -1))
        and np.all(np.isfinite(prediction))
        and np.all(np.isin(prediction, (0, 1)))
        and sha256_file(prediction_path) == metadata.get("output_sha256")
    )
    return {
        **base,
        "runtime_status": "executable_rule" if valid else "output_contract_failed",
        "output_count": int(len(prediction)),
        "output_shape_valid": prediction.ndim == 1,
        "output_binary_domain_valid": bool(np.all(np.isin(prediction, (0, 1)))),
        "output_finite": bool(np.all(np.isfinite(prediction))),
        "prediction_sha256": sha256_file(prediction_path),
        "predicted_positive_count": int(np.sum(prediction == 1)),
    }


def deterministic_replay_matches(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    fields = (
        "rule_sha256", "input_sha256", "image_id", "exit_code", "runtime_status",
        "output_count", "prediction_sha256", "predicted_positive_count",
    )
    return all(first.get(field) == second.get(field) for field in fields)


def load_private_prediction(output_directory: Path) -> np.ndarray:
    return np.asarray(np.load(output_directory / "output_labels.npy", allow_pickle=False), dtype=np.int8)
