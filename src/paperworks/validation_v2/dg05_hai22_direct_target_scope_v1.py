"""DEC-036 HAI22-only direct-target P1 scope construction.

This deliberately does not import the HAI23 scope module.  The manual's
``Target Controller`` column is the version-bound source root for process
membership; raw target cells remain raw and are never aliased to a feature.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping


DECISION_ID = "DEC-036"
V1_SCOPE_HASH = "0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619"
MANUAL_HASH = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"
_CONTROLLER_PROCESS = re.compile(r"^(P[1-4])-", re.ASCII)


def _bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def self_hashed(value: dict[str, Any]) -> dict[str, Any]:
    body = dict(value)
    body.pop("self_hash", None)
    return {**body, "self_hash": digest(body)}


def _token(value: str) -> str:
    if not value:
        raise ValueError("HAI22_OFFICIAL_TARGET_OR_CONTROLLER_MISSING")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _source_rooted_process(controllers: list[str]) -> str | None:
    """Read the explicit manual-controller notation, never target text."""
    processes = {_CONTROLLER_PROCESS.match(item).group(1) for item in controllers if _CONTROLLER_PROCESS.match(item)}
    return next(iter(processes)) if len(processes) == 1 else None


def build_target_process_authority(*, scenario_authority: Mapping[str, Any], decision_hash: str) -> dict[str, Any]:
    if scenario_authority.get("self_hash") != "34c53aef62a248a4d384083f187e47a4854df045d762533a4b8939fe54c707fb":
        raise ValueError("HAI22_SCENARIO_AUTHORITY_BINDING_REQUIRED")
    if len(decision_hash) != 64:
        raise ValueError("DEC036_HASH_REQUIRED")
    raw_to_controllers: dict[str, set[str]] = {}
    for scenario in scenario_authority.get("canonical_records", []):
        targets = scenario.get("attacked_identities", [])
        controllers = scenario.get("target_controller_components", [])
        if len(targets) != len(controllers):
            raise ValueError("HAI22_TARGET_CONTROLLER_ROW_BINDING_INCOMPLETE")
        for target, controller in zip(targets, controllers):
            raw_to_controllers.setdefault(target, set()).add(controller)
    records: list[dict[str, Any]] = []
    for target in sorted(raw_to_controllers):
        controllers = sorted(raw_to_controllers[target])
        process = _source_rooted_process(controllers)
        record = {
            "raw_official_target_identity_hash": _token(target),
            "target_namespace": "OTHER_OFFICIAL_HAI22_TARGET_IDENTITY",
            "canonical_hai_feature_identity": None,
            "official_controller_identity_hashes": [_token(item) for item in controllers],
            "official_process_membership": process or "UNRESOLVED",
            "source_artifact": "hai_dataset_technical_details.pdf",
            "source_sha256": MANUAL_HASH,
            "evidence_type": "OFFICIAL_HAI22_MANUAL_TARGET_CONTROLLER_COLUMN_ROW_BINDING" if process else "OFFICIAL_HAI22_CONTROLLER_MEMBERSHIP_CONFLICT",
            "mapping_rule": "HAI22_MANUAL_ROW_BOUND_TARGET_CONTROLLER_PROCESS_MEMBERSHIP_NO_TARGET_ALIAS" if process else "UNRESOLVED_WHEN_A_RAW_TARGET_HAS_NONUNIQUE_OFFICIAL_CONTROLLER_PROCESS_MEMBERSHIP",
            "heuristic_alias": False,
        }
        record["record_hash"] = digest(record)
        records.append(record)
    if not records:
        raise ValueError("HAI22_TARGET_PROCESS_RECORDS_REQUIRED")
    return self_hashed({
        "schema": "hai22_official_direct_target_process_authority_v1",
        "decision_id": DECISION_ID,
        "decision_hash": decision_hash,
        "scenario_authority_sha256": scenario_authority["self_hash"],
        "historical_predecessor": {"authority_id": "FULL_PROCESS_SCOPE_AUTHORITY_V1", "authority_sha256": V1_SCOPE_HASH},
        "official_source_roots": {"technical_manual_sha256": MANUAL_HASH},
        "records": records,
        "forbidden": ["CASE_NORMALIZATION_ALIAS", "UNDERSCORE_OR_DASH_ALIAS", "PREFIX_OR_SUBSTRING_TARGET_INFERENCE", "EDIT_DISTANCE_MAPPING", "CONTROLLER_INTUITION_WITHOUT_MANUAL_ROW_BINDING", "CANONICAL_FEATURE_FABRICATION"],
    })


def classify_scenarios(*, scenario_authority: Mapping[str, Any], target_authority: Mapping[str, Any], decision_hash: str) -> dict[str, Any]:
    if target_authority.get("decision_hash") != decision_hash or target_authority.get("decision_id") != DECISION_ID:
        raise ValueError("DEC036_TARGET_AUTHORITY_BINDING_REQUIRED")
    process_by_target = {record["raw_official_target_identity_hash"]: record["official_process_membership"] for record in target_authority["records"]}
    decisions: list[dict[str, Any]] = []
    for scenario in scenario_authority["canonical_records"]:
        memberships = [process_by_target.get(_token(target), "UNRESOLVED") for target in scenario["attacked_identities"]]
        status = "P1_ELIGIBLE" if "P1" in memberships else ("UNRESOLVED" if "UNRESOLVED" in memberships else "P1_NOT_ELIGIBLE")
        decisions.append({"scenario_id": scenario["scenario_id"], "primary_status": status, "membership_count": len(memberships)})
    return self_hashed({
        "schema": "hai22_p1_direct_target_eligibility_authority_v2",
        "decision_id": DECISION_ID,
        "decision_hash": decision_hash,
        "scenario_authority_sha256": scenario_authority["self_hash"],
        "target_process_authority_sha256": target_authority["self_hash"],
        "multi_target_aggregation": "ANY_VERIFIED_P1_DIRECT_TARGET",
        "unknown_handling": "UNRESOLVED_UNLESS_ANY_VERIFIED_P1_DIRECT_TARGET",
        "decisions": decisions,
    })
