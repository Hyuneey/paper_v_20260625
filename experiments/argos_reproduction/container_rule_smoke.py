"""Host-side TASK-033 rootless-Podman build and captured-rule smoke harness."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
OUTPUT_LIMIT_BYTES = 65_536
FROZEN_RULE_HASH = "e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659"


class Task033HarnessError(RuntimeError):
    """Fail-closed harness error without private source or output content."""


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: object) -> str:
    return sha256_bytes(stable_json(value).encode("utf-8"))


def private_rule_path() -> Path:
    return (
        REPO_ROOT
        / "artifacts"
        / "private_argos_reproduction"
        / "task026q"
        / "quarantine"
        / f"{FROZEN_RULE_HASH}.py"
    )


def verify_rule_hash(path: Path, expected_hash: str = FROZEN_RULE_HASH) -> str:
    if not path.is_file():
        raise Task033HarnessError("TASK033_RULE_UNAVAILABLE")
    actual = sha256_file(path)
    if actual != expected_hash:
        raise Task033HarnessError("TASK033_RULE_HASH_MISMATCH")
    return actual


def static_rule_summary(path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    verify_rule_hash(path, str(config["captured_rule_sha256"]))
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    inference_count = sum(node.name == "inference" for node in functions)
    if inference_count != 1:
        raise Task033HarnessError("TASK033_INFERENCE_COUNT_INVALID")
    inference = next(node for node in functions if node.name == "inference")
    if len(inference.args.args) != 1 or inference.args.args[0].arg != "sample":
        raise Task033HarnessError("TASK033_INFERENCE_SIGNATURE_INVALID")
    from experiments.argos_reproduction import rule_semantic_audit

    audit = rule_semantic_audit.audit_rule(
        REPO_ROOT / str(config["static_audit_config"]), persist=False
    )
    policy_status = audit["frozen_static_policy_review"]["policy_status"]
    if policy_status != "passed":
        raise Task033HarnessError("TASK033_STATIC_POLICY_REJECTED")
    return {
        "rule_sha256": str(config["captured_rule_sha256"]),
        "syntax_status": "passed",
        "inference_function_count": inference_count,
        "signature_status": "passed",
        "static_policy_status": policy_status,
        "raw_source_included": False,
    }


def validate_fixture(path: Path) -> dict[str, Any]:
    fixture_root = (REPO_ROOT / "fixtures" / "task033").resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(fixture_root)
    except ValueError as error:
        raise Task033HarnessError("TASK033_FIXTURE_PATH_OUTSIDE_APPROVED_ROOT") from error
    path = resolved
    payload = read_json(path)
    if payload.get("input_kind") != "synthetic_non_kpi":
        raise Task033HarnessError("TASK033_FIXTURE_KIND_INVALID")
    shape = payload.get("shape")
    values = payload.get("values")
    if not isinstance(shape, list) or len(shape) != 2 or shape[1] != 1:
        raise Task033HarnessError("TASK033_FIXTURE_SHAPE_INVALID")
    if not isinstance(shape[0], int) or shape[0] < 0:
        raise Task033HarnessError("TASK033_FIXTURE_SHAPE_INVALID")
    if not isinstance(values, list) or len(values) != shape[0]:
        raise Task033HarnessError("TASK033_FIXTURE_LENGTH_INVALID")
    if any(not isinstance(row, list) or len(row) != 1 for row in values):
        raise Task033HarnessError("TASK033_FIXTURE_ROW_INVALID")
    for row in values:
        value = row[0]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise Task033HarnessError("TASK033_FIXTURE_VALUE_INVALID")
        if value != value or value in (float("inf"), float("-inf")):
            raise Task033HarnessError("TASK033_FIXTURE_VALUE_INVALID")
    return {
        "fixture_id": str(payload["fixture_id"]),
        "fixture_sha256": sha256_file(path),
        "input_count": shape[0],
    }


def runtime_prefix(config: Mapping[str, Any]) -> list[str]:
    runtime = config["runtime"]
    return [
        "wsl",
        "-d",
        str(runtime["wsl_distribution"]),
        "-u",
        "root",
        "--",
        "runuser",
        "-u",
        str(runtime["rootless_user"]),
        "--",
        "env",
        f"XDG_RUNTIME_DIR={runtime['xdg_runtime_dir']}",
        f"DBUS_SESSION_BUS_ADDRESS=unix:path={runtime['xdg_runtime_dir']}/bus",
        "podman",
    ]


def safe_host_environment() -> dict[str, str]:
    allowed = ("SYSTEMROOT", "WINDIR", "PATH", "COMSPEC", "TEMP", "TMP", "PATHEXT")
    return {name: os.environ[name] for name in allowed if name in os.environ}


def run_host_command(
    command: Sequence[str], *, timeout: float, check: bool = False
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=safe_host_environment(),
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if check and completed.returncode != 0:
        raise Task033HarnessError("TASK033_RUNTIME_COMMAND_FAILED")
    return completed


def windows_to_wsl(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    suffix = resolved.as_posix().split(":", 1)[1]
    return f"/mnt/{drive}{suffix}"


def private_build_root() -> Path:
    return REPO_ROOT / "artifacts" / "private_argos_reproduction" / "task033" / "build_context"


def prepare_build_context() -> Path:
    target = private_build_root()
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "containers/argos_rule_runtime/Containerfile", target / "Containerfile")
    shutil.copy2(REPO_ROOT / "containers/argos_rule_runtime/requirements.lock", target / "requirements.lock")
    shutil.copy2(
        REPO_ROOT / "experiments/argos_reproduction/container_entrypoint.py",
        target / "container_entrypoint.py",
    )
    return target


def inspect_image(config: Mapping[str, Any]) -> dict[str, Any]:
    command = runtime_prefix(config) + ["image", "inspect", str(config["image"]["local_reference"])]
    completed = run_host_command(command, timeout=30, check=True)
    payload = json.loads(completed.stdout)[0]
    digest = payload.get("Digest") or payload.get("Id")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise Task033HarnessError("TASK033_IMAGE_DIGEST_UNAVAILABLE")
    return {
        "image_id": str(payload["Id"]),
        "image_digest": digest,
        "base_image_reference": str(config["image"]["pinned_from"]),
        "base_image_digest": str(config["image"]["base_digest"]),
        "python_version": "3.11.9",
        "numpy_version": "1.26.4",
        "containerfile_sha256": sha256_file(
            REPO_ROOT / "containers/argos_rule_runtime/Containerfile"
        ),
        "requirements_sha256": sha256_file(
            REPO_ROOT / "containers/argos_rule_runtime/requirements.lock"
        ),
        "build_context_contains_rule": False,
    }


def build_image(config: Mapping[str, Any]) -> dict[str, Any]:
    context = prepare_build_context()
    image = config["image"]
    command = runtime_prefix(config) + [
        "build",
        "--network",
        "slirp4netns",
        "--tag",
        str(image["local_reference"]),
        "--file",
        f"{windows_to_wsl(context)}/Containerfile",
        windows_to_wsl(context),
    ]
    run_host_command(command, timeout=300, check=True)
    report = inspect_image(config)
    report.update(
        {
            "base_image_reference": str(image["base_reference"]),
            "base_image_digest": str(image["base_digest"]),
            "containerfile_sha256": sha256_file(
                REPO_ROOT / "containers/argos_rule_runtime/Containerfile"
            ),
            "requirements_sha256": sha256_file(
                REPO_ROOT / "containers/argos_rule_runtime/requirements.lock"
            ),
            "build_context_contains_rule": False,
        }
    )
    return report


def isolation_arguments(config: Mapping[str, Any]) -> list[str]:
    controls = config["isolation"]
    return [
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        str(controls["pids_limit"]),
        "--cpus",
        str(controls["cpu_limit"]),
        "--memory",
        str(controls["memory_limit"]),
        "--tmpfs",
        str(controls["tmpfs"]),
        "--tmpfs",
        str(controls["output_tmpfs"]),
    ]


def parse_single_json_output(stdout: str) -> dict[str, Any]:
    encoded = stdout.encode("utf-8")
    if len(encoded) > OUTPUT_LIMIT_BYTES:
        raise Task033HarnessError("TASK033_OUTPUT_TOO_LARGE")
    lines = [line.strip() for line in stdout.splitlines() if line.strip().startswith("{")]
    if len(lines) != 1:
        raise Task033HarnessError("TASK033_OUTPUT_JSON_INVALID")
    payload = json.loads(lines[0])
    if not isinstance(payload, dict):
        raise Task033HarnessError("TASK033_OUTPUT_JSON_INVALID")
    return payload


def run_isolation_smoke(config: Mapping[str, Any], image_digest: str) -> dict[str, Any]:
    command = runtime_prefix(config) + [
        "run",
        "--rm",
        *isolation_arguments(config),
        str(config["image"]["local_reference"]),
        "--isolation-probe",
    ]
    completed = run_host_command(command, timeout=30, check=True)
    payload = parse_single_json_output(completed.stdout)["isolation_probe"]
    controls = config["isolation"]
    passed = (
        payload["uid"] != 0
        and payload["network_interfaces"] == ["lo"]
        and payload["network_connect_blocked"]
        and payload["root_write_blocked"]
        and payload["memory_max"] == str(controls["memory_limit_bytes"])
        and payload["pids_max"] == str(controls["pids_limit"])
        and payload["cpu_max"] == str(controls["cpu_max_expected"])
    )
    return {
        "status": "passed" if passed else "failed",
        "image_digest": image_digest,
        "non_root_verified": payload["uid"] != 0,
        "uid": payload["uid"],
        "network_none_verified": payload["network_interfaces"] == ["lo"] and payload["network_connect_blocked"],
        "read_only_root_verified": payload["root_write_blocked"],
        "memory_limit_verified": payload["memory_max"] == str(controls["memory_limit_bytes"]),
        "pids_limit_verified": payload["pids_max"] == str(controls["pids_limit"]),
        "cpu_limit_verified": payload["cpu_max"] == str(controls["cpu_max_expected"]),
        "research_mounts_present": False,
    }


def redacted_command_hash(command: Sequence[str], rule_path: Path, fixture_path: Path) -> str:
    replacements = {
        windows_to_wsl(rule_path): "<frozen-rule>",
        windows_to_wsl(fixture_path): "<synthetic-fixture>",
    }
    redacted = []
    for item in command:
        for original, replacement in replacements.items():
            item = item.replace(original, replacement)
        redacted.append(item)
    return sha256_json(redacted)


def duration_bucket(seconds: float) -> str:
    if seconds < 1:
        return "under_1_second"
    if seconds < 2:
        return "1_to_2_seconds"
    if seconds < 5:
        return "2_to_5_seconds"
    return "over_5_seconds_including_wsl_overhead"


def _wait_script(config: Mapping[str, Any], name: str) -> list[str]:
    runtime = config["runtime"]
    seconds = int(config["isolation"]["timeout_seconds"])
    user_command = (
        f"runuser -u {runtime['rootless_user']} -- env "
        f"XDG_RUNTIME_DIR={runtime['xdg_runtime_dir']} "
        f"DBUS_SESSION_BUS_ADDRESS=unix:path={runtime['xdg_runtime_dir']}/bus podman"
    )
    script = (
        f"timeout --foreground {seconds}s {user_command} wait {name}; "
        "wait_status=$?; "
        f"if [ $wait_status -eq 124 ]; then {user_command} rm -f {name} >/dev/null 2>&1; fi; "
        "exit $wait_status"
    )
    return [
        "wsl",
        "-d",
        str(runtime["wsl_distribution"]),
        "-u",
        "root",
        "--",
        "bash",
        "-lc",
        script,
    ]


def execute_fixture_once(
    config: Mapping[str, Any],
    fixture_path: Path,
    fixture: Mapping[str, Any],
    image_digest: str,
    run_index: int,
) -> dict[str, Any]:
    rule_path = private_rule_path()
    verify_rule_hash(rule_path, str(config["captured_rule_sha256"]))
    name = f"task033-{fixture['fixture_id']}-{run_index}".lower().replace("_", "-")
    mount_rule = f"type=bind,src={windows_to_wsl(rule_path)},dst=/rule/captured_rule.py,ro"
    mount_fixture = f"type=bind,src={windows_to_wsl(fixture_path)},dst=/fixture/input.json,ro"
    command = runtime_prefix(config) + [
        "run",
        "--detach",
        "--name",
        name,
        *isolation_arguments(config),
        "--mount",
        mount_rule,
        "--mount",
        mount_fixture,
        str(config["image"]["local_reference"]),
        "--rule",
        "/rule/captured_rule.py",
        "--fixture",
        "/fixture/input.json",
        "--expected-rule-hash",
        str(config["captured_rule_sha256"]),
    ]
    started = time.monotonic()
    launch = run_host_command(command, timeout=30)
    timed_out = False
    process_exit = None
    stdout = ""
    stderr = launch.stderr
    try:
        if launch.returncode != 0:
            raise Task033HarnessError("TASK033_CONTAINER_LAUNCH_FAILED")
        waited = run_host_command(_wait_script(config, name), timeout=30)
        timed_out = waited.returncode == 124
        if not timed_out:
            try:
                process_exit = int(waited.stdout.strip().splitlines()[-1])
            except (IndexError, ValueError):
                process_exit = None
            logs = run_host_command(runtime_prefix(config) + ["logs", name], timeout=30)
            stdout = logs.stdout
            stderr += logs.stderr
    finally:
        run_host_command(runtime_prefix(config) + ["rm", "-f", name], timeout=30)
    elapsed = time.monotonic() - started
    inference = {
        "loaded": False,
        "exception_type": None,
        "output_returned": False,
        "output_count": None,
        "output_shape_valid": False,
        "output_binary_domain_valid": False,
        "output_finite": False,
        "output_sha256": None,
    }
    if not timed_out and process_exit == 0:
        payload = parse_single_json_output(stdout)
        inference = {key: payload.get(key) for key in inference}
    return {
        "run_index": run_index,
        "fixture_id": fixture["fixture_id"],
        "fixture_sha256": fixture["fixture_sha256"],
        "input_count": fixture["input_count"],
        "container_image_digest": image_digest,
        "rule_sha256": str(config["captured_rule_sha256"]),
        "command_hash": redacted_command_hash(command, rule_path, fixture_path),
        "process": {
            "exit_code": process_exit,
            "timed_out": timed_out,
            "duration_bucket": duration_bucket(elapsed),
            "stdout_hash": sha256_bytes(stdout.encode("utf-8")),
            "stderr_hash": sha256_bytes(stderr.encode("utf-8")),
        },
        "inference": inference,
    }


def fixture_replay_status(runs: Sequence[Mapping[str, Any]]) -> str:
    successful = [
        item
        for item in runs
        if item["process"]["exit_code"] == 0
        and not item["process"]["timed_out"]
        and item["inference"]["output_returned"]
    ]
    if len(successful) != 2:
        return "not_applicable_unsuccessful_fixture"
    fields = (
        "rule_sha256",
        "fixture_sha256",
        "container_image_digest",
        "input_count",
    )
    equal = all(successful[0][field] == successful[1][field] for field in fields)
    equal = equal and all(
        successful[0]["inference"][field] == successful[1]["inference"][field]
        for field in ("output_count", "output_sha256", "output_binary_domain_valid")
    )
    equal = equal and successful[0]["process"]["exit_code"] == successful[1]["process"]["exit_code"]
    return "deterministic" if equal else "runtime_nondeterministic"


def evaluate_e1_status(
    isolation: Mapping[str, Any], fixture_results: Sequence[Mapping[str, Any]]
) -> str:
    if isolation.get("status") != "passed":
        return "blocked_environment"
    required = {"constant_series", "monotonic_series", "localized_spike"}
    by_id = {str(item["fixture_id"]): item for item in fixture_results}
    for fixture_id in required:
        item = by_id.get(fixture_id)
        if item is None:
            return "failed_rule_runtime"
        if item.get("replay_status") == "runtime_nondeterministic":
            return "runtime_nondeterministic"
        runs = item["runs"]
        if any(run["process"]["exit_code"] != 0 or run["process"]["timed_out"] for run in runs):
            return "failed_rule_runtime"
        if any(
            not run["inference"]["output_shape_valid"]
            or not run["inference"]["output_binary_domain_valid"]
            or not run["inference"]["output_finite"]
            for run in runs
        ):
            return "failed_output_contract"
    return "passed_runtime_smoke"


def run_e1(config_path: Path, *, build: bool) -> dict[str, Any]:
    config = read_json(config_path)
    if config["runtime"]["selected"] != "wsl_native_rootless_podman":
        raise Task033HarnessError("TASK033_RUNTIME_SELECTION_INVALID")
    image = build_image(config) if build else inspect_image(config)
    isolation = run_isolation_smoke(config, image["image_digest"])
    if isolation["status"] != "passed":
        raise Task033HarnessError("TASK033_ISOLATION_PREFLIGHT_FAILED")
    static = static_rule_summary(private_rule_path(), config)
    fixture_results: list[dict[str, Any]] = []
    for entry in config["fixtures"]:
        path = REPO_ROOT / str(entry["path"])
        fixture = validate_fixture(path)
        runs = [
            execute_fixture_once(config, path, fixture, image["image_digest"], run_index)
            for run_index in (1, 2)
        ]
        fixture_results.append(
            {**fixture, "runs": runs, "replay_status": fixture_replay_status(runs)}
        )
    report = {
        "schema_version": "1.0",
        "artifact_type": "task033_e1_runtime_report",
        "task_id": "TASK-033",
        "statement": config["statement"],
        "frozen_lineage": config["frozen_lineage"],
        "runtime": config["runtime"],
        "image": image,
        "isolation_preflight": isolation,
        "static_rule_verification": static,
        "fixtures": fixture_results,
        "execution_count": sum(len(item["runs"]) for item in fixture_results),
        "e1_status": evaluate_e1_status(isolation, fixture_results),
        "provider_calls": 0,
        "dataset_accessed": False,
        "performance_metrics_computed": False,
        "repair_agent_executed": False,
        "review_agent_executed": False,
        "detector_executed": False,
        "fusion_executed": False,
        "raw_rule_source_included": False,
        "raw_output_arrays_included": False,
        "private_paths_included": False,
        "config_sha256": sha256_file(config_path),
    }
    report["report_hash"] = sha256_json(report)
    verify_rule_hash(private_rule_path(), str(config["captured_rule_sha256"]))
    output = REPO_ROOT / str(config["report_output"])
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task033_e1_runtime_smoke.json")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    path = Path(args.config)
    if not path.is_absolute():
        path = REPO_ROOT / path
    report = run_e1(path.resolve(), build=args.build)
    print(
        stable_json(
            {
                "e1_status": report["e1_status"],
                "execution_count": report["execution_count"],
                "rule_sha256": report["static_rule_verification"]["rule_sha256"],
                "performance_metrics_computed": report["performance_metrics_computed"],
            }
        )
    )
    return 0 if report["e1_status"] == "passed_runtime_smoke" else 1


if __name__ == "__main__":
    raise SystemExit(main())
