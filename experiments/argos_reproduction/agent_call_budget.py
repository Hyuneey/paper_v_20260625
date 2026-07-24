"""Freeze the no-retry TASK-038A provider-call ceiling without making calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.agent_factorial_registry import (
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.agent_private_artifacts import (
    validate_tracked_payload,
)
from experiments.argos_reproduction.agent_validity_metrics import (
    future_metric_schema,
)
from experiments.argos_reproduction.expanded_kpi_cohort import read_json
from experiments.argos_reproduction.safe_repair_adapter import (
    REPAIR_PROMPT_SOURCE_SHA256,
    load_repair_system_prompt,
)
from experiments.argos_reproduction.safe_review_adapter import (
    REVIEW_PROMPT_SOURCE_SHA256,
    load_review_system_prompt,
)


class AgentCallBudgetError(RuntimeError):
    """Raised when provider ceilings do not match the frozen population."""


def build_call_budget(
    config: Mapping[str, Any],
    provider_policy: Mapping[str, Any],
    initial_registry: Mapping[str, Any],
    branch_registry: Mapping[str, Any],
) -> dict[str, Any]:
    failed = int(initial_registry["repair_population"])
    executable = int(initial_registry["initial_executable"])
    components = {
        "repair_unique": failed,
        "review_A2_ceiling": executable,
        "review_A3_initial_executable_ceiling": executable,
        "review_A3_repaired_ceiling": failed,
    }
    maximum = sum(components.values())
    if (
        failed != 13
        or executable != 83
        or branch_registry["branch_count"] != 384
        or maximum != int(provider_policy["maximum_unique_primary_study_calls"])
        or int(provider_policy["maximum_repair_calls"]) != failed
    ):
        raise AgentCallBudgetError("TASK038A_PROVIDER_BUDGET_POPULATION_MISMATCH")
    if any(
        bool(provider_policy[field])
        for field in (
            "automatic_retry",
            "manual_retry",
            "replacement_generation",
            "real_provider_execution_authorized",
        )
    ):
        raise AgentCallBudgetError("TASK038A_PROVIDER_POLICY_NOT_CLOSED")
    return {
        "schema_version": "1.0",
        "task_id": "TASK-038A",
        "artifact_type": "agent_provider_budget",
        "status": "frozen_not_authorized",
        "provider": provider_policy["provider"],
        "model": provider_policy["model"],
        "max_output_tokens": provider_policy["max_output_tokens"],
        "components": components,
        "maximum_unique_primary_study_calls": maximum,
        "exact_eligible_call_manifest_status": "deferred_until_task038b_or_task038c_pre_execution",
        "repair_reused_between_A1_and_A3": True,
        "automatic_retry": False,
        "manual_retry": False,
        "replacement_generation": False,
        "real_provider_execution_authorized": False,
        "real_provider_calls": 0,
        "initial_registry_hash": initial_registry["report_hash"],
        "branch_registry_hash": branch_registry["report_hash"],
        "outer_accessed": False,
        "sealed_test_accessed": False,
    }


def freeze_call_budget(config_path: Path, provider_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    provider = read_json(provider_path)
    initial = verify_hashed_report(
        ROOT / config["reports"]["initial_registry"],
        read_json(ROOT / config["reports"]["initial_registry"])["report_hash"],
    )
    branches = verify_hashed_report(
        ROOT / config["reports"]["branch_registry"],
        read_json(ROOT / config["reports"]["branch_registry"])["report_hash"],
    )
    report = build_call_budget(config, provider, initial, branches)
    return write_hashed_report(ROOT / config["reports"]["provider_budget"], report)


def freeze_protocol_report(config_path: Path, provider_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    provider = read_json(provider_path)
    initial = read_json(ROOT / config["reports"]["initial_registry"])
    branches = read_json(ROOT / config["reports"]["branch_registry"])
    budget = read_json(ROOT / config["reports"]["provider_budget"])
    repair_prompt = load_repair_system_prompt()
    review_prompt = load_review_system_prompt()
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038A",
        "artifact_type": "agent_factorial_protocol_freeze",
        "status": "passed_agent_factorial_protocol_freeze",
        "experiment_description": config["experiment_description"],
        "initial_rule_slots": initial["initial_rule_slots"],
        "branch_count": branches["branch_count"],
        "repair_population_frozen": initial["repair_population"],
        "review_population_policy_frozen": True,
        "provider_call_budget_frozen": True,
        "maximum_unique_primary_study_calls": budget[
            "maximum_unique_primary_study_calls"
        ],
        "repair_prompt_fidelity": {
            "verified": True,
            "source_sha256": REPAIR_PROMPT_SOURCE_SHA256,
            "system_prompt_sha256": hashlib.sha256(
                repair_prompt.encode("utf-8")
            ).hexdigest(),
        },
        "review_prompt_fidelity": {
            "verified": True,
            "source_sha256": REVIEW_PROMPT_SOURCE_SHA256,
            "system_prompt_sha256": hashlib.sha256(
                review_prompt.encode("utf-8")
            ).hexdigest(),
        },
        "branch_semantics": {
            "A0": "initial_rule_only",
            "A1": "one_repair_only_for_runtime_failure",
            "A2": "one_inner_review_only_for_executable_initial_rule",
            "A3": "shared_repair_then_one_inner_review",
            "repair_reused_between_A1_and_A3": True,
            "harmful_review_revert": False,
        },
        "future_full_aggregator_order": ["fp_correction", "fn_compensation"],
        "future_metric_schema": future_metric_schema(),
        "provider_policy": {
            "provider": provider["provider"],
            "model": provider["model"],
            "max_output_tokens": provider["max_output_tokens"],
            "automatic_retry": False,
            "manual_retry": False,
            "replacement_generation": False,
            "real_provider_execution_authorized": False,
        },
        "container_execution_only": True,
        "host_generated_code_execution": False,
        "inner_only_review": True,
        "outer_access": False,
        "sealed_test_access": False,
        "real_provider_calls": 0,
        "real_repair_execution": 0,
        "real_review_execution": 0,
        "detector_variant_selection": False,
        "initial_registry_hash": initial["report_hash"],
        "branch_registry_hash": branches["report_hash"],
        "provider_budget_hash": budget["report_hash"],
        "claim_boundary": (
            "Experimental and safety readiness only; RepairAgent, ReviewAgent, "
            "and ARGOS methodological effectiveness are not established."
        ),
    }
    validate_tracked_payload(report)
    return write_hashed_report(ROOT / config["reports"]["protocol_freeze"], report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038a_agent_factorial_protocol.json",
    )
    parser.add_argument(
        "--provider-policy",
        default="configs/argos_reproduction/task038a_agent_provider_policy.json",
    )
    args = parser.parse_args()
    report = freeze_call_budget(
        (ROOT / args.config).resolve(), (ROOT / args.provider_policy).resolve()
    )
    protocol = freeze_protocol_report(
        (ROOT / args.config).resolve(), (ROOT / args.provider_policy).resolve()
    )
    print(
        json.dumps(
            {
                "maximum_unique_primary_study_calls": report[
                    "maximum_unique_primary_study_calls"
                ],
                "real_provider_calls": report["real_provider_calls"],
                "protocol_status": protocol["status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
