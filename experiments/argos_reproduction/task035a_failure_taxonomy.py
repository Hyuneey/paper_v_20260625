"""Aggregate-only taxonomy for non-executable TASK-035A slots."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import read_json, sha256_json, write_json
from experiments.argos_reproduction.multi_rule_static_audit import extract_python_fence


class FailureTaxonomyError(RuntimeError):
    pass


def verify_report_hash(path: Path) -> dict[str, Any]:
    report = read_json(path)
    expected = report.get("report_hash")
    subject = dict(report); subject.pop("report_hash", None)
    if expected != sha256_json(subject):
        raise FailureTaxonomyError("TASK035AR_REPORT_HASH_MISMATCH")
    return report


def git_clean_commit() -> str:
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise FailureTaxonomyError("TASK035AR_EXECUTION_WORKTREE_NOT_CLEAN")
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def classify_failure(*, provider: dict[str, Any], static: dict[str, Any], runtime: dict[str, Any], response_text: str | None) -> str:
    if runtime["terminal_status"] == "runtime_failed":
        return "runtime_timeout" if runtime.get("timed_out") else "runtime_exception"
    if runtime["terminal_status"] == "output_contract_failed":
        if runtime.get("output_shape_valid") is False:
            return "runtime_shape_failure"
        if runtime.get("output_binary_domain_valid") is False or runtime.get("output_finite") is False:
            return "runtime_domain_failure"
        return "unknown_sanitized"
    if provider["capture_status"] == "response_without_rule" or not response_text:
        return "no_visible_output"
    code, fence_count = extract_python_fence(response_text)
    if code is None and "```python" in response_text.lower():
        return "visible_output_incomplete_python_fence"
    if fence_count == 0:
        return "visible_output_no_python_fence"
    if fence_count > 1:
        return "visible_output_multiple_python_fences"
    if code is None:
        return "visible_output_incomplete_python_fence"
    if static.get("inference_definition_count", 0) != 1:
        return "visible_output_no_inference"
    if static.get("static_status") == "static_invalid":
        return "extracted_static_invalid"
    return "unknown_sanitized"


def _token_summary(values: list[int]) -> dict[str, int | None]:
    if not values:
        return {"count": 0, "minimum": None, "maximum": None, "total": 0}
    return {"count": len(values), "minimum": min(values), "maximum": max(values), "total": sum(values)}


def build_taxonomy(config_path: Path, *, require_clean: bool = True) -> dict[str, Any]:
    config = read_json(config_path)
    commit = git_clean_commit() if require_clean else subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    old = config["task035a"]
    provider_report = verify_report_hash(ROOT / old["provider_report"])
    static_report = verify_report_hash(ROOT / old["static_report"])
    runtime_report = verify_report_hash(ROOT / old["runtime_report"])
    adequacy_report = verify_report_hash(ROOT / old["adequacy_report"])
    if adequacy_report["status"] != "insufficient_rule_yield":
        raise FailureTaxonomyError("TASK035AR_ORIGINAL_STATUS_CHANGED")
    provider_by = {item["slot_id"]: item for item in provider_report["slots"]}
    static_by = {item["slot_id"]: item for item in static_report["slots"]}
    categories: dict[str, dict[str, Any]] = defaultdict(lambda: {"slot_count": 0, "per_kpi_count": defaultdict(int), "output_tokens": [], "reasoning_tokens": []})
    original_private = ROOT / old["private_root"]
    failed = [item for item in runtime_report["slots"] if item["terminal_status"] != "executable_rule"]
    empty_slots = [item for item in provider_report["slots"] if item["capture_status"] == "response_without_rule"]
    exhausted = [
        item for item in empty_slots
        if int((item.get("usage") or {}).get("output_tokens", 0) or 0) == 2000
        and int(((item.get("usage") or {}).get("output_tokens_details") or {}).get("reasoning_tokens", 0) or 0) == 2000
    ]
    if (provider_report["responses_captured"], static_report["rules_extracted"], runtime_report["runtime_executable"], len(failed), len(empty_slots), len(exhausted)) != (84, 61, 55, 45, 16, 16):
        raise FailureTaxonomyError("TASK035AR_FROZEN_DIAGNOSIS_MISMATCH")
    for runtime in failed:
        provider = provider_by[runtime["slot_id"]]; static = static_by[runtime["slot_id"]]
        response_path = original_private / "responses" / runtime["slot_id"] / "raw_response.md"
        response_text = response_path.read_text(encoding="utf-8") if response_path.is_file() else None
        category = classify_failure(provider=provider, static=static, runtime=runtime, response_text=response_text)
        item = categories[category]; item["slot_count"] += 1; item["per_kpi_count"][runtime["kpi_id"]] += 1
        usage = provider.get("usage") or {}; item["output_tokens"].append(int(usage.get("output_tokens", 0) or 0)); item["reasoning_tokens"].append(int((usage.get("output_tokens_details") or {}).get("reasoning_tokens", 0) or 0))
    records = []
    for category, item in sorted(categories.items()):
        records.append({"category": category, "slot_count": item["slot_count"], "per_kpi_count": dict(sorted(item["per_kpi_count"].items())), "output_token_count_summary": _token_summary(item["output_tokens"]), "reasoning_token_count_summary": _token_summary(item["reasoning_tokens"])})
    report = {
        "schema_version": "1.0", "task_id": "TASK-035AR", "artifact_type": "task035a_failure_taxonomy",
        "execution_code_commit": commit, "task035a_status_preserved": "insufficient_rule_yield",
        "registered_slots": 100, "http_or_provider_errors": provider_report["provider_errors"],
        "non_empty_responses": provider_report["responses_captured"], "empty_visible_responses": 100 - provider_report["responses_captured"],
        "rules_extracted": static_report["rules_extracted"], "runtime_executable": runtime_report["runtime_executable"],
        "non_executable_slot_count": len(failed), "categories": records,
        "primary_diagnosis": "max_output_tokens_2000_consumed_by_reasoning_with_no_visible_response",
        "primary_diagnosis_matching_slots": len(exhausted),
        "performance_data_inspected": False, "raw_content_tracked": False, "private_paths_tracked": False,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / config["reports"]["taxonomy"], report)
    write_json(ROOT / config["private_root"] / "execution_receipt.json", {"execution_code_commit": commit, "task035a_result_report_sha256": hashlib.sha256((ROOT / old["adequacy_report"]).read_bytes()).hexdigest()})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--config", default="configs/argos_reproduction/task035ar_output_budget_remediation.json"); parser.add_argument("--allow-dirty-for-tests", action="store_true"); args = parser.parse_args()
    report = build_taxonomy((ROOT / args.config).resolve(), require_clean=not args.allow_dirty_for_tests)
    print(json.dumps({"non_executable_slot_count": report["non_executable_slot_count"], "category_count": len(report["categories"])})); return 0


if __name__ == "__main__": raise SystemExit(main())
