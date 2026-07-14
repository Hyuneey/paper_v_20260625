"""Rootless-Podman runtime gate and cohort adequacy aggregation for TASK-035A."""

from __future__ import annotations

import argparse
from collections import defaultdict
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

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, read_json, sha256_file, sha256_json, write_json


class MultiRuleRuntimeError(RuntimeError):
    pass


def safe_host_environment() -> dict[str, str]:
    allowed = ("SYSTEMROOT", "WINDIR", "PATH", "COMSPEC", "TEMP", "TMP", "PATHEXT")
    return {name: os.environ[name] for name in allowed if name in os.environ}


def host_command(command: Sequence[str], *, timeout: float, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(list(command), capture_output=True, text=True, timeout=timeout, env=safe_host_environment(), encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        raise MultiRuleRuntimeError("TASK035A_HOST_COMMAND_FAILED")
    return result


def runtime_prefix(config: Mapping[str, Any]) -> list[str]:
    runtime = config["runtime"]
    return ["wsl", "-d", runtime["wsl_distribution"], "-u", "root", "--", "runuser", "-u", runtime["rootless_user"], "--", "env", f"XDG_RUNTIME_DIR={runtime['xdg_runtime_dir']}", f"DBUS_SESSION_BUS_ADDRESS=unix:path={runtime['xdg_runtime_dir']}/bus", "podman"]


def windows_to_wsl(path: Path) -> str:
    resolved = path.resolve(); drive = resolved.drive.rstrip(":").lower(); suffix = resolved.as_posix().split(":", 1)[1]
    return f"/mnt/{drive}{suffix}"


def isolation_arguments(config: Mapping[str, Any]) -> list[str]:
    policy = config["isolation"]
    return ["--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", str(policy["pids_limit"]), "--cpus", str(policy["cpu_limit"]), "--memory", policy["memory_limit"], "--tmpfs", policy["tmpfs"], "--user", "1000:1000"]


def prepare_build_context(config: Mapping[str, Any]) -> Path:
    target = REPO_ROOT / config["private_root"] / "runtime_build_context"
    if target.exists(): shutil.rmtree(target)
    target.mkdir(parents=True)
    for source, name in (
        (REPO_ROOT / "containers/argos_multi_rule_runtime/Containerfile", "Containerfile"),
        (REPO_ROOT / "containers/argos_multi_rule_runtime/requirements.lock", "requirements.lock"),
        (REPO_ROOT / "experiments/argos_reproduction/multi_rule_container_entrypoint.py", "multi_rule_container_entrypoint.py"),
    ): shutil.copy2(source, target / name)
    return target


def inspect_image(config: Mapping[str, Any]) -> dict[str, str]:
    raw = host_command(runtime_prefix(config) + ["image", "inspect", config["image"]["local_reference"]], timeout=30, check=True).stdout
    payload = json.loads(raw)[0]; image_id = payload.get("Id", "")
    if len(image_id) == 64: image_id = "sha256:" + image_id
    digest = payload.get("Digest") or image_id
    if not str(image_id).startswith("sha256:") or not str(digest).startswith("sha256:"):
        raise MultiRuleRuntimeError("TASK035A_IMAGE_ID_INVALID")
    return {"image_id": image_id, "image_digest": digest, "base_image_reference": config["image"]["pinned_from"], "python_version": config["image"]["python_version"], "numpy_version": config["image"]["numpy_version"]}


def build_image(config: Mapping[str, Any]) -> dict[str, str]:
    context = prepare_build_context(config)
    host_command(runtime_prefix(config) + ["build", "--network", "slirp4netns", "--tag", config["image"]["local_reference"], "--file", windows_to_wsl(context / "Containerfile"), windows_to_wsl(context)], timeout=600, check=True)
    return inspect_image(config)


def isolation_probe(config: Mapping[str, Any], image_id: str) -> dict[str, Any]:
    result = host_command(runtime_prefix(config) + ["run", "--rm", *isolation_arguments(config), image_id, "--isolation-probe"], timeout=30, check=True)
    probe = json.loads(result.stdout.strip())["isolation_probe"]
    passed = probe["uid"] != 0 and probe["interfaces"] == ["lo"] and probe["network_blocked"] and probe["root_write_blocked"] and probe["memory_max"] == "268435456" and probe["pids_max"] == "64" and probe["cpu_max"] == "100000 100000"
    return {"status": "passed" if passed else "failed", "network_none_verified": probe["interfaces"] == ["lo"] and probe["network_blocked"], "non_root_verified": probe["uid"] != 0, "read_only_root_verified": probe["root_write_blocked"], "cpu_limit_verified": probe["cpu_max"] == "100000 100000", "memory_limit_verified": probe["memory_max"] == "268435456", "pids_limit_verified": probe["pids_max"] == "64", "research_mounts_present": False}


def _wait_command(config: Mapping[str, Any], name: str) -> list[str]:
    runtime = config["runtime"]; seconds = int(config["isolation"]["timeout_seconds"])
    command = f"runuser -u {runtime['rootless_user']} -- env XDG_RUNTIME_DIR={runtime['xdg_runtime_dir']} DBUS_SESSION_BUS_ADDRESS=unix:path={runtime['xdg_runtime_dir']}/bus podman"
    script = f"timeout --foreground {seconds}s {command} wait {name}; code=$?; if [ $code -eq 124 ]; then {command} rm -f {name} >/dev/null 2>&1; fi; exit $code"
    return ["wsl", "-d", runtime["wsl_distribution"], "-u", "root", "--", "bash", "-lc", script]


def execute_slot(config: Mapping[str, Any], image: Mapping[str, str], slot: Mapping[str, Any], rule_hash: str) -> dict[str, Any]:
    private_root = REPO_ROOT / config["private_root"]
    rule = private_root / "quarantine" / f"{rule_hash}.py"
    if sha256_file(rule) != rule_hash: raise MultiRuleRuntimeError("TASK035A_RULE_HASH_MISMATCH")
    anchor = private_root / "anchors" / slot["kpi_id"] / f"{slot['anchor_id']}.npz"
    with np.load(anchor, allow_pickle=False) as data: values = np.asarray(data["values"], dtype=np.float64).reshape(-1, 1)
    output = private_root / "runtime" / slot["slot_id"]
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    values_path = output / "input_values.npy"; np.save(values_path, values, allow_pickle=False)
    input_hash = sha256_file(values_path); name = "task035a-" + slot["slot_id"].lower()
    command = runtime_prefix(config) + ["run", "--detach", "--name", name, *isolation_arguments(config),
        "--mount", f"type=bind,src={windows_to_wsl(rule)},dst=/rule/generated_rule.py,ro",
        "--mount", f"type=bind,src={windows_to_wsl(values_path)},dst=/input/input_values.npy,ro",
        "--mount", f"type=bind,src={windows_to_wsl(output)},dst=/output,rw", image["image_id"],
        "--rule", "/rule/generated_rule.py", "--values", "/input/input_values.npy", "--output", "/output", "--rule-hash", rule_hash, "--input-hash", input_hash]
    started = time.monotonic(); launch = host_command(command, timeout=30); stdout = ""; stderr = launch.stderr; timed_out = False; exit_code: int | None = None
    try:
        if launch.returncode != 0: raise MultiRuleRuntimeError("TASK035A_CONTAINER_LAUNCH_FAILED")
        waited = host_command(_wait_command(config, name), timeout=int(config["isolation"]["timeout_seconds"]) + 30)
        timed_out = waited.returncode == 124
        if not timed_out:
            try: exit_code = int(waited.stdout.strip().splitlines()[-1])
            except (IndexError, ValueError): exit_code = None
            logs = host_command(runtime_prefix(config) + ["logs", name], timeout=30); stdout = logs.stdout; stderr += logs.stderr
    finally:
        host_command(runtime_prefix(config) + ["rm", "-f", name], timeout=30)
    elapsed = time.monotonic() - started
    if timed_out or exit_code != 0:
        return {"runtime_status": "runtime_failed", "exit_code": exit_code, "timed_out": timed_out, "duration_bucket": "timeout" if timed_out else "under_timeout", "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(), "labels_mounted": False}
    lines = [line for line in stdout.splitlines() if line.strip().startswith("{")]
    if len(lines) != 1: return {"runtime_status": "runtime_failed", "exit_code": exit_code, "timed_out": False, "labels_mounted": False}
    metadata = json.loads(lines[0]); valid = metadata["output_shape_valid"] and metadata["output_binary_domain_valid"] and metadata["output_finite"] and metadata["output_count"] == metadata["input_count"]
    return {"runtime_status": "executable_rule" if valid else "output_contract_failed", "exit_code": exit_code, "timed_out": False, "duration_bucket": "under_5_seconds" if elapsed < 5 else "5_seconds_or_more", "input_sha256": input_hash, "output_sha256": metadata.get("output_sha256"), "output_count": metadata.get("output_count"), "output_shape_valid": metadata.get("output_shape_valid"), "output_binary_domain_valid": metadata.get("output_binary_domain_valid"), "output_finite": metadata.get("output_finite"), "labels_mounted": False, "repository_root_mounted": False, "container_removed": True}


def run_runtime(config_path: Path, *, build: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_json(config_path); static = read_json(REPO_ROOT / config["reports"]["static"]); provider = read_json(REPO_ROOT / config["reports"]["provider"])
    image = build_image(config) if build else inspect_image(config); probe = isolation_probe(config, image["image_id"])
    if probe["status"] != "passed": raise MultiRuleRuntimeError("TASK035A_ISOLATION_PROBE_FAILED")
    provider_by_slot = {item["slot_id"]: item for item in provider["slots"]}; results: list[dict[str, Any]] = []
    for audit in static["slots"]:
        base = {key: audit[key] for key in ("slot_id", "kpi_id", "anchor_id", "replicate_id")}
        if audit.get("static_status") != "static_valid":
            results.append({**base, "terminal_status": audit["terminal_status"], "runtime_attempted": False}); continue
        runtime = execute_slot(config, image, audit, audit["rule_sha256"])
        results.append({**base, "rule_sha256": audit["rule_sha256"], "terminal_status": runtime["runtime_status"], "runtime_attempted": True, **runtime})
    runtime_report = {"schema_version": "1.0", "task_id": "TASK-035A", "artifact_type": "runtime_report", "image": image, "isolation": probe, "runtime_executable": sum(item["terminal_status"] == "executable_rule" for item in results), "output_contract_valid": sum(item["terminal_status"] == "executable_rule" for item in results), "slots": results, "labels_mounted": False, "performance_metrics_computed": False, "raw_outputs_tracked": False}
    runtime_report["report_hash"] = sha256_json(runtime_report); write_json(REPO_ROOT / config["reports"]["runtime"], runtime_report)
    per_kpi: dict[str, dict[str, Any]] = defaultdict(lambda: {"responses": 0, "static_valid": 0, "executable": 0, "rule_hashes": set()})
    static_by_slot = {item["slot_id"]: item for item in static["slots"]}
    for result in results:
        item = per_kpi[result["kpi_id"]]; capture = provider_by_slot[result["slot_id"]]
        item["responses"] += capture["capture_status"] == "provider_response_captured"
        item["static_valid"] += static_by_slot[result["slot_id"]].get("static_status") == "static_valid"
        item["executable"] += result["terminal_status"] == "executable_rule"
        if result.get("rule_sha256") and result["terminal_status"] == "executable_rule": item["rule_hashes"].add(result["rule_sha256"])
    per_kpi_report = {kpi: {"responses": item["responses"], "static_valid": item["static_valid"], "executable": item["executable"], "distinct_rule_hashes": len(item["rule_hashes"])} for kpi, item in sorted(per_kpi.items())}
    thresholds = config["adequacy"]; provider_responses = provider["responses_captured"]; executable = runtime_report["runtime_executable"]
    if provider_responses < thresholds["minimum_provider_responses"]: status = "insufficient_provider_yield"
    elif executable < thresholds["minimum_executable_rules_total"] or any(item["executable"] < thresholds["minimum_executable_rules_per_kpi"] for item in per_kpi_report.values()) or sum(item["executable"] >= 7 for item in per_kpi_report.values()) < thresholds["minimum_kpis_with_at_least_7_executable_rules"]: status = "insufficient_rule_yield"
    elif any(item["distinct_rule_hashes"] < thresholds["minimum_distinct_rule_hashes_per_kpi"] for item in per_kpi_report.values()): status = "insufficient_rule_diversity"
    else: status = "passed_generation_cohort"
    receipt = read_json(REPO_ROOT / config["private_root"] / "execution_receipt.json")
    code_paths = {"cohort_module_hash": "experiments/argos_reproduction/expanded_kpi_cohort.py", "anchor_module_hash": "experiments/argos_reproduction/anomaly_anchor_selection.py", "prompt_module_hash": "experiments/argos_reproduction/multi_prompt_capture.py", "provider_harness_hash": "experiments/argos_reproduction/multi_provider_capture.py", "static_audit_hash": "experiments/argos_reproduction/multi_rule_static_audit.py", "container_entrypoint_hash": "experiments/argos_reproduction/multi_rule_container_entrypoint.py", "containerfile_hash": "containers/argos_multi_rule_runtime/Containerfile", "requirements_hash": "containers/argos_multi_rule_runtime/requirements.lock", "config_hash": str(config_path.relative_to(REPO_ROOT)), "approval_hash": config["provider"]["approval_path"]}
    lineage = {key: sha256_file(REPO_ROOT / value) for key, value in code_paths.items()}
    adequacy = {"schema_version": "1.0", "task_id": "TASK-035A", "artifact_type": "cohort_adequacy_report", "status": status, "selected_kpi_count": len(per_kpi_report), "anchor_count": 50, "registered_slot_count": len(results), "terminal_slot_count": len(results), "provider_responses": provider_responses, "executable_rules_total": executable, "kpis_with_at_least_7_executable_rules": sum(item["executable"] >= 7 for item in per_kpi_report.values()), "per_kpi": per_kpi_report, "thresholds": thresholds, "slots": [{key: item.get(key) for key in ("slot_id", "kpi_id", "anchor_id", "replicate_id", "terminal_status", "rule_sha256")} for item in results], "test_values_parsed": False, "test_labels_parsed": False, "repair_or_review_calls": 0, "response_driven_retries": 0, "execution_code_commit": receipt["execution_code_commit"], **lineage, "runtime_image_id": image["image_id"], "runtime_image_digest": image["image_digest"], "performance_metrics_computed": False}
    adequacy["report_hash"] = sha256_json(adequacy); write_json(REPO_ROOT / config["reports"]["adequacy"], adequacy)
    return runtime_report, adequacy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--config", default="configs/argos_reproduction/task035a_expanded_rule_cohort.json"); parser.add_argument("--build", action="store_true"); args = parser.parse_args()
    runtime, adequacy = run_runtime((REPO_ROOT / args.config).resolve(), build=args.build)
    print(json.dumps({"runtime_executable": runtime["runtime_executable"], "status": adequacy["status"]}))
    return 0 if adequacy["status"] == "passed_generation_cohort" else 2


if __name__ == "__main__": raise SystemExit(main())
