"""Prospective HAI23 direct-target P1 denominator authority (V2).

V2 deliberately leaves ``FULL_PROCESS_SCOPE_AUTHORITY_V1`` intact.  It models
the distinct question introduced by DEC-034: whether an *official direct
attack target* is proven by source metadata to belong to physical process P1.
No target text is normalized, aliased, or converted into a HAI feature.
"""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence


class P1DirectTargetScopeV2Error(ValueError):
    """A malformed, heuristic, or insufficient V2 authority."""


V1_SCOPE_ID = "FULL_PROCESS_SCOPE_AUTHORITY_V1"
V1_SCOPE_HASH = "0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619"
DECISION_ID = "DEC-034"
DECISION_HASH = "67a724b3b433d2b21904d587a1ce357090021dc654f212e667e0dd7a79c45ccd"
MANUAL_HASH = "0668345c4e80331b918fe17c81f8f363b13bd22886831d286e761bc62b71a556"
OFFICIAL_REPOSITORY_COMMIT = "2a814cebc9a66b06c9e5cd545e2d72e65d383737"
PROCESS_MEMBERSHIP_EVIDENCE = "OFFICIAL_HAI23_ATTACK_OPERATION_BOILER_DCS_SCOPE"
PROCESS_MEMBERSHIP_RULE = "OFFICIAL_MANUAL_PAGE_32_BOILER_DCS_ATTACK_SCOPE_PLUS_PAGE_5_P1_BOILER_DEFINITION"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: Any) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def self_hashed(value: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(value)
    body.pop("self_hash", None)
    return {**body, "self_hash": digest(body)}


def verify_self_hash(value: Mapping[str, Any]) -> None:
    if value.get("self_hash") != digest({key: item for key, item in value.items() if key != "self_hash"}):
        raise P1DirectTargetScopeV2Error("SELF_HASH_MISMATCH")


def _sha(value: str, field: str) -> None:
    if type(value) is not str or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise P1DirectTargetScopeV2Error(f"{field}:SHA256_REQUIRED")


def _target_hash(value: str) -> str:
    if type(value) is not str or not value:
        raise P1DirectTargetScopeV2Error("RAW_OFFICIAL_TARGET_REQUIRED")
    return sha256(value.encode("utf-8")).hexdigest()


def build_target_process_authority(
    *,
    raw_targets: Iterable[str],
    canonical_hai23_identities: Iterable[str],
    target_controllers: Mapping[str, Sequence[str]],
    decision_hash: str,
    source_commit: str,
) -> dict[str, Any]:
    """Build source-rooted process evidence without alias construction.

    The HAI23 technical manual explicitly confines its HAIEnd attack operation
    to the boiler-control DCS, while separately defining the boiler as P1.
    This applies to each direct target recorded in the exact A201--A238 manual
    block, including targets outside the frozen HAI feature namespace.
    """
    _sha(decision_hash, "decision_hash")
    if decision_hash != DECISION_HASH:
        raise P1DirectTargetScopeV2Error("DECISION_HASH_BINDING_REQUIRED")
    canonical = set(canonical_hai23_identities)
    targets = sorted(set(raw_targets))
    if not targets:
        raise P1DirectTargetScopeV2Error("TARGET_SET_REQUIRED")
    records: list[dict[str, Any]] = []
    for raw in targets:
        raw_hash = _target_hash(raw)
        is_canonical = raw in canonical
        controllers = target_controllers.get(raw, ())
        if not controllers:
            raise P1DirectTargetScopeV2Error("OFFICIAL_TARGET_CONTROLLER_EVIDENCE_REQUIRED")
        record = {
            "raw_official_target_identity_hash": raw_hash,
            "target_namespace": "HAI_CANONICAL_FEATURE" if is_canonical else "OTHER_OFFICIAL_HAI_TARGET_IDENTITY",
            "canonical_hai_feature_identity": raw if is_canonical else None,
            "official_controller_identity_hashes": sorted({_target_hash(controller) for controller in controllers}),
            "official_process_membership": "P1",
            "source_artifact": "hai_dataset_technical_details.pdf",
            "source_sha256": MANUAL_HASH,
            "evidence_type": PROCESS_MEMBERSHIP_EVIDENCE,
            "mapping_rule": PROCESS_MEMBERSHIP_RULE,
            "heuristic_alias": False,
        }
        record["record_hash"] = digest(record)
        records.append(record)
    return self_hashed(
        {
            "schema": "hai23_official_direct_target_process_authority_v1",
            "decision_id": DECISION_ID,
            "decision_hash": decision_hash,
            "source_commit": source_commit,
            "historical_predecessor": {"authority_id": V1_SCOPE_ID, "authority_sha256": V1_SCOPE_HASH},
            "official_source_roots": {
                "technical_manual_sha256": MANUAL_HASH,
                "process_membership_evidence": PROCESS_MEMBERSHIP_EVIDENCE,
                "process_membership_rule": PROCESS_MEMBERSHIP_RULE,
            },
            "records": records,
            "forbidden": [
                "CASE_NORMALIZATION_ALIAS",
                "UNDERSCORE_OR_DASH_ALIAS",
                "PREFIX_OR_SUBSTRING_INFERENCE",
                "EDIT_DISTANCE_MAPPING",
                "CONTROLLER_STRING_INFERENCE_WITHOUT_AUTHORITY",
                "CANONICAL_FEATURE_FABRICATION",
            ],
        }
    )


def validate_target_process_authority(value: Mapping[str, Any]) -> None:
    verify_self_hash(value)
    if value.get("schema") != "hai23_official_direct_target_process_authority_v1":
        raise P1DirectTargetScopeV2Error("TARGET_AUTHORITY_SCHEMA_REQUIRED")
    if value.get("decision_id") != DECISION_ID:
        raise P1DirectTargetScopeV2Error("DECISION_BINDING_REQUIRED")
    if value.get("decision_hash") != DECISION_HASH or value.get("source_commit") != OFFICIAL_REPOSITORY_COMMIT:
        raise P1DirectTargetScopeV2Error("OFFICIAL_DECISION_OR_SOURCE_BINDING_REQUIRED")
    predecessor = value.get("historical_predecessor")
    if predecessor != {"authority_id": V1_SCOPE_ID, "authority_sha256": V1_SCOPE_HASH}:
        raise P1DirectTargetScopeV2Error("HISTORICAL_V1_BINDING_REQUIRED")
    seen: set[str] = set()
    for record in value.get("records", []):
        raw_hash = record.get("raw_official_target_identity_hash")
        _sha(raw_hash, "raw_official_target_identity_hash")
        if raw_hash in seen:
            raise P1DirectTargetScopeV2Error("DUPLICATE_TARGET_IDENTITY")
        seen.add(raw_hash)
        if record.get("target_namespace") not in {"HAI_CANONICAL_FEATURE", "OTHER_OFFICIAL_HAI_TARGET_IDENTITY"}:
            raise P1DirectTargetScopeV2Error("TARGET_NAMESPACE_REQUIRED")
        canonical = record.get("canonical_hai_feature_identity")
        if record["target_namespace"] == "HAI_CANONICAL_FEATURE" and not canonical:
            raise P1DirectTargetScopeV2Error("CANONICAL_IDENTITY_REQUIRED")
        if record["target_namespace"] != "HAI_CANONICAL_FEATURE" and canonical is not None:
            raise P1DirectTargetScopeV2Error("NONCANONICAL_ALIAS_PROHIBITED")
        controller_hashes = record.get("official_controller_identity_hashes")
        if not isinstance(controller_hashes, list) or not controller_hashes:
            raise P1DirectTargetScopeV2Error("OFFICIAL_CONTROLLER_EVIDENCE_REQUIRED")
        if controller_hashes != sorted(set(controller_hashes)):
            raise P1DirectTargetScopeV2Error("NONCANONICAL_CONTROLLER_SET")
        for controller_hash in controller_hashes:
            _sha(controller_hash, "official_controller_identity_hash")
        if record.get("official_process_membership") != "P1":
            raise P1DirectTargetScopeV2Error("OFFICIAL_P1_MEMBERSHIP_REQUIRED")
        if record.get("source_sha256") != MANUAL_HASH or record.get("evidence_type") != PROCESS_MEMBERSHIP_EVIDENCE:
            raise P1DirectTargetScopeV2Error("OFFICIAL_SOURCE_EVIDENCE_REQUIRED")
        if record.get("mapping_rule") != PROCESS_MEMBERSHIP_RULE or record.get("heuristic_alias") is not False:
            raise P1DirectTargetScopeV2Error("HEURISTIC_ALIAS_PROHIBITED")
        expected = dict(record)
        actual_hash = expected.pop("record_hash", None)
        if actual_hash != digest(expected):
            raise P1DirectTargetScopeV2Error("TARGET_RECORD_HASH_MISMATCH")
    if not seen:
        raise P1DirectTargetScopeV2Error("TARGET_RECORDS_REQUIRED")


def build_scope_authority(*, decision_hash: str, target_process_authority_hash: str) -> dict[str, Any]:
    _sha(decision_hash, "decision_hash")
    if decision_hash != DECISION_HASH:
        raise P1DirectTargetScopeV2Error("DECISION_HASH_BINDING_REQUIRED")
    _sha(target_process_authority_hash, "target_process_authority_hash")
    return self_hashed(
        {
            "schema": "p1_direct_target_process_scope_authority_v2",
            "decision_id": DECISION_ID,
            "decision_hash": decision_hash,
            "effective_scientific_phase": "AFTER_SOURCE_ONLY_HAI23_METADATA_REVIEW_BEFORE_HELDOUT_PERFORMANCE_CONTACT",
            "historical_predecessor": {"authority_id": V1_SCOPE_ID, "authority_sha256": V1_SCOPE_HASH},
            "target_process_authority_sha256": target_process_authority_hash,
            "direct_target_membership_semantic": "AT_LEAST_ONE_DIRECT_OFFICIAL_TARGET_WITH_OFFICIAL_PROCESS_MEMBERSHIP_P1",
            "multi_target_aggregation": "ANY_VERIFIED_P1_DIRECT_TARGET",
            "unknown_handling": "UNRESOLVED_UNLESS_ANY_VERIFIED_P1_DIRECT_TARGET",
            "namespace_rules": "RAW_IDENTITY_AND_CANONICAL_FEATURE_IDENTITY_REMAIN_DISTINCT",
            "forbidden_heuristics": True,
            "access_boundary": {
                "heldout_predictions_observed": 0,
                "heldout_metrics_observed": 0,
                "method_comparisons_observed": 0,
                "result_driven_change": 0,
            },
        }
    )


def validate_scope_authority(value: Mapping[str, Any], target_process_authority_hash: str) -> None:
    verify_self_hash(value)
    _sha(target_process_authority_hash, "target_process_authority_hash")
    if value.get("schema") != "p1_direct_target_process_scope_authority_v2":
        raise P1DirectTargetScopeV2Error("SCOPE_V2_SCHEMA_REQUIRED")
    if value.get("decision_id") != DECISION_ID:
        raise P1DirectTargetScopeV2Error("DECISION_BINDING_REQUIRED")
    if value.get("decision_hash") != DECISION_HASH:
        raise P1DirectTargetScopeV2Error("DECISION_HASH_BINDING_REQUIRED")
    if value.get("historical_predecessor") != {"authority_id": V1_SCOPE_ID, "authority_sha256": V1_SCOPE_HASH}:
        raise P1DirectTargetScopeV2Error("HISTORICAL_V1_BINDING_REQUIRED")
    if value.get("target_process_authority_sha256") != target_process_authority_hash:
        raise P1DirectTargetScopeV2Error("TARGET_PROCESS_AUTHORITY_BINDING_REQUIRED")
    if value.get("multi_target_aggregation") != "ANY_VERIFIED_P1_DIRECT_TARGET":
        raise P1DirectTargetScopeV2Error("ANY_AGGREGATION_REQUIRED")
    if value.get("unknown_handling") != "UNRESOLVED_UNLESS_ANY_VERIFIED_P1_DIRECT_TARGET":
        raise P1DirectTargetScopeV2Error("UNKNOWN_HANDLING_REQUIRED")
    if value.get("forbidden_heuristics") is not True:
        raise P1DirectTargetScopeV2Error("FORBIDDEN_HEURISTICS_REQUIRED")


def classify_scenario_targets(
    direct_targets: Sequence[str], target_process_authority: Mapping[str, Any], scope_authority: Mapping[str, Any]
) -> str:
    """Apply the frozen ANY rule without converting or guessing identities."""
    validate_target_process_authority(target_process_authority)
    validate_scope_authority(scope_authority, target_process_authority["self_hash"])
    records = {record["raw_official_target_identity_hash"]: record for record in target_process_authority["records"]}
    memberships: list[str] = []
    for raw in direct_targets:
        record = records.get(_target_hash(raw))
        memberships.append(record["official_process_membership"] if record else "UNRESOLVED")
    if "P1" in memberships:
        return "P1_ELIGIBLE"
    if "UNRESOLVED" in memberships:
        return "UNRESOLVED"
    return "P1_NOT_ELIGIBLE"
