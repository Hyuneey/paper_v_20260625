"""Container-only preflight for a future fixed-hash captured-rule run.

The preflight may inspect a local Docker or Podman installation and image. It
never launches a container and never imports or executes the captured rule.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.argos_reproduction import prompt_capture
from experiments.argos_reproduction.rule_semantic_audit import read_json


def _sanitized_environment() -> dict[str, str]:
    allowed = ("PATH", "SYSTEMROOT", "COMSPEC", "TEMP", "TMP")
    return {name: os.environ[name] for name in allowed if name in os.environ}


def _run_preflight_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
        env=_sanitized_environment(),
    )


def _future_command_spec(config: dict[str, Any], runtime: str) -> list[str]:
    policy = config["container_policy"]
    return [
        runtime,
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        str(policy["pid_limit"]),
        "--cpus",
        str(policy["cpu_limit"]),
        "--memory",
        str(policy["memory_limit"]),
        "--tmpfs",
        policy["tmpfs_spec"],
        "--mount",
        "type=bind,src=<isolated-rule-file>,dst=/rule/captured_rule.py,readonly",
        "--mount",
        "type=bind,src=<synthetic-input-file>,dst=/input/input.json,readonly",
        "--mount",
        "type=bind,src=<bounded-output-directory>,dst=/output",
        f"{policy['image_reference']}@<verified-image-digest>",
        "--expected-rule-hash",
        config["frozen_artifacts"]["rule_hash"],
    ]


def container_preflight(config_path: Path, *, persist: bool = True) -> dict[str, Any]:
    config = read_json(config_path)
    rule_path = REPO_ROOT / config["private_rule_path"]
    prompt_capture.assert_private_artifact_path(rule_path)
    actual_rule_hash = prompt_capture.sha256_file(rule_path)
    expected_rule_hash = config["frozen_artifacts"]["rule_hash"]
    if actual_rule_hash != expected_rule_hash:
        raise ValueError(f"Captured rule hash mismatch: {actual_rule_hash} != {expected_rule_hash}")

    approval_path = REPO_ROOT / config["execution_approval_template_path"]
    approval = read_json(approval_path)
    if approval.get("approved") is not False:
        raise ValueError("TASK-027 execution approval template must remain false")
    if approval.get("rule_hash") != expected_rule_hash:
        raise ValueError("Execution approval template rule hash does not match the frozen rule")

    runtime_path = shutil.which("docker") or shutil.which("podman")
    runtime_name = Path(runtime_path).stem if runtime_path else None
    command_spec = _future_command_spec(config, runtime_name or "docker-or-podman")
    image_digest = None
    runtime_version = None
    checks: list[dict[str, Any]] = []
    status = "unavailable"

    if runtime_path:
        version_result = _run_preflight_command([runtime_path, "--version"])
        runtime_version = version_result.stdout.strip() or version_result.stderr.strip() or None
        checks.append({"check": "runtime_version", "exit_code": version_result.returncode})
        inspect_result = _run_preflight_command(
            [runtime_path, "image", "inspect", "--format", "{{.Id}}", config["container_policy"]["image_reference"]]
        )
        checks.append({"check": "local_image_inspect", "exit_code": inspect_result.returncode})
        if inspect_result.returncode == 0 and inspect_result.stdout.strip().startswith("sha256:"):
            image_digest = inspect_result.stdout.strip()
            status = "ready_pending_execution_approval"
        else:
            status = "runtime_available_image_unavailable"

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "artifact_type": "task027_container_preflight",
        "task_id": "TASK-027",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "statement": config["report_statement"],
        "code_commit": config.get("code_commit", "untracked_synthetic_test"),
        "config_hash": prompt_capture.sha256_json(config),
        "random_seed": config.get("random_seed"),
        "rule_hash_verification_status": "passed",
        "rule_hash": actual_rule_hash,
        "container_preflight_status": status,
        "container_runtime": runtime_name,
        "container_runtime_version": runtime_version,
        "container_image_reference": config["container_policy"]["image_reference"],
        "container_image_digest": image_digest,
        "preflight_checks": checks,
        "future_container_command_spec": command_spec,
        "command_hash": prompt_capture.sha256_json(command_spec),
        "required_controls": config["container_policy"],
        "execution_approval": {
            "approved": False,
            "template_path": config["execution_approval_template_path"],
            "allowed_execution_count": approval["allowed_execution_count"],
            "allowed_input_kind": approval["allowed_input_kind"],
        },
        "captured_rule_execution_allowed": False,
        "captured_rule_executed": False,
        "container_launched": False,
        "restricted_subprocess_fallback_allowed": False,
        "provider_call_performed": False,
        "network_call_performed": False,
        "host_environment_propagated": False,
        "boundaries": config["boundaries"],
    }
    report["report_hash"] = prompt_capture.sha256_json(report)
    if persist:
        prompt_capture.write_json(REPO_ROOT / config["output_container_preflight_path"], report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task027_semantic_audit.json")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    report = container_preflight(config_path.resolve())
    print(
        prompt_capture.stable_json(
            {
                "container_preflight_status": report["container_preflight_status"],
                "captured_rule_execution_allowed": report["captured_rule_execution_allowed"],
                "container_launched": report["container_launched"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
