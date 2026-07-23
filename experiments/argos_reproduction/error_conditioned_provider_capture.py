"""Receipt-first, no-retry provider capture for TASK-037D."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
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


class ErrorConditionedProviderError(RuntimeError):
    """Raised when provider authorization or one-shot lineage fails."""


def approval_blockers(
    config: Mapping[str, Any],
    approval: Mapping[str, Any],
    allow_real_provider_call: bool,
) -> list[str]:
    count = int(config["design"]["exact_frozen_slot_count"])
    checks = {
        "approved": True,
        "provider": config["provider"]["provider"],
        "model": config["provider"]["model"],
        "maximum_requests": count,
        "maximum_requests_upper_bound": 120,
        "maximum_requests_per_slot": 1,
        "maximum_input_tokens_per_call": 20000,
        "maximum_output_tokens_per_call": 6000,
        "maximum_total_declared_input_tokens": count * 20000,
        "maximum_total_declared_output_tokens": count * 6000,
        "automatic_retry": False,
        "manual_retry": False,
        "replacement_generation": False,
        "temperature_parameter_sent": False,
        "provider_seed_sent": False,
        "reasoning_parameter_added": False,
    }
    blockers = [
        f"{key}_invalid" for key, expected in checks.items() if approval.get(key) != expected
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


def capture_error_conditioned_slots(
    config_path: Path, *, allow_real_provider_call: bool
) -> dict[str, Any]:
    config = read_json(config_path)
    approval = read_json(ROOT / str(config["provider"]["approval_path"]))
    blockers = approval_blockers(config, approval, allow_real_provider_call)
    if blockers:
        raise ErrorConditionedProviderError(
            "TASK037D_PROVIDER_PREFLIGHT_BLOCKED:" + ",".join(blockers)
        )
    manifest = read_json(ROOT / str(config["reports"]["requests"]))
    expected = int(config["design"]["exact_frozen_slot_count"])
    if manifest["registered_slot_count"] != expected or len(manifest["slots"]) != expected:
        raise ErrorConditionedProviderError("TASK037D_SLOT_COUNT_INVALID")
    private_root = ROOT / str(config["private_root"])
    outcomes: list[dict[str, Any]] = []
    global_block = False
    for index, slot in enumerate(manifest["slots"]):
        base = {
            key: slot[key]
            for key in ("slot_id", "detector_variant", "kpi_id", "direction")
        }
        if global_block:
            outcomes.append({**base, "capture_status": "not_attempted_global_block"})
            continue
        request_path = private_root / "requests" / slot["slot_id"] / "complete_request.json"
        request = read_json(request_path)
        if sha256_json(request) != slot["complete_request_hash"]:
            raise ErrorConditionedProviderError("TASK037D_REQUEST_HASH_MISMATCH")
        receipt_path = request_path.parent / "receipt.json"
        if receipt_path.exists():
            raise ErrorConditionedProviderError("TASK037D_SLOT_ALREADY_CONSUMED")
        write_json(
            receipt_path,
            {
                "slot_id": slot["slot_id"],
                "request_hash": slot["complete_request_hash"],
                "provider": approval["provider"],
                "model": approval["model"],
                "call_budget_consumed": True,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        response_dir = private_root / "responses" / slot["slot_id"]
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
                status = "provider_error"
                global_block = is_global_block(result)
            elif not result["raw_text"]:
                status = "response_without_rule"
            else:
                status = "provider_response_captured"
                (response_dir / "raw_response.md").write_bytes(
                    result["raw_text"].encode("utf-8")
                )
            outcomes.append(
                {
                    **base,
                    "capture_status": status,
                    "http_status_code": result["http_status_code"],
                    "response_sha256": (
                        hashlib.sha256(result["raw_text"].encode()).hexdigest()
                        if result["raw_text"]
                        else None
                    ),
                    "provider_reported_model": result["model_reported"],
                    "usage": result["usage"],
                    "global_block": global_block,
                }
            )
        except (OSError, TimeoutError, urllib.error.URLError) as error:
            write_json(
                response_dir / "transport_error.json",
                {"error_type": type(error).__name__},
            )
            outcomes.append({**base, "capture_status": "transport_error"})
        if index + 1 < expected and not global_block:
            time.sleep(float(config["provider"]["inter_call_delay_seconds"]))
    usage = [item.get("usage", {}) for item in outcomes]
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-037D",
        "artifact_type": "error_conditioned_provider_report",
        "slots_registered": expected,
        "requests_sent": sum(
            item["capture_status"] != "not_attempted_global_block" for item in outcomes
        ),
        "responses_captured": sum(
            item["capture_status"] == "provider_response_captured" for item in outcomes
        ),
        "empty_visible_responses": sum(
            item["capture_status"] == "response_without_rule" for item in outcomes
        ),
        "provider_errors": sum(
            item["capture_status"] == "provider_error" for item in outcomes
        ),
        "transport_errors": sum(
            item["capture_status"] == "transport_error" for item in outcomes
        ),
        "unattempted_after_global_block": sum(
            item["capture_status"] == "not_attempted_global_block" for item in outcomes
        ),
        "input_tokens_total": sum(
            int(item.get("input_tokens", 0) or 0) for item in usage
        ),
        "output_tokens_total": sum(
            int(item.get("output_tokens", 0) or 0) for item in usage
        ),
        "reasoning_tokens_total": sum(
            int((item.get("output_tokens_details") or {}).get("reasoning_tokens", 0) or 0)
            for item in usage
        ),
        "slots": outcomes,
        "automatic_retries": 0,
        "manual_retries": 0,
        "replacement_calls": 0,
        "repair_review_calls": 0,
        "raw_responses_tracked": False,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["provider"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037d_error_conditioned_rules.json",
    )
    parser.add_argument("--allow-real-provider-call", action="store_true")
    args = parser.parse_args()
    report = capture_error_conditioned_slots(
        (ROOT / args.config).resolve(),
        allow_real_provider_call=args.allow_real_provider_call,
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "requests_sent",
                    "responses_captured",
                    "provider_errors",
                    "transport_errors",
                )
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
