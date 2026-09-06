"""Private, value-custody audit of HAI23 direct target namespaces.

This is deliberately not a reconciliation authority.  It replays the closed
HAI23 scenario authority, enumerates non-canonical direct target strings only
in a caller-selected private output, and records the finite frozen P1 scope
that prevents automatic eligibility expansion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_hai23_resolution_aware_authority_v1 import (
    MANUAL_SHA256,
    canonical_bytes,
    manual_records,
)
from paperworks.validation_v2.dg05_execution_closure_v1 import (
    FROZEN_FULL_SCOPE_PROCESS_MAP_V1,
    canonical_bytes as scope_canonical_bytes,
    digest,
)


FULL_SCOPE_HASH = "0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619"
SCENARIO_AUTHORITY_HASH = "314a188ec18f681e58e7e0c7322a281748ba2f4acb7e58f418e2c4fb8b766e91"
OFFICIAL_REPOSITORY_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def self_hashed(body: dict[str, Any]) -> dict[str, Any]:
    value = dict(body)
    value["self_hash"] = sha256_bytes(canonical_bytes(value))
    return value


def load_self_hashed(path: Path, expected_hash: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    actual = value.get("self_hash")
    replayed = sha256_bytes(canonical_bytes({key: item for key, item in value.items() if key != "self_hash"}))
    if actual != replayed or actual != expected_hash:
        raise ValueError("HAI23_SCENARIO_AUTHORITY_REPLAY_FAILURE")
    return value


def exact_graph_literal_presence(official_root: Path, identity: str) -> dict[str, bool]:
    """Report literal-byte presence only; it never creates an equivalence."""
    result: dict[str, bool] = {}
    for path in sorted((official_root / "graph" / "boiler").glob("*.json")):
        result[path.name] = identity.encode("utf-8") in path.read_bytes()
    return result


def build(official_root: Path, private_authority: Path) -> dict[str, Any]:
    authority = load_self_hashed(private_authority, SCENARIO_AUTHORITY_HASH)
    manual = official_root / "hai_dataset_technical_details.pdf"
    rows = {row["manual_id"]: row for row in manual_records(manual)}
    records = authority["canonical_records"]
    if len(records) != 38 or {record["official_occurrence_id"] for record in records} != set(rows):
        raise ValueError("HAI23_SCENARIO_AUTHORITY_RECORD_SET_MISMATCH")

    canonical = {
        identity
        for points in FROZEN_FULL_SCOPE_PROCESS_MAP_V1["23.05"].values()
        for identity in points
    }
    if len(canonical) != 86:
        raise ValueError("FROZEN_P1_SCOPE_CANONICAL_UNIVERSE_MISMATCH")

    use: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        manual_row = rows[record["official_occurrence_id"]]
        if record["attacked_identities"] != manual_row["attacked_identities"]:
            raise ValueError("MANUAL_TARGET_REPLAY_MISMATCH")
        for target in record["attacked_identities"]:
            if target not in canonical:
                use[target].append(
                    {
                        "scenario_id": record["scenario_id"],
                        "official_occurrence_id": record["official_occurrence_id"],
                        "manual_target_controller_components": manual_row["target_controller_components"],
                        "manual_scenario_components": manual_row["scenario_components"],
                    }
                )
    worksheet = []
    for target in sorted(use):
        worksheet.append(
            {
                "raw_manual_target_representation": target,
                "raw_identity_sha256": sha256_bytes(target.encode("utf-8")),
                "occurrences": use[target],
                "exact_in_frozen_hai23_canonical_scope": False,
                "exact_literal_presence_in_official_boiler_graph_files": exact_graph_literal_presence(official_root, target),
                "classification": "DEFERRED_FROZEN_P1_SCOPE_EXACT_MEMBERSHIP_BLOCK",
                "canonical_hai_identity": None,
                "official_equivalent": None,
                "automatic_p1_eligibility_effect": "PROHIBITED_PENDING_PROSPECTIVE_SOURCE_AMENDMENT",
                "source_hashes": {"technical_manual_sha256": MANUAL_SHA256},
            }
        )
    affected = {item["scenario_id"] for entries in use.values() for item in entries}
    raw_set_hash = sha256_bytes(canonical_bytes(sorted(use)))
    if len(worksheet) != 14 or sum(len(items) for items in use.values()) != 24 or len(affected) != 21:
        raise ValueError("UNRESOLVED_TARGET_CENSUS_MISMATCH")
    return self_hashed(
        {
            "schema": "hai23_private_target_namespace_p1_audit_v1",
            "status": "BLOCKED_FROZEN_SCOPE_EXACT_MEMBERSHIP",
            "task_id": "DG05-HAI23-OFFICIAL-TARGET-NAMESPACE-P1-CLOSURE-001",
            "official_repository_commit": OFFICIAL_REPOSITORY_COMMIT,
            "scenario_authority_sha256": SCENARIO_AUTHORITY_HASH,
            "full_process_scope_authority_sha256": FULL_SCOPE_HASH,
            "frozen_scope_semantics": "EXACT_MEMBERSHIP_IN_FINITE_CANONICAL_HAI23_IDENTITY_SET",
            "frozen_scope_canonical_identity_set_sha256": digest(sorted(canonical)),
            "official_manual_context": {
                "manual_sha256": MANUAL_SHA256,
                "p1_process_definition_page": 5,
                "hai23_attack_operation_context_page": 32,
                "statement": "HAIEnd collection and HAI23 attack scenarios target the boiler control system; the manual defines the boiler as P1.",
            },
            "unresolved_representation_set_sha256": raw_set_hash,
            "unresolved_representation_count": len(worksheet),
            "unresolved_token_occurrences": sum(len(items) for items in use.values()),
            "scenarios_with_at_least_one_unresolved_target": len(affected),
            "private_reconciliation_worksheet": worksheet,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--private-authority", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    payload = build(args.official_root, args.private_authority)
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_bytes(canonical_bytes(payload) + b"\n")
    print(
        json.dumps(
            {
                "private_worksheet_hash": payload["self_hash"],
                "status": payload["status"],
                "unresolved_representation_count": payload["unresolved_representation_count"],
                "unresolved_token_occurrences": payload["unresolved_token_occurrences"],
                "affected_scenarios": payload["scenarios_with_at_least_one_unresolved_target"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
