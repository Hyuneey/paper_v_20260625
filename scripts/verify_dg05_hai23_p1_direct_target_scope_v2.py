"""Independent read-only replay for the DEC-034 HAI23 P1 V2 authorities.

This verifier intentionally does not import the V2 authority builder.  It
reconstructs direct-target hashes and the process conclusion from the frozen
scenario authority plus independent official-manual page evidence.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

import pdfplumber

from build_hai23_resolution_aware_authority_v1 import manual_records
from paperworks.validation_v2.dg05_execution_closure_v1 import FROZEN_FULL_SCOPE_PROCESS_MAP_V1


SCENARIO_HASH = "314a188ec18f681e58e7e0c7322a281748ba2f4acb7e58f418e2c4fb8b766e91"
DECISION_HASH = "67a724b3b433d2b21904d587a1ce357090021dc654f212e667e0dd7a79c45ccd"
MANUAL_HASH = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def verify_hashed(value: dict[str, Any], expected: str | None = None) -> None:
    if value.get("self_hash") != digest({key: item for key, item in value.items() if key != "self_hash"}):
        raise ValueError("SELF_HASH_MISMATCH")
    if expected is not None and value["self_hash"] != expected:
        raise ValueError("EXPECTED_AUTHORITY_HASH_MISMATCH")


def raw_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@lru_cache(maxsize=4)
def verify_manual_root(path_text: str) -> None:
    official_manual = Path(path_text)
    if hashlib.sha256(official_manual.read_bytes()).hexdigest() != MANUAL_HASH:
        raise ValueError("OFFICIAL_MANUAL_HASH_MISMATCH")
    with pdfplumber.open(official_manual) as document:
        p1_text = document.pages[4].extract_text() or ""
        internal_text = document.pages[8].extract_text() or ""
        operation_text = document.pages[31].extract_text() or ""
    if "boiler process (P1)" not in p1_text:
        raise ValueError("OFFICIAL_P1_PROCESS_EVIDENCE_MISSING")
    if "internal points" not in internal_text or "algorithm blocks" not in internal_text:
        raise ValueError("OFFICIAL_INTERNAL_TARGET_EVIDENCE_MISSING")
    if "boiler control system" not in operation_text:
        raise ValueError("OFFICIAL_ATTACK_OPERATION_SCOPE_EVIDENCE_MISSING")


@lru_cache(maxsize=4)
def manual_rows_by_id(path_text: str) -> dict[str, dict[str, Any]]:
    return {row["manual_id"]: row for row in manual_records(Path(path_text))}


def replay(
    *,
    private_scenario: Path,
    target_authority_path: Path,
    scope_authority_path: Path,
    eligibility_authority_path: Path,
    official_manual: Path,
) -> dict[str, Any]:
    scenario = json.loads(private_scenario.read_text(encoding="utf-8"))
    target_authority = json.loads(target_authority_path.read_text(encoding="utf-8"))
    scope = json.loads(scope_authority_path.read_text(encoding="utf-8"))
    eligibility = json.loads(eligibility_authority_path.read_text(encoding="utf-8"))
    verify_hashed(scenario, SCENARIO_HASH)
    verify_hashed(target_authority)
    verify_hashed(scope)
    verify_hashed(eligibility)
    verify_manual_root(str(official_manual))
    canonical = {identity for identities in FROZEN_FULL_SCOPE_PROCESS_MAP_V1["23.05"].values() for identity in identities}
    target_records = {record["raw_official_target_identity_hash"]: record for record in target_authority["records"]}
    expected_targets = {target for record in scenario["canonical_records"] for target in record["attacked_identities"]}
    if len(scenario["canonical_records"]) != 38 or len(expected_targets) != 30 or len(target_records) != 30:
        raise ValueError("TARGET_CENSUS_MISMATCH")
    manual_rows = manual_rows_by_id(str(official_manual))
    expected_controllers: dict[str, set[str]] = {}
    for scenario_record in scenario["canonical_records"]:
        manual_row = manual_rows.get(scenario_record["official_occurrence_id"])
        if manual_row is None or manual_row["attacked_identities"] != scenario_record["attacked_identities"]:
            raise ValueError("OFFICIAL_MANUAL_TARGET_OR_SCENARIO_MUTATION")
        for target in manual_row["attacked_identities"]:
            expected_controllers.setdefault(target, set()).update(manual_row["target_controller_components"])
    for target in expected_targets:
        record = target_records.get(raw_hash(target))
        if record is None:
            raise ValueError("OFFICIAL_TARGET_MISSING")
        expected_namespace = "HAI_CANONICAL_FEATURE" if target in canonical else "OTHER_OFFICIAL_HAI_TARGET_IDENTITY"
        if record["target_namespace"] != expected_namespace:
            raise ValueError("TARGET_NAMESPACE_MUTATION")
        if record["canonical_hai_feature_identity"] != (target if target in canonical else None):
            raise ValueError("CANONICAL_ALIAS_OR_SUBSTITUTION")
        if record["official_controller_identity_hashes"] != sorted(raw_hash(item) for item in expected_controllers[target]):
            raise ValueError("OFFICIAL_CONTROLLER_MUTATION")
        if record["official_process_membership"] != "P1" or record["heuristic_alias"] is not False:
            raise ValueError("PROCESS_MEMBERSHIP_OR_HEURISTIC_MUTATION")
        if record["source_sha256"] != MANUAL_HASH or record["evidence_type"] != "OFFICIAL_HAI23_ATTACK_OPERATION_BOILER_DCS_SCOPE":
            raise ValueError("OFFICIAL_SOURCE_EVIDENCE_MUTATION")
    if scope.get("historical_predecessor") != {
        "authority_id": "FULL_PROCESS_SCOPE_AUTHORITY_V1",
        "authority_sha256": "0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619",
    }:
        raise ValueError("HISTORICAL_V1_MUTATION")
    if scope.get("decision_hash") != DECISION_HASH or scope.get("target_process_authority_sha256") != target_authority["self_hash"]:
        raise ValueError("SCOPE_DECISION_OR_TARGET_BINDING_MUTATION")
    if scope.get("multi_target_aggregation") != "ANY_VERIFIED_P1_DIRECT_TARGET":
        raise ValueError("ANY_RULE_MUTATION")
    if scope.get("unknown_handling") != "UNRESOLVED_UNLESS_ANY_VERIFIED_P1_DIRECT_TARGET":
        raise ValueError("UNKNOWN_HANDLING_MUTATION")
    observed = {entry["scenario_id"]: entry["eligibility"] for entry in eligibility["records"]}
    expected = {record["scenario_id"]: "P1_ELIGIBLE" for record in scenario["canonical_records"]}
    if observed != expected or eligibility.get("status_counts") != {"P1_ELIGIBLE": 38, "P1_NOT_ELIGIBLE": 0, "UNRESOLVED": 0}:
        raise ValueError("SCENARIO_ELIGIBILITY_MISMATCH")
    return {
        "schema": "hai23_p1_direct_target_process_scope_v2_independent_replay_v1",
        "status": "PASS",
        "scenario_authority_sha256": scenario["self_hash"],
        "target_process_authority_sha256": target_authority["self_hash"],
        "scope_authority_sha256": scope["self_hash"],
        "eligibility_authority_sha256": eligibility["self_hash"],
        "scenario_agreement": "38_OF_38",
        "authority_agreement": "PASS",
        "status_counts": eligibility["status_counts"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-scenario", type=Path, required=True)
    parser.add_argument("--target-authority", type=Path, required=True)
    parser.add_argument("--scope-authority", type=Path, required=True)
    parser.add_argument("--eligibility-authority", type=Path, required=True)
    parser.add_argument("--official-manual", type=Path, required=True)
    args = parser.parse_args()
    result = replay(
        private_scenario=args.private_scenario,
        target_authority_path=args.target_authority,
        scope_authority_path=args.scope_authority,
        eligibility_authority_path=args.eligibility_authority,
        official_manual=args.official_manual,
    )
    result["self_hash"] = digest(result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
