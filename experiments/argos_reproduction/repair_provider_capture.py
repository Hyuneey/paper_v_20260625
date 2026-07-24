"""Execute the frozen TASK-038B Repair manifest once, receipt first."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.multi_provider_capture import (
    call_once,
    is_global_block,
)
from experiments.argos_reproduction.repair_failure_replay import verify_report_hash


class RepairProviderCaptureError(RuntimeError):
    """Raised when real Repair execution is not exactly authorized."""


def clean_execution_commit() -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    if status.stdout.strip():
        raise RepairProviderCaptureError("TASK038B_EXECUTION_WORKTREE_NOT_CLEAN")
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def approval_blockers(
    config: Mapping[str, Any],
    approval: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    allow_real_provider_call: bool,
) -> list[str]:
    exact = int(manifest["authorized_call_count"])
    checks = {
        "approved": True,
        "provider": config["provider"]["provider"],
        "model": config["provider"]["model"],
        "maximum_requests": exact,
        "maximum_requests_upper_bound": 13,
        "maximum_requests_per_initial_rule": 1,
        "maximum_input_tokens_per_call": 20000,
        "maximum_output_tokens_per_call": 6000,
        "maximum_total_declared_input_tokens": exact * 20000,
        "maximum_total_declared_output_tokens": exact * 6000,
        "temperature_parameter_sent": False,
        "provider_seed_sent": False,
        "automatic_retry": False,
        "manual_retry": False,
        "replacement_generation": False,
        "review_agent_calls": 0,
    }
    blockers = [
        f"{key}_invalid"
        for key, expected in checks.items()
        if approval.get(key) != expected
    ]
    if not allow_real_provider_call:
        blockers.append("cli_allow_flag_missing")
    for field in ("approved_by", "approval_date", "credential_env_var"):
        if not approval.get(field):
            blockers.append(f"{field}_missing")
    credential_name = str(approval.get("credential_env_var") or "")
    if credential_name and not os.environ.get(credential_name):
        blockers.append("credential_missing")
    return blockers


def _usage_value(usage: Mapping[str, Any], field: str) -> int:
    return int(usage.get(field, 0) or 0)


def capture_repair_calls(
    config_path: Path, *, allow_real_provider_call: bool
) -> dict[str, Any]:
    execution_commit = clean_execution_commit()
    config = read_json(config_path)
    manifest_raw = read_json(ROOT / str(config["reports"]["call_manifest"]))
    manifest = verify_report_hash(
        ROOT / str(config["reports"]["call_manifest"]),
        str(manifest_raw["report_hash"]),
    )
    approval = read_json(ROOT / str(config["provider"]["approval_path"]))
    blockers = approval_blockers(
        config,
        approval,
        manifest,
        allow_real_provider_call=allow_real_provider_call,
    )
    if blockers:
        raise RepairProviderCaptureError(
            "TASK038B_PROVIDER_PREFLIGHT_BLOCKED:" + ",".join(blockers)
        )
    slots = sorted(manifest["slots"], key=lambda item: item["request_order"])
    if [item["request_order"] for item in slots] != list(
        range(1, len(slots) + 1)
    ):
        raise RepairProviderCaptureError("TASK038B_REQUEST_ORDER_INVALID")
    private_root = ROOT / str(config["private_root"])
    outcomes: list[dict[str, Any]] = []
    global_block = False
    for index, slot in enumerate(slots):
        base = {
            key: slot[key]
            for key in (
                "repair_call_slot_id",
                "initial_slot_id",
                "detector_variant",
                "kpi_id",
                "direction",
            )
        }
        if global_block:
            outcomes.append({**base, "capture_status": "not_attempted_global_block"})
            continue
        request_dir = private_root / "requests" / slot["repair_call_slot_id"]
        request = read_json(request_dir / "complete_request.json")
        if sha256_json(request) != slot["complete_request_hash"]:
            raise RepairProviderCaptureError("TASK038B_REQUEST_HASH_MISMATCH")
        receipt_path = private_root / "receipts" / f"{slot['repair_call_slot_id']}.json"
        if receipt_path.exists():
            raise RepairProviderCaptureError("TASK038B_SLOT_ALREADY_CONSUMED")
        write_json(
            receipt_path,
            {
                "repair_call_slot_id": slot["repair_call_slot_id"],
                "initial_slot_id": slot["initial_slot_id"],
                "request_hash": slot["complete_request_hash"],
                "provider": approval["provider"],
                "model": approval["model"],
                "call_budget_consumed": True,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        response_dir = private_root / "responses" / slot["repair_call_slot_id"]
        response_dir.mkdir(parents=True, exist_ok=True)
        try:
            result = call_once(
                request, approval, int(config["provider"]["timeout_seconds"])
            )
            provider_failed = (
                result["provider_error"] is not None
                or int(result["http_status_code"]) >= 400
            )
            write_json(
                response_dir
                / ("provider_error.json" if provider_failed else "raw_response.json"),
                result["raw_json"],
            )
            if provider_failed:
                capture_status = "provider_error"
                global_block = is_global_block(result)
            elif not result["raw_text"]:
                capture_status = "empty_visible_response"
            else:
                capture_status = "provider_response_captured"
                (response_dir / "raw_response.md").write_bytes(
                    result["raw_text"].encode("utf-8")
                )
            usage = result.get("usage") or {}
            outcomes.append(
                {
                    **base,
                    "capture_status": capture_status,
                    "http_status": int(result["http_status_code"]),
                    "provider_reported_model": result["model_reported"],
                    "response_hash": (
                        hashlib.sha256(result["raw_text"].encode()).hexdigest()
                        if result["raw_text"]
                        else None
                    ),
                    "visible_response_present": bool(result["raw_text"]),
                    "usage": usage,
                    "global_block": global_block,
                }
            )
        except json.JSONDecodeError:
            write_json(
                response_dir / "malformed_provider_payload.json",
                {"error_type": "JSONDecodeError"},
            )
            outcomes.append({**base, "capture_status": "malformed_provider_payload"})
        except (OSError, TimeoutError, urllib.error.URLError) as error:
            write_json(
                response_dir / "transport_error.json",
                {"error_type": type(error).__name__},
            )
            outcomes.append({**base, "capture_status": "transport_error"})
        if index + 1 < len(slots) and not global_block:
            time.sleep(float(config["provider"]["inter_call_delay_seconds"]))
    usage_records = [item.get("usage") or {} for item in outcomes]
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038B",
        "artifact_type": "repair_provider_report",
        "execution_commit": execution_commit,
        "authorized_call_count": len(slots),
        "calls_attempted": sum(
            item["capture_status"] != "not_attempted_global_block"
            for item in outcomes
        ),
        "responses_captured": sum(
            item["capture_status"] == "provider_response_captured"
            for item in outcomes
        ),
        "empty_visible_responses": sum(
            item["capture_status"] == "empty_visible_response" for item in outcomes
        ),
        "provider_errors": sum(
            item["capture_status"] == "provider_error" for item in outcomes
        ),
        "transport_errors": sum(
            item["capture_status"] == "transport_error" for item in outcomes
        ),
        "malformed_provider_payloads": sum(
            item["capture_status"] == "malformed_provider_payload"
            for item in outcomes
        ),
        "not_attempted_global_block": sum(
            item["capture_status"] == "not_attempted_global_block"
            for item in outcomes
        ),
        "input_tokens_total": sum(
            _usage_value(item, "input_tokens") for item in usage_records
        ),
        "cached_input_tokens_total": sum(
            int((item.get("input_tokens_details") or {}).get("cached_tokens", 0) or 0)
            for item in usage_records
        ),
        "output_tokens_total": sum(
            _usage_value(item, "output_tokens") for item in usage_records
        ),
        "reasoning_tokens_total": sum(
            int(
                (item.get("output_tokens_details") or {}).get(
                    "reasoning_tokens", 0
                )
                or 0
            )
            for item in usage_records
        ),
        "total_tokens": sum(
            _usage_value(item, "total_tokens") for item in usage_records
        ),
        "automatic_retries": 0,
        "manual_retries": 0,
        "replacement_calls": 0,
        "review_agent_calls": 0,
        "raw_responses_tracked": False,
        "slots": outcomes,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["provider"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038b_repair_execution.json",
    )
    parser.add_argument("--allow-real-provider-call", action="store_true")
    args = parser.parse_args()
    report = capture_repair_calls(
        (ROOT / args.config).resolve(),
        allow_real_provider_call=args.allow_real_provider_call,
    )
    print(
        json.dumps(
            {
                "authorized_call_count": report["authorized_call_count"],
                "calls_attempted": report["calls_attempted"],
                "responses_captured": report["responses_captured"],
                "provider_errors": report["provider_errors"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
