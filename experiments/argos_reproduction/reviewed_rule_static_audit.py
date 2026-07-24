"""Apply the frozen generated-rule static policy to Review revisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import read_json, write_json
from experiments.argos_reproduction.multi_rule_static_audit import audit_response
from experiments.argos_reproduction.review_parent_registry import (
    verify_hashed_report,
    write_hashed_report,
)
from experiments.argos_reproduction.reviewed_rule_extraction import (
    extract_reviewed_rules,
)


def _provider_terminal(status: str) -> str:
    return {
        "provider_error": "reviewed_provider_error",
        "transport_error": "reviewed_transport_error",
        "empty_visible_response": "reviewed_empty_response",
        "not_attempted_global_block": "not_attempted_global_block",
        "malformed_provider_payload": "reviewed_provider_error",
    }.get(status, "reviewed_response_without_rule")


def audit_reviewed_rules(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    provider = verify_hashed_report(ROOT / str(config["reports"]["provider"]))
    extracted = {
        row["review_call_slot_id"]: row for row in extract_reviewed_rules(config_path)
    }
    private_root = ROOT / str(config["private_roots"]["task038c"])
    records: list[dict[str, Any]] = []
    for outcome in provider["slots"]:
        base = {
            key: outcome[key]
            for key in (
                "review_call_slot_id",
                "branch_id",
                "initial_slot_id",
                "detector_variant",
                "kpi_id",
                "direction",
                "parent_rule_hash",
            )
        }
        extraction = extracted[outcome["review_call_slot_id"]]
        if outcome["capture_status"] != "provider_response_captured":
            records.append(
                {
                    **base,
                    "reviewed_rule_hash": None,
                    "response_hash": outcome.get("response_hash"),
                    "extraction_status": extraction["extraction_status"],
                    "static_status": "not_audited_no_rule",
                    "terminal_status": _provider_terminal(
                        outcome["capture_status"]
                    ),
                }
            )
            continue
        response_path = (
            private_root
            / "responses"
            / outcome["review_call_slot_id"]
            / "raw_response.md"
        )
        audit, _ = audit_response(response_path.read_text(encoding="utf-8"))
        terminal = (
            "reviewed_static_valid"
            if extraction["extraction_status"] == "extracted_single_rule"
            and audit["static_status"] == "static_valid"
            else (
                "reviewed_response_without_rule"
                if extraction["extraction_status"] != "extracted_single_rule"
                else "reviewed_static_invalid"
            )
        )
        write_json(
            private_root
            / "static_audits"
            / f"{outcome['review_call_slot_id']}.json",
            audit,
        )
        records.append(
            {
                **base,
                "reviewed_rule_hash": extraction["reviewed_rule_hash"],
                "response_hash": outcome.get("response_hash"),
                "extraction_status": extraction["extraction_status"],
                "code_fence_count": audit["code_fence_count"],
                "syntax_valid": audit["syntax_valid"],
                "signature_valid": audit["signature_valid"],
                "allowed_imports_valid": audit["allowed_imports_valid"],
                "prohibited_calls_absent": audit["prohibited_calls_absent"],
                "hardcoded_output_absent": not audit[
                    "hardcoded_index_or_label_suspicion"
                ],
                "static_status": audit["static_status"],
                "terminal_status": terminal,
            }
        )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038C",
        "artifact_type": "reviewed_rule_static_audit_report",
        "provider_call_slots": len(records),
        "rules_extracted": sum(
            row["extraction_status"] == "extracted_single_rule" for row in records
        ),
        "static_valid_revisions": sum(
            row["static_status"] == "static_valid" for row in records
        ),
        "policy_source": "TASK-037D/TASK-038A",
        "raw_rule_source_tracked": False,
        "host_rule_execution": False,
        "repair_agent_calls": 0,
        "records": records,
    }
    return write_hashed_report(ROOT / str(config["reports"]["static"]), report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    report = audit_reviewed_rules((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "rules_extracted": report["rules_extracted"],
                "static_valid": report["static_valid_revisions"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
