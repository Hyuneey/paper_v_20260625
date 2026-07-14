"""Host orchestrator for TASK-034 validation-only container execution."""

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

import numpy as np

from experiments.argos_reproduction.argos_source_faithful_metrics import (
    argos_label_aware_validation_diagnostics,
    source_faithful_metric_protocol_hash,
    verify_frozen_synthetic_fidelity,
)
from experiments.argos_reproduction.kpi_split_guard import (
    compute_pinned_argos_split,
    read_validation_prefix,
    sha256_file,
    split_manifest_payload,
)
from experiments.argos_reproduction.kpi_validation_metrics import (
    direct_binary_validation_diagnostics,
    metric_protocol_hash,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_RULE_HASH = "e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659"
STDIO_LIMIT_BYTES = 65_536


class Task034RunnerError(RuntimeError):
    """Fail-closed orchestration error with a stable issue code."""


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise Task034RunnerError("TASK034_JSON_OBJECT_REQUIRED")
    return payload


def stable_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(stable_json_bytes(value)).hexdigest()


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
        raise Task034RunnerError("TASK034_HOST_COMMAND_FAILED")
    return completed


def git_clean_commit() -> str:
    status = run_host_command(["git", "status", "--porcelain"], timeout=30, check=True)
    if status.stdout.strip():
        raise Task034RunnerError("TASK034_EXECUTION_WORKTREE_NOT_CLEAN")
    head = run_host_command(["git", "rev-parse", "HEAD"], timeout=30, check=True).stdout.strip()
    if len(head) != 40:
        raise Task034RunnerError("TASK034_EXECUTION_COMMIT_INVALID")
    return head


def private_rule_path() -> Path:
    return (
        REPO_ROOT
        / "artifacts/private_argos_reproduction/task026q/quarantine"
        / f"{FROZEN_RULE_HASH}.py"
    )


def verify_rule_static(path: Path, expected_hash: str) -> dict[str, Any]:
    if not path.is_file() or sha256_file(path) != expected_hash:
        raise Task034RunnerError("TASK034_RULE_HASH_MISMATCH")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "inference"]
    if len(functions) != 1 or len(functions[0].args.args) != 1 or functions[0].args.args[0].arg != "sample":
        raise Task034RunnerError("TASK034_RULE_SIGNATURE_INVALID")
    return {
        "rule_sha256": expected_hash,
        "syntax_status": "passed",
        "inference_function_count": 1,
        "signature_status": "passed",
        "source_modified": False,
        "source_in_tracked_report": False,
    }


def runtime_prefix(config: Mapping[str, Any]) -> list[str]:
    runtime = config["runtime"]
    return [
        "wsl", "-d", str(runtime["wsl_distribution"]), "-u", "root", "--",
        "runuser", "-u", str(runtime["rootless_user"]), "--", "env",
        f"XDG_RUNTIME_DIR={runtime['xdg_runtime_dir']}",
        f"DBUS_SESSION_BUS_ADDRESS=unix:path={runtime['xdg_runtime_dir']}/bus",
        "podman",
    ]


def windows_to_wsl(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    suffix = resolved.as_posix().split(":", 1)[1]
    return f"/mnt/{drive}{suffix}"


def private_root(config: Mapping[str, Any]) -> Path:
    return REPO_ROOT / str(config["private_output_root"])


def prepare_build_context(config: Mapping[str, Any]) -> Path:
    target = private_root(config) / "build_context"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "containers/argos_rule_validation/Containerfile", target / "Containerfile")
    shutil.copy2(REPO_ROOT / "containers/argos_rule_validation/requirements.lock", target / "requirements.lock")
    shutil.copy2(
        REPO_ROOT / "experiments/argos_reproduction/kpi_validation_entrypoint.py",
        target / "kpi_validation_entrypoint.py",
    )
    return target


