"""Canonical Utility Protocol V4 authority closure for TASK-039E3 R2R.

This module is deliberately metadata-only.  It binds the frozen COMMON-42
portfolio to the independently audited normal-only numeric authority without
opening the private registry, HAI data, labels, or attack intervals.  It also
defines fail-closed planning and provenance contracts for a later evaluator;
it does not implement or authorize utility execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any, Mapping

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 import (
    AUTHORITY_VERSION as NUMERIC_AUTHORITY_VERSION,
    CALIBRATION_POLICY_HASH,
    CANONICAL_AUTHORITY_DEFINITION_HASH,
    COMMON42_AUTHORITY_CHECK_HASH,
    EXECUTABLE_EQUIVALENCE_HASH,
    HISTORICAL_E1_HASH,
    HISTORICAL_E1_IDENTITY_RESTORED,
    HISTORICAL_NUMERIC_IDENTITY_RESTORED,
    HISTORICAL_NUMERIC_REGISTRY_HASH,
    NORMAL_INPUT_IDENTITY_SET_HASH,
    T2_UTILITY_SCOPE_AUTHORIZED as NUMERIC_T2_SCOPE_AUTHORIZED,
    UTILITY_NUMERIC_ROLES,
    NormalOnlyAuthorityDefinitionV1,
    build_common42_authority_v1,
    validate_canonical_common42_authority_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v2 import (
    DATASET_MANIFEST_ID,
    INNER_SPLIT_ID,
    OUTER_SPLIT_ID,
    SOURCE_POST_WINDOW,
    SOURCE_PRE_WINDOW,
    TARGET_BASELINE_WINDOW,
    TARGET_RESPONSE_WINDOW,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    FILE_ROW_COUNTS,
    FILE_SPLITS,
    UTILITY_SOURCE_UNIVERSE_V3,
    build_p1_utility_feature_schema_v3,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-PROTOCOL-V4-NORMAL-ONLY-AUTHORITY-REBIND-AND-CANONICAL-CLOSURE"
PROTOCOL_VERSION = "TASK039E3_R2R_UTILITY_PROTOCOL_V4"
SCHEMA_VERSION = "4.0.0"
BASE_COMMIT = "e971c8c8543f49b31aba2a57cf60257d190b76d5"
V3_LINEAGE = "BASE_V1_PLUS_REMEDIATION_V2_PLUS_FINAL_CLOSURE_V3"

UTILITY_MAIN_PORTFOLIO = "COMMON-42"
T2_UTILITY_SCOPE_AUTHORIZED = False
COMMON_RELATION_COUNT = 42
UTILITY_ROLE_COUNT = 10
UTILITY_REFERENCE_COUNT = 420

PRIVATE_REGISTRY_CONTENT_HASH = "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
MATERIALIZED_AUTHORITY_AUDIT_RECEIPT_HASH = "1f319fd7283040a4e866df3ac7d679e896142162084209bf00962947256c2bf1"
MATERIALIZED_AUTHORITY_AUDIT_BUNDLE_HASH = "d2e4b8e9976695c151f83eba49eb89e2cb5193b4381dd51913026b819ebc5b13"
MATERIALIZED_INDEPENDENT_AUDIT_HASH = "7e7f9a776d92bac40b6f9647823d1c193a4b767048c4cb6cabba1ab60d76185a"
MATERIALIZED_IDENTITY_AUDIT_HASH = "8b1bfe945ce056bd1120d141abf2095c95df1af21f62f853e285040f1c64a45b"
MATERIALIZED_CUSTODY_AUDIT_HASH = "977aa2b46154294eb22f5d54eb9f57312ce3bd7e9fda1592dae3599d67c93b24"
MATERIALIZATION_PUBLIC_RECEIPT_HASH = "3054bf3eaf50bdc4297652a475b3b465e59b449810493ac775fed0bcf7567ced"
LOCAL_LOCATOR_HASH = "b5588c04d08d88d4ee2a2d319708e62d10bc04330baeb7591876f076270e4ac4"

CANONICAL_FEATURE_SCHEMA_HASH = "62fd76bd541437694aff274db865670f24eecbabf3c736f32893bd97081564b8"
CANONICAL_RUNTIME_FEATURE_SCHEMA_HASH = "e7a0c46d28491b9d03a333a0ad1e87d686a982bafba072861913e05fb6c50b58"
NEW_REFERENCE_SET_HASH = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"

CORRECTED_REGRESSION_NUMERIC_REFERENCE_AUTHORITY_HASH = (
    "e50300efd372fb8a5c4567a6fa9e3277e36804506b306ea0053f7fc4ab48ceed"
)
CORRECTED_EVENT_POLICY_HASH = "6e4a4467953c5c9bf973a0a8a18950669dc902310407b7b354128ad91febb2f4"
CORRECTED_METRIC_POLICY_HASH = "4c7b6cfdb6b3889e56e7151be60b92a7e6f46ce0135de0ed65ebf3207a7b0d6a"
HISTORICAL_WRONG_REGRESSION_HASHES = (
    "e50300ef65ae8ab71631c00125fe6d694397714daf220a3a3a7df79115ce68bb",
    "6e4a446743cbd8c69cd93b9ccbd660b1f4e30f63f75575d37dd57bb6ab4c8250",
    "4c7b6cfd2c18ddc5a6ca5b13285fc2acb67e4bda43fd8436dbb1e302164a1da0",
)

V3_FOCUSED_AUDIT_HASHES = {
    "opportunity": "04a2aed36e7aa90810612b0dcaaade3d2464b77cc8d5754efbb6f74aa4acfae3",
    "feature_authority": "dee0fed8a8f1202ab6206aba96317c14b5b2c49e08f312c3732de2d480e61bf0",
    "type_policy": "023d7024a3fa95b913ae17a51c2fe9fdd561968787d5491e386c43ce736117f6",
    "regression": "91daf11c621790d846d480945dc80eb67bfb3835648a683e7ce94f062c359c42",
}

BLOCKER_CLOSURES = (
    ("BLOCKER_V3_T2_EXACT_PORTFOLIO_MEMBERSHIP_UNBOUND", "CLOSED_BY_EXPLICIT_SCOPE_EXCLUSION"),
    ("BLOCKER_V3_OPPORTUNITY_RECORD_SEMANTIC_IDENTITY_UNCHECKED", "CLOSED_BY_V4_CANONICAL_SEMANTIC_REPLAY"),
    ("BLOCKER_V3_FULL_CENSUS_NUMERIC_REFERENCE_AUTHORITY_UNBOUND", "CLOSED_BY_AUDITED_V1_420_REFERENCE_AUTHORITY"),
    ("BLOCKER_V3_CANONICAL_FULL_CENSUS_PROVENANCE_BYPASS", "CLOSED_BY_V4_CANONICAL_FULL_CENSUS_PLAN"),
    ("BLOCKER_V3_SERIALIZED_FEATURE_SCHEMA_AUTHORITY_SUBSTITUTION", "CLOSED_BY_V4_COMMITTED_METADATA_REPLAY"),
    ("BLOCKER_V3_CANONICAL_SCALAR_TYPE_POLICY_NOT_ENFORCED", "CLOSED_BY_V4_EXACT_SCALAR_TYPES"),
    ("BLOCKER_V3_TARGET_TERMINAL_STATE_PROVENANCE_UNBOUND", "CLOSED_BY_V4_PARENT_CHAIN_TRANSITIONS"),
    ("BLOCKER_V3_REGRESSION_COMPONENT_AUTHORITY_HASH_MISMATCH", "CLOSED_BY_CORRECTED_AUTHORITY_HASH_BINDING"),
)

OPPORTUNITY_ENUMERATION_POLICY = {
    "policy_version": "TASK039E3_V4_FULL_CENSUS_ENUMERATION_V1",
    "sampling": "FULL_CENSUS_NO_FIXED_SAMPLE_SIZE",
    "source_event_coverage": "ALL_AUTOMATICALLY_ENUMERATED_APPLICABLE_EVENTS",
    "relation_scope": UTILITY_MAIN_PORTFOLIO,
    "caller_opportunity_list_authorized": False,
    "caller_sample_size_authorized": False,
    "caller_denominator_authorized": False,
}
OPPORTUNITY_ENUMERATION_POLICY_HASH = stable_hash_v1(OPPORTUNITY_ENUMERATION_POLICY)
SOURCE_UNIVERSE_POLICY_HASH = stable_hash_v1(
    {
        "policy_version": "TASK039E3_V4_SOURCE_UNIVERSE_POLICY_V1",
        "evaluator_sources": list(UTILITY_SOURCE_UNIVERSE_V3),
        "evaluator_source_count": 12,
        "common_materialization_scope_is_separate": True,
    }
)
BOUNDARY_WINDOW_POLICY_HASH = stable_hash_v1(
    {
        "policy_version": "TASK039E3_V4_BOUNDARY_WINDOW_POLICY_V1",
        "source_pre_window_seconds": SOURCE_PRE_WINDOW,
        "source_post_window_seconds": SOURCE_POST_WINDOW,
        "target_baseline_window_seconds": TARGET_BASELINE_WINDOW,
        "target_response_window_seconds": TARGET_RESPONSE_WINDOW,
        "target_boundary_precedence": [
            "file_boundary",
            "split_boundary",
            "incomplete_target_response_window",
        ],
    }
)
PURGE_POLICY_HASH = stable_hash_v1(
    {
        "policy_version": "TASK039E3_V4_VIRTUAL_PURGE_POLICY_V1",
        "purge_seconds": 120,
        "inner_file": "hai-test1.csv",
        "outer_file": "hai-test2.csv",
    }
)
STRICT_SCALAR_POLICY_HASH = stable_hash_v1(
    {
        "policy_version": "TASK039E3_V4_STRICT_SCALAR_POLICY_V1",
        "integer": "type(value) is int",
        "boolean": "type(value) is bool",
        "float": "type(value) is float and finite",
        "string": "type(value) is str",
        "tuple": "type(value) is tuple",
        "silent_coercion": False,
    }
)
TERMINAL_TRANSITION_POLICY_HASH = stable_hash_v1(
    {
        "policy_version": "TASK039E3_V4_TARGET_TERMINAL_TRANSITION_V1",
        "parent_chain": [
            "CanonicalOpportunityV4",
            "SourceQualificationStateV4",
            "TargetEvaluationStateV4",
        ],
        "terminal_states": [
            "evaluated_expected_response",
            "evaluated_anomaly",
            "abstain",
        ],
        "malformed_input_is_abstention": False,
    }
)
COMPARISON_POLICY_HASH = stable_hash_v1(
    {
        "policy_version": "TASK039E3_V4_D0_D1_D2_COMPARISON_V1",
        "D0": "detector_only",
        "D1": "COMMON_42_verified_rule_only",
        "D2": "detector_plus_same_COMMON_42_verified_rule",
        "same_numeric_authority_for_D1_D2": True,
        "weighted_winner": False,
    }
)

CANONICAL_V4_AUTHORITY_HASH = "2864c99017dcea576437efe9f9c5d531cc0d7810504cb2bd8e8585643d2fa0a1"


class UtilityProtocolV4Error(ValueError):
    """A fail-closed V4 authority, schema, type, or provenance violation."""


def _strict_str(value: object, name: str, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        raise UtilityProtocolV4Error(f"{name} must be an exact string")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise UtilityProtocolV4Error(f"{name} must be an exact boolean")
    return value


def _strict_int(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise UtilityProtocolV4Error(f"{name} must be an exact integer at least {minimum}")
    return value


def _strict_float(value: object, name: str, *, positive: bool = False) -> float:
    if type(value) is not float or not math.isfinite(value) or (positive and value <= 0.0):
        raise UtilityProtocolV4Error(f"{name} must be an exact finite float")
    return value


def _strict_tuple(value: object, name: str) -> tuple[Any, ...]:
    if type(value) is not tuple:
        raise UtilityProtocolV4Error(f"{name} must be an exact tuple")
    return value


def _sha(value: object, name: str) -> str:
    result = _strict_str(value, name)
    if len(result) != 64 or result != result.lower():
        raise UtilityProtocolV4Error(f"{name} must be a SHA-256 identity")
    try:
        int(result, 16)
    except ValueError as exc:
        raise UtilityProtocolV4Error(f"{name} must be hexadecimal") from exc
    return result


def _numeric_reference(value: object, name: str = "numeric reference") -> str:
    result = _strict_str(value, name)
    prefix = f"{NUMERIC_AUTHORITY_VERSION}:"
    if not result.startswith(prefix):
        raise UtilityProtocolV4Error(f"{name} must use the new V1 namespace")
    _sha(result[len(prefix):], name)
    return result


def _verify_exact_self_hash(
    document: Mapping[str, Any], expected_hash: str, *, key: str = "artifact_hash"
) -> str:
    if type(document) is not dict:
        raise UtilityProtocolV4Error("authority document must be an exact dictionary")
    observed = _sha(document.get(key), key)
    payload = {name: value for name, value in document.items() if name != key}
    if stable_hash_v1(payload) != observed or observed != expected_hash:
        raise UtilityProtocolV4Error("authority document self-hash or frozen identity differs")
    return observed


def validate_materialized_authority_audit_receipt_v4(
    receipt: Mapping[str, Any],
) -> str:
    """Validate the exact public PASS receipt without touching private custody."""

    observed = _verify_exact_self_hash(receipt, MATERIALIZED_AUTHORITY_AUDIT_RECEIPT_HASH)
    if (
        receipt.get("status")
        != "passed_task039e3_r2r_utility_normal_only_authority_v1_materialized_independent_audit"
        or receipt.get("bundle_hash") != MATERIALIZED_AUTHORITY_AUDIT_BUNDLE_HASH
        or receipt.get("independent_audit_hash") != MATERIALIZED_INDEPENDENT_AUDIT_HASH
        or receipt.get("identity_audit_hash") != MATERIALIZED_IDENTITY_AUDIT_HASH
        or receipt.get("custody_audit_hash") != MATERIALIZED_CUSTODY_AUDIT_HASH
        or receipt.get("private_registry_hash") != PRIVATE_REGISTRY_CONTENT_HASH
        or receipt.get("public_receipt_hash") != MATERIALIZATION_PUBLIC_RECEIPT_HASH
        or receipt.get("remaining_blockers") != []
    ):
        raise UtilityProtocolV4Error("materialized authority audit lineage differs")
    for name in (
        "normal_only_authority_protocol_audited",
        "normal_only_authority_materialized",
        "normal_only_authority_materialization_audited",
    ):
        if _strict_bool(receipt.get(name), name) is not True:
            raise UtilityProtocolV4Error("materialized authority audit state is not PASS")
    return observed


def build_common42_public_authority_v4(
    executable_equivalence: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
) -> NormalOnlyAuthorityDefinitionV1:
    authority = build_common42_authority_v1(executable_equivalence, evidence_manifest)
    if validate_canonical_common42_authority_v1(authority) != CANONICAL_AUTHORITY_DEFINITION_HASH:
        raise UtilityProtocolV4Error("COMMON-42 authority replay differs")
    if len(authority.relations) != COMMON_RELATION_COUNT or len(authority.reference_identities) != UTILITY_REFERENCE_COUNT:
        raise UtilityProtocolV4Error("COMMON-42 or reference cardinality differs")
    return authority


@dataclass(frozen=True)
class NumericAuthorityDescriptorV4:
    authority_version: str
    private_registry_content_hash: str
    materialized_authority_audit_receipt_hash: str
    authority_definition_hash: str
    calibration_policy_hash: str
    common42_authority_hash: str
    common_executable_equivalence_hash: str
    normal_input_identity_set_hash: str
    new_reference_set_hash: str
    record_count: int
    reference_count: int
    relation_count: int
    role_count: int
    historical_e1_identity_restored: bool
    historical_numeric_identity_restored: bool
    t2_utility_scope_authorized: bool

    def __post_init__(self) -> None:
        _strict_str(self.authority_version, "authority_version")
        for name in (
            "private_registry_content_hash",
            "materialized_authority_audit_receipt_hash",
            "authority_definition_hash",
            "calibration_policy_hash",
            "common42_authority_hash",
            "common_executable_equivalence_hash",
            "normal_input_identity_set_hash",
            "new_reference_set_hash",
        ):
            _sha(getattr(self, name), name)
        for name in ("record_count", "reference_count", "relation_count", "role_count"):
            _strict_int(getattr(self, name), name, minimum=1)
        for name in (
            "historical_e1_identity_restored",
            "historical_numeric_identity_restored",
            "t2_utility_scope_authorized",
        ):
            _strict_bool(getattr(self, name), name)

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_numeric_authority_descriptor",
            "authority_definition_hash": self.authority_definition_hash,
            "authority_version": self.authority_version,
            "calibration_policy_hash": self.calibration_policy_hash,
            "common42_authority_hash": self.common42_authority_hash,
            "common_executable_equivalence_hash": self.common_executable_equivalence_hash,
            "historical_e1_identity_restored": self.historical_e1_identity_restored,
            "historical_numeric_identity_restored": self.historical_numeric_identity_restored,
            "materialized_authority_audit_receipt_hash": self.materialized_authority_audit_receipt_hash,
            "new_reference_set_hash": self.new_reference_set_hash,
            "normal_input_identity_set_hash": self.normal_input_identity_set_hash,
            "private_registry_content_hash": self.private_registry_content_hash,
            "record_count": self.record_count,
            "reference_count": self.reference_count,
            "relation_count": self.relation_count,
            "role_count": self.role_count,
            "schema_version": SCHEMA_VERSION,
            "t2_utility_scope_authorized": self.t2_utility_scope_authorized,
        }

    @property
    def descriptor_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "descriptor_hash": self.descriptor_hash}


def build_numeric_authority_descriptor_v4(
    common_authority: NormalOnlyAuthorityDefinitionV1,
    materialized_audit_receipt: Mapping[str, Any],
) -> NumericAuthorityDescriptorV4:
    validate_materialized_authority_audit_receipt_v4(materialized_audit_receipt)
    validate_canonical_common42_authority_v1(common_authority)
    reference_set_hash = stable_hash_v1(
        {
            "authority_version": NUMERIC_AUTHORITY_VERSION,
            "reference_count": len(common_authority.reference_identities),
            "reference_identities": sorted(common_authority.reference_identities),
        }
    )
    if reference_set_hash != NEW_REFERENCE_SET_HASH:
        raise UtilityProtocolV4Error("new 420-reference set identity differs")
    descriptor = NumericAuthorityDescriptorV4(
        NUMERIC_AUTHORITY_VERSION,
        PRIVATE_REGISTRY_CONTENT_HASH,
        MATERIALIZED_AUTHORITY_AUDIT_RECEIPT_HASH,
        CANONICAL_AUTHORITY_DEFINITION_HASH,
        CALIBRATION_POLICY_HASH,
        COMMON42_AUTHORITY_CHECK_HASH,
        EXECUTABLE_EQUIVALENCE_HASH,
        NORMAL_INPUT_IDENTITY_SET_HASH,
        NEW_REFERENCE_SET_HASH,
        420,
        420,
        42,
        10,
        False,
        False,
        False,
    )
    if descriptor.private_registry_content_hash in {HISTORICAL_E1_HASH, HISTORICAL_NUMERIC_REGISTRY_HASH}:
        raise UtilityProtocolV4Error("historical authority substitution is prohibited")
    return descriptor


def validate_numeric_authority_descriptor_v4(
    descriptor: NumericAuthorityDescriptorV4,
    common_authority: NormalOnlyAuthorityDefinitionV1,
    materialized_audit_receipt: Mapping[str, Any],
) -> str:
    if type(descriptor) is not NumericAuthorityDescriptorV4:
        raise UtilityProtocolV4Error("numeric authority descriptor type differs")
    expected = build_numeric_authority_descriptor_v4(common_authority, materialized_audit_receipt)
    if descriptor != expected or descriptor.to_dict() != expected.to_dict():
        raise UtilityProtocolV4Error("numeric authority descriptor is not canonical")
    return descriptor.descriptor_hash


@dataclass(frozen=True)
class CanonicalRuleDescriptorV4:
    relation_identity: str
    relation_binding_hash: str
    semantic_execution_hash: str
    source: str
    target: str
    source_direction: str
    target_direction: str
    selected_horizon_seconds: int
    numeric_reference_bindings: tuple[tuple[str, str], ...]
    numeric_authority_descriptor_hash: str

    def __post_init__(self) -> None:
        _strict_str(self.relation_identity, "relation_identity")
        _sha(self.relation_binding_hash, "relation_binding_hash")
        _sha(self.semantic_execution_hash, "semantic_execution_hash")
        _strict_str(self.source, "source")
        _strict_str(self.target, "target")
        if self.source_direction not in {"step_up", "step_down"}:
            raise UtilityProtocolV4Error("source direction differs")
        if self.target_direction not in {"increase", "decrease"}:
            raise UtilityProtocolV4Error("target direction differs")
        if _strict_int(self.selected_horizon_seconds, "selected_horizon_seconds", minimum=1) not in {1, 5, 10, 30, 60}:
            raise UtilityProtocolV4Error("selected horizon differs")
        bindings = _strict_tuple(self.numeric_reference_bindings, "numeric_reference_bindings")
        if len(bindings) != UTILITY_ROLE_COUNT or tuple(role for role, _ in bindings) != UTILITY_NUMERIC_ROLES:
            raise UtilityProtocolV4Error("numeric reference roles differ")
        if len({_numeric_reference(reference) for _, reference in bindings}) != UTILITY_ROLE_COUNT:
            raise UtilityProtocolV4Error("numeric references duplicate")
        _sha(self.numeric_authority_descriptor_hash, "numeric_authority_descriptor_hash")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_rule_descriptor",
            "numeric_authority_descriptor_hash": self.numeric_authority_descriptor_hash,
            "numeric_reference_bindings": [
                {"numeric_role": role, "reference_identity": reference}
                for role, reference in self.numeric_reference_bindings
            ],
            "relation_binding_hash": self.relation_binding_hash,
            "relation_identity": self.relation_identity,
            "schema_version": SCHEMA_VERSION,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "semantic_execution_hash": self.semantic_execution_hash,
            "source": self.source,
            "source_direction": self.source_direction,
            "target": self.target,
            "target_direction": self.target_direction,
        }

    @property
    def descriptor_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "descriptor_hash": self.descriptor_hash}

    def reference_for(self, role: str) -> str:
        matches = [reference for observed, reference in self.numeric_reference_bindings if observed == role]
        if len(matches) != 1:
            raise UtilityProtocolV4Error("rule numeric reference role differs")
        return matches[0]


def build_canonical_rule_descriptors_v4(
    common_authority: NormalOnlyAuthorityDefinitionV1,
    numeric_authority: NumericAuthorityDescriptorV4,
) -> tuple[CanonicalRuleDescriptorV4, ...]:
    validate_canonical_common42_authority_v1(common_authority)
    if numeric_authority.authority_definition_hash != common_authority.authority_definition_hash:
        raise UtilityProtocolV4Error("numeric and COMMON authority definitions differ")
    references = iter(common_authority.reference_identities)
    result = tuple(
        CanonicalRuleDescriptorV4(
            relation.relation_identity,
            relation.relation_binding_hash,
            relation.semantic_execution_hash,
            relation.source,
            relation.target,
            relation.source_direction,
            relation.target_direction,
            relation.selected_horizon_seconds,
            tuple((role, next(references)) for role in UTILITY_NUMERIC_ROLES),
            numeric_authority.descriptor_hash,
        )
        for relation in common_authority.relations
    )
    try:
        next(references)
    except StopIteration:
        pass
    else:
        raise UtilityProtocolV4Error("numeric reference iterator has unexpected entries")
    if len(result) != 42 or len({item.descriptor_hash for item in result}) != 42:
        raise UtilityProtocolV4Error("canonical rule descriptor closure differs")
    return result


def validate_canonical_rule_descriptors_v4(
    descriptors: tuple[CanonicalRuleDescriptorV4, ...],
    common_authority: NormalOnlyAuthorityDefinitionV1,
    numeric_authority: NumericAuthorityDescriptorV4,
) -> str:
    if type(descriptors) is not tuple:
        raise UtilityProtocolV4Error("rule descriptors must be a canonical tuple")
    expected = build_canonical_rule_descriptors_v4(common_authority, numeric_authority)
    if descriptors != expected:
        raise UtilityProtocolV4Error("rule descriptors differ from canonical COMMON replay")
    return stable_hash_v1(
        {
            "portfolio_identity": UTILITY_MAIN_PORTFOLIO,
            "rule_descriptor_hashes": [item.descriptor_hash for item in descriptors],
        }
    )


def validate_canonical_rule_descriptor_v4(
    descriptor: CanonicalRuleDescriptorV4,
    authority: "UtilityProtocolV4CanonicalAuthority",
) -> str:
    validate_utility_protocol_v4_authority(authority)
    if type(descriptor) is not CanonicalRuleDescriptorV4:
        raise UtilityProtocolV4Error("canonical rule descriptor type differs")
    expected = authority.rule_by_binding(descriptor.relation_binding_hash)
    if descriptor != expected or descriptor.to_dict() != expected.to_dict():
        raise UtilityProtocolV4Error("canonical rule descriptor replay differs")
    return descriptor.descriptor_hash


@dataclass(frozen=True)
class CanonicalFeatureSchemaV4:
    canonical_v3_schema_report_hash: str
    canonical_runtime_schema_hash: str
    source_features: tuple[str, ...]
    target_features: tuple[str, ...]
    union_features: tuple[str, ...]
    common_source_footprint: tuple[str, ...]
    common_target_footprint: tuple[str, ...]
    common_feature_footprint: tuple[str, ...]
    metadata_authorities: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _sha(self.canonical_v3_schema_report_hash, "canonical_v3_schema_report_hash")
        _sha(self.canonical_runtime_schema_hash, "canonical_runtime_schema_hash")
        if self.canonical_v3_schema_report_hash != CANONICAL_FEATURE_SCHEMA_HASH:
            raise UtilityProtocolV4Error("canonical feature-schema report identity differs")
        if self.canonical_runtime_schema_hash != CANONICAL_RUNTIME_FEATURE_SCHEMA_HASH:
            raise UtilityProtocolV4Error("canonical runtime feature-schema identity differs")
        for name in (
            "source_features",
            "target_features",
            "union_features",
            "common_source_footprint",
            "common_target_footprint",
            "common_feature_footprint",
            "metadata_authorities",
        ):
            _strict_tuple(getattr(self, name), name)
        if self.source_features != tuple(sorted(set(self.source_features))) or len(self.source_features) != 12:
            raise UtilityProtocolV4Error("V3 source feature authority differs")
        if self.target_features != tuple(sorted(set(self.target_features))) or len(self.target_features) != 10:
            raise UtilityProtocolV4Error("V3 target feature authority differs")
        if self.union_features != tuple(sorted(set(self.source_features) | set(self.target_features))) or len(self.union_features) != 22:
            raise UtilityProtocolV4Error("V3 evaluator union differs")
        if not set(self.common_source_footprint) <= set(self.source_features):
            raise UtilityProtocolV4Error("COMMON source footprint escapes evaluator schema")
        if self.common_target_footprint != self.target_features:
            raise UtilityProtocolV4Error("COMMON target footprint differs from evaluator targets")
        if self.common_feature_footprint != tuple(sorted(set(self.common_source_footprint) | set(self.common_target_footprint))):
            raise UtilityProtocolV4Error("COMMON feature footprint differs")
        if (len(self.common_source_footprint), len(self.common_target_footprint), len(self.common_feature_footprint)) != (9, 10, 19):
            raise UtilityProtocolV4Error("COMMON materialization footprint differs")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_feature_schema_authority",
            "canonical_runtime_schema_hash": self.canonical_runtime_schema_hash,
            "canonical_v3_schema_report_hash": self.canonical_v3_schema_report_hash,
            "common_feature_footprint": list(self.common_feature_footprint),
            "common_source_footprint": list(self.common_source_footprint),
            "common_target_footprint": list(self.common_target_footprint),
            "metadata_authorities": dict(self.metadata_authorities),
            "schema_version": SCHEMA_VERSION,
            "source_features": list(self.source_features),
            "target_features": list(self.target_features),
            "union_features": list(self.union_features),
        }

    @property
    def authority_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "authority_hash": self.authority_hash}


def build_canonical_feature_schema_v4(
    *,
    dataset_manifest: Mapping[str, Any],
    csv_structure_report: Mapping[str, Any],
    c0_config: Mapping[str, Any],
    br2_config: Mapping[str, Any],
    executable_equivalence: Mapping[str, Any],
    common_authority: NormalOnlyAuthorityDefinitionV1,
) -> CanonicalFeatureSchemaV4:
    v3 = build_p1_utility_feature_schema_v3(
        dataset_manifest=dataset_manifest,
        csv_structure_report=csv_structure_report,
        c0_config=c0_config,
        br2_config=br2_config,
        executable_equivalence=executable_equivalence,
    )
    if v3.artifact_hash != CANONICAL_RUNTIME_FEATURE_SCHEMA_HASH:
        raise UtilityProtocolV4Error("committed V3 feature-schema replay differs")
    sources = tuple(
        sorted(entry.feature_name for entry in v3.feature_entries if entry.role in {"source", "source_and_target"})
    )
    targets = tuple(
        sorted(entry.feature_name for entry in v3.feature_entries if entry.role in {"target", "source_and_target"})
    )
    common_sources = tuple(sorted({relation.source for relation in common_authority.relations}))
    common_targets = tuple(sorted({relation.target for relation in common_authority.relations}))
    return CanonicalFeatureSchemaV4(
        CANONICAL_FEATURE_SCHEMA_HASH,
        v3.artifact_hash,
        sources,
        targets,
        tuple(sorted(set(sources) | set(targets))),
        common_sources,
        common_targets,
        tuple(sorted(set(common_sources) | set(common_targets))),
        tuple(sorted((str(key), str(value)) for key, value in v3.metadata_authorities.items())),
    )


def validate_canonical_feature_schema_v4(
    schema: CanonicalFeatureSchemaV4,
    *,
    dataset_manifest: Mapping[str, Any],
    csv_structure_report: Mapping[str, Any],
    c0_config: Mapping[str, Any],
    br2_config: Mapping[str, Any],
    executable_equivalence: Mapping[str, Any],
    common_authority: NormalOnlyAuthorityDefinitionV1,
) -> str:
    if type(schema) is not CanonicalFeatureSchemaV4:
        raise UtilityProtocolV4Error("feature schema authority type differs")
    expected = build_canonical_feature_schema_v4(
        dataset_manifest=dataset_manifest,
        csv_structure_report=csv_structure_report,
        c0_config=c0_config,
        br2_config=br2_config,
        executable_equivalence=executable_equivalence,
        common_authority=common_authority,
    )
    if schema != expected:
        raise UtilityProtocolV4Error("serialized feature schema substitution rejected")
    return schema.authority_hash


@dataclass(frozen=True)
class CanonicalFullCensusPlanV4:
    portfolio_identity: str
    common_portfolio_hash: str
    rule_descriptor_hashes: tuple[str, ...]
    numeric_authority_descriptor_hash: str
    feature_schema_authority_hash: str
    dataset_manifest_identity: str
    inner_split_identity: str
    outer_split_identity: str
    opportunity_enumeration_policy_hash: str
    event_policy_hash: str
    metric_policy_hash: str
    source_universe_policy_hash: str
    boundary_window_policy_hash: str
    purge_policy_hash: str

    def __post_init__(self) -> None:
        if self.portfolio_identity != UTILITY_MAIN_PORTFOLIO:
            raise UtilityProtocolV4Error("only COMMON-42 is authorized")
        for name in (
            "common_portfolio_hash",
            "numeric_authority_descriptor_hash",
            "feature_schema_authority_hash",
            "dataset_manifest_identity",
            "inner_split_identity",
            "outer_split_identity",
            "opportunity_enumeration_policy_hash",
            "event_policy_hash",
            "metric_policy_hash",
            "source_universe_policy_hash",
            "boundary_window_policy_hash",
            "purge_policy_hash",
        ):
            _sha(getattr(self, name), name)
        hashes = _strict_tuple(self.rule_descriptor_hashes, "rule_descriptor_hashes")
        if len(hashes) != 42 or len({_sha(value, "rule descriptor hash") for value in hashes}) != 42:
            raise UtilityProtocolV4Error("full census must bind exactly 42 canonical rules")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_canonical_full_census_plan",
            "boundary_window_policy_hash": self.boundary_window_policy_hash,
            "common_portfolio_hash": self.common_portfolio_hash,
            "dataset_manifest_identity": self.dataset_manifest_identity,
            "event_policy_hash": self.event_policy_hash,
            "feature_schema_authority_hash": self.feature_schema_authority_hash,
            "inner_split_identity": self.inner_split_identity,
            "metric_policy_hash": self.metric_policy_hash,
            "numeric_authority_descriptor_hash": self.numeric_authority_descriptor_hash,
            "opportunity_enumeration_policy_hash": self.opportunity_enumeration_policy_hash,
            "outer_split_identity": self.outer_split_identity,
            "portfolio_identity": self.portfolio_identity,
            "purge_policy_hash": self.purge_policy_hash,
            "rule_descriptor_hashes": list(self.rule_descriptor_hashes),
            "schema_version": SCHEMA_VERSION,
            "source_universe_policy_hash": self.source_universe_policy_hash,
        }

    @property
    def plan_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "plan_hash": self.plan_hash}


def build_canonical_full_census_plan_v4(
    numeric_authority: NumericAuthorityDescriptorV4,
    rule_descriptors: tuple[CanonicalRuleDescriptorV4, ...],
    feature_schema: CanonicalFeatureSchemaV4,
) -> CanonicalFullCensusPlanV4:
    if type(rule_descriptors) is not tuple or len(rule_descriptors) != 42:
        raise UtilityProtocolV4Error("canonical full census requires all 42 rules")
    common_portfolio_hash = stable_hash_v1(
        {
            "portfolio_identity": UTILITY_MAIN_PORTFOLIO,
            "rule_descriptor_hashes": [item.descriptor_hash for item in rule_descriptors],
        }
    )
    return CanonicalFullCensusPlanV4(
        UTILITY_MAIN_PORTFOLIO,
        common_portfolio_hash,
        tuple(item.descriptor_hash for item in rule_descriptors),
        numeric_authority.descriptor_hash,
        feature_schema.authority_hash,
        DATASET_MANIFEST_ID,
        INNER_SPLIT_ID,
        OUTER_SPLIT_ID,
        OPPORTUNITY_ENUMERATION_POLICY_HASH,
        CORRECTED_EVENT_POLICY_HASH,
        CORRECTED_METRIC_POLICY_HASH,
        SOURCE_UNIVERSE_POLICY_HASH,
        BOUNDARY_WINDOW_POLICY_HASH,
        PURGE_POLICY_HASH,
    )


def validate_canonical_full_census_plan_v4(
    plan: CanonicalFullCensusPlanV4,
    authority: "UtilityProtocolV4CanonicalAuthority",
) -> str:
    validate_utility_protocol_v4_authority(authority)
    if type(plan) is not CanonicalFullCensusPlanV4:
        raise UtilityProtocolV4Error("canonical full-census plan type differs")
    expected = build_canonical_full_census_plan_v4(
        authority.numeric_authority,
        authority.rule_descriptors,
        authority.feature_schema,
    )
    if plan != expected or plan.to_dict() != expected.to_dict():
        raise UtilityProtocolV4Error("canonical full-census provenance replay differs")
    return plan.plan_hash


@dataclass(frozen=True)
class PrivateNumericResolverContractV4:
    numeric_authority_descriptor_hash: str
    private_registry_content_hash: str
    materialized_authority_audit_receipt_hash: str
    exact_local_locator_hash: str
    lookup_key_fields: tuple[str, ...]
    expected_records: int
    returns_partial_lookup_on_failure: bool
    historical_private_authority_required: bool
    exposes_private_serialization: bool

    def __post_init__(self) -> None:
        for name in (
            "numeric_authority_descriptor_hash",
            "private_registry_content_hash",
            "materialized_authority_audit_receipt_hash",
            "exact_local_locator_hash",
        ):
            _sha(getattr(self, name), name)
        if self.lookup_key_fields != ("relation_binding_hash", "numeric_role"):
            raise UtilityProtocolV4Error("private lookup key schema differs")
        if _strict_int(self.expected_records, "expected_records", minimum=1) != 420:
            raise UtilityProtocolV4Error("private resolver record closure differs")
        for name in (
            "returns_partial_lookup_on_failure",
            "historical_private_authority_required",
            "exposes_private_serialization",
        ):
            if _strict_bool(getattr(self, name), name) is not False:
                raise UtilityProtocolV4Error("private resolver grants a prohibited capability")

    @property
    def contract_hash(self) -> str:
        return stable_hash_v1(
            {
                "artifact_type": "task039e3_r2r_utility_protocol_v4_private_numeric_resolver_contract",
                "exact_local_locator_hash": self.exact_local_locator_hash,
                "expected_records": self.expected_records,
                "exposes_private_serialization": self.exposes_private_serialization,
                "historical_private_authority_required": self.historical_private_authority_required,
                "lookup_key_fields": list(self.lookup_key_fields),
                "materialized_authority_audit_receipt_hash": self.materialized_authority_audit_receipt_hash,
                "numeric_authority_descriptor_hash": self.numeric_authority_descriptor_hash,
                "private_registry_content_hash": self.private_registry_content_hash,
                "returns_partial_lookup_on_failure": self.returns_partial_lookup_on_failure,
                "schema_version": SCHEMA_VERSION,
            }
        )


@dataclass(frozen=True)
class UtilityProtocolV4CanonicalAuthority:
    numeric_authority: NumericAuthorityDescriptorV4
    rule_descriptors: tuple[CanonicalRuleDescriptorV4, ...]
    feature_schema: CanonicalFeatureSchemaV4
    full_census_plan: CanonicalFullCensusPlanV4
    private_resolver_contract: PrivateNumericResolverContractV4
    blocker_closures: tuple[tuple[str, str], ...]
    regression_authority_hashes: tuple[str, str, str]

    def __post_init__(self) -> None:
        if self.blocker_closures != BLOCKER_CLOSURES:
            raise UtilityProtocolV4Error("eight-blocker closure matrix differs")
        if self.regression_authority_hashes != (
            CORRECTED_REGRESSION_NUMERIC_REFERENCE_AUTHORITY_HASH,
            CORRECTED_EVENT_POLICY_HASH,
            CORRECTED_METRIC_POLICY_HASH,
        ):
            raise UtilityProtocolV4Error("corrected regression authorities differ")
        if self.full_census_plan.numeric_authority_descriptor_hash != self.numeric_authority.descriptor_hash:
            raise UtilityProtocolV4Error("census and numeric authorities differ")
        if self.full_census_plan.feature_schema_authority_hash != self.feature_schema.authority_hash:
            raise UtilityProtocolV4Error("census and feature authorities differ")
        if self.full_census_plan.rule_descriptor_hashes != tuple(item.descriptor_hash for item in self.rule_descriptors):
            raise UtilityProtocolV4Error("census and rule authorities differ")
        if self.private_resolver_contract.numeric_authority_descriptor_hash != self.numeric_authority.descriptor_hash:
            raise UtilityProtocolV4Error("private resolver and numeric authority differ")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_canonical_authority",
            "blocker_closures": [
                {"finding": finding, "closure": closure}
                for finding, closure in self.blocker_closures
            ],
            "claim_boundary": {
                "evaluator_implemented": False,
                "private_numeric_values_accessed": False,
                "real_utility_executed": False,
            },
            "common_construction_cells": ["T0", "T1", "T1-B"],
            "common_runtime_library_count": 1,
            "comparison_policy_hash": COMPARISON_POLICY_HASH,
            "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
            "feature_schema": self.feature_schema.to_dict(),
            "full_census_plan": self.full_census_plan.to_dict(),
            "historical_v3_focused_audit_hashes": dict(V3_FOCUSED_AUDIT_HASHES),
            "main_portfolio": UTILITY_MAIN_PORTFOLIO,
            "metric_policy_hash": CORRECTED_METRIC_POLICY_HASH,
            "numeric_authority": self.numeric_authority.to_dict(),
            "private_resolver_contract_hash": self.private_resolver_contract.contract_hash,
            "protocol_version": PROTOCOL_VERSION,
            "regression_authority_hashes": list(self.regression_authority_hashes),
            "rule_descriptors": [item.to_dict() for item in self.rule_descriptors],
            "schema_version": SCHEMA_VERSION,
            "strict_scalar_policy_hash": STRICT_SCALAR_POLICY_HASH,
            "t2_utility_scope_authorized": False,
            "terminal_transition_policy_hash": TERMINAL_TRANSITION_POLICY_HASH,
            "v3_lineage": V3_LINEAGE,
        }

    @property
    def authority_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "authority_hash": self.authority_hash}

    def rule_by_binding(self, relation_binding_hash: str) -> CanonicalRuleDescriptorV4:
        matches = [item for item in self.rule_descriptors if item.relation_binding_hash == relation_binding_hash]
        if len(matches) != 1:
            raise UtilityProtocolV4Error("relation is outside canonical COMMON-42")
        return matches[0]


def build_utility_protocol_v4_canonical_authority(
    *,
    executable_equivalence: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    csv_structure_report: Mapping[str, Any],
    c0_config: Mapping[str, Any],
    br2_config: Mapping[str, Any],
    materialized_audit_receipt: Mapping[str, Any],
) -> UtilityProtocolV4CanonicalAuthority:
    common = build_common42_public_authority_v4(executable_equivalence, evidence_manifest)
    numeric = build_numeric_authority_descriptor_v4(common, materialized_audit_receipt)
    rules = build_canonical_rule_descriptors_v4(common, numeric)
    feature = build_canonical_feature_schema_v4(
        dataset_manifest=dataset_manifest,
        csv_structure_report=csv_structure_report,
        c0_config=c0_config,
        br2_config=br2_config,
        executable_equivalence=executable_equivalence,
        common_authority=common,
    )
    plan = build_canonical_full_census_plan_v4(numeric, rules, feature)
    resolver = PrivateNumericResolverContractV4(
        numeric.descriptor_hash,
        PRIVATE_REGISTRY_CONTENT_HASH,
        MATERIALIZED_AUTHORITY_AUDIT_RECEIPT_HASH,
        LOCAL_LOCATOR_HASH,
        ("relation_binding_hash", "numeric_role"),
        420,
        False,
        False,
        False,
    )
    return UtilityProtocolV4CanonicalAuthority(
        numeric,
        rules,
        feature,
        plan,
        resolver,
        BLOCKER_CLOSURES,
        (
            CORRECTED_REGRESSION_NUMERIC_REFERENCE_AUTHORITY_HASH,
            CORRECTED_EVENT_POLICY_HASH,
            CORRECTED_METRIC_POLICY_HASH,
        ),
    )


def validate_utility_protocol_v4_authority(authority: UtilityProtocolV4CanonicalAuthority) -> str:
    if type(authority) is not UtilityProtocolV4CanonicalAuthority:
        raise UtilityProtocolV4Error("canonical V4 authority type differs")
    if CANONICAL_V4_AUTHORITY_HASH == "__TO_BE_FROZEN__":
        raise UtilityProtocolV4Error("canonical V4 authority hash is not frozen")
    if authority.authority_hash != CANONICAL_V4_AUTHORITY_HASH:
        raise UtilityProtocolV4Error("canonical V4 authority identity differs")
    UtilityProtocolV4CanonicalAuthority(
        authority.numeric_authority,
        authority.rule_descriptors,
        authority.feature_schema,
        authority.full_census_plan,
        authority.private_resolver_contract,
        authority.blocker_closures,
        authority.regression_authority_hashes,
    )
    return authority.authority_hash


def authorize_canonical_full_census_plan_v4(
    authority: UtilityProtocolV4CanonicalAuthority,
    *,
    portfolio_identity: str = UTILITY_MAIN_PORTFOLIO,
    **caller_overrides: object,
) -> CanonicalFullCensusPlanV4:
    validate_utility_protocol_v4_authority(authority)
    if portfolio_identity != UTILITY_MAIN_PORTFOLIO:
        raise UtilityProtocolV4Error("T2 or caller portfolio authority is prohibited")
    if caller_overrides:
        raise UtilityProtocolV4Error("caller census counts, lists, subsets, and denominators are prohibited")
    expected = build_canonical_full_census_plan_v4(
        authority.numeric_authority,
        authority.rule_descriptors,
        authority.feature_schema,
    )
    if authority.full_census_plan != expected:
        raise UtilityProtocolV4Error("canonical full-census plan replay differs")
    return authority.full_census_plan


_CANONICAL_CONSTRUCTION_TOKEN = object()


@dataclass(frozen=True, init=False)
class CanonicalRowTimeIdentityV4:
    dataset_manifest_identity: str
    split_identity: str
    source_file_identity: str
    physical_row_index: int
    timestamp_identity: str
    row_time_identity: str

    def __new__(cls, construction_token: object) -> "CanonicalRowTimeIdentityV4":
        if construction_token is not _CANONICAL_CONSTRUCTION_TOKEN:
            raise UtilityProtocolV4Error("canonical row/time construction is factory-only")
        return super().__new__(cls)


@dataclass(frozen=True, init=False)
class CanonicalOpportunityV4:
    dataset_manifest_identity: str
    split_identity: str
    source_file_identity: str
    relation_identity: str
    relation_binding_hash: str
    semantic_execution_hash: str
    source: str
    target: str
    source_direction: str
    target_direction: str
    selected_horizon_seconds: int
    canonical_row_time_identity: str
    physical_row_index: int
    timestamp_identity: str
    rule_descriptor_hash: str
    numeric_authority_descriptor_hash: str
    event_policy_hash: str
    opportunity_enumeration_policy_hash: str
    opportunity_id: str

    def __new__(cls, construction_token: object) -> "CanonicalOpportunityV4":
        if construction_token is not _CANONICAL_CONSTRUCTION_TOKEN:
            raise UtilityProtocolV4Error("canonical opportunity construction is factory-only")
        return super().__new__(cls)


@dataclass(frozen=True, init=False)
class SourceQualificationStateV4:
    opportunity_id: str
    rule_descriptor_hash: str
    source_window_identity: str
    retained_source_event_identity: str
    retained_source_event_census_hash: str
    source_step_reference_identity: str
    source_stability_reference_identity: str
    event_policy_hash: str
    state: str
    source_qualification_identity: str

    def __new__(cls, construction_token: object) -> "SourceQualificationStateV4":
        if construction_token is not _CANONICAL_CONSTRUCTION_TOKEN:
            raise UtilityProtocolV4Error("source qualification construction is factory-only")
        return super().__new__(cls)


@dataclass(frozen=True, init=False)
class TargetEvaluationStateV4:
    opportunity_id: str
    rule_descriptor_hash: str
    source_qualification_identity: str
    target_window_input_identity: str
    target_noise_reference_identity: str
    numeric_authority_descriptor_hash: str
    transition_policy_hash: str
    physical_row_count: int
    within_split: bool
    target_context_available: bool
    response_matched: bool
    target_evaluation_state: str
    decision_row_time_identity: str | None
    alarm_emitted: bool
    abstention_reason: str | None
    terminal_state_provenance_hash: str

    def __new__(cls, construction_token: object) -> "TargetEvaluationStateV4":
        if construction_token is not _CANONICAL_CONSTRUCTION_TOKEN:
            raise UtilityProtocolV4Error("target terminal construction is factory-only")
        return super().__new__(cls)


def _construct(cls: type[Any], **values: object) -> Any:
    result = object.__new__(cls)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    return result


def _row_time_payload(row_time: CanonicalRowTimeIdentityV4) -> dict[str, Any]:
    return {
        "dataset_manifest_identity": row_time.dataset_manifest_identity,
        "physical_row_index": row_time.physical_row_index,
        "source_file_identity": row_time.source_file_identity,
        "split_identity": row_time.split_identity,
        "timestamp_identity": row_time.timestamp_identity,
    }


def build_canonical_row_time_identity_v4(
    *, source_file_identity: str, physical_row_index: int, timestamp_identity: str
) -> CanonicalRowTimeIdentityV4:
    if source_file_identity not in FILE_ROW_COUNTS:
        raise UtilityProtocolV4Error("source file identity is outside INNER/OUTER authority")
    index = _strict_int(physical_row_index, "physical_row_index")
    if index >= FILE_ROW_COUNTS[source_file_identity]:
        raise UtilityProtocolV4Error("row coordinate is outside the physical file")
    timestamp = _sha(timestamp_identity, "timestamp_identity")
    values = {
        "dataset_manifest_identity": DATASET_MANIFEST_ID,
        "split_identity": FILE_SPLITS[source_file_identity],
        "source_file_identity": source_file_identity,
        "physical_row_index": index,
        "timestamp_identity": timestamp,
    }
    return _construct(
        CanonicalRowTimeIdentityV4,
        **values,
        row_time_identity=stable_hash_v1(values),
    )


def _opportunity_payload(opportunity: CanonicalOpportunityV4) -> dict[str, Any]:
    return {
        "canonical_row_time_identity": opportunity.canonical_row_time_identity,
        "dataset_manifest_identity": opportunity.dataset_manifest_identity,
        "event_policy_hash": opportunity.event_policy_hash,
        "numeric_authority_descriptor_hash": opportunity.numeric_authority_descriptor_hash,
        "opportunity_enumeration_policy_hash": opportunity.opportunity_enumeration_policy_hash,
        "physical_row_index": opportunity.physical_row_index,
        "relation_binding_hash": opportunity.relation_binding_hash,
        "relation_identity": opportunity.relation_identity,
        "rule_descriptor_hash": opportunity.rule_descriptor_hash,
        "selected_horizon_seconds": opportunity.selected_horizon_seconds,
        "semantic_execution_hash": opportunity.semantic_execution_hash,
        "source": opportunity.source,
        "source_direction": opportunity.source_direction,
        "source_file_identity": opportunity.source_file_identity,
        "split_identity": opportunity.split_identity,
        "target": opportunity.target,
        "target_direction": opportunity.target_direction,
        "timestamp_identity": opportunity.timestamp_identity,
    }


def build_canonical_opportunity_v4(
    authority: UtilityProtocolV4CanonicalAuthority,
    *,
    relation_binding_hash: str,
    row_time: CanonicalRowTimeIdentityV4,
) -> CanonicalOpportunityV4:
    validate_utility_protocol_v4_authority(authority)
    if type(row_time) is not CanonicalRowTimeIdentityV4:
        raise UtilityProtocolV4Error("canonical row/time identity is required")
    if stable_hash_v1(_row_time_payload(row_time)) != row_time.row_time_identity:
        raise UtilityProtocolV4Error("canonical row/time replay differs")
    rule = authority.rule_by_binding(relation_binding_hash)
    values = {
        "dataset_manifest_identity": row_time.dataset_manifest_identity,
        "split_identity": row_time.split_identity,
        "source_file_identity": row_time.source_file_identity,
        "relation_identity": rule.relation_identity,
        "relation_binding_hash": rule.relation_binding_hash,
        "semantic_execution_hash": rule.semantic_execution_hash,
        "source": rule.source,
        "target": rule.target,
        "source_direction": rule.source_direction,
        "target_direction": rule.target_direction,
        "selected_horizon_seconds": rule.selected_horizon_seconds,
        "canonical_row_time_identity": row_time.row_time_identity,
        "physical_row_index": row_time.physical_row_index,
        "timestamp_identity": row_time.timestamp_identity,
        "rule_descriptor_hash": rule.descriptor_hash,
        "numeric_authority_descriptor_hash": authority.numeric_authority.descriptor_hash,
        "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
        "opportunity_enumeration_policy_hash": OPPORTUNITY_ENUMERATION_POLICY_HASH,
    }
    provisional = _construct(CanonicalOpportunityV4, **values, opportunity_id="")
    return _construct(
        CanonicalOpportunityV4,
        **values,
        opportunity_id=stable_hash_v1(_opportunity_payload(provisional)),
    )


def validate_canonical_opportunity_v4(
    opportunity: CanonicalOpportunityV4,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> str:
    if type(opportunity) is not CanonicalOpportunityV4:
        raise UtilityProtocolV4Error("canonical opportunity type differs")
    validate_utility_protocol_v4_authority(authority)
    rule = authority.rule_by_binding(opportunity.relation_binding_hash)
    expected = {
        "relation_identity": rule.relation_identity,
        "semantic_execution_hash": rule.semantic_execution_hash,
        "source": rule.source,
        "target": rule.target,
        "source_direction": rule.source_direction,
        "target_direction": rule.target_direction,
        "selected_horizon_seconds": rule.selected_horizon_seconds,
        "rule_descriptor_hash": rule.descriptor_hash,
        "numeric_authority_descriptor_hash": authority.numeric_authority.descriptor_hash,
        "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
        "opportunity_enumeration_policy_hash": OPPORTUNITY_ENUMERATION_POLICY_HASH,
        "dataset_manifest_identity": DATASET_MANIFEST_ID,
    }
    if any(getattr(opportunity, name) != value for name, value in expected.items()):
        raise UtilityProtocolV4Error("opportunity semantic replay differs")
    if opportunity.source_file_identity not in FILE_ROW_COUNTS or opportunity.split_identity != FILE_SPLITS[opportunity.source_file_identity]:
        raise UtilityProtocolV4Error("opportunity split/file authority differs")
    index = _strict_int(opportunity.physical_row_index, "physical_row_index")
    if index >= FILE_ROW_COUNTS[opportunity.source_file_identity]:
        raise UtilityProtocolV4Error("opportunity coordinate is outside the physical file")
    _sha(opportunity.timestamp_identity, "timestamp_identity")
    _sha(opportunity.canonical_row_time_identity, "canonical_row_time_identity")
    row_payload = {
        "dataset_manifest_identity": opportunity.dataset_manifest_identity,
        "physical_row_index": index,
        "source_file_identity": opportunity.source_file_identity,
        "split_identity": opportunity.split_identity,
        "timestamp_identity": opportunity.timestamp_identity,
    }
    if stable_hash_v1(row_payload) != opportunity.canonical_row_time_identity:
        raise UtilityProtocolV4Error("opportunity row/time provenance differs")
    if stable_hash_v1(_opportunity_payload(opportunity)) != opportunity.opportunity_id:
        raise UtilityProtocolV4Error("opportunity identity preimage differs")
    return opportunity.opportunity_id


def validate_canonical_opportunity_set_v4(
    opportunities: object,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> str:
    values = _strict_tuple(opportunities, "canonical opportunities")
    ids: list[str] = []
    logical_keys: list[tuple[str, str]] = []
    for item in values:
        ids.append(validate_canonical_opportunity_v4(item, authority))
        logical_keys.append((item.relation_binding_hash, item.canonical_row_time_identity))
    if len(ids) != len(set(ids)) or len(logical_keys) != len(set(logical_keys)):
        raise UtilityProtocolV4Error("canonical opportunity census contains duplicates")
    if tuple(sorted(values, key=lambda item: (item.relation_binding_hash, item.canonical_row_time_identity))) != values:
        raise UtilityProtocolV4Error("canonical opportunity census ordering differs")
    return stable_hash_v1({"opportunity_ids": ids})


def build_source_qualification_state_v4(
    opportunity: CanonicalOpportunityV4,
    authority: UtilityProtocolV4CanonicalAuthority,
    *,
    source_window_identity: str,
    retained_source_event_identity: str,
    retained_source_event_census_hash: str,
) -> SourceQualificationStateV4:
    validate_canonical_opportunity_v4(opportunity, authority)
    rule = authority.rule_by_binding(opportunity.relation_binding_hash)
    values = {
        "opportunity_id": opportunity.opportunity_id,
        "rule_descriptor_hash": rule.descriptor_hash,
        "source_window_identity": _sha(source_window_identity, "source_window_identity"),
        "retained_source_event_identity": _sha(retained_source_event_identity, "retained_source_event_identity"),
        "retained_source_event_census_hash": _sha(retained_source_event_census_hash, "retained_source_event_census_hash"),
        "source_step_reference_identity": rule.reference_for("source_step_threshold"),
        "source_stability_reference_identity": rule.reference_for("source_stability_tolerance"),
        "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
        "state": "source_qualified",
    }
    return _construct(
        SourceQualificationStateV4,
        **values,
        source_qualification_identity=stable_hash_v1(values),
    )


def validate_source_qualification_state_v4(
    state: SourceQualificationStateV4,
    opportunity: CanonicalOpportunityV4,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> str:
    if type(state) is not SourceQualificationStateV4:
        raise UtilityProtocolV4Error("source qualification parent type differs")
    validate_canonical_opportunity_v4(opportunity, authority)
    rule = authority.rule_by_binding(opportunity.relation_binding_hash)
    values = {
        "opportunity_id": opportunity.opportunity_id,
        "rule_descriptor_hash": rule.descriptor_hash,
        "source_window_identity": _sha(state.source_window_identity, "source_window_identity"),
        "retained_source_event_identity": _sha(state.retained_source_event_identity, "retained_source_event_identity"),
        "retained_source_event_census_hash": _sha(state.retained_source_event_census_hash, "retained_source_event_census_hash"),
        "source_step_reference_identity": rule.reference_for("source_step_threshold"),
        "source_stability_reference_identity": rule.reference_for("source_stability_tolerance"),
        "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
        "state": "source_qualified",
    }
    if any(getattr(state, name) != value for name, value in values.items()) or stable_hash_v1(values) != state.source_qualification_identity:
        raise UtilityProtocolV4Error("source qualification provenance replay differs")
    return state.source_qualification_identity


def transition_target_evaluation_v4(
    opportunity: CanonicalOpportunityV4,
    source_state: SourceQualificationStateV4,
    authority: UtilityProtocolV4CanonicalAuthority,
    *,
    target_window_input_identity: str,
    within_split: bool,
    target_context_available: bool,
    response_matched: bool,
) -> TargetEvaluationStateV4:
    validate_source_qualification_state_v4(source_state, opportunity, authority)
    _strict_bool(within_split, "within_split")
    _strict_bool(target_context_available, "target_context_available")
    _strict_bool(response_matched, "response_matched")
    rule = authority.rule_by_binding(opportunity.relation_binding_hash)
    decision_index = opportunity.physical_row_index + rule.selected_horizon_seconds + TARGET_RESPONSE_WINDOW - 1
    reason = (
        "file_boundary"
        if decision_index >= FILE_ROW_COUNTS[opportunity.source_file_identity]
        else "split_boundary"
        if not within_split
        else "incomplete_target_response_window"
        if not target_context_available
        else None
    )
    if reason is not None:
        target_state = "abstain"
        decision_identity = None
        alarm = False
    else:
        target_state = "evaluated_expected_response" if response_matched else "evaluated_anomaly"
        decision_identity = stable_hash_v1(
            {
                "dataset_manifest_identity": DATASET_MANIFEST_ID,
                "decision_physical_row_index": decision_index,
                "source_file_identity": opportunity.source_file_identity,
                "split_identity": opportunity.split_identity,
            }
        )
        alarm = not response_matched
    values = {
        "opportunity_id": opportunity.opportunity_id,
        "rule_descriptor_hash": rule.descriptor_hash,
        "source_qualification_identity": source_state.source_qualification_identity,
        "target_window_input_identity": _sha(target_window_input_identity, "target_window_input_identity"),
        "target_noise_reference_identity": rule.reference_for("target_noise_scale"),
        "numeric_authority_descriptor_hash": authority.numeric_authority.descriptor_hash,
        "transition_policy_hash": TERMINAL_TRANSITION_POLICY_HASH,
        "physical_row_count": FILE_ROW_COUNTS[opportunity.source_file_identity],
        "within_split": within_split,
        "target_context_available": target_context_available,
        "response_matched": response_matched,
        "target_evaluation_state": target_state,
        "decision_row_time_identity": decision_identity,
        "alarm_emitted": alarm,
        "abstention_reason": reason,
    }
    return _construct(
        TargetEvaluationStateV4,
        **values,
        terminal_state_provenance_hash=stable_hash_v1(values),
    )


def validate_target_evaluation_state_v4(
    state: TargetEvaluationStateV4,
    opportunity: CanonicalOpportunityV4,
    source_state: SourceQualificationStateV4,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> str:
    if type(state) is not TargetEvaluationStateV4:
        raise UtilityProtocolV4Error("target terminal state type differs")
    validate_source_qualification_state_v4(source_state, opportunity, authority)
    rule = authority.rule_by_binding(opportunity.relation_binding_hash)
    fixed = {
        "opportunity_id": opportunity.opportunity_id,
        "rule_descriptor_hash": rule.descriptor_hash,
        "source_qualification_identity": source_state.source_qualification_identity,
        "target_noise_reference_identity": rule.reference_for("target_noise_scale"),
        "numeric_authority_descriptor_hash": authority.numeric_authority.descriptor_hash,
        "transition_policy_hash": TERMINAL_TRANSITION_POLICY_HASH,
    }
    if any(getattr(state, name) != value for name, value in fixed.items()):
        raise UtilityProtocolV4Error("terminal parent-chain provenance differs")
    _sha(state.target_window_input_identity, "target_window_input_identity")
    _strict_bool(state.alarm_emitted, "alarm_emitted")
    if _strict_int(state.physical_row_count, "physical_row_count", minimum=1) != FILE_ROW_COUNTS[opportunity.source_file_identity]:
        raise UtilityProtocolV4Error("terminal physical-row authority differs")
    _strict_bool(state.within_split, "within_split")
    _strict_bool(state.target_context_available, "target_context_available")
    _strict_bool(state.response_matched, "response_matched")
    decision_index = opportunity.physical_row_index + rule.selected_horizon_seconds + TARGET_RESPONSE_WINDOW - 1
    expected_reason = (
        "file_boundary"
        if decision_index >= state.physical_row_count
        else "split_boundary"
        if not state.within_split
        else "incomplete_target_response_window"
        if not state.target_context_available
        else None
    )
    expected_state = (
        "abstain"
        if expected_reason is not None
        else "evaluated_expected_response"
        if state.response_matched
        else "evaluated_anomaly"
    )
    expected_alarm = expected_state == "evaluated_anomaly"
    expected_decision = (
        None
        if expected_state == "abstain"
        else stable_hash_v1(
            {
                "dataset_manifest_identity": DATASET_MANIFEST_ID,
                "decision_physical_row_index": decision_index,
                "source_file_identity": opportunity.source_file_identity,
                "split_identity": opportunity.split_identity,
            }
        )
    )
    if (
        state.target_evaluation_state != expected_state
        or state.abstention_reason != expected_reason
        or state.alarm_emitted is not expected_alarm
        or state.decision_row_time_identity != expected_decision
    ):
        raise UtilityProtocolV4Error("terminal target state differs from coordinate/context replay")
    if state.decision_row_time_identity is not None:
        _sha(state.decision_row_time_identity, "decision_row_time_identity")
    values = {
        **fixed,
        "target_window_input_identity": state.target_window_input_identity,
        "physical_row_count": state.physical_row_count,
        "within_split": state.within_split,
        "target_context_available": state.target_context_available,
        "response_matched": state.response_matched,
        "target_evaluation_state": state.target_evaluation_state,
        "decision_row_time_identity": state.decision_row_time_identity,
        "alarm_emitted": state.alarm_emitted,
        "abstention_reason": state.abstention_reason,
    }
    if stable_hash_v1(values) != state.terminal_state_provenance_hash:
        raise UtilityProtocolV4Error("terminal-state provenance hash differs")
    return state.terminal_state_provenance_hash


def validate_strict_scalar_policy_v4(
    *, integer_value: object, boolean_value: object, float_value: object, string_value: object,
    tuple_value: object,
) -> str:
    _strict_int(integer_value, "integer_value")
    _strict_bool(boolean_value, "boolean_value")
    _strict_float(float_value, "float_value")
    _strict_str(string_value, "string_value")
    _strict_tuple(tuple_value, "tuple_value")
    return STRICT_SCALAR_POLICY_HASH


def validate_regression_authorities_v4(
    numeric_reference_hash: str, event_policy_hash: str, metric_policy_hash: str
) -> tuple[str, str, str]:
    observed = (
        _sha(numeric_reference_hash, "numeric_reference_hash"),
        _sha(event_policy_hash, "event_policy_hash"),
        _sha(metric_policy_hash, "metric_policy_hash"),
    )
    expected = (
        CORRECTED_REGRESSION_NUMERIC_REFERENCE_AUTHORITY_HASH,
        CORRECTED_EVENT_POLICY_HASH,
        CORRECTED_METRIC_POLICY_HASH,
    )
    if observed != expected or any(value in HISTORICAL_WRONG_REGRESSION_HASHES for value in observed):
        raise UtilityProtocolV4Error("regression component authority hashes differ")
    return observed


_ASCII_DECIMAL_TOKEN = re.compile(
    r"[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?\Z"
)


def validate_selected_feature_header_v4(
    header: object,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> tuple[str, ...]:
    """Require the exact canonical 22-feature evaluator header."""

    validate_utility_protocol_v4_authority(authority)
    values = _strict_tuple(header, "selected feature header")
    if any(type(value) is not str for value in values):
        raise UtilityProtocolV4Error("selected feature header contains a non-string")
    expected = ("timestamp", *authority.feature_schema.union_features)
    if values != expected or len(values) != len(set(values)):
        raise UtilityProtocolV4Error("selected feature header differs from canonical V3 replay")
    return values


def parse_raw_feature_tokens_v4(
    feature_identity: object,
    raw_tokens: object,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> tuple[float, ...]:
    """Parse strict ASCII decimals only after canonical feature-schema replay."""

    validate_utility_protocol_v4_authority(authority)
    feature = _strict_str(feature_identity, "feature_identity")
    if feature not in authority.feature_schema.union_features:
        raise UtilityProtocolV4Error("feature identity is outside the canonical evaluator schema")
    tokens = _strict_tuple(raw_tokens, "raw feature tokens")
    result: list[float] = []
    for token in tokens:
        if type(token) is not str or _ASCII_DECIMAL_TOKEN.fullmatch(token) is None:
            raise UtilityProtocolV4Error("raw feature token is not a strict ASCII decimal")
        value = float(token)
        if not math.isfinite(value):
            raise UtilityProtocolV4Error("raw feature token is nonfinite")
        result.append(value)
    return tuple(result)


def parse_raw_label_tokens_v4(
    raw_tokens: object,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> tuple[int, ...]:
    """Freeze the future label boundary without reading any labels here."""

    validate_utility_protocol_v4_authority(authority)
    tokens = _strict_tuple(raw_tokens, "raw label tokens")
    if any(type(token) is not str or token not in {"0", "1"} for token in tokens):
        raise UtilityProtocolV4Error("label token is not exact binary text")
    return tuple(0 if token == "0" else 1 for token in tokens)


__all__ = [name for name in globals() if not name.startswith("_")]
