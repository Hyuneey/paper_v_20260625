"""Extract one complete repaired rule from each captured Repair response."""

from __future__ import annotations

import ast
import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import (
    read_json,
    write_json,
)
from experiments.argos_reproduction.multi_rule_static_audit import (
    extract_python_fence,
)
from experiments.argos_reproduction.repair_failure_replay import verify_report_hash


def _signature_valid(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    definitions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "inference"
    ]
    if len(definitions) != 1:
        return False
    function = definitions[0]
    return bool(
        len(function.args.args) == 1
        and function.args.args[0].arg == "sample"
        and not function.args.vararg
        and not function.args.kwarg
        and not function.args.kwonlyargs
    )


def extraction_status(response: str) -> tuple[str, str | None, int]:
    code, fence_count = extract_python_fence(response)
    if fence_count == 0:
        return "response_without_rule", None, fence_count
    if fence_count > 1:
        return "multiple_code_blocks", None, fence_count
    if code is None:
        return "response_without_rule", None, fence_count
    if not _signature_valid(code):
        return "invalid_function_signature", code, fence_count
    return "extracted_single_rule", code, fence_count


def extract_repaired_rules(config_path: Path) -> list[dict[str, Any]]:
    config = read_json(config_path)
    provider_raw = read_json(ROOT / str(config["reports"]["provider"]))
    provider = verify_report_hash(
        ROOT / str(config["reports"]["provider"]),
        str(provider_raw["report_hash"]),
    )
    private_root = ROOT / str(config["private_root"])
    records: list[dict[str, Any]] = []
    for outcome in provider["slots"]:
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
        if outcome["capture_status"] != "provider_response_captured":
            records.append(
                {
                    **base,
                    "response_hash": outcome.get("response_hash"),
                    "extraction_status": "not_attempted_no_visible_response",
                    "repaired_rule_hash": None,
                }
            )
            continue
        response_path = (
            private_root
            / "responses"
            / outcome["repair_call_slot_id"]
            / "raw_response.md"
        )
        response = response_path.read_text(encoding="utf-8")
        observed_hash = hashlib.sha256(response.encode()).hexdigest()
        if observed_hash != outcome["response_hash"]:
            raise RuntimeError("TASK038B_RESPONSE_HASH_MISMATCH")
        status, code, fence_count = extraction_status(response)
        repaired_hash = hashlib.sha256(code.encode()).hexdigest() if code else None
        if code is not None:
            rule_path = private_root / "repaired_rules" / f"{repaired_hash}.py"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            if rule_path.exists() and rule_path.read_text(encoding="utf-8") != code:
                raise RuntimeError("TASK038B_REPAIRED_RULE_HASH_COLLISION")
            rule_path.write_bytes(code.encode("utf-8"))
        private_record = {
            **base,
            "response_hash": observed_hash,
            "extraction_status": status,
            "code_fence_count": fence_count,
            "repaired_rule_hash": repaired_hash,
        }
        write_json(
            private_root
            / "extractions"
            / f"{outcome['repair_call_slot_id']}.json",
            private_record,
        )
        records.append(private_record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038b_repair_execution.json",
    )
    args = parser.parse_args()
    records = extract_repaired_rules((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "visible_responses": sum(
                    item["extraction_status"] != "not_attempted_no_visible_response"
                    for item in records
                ),
                "rules_extracted": sum(
                    item["extraction_status"] == "extracted_single_rule"
                    for item in records
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
