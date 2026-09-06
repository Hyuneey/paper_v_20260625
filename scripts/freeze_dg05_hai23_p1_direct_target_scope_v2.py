"""Freeze private HAI23 direct-target process and eligibility authorities.

This source-only command consumes the immutable scenario authority and official
manual.  It neither opens held-out feature rows nor invokes a detector.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from build_hai23_resolution_aware_authority_v1 import canonical_bytes, manual_records
from paperworks.validation_v2.dg05_execution_closure_v1 import FROZEN_FULL_SCOPE_PROCESS_MAP_V1
from paperworks.validation_v2.dg05_p1_direct_target_scope_v2 import (
    V1_SCOPE_HASH,
    build_scope_authority,
    build_target_process_authority,
    classify_scenario_targets,
    digest,
    self_hashed,
    validate_target_process_authority,
    verify_self_hash,
)


SCENARIO_HASH = "314a188ec18f681e58e7e0c7322a281748ba2f4acb7e58f418e2c4fb8b766e91"
SOURCE_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"


def load_authority(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    verify_self_hash(value)
    if value["self_hash"] != SCENARIO_HASH or len(value.get("canonical_records", [])) != 38:
        raise ValueError("HAI23_SCENARIO_AUTHORITY_REPLAY_FAILURE")
    return value


def build(private_scenario_authority: Path, official_root: Path, decision_hash: str) -> dict[str, dict[str, Any]]:
    scenario = load_authority(private_scenario_authority)
    manual_rows = {row["manual_id"]: row for row in manual_records(official_root / "hai_dataset_technical_details.pdf")}
    if set(manual_rows) != {record["official_occurrence_id"] for record in scenario["canonical_records"]}:
        raise ValueError("OFFICIAL_MANUAL_SCENARIO_BINDING_MISMATCH")
    canonical = {
        identity
        for identities in FROZEN_FULL_SCOPE_PROCESS_MAP_V1["23.05"].values()
        for identity in identities
    }
    controllers: dict[str, set[str]] = {}
    raw_targets: set[str] = set()
    for scenario_record in scenario["canonical_records"]:
        manual = manual_rows[scenario_record["official_occurrence_id"]]
        if manual["attacked_identities"] != scenario_record["attacked_identities"]:
            raise ValueError("OFFICIAL_DIRECT_TARGET_REPLAY_MISMATCH")
        for target in scenario_record["attacked_identities"]:
            raw_targets.add(target)
            controllers.setdefault(target, set()).update(manual["target_controller_components"])
    target_authority = build_target_process_authority(
        raw_targets=raw_targets,
        canonical_hai23_identities=canonical,
        target_controllers={target: sorted(values) for target, values in controllers.items()},
        decision_hash=decision_hash,
        source_commit=SOURCE_COMMIT,
    )
    validate_target_process_authority(target_authority)
    scope_authority = build_scope_authority(decision_hash=decision_hash, target_process_authority_hash=target_authority["self_hash"])
    eligibility_records = []
    for record in scenario["canonical_records"]:
        eligibility_records.append(
            {
                "scenario_id": record["scenario_id"],
                "direct_target_set_hash": digest(sorted(record["attacked_identities"])),
                "eligibility": classify_scenario_targets(record["attacked_identities"], target_authority, scope_authority),
            }
        )
    status_counts = {status: sum(entry["eligibility"] == status for entry in eligibility_records) for status in ("P1_ELIGIBLE", "P1_NOT_ELIGIBLE", "UNRESOLVED")}
    if status_counts != {"P1_ELIGIBLE": 38, "P1_NOT_ELIGIBLE": 0, "UNRESOLVED": 0}:
        raise ValueError("HAI23_P1_ELIGIBILITY_REPLAY_INCOMPLETE")
    eligibility_authority = self_hashed(
        {
            "schema": "hai23_p1_direct_target_eligibility_authority_v2",
            "historical_v1_scope_sha256": V1_SCOPE_HASH,
            "target_process_authority_sha256": target_authority["self_hash"],
            "scope_authority_sha256": scope_authority["self_hash"],
            "scenario_authority_sha256": scenario["self_hash"],
            "records": eligibility_records,
            "status_counts": status_counts,
        }
    )
    return {"target_process": target_authority, "scope": scope_authority, "eligibility": eligibility_authority}


def write_authorities(output: Path, authorities: dict[str, dict[str, Any]]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    names = {
        "target_process": "HAI23_OFFICIAL_DIRECT_TARGET_PROCESS_AUTHORITY_V1.private.json",
        "scope": "P1_DIRECT_TARGET_PROCESS_SCOPE_AUTHORITY_V2.private.json",
        "eligibility": "HAI23_P1_DIRECT_TARGET_ELIGIBILITY_AUTHORITY_V2.private.json",
    }
    for key, name in names.items():
        path = output / name
        if path.exists() and path.read_bytes() != canonical_bytes(authorities[key]) + b"\n":
            raise ValueError("APPEND_ONLY_PRIVATE_AUTHORITY_CONFLICT")
        path.write_bytes(canonical_bytes(authorities[key]) + b"\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-scenario-authority", type=Path, required=True)
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--decision-hash", required=True)
    parser.add_argument("--private-output-dir", type=Path, required=True)
    args = parser.parse_args()
    authorities = build(args.private_scenario_authority, args.official_root, args.decision_hash)
    write_authorities(args.private_output_dir, authorities)
    target_records = authorities["target_process"]["records"]
    print(json.dumps({
        "target_process_authority_hash": authorities["target_process"]["self_hash"],
        "scope_authority_hash": authorities["scope"]["self_hash"],
        "eligibility_authority_hash": authorities["eligibility"]["self_hash"],
        "target_representations": len(target_records),
        "canonical_feature_identities": sum(row["target_namespace"] == "HAI_CANONICAL_FEATURE" for row in target_records),
        "noncanonical_other_identities": sum(row["target_namespace"] != "HAI_CANONICAL_FEATURE" for row in target_records),
        "status_counts": authorities["eligibility"]["status_counts"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
