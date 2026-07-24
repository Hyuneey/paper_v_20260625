"""Apply the frozen generated-rule static policy to Repair revisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    sha256_json,
    write_json,
)
from experiments.argos_reproduction.multi_rule_static_audit import audit_response
from experiments.argos_reproduction.repair_failure_replay import (
    load_repair_population,
    verify_report_hash,
)
from experiments.argos_reproduction.repaired_rule_extraction import (
    extract_repaired_rules,
)


def classify_static_failure(audit: Mapping[str, Any]) -> str:
    if not audit.get("syntax_valid"):
        return "repaired_syntax_invalid"
    if not audit.get("signature_valid"):
        return "repaired_signature_invalid"
    if not audit.get("allowed_imports_valid"):
        return "repaired_unsafe_import"
    if not audit.get("prohibited_calls_absent"):
        return "repaired_forbidden_operation"
    if audit.get("hardcoded_index_or_label_suspicion"):
        return "repaired_hardcoded_output"
    return "repaired_static_invalid_other"


def _provider_terminal(status: str) -> str:
    return {
        "provider_error": "repair_provider_error",
        "transport_error": "repair_transport_error",
        "empty_visible_response": "repair_empty_response",
        "not_attempted_global_block": "not_attempted_global_block",
        "malformed_provider_payload": "repair_provider_error",
    }.get(status, "repair_response_without_rule")


def audit_repaired_rules(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    population = {
        item["initial_slot_id"]: item for item in load_repair_population(config)
    }
    provider_raw = read_json(ROOT / str(config["reports"]["provider"]))
    provider = verify_report_hash(
        ROOT / str(config["reports"]["provider"]),
        str(provider_raw["report_hash"]),
    )
    extraction = {
        item["repair_call_slot_id"]: item
        for item in extract_repaired_rules(config_path)
    }
    private_root = ROOT / str(config["private_root"])
    records: list[dict[str, Any]] = []
    for outcome in provider["slots"]:
        initial = population[outcome["initial_slot_id"]]
        base = {
            key: outcome[key]
            for key in (
                "repair_call_slot_id",
                "initial_slot_id",
                "detector_variant",
                "kpi_id",
                "direction",
            )
        }
        extracted = extraction[outcome["repair_call_slot_id"]]
        if outcome["capture_status"] != "provider_response_captured":
            records.append(
                {
                    **base,
                    "initial_rule_hash": initial["initial_rule_hash"],
                    "repaired_rule_hash": None,
                    "extraction_status": extracted["extraction_status"],
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
            / outcome["repair_call_slot_id"]
            / "raw_response.md"
        )
        audit, code = audit_response(response_path.read_text(encoding="utf-8"))
        if extracted["extraction_status"] != "extracted_single_rule":
            terminal = "repair_response_without_rule"
        elif audit["static_status"] == "static_valid":
            terminal = "repaired_static_valid"
        else:
            terminal = "repaired_static_invalid"
        private_audit = {
            **audit,
            "classified_static_status": (
                "repaired_static_valid"
                if audit["static_status"] == "static_valid"
                else classify_static_failure(audit)
            ),
        }
        write_json(
            private_root
            / "static_audits"
            / f"{outcome['repair_call_slot_id']}.json",
            private_audit,
        )
        records.append(
            {
                **base,
                "initial_rule_hash": initial["initial_rule_hash"],
                "repaired_rule_hash": extracted["repaired_rule_hash"],
                "response_hash": outcome.get("response_hash"),
                "extraction_status": extracted["extraction_status"],
                "code_fence_count": audit["code_fence_count"],
                "syntax_valid": audit["syntax_valid"],
                "signature_valid": audit["signature_valid"],
                "allowed_imports_valid": audit["allowed_imports_valid"],
                "prohibited_calls_absent": audit["prohibited_calls_absent"],
                "hardcoded_output_absent": not audit[
                    "hardcoded_index_or_label_suspicion"
                ],
                "classified_static_status": private_audit[
                    "classified_static_status"
                ],
                "static_status": audit["static_status"],
                "terminal_status": terminal,
            }
        )
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-038B",
        "artifact_type": "repaired_rule_static_audit_report",
        "frozen_repair_population": 13,
        "provider_call_slots": len(records),
        "rules_extracted": sum(
            item["extraction_status"] == "extracted_single_rule"
            for item in records
        ),
        "static_valid_revisions": sum(
            item["static_status"] == "static_valid" for item in records
        ),
        "policy_source": "TASK-037D/TASK-038A",
        "raw_rule_source_tracked": False,
        "host_rule_execution": False,
        "records": records,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["static"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038b_repair_execution.json",
    )
    args = parser.parse_args()
    report = audit_repaired_rules((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "rules_extracted": report["rules_extracted"],
                "static_valid_revisions": report["static_valid_revisions"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
