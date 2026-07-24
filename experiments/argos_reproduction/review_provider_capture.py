"""Execute the frozen TASK-038C Review manifest once, receipt first."""

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
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)


class ReviewProviderCaptureError(RuntimeError):
    """Raised when Review provider execution is not exactly authorized."""


def clean_execution_commit() -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    if status.stdout.strip():
        raise ReviewProviderCaptureError("TASK038C_EXECUTION_WORKTREE_NOT_CLEAN")
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
    exact = int(manifest["review_required_count"])
    checks = {
        "approved": True,
        "provider": config["provider"]["provider"],
        "model": config["provider"]["model"],
        "maximum_requests": exact,
        "maximum_requests_upper_bound": 179,
        "maximum_requests_per_review_branch": 1,
        "maximum_input_tokens_per_call": 20000,
        "maximum_output_tokens_per_call": 6000,
        "maximum_total_declared_input_tokens": exact * 20000,
        "maximum_total_declared_output_tokens": exact * 6000,
        "temperature_parameter_sent": False,
        "provider_seed_sent": False,
        "automatic_retry": False,
        "manual_retry": False,
        "replacement_generation": False,
        "repair_agent_calls": 0,
        "detection_agent_calls": 0,
        "exact_count_frozen": True,
        "call_manifest_hash": manifest["report_hash"],
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
    credential = str(approval.get("credential_env_var") or "")
    if credential and not os.environ.get(credential):
        blockers.append("credential_missing")
    return blockers


def _usage_value(usage: Mapping[str, Any], field: str) -> int:
    return int(usage.get(field, 0) or 0)


def capture_review_calls(
    config_path: Path, *, allow_real_provider_call: bool
) -> dict[str, Any]:
    execution_commit = clean_execution_commit()
    config = read_json(config_path)
    manifest = verify_hashed_report(ROOT / str(config["reports"]["call_manifest"]))
    approval = read_json(ROOT / str(config["provider"]["approval_path"]))
    blockers = approval_blockers(
        config,
        approval,
        manifest,
        allow_real_provider_call=allow_real_provider_call,
    )
    if blockers:
        raise ReviewProviderCaptureError(
            "TASK038C_PROVIDER_PREFLIGHT_BLOCKED:" + ",".join(blockers)
        )
    slots = sorted(manifest["slots"], key=lambda row: row["request_order"])
    if [row["request_order"] for row in slots] != list(range(1, len(slots) + 1)):
        raise ReviewProviderCaptureError("TASK038C_REQUEST_ORDER_INVALID")
    private_root = ROOT / str(config["private_roots"]["task038c"])
    outcomes: list[dict[str, Any]] = []
    global_block = False
    for index, slot in enumerate(slots):
        base = {
            key: slot[key]
            for key in (
                "review_call_slot_id",
                "branch_id",
                "initial_slot_id",
                "detector_variant",
                "kpi_id",
                "direction",
                "parent_type",
                "parent_rule_hash",
            )
        }
        if global_block:
            outcomes.append({**base, "capture_status": "not_attempted_global_block"})
            continue
        request_path = (
            private_root
            / "requests"
            / slot["review_call_slot_id"]
            / "complete_request.json"
        )
        request = read_json(request_path)
        if sha256_json(request) != slot["prompt_payload_hash"]:
            raise ReviewProviderCaptureError("TASK038C_REQUEST_HASH_MISMATCH")
        receipt_path = (
            private_root / "receipts" / f"{slot['review_call_slot_id']}.json"
        )
        if receipt_path.exists():
            raise ReviewProviderCaptureError("TASK038C_SLOT_ALREADY_CONSUMED")
        write_json(
            receipt_path,
            {
                "review_call_slot_id": slot["review_call_slot_id"],
                "branch_id": slot["branch_id"],
                "initial_slot_id": slot["initial_slot_id"],
                "branch_request_hash": slot["branch_request_hash"],
                "provider": approval["provider"],
                "model": approval["model"],
                "call_budget_consumed": True,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        response_dir = (
            private_root / "responses" / slot["review_call_slot_id"]
        )
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
                    "usage": result.get("usage") or {},
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
    usages = [row.get("usage") or {} for row in outcomes]
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "review_provider_report",
        "execution_commit": execution_commit,
        "authorized_call_count": len(slots),
        "calls_attempted": sum(
            row["capture_status"] != "not_attempted_global_block"
            for row in outcomes
        ),
        "responses_captured": sum(
            row["capture_status"] == "provider_response_captured"
            for row in outcomes
        ),
        "empty_visible_responses": sum(
            row["capture_status"] == "empty_visible_response" for row in outcomes
        ),
        "provider_errors": sum(
            row["capture_status"] == "provider_error" for row in outcomes
        ),
        "transport_errors": sum(
            row["capture_status"] == "transport_error" for row in outcomes
        ),
        "malformed_provider_payloads": sum(
            row["capture_status"] == "malformed_provider_payload"
            for row in outcomes
        ),
        "input_tokens_total": sum(_usage_value(row, "input_tokens") for row in usages),
        "cached_input_tokens_total": sum(
            int((row.get("input_tokens_details") or {}).get("cached_tokens", 0) or 0)
            for row in usages
        ),
        "output_tokens_total": sum(
            _usage_value(row, "output_tokens") for row in usages
        ),
        "reasoning_tokens_total": sum(
            int(
                (row.get("output_tokens_details") or {}).get(
                    "reasoning_tokens", 0
                )
                or 0
            )
            for row in usages
        ),
        "total_tokens": sum(_usage_value(row, "total_tokens") for row in usages),
        "automatic_retries": 0,
        "manual_retries": 0,
        "replacement_calls": 0,
        "repair_agent_calls": 0,
        "detection_agent_calls": 0,
        "raw_responses_tracked": False,
        "slots": outcomes,
    }
    return write_hashed_report(ROOT / str(config["reports"]["provider"]), report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    parser.add_argument("--allow-real-provider-call", action="store_true")
    args = parser.parse_args()
    report = capture_review_calls(
        (ROOT / args.config).resolve(),
        allow_real_provider_call=args.allow_real_provider_call,
    )
    print(
        json.dumps(
            {
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
