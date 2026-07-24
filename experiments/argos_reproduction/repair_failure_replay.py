"""Replay the frozen TASK-037D failures in fresh isolated containers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Mapping, Sequence

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
from experiments.argos_reproduction.error_conditioned_target_selection import (
    canonical_chunk_hash,
)
from experiments.argos_reproduction.multi_rule_runtime import (
    _wait_command,
    host_command,
    inspect_image,
    isolation_arguments,
    isolation_probe,
    runtime_prefix,
    windows_to_wsl,
)


class RepairFailureReplayError(RuntimeError):
    """Raised when frozen failure replay cannot proceed safely."""


def verify_report_hash(path: Path, expected: str) -> dict[str, Any]:
    payload = read_json(path)
    observed = payload.get("report_hash")
    material = {key: value for key, value in payload.items() if key != "report_hash"}
    if observed != sha256_json(material) or observed != expected:
        raise RepairFailureReplayError("TASK038B_LINEAGE_REPORT_HASH_MISMATCH")
    return payload


def verify_commit_ancestor(commit: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RepairFailureReplayError("TASK038B_REQUIRED_COMMIT_NOT_ANCESTOR")


def load_repair_population(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    verify_commit_ancestor(str(config["lineage"]["task038a_protocol_freeze_commit"]))
    hashes = config["task038a_hashes"]
    registry = verify_report_hash(
        ROOT / str(config["sources"]["initial_registry"]),
        str(hashes["initial_registry_hash"]),
    )
    verify_report_hash(
        ROOT / str(config["sources"]["branch_registry"]),
        str(hashes["branch_registry_hash"]),
    )
    verify_report_hash(
        ROOT / str(config["sources"]["protocol_freeze"]),
        str(hashes["protocol_freeze_hash"]),
    )
    allowed = set(config["population"]["allowed_initial_runtime_statuses"])
    records = [
        dict(item)
        for item in registry["records"]
        if item.get("repair_eligible") is True
    ]
    if len(registry["records"]) != int(config["population"]["initial_rule_slots"]):
        raise RepairFailureReplayError("TASK038B_INITIAL_REGISTRY_COUNT_MISMATCH")
    if len(records) != int(config["population"]["repair_candidates"]):
        raise RepairFailureReplayError("TASK038B_REPAIR_POPULATION_MISMATCH")
    if any(
        not item["initial_static_valid"]
        or item["initial_executable"]
        or item["initial_runtime_status"] not in allowed
        for item in records
    ):
        raise RepairFailureReplayError("TASK038B_REPAIR_POPULATION_INVALID")
    return sorted(records, key=lambda item: item["initial_slot_id"])


def _normalize_message(message: str) -> str:
    value = re.sub(r"[A-Za-z]:\\[^\s\"']+", "<private-path>", message)
    value = re.sub(r"/(?:mnt|home|Users|tmp)/[^\s\"']+", "<private-path>", value)
    value = re.sub(r"\b[0-9a-f]{12,64}\b", "<runtime-id>", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:500]


def sanitize_error_evidence(
    stderr: str, *, failure_stage: str, timed_out: bool
) -> dict[str, Any]:
    if timed_out:
        return {
            "exception_type": "TimeoutError",
            "normalized_message": "container execution exceeded the frozen timeout",
            "rule_line_number_if_available": None,
            "failure_stage": failure_stage,
            "expected_output_contract": "finite one-dimensional length-matched binary output",
            "error_category": "runtime_timeout",
        }
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    exception_type = "RuntimeError"
    message = "containerized rule execution failed"
    for line in reversed(lines):
        matched = re.match(
            r"^(?P<kind>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(?P<message>.*)$",
            line,
        )
        if matched:
            exception_type = matched.group("kind").split(".")[-1]
            message = matched.group("message") or message
            break
    line_number: int | None = None
    for line in lines:
        matched = re.search(r'File "/rule/generated_rule.py", line (\d+)', line)
        if matched:
            line_number = int(matched.group(1))
    normalized = _normalize_message(message)
    if "output contract invalid" in normalized.lower():
        category = "output_contract_failure"
    elif exception_type in {"ImportError", "ModuleNotFoundError"}:
        category = "runtime_import_failure"
    else:
        category = "runtime_exception"
    return {
        "exception_type": exception_type,
        "normalized_message": normalized,
        "rule_line_number_if_available": line_number,
        "failure_stage": failure_stage,
        "expected_output_contract": "finite one-dimensional length-matched binary output",
        "error_category": category,
    }


def _write_values_only(source: Path, target: Path, expected_chunk_hash: str) -> str:
    with np.load(source, allow_pickle=False) as payload:
        values = np.asarray(payload["values"], dtype=np.float64).reshape(-1, 1)
        labels = np.asarray(payload["labels"], dtype=np.int8).reshape(-1)
        indices = np.asarray(payload["indices"], dtype=np.int64).reshape(-1)
    if canonical_chunk_hash(values.reshape(-1), labels, indices) != expected_chunk_hash:
        raise RepairFailureReplayError("TASK038B_FROZEN_CHUNK_HASH_MISMATCH")
    if (
        values.ndim != 2
        or values.shape[1] != 1
        or not np.all(np.isfinite(values))
    ):
        raise RepairFailureReplayError("TASK038B_VALUES_ONLY_INPUT_INVALID")
    target.parent.mkdir(parents=True, exist_ok=True)
    np.save(target, values, allow_pickle=False)
    return sha256_file(target)


def execute_container_once(
    config: Mapping[str, Any],
    *,
    image_id: str,
    rule_path: Path,
    rule_hash: str,
    values_path: Path,
    output_dir: Path,
    name_parts: Sequence[str],
    failure_stage: str,
) -> dict[str, Any]:
    if sha256_file(rule_path) != rule_hash:
        raise RepairFailureReplayError("TASK038B_RULE_HASH_MISMATCH")
    input_hash = sha256_file(values_path)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    seed = ":".join(name_parts)
    name = "task038b-" + hashlib.sha256(seed.encode()).hexdigest()[:20]
    command = runtime_prefix(config) + [
        "run",
        "--detach",
        "--name",
        name,
        *isolation_arguments(config),
        "--mount",
        f"type=bind,src={windows_to_wsl(rule_path)},dst=/rule/generated_rule.py,ro",
        "--mount",
        f"type=bind,src={windows_to_wsl(values_path)},dst=/input/input_values.npy,ro",
        "--mount",
        f"type=bind,src={windows_to_wsl(output_dir)},dst=/output,rw",
        image_id,
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
    launch = host_command(command, timeout=30)
    stdout = ""
    stderr = launch.stderr
    timed_out = False
    exit_code: int | None = None
    try:
        if launch.returncode == 0:
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
        else:
            exit_code = launch.returncode
    finally:
        host_command(runtime_prefix(config) + ["rm", "-f", name], timeout=30)
    (output_dir / "private_stdout.log").write_text(stdout, encoding="utf-8")
    (output_dir / "private_stderr.log").write_text(stderr, encoding="utf-8")
    if timed_out or exit_code != 0:
        evidence = sanitize_error_evidence(
            stderr, failure_stage=failure_stage, timed_out=timed_out
        )
        return {
            "status": "failed",
            "failure_category": evidence["error_category"],
            "sanitized_error_hash": sha256_json(evidence),
            "sanitized_error": evidence,
            "input_hash": input_hash,
            "exit_code": exit_code,
            "timed_out": timed_out,
        }
    lines = [line for line in stdout.splitlines() if line.strip().startswith("{")]
    if len(lines) != 1:
        evidence = sanitize_error_evidence(
            "RuntimeError: machine-readable runtime result missing",
            failure_stage=failure_stage,
            timed_out=False,
        )
        return {
            "status": "failed",
            "failure_category": "runtime_result_missing",
            "sanitized_error_hash": sha256_json(evidence),
            "sanitized_error": evidence,
            "input_hash": input_hash,
            "exit_code": exit_code,
            "timed_out": False,
        }
    metadata = json.loads(lines[0])
    output_path = output_dir / "output_labels.npy"
    prediction = np.load(output_path, allow_pickle=False)
    return {
        "status": "valid",
        "failure_category": None,
        "sanitized_error_hash": None,
        "sanitized_error": None,
        "input_hash": input_hash,
        "exit_code": exit_code,
        "timed_out": False,
        "output_hash": metadata["output_sha256"],
        "output_count": int(metadata["output_count"]),
        "predicted_positive_count": int(np.sum(prediction == 1)),
    }


def _failing_fixture(
    record: Mapping[str, Any], runtime_record: Mapping[str, Any]
) -> str:
    status = record["initial_runtime_status"]
    if status == "target_runtime_failed":
        return "target"
    if status == "contrast_runtime_failed":
        return "contrast"
    target = runtime_record.get("target_runtime") or {}
    return "target" if target.get("status") == "output_contract_failed" else "contrast"


def run_failure_replay(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    population = load_repair_population(config)
    task037d_hashes = config["task037d_hashes"]
    requests = verify_report_hash(
        ROOT / str(config["sources"]["task037d_requests"]),
        str(task037d_hashes["request_manifest_hash"]),
    )
    verify_report_hash(
        ROOT / str(config["sources"]["task037d_static"]),
        str(task037d_hashes["static_audit_hash"]),
    )
    runtime = verify_report_hash(
        ROOT / str(config["sources"]["task037d_runtime"]),
        str(task037d_hashes["runtime_report_hash"]),
    )
    request_by_slot = {item["slot_id"]: item for item in requests["slots"]}
    runtime_by_slot = {item["slot_id"]: item for item in runtime["slots"]}
    image = inspect_image(config)
    if (
        image["image_id"] != config["image"]["expected_image_id"]
        or image["image_digest"] != config["image"]["expected_image_digest"]
    ):
        raise RepairFailureReplayError("TASK038B_RUNTIME_IMAGE_MISMATCH")
    isolation = isolation_probe(config, image["image_id"])
    if isolation["status"] != "passed":
        raise RepairFailureReplayError("TASK038B_ISOLATION_PROBE_FAILED")
    source_root = ROOT / str(config["sources"]["task037d_private_root"])
    private_root = ROOT / str(config["private_root"])
    records: list[dict[str, Any]] = []
    for record in population:
        slot_id = record["initial_slot_id"]
        source_slot = request_by_slot[slot_id]
        runtime_record = runtime_by_slot[slot_id]
        fixture = _failing_fixture(record, runtime_record)
        expected_chunk_hash = record[f"{fixture}_chunk_hash"]
        source_values = (
            source_root / "targets" / f"{fixture}_chunks" / f"{slot_id}.npz"
        )
        replay_root = private_root / "failure_replay" / slot_id / fixture
        values_path = replay_root / "input_values.npy"
        input_hash = _write_values_only(
            source_values, values_path, str(expected_chunk_hash)
        )
        rule_path = (
            source_root
            / "quarantine"
            / str(record["direction"]).lower()
            / f"{record['initial_rule_hash']}.py"
        )
        runs = [
            execute_container_once(
                config,
                image_id=image["image_id"],
                rule_path=rule_path,
                rule_hash=str(record["initial_rule_hash"]),
                values_path=values_path,
                output_dir=replay_root / f"run_{run_index}",
                name_parts=(slot_id, fixture, str(run_index)),
                failure_stage=fixture,
            )
            for run_index in (1, 2)
        ]
        reproducible = bool(
            all(item["status"] == "failed" for item in runs)
            and runs[0]["failure_category"] == runs[1]["failure_category"]
            and runs[0]["sanitized_error_hash"] == runs[1]["sanitized_error_hash"]
            and all(item["input_hash"] == input_hash for item in runs)
        )
        private_error = runs[0].get("sanitized_error")
        if private_error:
            write_json(replay_root / "sanitized_error.private.json", private_error)
        records.append(
            {
                "initial_slot_id": slot_id,
                "initial_rule_hash": record["initial_rule_hash"],
                "detector_variant": record["detector_variant"],
                "kpi_id": record["kpi_id"],
                "direction": record["direction"],
                "repair_reuse_key": record["repair_reuse_key"],
                "original_failure_status": record["initial_runtime_status"],
                "replay_1_status": runs[0]["status"],
                "replay_2_status": runs[1]["status"],
                "sanitized_error_category": runs[0].get("failure_category"),
                "sanitized_error_hash": runs[0].get("sanitized_error_hash"),
                "failing_fixture": fixture,
                "failing_input_hash": input_hash,
                "frozen_chunk_hash": source_slot[f"{fixture}_chunk_hash"],
                "failure_reproducible": reproducible,
                "repair_status": (
                    "eligible_for_repair_call"
                    if reproducible
                    else "blocked_nonreproducible_initial_failure"
                ),
            }
        )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038B",
        "artifact_type": "repair_failure_replay_report",
        "status": "failure_replay_complete",
        "frozen_repair_population": len(population),
        "all_initial_failures_replayed": len(records) == len(population),
        "reproducible_failure_count": sum(
            item["failure_reproducible"] for item in records
        ),
        "nonreproducible_failure_count": sum(
            not item["failure_reproducible"] for item in records
        ),
        "fresh_container_runs": 2 * len(records),
        "image": image,
        "isolation": isolation,
        "labels_mounted": False,
        "detector_predictions_mounted": False,
        "inner_access": False,
        "outer_access": False,
        "sealed_test_access": False,
        "records": records,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["failure_replay"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038b_repair_execution.json",
    )
    args = parser.parse_args()
    report = run_failure_replay((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "frozen_repair_population": report["frozen_repair_population"],
                "reproducible_failure_count": report[
                    "reproducible_failure_count"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
