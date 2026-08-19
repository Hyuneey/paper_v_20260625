"""Canonical authority and synthetic numeric resolver for Utility Evaluator V1.

The module is deliberately side-effect free.  The real resolver entry point
fails before inspecting a path because real utility execution has not been
authorized.  Synthetic values live only in a contract-test resolver whose
identity and purpose cannot be confused with either materialized authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import weakref

from paperworks.v6.task039e3_r2r_utility_evaluator_types_v1 import (
    EVALUATOR_VERSION,
    REAL_UTILITY_EXECUTION_AUTHORIZED,
    SYNTHETIC_AUTHORITY_IDENTITY,
    SYNTHETIC_CONTRACT_ONLY,
    UtilityEvaluatorV1Error,
    stable_hash_v1,
    strict_float_v1,
    strict_int_v1,
    strict_str_v1,
    strict_tuple_v1,
)
from paperworks.v6 import task039e3_r2r_utility_protocol_v4 as v4
from paperworks.v6 import task039e3_r2r_utility_source_census_supplement_v1 as supplement


HISTORICAL_V4_AUTHORITY_HASH = "2864c99017dcea576437efe9f9c5d531cc0d7810504cb2bd8e8585643d2fa0a1"
V4_R1_FOCUSED_AUDIT_HASH = "8c66590f222ad656add781745a361e483ba0ecd3c42bccbfa11f08cfaa6550ae"
V4_R1_FOCUSED_RECEIPT_HASH = "09cf661a21cb4bd0d5ad356c2cf725264d76aeaffc7963858425e88267717509"

MAIN_DESCRIPTOR_HASH = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
MAIN_REFERENCE_SET_HASH = "d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae"
MAIN_PRIVATE_REGISTRY_HASH = "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
MAIN_AUDIT_RECEIPT_HASH = "1f319fd7283040a4e866df3ac7d679e896142162084209bf00962947256c2bf1"
MAIN_LOCATOR_HASH = "b5588c04d08d88d4ee2a2d319708e62d10bc04330baeb7591876f076270e4ac4"

SUPPLEMENT_DESCRIPTOR_HASH = "d45af926511c669ec04dd13c36823d454b67ccaa98ae0a7be2919b02652bd927"
SUPPLEMENT_REFERENCE_SET_HASH = "5139cae6e454318f0ca4317f3f5eaa5f775bd4f75261c4110ea610815929b580"
SUPPLEMENT_PRIVATE_REGISTRY_HASH = "12ec7f50a953e097cd7cbe3ac93c7cabfb669130612d7f30ab3b19df85289aaf"
SUPPLEMENT_LOCATOR_HASH = "8c11872dca6a0c8b2544c2988dd57c969ddc036f51b04578d936fdc3a60757ac"
SUPPLEMENT_PUBLIC_RECEIPT_HASH = "56e455d69823e87b7fa217c6ee7d8d86f5d08b7fc5aaf9865ff1241c6798d16e"
SUPPLEMENT_FINAL_AUDIT_HASH = "ad61a4c435e7904b5a80feca40e7e629dc3522e8dc4f68c99b2b9ab9b45d142b"
SUPPLEMENT_FINAL_BUNDLE_HASH = "d379cfe8e3c452100f2993c2e16f21e39b54393bbbe178ebfda0d1ee91a10620"
SUPPLEMENT_FINAL_RECEIPT_HASH = "c4397b83155bff74c0997c8e4837b0c90198e6df6dd0bea748d62086eef7ba98"

COMBINED_SOURCE_CENSUS_CONTRACT_HASH = "cb53d0e4533ebadb61edbdc72b549fe47b46c8dcc4621841aac93a007660ced9"
SOURCE_CENSUS_EVENT_POLICY_HASH = "3fb20068feff44632be3e4e6917183d52fea5616feec68ede5e9b62f95ecb390"
CROSS_SOURCE_ISOLATION_POLICY_HASH = "f62075523632a7573d28e95ca7f0402d87e62977f4a2f14f4eaf2b9a58f0e280"
SUPPLEMENT_PURPOSE = "CROSS_SOURCE_ISOLATION_EVENT_CENSUS_ONLY"

CANONICAL_FEATURE_SCHEMA_HASH = "62fd76bd541437694aff274db865670f24eecbabf3c736f32893bd97081564b8"
RUNTIME_FEATURE_SCHEMA_HASH = "e7a0c46d28491b9d03a333a0ad1e87d686a982bafba072861913e05fb6c50b58"

MAIN_SOURCES = supplement.MAIN_SOURCES
SUPPLEMENT_SOURCES = supplement.SUPPLEMENT_SOURCES
EVALUATOR_SOURCE_CENSUS = tuple(sorted(MAIN_SOURCES + SUPPLEMENT_SOURCES))
SOURCE_CENSUS_ROLES = supplement.SUPPLEMENT_ROLES
MAIN_NUMERIC_ROLES = v4.UTILITY_NUMERIC_ROLES


@dataclass(frozen=True)
class EvaluatorAuthorityBundleV1:
    """Public, value-free binding of every frozen evaluator authority."""

    v4_authority: v4.UtilityProtocolV4CanonicalAuthority
    evaluator_version: str
    v4_authority_hash: str
    v4_focused_audit_hash: str
    v4_focused_receipt_hash: str
    common_portfolio: str
    common_relation_count: int
    t2_utility_authorized: bool
    main_descriptor_hash: str
    main_reference_set_hash: str
    main_private_registry_hash: str
    main_audit_receipt_hash: str
    main_locator_hash: str
    supplement_descriptor_hash: str
    supplement_reference_set_hash: str
    supplement_private_registry_hash: str
    supplement_locator_hash: str
    supplement_public_receipt_hash: str
    supplement_final_audit_hash: str
    supplement_final_bundle_hash: str
    supplement_final_receipt_hash: str
    combined_source_census_contract_hash: str
    source_census_event_policy_hash: str
    cross_source_isolation_policy_hash: str
    utility_event_aggregation_policy_hash: str
    metric_policy_hash: str
    canonical_feature_schema_hash: str
    runtime_feature_schema_hash: str
    dataset_manifest_identity: str
    split_identities: tuple[str, str]
    purge_policy_hash: str
    main_sources: tuple[str, ...]
    supplement_sources: tuple[str, ...]
    evaluator_source_census: tuple[str, ...]

    def _payload(self) -> dict[str, object]:
        return {
            "artifact_type": "task039e3_r2r_utility_evaluator_authority_bundle_v1",
            "evaluator_version": self.evaluator_version,
            "v4_authority_hash": self.v4_authority_hash,
            "v4_focused_audit_hash": self.v4_focused_audit_hash,
            "v4_focused_receipt_hash": self.v4_focused_receipt_hash,
            "common_portfolio": self.common_portfolio,
            "common_relation_count": self.common_relation_count,
            "t2_utility_authorized": self.t2_utility_authorized,
            "main": {
                "descriptor_hash": self.main_descriptor_hash,
                "reference_set_hash": self.main_reference_set_hash,
                "reference_count": 420,
                "private_registry_hash": self.main_private_registry_hash,
                "audit_receipt_hash": self.main_audit_receipt_hash,
                "locator_hash": self.main_locator_hash,
                "source_count": len(self.main_sources),
            },
            "supplement": {
                "purpose": SUPPLEMENT_PURPOSE,
                "descriptor_hash": self.supplement_descriptor_hash,
                "reference_set_hash": self.supplement_reference_set_hash,
                "reference_count": 6,
                "private_registry_hash": self.supplement_private_registry_hash,
                "locator_hash": self.supplement_locator_hash,
                "public_receipt_hash": self.supplement_public_receipt_hash,
                "final_audit_hash": self.supplement_final_audit_hash,
                "final_bundle_hash": self.supplement_final_bundle_hash,
                "final_receipt_hash": self.supplement_final_receipt_hash,
                "source_count": len(self.supplement_sources),
            },
            "combined_source_census_contract_hash": self.combined_source_census_contract_hash,
            "source_census_event_policy_hash": self.source_census_event_policy_hash,
            "cross_source_isolation_policy_hash": self.cross_source_isolation_policy_hash,
            "utility_event_aggregation_policy_hash": self.utility_event_aggregation_policy_hash,
            "metric_policy_hash": self.metric_policy_hash,
            "canonical_feature_schema_hash": self.canonical_feature_schema_hash,
            "runtime_feature_schema_hash": self.runtime_feature_schema_hash,
            "dataset_manifest_identity": self.dataset_manifest_identity,
            "split_identities": list(self.split_identities),
            "purge_policy_hash": self.purge_policy_hash,
            "main_sources": list(self.main_sources),
            "supplement_sources": list(self.supplement_sources),
            "evaluator_source_census": list(self.evaluator_source_census),
        }

    @property
    def bundle_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_public_dict(self) -> dict[str, object]:
        return {**self._payload(), "bundle_hash": self.bundle_hash}


_ISSUED_EVALUATOR_AUTHORITY_BUNDLES: dict[
    int, tuple[weakref.ReferenceType[EvaluatorAuthorityBundleV1], str]
] = {}


def _issue_evaluator_authority_bundle_v1(
    bundle: EvaluatorAuthorityBundleV1,
) -> EvaluatorAuthorityBundleV1:
    """Record exact process-local factory custody without retaining the object."""

    object_id = id(bundle)

    def cleanup(dead_ref: weakref.ReferenceType[EvaluatorAuthorityBundleV1]) -> None:
        issued = _ISSUED_EVALUATOR_AUTHORITY_BUNDLES.get(object_id)
        if issued is not None and issued[0] is dead_ref:
            _ISSUED_EVALUATOR_AUTHORITY_BUNDLES.pop(object_id, None)

    issued_ref = weakref.ref(bundle, cleanup)
    _ISSUED_EVALUATOR_AUTHORITY_BUNDLES[object_id] = (issued_ref, bundle.bundle_hash)
    return bundle


def _build_expected_evaluator_authority_bundle_v1(
    v4_authority: v4.UtilityProtocolV4CanonicalAuthority,
) -> EvaluatorAuthorityBundleV1:
    """Pure semantic replay constructor; it deliberately grants no custody."""

    try:
        v4.validate_utility_protocol_v4_authority(v4_authority)
    except (TypeError, ValueError) as exc:
        raise UtilityEvaluatorV1Error("EVALUATOR_V4_AUTHORITY_REJECTED") from exc
    if v4_authority.authority_hash != v4.CANONICAL_V4_AUTHORITY_HASH:
        raise UtilityEvaluatorV1Error("EVALUATOR_V4_AUTHORITY_REJECTED")
    if v4_authority.numeric_authority.descriptor_hash != MAIN_DESCRIPTOR_HASH:
        raise UtilityEvaluatorV1Error("EVALUATOR_MAIN_DESCRIPTOR_REJECTED")
    if v4_authority.numeric_authority.new_reference_set_hash != MAIN_REFERENCE_SET_HASH:
        raise UtilityEvaluatorV1Error("EVALUATOR_MAIN_REFERENCE_SET_REJECTED")
    if len(v4_authority.rule_descriptors) != 42:
        raise UtilityEvaluatorV1Error("EVALUATOR_COMMON_RELATION_COUNT_REJECTED")
    if supplement.SUPPLEMENT_DESCRIPTOR_HASH != SUPPLEMENT_DESCRIPTOR_HASH:
        raise UtilityEvaluatorV1Error("EVALUATOR_SUPPLEMENT_DESCRIPTOR_REJECTED")
    if supplement.SUPPLEMENT_REFERENCE_SET_HASH != SUPPLEMENT_REFERENCE_SET_HASH:
        raise UtilityEvaluatorV1Error("EVALUATOR_SUPPLEMENT_REFERENCE_SET_REJECTED")
    if supplement.SOURCE_CENSUS_EVENT_POLICY_HASH != SOURCE_CENSUS_EVENT_POLICY_HASH:
        raise UtilityEvaluatorV1Error("EVALUATOR_SOURCE_CENSUS_POLICY_REJECTED")
    if len(MAIN_SOURCES) != 9 or len(SUPPLEMENT_SOURCES) != 3 or len(EVALUATOR_SOURCE_CENSUS) != 12:
        raise UtilityEvaluatorV1Error("EVALUATOR_SOURCE_CENSUS_REJECTED")
    return EvaluatorAuthorityBundleV1(
        v4_authority,
        EVALUATOR_VERSION,
        v4.CANONICAL_V4_AUTHORITY_HASH,
        V4_R1_FOCUSED_AUDIT_HASH,
        V4_R1_FOCUSED_RECEIPT_HASH,
        v4.UTILITY_MAIN_PORTFOLIO,
        42,
        False,
        MAIN_DESCRIPTOR_HASH,
        MAIN_REFERENCE_SET_HASH,
        MAIN_PRIVATE_REGISTRY_HASH,
        MAIN_AUDIT_RECEIPT_HASH,
        MAIN_LOCATOR_HASH,
        SUPPLEMENT_DESCRIPTOR_HASH,
        SUPPLEMENT_REFERENCE_SET_HASH,
        SUPPLEMENT_PRIVATE_REGISTRY_HASH,
        SUPPLEMENT_LOCATOR_HASH,
        SUPPLEMENT_PUBLIC_RECEIPT_HASH,
        SUPPLEMENT_FINAL_AUDIT_HASH,
        SUPPLEMENT_FINAL_BUNDLE_HASH,
        SUPPLEMENT_FINAL_RECEIPT_HASH,
        COMBINED_SOURCE_CENSUS_CONTRACT_HASH,
        SOURCE_CENSUS_EVENT_POLICY_HASH,
        CROSS_SOURCE_ISOLATION_POLICY_HASH,
        v4.CORRECTED_EVENT_POLICY_HASH,
        v4.CORRECTED_METRIC_POLICY_HASH,
        CANONICAL_FEATURE_SCHEMA_HASH,
        RUNTIME_FEATURE_SCHEMA_HASH,
        v4.DATASET_MANIFEST_ID,
        (v4.INNER_SPLIT_ID, v4.OUTER_SPLIT_ID),
        v4.PURGE_POLICY_HASH,
        MAIN_SOURCES,
        SUPPLEMENT_SOURCES,
        EVALUATOR_SOURCE_CENSUS,
    )


def build_evaluator_authority_bundle_v1(
    v4_authority: v4.UtilityProtocolV4CanonicalAuthority,
) -> EvaluatorAuthorityBundleV1:
    """Issue an authoritative bundle from an exact current V4 R1 replay."""

    return _issue_evaluator_authority_bundle_v1(
        _build_expected_evaluator_authority_bundle_v1(v4_authority)
    )


def validate_evaluator_authority_bundle_v1(bundle: EvaluatorAuthorityBundleV1) -> str:
    if type(bundle) is not EvaluatorAuthorityBundleV1:
        raise UtilityEvaluatorV1Error("EVALUATOR_AUTHORITY_BUNDLE_TYPE_REJECTED")
    issued = _ISSUED_EVALUATOR_AUTHORITY_BUNDLES.get(id(bundle))
    if (
        issued is None
        or issued[0]() is not bundle
        or issued[1] != bundle.bundle_hash
    ):
        raise UtilityEvaluatorV1Error("EVALUATOR_AUTHORITY_BUNDLE_FACTORY_CUSTODY_REJECTED")
    expected = _build_expected_evaluator_authority_bundle_v1(bundle.v4_authority)
    if bundle != expected or bundle.to_public_dict() != expected.to_public_dict():
        raise UtilityEvaluatorV1Error("EVALUATOR_AUTHORITY_BUNDLE_REPLAY_REJECTED")
    return bundle.bundle_hash


@dataclass(frozen=True)
class SyntheticNumericRecordV1:
    authority_plane: str
    source: str
    relation_binding_hash: str | None
    numeric_role: str
    reference_identity: str
    value: int | float


def _validate_synthetic_value(role: str, value: object) -> int | float:
    if role == "source_step_threshold" or role == "target_noise_scale":
        return strict_float_v1(value, "synthetic numeric value", positive=True)
    if role == "source_stability_tolerance":
        return strict_float_v1(value, "synthetic numeric value", nonnegative=True)
    if role == "minimum_source_stability_fraction":
        result = strict_float_v1(value, "synthetic numeric value")
        if result != 0.8:
            raise UtilityEvaluatorV1Error("SYNTHETIC_FROZEN_CONSTANT_REJECTED")
        return result
    expected_ints = {
        "source_pre_window_seconds": 5,
        "source_post_window_seconds": 5,
        "source_refractory_seconds": 10,
        "cross_source_isolation_radius_seconds": 2,
        "target_baseline_window_seconds": 5,
        "target_response_window_seconds": 3,
    }
    if role in expected_ints:
        result = strict_int_v1(value, "synthetic numeric value")
        if result != expected_ints[role]:
            raise UtilityEvaluatorV1Error("SYNTHETIC_FROZEN_CONSTANT_REJECTED")
        return result
    raise UtilityEvaluatorV1Error("SYNTHETIC_NUMERIC_ROLE_REJECTED")


class SyntheticNumericResolverV1:
    """Validated all-or-nothing synthetic lookup; representation is redacted."""

    __slots__ = (
        "_bundle",
        "_bundle_hash",
        "_relation_values",
        "_relation_references",
        "_source_values",
        "_resolver_identity",
        "validated",
        "__weakref__",
    )

    def __init__(
        self,
        *,
        _factory_token: object,
        bundle: EvaluatorAuthorityBundleV1,
        bundle_hash: str,
        relation_values: dict[tuple[str, str], int | float],
        relation_references: dict[tuple[str, str], str],
        source_values: dict[tuple[str, str], float],
    ) -> None:
        if _factory_token is not _SYNTHETIC_RESOLVER_FACTORY_TOKEN:
            raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_FACTORY_CUSTODY_REJECTED")
        self._bundle = bundle
        self._bundle_hash = bundle_hash
        self._relation_values = relation_values
        self._relation_references = relation_references
        self._source_values = source_values
        self._resolver_identity = _synthetic_resolver_identity_v1(
            bundle_hash, relation_values, relation_references, source_values
        )
        self.validated = True

    @property
    def execution_mode(self) -> str:
        return SYNTHETIC_CONTRACT_ONLY

    @property
    def authority_identity(self) -> str:
        return SYNTHETIC_AUTHORITY_IDENTITY

    @property
    def bundle_hash(self) -> str:
        return self._bundle_hash

    @property
    def resolver_identity(self) -> str:
        return self._resolver_identity

    def __repr__(self) -> str:
        return "<SyntheticNumericResolverV1 validated=True values=REDACTED>"

    def __reduce__(self) -> object:
        raise UtilityEvaluatorV1Error("SYNTHETIC_PRIVATE_SERIALIZATION_PROHIBITED")

    def export_private_document(self) -> None:
        raise UtilityEvaluatorV1Error("SYNTHETIC_PRIVATE_SERIALIZATION_PROHIBITED")

    def relation_value(
        self,
        relation_binding_hash: str,
        role: str,
        reference_identity: str | None = None,
    ) -> int | float:
        validate_synthetic_numeric_resolver_v1(self, self._bundle)
        strict_str_v1(relation_binding_hash, "relation_binding_hash")
        strict_str_v1(role, "numeric_role")
        key = (relation_binding_hash, role)
        if key not in self._relation_values:
            raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_RELATION_LOOKUP_REJECTED")
        if reference_identity is not None:
            strict_str_v1(reference_identity, "reference_identity")
            if self._relation_references[key] != reference_identity:
                raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_REFERENCE_REJECTED")
        return self._relation_values[key]

    def source_census_value(self, source: str, role: str) -> float:
        validate_synthetic_numeric_resolver_v1(self, self._bundle)
        strict_str_v1(source, "source")
        strict_str_v1(role, "numeric_role")
        if role not in SOURCE_CENSUS_ROLES:
            raise UtilityEvaluatorV1Error("SYNTHETIC_SOURCE_CENSUS_ROLE_REJECTED")
        key = (source, role)
        if key not in self._source_values:
            raise UtilityEvaluatorV1Error("SYNTHETIC_SOURCE_CENSUS_LOOKUP_REJECTED")
        return self._source_values[key]


_SYNTHETIC_RESOLVER_FACTORY_TOKEN = object()
_ISSUED_SYNTHETIC_RESOLVERS: weakref.WeakKeyDictionary[
    SyntheticNumericResolverV1, tuple[str, str]
] = weakref.WeakKeyDictionary()


def _synthetic_resolver_identity_v1(
    bundle_hash: str,
    relation_values: dict[tuple[str, str], int | float],
    relation_references: dict[tuple[str, str], str],
    source_values: dict[tuple[str, str], float],
) -> str:
    """Hash private synthetic state without returning or serializing values."""

    return stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_evaluator_synthetic_numeric_resolver_v1",
            "execution_mode": SYNTHETIC_CONTRACT_ONLY,
            "synthetic_authority_identity": SYNTHETIC_AUTHORITY_IDENTITY,
            "bundle_hash": bundle_hash,
            "relation_records": [
                {
                    "relation_binding_hash": relation,
                    "numeric_role": role,
                    "reference_identity": relation_references[(relation, role)],
                    "synthetic_value": value,
                }
                for (relation, role), value in sorted(relation_values.items())
            ],
            "source_projection": [
                {"source": source, "numeric_role": role, "synthetic_value": value}
                for (source, role), value in sorted(source_values.items())
            ],
            "scientific_eligibility": False,
        }
    )


def validate_synthetic_numeric_resolver_v1(
    resolver: SyntheticNumericResolverV1,
    bundle: EvaluatorAuthorityBundleV1,
) -> str:
    """Replay factory custody and exact closed synthetic numeric state."""

    if type(resolver) is not SyntheticNumericResolverV1:
        raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_TYPE_REJECTED")
    issued = _ISSUED_SYNTHETIC_RESOLVERS.get(resolver)
    if issued is None:
        raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_FACTORY_CUSTODY_REJECTED")
    bundle_hash = validate_evaluator_authority_bundle_v1(bundle)
    if (
        resolver.validated is not True
        or resolver._bundle is not bundle
        or resolver._bundle_hash != bundle_hash
        or issued[0] != bundle_hash
        or resolver.execution_mode != SYNTHETIC_CONTRACT_ONLY
        or resolver.authority_identity != SYNTHETIC_AUTHORITY_IDENTITY
    ):
        raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_CUSTODY_REJECTED")
    if (
        type(resolver._relation_values) is not dict
        or type(resolver._relation_references) is not dict
        or type(resolver._source_values) is not dict
    ):
        raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_STATE_TYPE_REJECTED")

    expected_relations: dict[tuple[str, str], tuple[str, str]] = {}
    for rule in bundle.v4_authority.rule_descriptors:
        for role, reference in rule.numeric_reference_bindings:
            expected_relations[(rule.relation_binding_hash, role)] = (rule.source, reference)
    if (
        len(expected_relations) != 420
        or set(resolver._relation_values) != set(expected_relations)
        or set(resolver._relation_references) != set(expected_relations)
    ):
        raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_RELATION_CLOSURE_REJECTED")

    projected: dict[tuple[str, str], list[float]] = {}
    for key, (source, reference) in expected_relations.items():
        relation, role = key
        if resolver._relation_references.get((relation, role)) != reference:
            raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_REFERENCE_REPLAY_REJECTED")
        value = _validate_synthetic_value(role, resolver._relation_values[key])
        if role in SOURCE_CENSUS_ROLES:
            projected.setdefault((source, role), []).append(value)  # type: ignore[arg-type]

    expected_source_keys = {
        (source, role)
        for source in EVALUATOR_SOURCE_CENSUS
        for role in SOURCE_CENSUS_ROLES
    }
    if set(resolver._source_values) != expected_source_keys:
        raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_SOURCE_CLOSURE_REJECTED")
    for key, values in projected.items():
        if len({value.hex() for value in values}) != 1:
            raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_MAIN_PROJECTION_REJECTED")
        observed = _validate_synthetic_value(key[1], resolver._source_values[key])
        if observed.hex() != values[0].hex():  # type: ignore[union-attr]
            raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_MAIN_PROJECTION_REJECTED")
    for source in SUPPLEMENT_SOURCES:
        for role in SOURCE_CENSUS_ROLES:
            _validate_synthetic_value(role, resolver._source_values[(source, role)])

    observed_identity = _synthetic_resolver_identity_v1(
        resolver._bundle_hash,
        resolver._relation_values,
        resolver._relation_references,
        resolver._source_values,
    )
    if resolver._resolver_identity != observed_identity or issued[1] != observed_identity:
        raise UtilityEvaluatorV1Error("SYNTHETIC_RESOLVER_IDENTITY_REJECTED")
    return observed_identity


def build_synthetic_numeric_resolver_v1(
    bundle: EvaluatorAuthorityBundleV1,
    main_records: tuple[SyntheticNumericRecordV1, ...],
    supplement_records: tuple[SyntheticNumericRecordV1, ...],
) -> SyntheticNumericResolverV1:
    bundle_hash = validate_evaluator_authority_bundle_v1(bundle)
    strict_tuple_v1(main_records, "main_records")
    strict_tuple_v1(supplement_records, "supplement_records")
    if any(type(item) is not SyntheticNumericRecordV1 for item in main_records + supplement_records):
        raise UtilityEvaluatorV1Error("SYNTHETIC_NUMERIC_RECORD_TYPE_REJECTED")

    expected_main: dict[tuple[str, str], tuple[str, str]] = {}
    for rule in bundle.v4_authority.rule_descriptors:
        for role, reference in rule.numeric_reference_bindings:
            expected_main[(rule.relation_binding_hash, role)] = (rule.source, reference)
    if len(expected_main) != 420 or len(main_records) != 420:
        raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_REGISTRY_CLOSURE_REJECTED")

    relation_values: dict[tuple[str, str], int | float] = {}
    relation_references: dict[tuple[str, str], str] = {}
    main_source_groups: dict[tuple[str, str], list[float]] = {}
    for record in main_records:
        if record.authority_plane != "SYNTHETIC_MAIN_420":
            raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_PLANE_REJECTED")
        if record.relation_binding_hash is None:
            raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_RELATION_REJECTED")
        key = (record.relation_binding_hash, record.numeric_role)
        if key not in expected_main or key in relation_values:
            raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_KEY_REJECTED")
        source, reference = expected_main[key]
        if record.source != source or record.reference_identity != reference:
            raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_BINDING_REJECTED")
        value = _validate_synthetic_value(record.numeric_role, record.value)
        relation_values[key] = value
        relation_references[key] = reference
        if record.numeric_role in SOURCE_CENSUS_ROLES:
            main_source_groups.setdefault((source, record.numeric_role), []).append(value)  # type: ignore[arg-type]
    if set(relation_values) != set(expected_main):
        raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_REGISTRY_CLOSURE_REJECTED")

    source_values: dict[tuple[str, str], float] = {}
    expected_main_groups = {(source, role) for source in MAIN_SOURCES for role in SOURCE_CENSUS_ROLES}
    if set(main_source_groups) != expected_main_groups:
        raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_SOURCE_PROJECTION_REJECTED")
    for key, values in main_source_groups.items():
        if len({value.hex() for value in values}) != 1:
            raise UtilityEvaluatorV1Error("SYNTHETIC_MAIN_SOURCE_PROJECTION_REJECTED")
        source_values[key] = values[0]

    expected_supplement = {
        (source, role): reference
        for source in SUPPLEMENT_SOURCES
        for role, reference in (
            (role, supplement.supplement_reference_identity_v1(source, role))
            for role in SOURCE_CENSUS_ROLES
        )
    }
    if len(supplement_records) != 6:
        raise UtilityEvaluatorV1Error("SYNTHETIC_SUPPLEMENT_REGISTRY_CLOSURE_REJECTED")
    observed_supplement: set[tuple[str, str]] = set()
    for record in supplement_records:
        if record.authority_plane != SUPPLEMENT_PURPOSE or record.relation_binding_hash is not None:
            raise UtilityEvaluatorV1Error("SYNTHETIC_SUPPLEMENT_PLANE_REJECTED")
        key = (record.source, record.numeric_role)
        if key not in expected_supplement or key in observed_supplement:
            raise UtilityEvaluatorV1Error("SYNTHETIC_SUPPLEMENT_KEY_REJECTED")
        if record.reference_identity != expected_supplement[key]:
            raise UtilityEvaluatorV1Error("SYNTHETIC_SUPPLEMENT_REFERENCE_REJECTED")
        source_values[key] = _validate_synthetic_value(record.numeric_role, record.value)  # type: ignore[assignment]
        observed_supplement.add(key)
    if observed_supplement != set(expected_supplement):
        raise UtilityEvaluatorV1Error("SYNTHETIC_SUPPLEMENT_REGISTRY_CLOSURE_REJECTED")

    resolver = SyntheticNumericResolverV1(
        _factory_token=_SYNTHETIC_RESOLVER_FACTORY_TOKEN,
        bundle=bundle,
        bundle_hash=bundle_hash,
        relation_values=relation_values,
        relation_references=relation_references,
        source_values=source_values,
    )
    _ISSUED_SYNTHETIC_RESOLVERS[resolver] = (bundle_hash, resolver.resolver_identity)
    validate_synthetic_numeric_resolver_v1(resolver, bundle)
    return resolver


def open_real_private_numeric_resolver_v1(
    *,
    authority_bundle: EvaluatorAuthorityBundleV1,
    future_execution_authorization: object,
    main_locator_path: object,
    supplement_locator_path: object,
) -> None:
    """Fail before path inspection until a separate execution task authorizes it."""

    del authority_bundle, future_execution_authorization, main_locator_path, supplement_locator_path
    if not REAL_UTILITY_EXECUTION_AUTHORIZED:
        raise UtilityEvaluatorV1Error("REAL_UTILITY_EXECUTION_NOT_AUTHORIZED")
    raise UtilityEvaluatorV1Error("REAL_PRIVATE_RESOLVER_NOT_IMPLEMENTED")


__all__ = [
    "EvaluatorAuthorityBundleV1",
    "SyntheticNumericRecordV1",
    "SyntheticNumericResolverV1",
    "build_evaluator_authority_bundle_v1",
    "validate_evaluator_authority_bundle_v1",
    "build_synthetic_numeric_resolver_v1",
    "validate_synthetic_numeric_resolver_v1",
    "open_real_private_numeric_resolver_v1",
    "MAIN_SOURCES",
    "SUPPLEMENT_SOURCES",
    "EVALUATOR_SOURCE_CENSUS",
    "SOURCE_CENSUS_ROLES",
    "MAIN_NUMERIC_ROLES",
    "MAIN_DESCRIPTOR_HASH",
    "MAIN_REFERENCE_SET_HASH",
    "SUPPLEMENT_DESCRIPTOR_HASH",
    "SUPPLEMENT_REFERENCE_SET_HASH",
    "COMBINED_SOURCE_CENSUS_CONTRACT_HASH",
    "SOURCE_CENSUS_EVENT_POLICY_HASH",
    "CROSS_SOURCE_ISOLATION_POLICY_HASH",
    "SUPPLEMENT_PURPOSE",
]
