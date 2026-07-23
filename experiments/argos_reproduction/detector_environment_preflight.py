"""Rootless-Podman build, isolation preflight, and synthetic detector smoke."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping, Sequence

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from experiments.argos_reproduction.easytsad_detector_audit import (
    PINNED_EASYTSAD_COMMIT,
    REPO_ROOT,
    _git_head,
    read_json,
    sha256_file,
    with_report_hash,
    write_json,
)


class DetectorPreflightError(RuntimeError):
    pass


def safe_host_environment() -> dict[str, str]:
    allowed = ("SYSTEMROOT", "WINDIR", "PATH", "COMSPEC", "TEMP", "TMP", "PATHEXT")
    return {name: os.environ[name] for name in allowed if name in os.environ}


def host_command(command: Sequence[str], *, timeout: int, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command), capture_output=True, text=True, timeout=timeout,
        env=safe_host_environment(), encoding="utf-8", errors="replace", check=False,
    )
    if check and result.returncode != 0:
        raise DetectorPreflightError("TASK037A_CONTAINER_COMMAND_FAILED")
    return result


def runtime_prefix(config: Mapping[str, Any]) -> list[str]:
    runtime = config["runtime"]
    return [
        "wsl", "-d", str(runtime["wsl_distribution"]), "-u", "root", "--",
        "runuser", "-u", str(runtime["rootless_user"]), "--", "env",
        f"XDG_RUNTIME_DIR={runtime['xdg_runtime_dir']}",
        f"DBUS_SESSION_BUS_ADDRESS=unix:path={runtime['xdg_runtime_dir']}/bus", "podman",
    ]


def windows_to_wsl(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    return f"/mnt/{drive}{resolved.as_posix().split(':', 1)[1]}"


def isolation_arguments(config: Mapping[str, Any]) -> list[str]:
    policy = config["isolation"]
    return [
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--pids-limit", str(policy["pids_limit"]),
        "--cpus", str(policy["cpu_limit"]), "--memory", str(policy["memory_limit"]),
        "--tmpfs", str(policy["tmpfs"]), "--user", "65532:65532",
    ]


def prepare_build_context(config: Mapping[str, Any]) -> Path:
    easytsad = REPO_ROOT / str(config["sources"]["easytsad_checkout"])
    if _git_head(easytsad) != PINNED_EASYTSAD_COMMIT:
        raise DetectorPreflightError("TASK037A_EASYTSAD_COMMIT_MISMATCH")
    target = REPO_ROOT / str(config["private_build_context"])
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "containers/argos_lstm_detector/Containerfile", target / "Containerfile")
    shutil.copy2(REPO_ROOT / "containers/argos_lstm_detector/requirements.lock", target / "requirements.lock")
    shutil.copy2(
        REPO_ROOT / "experiments/argos_reproduction/detector_synthetic_smoke.py",
        target / "detector_synthetic_smoke.py",
    )
    shutil.copytree(easytsad / "EasyTSAD", target / "EasyTSAD")
    return target


def inspect_image(config: Mapping[str, Any]) -> dict[str, Any]:
    raw = host_command(
        runtime_prefix(config) + ["image", "inspect", str(config["image"]["local_reference"])],
        timeout=30, check=True,
    ).stdout
    payload = json.loads(raw)[0]
    image_id = str(payload.get("Id", ""))
    if len(image_id) == 64:
        image_id = "sha256:" + image_id
    if not image_id.startswith("sha256:"):
        raise DetectorPreflightError("TASK037A_IMAGE_DIGEST_INVALID")
    return {
        "image_id": image_id,
        "image_digest": str(payload.get("Digest") or image_id),
        "base_image": config["image"]["pinned_from"],
        "containerfile_hash": sha256_file(REPO_ROOT / "containers/argos_lstm_detector/Containerfile"),
        "requirements_hash": sha256_file(REPO_ROOT / "containers/argos_lstm_detector/requirements.lock"),
    }


def build_image(config: Mapping[str, Any]) -> dict[str, Any]:
    context = prepare_build_context(config)
    command = runtime_prefix(config) + [
        "build", "--network", "slirp4netns", "--tag", str(config["image"]["local_reference"]),
        "--file", windows_to_wsl(context / "Containerfile"), windows_to_wsl(context),
    ]
    host_command(command, timeout=int(config["build_timeout_seconds"]), check=True)
    return inspect_image(config)


def isolation_probe(config: Mapping[str, Any], image_id: str) -> dict[str, Any]:
    result = host_command(
        runtime_prefix(config) + ["run", "--rm", *isolation_arguments(config), image_id, "--isolation-probe"],
        timeout=60, check=True,
    )
    payload = json.loads(result.stdout.strip().splitlines()[-1])["isolation_probe"]
    expected = config["isolation"]
    passed = (
        payload["uid"] != 0 and payload["interfaces"] == ["lo"] and payload["root_write_blocked"]
        and payload["pids_max"] == str(expected["pids_limit"])
        and payload["memory_max"] == str(expected["memory_limit_bytes"])
        and payload["cpu_max"] == str(expected["cpu_max_expected"])
    )
    return {
        "status": "passed" if passed else "failed",
        "network_none": payload["interfaces"] == ["lo"],
        "non_root": payload["uid"] != 0,
        "read_only_root": payload["root_write_blocked"],
        "cpu_limit": payload["cpu_max"] == str(expected["cpu_max_expected"]),
        "memory_limit": payload["memory_max"] == str(expected["memory_limit_bytes"]),
        "pids_limit": payload["pids_max"] == str(expected["pids_limit"]),
        "host_mounts": [],
        "provider_credentials_visible": False,
    }


def run_synthetic_smoke(config: Mapping[str, Any], image_id: str) -> dict[str, Any]:
    result = host_command(
        runtime_prefix(config) + ["run", "--rm", *isolation_arguments(config), image_id, "--container-run"],
        timeout=int(config["isolation"]["timeout_seconds"]), check=False,
    )
    if result.returncode != 0:
        return {"status": "failed", "exit_code": result.returncode, "stderr_hash": __import__("hashlib").sha256(result.stderr.encode()).hexdigest()}
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as error:
        raise DetectorPreflightError("TASK037A_SMOKE_OUTPUT_INVALID") from error
    payload["exit_code"] = result.returncode
    payload["raw_arrays_reported"] = False
    return payload


def run_preflight(config_path: Path, *, build: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_json(config_path)
    image = build_image(config) if build else inspect_image(config)
    runtime_version = host_command(runtime_prefix(config) + ["version", "--format", "{{.Client.Version}}"], timeout=30, check=True).stdout.strip()
    probe = isolation_probe(config, image["image_id"])
    smoke = run_synthetic_smoke(config, image["image_id"]) if probe["status"] == "passed" else {"status": "not_run_isolation_failed"}
    environment = with_report_hash({
        "schema_version": "1.0", "task_id": "TASK-037A", "artifact_type": "environment_preflight_report",
        "status": "passed" if probe["status"] == "passed" else "blocked_environment",
        "runtime": "WSL-native rootless Podman", "runtime_version": runtime_version,
        "runtime_source": config["runtime"]["source"],
        "runtime_package_version": config["runtime"]["package_version"],
        "runtime_candidates": config["runtime"]["candidates"],
        "rootless": True, "image": image, "isolation": probe,
        "synthetic_only": True, "kpi_mounted": False, "rule_artifacts_mounted": False,
        "repository_root_mounted": False, "provider_configuration_mounted": False,
    })
    smoke_report = with_report_hash({
        "schema_version": "1.0", "task_id": "TASK-037A", "artifact_type": "synthetic_smoke_report",
        **smoke, "image_digest": image["image_digest"], "real_kpi_detector_training": False,
        "detector_performance_metrics": False, "fusion_execution": False,
    })
    return environment, smoke_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/argos_reproduction/task037a_detector_preflight.json")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    config_path = REPO_ROOT / args.config
    config = read_json(config_path)
    environment, smoke = run_preflight(config_path, build=args.build)
    write_json(REPO_ROOT / config["reports"]["environment"], environment)
    write_json(REPO_ROOT / config["reports"]["smoke"], smoke)
    print(json.dumps({"environment": environment["status"], "smoke": smoke["status"]}, sort_keys=True))
    return 0 if environment["status"] == "passed" and smoke["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
