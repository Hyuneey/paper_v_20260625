"""Sequential, receipt-first, no-retry provider capture for TASK-035A."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any
import urllib.error
import urllib.request

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, read_json, sha256_json, write_json
from experiments.argos_reproduction.provider_capture import response_text_from_openai_response


GLOBAL_HTTP_CODES = {401, 403, 404, 429}
GLOBAL_ERROR_TOKENS = ("insufficient_quota", "billing", "model_not_found", "invalid_api_key", "permission")


class MultiProviderError(RuntimeError):
    pass


def approval_blockers(config: dict[str, Any], approval: dict[str, Any], allow: bool) -> list[str]:
    blockers: list[str] = []
    if not allow: blockers.append("cli_approval_flag_missing")
    if approval.get("approved") is not True: blockers.append("approval_not_true")
    if approval.get("provider") != config["provider"]["provider"]: blockers.append("provider_mismatch")
    if approval.get("model") != config["provider"]["model"]: blockers.append("model_mismatch")
    if approval.get("maximum_requests_sent") != config["design"]["total_slots"]: blockers.append("request_budget_mismatch")
    if approval.get("maximum_requests_per_slot") != 1: blockers.append("per_slot_budget_invalid")
    if approval.get("automatic_retry") is not False: blockers.append("retry_policy_invalid")
    if approval.get("maximum_input_tokens_per_call") != 20000: blockers.append("input_budget_invalid")
    if approval.get("maximum_output_tokens_per_call") != 2000: blockers.append("output_budget_invalid")
    if approval.get("maximum_total_declared_input_tokens") != 2000000: blockers.append("total_input_budget_invalid")
    if approval.get("maximum_total_declared_output_tokens") != 200000: blockers.append("total_output_budget_invalid")
    if approval.get("temperature_parameter_sent") is not False or approval.get("provider_seed_sent") is not False: blockers.append("sampling_policy_invalid")
    for field in ("approved_by", "approval_date", "credential_env_var"):
        if not approval.get(field): blockers.append(f"{field}_missing")
    if approval.get("credential_env_var") and not os.environ.get(approval["credential_env_var"]): blockers.append("credential_missing")
    return blockers


def _payload(request: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": approval["model"],
        "input": [{"role": message["role"], "content": [{"type": "input_text", "text": message["content"]}]} for message in request["messages"]],
        "max_output_tokens": approval["maximum_output_tokens_per_call"],
        "store": False,
    }


def call_once(request: dict[str, Any], approval: dict[str, Any], timeout: int) -> dict[str, Any]:
    body = json.dumps(_payload(request, approval)).encode("utf-8")
    http_request = urllib.request.Request(
        "https://api.openai.com/v1/responses", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.environ[approval['credential_env_var']]}"},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(http_request, timeout=timeout) as response:
            raw = response.read().decode("utf-8"); status = response.status
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace"); status = error.code
    parsed = json.loads(raw) if raw else {}
    return {
        "http_status_code": status, "duration_seconds": time.perf_counter() - started,
        "raw_json": parsed, "raw_text": response_text_from_openai_response(parsed),
        "request_id": parsed.get("id"), "model_reported": parsed.get("model"),
        "usage": parsed.get("usage") or {}, "provider_error": parsed.get("error"),
    }


def is_global_block(result: dict[str, Any]) -> bool:
    if result["http_status_code"] in GLOBAL_HTTP_CODES:
        return True
    serialized = json.dumps(result.get("provider_error") or {}).lower()
    return any(token in serialized for token in GLOBAL_ERROR_TOKENS)


def capture_slots(config_path: Path, *, allow_real_provider_call: bool) -> dict[str, Any]:
    config = read_json(config_path)
    approval_path = REPO_ROOT / config["provider"]["approval_path"]
    approval = read_json(approval_path)
    blockers = approval_blockers(config, approval, allow_real_provider_call)
    if blockers:
        raise MultiProviderError("TASK035A_PROVIDER_PREFLIGHT_BLOCKED:" + ",".join(blockers))
    manifest = read_json(REPO_ROOT / config["reports"]["requests"])
    if manifest["registered_slot_count"] != 100:
        raise MultiProviderError("TASK035A_SLOT_COUNT_INVALID")
    private_root = REPO_ROOT / config["private_root"]
    outcomes: list[dict[str, Any]] = []
    global_block = False
    for index, slot in enumerate(manifest["slots"]):
        if global_block:
            outcomes.append({**{key: slot[key] for key in ("slot_id", "kpi_id", "anchor_id", "replicate_id")}, "capture_status": "not_attempted_global_block"})
            continue
        request_path = private_root / "requests" / slot["slot_id"] / "complete_request.json"
        request = read_json(request_path)
        if sha256_json(request) != slot["complete_request_hash"]:
            raise MultiProviderError("TASK035A_REQUEST_HASH_MISMATCH")
        receipt_path = request_path.parent / "receipt.json"
        response_dir = private_root / "responses" / slot["slot_id"]
        if receipt_path.exists():
            raise MultiProviderError("TASK035A_SLOT_ALREADY_CONSUMED")
        write_json(receipt_path, {
            "slot_id": slot["slot_id"], "kpi_id": slot["kpi_id"], "anchor_id": slot["anchor_id"],
            "replicate_id": slot["replicate_id"], "request_sha256": slot["complete_request_hash"],
            "provider": approval["provider"], "model": approval["model"], "call_budget_consumed": True,
            "started_at": datetime.now(timezone.utc).isoformat(),
        })
        response_dir.mkdir(parents=True, exist_ok=True)
        try:
            result = call_once(request, approval, int(config["provider"]["timeout_seconds"]))
            write_json(response_dir / ("raw_response.json" if result["provider_error"] is None else "provider_error.json"), result["raw_json"])
            if result["provider_error"] is not None or result["http_status_code"] >= 400:
                capture_status = "provider_error"
                global_block = is_global_block(result)
            elif not result["raw_text"]:
                capture_status = "response_without_rule"
            else:
                capture_status = "provider_response_captured"
            outcome = {
                **{key: slot[key] for key in ("slot_id", "kpi_id", "anchor_id", "replicate_id")},
                "capture_status": capture_status, "http_status_code": result["http_status_code"],
                "response_sha256": hashlib.sha256(result["raw_text"].encode()).hexdigest() if result["raw_text"] else None,
                "provider_reported_model": result["model_reported"], "usage": result["usage"],
                "global_block": global_block,
            }
            if result["raw_text"]:
                (response_dir / "raw_response.md").write_text(result["raw_text"], encoding="utf-8")
        except (OSError, TimeoutError, urllib.error.URLError) as error:
            write_json(response_dir / "transport_error.json", {"error_type": type(error).__name__})
            outcome = {**{key: slot[key] for key in ("slot_id", "kpi_id", "anchor_id", "replicate_id")}, "capture_status": "transport_error"}
        outcomes.append(outcome)
        if index + 1 < len(manifest["slots"]) and not global_block:
            time.sleep(float(config["provider"]["inter_call_delay_seconds"]))
    usage = [item.get("usage", {}) for item in outcomes]
    report = {
        "schema_version": "1.0", "task_id": "TASK-035A", "artifact_type": "provider_report",
        "slots_registered": len(manifest["slots"]), "requests_sent": sum(item["capture_status"] != "not_attempted_global_block" for item in outcomes),
        "responses_captured": sum(item["capture_status"] == "provider_response_captured" for item in outcomes),
        "provider_errors": sum(item["capture_status"] == "provider_error" for item in outcomes),
        "transport_errors": sum(item["capture_status"] == "transport_error" for item in outcomes),
        "unattempted_after_global_block": sum(item["capture_status"] == "not_attempted_global_block" for item in outcomes),
        "input_tokens_total": sum(int(item.get("input_tokens", 0) or 0) for item in usage),
        "output_tokens_total": sum(int(item.get("output_tokens", 0) or 0) for item in usage),
        "reasoning_tokens_total": sum(int((item.get("output_tokens_details") or {}).get("reasoning_tokens", 0) or 0) for item in usage),
        "slots": outcomes, "automatic_retries": 0, "repair_review_calls": 0,
        "raw_responses_tracked": False,
    }
    report["report_hash"] = sha256_json(report)
    write_json(REPO_ROOT / config["reports"]["provider"], report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task035a_expanded_rule_cohort.json")
    parser.add_argument("--allow-real-provider-call", action="store_true")
    args = parser.parse_args()
    result = capture_slots((REPO_ROOT / args.config).resolve(), allow_real_provider_call=args.allow_real_provider_call)
    print(json.dumps({key: result[key] for key in ("requests_sent", "responses_captured", "provider_errors", "transport_errors")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
