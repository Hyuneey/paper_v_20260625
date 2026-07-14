"""Run TASK-035AR rules and merge the balanced 200-slot cohort."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import read_json, sha256_json, write_json
from experiments.argos_reproduction.multi_rule_runtime import build_image, execute_slot, inspect_image, isolation_probe
from experiments.argos_reproduction.task035a_failure_taxonomy import verify_report_hash


def run_remediation_runtime(config_path: Path, *, build: bool = False) -> dict[str, Any]:
    config = read_json(config_path)
    static = verify_report_hash(ROOT / config["reports"]["static"])
    image = build_image(config) if build else inspect_image(config)
    isolation = isolation_probe(config, image["image_id"])
    if isolation["status"] != "passed":
        raise RuntimeError("TASK035AR_RUNTIME_ENVIRONMENT_FAILED")

    results: list[dict[str, Any]] = []
    for audit in static["slots"]:
        base = {key: audit[key] for key in ("slot_id", "kpi_id", "anchor_id", "replicate_id")}
        if audit.get("static_status") != "static_valid":
            results.append({**base, "terminal_status": audit["terminal_status"], "runtime_attempted": False})
            continue
        runtime = execute_slot(config, image, audit, audit["rule_sha256"])
        results.append({
            **base,
            "rule_sha256": audit["rule_sha256"],
            "terminal_status": runtime["runtime_status"],
            "runtime_attempted": True,
            **runtime,
        })

    failed_statuses = {"runtime_failed", "output_contract_failed"}
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-035AR",
        "artifact_type": "remediation_runtime_report",
        "image": image,
        "isolation": isolation,
        "terminal_slot_count": len(results),
        "runtime_executable_rules": sum(item["terminal_status"] == "executable_rule" for item in results),
        "runtime_failed": sum(item["terminal_status"] in failed_statuses for item in results),
        "output_contract_failed": sum(item["terminal_status"] == "output_contract_failed" for item in results),
        "slots": results,
        "labels_mounted": False,
        "performance_metrics_computed": False,
        "raw_outputs_tracked": False,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / config["reports"]["runtime"], report)
    return report


def _yield(response: int, extracted: int, executable: int) -> dict[str, float | int]:
    return {
        "response_count": response,
        "extraction_count": extracted,
        "executable_count": executable,
        "response_yield": response / 100,
        "extraction_yield": extracted / 100,
        "executable_yield": executable / 100,
    }


def evaluate_adequacy(summary: dict[str, Any], thresholds: dict[str, int]) -> str:
    if summary.get("remediation_requests_sent") != 100 or summary.get("remediation_retries") != 0:
        return "blocked_provider_global"
    if summary.get("total_registered_slots") != 200 or summary.get("terminal_slot_count") != 200:
        return "failed_runtime_environment"
    if summary.get("selected_kpi_count") != 10:
        return "insufficient_kpi_balance"
    if summary.get("anchor_count") != 50:
        return "insufficient_anchor_coverage"
    if summary["remediation_non_empty_responses"] < thresholds["minimum_remediation_non_empty_responses"]:
        return "insufficient_remediation_response_yield"
    if summary["remediation_executable_rules"] < thresholds["minimum_remediation_executable_rules"]:
        return "insufficient_remediation_rule_yield"
    if summary["cumulative_executable_rules"] < thresholds["minimum_cumulative_executable_rules"]:
        return "insufficient_combined_rule_yield"
    if (
        summary["minimum_cumulative_executable_per_kpi"] < thresholds["minimum_cumulative_executable_rules_per_kpi"]
        or summary["minimum_cumulative_distinct_per_kpi"] < thresholds["minimum_cumulative_distinct_rules_per_kpi"]
        or summary["kpis_with_at_least_10_executable"] < thresholds["minimum_kpis_with_at_least_10_executable_rules"]
    ):
        return "insufficient_kpi_balance"
    if summary["anchors_with_at_least_2_executable"] < thresholds["minimum_anchors_with_at_least_2_executable_rules"]:
        return "insufficient_anchor_coverage"
    return "passed_balanced_generation_cohort"


def merge_cohorts(config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_json(config_path)
    old = config["task035a"]
    old_provider = verify_report_hash(ROOT / old["provider_report"])
    old_static = verify_report_hash(ROOT / old["static_report"])
    old_runtime = verify_report_hash(ROOT / old["runtime_report"])
    old_adequacy = verify_report_hash(ROOT / old["adequacy_report"])
    new_provider = verify_report_hash(ROOT / config["reports"]["provider"])
    new_static = verify_report_hash(ROOT / config["reports"]["static"])
    new_runtime = verify_report_hash(ROOT / config["reports"]["runtime"])
    if old_adequacy["status"] != "insufficient_rule_yield":
        raise RuntimeError("TASK035AR_ORIGINAL_STATUS_CHANGED")

    old_static_by_slot = {item["slot_id"]: item for item in old_static["slots"]}
    new_static_by_slot = {item["slot_id"]: item for item in new_static["slots"]}
    old_provider_by_slot = {item["slot_id"]: item for item in old_provider["slots"]}
    new_provider_by_slot = {item["slot_id"]: item for item in new_provider["slots"]}
    anchors: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"old": [], "new": []})
    for item in old_runtime["slots"]:
        anchors[item["anchor_id"]]["old"].append(item)
    for item in new_runtime["slots"]:
        anchors[item["anchor_id"]]["new"].append(item)

    per_anchor: list[dict[str, Any]] = []
    kpi_records: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"old": [], "new": []})
    for anchor_id, groups in sorted(anchors.items()):
        all_runs = groups["old"] + groups["new"]
        kpi_id = all_runs[0]["kpi_id"]
        old_executable = [item for item in groups["old"] if item["terminal_status"] == "executable_rule"]
        new_executable = [item for item in groups["new"] if item["terminal_status"] == "executable_rule"]
        executable = old_executable + new_executable
        responses = [old_provider_by_slot[item["slot_id"]].get("response_sha256") for item in groups["old"]]
        responses += [new_provider_by_slot[item["slot_id"]].get("response_sha256") for item in groups["new"]]
        rules = [old_static_by_slot[item["slot_id"]].get("rule_sha256") for item in groups["old"]]
        rules += [new_static_by_slot[item["slot_id"]].get("rule_sha256") for item in groups["new"]]
        non_null_responses = [value for value in responses if value]
        non_null_rules = [value for value in rules if value]
        per_anchor.append({
            "anchor_id": anchor_id,
            "kpi_id": kpi_id,
            "original_executable_count": len(old_executable),
            "remediation_executable_count": len(new_executable),
            "cumulative_executable_count": len(executable),
            "cumulative_distinct_rule_hash_count": len({item["rule_sha256"] for item in executable}),
            "any_executable": len(executable) >= 1,
            "at_least_two_executable": len(executable) >= 2,
            "all_four_executable": len(executable) == 4,
            "response_hash_duplicate_count": len(non_null_responses) - len(set(non_null_responses)),
            "rule_hash_duplicate_count": len(non_null_rules) - len(set(non_null_rules)),
        })
        kpi_records[kpi_id]["old"].extend(old_executable)
        kpi_records[kpi_id]["new"].extend(new_executable)

    per_kpi: dict[str, dict[str, int]] = {}
    for kpi_id, groups in sorted(kpi_records.items()):
        combined = groups["old"] + groups["new"]
        per_kpi[kpi_id] = {
            "original_executable": len(groups["old"]),
            "remediation_executable": len(groups["new"]),
            "cumulative_executable": len(combined),
            "cumulative_distinct_rule_hashes": len({item["rule_sha256"] for item in combined}),
        }

    original = _yield(old_provider["responses_captured"], old_static["rules_extracted"], old_runtime["runtime_executable"])
    remediation = _yield(new_provider["non_empty_responses"], new_static["rules_extracted"], new_runtime["runtime_executable_rules"])
    remediation_counts = {
        "requests_sent": new_provider["requests_sent"],
        "non_empty_responses": new_provider["non_empty_responses"],
        "empty_visible_responses": new_provider["empty_visible_responses"],
        "rules_extracted": new_static["rules_extracted"],
        "static_valid_rules": new_static["static_valid"],
        "runtime_executable_rules": new_runtime["runtime_executable_rules"],
        "response_without_rule": sum(item.get("terminal_status") == "response_without_rule" for item in new_static["slots"]),
        "runtime_failed": new_runtime["runtime_failed"],
        "provider_errors": new_provider["provider_errors"],
        "transport_errors": new_provider["transport_errors"],
        "input_tokens_total": new_provider["input_tokens_total"],
        "output_tokens_total": new_provider["output_tokens_total"],
        "reasoning_tokens_total": new_provider["reasoning_tokens_total"],
    }
    combined_report = {
        "schema_version": "1.0",
        "task_id": "TASK-035AR",
        "artifact_type": "combined_generation_cohort",
        "task035a_status": "insufficient_rule_yield",
        "total_registered_slots": 200,
        "terminal_slots": len(old_runtime["slots"]) + len(new_runtime["slots"]),
        "original": original,
        "remediation": remediation,
        "remediation_counts": remediation_counts,
        "absolute_difference": {key: remediation[key] - original[key] for key in ("response_yield", "extraction_yield", "executable_yield")},
        "relative_difference": {key: (remediation[key] - original[key]) / original[key] if original[key] else None for key in ("response_yield", "extraction_yield", "executable_yield")},
        "per_kpi": per_kpi,
        "per_anchor": per_anchor,
        "performance_metrics_computed": False,
        "all_executable_rules_included": True,
    }
    combined_report["report_hash"] = sha256_json(combined_report)
    write_json(ROOT / config["reports"]["combined"], combined_report)

    summary = {
        "remediation_requests_sent": new_provider["requests_sent"],
        "remediation_retries": 0,
        "total_registered_slots": 200,
        "terminal_slot_count": combined_report["terminal_slots"],
        "selected_kpi_count": len(per_kpi),
        "anchor_count": len(per_anchor),
        "remediation_non_empty_responses": new_provider["non_empty_responses"],
        "remediation_executable_rules": new_runtime["runtime_executable_rules"],
        "cumulative_executable_rules": sum(item["cumulative_executable"] for item in per_kpi.values()),
        "minimum_cumulative_executable_per_kpi": min(item["cumulative_executable"] for item in per_kpi.values()),
        "minimum_cumulative_distinct_per_kpi": min(item["cumulative_distinct_rule_hashes"] for item in per_kpi.values()),
        "kpis_with_at_least_10_executable": sum(item["cumulative_executable"] >= 10 for item in per_kpi.values()),
        "anchors_with_at_least_2_executable": sum(item["at_least_two_executable"] for item in per_anchor),
    }
    status = evaluate_adequacy(summary, config["adequacy"])
    adequacy = {
        "schema_version": "1.0",
        "task_id": "TASK-035AR",
        "artifact_type": "balanced_cohort_adequacy",
        "status": status,
        "remediation_provider_errors": new_provider["provider_errors"],
        **summary,
        "thresholds": config["adequacy"],
        "task035b_authorized": status == "passed_balanced_generation_cohort",
        "test_values_parsed": False,
        "test_labels_parsed": False,
        "inner_selection_performed": False,
        "outer_validation_performed": False,
        "performance_metrics_computed": False,
    }
    adequacy["report_hash"] = sha256_json(adequacy)
    write_json(ROOT / config["reports"]["adequacy"], adequacy)
    return combined_report, adequacy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task035ar_output_budget_remediation.json")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    path = (ROOT / args.config).resolve()
    runtime = run_remediation_runtime(path, build=args.build)
    _, adequacy = merge_cohorts(path)
    print(json.dumps({
        "runtime_executable": runtime["runtime_executable_rules"],
        "cumulative_executable": adequacy["cumulative_executable_rules"],
        "status": adequacy["status"],
    }))
    return 0 if adequacy["status"] == "passed_balanced_generation_cohort" else 2


if __name__ == "__main__":
    raise SystemExit(main())