def inspect_image(config: Mapping[str, Any]) -> dict[str, Any]:
    command = runtime_prefix(config) + ["image", "inspect", str(config["image"]["local_reference"])]
    payload = json.loads(run_host_command(command, timeout=30, check=True).stdout)[0]
    image_id = str(payload.get("Id", ""))
    if len(image_id) == 64 and all(character in "0123456789abcdef" for character in image_id.lower()):
        image_id = f"sha256:{image_id}"
    digest = str(payload.get("Digest") or image_id)
    if not image_id.startswith("sha256:") or not digest.startswith("sha256:"):
        raise Task034RunnerError("TASK034_IMAGE_ID_INVALID")
    return {
        "image_id": image_id,
        "image_digest": digest,
        "base_image_reference": str(config["image"]["pinned_from"]),
        "python_version": str(config["image"]["python_version"]),
        "numpy_version": str(config["image"]["numpy_version"]),
    }


def build_image(config: Mapping[str, Any]) -> dict[str, Any]:
    context = prepare_build_context(config)
    command = runtime_prefix(config) + [
        "build", "--network", "slirp4netns", "--tag", str(config["image"]["local_reference"]),
        "--file", f"{windows_to_wsl(context)}/Containerfile", windows_to_wsl(context),
    ]
    run_host_command(command, timeout=300, check=True)
    return inspect_image(config)


def isolation_arguments(config: Mapping[str, Any]) -> list[str]:
    policy = config["isolation"]
    return [
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--pids-limit", str(policy["pids_limit"]),
        "--cpus", str(policy["cpu_limit"]), "--memory", str(policy["memory_limit"]),
        "--tmpfs", str(policy["tmpfs"]), "--user", "1000:1000",
    ]


def parse_json_stdout(stdout: str) -> dict[str, Any]:
    if len(stdout.encode("utf-8")) > STDIO_LIMIT_BYTES:
        raise Task034RunnerError("TASK034_STDOUT_TOO_LARGE")
    lines = [line for line in stdout.splitlines() if line.strip().startswith("{")]
    if len(lines) != 1:
        raise Task034RunnerError("TASK034_STDOUT_JSON_INVALID")
    payload = json.loads(lines[0])
    if not isinstance(payload, dict):
        raise Task034RunnerError("TASK034_STDOUT_JSON_INVALID")
    return payload


def run_isolation_probe(config: Mapping[str, Any], image_id: str) -> dict[str, Any]:
    command = runtime_prefix(config) + [
        "run", "--rm", *isolation_arguments(config), image_id, "--isolation-probe",
    ]
    completed = run_host_command(command, timeout=30, check=True)
    probe = parse_json_stdout(completed.stdout)["isolation_probe"]
    passed = (
        probe["uid"] != 0
        and probe["network_interfaces"] == ["lo"]
        and probe["network_connect_blocked"]
        and probe["root_write_blocked"]
        and probe["memory_max"] == "536870912"
        and probe["pids_max"] == "64"
        and probe["cpu_max"] == "100000 100000"
    )
    return {
        "status": "passed" if passed else "failed",
        "non_root_verified": probe["uid"] != 0,
        "network_none_verified": probe["network_interfaces"] == ["lo"] and probe["network_connect_blocked"],
        "read_only_root_verified": probe["root_write_blocked"],
        "memory_limit_verified": probe["memory_max"] == "536870912",
        "pids_limit_verified": probe["pids_max"] == "64",
        "cpu_limit_verified": probe["cpu_max"] == "100000 100000",
        "research_mounts_present": False,
    }


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
    return ["wsl", "-d", str(runtime["wsl_distribution"]), "-u", "root", "--", "bash", "-lc", script]


def duration_bucket(seconds: float) -> str:
    if seconds < 5:
        return "under_5_seconds"
    if seconds < 30:
        return "5_to_30_seconds"
    if seconds < 120:
        return "30_to_120_seconds"
    return "timeout_boundary_or_above"


