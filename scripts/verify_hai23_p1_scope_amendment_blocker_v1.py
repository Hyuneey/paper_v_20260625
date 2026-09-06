"""Independently replay the public-safe HAI23 P1 scope-amendment blocker.

It intentionally does not import the private-audit builder or construct target
aliases.  It reads the frozen scenario authority and the frozen finite scope,
then checks only aggregate facts suitable for a public receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pdfplumber

from paperworks.validation_v2.dg05_execution_closure_v1 import FROZEN_FULL_SCOPE_PROCESS_MAP_V1


SCENARIO_HASH = "314a188ec18f681e58e7e0c7322a281748ba2f4acb7e58f418e2c4fb8b766e91"
MANUAL_HASH = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def replay(private_authority: Path, manual: Path) -> dict[str, Any]:
    authority = json.loads(private_authority.read_text(encoding="utf-8"))
    replayed = digest({key: value for key, value in authority.items() if key != "self_hash"})
    if authority.get("self_hash") != SCENARIO_HASH or replayed != SCENARIO_HASH:
        raise ValueError("HAI23_SCENARIO_AUTHORITY_REPLAY_FAILURE")
    if hashlib.sha256(manual.read_bytes()).hexdigest() != MANUAL_HASH:
        raise ValueError("OFFICIAL_MANUAL_HASH_MISMATCH")
    with pdfplumber.open(manual) as document:
        process_text = document.pages[4].extract_text() or ""
        namespace_text = document.pages[8].extract_text() or ""
        operation_text = document.pages[31].extract_text() or ""
    if "boiler process (P1)" not in process_text:
        raise ValueError("OFFICIAL_P1_PROCESS_EVIDENCE_MISSING")
    if "internal points" not in namespace_text or "algorithm blocks" not in namespace_text:
        raise ValueError("OFFICIAL_HAIEND_INTERNAL_POINT_EVIDENCE_MISSING")
    if "boiler control system" not in operation_text:
        raise ValueError("OFFICIAL_HAI23_BOILER_ATTACK_SCOPE_EVIDENCE_MISSING")
    canonical = {
        identity
        for identities in FROZEN_FULL_SCOPE_PROCESS_MAP_V1["23.05"].values()
        for identity in identities
    }
    p1 = set(FROZEN_FULL_SCOPE_PROCESS_MAP_V1["23.05"]["P1"])
    unresolved: set[str] = set()
    occurrences = 0
    affected: set[str] = set()
    for record in authority["canonical_records"]:
        record_unresolved = False
        for target in record["attacked_identities"]:
            if target not in canonical:
                unresolved.add(target)
                occurrences += 1
                record_unresolved = True
        if record_unresolved:
            affected.add(record["scenario_id"])
    if len(authority["canonical_records"]) != 38 or len(canonical) != 86 or len(p1) != 44:
        raise ValueError("FROZEN_SCOPE_CENSUS_MISMATCH")
    if (len(unresolved), occurrences, len(affected)) != (14, 24, 21):
        raise ValueError("P1_SCOPE_BLOCKER_AGGREGATE_MISMATCH")
    return {
        "schema": "hai23_p1_scope_amendment_blocker_independent_replay_v1",
        "status": "PASS",
        "scenario_authority_sha256": SCENARIO_HASH,
        "official_manual_sha256": MANUAL_HASH,
        "frozen_hai23_canonical_identity_count": len(canonical),
        "frozen_hai23_p1_identity_count": len(p1),
        "unresolved_representation_count": len(unresolved),
        "unresolved_token_occurrences": occurrences,
        "scenarios_with_at_least_one_unresolved_target": len(affected),
        "semantic_conclusion": "FINITE_EXACT_CANONICAL_MEMBERSHIP_CANNOT_CLASSIFY_NONCANONICAL_DIRECT_TARGETS",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-authority", type=Path, required=True)
    parser.add_argument("--official-manual", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.private_authority, args.official_manual)
    result["self_hash"] = digest(result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
