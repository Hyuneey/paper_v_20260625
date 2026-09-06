"""Audit HAI22's frozen P1 scope without creating an amendment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from paperworks.validation_v2.dg05_execution_closure_v1 import FROZEN_FULL_SCOPE_PROCESS_MAP_V1, canonical_bytes


V1_HASH = "0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619"
MANUAL_HASH = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"


def self_hashed(value: dict[str, Any]) -> dict[str, Any]:
    body = dict(value)
    body.pop("self_hash", None)
    return {**body, "self_hash": hashlib.sha256(canonical_bytes(body)).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-authority", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    args = parser.parse_args()
    scenario = json.loads(args.scenario_authority.read_text(encoding="utf-8"))
    canonical = {item for values in FROZEN_FULL_SCOPE_PROCESS_MAP_V1["22.04"].values() for item in values}
    unresolved: dict[str, list[str]] = {}
    for record in scenario["canonical_records"]:
        missing = [target for target in record["attacked_identities"] if target not in canonical]
        if missing:
            unresolved[record["scenario_id"]] = missing
    private = self_hashed({
        "schema": "hai22_private_target_namespace_p1_audit_v1",
        "status": "REQUIRES_VERSION_SPECIFIC_PROSPECTIVE_AMENDMENT",
        "scenario_authority_sha256": scenario["self_hash"],
        "full_process_scope_authority_sha256": V1_HASH,
        "official_manual_sha256": MANUAL_HASH,
        "frozen_mapping_policy": "EXACT_CANONICAL_IDENTITY_ONLY_NO_NEW_ALIAS",
        "unresolved_scenario_targets": unresolved,
    })
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_bytes(canonical_bytes(private) + b"\n")
    public = self_hashed({
        "schema": "hai22_p1_scope_prospective_amendment_decision_brief_v1",
        "status": "USER_DECISION_REQUIRED",
        "verdict": "HAI22_P1_SCOPE_REQUIRES_VERSION_SPECIFIC_PROSPECTIVE_AMENDMENT",
        "scenario_authority_sha256": scenario["self_hash"],
        "historical_full_process_scope_authority_sha256": V1_HASH,
        "official_manual_sha256": MANUAL_HASH,
        "affected_scenarios": len(unresolved),
        "unresolved_direct_target_representation_count": len({target for targets in unresolved.values() for target in targets}),
        "proposed_minimal_amendment": "VERSION_SPECIFIC_DIRECT_OFFICIAL_TARGET_SOURCE_ROOTED_TO_P1_ANY_SEMANTICS",
        "automatic_dec034_transfer": False,
        "post_hoc_risk": "NO_DETECTOR_PREDICTIONS_OR_METRICS_OBSERVED; USER_DECISION_REQUIRED",
        "performance_contact": {"heldout_predictions_observed": 0, "heldout_metrics_observed": 0, "method_comparisons_observed": 0},
        "private_audit_sha256": private["self_hash"],
    })
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.write_bytes(canonical_bytes(public) + b"\n")
    print(json.dumps({"status": public["status"], "affected_scenarios": len(unresolved), "private_audit_hash": private["self_hash"], "decision_brief_hash": public["self_hash"]}, sort_keys=True))


if __name__ == "__main__":
    main()