def execute_validation_once(
    config: Mapping[str, Any], image: Mapping[str, Any], values_path: Path, run_index: int
) -> dict[str, Any]:
    rule_path = private_rule_path()
    expected_rule_hash = str(config["captured_rule_sha256"])
    verify_rule_static(rule_path, expected_rule_hash)
    validation_hash = sha256_file(values_path)
    output_dir = private_root(config) / f"container_output_run_{run_index}"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    name = f"task034-validation-{run_index}"
    command = runtime_prefix(config) + [
        "run", "--detach", "--name", name, *isolation_arguments(config),
        "--mount", f"type=bind,src={windows_to_wsl(rule_path)},dst=/rule/captured_rule.py,ro",
        "--mount", f"type=bind,src={windows_to_wsl(values_path)},dst=/input/validation_values.npy,ro",
        "--mount", f"type=bind,src={windows_to_wsl(output_dir)},dst=/output,rw",
        str(image["image_id"]),
        "--rule", "/rule/captured_rule.py", "--values", "/input/validation_values.npy",
        "--output", "/output", "--expected-rule-hash", expected_rule_hash,
        "--expected-input-hash", validation_hash,
    ]
    started = time.monotonic()
    launch = run_host_command(command, timeout=30)
    stdout = ""
    stderr = launch.stderr
    timed_out = False
    exit_code: int | None = None
    actual_image_id: str | None = None
    try:
        if launch.returncode != 0:
            raise Task034RunnerError("TASK034_CONTAINER_LAUNCH_FAILED")
        inspect = run_host_command(
            runtime_prefix(config) + ["inspect", "--format", "{{.Image}}", name], timeout=30, check=True
        )
        actual_image_id = inspect.stdout.strip()
        if actual_image_id.removeprefix("sha256:") != str(image["image_id"]).removeprefix("sha256:"):
            raise Task034RunnerError("TASK034_CONTAINER_IMAGE_MISMATCH")
        waited = run_host_command(_wait_script(config, name), timeout=150)
        timed_out = waited.returncode == 124
        if not timed_out:
            try:
                exit_code = int(waited.stdout.strip().splitlines()[-1])
            except (IndexError, ValueError):
                exit_code = None
            logs = run_host_command(runtime_prefix(config) + ["logs", name], timeout=30)
            stdout = logs.stdout
            stderr += logs.stderr
    finally:
        run_host_command(runtime_prefix(config) + ["rm", "-f", name], timeout=30)
    elapsed = time.monotonic() - started
    if len(stderr.encode("utf-8")) > STDIO_LIMIT_BYTES:
        raise Task034RunnerError("TASK034_STDERR_TOO_LARGE")
    if timed_out or exit_code != 0:
        raise Task034RunnerError("TASK034_RULE_RUNTIME_FAILED")
    metadata = parse_json_stdout(stdout)
    prediction_source = output_dir / "prediction.npy"
    result_source = output_dir / "result.json"
    if not prediction_source.is_file() or not result_source.is_file():
        raise Task034RunnerError("TASK034_CONTAINER_OUTPUT_MISSING")
    total_size = sum(path.stat().st_size for path in output_dir.iterdir() if path.is_file())
    if total_size > int(config["isolation"]["output_limit_bytes"]):
        raise Task034RunnerError("TASK034_CONTAINER_OUTPUT_TOO_LARGE")
    prediction_target = private_root(config) / f"prediction_run_{run_index}.npy"
    shutil.copy2(prediction_source, prediction_target)
    if sha256_file(prediction_target) != metadata["prediction_sha256"]:
        raise Task034RunnerError("TASK034_PREDICTION_HASH_MISMATCH")
    return {
        "run_index": run_index,
        "actual_container_image_id": actual_image_id,
        "validation_input_sha256": validation_hash,
        "prediction_sha256": metadata["prediction_sha256"],
        "validation_row_count": metadata["validation_row_count"],
        "predicted_positive_count": metadata["predicted_positive_count"],
        "output_count": metadata["output_count"],
        "output_shape_valid": metadata["output_shape_valid"],
        "output_binary_domain_valid": metadata["output_binary_domain_valid"],
        "output_finite": metadata["output_finite"],
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_bucket": duration_bucket(elapsed),
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
        "container_removed": True,
        "labels_mounted": False,
        "repository_root_mounted": False,
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    value = dict(payload)
    value["report_hash"] = sha256_json(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _code_hashes(config_path: Path) -> dict[str, str]:
    paths = {
        "host_harness_sha256": REPO_ROOT / "experiments/argos_reproduction/kpi_validation_runner.py",
        "container_entrypoint_sha256": REPO_ROOT / "experiments/argos_reproduction/kpi_validation_entrypoint.py",
        "containerfile_sha256": REPO_ROOT / "containers/argos_rule_validation/Containerfile",
        "requirements_sha256": REPO_ROOT / "containers/argos_rule_validation/requirements.lock",
        "config_sha256": config_path,
        "metric_module_sha256": REPO_ROOT / "experiments/argos_reproduction/kpi_validation_metrics.py",
        "source_faithful_metric_module_sha256": REPO_ROOT / "experiments/argos_reproduction/argos_source_faithful_metrics.py",
        "split_module_sha256": REPO_ROOT / "experiments/argos_reproduction/kpi_split_guard.py",
    }
    return {name: sha256_file(path) for name, path in paths.items()}


def run_e2(config_path: Path, *, build: bool) -> dict[str, Any]:
    execution_commit = git_clean_commit()
    config = read_json(config_path)
    rule_static = verify_rule_static(private_rule_path(), str(config["captured_rule_sha256"]))
    csv_path = REPO_ROOT / str(config["converted_csv"]["private_relative_path"])
    if sha256_file(csv_path) != config["converted_csv"]["sha256"]:
        raise Task034RunnerError("TASK034_PRIVATE_DATA_HASH_MISMATCH")
    boundaries = compute_pinned_argos_split(
        int(config["converted_csv"]["row_count"]),
        train_test_split=float(config["split"]["train_test_split"]),
        validation_split=float(config["split"]["validation_split"]),
    )
    manifest = split_manifest_payload(
        boundaries,
        source_commit=str(config["frozen_lineage"]["argos_commit"]),
        source_blob_hash=str(config["split"]["source_blob_hash"]),
    )
    private = private_root(config)
    private.mkdir(parents=True, exist_ok=True)
    (private / "split_manifest.private.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    guarded = read_validation_prefix(csv_path, boundaries)
    values_path = private / "validation_values.npy"
    labels_path = private / "validation_labels.npy"
    np.save(values_path, guarded.values, allow_pickle=False)
    np.save(labels_path, guarded.labels, allow_pickle=False)
    image = build_image(config) if build else inspect_image(config)
    isolation = run_isolation_probe(config, image["image_id"])
    if isolation["status"] != "passed":
        raise Task034RunnerError("TASK034_ISOLATION_FAILED")
    runs = [execute_validation_once(config, image, values_path, index) for index in (1, 2)]
    replay_fields = (
        "validation_input_sha256", "prediction_sha256", "validation_row_count",
        "predicted_positive_count", "output_count", "exit_code",
    )
    deterministic = all(runs[0][field] == runs[1][field] for field in replay_fields)
    deterministic = deterministic and all(
        run["actual_container_image_id"].removeprefix("sha256:") == image["image_id"].removeprefix("sha256:")
        for run in runs
    )
    if not deterministic:
        raise Task034RunnerError("TASK034_RUNTIME_NONDETERMINISTIC")
    predictions = np.load(private / "prediction_run_1.npy", allow_pickle=False)
    labels = np.load(labels_path, allow_pickle=False)
    direct = direct_binary_validation_diagnostics(labels, predictions)
    fidelity = verify_frozen_synthetic_fidelity()
    if fidelity["status"] != "passed":
        raise Task034RunnerError("TASK034_METRIC_FIDELITY_FAILED")
    supplementary = argos_label_aware_validation_diagnostics(predictions, labels)
    smoothed = supplementary.pop("smoothed_scores")
    smoothed_path = private / "smoothed_validation_scores.npy"
    np.save(smoothed_path, smoothed, allow_pickle=False)
    code_hashes = _code_hashes(config_path)
    common = {
        "schema_version": "1.0",
        "task_id": "TASK-034",
        "statement": config["statement"],
        "execution_code_commit": execution_commit,
        "selected_kpi_id": config["selected_kpi_id"],
        "captured_rule_sha256": config["captured_rule_sha256"],
        "provider_calls": 0,
        "agents_executed": False,
        "detector_executed": False,
        "fusion_executed": False,
        "benchmark_claim": False,
        "private_paths_included": False,
    }
    split_report = {
        **common,
        "artifact_type": "task034_split_manifest",
        **boundaries.to_dict(),
        "boundary_algorithm": manifest["boundary_algorithm"],
        "source_commit": manifest["source_commit"],
        "source_file": manifest["source_file"],
        "source_lineage_hash": manifest["source_lineage_hash"],
        "split_manifest_hash": manifest["split_manifest_hash"],
        "maximum_parsed_row_exclusive": guarded.maximum_parsed_row_exclusive,
        "test_rows_parsed": guarded.test_rows_parsed,
        "test_status": "sealed_not_accessed",
        "phase2_ground_truth_package_accessed": False,
    }
    runtime_report = {
        **common,
        "artifact_type": "task034_runtime_report",
        "image": image,
        "isolation": isolation,
        "rule_static_verification": rule_static,
        "runs": runs,
        "runtime_replay": "deterministic",
        "execution_count": 2,
        "validation_labels_mounted": False,
        "train_or_test_data_mounted": False,
        "code_hashes": code_hashes,
    }
    metrics_report = {
        **common,
        "artifact_type": "task034_validation_metrics_report",
        "direct_binary_validation_diagnostics": direct,
        "argos_label_aware_validation_diagnostics": supplementary,
        "metric_fidelity": fidelity,
        "direct_metric_protocol_hash": metric_protocol_hash(),
        "paper_faithful_metric_protocol_hash": source_faithful_metric_protocol_hash(),
        "validation_label_sha256": sha256_file(labels_path),
        "validation_prediction_sha256": runs[0]["prediction_sha256"],
        "smoothed_score_sha256": sha256_file(smoothed_path),
        "test_metrics_computed": False,
    }
    freeze_report = {
        **common,
        "artifact_type": "task034_e3_freeze_record",
        "rule_sha256": config["captured_rule_sha256"],
        "split_manifest_hash": manifest["split_manifest_hash"],
        "validation_input_hash": sha256_file(values_path),
        "validation_label_hash": sha256_file(labels_path),
        "validation_prediction_hash": runs[0]["prediction_sha256"],
        "smoothed_score_hash": sha256_file(smoothed_path),
        "direct_metric_protocol_hash": metric_protocol_hash(),
        "paper_faithful_metric_protocol_hash": source_faithful_metric_protocol_hash(),
        "score_source": "smooth_labels_window_3",
        "selection_split": "validation",
        "selection_metric": "Event-F1-PA",
        "frozen_event_f1_pa_threshold": supplementary["event_f1_pa"]["threshold"],
        "tie_breaking_policy": supplementary["tie_breaking_policy"],
        "smoothing_window": 3,
        "metric_source_commit": supplementary["source_commit"],
        "container_image_id": image["image_id"],
        "container_image_digest": image["image_digest"],
        "execution_config_hash": code_hashes["config_sha256"],
        "e3_test_status": "sealed_not_accessed",
        "e3_run_status": "not_run",
        "e3_authorization_status": "not_authorized",
    }
    for key, report in (
        ("split", split_report), ("runtime", runtime_report),
        ("metrics", metrics_report), ("freeze", freeze_report),
    ):
        _write_report(REPO_ROOT / str(config["reports"][key]), report)
    return {
        "e2_status": "passed_validation_feasibility",
        "execution_code_commit": execution_commit,
        "prediction_sha256": runs[0]["prediction_sha256"],
        "validation_row_count": boundaries.validation_row_count,
        "frozen_event_f1_pa_threshold": supplementary["event_f1_pa"]["threshold"],
        "test_status": "sealed_not_accessed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task034_e2_kpi_validation.json")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    result = run_e2(config_path.resolve(), build=args.build)
    print(stable_json_bytes(result).decode("utf-8"))
    return 0 if result["e2_status"] == "passed_validation_feasibility" else 1


if __name__ == "__main__":
    raise SystemExit(main())
