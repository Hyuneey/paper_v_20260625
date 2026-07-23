"""Apply the frozen TASK-035A static rule policy to TASK-037D responses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
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
from experiments.argos_reproduction.multi_rule_static_audit import audit_response


def audit_error_conditioned_rules(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    provider = read_json(ROOT / str(config["reports"]["provider"]))
    requests = read_json(ROOT / str(config["reports"]["requests"]))
    request_by_slot = {item["slot_id"]: item for item in requests["slots"]}
    private_root = ROOT / str(config["private_root"])
    records: list[dict[str, Any]] = []
    for outcome in provider["slots"]:
        slot = request_by_slot[outcome["slot_id"]]
        base = {
            key: slot[key]
            for key in (
                "slot_id",
                "detector_variant",
                "kpi_id",
                "direction",
                "target_chunk_hash",
                "contrast_chunk_hash",
            )
        }
        if outcome["capture_status"] != "provider_response_captured":
            records.append(
                {
                    **base,
                    "static_status": "not_audited_no_response",
                    "terminal_status": outcome["capture_status"],
                }
            )
            continue
        response_path = (
            private_root / "responses" / slot["slot_id"] / "raw_response.md"
        )
        response = response_path.read_text(encoding="utf-8")
        audit, code = audit_response(response)
        if code is not None:
            rule_path = (
                private_root
                / "quarantine"
                / slot["direction"].lower()
                / f"{audit['rule_sha256']}.py"
            )
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            if rule_path.exists() and rule_path.read_text(encoding="utf-8") != code:
                raise RuntimeError("TASK037D_RULE_HASH_COLLISION")
            rule_path.write_bytes(code.encode("utf-8"))
        write_json(
            private_root / "static_audits" / f"{slot['slot_id']}.json", audit
        )
        terminal = (
            "response_without_rule"
            if not audit["rule_extracted"]
            else (
                "static_invalid"
                if audit["static_status"] != "static_valid"
                else "provider_response_captured"
            )
        )
        records.append({**base, **audit, "terminal_status": terminal})
    report = {
        "schema_version": "1.0",
        "task_id": "TASK-037D",
        "artifact_type": "error_conditioned_static_audit_report",
        "rules_extracted": sum(bool(item.get("rule_extracted")) for item in records),
        "static_valid": sum(item.get("static_status") == "static_valid" for item in records),
        "slots": records,
        "policy_source": "TASK-035A/TASK-035AR",
        "directional_correctness_evaluated": False,
        "raw_rule_source_tracked": False,
    }
    report["report_hash"] = sha256_json(report)
    write_json(ROOT / str(config["reports"]["static"]), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task037d_error_conditioned_rules.json",
    )
    args = parser.parse_args()
    report = audit_error_conditioned_rules((ROOT / args.config).resolve())
    print(
        json.dumps(
            {
                "rules_extracted": report["rules_extracted"],
                "static_valid": report["static_valid"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
