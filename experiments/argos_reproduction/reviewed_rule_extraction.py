"""Extract one complete reviewed rule from each captured Review response."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import read_json, write_json
from experiments.argos_reproduction.repaired_rule_extraction import extraction_status
from experiments.argos_reproduction.review_parent_registry import verify_hashed_report


def extract_reviewed_rules(config_path: Path) -> list[dict[str, Any]]:
    config = read_json(config_path)
    provider = verify_hashed_report(ROOT / str(config["reports"]["provider"]))
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
        if outcome["capture_status"] != "provider_response_captured":
            records.append(
                {
                    **base,
                    "response_hash": outcome.get("response_hash"),
                    "extraction_status": "not_attempted_no_visible_response",
                    "reviewed_rule_hash": None,
                }
            )
            continue
        response_path = (
            private_root
            / "responses"
            / outcome["review_call_slot_id"]
            / "raw_response.md"
        )
        response = response_path.read_text(encoding="utf-8")
        response_hash = hashlib.sha256(response.encode()).hexdigest()
        if response_hash != outcome["response_hash"]:
            raise RuntimeError("TASK038C_RESPONSE_HASH_MISMATCH")
        status, code, fence_count = extraction_status(response)
        reviewed_hash = hashlib.sha256(code.encode()).hexdigest() if code else None
        if code is not None:
            rule_path = private_root / "reviewed_rules" / f"{reviewed_hash}.py"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            if rule_path.exists() and rule_path.read_text(encoding="utf-8") != code:
                raise RuntimeError("TASK038C_REVIEWED_RULE_HASH_COLLISION")
            rule_path.write_bytes(code.encode("utf-8"))
        record = {
            **base,
            "response_hash": response_hash,
            "extraction_status": status,
            "code_fence_count": fence_count,
            "reviewed_rule_hash": reviewed_hash,
        }
        write_json(
            private_root
            / "extractions"
            / f"{outcome['review_call_slot_id']}.json",
            record,
        )
        records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task038c_review_inner_experiment.json",
    )
    args = parser.parse_args()
    records = extract_reviewed_rules((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "rules_extracted": sum(
                    row["extraction_status"] == "extracted_single_rule"
                    for row in records
                )
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
