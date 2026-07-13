"""TASK-026 one-shot real LLM capture gate.

The default configuration does not call a provider. API capture requires an
explicit approval artifact, populated budgets, credentials, and a CLI flag.
Manual capture reads exactly one user-provided private response file. Captured
Python is never executed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.argos_reproduction import prompt_capture, rule_static_analysis


TASK026_STATEMENT = (
    "This is a one-shot ARGOS real-LLM response capture protocol. It evaluates "
    "response format and static rule structure only; it is not a benchmark "
    "result and must not be used as a thesis performance claim."
)


def _task_id(config: dict[str, Any]) -> str:
    return str(config.get("task_id", "TASK-026"))


def _artifact_type(config: dict[str, Any], suffix: str) -> str:
    namespace = str(config.get("artifact_namespace", "task026"))
    return f"{namespace}_{suffix}"


def _report_statement(config: dict[str, Any]) -> str:
    return str(config.get("report_statement", TASK026_STATEMENT))


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    prompt_capture.write_json(path, data)


def write_text(path: Path, text: str) -> None:
    prompt_capture.write_text(path, text)


def _relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def _provider_call_receipt_path(config: dict[str, Any], private_root: Path) -> Path:
    configured_path = config.get("provider_call_receipt_path")
    path = REPO_ROOT / configured_path if configured_path else private_root / "metadata" / "provider_call_receipt.json"
    prompt_capture.assert_private_artifact_path(path)
    return path


def _write_provider_call_receipt(
    path: Path,
    *,
    config: dict[str, Any],
    approval: dict[str, Any],
    request_hash: str,
    status: str,
    provider_result: dict[str, Any] | None = None,
) -> None:
    receipt = {
        "schema_version": "1.0",
        "artifact_type": _artifact_type(config, "provider_call_receipt"),
        "task_id": _task_id(config),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision_id": approval.get("decision_id"),
        "approval_hash": prompt_capture.sha256_json(approval),
        "request_hash": request_hash,
        "provider": approval.get("provider"),
        "model": approval.get("model"),
        "temperature_parameter_sent": approval.get("temperature") is not None,
        "max_calls": approval.get("max_calls"),
        "request_count": 0,
    }
    if provider_result is not None:
        receipt.update(
            {
                "http_status_code": provider_result.get("http_status_code"),
                "request_id": provider_result.get("request_id"),
                "request_count": provider_result.get("request_count", 0),
                "response_hash": prompt_capture.sha256_text(provider_result.get("raw_text", "")),
                "provider_error_present": provider_result.get("provider_error") is not None,
            }
        )
    write_json(path, receipt)


def approval_blockers(approval: dict[str, Any], allow_real_provider_call: bool) -> list[str]:
    blockers: list[str] = []
    required = [
        "provider",
        "model",
        "model_version_identifier",
        "max_calls",
        "max_input_tokens",
        "max_output_tokens",
        "max_cost_usd",
        "credential_env_vars",
        "prompt_response_retention",
        "approved_by",
        "approval_date",
    ]
    if approval.get("approved") is not True:
        blockers.append("approval_not_true")
    if approval.get("decision_status") != "resolved":
        blockers.append("dec028_not_resolved")
    if approval.get("provider") not in {"openai_responses"}:
        blockers.append("provider_not_supported_by_task026_api_client")
    if "temperature" not in approval:
        blockers.append("temperature_missing")
    if not allow_real_provider_call:
        blockers.append("cli_allow_real_provider_call_missing")
    for field in required:
        value = approval.get(field)
        if value is None or value == "" or value == []:
            blockers.append(f"{field}_missing")
    if approval.get("max_calls") != 1:
        blockers.append("max_calls_not_exactly_one")
    for name in approval.get("credential_env_vars", []) or []:
        if not os.environ.get(name):
            blockers.append(f"credential_missing:{name}")
    return blockers


def load_private_request(config: dict[str, Any]) -> tuple[dict[str, Any], str]:
    task025_report = read_json(REPO_ROOT / config["task025_capture_report_path"])
    request_path = REPO_ROOT / task025_report["private_artifacts"]["complete_request_path"]
    prompt_capture.assert_private_artifact_path(request_path)
    request = read_json(request_path)
    request_hash = prompt_capture.sha256_json(request)
    expected_hash = config["frozen_inputs"]["complete_request_hash"]
    if request_hash != expected_hash:
        raise ValueError(f"Frozen request hash mismatch: {request_hash} != {expected_hash}")
    return request, request_hash


def response_text_from_openai_response(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str) and response["output_text"]:
        return response["output_text"]
    texts: list[str] = []
    for item in response.get("output", []) or []:
        for content in item.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str):
                texts.append(text)
    return "\n".join(texts)


def _to_openai_responses_input(messages: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "role": message["role"],
            "content": [{"type": "input_text", "text": message["content"]}],
        }
        for message in messages
    ]


def call_openai_responses_once(
    request: dict[str, Any],
    approval: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    credential_name = approval["credential_env_vars"][0]
    api_key = os.environ[credential_name]
    payload = {
        "model": approval["model"],
        "input": _to_openai_responses_input(request["messages"]),
        "max_output_tokens": approval["max_output_tokens"],
        "store": False,
    }
    if approval.get("temperature") is not None:
        payload["temperature"] = approval["temperature"]
    body = json.dumps(payload).encode("utf-8")
    http_request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(http_request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            status_code = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status_code = exc.code
    duration = time.perf_counter() - start
    parsed = json.loads(raw) if raw else {}
    return {
        "raw_json": parsed,
        "raw_text": response_text_from_openai_response(parsed),
        "provider_request_payload_hash": prompt_capture.sha256_json(
            {
                key: value
                for key, value in payload.items()
                if key != "input"
            }
        ),
        "http_status_code": status_code,
        "duration_seconds": duration,
        "request_count": 1,
        "request_id": parsed.get("id"),
        "usage": parsed.get("usage"),
        "model_reported": parsed.get("model"),
        "provider_error": parsed.get("error"),
    }


def _persist_provider_result(
    private_root: Path,
    provider_result: dict[str, Any],
    approval: dict[str, Any],
    capture_type: str,
) -> dict[str, str]:
    response_dir = private_root / "responses"
    metadata_dir = private_root / "metadata"
    response_path = response_dir / "raw_response.md"
    metadata_path = metadata_dir / "provider_response_metadata.json"
    write_text(response_path, provider_result.get("raw_text", ""))
    if provider_result.get("raw_json") is not None:
        write_json(response_dir / "raw_response.json", provider_result["raw_json"])
    write_json(
        metadata_path,
        {
            "capture_type": capture_type,
            "provider": approval.get("provider"),
            "model": approval.get("model") or provider_result.get("model_reported"),
            "request_id": provider_result.get("request_id"),
            "usage": provider_result.get("usage"),
            "http_status_code": provider_result.get("http_status_code"),
            "duration_seconds": provider_result.get("duration_seconds"),
            "request_count": provider_result.get("request_count", 0),
            "provider_error_present": provider_result.get("provider_error") is not None,
        },
    )
    return {
        "raw_response_path": _relative(response_path),
        "metadata_path": _relative(metadata_path),
    }


def load_manual_capture(config: dict[str, Any]) -> dict[str, Any] | None:
    manual_path = REPO_ROOT / config["manual_capture"]["response_path"]
    prompt_capture.assert_private_artifact_path(manual_path)
    if not manual_path.exists():
        return None
    metadata_path = REPO_ROOT / config["manual_capture"].get(
        "metadata_path",
        "artifacts/private_argos_reproduction/task026/manual_response_metadata.json",
    )
    metadata = {}
    if metadata_path.exists():
        metadata = read_json(metadata_path)
    return {
        "raw_text": manual_path.read_text(encoding="utf-8"),
        "raw_json": None,
        "metadata": metadata,
        "request_count": 0,
        "capture_type": "manual_exploratory_capture",
        "request_id": metadata.get("request_id"),
        "usage": metadata.get("usage"),
        "model_reported": metadata.get("model"),
    }


def pending_reports(config: dict[str, Any], request_hash: str, reason: str, blockers: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    report = {
        "schema_version": "1.0",
        "artifact_type": _artifact_type(config, "real_llm_capture_report"),
        "task_id": _task_id(config),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "statement": _report_statement(config),
        "frozen_inputs": config["frozen_inputs"],
        "capture_status": "not_captured_pending_approval_or_manual_response",
        "pending_reason": reason,
        "blockers": blockers,
        "request_hash": request_hash,
        "response_hash": None,
        "rule_hash": None,
        "provider_metadata": {
            "capture_mode": config["capture_mode"],
            "request_count": 0,
            "real_provider_call_performed": False,
            "manual_capture_performed": False,
        },
        "execution_performed": False,
        "generated_python_executed": False,
        "performance_metric_reported": False,
        "retry_count": 0,
        "response_driven_prompt_tuning": False,
        "raw_prompt_tracked": False,
        "raw_response_tracked": False,
        "boundaries": config.get("boundaries", {}),
    }
    static_report = {
        "schema_version": "1.0",
        "artifact_type": _artifact_type(config, "rule_static_analysis"),
        "task_id": _task_id(config),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "not_available_no_response_captured",
        "statement": _report_statement(config),
        "execution_performed": False,
        "performance_metric_reported": False,
    }
    return report, static_report


def run_capture(config_path: Path, allow_real_provider_call: bool = False) -> dict[str, Any]:
    config = read_json(config_path)
    approval = read_json(REPO_ROOT / config["approval_path"])
    request, request_hash = load_private_request(config)
    private_root = REPO_ROOT / config["private_artifact_root"]
    prompt_capture.assert_private_artifact_path(private_root)

    capture_mode = config["capture_mode"]
    if capture_mode not in {"manual_capture", "api_capture"}:
        raise ValueError(f"Unsupported capture_mode: {capture_mode}")

    provider_result: dict[str, Any] | None = None
    blockers: list[str] = []
    if capture_mode == "api_capture":
        blockers = approval_blockers(approval, allow_real_provider_call)
        receipt_path = _provider_call_receipt_path(config, private_root)
        if receipt_path.exists():
            blockers.append("provider_call_already_attempted")
        if blockers:
            capture_report, static_report = pending_reports(
                config, request_hash, "api_capture_not_approved", blockers
            )
            write_json(REPO_ROOT / config["output_capture_report_path"], capture_report)
            write_json(REPO_ROOT / config["output_static_analysis_path"], static_report)
            return {"capture_report": capture_report, "static_report": static_report}
        _write_provider_call_receipt(
            receipt_path,
            config=config,
            approval=approval,
            request_hash=request_hash,
            status="started",
        )
        try:
            provider_result = call_openai_responses_once(
                request,
                approval,
                int(config.get("request_timeout_seconds", 120)),
            )
        except Exception:
            _write_provider_call_receipt(
                receipt_path,
                config=config,
                approval=approval,
                request_hash=request_hash,
                status="transport_exception",
            )
            raise
        _write_provider_call_receipt(
            receipt_path,
            config=config,
            approval=approval,
            request_hash=request_hash,
            status="completed",
            provider_result=provider_result,
        )
        capture_type = "approved_api_capture"
        real_provider_call_performed = True
        manual_capture_performed = False
        provider_error = provider_result.get("provider_error")
        status_code = int(provider_result.get("http_status_code") or 0)
        if status_code >= 400 or provider_error is not None or not provider_result.get("raw_text"):
            private_paths = _persist_provider_result(private_root, provider_result, approval, capture_type)
            raw_response_hash = prompt_capture.sha256_text(provider_result.get("raw_text", ""))
            capture_report = {
                "schema_version": "1.0",
                "artifact_type": _artifact_type(config, "real_llm_capture_report"),
                "task_id": _task_id(config),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "statement": _report_statement(config),
                "frozen_inputs": config["frozen_inputs"],
                "capture_status": "provider_error_no_rule_response",
                "capture_type": capture_type,
                "request_hash": request_hash,
                "response_hash": raw_response_hash,
                "rule_hash": None,
                "code_extraction_status": "not_attempted_provider_error_or_empty_response",
                "provider_metadata": {
                    "provider": approval.get("provider"),
                    "model": approval.get("model") or provider_result.get("model_reported"),
                    "model_version_identifier": approval.get("model_version_identifier"),
                    "temperature": approval.get("temperature"),
                    "request_count": provider_result.get("request_count", 0),
                    "max_calls": approval.get("max_calls"),
                    "token_usage": provider_result.get("usage"),
                    "cost_total_usd": provider_result.get("cost_total_usd"),
                    "request_id": provider_result.get("request_id"),
                    "http_status_code": provider_result.get("http_status_code"),
                    "provider_error_type": provider_error.get("type") if isinstance(provider_error, dict) else None,
                    "provider_error_code": provider_error.get("code") if isinstance(provider_error, dict) else None,
                    "provider_error_message": provider_error.get("message") if isinstance(provider_error, dict) else None,
                    "real_provider_call_performed": True,
                    "manual_capture_performed": False,
                },
                "private_artifacts": {
                    **private_paths,
                    "quarantined_rule_path": None,
                },
                "static_validation_summary": {
                    "analysis_status": "not_available_provider_error_or_empty_response",
                    "execution_performed": False,
                    "required_signature_status": "not_available",
                    "static_safety_passed": False,
                    "syntax_parse_status": "not_parsed",
                },
                "raw_prompt_tracked": False,
                "raw_response_tracked": False,
                "generated_python_executed": False,
                "performance_metric_reported": False,
                "retry_count": 0,
                "response_driven_prompt_tuning": False,
                "boundaries": config["boundaries"],
            }
            static_report = {
                "schema_version": "1.0",
                "artifact_type": _artifact_type(config, "rule_static_analysis"),
                "task_id": _task_id(config),
                "created_at": capture_report["created_at"],
                "statement": _report_statement(config),
                "analysis_status": "not_available_provider_error_or_empty_response",
                "response_hash": raw_response_hash,
                "rule_hash": None,
                "execution_performed": False,
                "performance_metric_reported": False,
                "structural_diagnostics_only": True,
            }
            capture_report["report_hash"] = prompt_capture.sha256_json(capture_report)
            static_report["report_hash"] = prompt_capture.sha256_json(static_report)
            write_json(REPO_ROOT / config["output_capture_report_path"], capture_report)
            write_json(REPO_ROOT / config["output_static_analysis_path"], static_report)
            return {"capture_report": capture_report, "static_report": static_report}
    else:
        provider_result = load_manual_capture(config)
        if provider_result is None:
            capture_report, static_report = pending_reports(
                config,
                request_hash,
                "manual_response_file_missing",
                [f"manual_response_missing:{config['manual_capture']['response_path']}"],
            )
            write_json(REPO_ROOT / config["output_capture_report_path"], capture_report)
            write_json(REPO_ROOT / config["output_static_analysis_path"], static_report)
            return {"capture_report": capture_report, "static_report": static_report}
        capture_type = "manual_exploratory_capture"
        real_provider_call_performed = False
        manual_capture_performed = True

    raw_response_text = provider_result["raw_text"]
    raw_response_hash = prompt_capture.sha256_text(raw_response_text)
    rule_code = ""
    rule_hash = None
    extraction_status = "not_extracted"
    try:
        rule_code = rule_static_analysis.extract_first_code_fence(raw_response_text)
        rule_hash = prompt_capture.sha256_text(rule_code)
        extraction_status = "code_extracted"
    except Exception as exc:
        extraction_status = f"code_extraction_failed:{exc}"

    quarantine_dir = private_root / "quarantine"
    private_paths = _persist_provider_result(private_root, provider_result, approval, capture_type)
    if rule_code:
        write_text(quarantine_dir / f"{rule_hash}.py", rule_code)

    static_analysis = rule_static_analysis.analyze_response(
        raw_response_text,
        set(config.get("allowed_imports", ["numpy"])),
    )
    static_report = {
        "schema_version": "1.0",
        "artifact_type": _artifact_type(config, "rule_static_analysis"),
        "task_id": _task_id(config),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "statement": _report_statement(config),
        "analysis_status": "completed",
        "response_hash": raw_response_hash,
        "rule_hash": rule_hash,
        "analysis": static_analysis,
        "execution_performed": False,
        "performance_metric_reported": False,
        "structural_diagnostics_only": True,
    }
    capture_report = {
        "schema_version": "1.0",
        "artifact_type": _artifact_type(config, "real_llm_capture_report"),
        "task_id": _task_id(config),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "statement": _report_statement(config),
        "frozen_inputs": config["frozen_inputs"],
        "capture_status": "captured",
        "capture_type": capture_type,
        "request_hash": request_hash,
        "response_hash": raw_response_hash,
        "rule_hash": rule_hash,
        "code_extraction_status": extraction_status,
        "provider_metadata": {
            "provider": approval.get("provider"),
            "model": approval.get("model") or provider_result.get("model_reported"),
            "model_version_identifier": approval.get("model_version_identifier"),
            "temperature": approval.get("temperature"),
            "request_count": provider_result.get("request_count", 0),
            "max_calls": approval.get("max_calls"),
            "token_usage": provider_result.get("usage"),
            "cost_total_usd": provider_result.get("cost_total_usd"),
            "request_id": provider_result.get("request_id"),
            "real_provider_call_performed": real_provider_call_performed,
            "manual_capture_performed": manual_capture_performed,
        },
        "private_artifacts": {
            "raw_response_path": private_paths["raw_response_path"],
            "metadata_path": private_paths["metadata_path"],
            "quarantined_rule_path": _relative(quarantine_dir / f"{rule_hash}.py") if rule_hash else None,
        },
        "static_validation_summary": {
            "analysis_status": static_report["analysis_status"],
            "syntax_parse_status": static_analysis.get("syntax_parse_status"),
            "required_signature_status": static_analysis.get("required_signature_status"),
            "static_safety_passed": static_analysis.get("static_safety_passed"),
            "execution_performed": False,
        },
        "raw_prompt_tracked": False,
        "raw_response_tracked": False,
        "generated_python_executed": False,
        "performance_metric_reported": False,
        "retry_count": 0,
        "response_driven_prompt_tuning": False,
        "boundaries": config["boundaries"],
    }
    capture_report["report_hash"] = prompt_capture.sha256_json(capture_report)
    static_report["report_hash"] = prompt_capture.sha256_json(static_report)
    write_json(REPO_ROOT / config["output_capture_report_path"], capture_report)
    write_json(REPO_ROOT / config["output_static_analysis_path"], static_report)
    return {"capture_report": capture_report, "static_report": static_report}


def main() -> int:
    parser = argparse.ArgumentParser(description="TASK-026 one-shot LLM response capture")
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task026_real_capture.json",
        help="Path to TASK-026 capture config JSON.",
    )
    parser.add_argument(
        "--allow-real-provider-call",
        action="store_true",
        help="Allow an approved one-shot provider call. Requires approved artifact and credentials.",
    )
    args = parser.parse_args()
    result = run_capture((REPO_ROOT / args.config).resolve(), args.allow_real_provider_call)
    report = result["capture_report"]
    print(
        json.dumps(
            {
                "capture_status": report["capture_status"],
                "capture_type": report.get("capture_type"),
                "request_hash": report["request_hash"],
                "response_hash": report.get("response_hash"),
                "generated_python_executed": report.get("generated_python_executed", False),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
