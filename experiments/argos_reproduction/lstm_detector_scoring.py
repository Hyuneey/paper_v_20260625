"""Rootless-Podman training and values-only scoring for TASK-037B."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import time
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.argos_reproduction.detector_environment_preflight import (
    host_command,
    inspect_image,
    isolation_arguments,
    runtime_prefix,
    windows_to_wsl,
)
from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, sha256_file


class DetectorScoringError(RuntimeError):
    pass


def inspect_frozen_image(config: Mapping[str, Any]) -> dict[str, Any]:
    image = inspect_image(config)
    frozen = config["image"]
    if image["image_id"] != frozen["expected_image_id"]:
        raise DetectorScoringError("TASK037B_IMAGE_ID_MISMATCH")
    if image["image_digest"] != frozen["expected_image_digest"]:
        raise DetectorScoringError("TASK037B_IMAGE_DIGEST_MISMATCH")
    return image


def _wait_command(config: Mapping[str, Any], name: str) -> list[str]:
    runtime = config["runtime"]
    seconds = int(config["isolation"]["timeout_seconds"])
    podman = (
        f"runuser -u {runtime['rootless_user']} -- env "
        f"XDG_RUNTIME_DIR={runtime['xdg_runtime_dir']} "
        f"DBUS_SESSION_BUS_ADDRESS=unix:path={runtime['xdg_runtime_dir']}/bus podman"
    )
    script = (
        f"timeout --foreground {seconds}s {podman} wait {name}; code=$?; "
        f"if [ $code -eq 124 ]; then {podman} rm -f {name} >/dev/null 2>&1; fi; exit $code"
    )
    return [
        "wsl", "-d", str(runtime["wsl_distribution"]), "-u", "root", "--",
        "bash", "-lc", script,
    ]


def _clean_output(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _container_run(
    config: Mapping[str, Any],
    image: Mapping[str, Any],
    *,
    operation: str,
    run_id: str,
    variant: str,
    values_path: Path,
    output_dir: Path,
    checkpoint_path: Path | None = None,
    normalization_path: Path | None = None,
) -> dict[str, Any]:
    if operation not in ("train", "score"):
        raise DetectorScoringError("TASK037B_OPERATION_INVALID")
    if not values_path.is_file():
        raise DetectorScoringError("TASK037B_VALUES_FILE_MISSING")
    _clean_output(output_dir)
    adapter = REPO_ROOT / "experiments/argos_reproduction/easytsad_lstm_adapter.py"
    config_path = REPO_ROOT / "configs/argos_reproduction/task037b_dual_lstm_detector_validation.json"
    name = "task037b-" + hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:24]
    mounts = [
        "--mount", f"type=bind,src={windows_to_wsl(adapter)},dst=/adapter/easytsad_lstm_adapter.py,ro",
        "--mount", f"type=bind,src={windows_to_wsl(config_path)},dst=/config/task037b.json,ro",
        "--mount", f"type=bind,src={windows_to_wsl(values_path)},dst=/input/values.npy,ro",
        "--mount", f"type=bind,src={windows_to_wsl(output_dir)},dst=/output,rw",
    ]
    args = [
        "/adapter/easytsad_lstm_adapter.py", operation,
        "--variant", variant,
        "--values", "/input/values.npy",
        "--config", "/config/task037b.json",
        "--output", "/output",
        "--seed", str(config["execution"]["seeds"][0]),
    ]
    if operation == "score":
        if checkpoint_path is None or normalization_path is None:
            raise DetectorScoringError("TASK037B_SCORE_BINDINGS_MISSING")
        if not checkpoint_path.is_file() or not normalization_path.is_file():
            raise DetectorScoringError("TASK037B_SCORE_BINDING_FILE_MISSING")
        mounts.extend([
            "--mount", f"type=bind,src={windows_to_wsl(checkpoint_path)},dst=/model/best_network.pth,ro",
            "--mount", f"type=bind,src={windows_to_wsl(normalization_path)},dst=/model/normalization.json,ro",
        ])
        args.extend(["--checkpoint", "/model/best_network.pth", "--normalization", "/model/normalization.json"])
    command = runtime_prefix(config) + [
        "run", "--detach", "--name", name,
        *isolation_arguments(config),
        *mounts,
        "--entrypoint", "python",
        str(image["image_id"]),
        *args,
    ]
    started = time.monotonic()
    launch = host_command(command, timeout=30)
    stderr = launch.stderr
    stdout = ""
    timed_out = False
    exit_code: int | None = None
    try:
        if launch.returncode != 0:
            raise DetectorScoringError("TASK037B_CONTAINER_LAUNCH_FAILED")
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
    if timed_out:
        return {"status": "timeout", "timed_out": True, "container_removed": True}
    if exit_code != 0:
        return {
            "status": "failed",
            "timed_out": False,
            "exit_code": exit_code,
            "stderr_hash": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
            "container_removed": True,
        }
    lines = [line for line in stdout.splitlines() if line.strip().startswith("{")]
    if len(lines) != 1:
        raise DetectorScoringError("TASK037B_CONTAINER_RESULT_INVALID")
    result = json.loads(lines[0])
    result.update(
        {
            "timed_out": False,
            "exit_code": exit_code,
            "duration_seconds": time.monotonic() - started,
            "container_removed": True,
            "labels_mounted": False,
            "test_mounted": False,
            "repository_root_mounted": False,
            "input_hash": sha256_file(values_path),
            "image_id": image["image_id"],
            "image_digest": image["image_digest"],
        }
    )
    return result


def train_execution_unit(
    config: Mapping[str, Any],
    image: Mapping[str, Any],
    *,
    kpi_id: str,
    variant: str,
    values_path: Path,
    unit_root: Path,
) -> dict[str, Any]:
    return _container_run(
        config,
        image,
        operation="train",
        run_id=f"train-{variant}-{kpi_id}",
        variant=variant,
        values_path=values_path,
        output_dir=unit_root / "fit",
    )


def score_execution_unit(
    config: Mapping[str, Any],
    image: Mapping[str, Any],
    *,
    kpi_id: str,
    variant: str,
    split: str,
    replay: int,
    values_path: Path,
    unit_root: Path,
) -> dict[str, Any]:
    return _container_run(
        config,
        image,
        operation="score",
        run_id=f"score-{variant}-{kpi_id}-{split}-{replay}",
        variant=variant,
        values_path=values_path,
        output_dir=unit_root / "scores" / split / f"replay_{replay}",
        checkpoint_path=unit_root / "fit/checkpoint/best_network.pth",
        normalization_path=unit_root / "fit/normalization.json",
    )


def exact_replay(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    fields = (
        "status", "variant", "seed", "input_count", "raw_score_count",
        "aligned_score_count", "missing_prefix_count", "raw_score_sha256",
        "aligned_score_sha256", "input_hash", "image_id", "image_digest",
    )
    return all(first.get(field) == second.get(field) for field in fields)


def load_aligned_score(unit_root: Path, split: str, replay: int = 1) -> np.ndarray:
    path = unit_root / "scores" / split / f"replay_{replay}" / "aligned_score.npy"
    scores = np.asarray(np.load(path, allow_pickle=False), dtype=np.float64)
    if scores.ndim != 1 or not np.all(np.isfinite(scores)):
        raise DetectorScoringError("TASK037B_PRIVATE_SCORE_INVALID")
    return scores
