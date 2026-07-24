"""Aggregate TASK-038B operability, usage, and completion status."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.repair_failure_replay import verify_report_hash


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    spread = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / total
            + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return max(0.0, center - spread), min(1.0, center + spread)


def _load_report(config: dict[str, Any], name: str) -> dict[str, Any]:
    path = ROOT / str(config["reports"][name])
    raw = read_json(path)
    return verify_report_hash(path, str(raw["report_hash"]))


def _mean(total: int, count: int) -> float:
    return total / count if count else 0.0


def _manifest_committed(execution_commit: str, report_path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{execution_commit}:{report_path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def build_operability_report(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    replay = _load_report(config, "failure_replay")
    manifest = _load_report(config, "call_manifest")
    provider = _load_report(config, "provider")
    static = _load_report(config, "static")
    runtime = _load_report(config, "runtime")
    branch = _load_report(config, "branch_update")
    drift = _load_report(config, "semantic_drift")
    repaired = int(runtime["repaired_executable_count"])
    denominator = 13
    reproducible = int(replay["reproducible_failure_count"])
    lower, upper = wilson_interval(repaired, denominator)
    primary_rate = repaired / denominator
    conditional_rate = repaired / reproducible if reproducible else 0.0
    terminal_records = runtime["records"]
    receipts = list(
        (ROOT / str(config["private_root"]) / "receipts").glob("REPAIR-*.json")
    )
    exact_manifest_committed = _manifest_committed(
        str(provider["execution_commit"]),
        str(config["reports"]["call_manifest"]),
    )
    if provider["not_attempted_global_block"]:
        task_status = "blocked_provider_global"
    elif len(receipts) != int(provider["authorized_call_count"]):
        task_status = "failed_receipt_contract"
    elif len(terminal_records) != denominator:
        task_status = "incomplete_repair_terminal_states"
    elif not branch["repair_reuse_preserved"]:
        task_status = "failed_branch_update"
    elif not exact_manifest_committed:
        task_status = "blocked_exact_call_manifest"
    else:
        task_status = "passed_repair_agent_operability_experiment"
    if repaired / denominator >= 0.5:
        classification = "substantial_operability_support"
    elif repaired:
        classification = "limited_operability_support"
    else:
        classification = "no_observed_operability_support"
    records_by_slot = {item["initial_slot_id"]: item for item in terminal_records}
    recovered = [
        item
        for item in terminal_records
        if item["terminal_status"] == "repaired_executable"
    ]
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038B",
        "artifact_type": "repair_operability_report",
        "status": task_status,
        "operability_classification": classification,
        "frozen_repair_population": denominator,
        "reproducible_failure_count": reproducible,
        "nonreproducible_failure_count": replay[
            "nonreproducible_failure_count"
        ],
        "authorized_call_count": manifest["authorized_call_count"],
        "calls_attempted": provider["calls_attempted"],
        "responses_captured": provider["responses_captured"],
        "rules_extracted": static["rules_extracted"],
        "static_valid_revisions": static["static_valid_revisions"],
        "repaired_executable_count": repaired,
        "deterministic_replay_count": runtime["deterministic_replay_count"],
        "primary_repair_recovery_rate": primary_rate,
        "conditional_repair_recovery_rate": conditional_rate,
        "primary_recovery_interval": {
            "method": "Wilson score interval",
            "confidence_level": 0.95,
            "lower": lower,
            "upper": upper,
            "formal_population_inference": False,
        },
        "target_failures_recovered": sum(
            item["initial_runtime_status"] == "target_runtime_failed"
            for item in recovered
        ),
        "contrast_failures_recovered": sum(
            item["initial_runtime_status"] == "contrast_runtime_failed"
            for item in recovered
        ),
        "output_contract_failures_recovered": sum(
            item["initial_runtime_status"] == "output_contract_failed"
            for item in recovered
        ),
        "FN_rules_recovered": sum(item["direction"] == "FN" for item in recovered),
        "FP_rules_recovered": sum(item["direction"] == "FP" for item in recovered),
        "LSTMADalpha_rules_recovered": sum(
            item["detector_variant"] == "LSTMADalpha" for item in recovered
        ),
        "LSTMADbeta_rules_recovered": sum(
            item["detector_variant"] == "LSTMADbeta" for item in recovered
        ),
        "usage": {
            "input_tokens_total": provider["input_tokens_total"],
            "cached_input_tokens_total": provider["cached_input_tokens_total"],
            "output_tokens_total": provider["output_tokens_total"],
            "reasoning_tokens_total": provider["reasoning_tokens_total"],
            "total_tokens": provider["total_tokens"],
            "mean_input_tokens_per_call": _mean(
                provider["input_tokens_total"], provider["calls_attempted"]
            ),
            "mean_output_tokens_per_call": _mean(
                provider["output_tokens_total"], provider["calls_attempted"]
            ),
            "mean_total_tokens_per_call": _mean(
                provider["total_tokens"], provider["calls_attempted"]
            ),
            "estimated_provider_cost": "not_computed_unfrozen_pricing",
        },
        "completion_gate": {
            "all_initial_failures_replayed": replay[
                "all_initial_failures_replayed"
            ],
            "exact_call_manifest_committed_before_calls": exact_manifest_committed,
            "every_authorized_call_has_one_receipt": len(receipts)
            == provider["authorized_call_count"],
            "every_authorized_call_has_one_terminal_outcome": len(
                provider["slots"]
            )
            == provider["authorized_call_count"],
            "every_initial_repair_candidate_has_one_terminal_status": len(
                records_by_slot
            )
            == denominator,
            "automatic_retries": provider["automatic_retries"],
            "manual_retries": provider["manual_retries"],
            "replacement_calls": provider["replacement_calls"],
            "ReviewAgent_calls": provider["review_agent_calls"],
            "host_generated_code_execution": runtime[
                "host_generated_code_execution"
            ],
            "inner_label_access": False,
            "outer_access": False,
            "sealed_test_access": False,
            "A1_A3_repair_reuse_preserved": branch["repair_reuse_preserved"],
            "raw_private_artifacts_tracked": False,
        },
        "semantic_drift_report_hash": drift["report_hash"],
        "branch_update_hash": branch["report_hash"],
        "effectiveness_scope": "repair_operability_only",
        "detection_performance_computed": False,
        "review_agent_evaluated": False,
        "fusion_evaluated": False,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["operability"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038b_repair_execution.json",
    )
    args = parser.parse_args()
    report = build_operability_report((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "status": report["status"],
                "repaired_executable_count": report["repaired_executable_count"],
                "primary_repair_recovery_rate": report[
                    "primary_repair_recovery_rate"
                ],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed_repair_agent_operability_experiment" else 2


if __name__ == "__main__":
    raise SystemExit(main())
