"""Adversarial root-replay QA for DEC-034 private authorities.

Temporary mutated authorities are never persisted outside the system temporary
directory.  The script reports only case names and aggregate pass/fail counts.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from typing import Any, Callable

from verify_dg05_hai23_p1_direct_target_scope_v2 import digest, replay


def refresh(value: dict[str, Any]) -> dict[str, Any]:
    body = {key: item for key, item in value.items() if key != "self_hash"}
    return {**body, "self_hash": digest(body)}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def run_case(
    name: str,
    mutate: Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], None],
    scenario: Path,
    target_path: Path,
    scope_path: Path,
    eligibility_path: Path,
    manual: Path,
) -> bool:
    target, scope, eligibility = load(target_path), load(scope_path), load(eligibility_path)
    mutate(target, scope, eligibility)
    with tempfile.TemporaryDirectory(prefix="dg05-p1-v2-adversarial-") as directory:
        root = Path(directory)
        target_file, scope_file, eligibility_file = root / "target.json", root / "scope.json", root / "eligibility.json"
        write(target_file, target)
        write(scope_file, scope)
        write(eligibility_file, eligibility)
        try:
            replay(
                private_scenario=scenario,
                target_authority_path=target_file,
                scope_authority_path=scope_file,
                eligibility_authority_path=eligibility_file,
                official_manual=manual,
            )
        except ValueError:
            return True
    return False


def refresh_target_chain(target: dict[str, Any], scope: dict[str, Any], eligibility: dict[str, Any]) -> None:
    target.update(refresh(target))
    scope["target_process_authority_sha256"] = target["self_hash"]
    scope.update(refresh(scope))
    eligibility["target_process_authority_sha256"] = target["self_hash"]
    eligibility["scope_authority_sha256"] = scope["self_hash"]
    eligibility.update(refresh(eligibility))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-scenario", type=Path, required=True)
    parser.add_argument("--target-authority", type=Path, required=True)
    parser.add_argument("--scope-authority", type=Path, required=True)
    parser.add_argument("--eligibility-authority", type=Path, required=True)
    parser.add_argument("--official-manual", type=Path, required=True)
    args = parser.parse_args()

    def target_mutation(field: str, value: Any) -> Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], None]:
        def mutate(target: dict[str, Any], scope: dict[str, Any], eligibility: dict[str, Any]) -> None:
            record = next(item for item in target["records"] if item["target_namespace"] != "HAI_CANONICAL_FEATURE")
            record[field] = value
            record.update({"record_hash": digest({key: item for key, item in record.items() if key != "record_hash"})})
            refresh_target_chain(target, scope, eligibility)
        return mutate

    def scope_mutation(field: str, value: Any) -> Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], None]:
        def mutate(target: dict[str, Any], scope: dict[str, Any], eligibility: dict[str, Any]) -> None:
            scope[field] = value
            scope.update(refresh(scope))
            eligibility["scope_authority_sha256"] = scope["self_hash"]
            eligibility.update(refresh(eligibility))
        return mutate

    def remove_target(target: dict[str, Any], scope: dict[str, Any], eligibility: dict[str, Any]) -> None:
        target["records"].pop()
        refresh_target_chain(target, scope, eligibility)

    def add_target(target: dict[str, Any], scope: dict[str, Any], eligibility: dict[str, Any]) -> None:
        forged = deepcopy(target["records"][0])
        forged["raw_official_target_identity_hash"] = "f" * 64
        forged["record_hash"] = digest({key: item for key, item in forged.items() if key != "record_hash"})
        target["records"].append(forged)
        refresh_target_chain(target, scope, eligibility)

    def remove_scenario(target: dict[str, Any], scope: dict[str, Any], eligibility: dict[str, Any]) -> None:
        eligibility["records"].pop()
        eligibility.update(refresh(eligibility))

    def add_scenario(target: dict[str, Any], scope: dict[str, Any], eligibility: dict[str, Any]) -> None:
        forged = deepcopy(eligibility["records"][0])
        forged["scenario_id"] = "FORGED_SCENARIO"
        eligibility["records"].append(forged)
        eligibility.update(refresh(eligibility))

    cases: list[tuple[str, Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], None]]] = [
        ("fake_canonical_alias", target_mutation("canonical_hai_feature_identity", "FORGED_CANONICAL")),
        ("case_only_alias", target_mutation("canonical_hai_feature_identity", "case_variant")),
        ("underscore_only_alias", target_mutation("canonical_hai_feature_identity", "UNDER_SCORE_VARIANT")),
        ("prefix_inference", target_mutation("canonical_hai_feature_identity", "P1_FORGED")),
        ("substring_inference", target_mutation("canonical_hai_feature_identity", "FORGED_P1_FRAGMENT")),
        ("edit_distance_mapping", target_mutation("canonical_hai_feature_identity", "NEAR_CANONICAL")),
        ("forced_haiend_feature_alias", target_mutation("target_namespace", "HAI_CANONICAL_FEATURE")),
        ("source_hash_mutation", target_mutation("source_sha256", "a" * 64)),
        ("process_membership_mutation", target_mutation("official_process_membership", "P2")),
        ("controller_mutation", target_mutation("official_controller_identity_hashes", ["b" * 64])),
        ("target_representation_mutation", target_mutation("raw_official_target_identity_hash", "c" * 64)),
        ("any_to_all_mutation", scope_mutation("multi_target_aggregation", "ALL_VERIFIED_P1_DIRECT_TARGETS")),
        ("unknown_to_nonp1_mutation", scope_mutation("unknown_handling", "P1_NOT_ELIGIBLE")),
        ("unknown_to_p1_mutation", scope_mutation("unknown_handling", "P1_ELIGIBLE")),
        ("historical_v1_hash_mutation", scope_mutation("historical_predecessor", {"authority_id": "FULL_PROCESS_SCOPE_AUTHORITY_V1", "authority_sha256": "0" * 64})),
        ("decision_binding_mutation", scope_mutation("decision_hash", "d" * 64)),
        ("scenario_target_removal", remove_target),
        ("scenario_target_addition", add_target),
        ("eligibility_scenario_removal", remove_scenario),
        ("eligibility_scenario_addition", add_scenario),
    ]
    rejected = [name for name, mutation in cases if run_case(name, mutation, args.private_scenario, args.target_authority, args.scope_authority, args.eligibility_authority, args.official_manual)]
    if len(rejected) != len(cases):
        print(json.dumps({"cases": len(cases), "rejected": len(rejected), "accepted_case_names": sorted(set(name for name, _ in cases) - set(rejected)), "status": "FAIL"}, sort_keys=True))
        raise SystemExit("ADVERSARIAL_CASE_ACCEPTED")
    print(json.dumps({"cases": len(cases), "rejected": len(rejected), "unexpected_accepts": 0, "status": "PASS"}, sort_keys=True))


if __name__ == "__main__":
    main()
