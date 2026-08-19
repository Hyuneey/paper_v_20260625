"""Normal-only numeric supplement for the V3 twelve-source event census.

The audited MAIN numeric authority remains the sole authority for COMMON-42
rule evaluation.  This module adds exactly two source-calibration roles for
the three V3 event-census sources that are outside the COMMON relation
footprint.  Importing the module performs no I/O and grants no utility,
detector, label, test-data, provider, or LLM authority.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence
from uuid import uuid4

from paperworks.v6.common import canonical_json_v1, stable_hash_v1
from paperworks.v6.task039e3_r2r_utility_normal_only_authority_v1 import (
    CALIBRATION_POLICY_HASH,
    NORMAL_INPUT_IDENTITY_SET_HASH,
    NORMAL_TRAIN1_IDENTITY,
    NORMAL_TRAIN2_IDENTITY,
    NormalOnlyAuthorityDefinitionV1,
    build_common42_authority_v1,
    derive_source_parameters_normal_only_v1,
    load_verified_normal_features_v1,
    validate_canonical_common42_authority_v1,
    validate_private_registry_document_v1 as validate_main_private_registry_document_v1,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    UTILITY_SOURCE_UNIVERSE_V3,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v4 import (
    CANONICAL_V4_AUTHORITY_HASH,
    CORRECTED_EVENT_POLICY_HASH,
    MATERIALIZED_AUTHORITY_AUDIT_RECEIPT_HASH,
    NumericAuthorityDescriptorV4,
    build_common42_public_authority_v4,
    build_numeric_authority_descriptor_v4,
    validate_materialized_authority_audit_receipt_v4,
    validate_numeric_authority_descriptor_v4,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-SOURCE-CENSUS-SUPPLEMENT-V1-END-TO-END-CLOSURE"
AUTHORITY_VERSION = "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1"
SCHEMA_VERSION = "1.0.0"
PURPOSE = "CROSS_SOURCE_ISOLATION_EVENT_CENSUS_ONLY"
MATERIALIZATION_SCOPE = "NORMAL_TRAIN1_TRAIN2_THREE_SOURCE_CENSUS_SUPPLEMENT_ONLY"
PRIVATE_AUTHORITY_ENV = "TASK039E3_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1"

V4_R1_AUTHORITY_HASH = CANONICAL_V4_AUTHORITY_HASH
V4_R1_FOCUSED_AUDIT_HASH = "8c66590f222ad656add781745a361e483ba0ecd3c42bccbfa11f08cfaa6550ae"
V4_R1_FOCUSED_RECEIPT_HASH = "09cf661a21cb4bd0d5ad356c2cf725264d76aeaffc7963858425e88267717509"
MAIN_AUTHORITY_VERSION = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1"
MAIN_PRIVATE_REGISTRY_HASH = "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
MAIN_AUDIT_RECEIPT_HASH = MATERIALIZED_AUTHORITY_AUDIT_RECEIPT_HASH
MAIN_DESCRIPTOR_HASH = "665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928"
MAIN_RECORD_COUNT = 420
MAIN_SOURCE_COUNT = 9
MAIN_IDENTITY_AUDIT_HASH = "8b1bfe945ce056bd1120d141abf2095c95df1af21f62f853e285040f1c64a45b"

SUPPLEMENT_SOURCES = ("P1_FCV02Z", "P1_PCV02Z", "P1_PP04")
SUPPLEMENT_ROLES = ("source_step_threshold", "source_stability_tolerance")
MAIN_SOURCES = tuple(sorted(set(UTILITY_SOURCE_UNIVERSE_V3) - set(SUPPLEMENT_SOURCES)))
SUPPLEMENT_RECORD_COUNT = 6
V3_SOURCE_COUNT = 12
COMBINED_SOURCE_COUNT = 12

NORMAL_ONLY_SOURCE_PATH = "src/paperworks/v6/task039e3_r2r_utility_normal_only_authority_v1.py"
NORMAL_ONLY_SOURCE_BLOB = "5e6d52fdfadada7373c50c382a347930f3384e24"
NORMAL_ONLY_SOURCE_RAW_SHA256 = "1b15098e9f8c75a76ad98f7a0ef998af86470b195d035ffab08e9f185fe1a3d9"
CALIBRATION_DEPENDENCY_PATH = "src/paperworks/v6/relation_profiling_protocol_v1.py"
CALIBRATION_DEPENDENCY_BLOB = "7d7da2c07cbd5207edc223b4a854885f30b584b3"
CALIBRATION_DEPENDENCY_RAW_SHA256 = "ba7a7ea29eb0d68077a51442691d201915470d16dca751dff3c214a7ead3c529"
V3_SOURCE_PATH = "src/paperworks/v6/task039e3_r2r_utility_protocol_v3.py"
V3_SOURCE_BLOB = "d233cb05ce2a10930ee20952f3ce6784f3ece8bf"
V3_SOURCE_RAW_SHA256 = "85fb16f257a957736548ddf852f6e594be06fe0800b94f066c54b9eb3e988a3e"
V4_R1_SOURCE_PATH = "src/paperworks/v6/task039e3_r2r_utility_protocol_v4.py"
V4_R1_SOURCE_BLOB = "8ce6e56215246a5ec14ae148de20cdf0680c1658"
V4_R1_SOURCE_RAW_SHA256 = "880bc1b08ea9941349042d664314184d8afa8337c13f778563b90404436429f9"
SUPPLEMENT_SOURCE_PATH = "src/paperworks/v6/task039e3_r2r_utility_source_census_supplement_v1.py"
INDEPENDENT_TEST_PATH = "tests/test_task039e3_r2r_utility_source_census_supplement_v1_independent.py"

COVERAGE_DECISION_RELATIVE_PATH = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1_COVERAGE_DECISION.json"
)
COVERAGE_DECISION_HASH = "57242d1b03a801a6df321d816f3a7c99f84544b0790487f272e6f08385ed3fdb"
AUTHORIZATION_RELATIVE_PATH = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1_MATERIALIZATION_AUTHORIZATION.json"
)
PUBLIC_RECEIPT_RELATIVE_PATH = (
    "docs/task_reports/TASK-039E3_R2R_UTILITY_SOURCE_CENSUS_SUPPLEMENT_V1_MATERIALIZATION_PUBLIC_RECEIPT.json"
)

SOURCE_CENSUS_EVENT_POLICY = {
    "policy_version": "TASK039E3_SOURCE_CENSUS_EVENT_POLICY_V1",
    "source_pre_window_seconds": 5,
    "source_post_window_seconds": 5,
    "minimum_source_stability_fraction": 0.8,
    "source_refractory_seconds": 10,
    "cross_source_isolation_radius_seconds": 2,
    "clustering": "single_link_within_refractory_window",
    "retention": "largest_absolute_step_amplitude",
    "exact_amplitude_tie": "earliest_physical_index",
    "v4_event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
}
SOURCE_CENSUS_EVENT_POLICY_HASH = stable_hash_v1(SOURCE_CENSUS_EVENT_POLICY)
SOURCE_CENSUS_PURPOSE_IDENTITY = stable_hash_v1(
    {
        "authority_version": AUTHORITY_VERSION,
        "purpose": PURPOSE,
        "sources": list(SUPPLEMENT_SOURCES),
        "roles": list(SUPPLEMENT_ROLES),
        "event_policy_hash": SOURCE_CENSUS_EVENT_POLICY_HASH,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
    }
)
MAIN_SOURCE_COLLAPSE_POLICY_HASH = stable_hash_v1(
    {
        "policy_version": "TASK039E3_MAIN_SOURCE_CENSUS_COLLAPSE_V1",
        "main_descriptor_hash": MAIN_DESCRIPTOR_HASH,
        "main_private_registry_hash": MAIN_PRIVATE_REGISTRY_HASH,
        "main_audit_receipt_hash": MAIN_AUDIT_RECEIPT_HASH,
        "main_identity_audit_hash": MAIN_IDENTITY_AUDIT_HASH,
        "source_groups": 9,
        "within_source_inconsistencies": 0,
        "applicable_records": "all_canonical_relation_records_for_source_and_role",
        "equality": "one_exact_float_hex_identity",
        "caller_representative_relation_authorized": False,
    }
)


class SourceCensusSupplementV1Error(ValueError):
    """A fail-closed coverage, authority, materialization, or custody error."""


def _strict_str(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise SourceCensusSupplementV1Error(f"{name} must be an exact nonempty string")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise SourceCensusSupplementV1Error(f"{name} must be an exact boolean")
    return value


def _strict_int(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise SourceCensusSupplementV1Error(f"{name} must be an exact integer at least {minimum}")
    return value


def _sha(value: object, name: str) -> str:
    if type(value) is not str or len(value) != 64 or value.lower() != value:
        raise SourceCensusSupplementV1Error(f"{name} must be a lowercase SHA-256 identity")
    try:
        int(value, 16)
    except ValueError as exc:
        raise SourceCensusSupplementV1Error(f"{name} must be hexadecimal") from exc
    return value


def _git_oid(value: object, name: str) -> str:
    if type(value) is not str or len(value) != 40 or value.lower() != value:
        raise SourceCensusSupplementV1Error(f"{name} must be a lowercase Git object identity")
    try:
        int(value, 16)
    except ValueError as exc:
        raise SourceCensusSupplementV1Error(f"{name} must be hexadecimal") from exc
    return value


def _exact_float(value: object, name: str, *, positive: bool) -> float:
    if type(value) is not float or not math.isfinite(value):
        raise SourceCensusSupplementV1Error(f"{name} must be an exact finite float")
    if (positive and value <= 0.0) or (not positive and value < 0.0):
        raise SourceCensusSupplementV1Error(f"{name} is outside its numeric domain")
    return value


def _timezone_aware(value: object, name: str) -> str:
    text = _strict_str(value, name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SourceCensusSupplementV1Error(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise SourceCensusSupplementV1Error(f"{name} must be timezone-aware")
    return text


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _self_hash(document: Mapping[str, Any]) -> str:
    return stable_hash_v1({key: value for key, value in document.items() if key != "artifact_hash"})


def _validate_self_hashed_dict(
    document: Mapping[str, Any], *, allowed_keys: frozenset[str], name: str
) -> str:
    if type(document) is not dict or set(document) != allowed_keys:
        raise SourceCensusSupplementV1Error(f"{name} schema is not exactly closed")
    observed = _sha(document.get("artifact_hash"), f"{name} hash")
    if _self_hash(document) != observed:
        raise SourceCensusSupplementV1Error(f"{name} self-hash differs")
    return observed


def supplement_reference_identity_v1(source: object, numeric_role: object) -> str:
    source_name = _strict_str(source, "supplement source")
    role = _strict_str(numeric_role, "supplement numeric role")
    if source_name not in SUPPLEMENT_SOURCES:
        raise SourceCensusSupplementV1Error("source is outside the exact supplemental set")
    if role not in SUPPLEMENT_ROLES:
        raise SourceCensusSupplementV1Error("numeric role is outside supplement scope")
    digest = stable_hash_v1(
        {
            "authority_version": AUTHORITY_VERSION,
            "source_identity": source_name,
            "numeric_role": role,
            "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
            "calibration_policy_hash": CALIBRATION_POLICY_HASH,
            "source_census_purpose_identity": SOURCE_CENSUS_PURPOSE_IDENTITY,
        }
    )
    return f"{AUTHORITY_VERSION}:{digest}"


def supplement_provenance_identity_v1(source: object, numeric_role: object) -> str:
    source_name = _strict_str(source, "supplement source")
    role = _strict_str(numeric_role, "supplement numeric role")
    if source_name not in SUPPLEMENT_SOURCES or role not in SUPPLEMENT_ROLES:
        raise SourceCensusSupplementV1Error("supplement provenance scope differs")
    return stable_hash_v1(
        {
            "authority_version": AUTHORITY_VERSION,
            "purpose": PURPOSE,
            "source_identity": source_name,
            "numeric_role": role,
            "normal_train1_identity": NORMAL_TRAIN1_IDENTITY.sha256,
            "normal_train2_identity": NORMAL_TRAIN2_IDENTITY.sha256,
            "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
            "calibration_policy_hash": CALIBRATION_POLICY_HASH,
            "source_function": "derive_source_parameters_normal_only_v1",
        }
    )


SUPPLEMENT_REFERENCE_IDENTITIES = tuple(
    supplement_reference_identity_v1(source, role)
    for source in SUPPLEMENT_SOURCES
    for role in SUPPLEMENT_ROLES
)
SUPPLEMENT_REFERENCE_SET_HASH = stable_hash_v1(
    {
        "authority_version": AUTHORITY_VERSION,
        "reference_count": SUPPLEMENT_RECORD_COUNT,
        "reference_identities": sorted(SUPPLEMENT_REFERENCE_IDENTITIES),
    }
)


@dataclass(frozen=True)
class SourceCensusCoverageDecisionV1:
    v3_sources: tuple[str, ...]
    main_sources: tuple[str, ...]
    missing_sources: tuple[str, ...]
    existing_final_runtime_authority_found: bool
    selected_route: str

    def __post_init__(self) -> None:
        if type(self.v3_sources) is not tuple or type(self.main_sources) is not tuple or type(self.missing_sources) is not tuple:
            raise SourceCensusSupplementV1Error("coverage source containers must be exact tuples")
        if any(type(item) is not str for item in (*self.v3_sources, *self.main_sources, *self.missing_sources)):
            raise SourceCensusSupplementV1Error("coverage source identities must be exact strings")
        _strict_bool(self.existing_final_runtime_authority_found, "existing authority flag")
        _strict_str(self.selected_route, "selected route")

    @property
    def decision_hash(self) -> str:
        return stable_hash_v1(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "artifact_type": "task039e3_r2r_utility_source_census_coverage_decision_v1",
            "schema_version": SCHEMA_VERSION,
            "v3_sources": list(self.v3_sources),
            "main_sources": list(self.main_sources),
            "missing_sources": list(self.missing_sources),
            "existing_final_runtime_authority_found": self.existing_final_runtime_authority_found,
            "selected_route": self.selected_route,
        }
        return {**payload, "decision_hash": self.decision_hash} if include_hash else payload


def build_source_census_coverage_decision_v1(
    *,
    executable_equivalence: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
    materialized_main_audit_receipt: Mapping[str, Any],
    br2_config: Mapping[str, Any],
) -> SourceCensusCoverageDecisionV1:
    """Derive the gap from canonical public authorities only."""

    validate_materialized_authority_audit_receipt_v4(materialized_main_audit_receipt)
    common = build_common42_public_authority_v4(executable_equivalence, evidence_manifest)
    main_descriptor = build_numeric_authority_descriptor_v4(common, materialized_main_audit_receipt)
    if validate_numeric_authority_descriptor_v4(main_descriptor, common, materialized_main_audit_receipt) != MAIN_DESCRIPTOR_HASH:
        raise SourceCensusSupplementV1Error("MAIN numeric descriptor differs")
    v3_sources = tuple(sorted(UTILITY_SOURCE_UNIVERSE_V3))
    main_sources = tuple(sorted({relation.source for relation in common.relations}))
    missing = tuple(sorted(set(v3_sources) - set(main_sources)))
    parameter_authority = br2_config.get("parameter_authority") if type(br2_config) is dict else None
    if type(parameter_authority) is not dict or set(parameter_authority) != {
        "agent_selectable", "final_calibration", "implicit_promotion", "parameter_class", "runtime"
    }:
        raise SourceCensusSupplementV1Error("BR2 parameter authority schema differs")
    if (
        parameter_authority.get("parameter_class") != "feasibility_screening"
        or parameter_authority.get("final_calibration") is not False
        or parameter_authority.get("runtime") is not False
        or parameter_authority.get("implicit_promotion") is not False
    ):
        raise SourceCensusSupplementV1Error("BR2 screening authority cannot be classified safely")
    decision = SourceCensusCoverageDecisionV1(
        v3_sources,
        main_sources,
        missing,
        False,
        "CREATE_SUPPLEMENTAL_SOURCE_CENSUS_AUTHORITY_V1",
    )
    validate_source_census_coverage_decision_v1(decision)
    return decision


def validate_source_census_coverage_decision_v1(decision: SourceCensusCoverageDecisionV1) -> str:
    if type(decision) is not SourceCensusCoverageDecisionV1:
        raise SourceCensusSupplementV1Error("coverage decision type differs")
    if (
        decision.v3_sources != tuple(sorted(UTILITY_SOURCE_UNIVERSE_V3))
        or len(decision.v3_sources) != V3_SOURCE_COUNT
        or len(decision.main_sources) != MAIN_SOURCE_COUNT
        or decision.missing_sources != SUPPLEMENT_SOURCES
        or set(decision.v3_sources) != set(decision.main_sources) | set(decision.missing_sources)
        or decision.existing_final_runtime_authority_found is not False
        or decision.selected_route != "CREATE_SUPPLEMENTAL_SOURCE_CENSUS_AUTHORITY_V1"
    ):
        raise SourceCensusSupplementV1Error("coverage decision differs from canonical authority")
    return decision.decision_hash


@dataclass(frozen=True)
class SupplementAuthorityDefinitionV1:
    authority_version: str
    purpose: str
    sources: tuple[str, ...]
    roles: tuple[str, ...]
    reference_identities: tuple[str, ...]
    reference_set_hash: str
    normal_input_identity_set_hash: str
    calibration_policy_hash: str
    event_policy_hash: str
    purpose_identity: str

    @property
    def descriptor_hash(self) -> str:
        return stable_hash_v1(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "artifact_type": "task039e3_r2r_utility_source_census_supplement_definition_v1",
            "schema_version": SCHEMA_VERSION,
            "authority_version": self.authority_version,
            "purpose": self.purpose,
            "sources": list(self.sources),
            "roles": list(self.roles),
            "reference_identities": list(self.reference_identities),
            "reference_set_hash": self.reference_set_hash,
            "normal_input_identity_set_hash": self.normal_input_identity_set_hash,
            "calibration_policy_hash": self.calibration_policy_hash,
            "event_policy_hash": self.event_policy_hash,
            "purpose_identity": self.purpose_identity,
        }
        return {**payload, "descriptor_hash": self.descriptor_hash} if include_hash else payload


def build_supplement_authority_definition_v1() -> SupplementAuthorityDefinitionV1:
    definition = SupplementAuthorityDefinitionV1(
        AUTHORITY_VERSION,
        PURPOSE,
        SUPPLEMENT_SOURCES,
        SUPPLEMENT_ROLES,
        SUPPLEMENT_REFERENCE_IDENTITIES,
        SUPPLEMENT_REFERENCE_SET_HASH,
        NORMAL_INPUT_IDENTITY_SET_HASH,
        CALIBRATION_POLICY_HASH,
        SOURCE_CENSUS_EVENT_POLICY_HASH,
        SOURCE_CENSUS_PURPOSE_IDENTITY,
    )
    validate_supplement_authority_definition_v1(definition)
    return definition


def validate_supplement_authority_definition_v1(definition: SupplementAuthorityDefinitionV1) -> str:
    if type(definition) is not SupplementAuthorityDefinitionV1:
        raise SourceCensusSupplementV1Error("supplement definition type differs")
    if (
        definition.authority_version != AUTHORITY_VERSION
        or definition.purpose != PURPOSE
        or type(definition.sources) is not tuple
        or definition.sources != SUPPLEMENT_SOURCES
        or type(definition.roles) is not tuple
        or definition.roles != SUPPLEMENT_ROLES
        or type(definition.reference_identities) is not tuple
        or definition.reference_identities != SUPPLEMENT_REFERENCE_IDENTITIES
        or len(set(definition.reference_identities)) != SUPPLEMENT_RECORD_COUNT
        or definition.reference_set_hash != SUPPLEMENT_REFERENCE_SET_HASH
        or definition.normal_input_identity_set_hash != NORMAL_INPUT_IDENTITY_SET_HASH
        or definition.calibration_policy_hash != CALIBRATION_POLICY_HASH
        or definition.event_policy_hash != SOURCE_CENSUS_EVENT_POLICY_HASH
        or definition.purpose_identity != SOURCE_CENSUS_PURPOSE_IDENTITY
    ):
        raise SourceCensusSupplementV1Error("supplement definition replay differs")
    return definition.descriptor_hash


SUPPLEMENT_DESCRIPTOR_HASH = build_supplement_authority_definition_v1().descriptor_hash


def _validate_role_value(role: str, value: object) -> float:
    if role == "source_step_threshold":
        return _exact_float(value, role, positive=True)
    if role == "source_stability_tolerance":
        return _exact_float(value, role, positive=False)
    raise SourceCensusSupplementV1Error("target, T2, Direct-number, or unknown role is prohibited")


def derive_supplement_role_values_v1(
    train1_features: Mapping[str, Sequence[float]],
    train2_features: Mapping[str, Sequence[float]],
) -> dict[tuple[str, str], float]:
    """Delegate exactly three source calibrations to the audited implementation."""

    if type(train1_features) is not dict or type(train2_features) is not dict:
        raise SourceCensusSupplementV1Error("normal feature mappings must be exact dictionaries")
    if set(train1_features) != set(SUPPLEMENT_SOURCES) or set(train2_features) != set(SUPPLEMENT_SOURCES):
        raise SourceCensusSupplementV1Error("normal feature mapping differs from exact supplement")
    result: dict[tuple[str, str], float] = {}
    for source in SUPPLEMENT_SOURCES:
        threshold, tolerance = derive_source_parameters_normal_only_v1(
            train1_features[source], train2_features[source]
        )
        result[(source, "source_step_threshold")] = _validate_role_value(
            "source_step_threshold", threshold
        )
        result[(source, "source_stability_tolerance")] = _validate_role_value(
            "source_stability_tolerance", tolerance
        )
    if len(result) != SUPPLEMENT_RECORD_COUNT:
        raise SourceCensusSupplementV1Error("supplement calibration cardinality differs")
    return result


PRIVATE_REGISTRY_KEYS = frozenset(
    {
        "artifact_type",
        "schema_version",
        "authority_version",
        "purpose",
        "supplement_descriptor_hash",
        "reference_set_hash",
        "normal_input_identity_set_hash",
        "calibration_policy_hash",
        "event_policy_hash",
        "source_count",
        "role_count",
        "record_count",
        "records",
        "artifact_hash",
    }
)
PRIVATE_RECORD_KEYS = frozenset(
    {
        "schema_version",
        "authority_version",
        "purpose",
        "source_identity",
        "numeric_role",
        "new_reference_identity",
        "numeric_value",
        "normal_train1_identity",
        "normal_train2_identity",
        "normal_input_identity_set_hash",
        "calibration_policy_hash",
        "provenance_identity",
        "record_hash",
    }
)


def build_supplement_private_registry_document_v1(
    definition: SupplementAuthorityDefinitionV1,
    role_values: Mapping[tuple[str, str], object],
) -> dict[str, Any]:
    validate_supplement_authority_definition_v1(definition)
    expected = {(source, role) for source in SUPPLEMENT_SOURCES for role in SUPPLEMENT_ROLES}
    if type(role_values) is not dict or set(role_values) != expected:
        raise SourceCensusSupplementV1Error("supplement values have missing or unexpected keys")
    records: list[dict[str, Any]] = []
    for source in SUPPLEMENT_SOURCES:
        for role in SUPPLEMENT_ROLES:
            value = _validate_role_value(role, role_values[(source, role)])
            payload: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "authority_version": AUTHORITY_VERSION,
                "purpose": PURPOSE,
                "source_identity": source,
                "numeric_role": role,
                "new_reference_identity": supplement_reference_identity_v1(source, role),
                "numeric_value": value,
                "normal_train1_identity": NORMAL_TRAIN1_IDENTITY.sha256,
                "normal_train2_identity": NORMAL_TRAIN2_IDENTITY.sha256,
                "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
                "calibration_policy_hash": CALIBRATION_POLICY_HASH,
                "provenance_identity": supplement_provenance_identity_v1(source, role),
            }
            payload["record_hash"] = stable_hash_v1(payload)
            records.append(payload)
    document: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_utility_source_census_supplement_private_registry_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "purpose": PURPOSE,
        "supplement_descriptor_hash": definition.descriptor_hash,
        "reference_set_hash": definition.reference_set_hash,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "event_policy_hash": SOURCE_CENSUS_EVENT_POLICY_HASH,
        "source_count": len(SUPPLEMENT_SOURCES),
        "role_count": len(SUPPLEMENT_ROLES),
        "record_count": len(records),
        "records": records,
    }
    document["artifact_hash"] = stable_hash_v1(document)
    validate_supplement_private_registry_document_v1(document, definition)
    return document


def validate_supplement_private_registry_document_v1(
    document: Mapping[str, Any], definition: SupplementAuthorityDefinitionV1 | None = None
) -> str:
    definition = definition or build_supplement_authority_definition_v1()
    validate_supplement_authority_definition_v1(definition)
    observed = _validate_self_hashed_dict(
        document, allowed_keys=PRIVATE_REGISTRY_KEYS, name="supplement private registry"
    )
    if (
        document.get("artifact_type")
        != "task039e3_r2r_utility_source_census_supplement_private_registry_v1"
        or document.get("schema_version") != SCHEMA_VERSION
        or document.get("authority_version") != AUTHORITY_VERSION
        or document.get("purpose") != PURPOSE
        or document.get("supplement_descriptor_hash") != definition.descriptor_hash
        or document.get("reference_set_hash") != SUPPLEMENT_REFERENCE_SET_HASH
        or document.get("normal_input_identity_set_hash") != NORMAL_INPUT_IDENTITY_SET_HASH
        or document.get("calibration_policy_hash") != CALIBRATION_POLICY_HASH
        or document.get("event_policy_hash") != SOURCE_CENSUS_EVENT_POLICY_HASH
        or type(document.get("source_count")) is not int
        or document.get("source_count") != 3
        or type(document.get("role_count")) is not int
        or document.get("role_count") != 2
        or type(document.get("record_count")) is not int
        or document.get("record_count") != 6
        or type(document.get("records")) is not list
        or len(document["records"]) != 6
    ):
        raise SourceCensusSupplementV1Error("supplement private registry authority differs")
    expected_keys = {(source, role) for source in SUPPLEMENT_SOURCES for role in SUPPLEMENT_ROLES}
    observed_keys: set[tuple[str, str]] = set()
    references: set[str] = set()
    for record in document["records"]:
        if type(record) is not dict or set(record) != PRIVATE_RECORD_KEYS:
            raise SourceCensusSupplementV1Error("supplement private record schema differs")
        record_hash = _sha(record.get("record_hash"), "supplement record hash")
        if stable_hash_v1({key: value for key, value in record.items() if key != "record_hash"}) != record_hash:
            raise SourceCensusSupplementV1Error("supplement record hash differs")
        source = _strict_str(record.get("source_identity"), "record source")
        role = _strict_str(record.get("numeric_role"), "record numeric role")
        key = (source, role)
        if key not in expected_keys or key in observed_keys:
            raise SourceCensusSupplementV1Error("supplement record key is duplicate or foreign")
        observed_keys.add(key)
        reference = _strict_str(record.get("new_reference_identity"), "new reference identity")
        if reference != supplement_reference_identity_v1(source, role) or reference in references:
            raise SourceCensusSupplementV1Error("supplement reference identity differs or duplicates")
        references.add(reference)
        _validate_role_value(role, record.get("numeric_value"))
        if (
            record.get("schema_version") != SCHEMA_VERSION
            or record.get("authority_version") != AUTHORITY_VERSION
            or record.get("purpose") != PURPOSE
            or record.get("normal_train1_identity") != NORMAL_TRAIN1_IDENTITY.sha256
            or record.get("normal_train2_identity") != NORMAL_TRAIN2_IDENTITY.sha256
            or record.get("normal_input_identity_set_hash") != NORMAL_INPUT_IDENTITY_SET_HASH
            or record.get("calibration_policy_hash") != CALIBRATION_POLICY_HASH
            or record.get("provenance_identity") != supplement_provenance_identity_v1(source, role)
        ):
            raise SourceCensusSupplementV1Error("supplement record provenance differs")
    if observed_keys != expected_keys or references != set(SUPPLEMENT_REFERENCE_IDENTITIES):
        raise SourceCensusSupplementV1Error("supplement registry closure differs")
    return observed


@dataclass(frozen=True)
class CombinedSourceCensusNumericContractV1:
    main_descriptor_hash: str
    main_private_registry_hash: str
    main_audit_receipt_hash: str
    supplement_descriptor_hash: str
    supplement_private_registry_hash: str
    supplement_audit_receipt_hash: str
    v3_sources: tuple[str, ...]
    main_sources: tuple[str, ...]
    supplement_sources: tuple[str, ...]
    event_policy_hash: str
    cross_source_isolation_policy_hash: str
    main_source_collapse_policy_hash: str
    total_covered_sources: int

    @property
    def contract_hash(self) -> str:
        return stable_hash_v1(self.to_dict(include_hash=False))

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = {
            "artifact_type": "task039e3_r2r_utility_source_census_combined_numeric_contract_v1",
            "schema_version": SCHEMA_VERSION,
            "main_descriptor_hash": self.main_descriptor_hash,
            "main_private_registry_hash": self.main_private_registry_hash,
            "main_audit_receipt_hash": self.main_audit_receipt_hash,
            "supplement_descriptor_hash": self.supplement_descriptor_hash,
            "supplement_private_registry_hash": self.supplement_private_registry_hash,
            "supplement_audit_receipt_hash": self.supplement_audit_receipt_hash,
            "v3_sources": list(self.v3_sources),
            "main_sources": list(self.main_sources),
            "supplement_sources": list(self.supplement_sources),
            "event_policy_hash": self.event_policy_hash,
            "cross_source_isolation_policy_hash": self.cross_source_isolation_policy_hash,
            "main_source_collapse_policy_hash": self.main_source_collapse_policy_hash,
            "total_covered_sources": self.total_covered_sources,
            "main_source_resolution": "validate_all_applicable_records_then_require_one_unique_value",
            "supplement_purpose": PURPOSE,
        }
        return {**payload, "contract_hash": self.contract_hash} if include_hash else payload


CROSS_SOURCE_ISOLATION_POLICY_HASH = stable_hash_v1(
    {
        "policy_version": "TASK039E3_CROSS_SOURCE_ISOLATION_V1",
        "source_universe": list(UTILITY_SOURCE_UNIVERSE_V3),
        "radius_seconds": 2,
        "all_sources_require_threshold_and_tolerance": True,
        "main_source_representative_relation_caller_selectable": False,
    }
)


def build_combined_source_census_numeric_contract_v1(
    *,
    common_authority: NormalOnlyAuthorityDefinitionV1,
    main_descriptor: NumericAuthorityDescriptorV4,
    materialized_main_audit_receipt: Mapping[str, Any],
    supplement_private_registry_hash: str,
    supplement_audit_receipt_hash: str,
) -> CombinedSourceCensusNumericContractV1:
    validate_canonical_common42_authority_v1(common_authority)
    validate_numeric_authority_descriptor_v4(
        main_descriptor, common_authority, materialized_main_audit_receipt
    )
    main_sources = tuple(sorted({relation.source for relation in common_authority.relations}))
    if main_sources != MAIN_SOURCES:
        raise SourceCensusSupplementV1Error("MAIN source footprint differs")
    contract = CombinedSourceCensusNumericContractV1(
        MAIN_DESCRIPTOR_HASH,
        MAIN_PRIVATE_REGISTRY_HASH,
        MAIN_AUDIT_RECEIPT_HASH,
        SUPPLEMENT_DESCRIPTOR_HASH,
        _sha(supplement_private_registry_hash, "supplement private registry hash"),
        _sha(supplement_audit_receipt_hash, "supplement audit receipt hash"),
        tuple(sorted(UTILITY_SOURCE_UNIVERSE_V3)),
        main_sources,
        SUPPLEMENT_SOURCES,
        SOURCE_CENSUS_EVENT_POLICY_HASH,
        CROSS_SOURCE_ISOLATION_POLICY_HASH,
        MAIN_SOURCE_COLLAPSE_POLICY_HASH,
        COMBINED_SOURCE_COUNT,
    )
    validate_combined_source_census_numeric_contract_v1(contract)
    return contract


def validate_combined_source_census_numeric_contract_v1(
    contract: CombinedSourceCensusNumericContractV1,
) -> str:
    if type(contract) is not CombinedSourceCensusNumericContractV1:
        raise SourceCensusSupplementV1Error("combined contract type differs")
    for name in (
        "main_descriptor_hash", "main_private_registry_hash", "main_audit_receipt_hash",
        "supplement_descriptor_hash", "supplement_private_registry_hash",
        "supplement_audit_receipt_hash", "event_policy_hash",
        "cross_source_isolation_policy_hash", "main_source_collapse_policy_hash",
    ):
        _sha(getattr(contract, name), name)
    if (
        contract.main_descriptor_hash != MAIN_DESCRIPTOR_HASH
        or contract.main_private_registry_hash != MAIN_PRIVATE_REGISTRY_HASH
        or contract.main_audit_receipt_hash != MAIN_AUDIT_RECEIPT_HASH
        or contract.supplement_descriptor_hash != SUPPLEMENT_DESCRIPTOR_HASH
        or type(contract.v3_sources) is not tuple
        or contract.v3_sources != tuple(sorted(UTILITY_SOURCE_UNIVERSE_V3))
        or type(contract.main_sources) is not tuple
        or contract.main_sources != MAIN_SOURCES
        or type(contract.supplement_sources) is not tuple
        or contract.supplement_sources != SUPPLEMENT_SOURCES
        or set(contract.v3_sources) != set(contract.main_sources) | set(contract.supplement_sources)
        or contract.event_policy_hash != SOURCE_CENSUS_EVENT_POLICY_HASH
        or contract.cross_source_isolation_policy_hash != CROSS_SOURCE_ISOLATION_POLICY_HASH
        or contract.main_source_collapse_policy_hash != MAIN_SOURCE_COLLAPSE_POLICY_HASH
        or type(contract.total_covered_sources) is not int
        or contract.total_covered_sources != COMBINED_SOURCE_COUNT
    ):
        raise SourceCensusSupplementV1Error("combined source-census contract differs")
    return contract.contract_hash


def collapse_main_source_role_v1(
    *,
    main_registry: Mapping[str, Any],
    common_authority: NormalOnlyAuthorityDefinitionV1,
    source: str,
    numeric_role: str,
) -> float:
    """Collapse all MAIN relation records for one source; caller selects no relation."""

    if source not in {relation.source for relation in common_authority.relations}:
        raise SourceCensusSupplementV1Error("source is not in the MAIN source footprint")
    if numeric_role not in SUPPLEMENT_ROLES:
        raise SourceCensusSupplementV1Error("MAIN source-census role differs")
    observed_registry_hash = validate_main_private_registry_document_v1(
        main_registry, common_authority
    )
    if observed_registry_hash != MAIN_PRIVATE_REGISTRY_HASH:
        raise SourceCensusSupplementV1Error("MAIN private registry authority differs")
    relation_hashes = {
        relation.relation_binding_hash
        for relation in common_authority.relations
        if relation.source == source
    }
    values = [
        record["numeric_value"]
        for record in main_registry["records"]
        if record["relation_binding_hash"] in relation_hashes
        and record["numeric_role"] == numeric_role
    ]
    if (
        not values
        or any(type(value) is not float for value in values)
        or len({value.hex() for value in values}) != 1
    ):
        raise SourceCensusSupplementV1Error("MAIN within-source calibration values differ")
    return _validate_role_value(numeric_role, values[0])


AUTHORIZATION_KEYS = frozenset(
    {
        "artifact_type", "schema_version", "task_id", "authority_version", "purpose",
        "scope", "coverage_decision_hash", "supplement_descriptor_hash",
        "reference_set_hash", "normal_input_identity_set_hash", "calibration_policy_hash",
        "event_policy_hash", "v4_r1_authority_hash", "v4_r1_focused_receipt_hash",
        "implementation_commit", "implementation_source_git_blob",
        "implementation_source_raw_sha256", "independent_audit_commit",
        "independent_test_git_blob", "independent_test_raw_sha256",
        "normal_only_source_git_blob", "normal_only_source_raw_sha256",
        "calibration_dependency_git_blob", "calibration_dependency_raw_sha256",
        "authorized_sources", "train1_access", "train2_access", "train3_access",
        "train4_access", "test1_access", "test2_access", "label_access",
        "attack_interval_access", "provider_access", "llm_access", "utility_execution",
        "detector_execution", "materialization_authorized", "artifact_hash",
    }
)


def validate_materialization_authorization_document_v1(document: Mapping[str, Any]) -> str:
    observed = _validate_self_hashed_dict(
        document, allowed_keys=AUTHORIZATION_KEYS, name="supplement materialization authorization"
    )
    if (
        document.get("artifact_type")
        != "task039e3_r2r_utility_source_census_supplement_v1_materialization_authorization"
        or document.get("schema_version") != SCHEMA_VERSION
        or document.get("task_id") != TASK_ID
        or document.get("authority_version") != AUTHORITY_VERSION
        or document.get("purpose") != PURPOSE
        or document.get("scope") != MATERIALIZATION_SCOPE
        or document.get("supplement_descriptor_hash") != SUPPLEMENT_DESCRIPTOR_HASH
        or document.get("reference_set_hash") != SUPPLEMENT_REFERENCE_SET_HASH
        or document.get("normal_input_identity_set_hash") != NORMAL_INPUT_IDENTITY_SET_HASH
        or document.get("calibration_policy_hash") != CALIBRATION_POLICY_HASH
        or document.get("event_policy_hash") != SOURCE_CENSUS_EVENT_POLICY_HASH
        or document.get("v4_r1_authority_hash") != V4_R1_AUTHORITY_HASH
        or document.get("v4_r1_focused_receipt_hash") != V4_R1_FOCUSED_RECEIPT_HASH
        or type(document.get("authorized_sources")) is not list
        or document.get("authorized_sources") != list(SUPPLEMENT_SOURCES)
    ):
        raise SourceCensusSupplementV1Error("supplement authorization authority differs")
    if document.get("coverage_decision_hash") != COVERAGE_DECISION_HASH:
        raise SourceCensusSupplementV1Error("coverage decision authorization differs")
    _git_oid(document.get("implementation_commit"), "implementation commit")
    _git_oid(document.get("implementation_source_git_blob"), "implementation source blob")
    _sha(document.get("implementation_source_raw_sha256"), "implementation source SHA-256")
    _git_oid(document.get("independent_audit_commit"), "independent audit commit")
    _git_oid(document.get("independent_test_git_blob"), "independent test blob")
    _sha(document.get("independent_test_raw_sha256"), "independent test SHA-256")
    if (
        document.get("normal_only_source_git_blob") != NORMAL_ONLY_SOURCE_BLOB
        or document.get("normal_only_source_raw_sha256") != NORMAL_ONLY_SOURCE_RAW_SHA256
        or document.get("calibration_dependency_git_blob") != CALIBRATION_DEPENDENCY_BLOB
        or document.get("calibration_dependency_raw_sha256") != CALIBRATION_DEPENDENCY_RAW_SHA256
    ):
        raise SourceCensusSupplementV1Error("supplement authorization dependency differs")
    for name in ("train1_access", "train2_access", "materialization_authorized"):
        if _strict_bool(document.get(name), name) is not True:
            raise SourceCensusSupplementV1Error("required supplement authorization is false")
    for name in (
        "train3_access", "train4_access", "test1_access", "test2_access", "label_access",
        "attack_interval_access", "provider_access", "llm_access", "utility_execution",
        "detector_execution",
    ):
        if _strict_bool(document.get(name), name) is not False:
            raise SourceCensusSupplementV1Error("supplement authorization scope broadened")
    return observed


def _git_output(root: Path, *args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=not binary
    )
    return result.stdout if binary else result.stdout.strip()


def _verify_tracked_file(root: Path, relative: str, *, expected_blob: str, expected_raw: str) -> None:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise SourceCensusSupplementV1Error("authorized source dependency is not a regular file")
    blob = str(_git_output(root, "rev-parse", f"HEAD:{relative}"))
    dirty = str(_git_output(root, "status", "--porcelain", "--", relative))
    if blob != expected_blob or _file_sha256(path) != expected_raw or dirty:
        raise SourceCensusSupplementV1Error("authorized source dependency checkout differs")


def load_committed_materialization_authorization_v1(repository_root: Path) -> dict[str, Any]:
    """Load only the fixed clean Commit-C authorization; callers choose no authority."""

    root = repository_root.resolve(strict=True)
    module_root = Path(__file__).resolve(strict=True).parents[3]
    if repository_root.is_symlink() or root != module_root:
        raise SourceCensusSupplementV1Error("repository root does not own supplement implementation")
    path = root / AUTHORIZATION_RELATIVE_PATH
    if path.is_symlink() or not path.is_file() or root not in path.resolve(strict=True).parents:
        raise SourceCensusSupplementV1Error("committed supplement authorization is unavailable")
    if _git_output(root, "status", "--porcelain", "--", AUTHORIZATION_RELATIVE_PATH):
        raise SourceCensusSupplementV1Error("supplement authorization working bytes are dirty")
    committed = _git_output(root, "show", f"HEAD:{AUTHORIZATION_RELATIVE_PATH}", binary=True)
    working = path.read_bytes()
    if committed != working:
        raise SourceCensusSupplementV1Error("supplement authorization differs from HEAD")
    document = json.loads(working.decode("utf-8"))
    validate_materialization_authorization_document_v1(document)
    coverage_path = root / COVERAGE_DECISION_RELATIVE_PATH
    if (
        coverage_path.is_symlink()
        or not coverage_path.is_file()
        or _git_output(root, "status", "--porcelain", "--", COVERAGE_DECISION_RELATIVE_PATH)
    ):
        raise SourceCensusSupplementV1Error("coverage decision custody is unavailable")
    coverage_committed = _git_output(
        root, "show", f"HEAD:{COVERAGE_DECISION_RELATIVE_PATH}", binary=True
    )
    if coverage_committed != coverage_path.read_bytes():
        raise SourceCensusSupplementV1Error("coverage decision differs from HEAD")
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    if (
        type(coverage) is not dict
        or coverage.get("artifact_hash") != COVERAGE_DECISION_HASH
        or _self_hash(coverage) != COVERAGE_DECISION_HASH
    ):
        raise SourceCensusSupplementV1Error("coverage decision self-hash differs")
    head = str(_git_output(root, "rev-parse", "HEAD"))
    parent = str(_git_output(root, "rev-parse", "HEAD^"))
    if parent != document["independent_audit_commit"]:
        raise SourceCensusSupplementV1Error("execution HEAD is not the separate authorization commit")
    if subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", document["implementation_commit"], head],
        check=False, capture_output=True,
    ).returncode != 0:
        raise SourceCensusSupplementV1Error("implementation commit is outside execution lineage")
    implementation_blob = str(
        _git_output(root, "rev-parse", f"{document['implementation_commit']}:{SUPPLEMENT_SOURCE_PATH}")
    )
    head_blob = str(_git_output(root, "rev-parse", f"HEAD:{SUPPLEMENT_SOURCE_PATH}"))
    implementation_bytes = _git_output(
        root, "show", f"{document['implementation_commit']}:{SUPPLEMENT_SOURCE_PATH}", binary=True
    )
    if (
        implementation_blob != document["implementation_source_git_blob"]
        or head_blob != implementation_blob
        or sha256(implementation_bytes).hexdigest() != document["implementation_source_raw_sha256"]
        or _file_sha256(root / SUPPLEMENT_SOURCE_PATH) != document["implementation_source_raw_sha256"]
        or _git_output(root, "status", "--porcelain", "--", SUPPLEMENT_SOURCE_PATH)
    ):
        raise SourceCensusSupplementV1Error("supplement implementation checkout differs")
    independent_blob = str(_git_output(root, "rev-parse", f"HEAD:{INDEPENDENT_TEST_PATH}"))
    if (
        independent_blob != document["independent_test_git_blob"]
        or _file_sha256(root / INDEPENDENT_TEST_PATH) != document["independent_test_raw_sha256"]
        or _git_output(root, "status", "--porcelain", "--", INDEPENDENT_TEST_PATH)
    ):
        raise SourceCensusSupplementV1Error("independent audit test checkout differs")
    _verify_tracked_file(
        root, NORMAL_ONLY_SOURCE_PATH,
        expected_blob=NORMAL_ONLY_SOURCE_BLOB, expected_raw=NORMAL_ONLY_SOURCE_RAW_SHA256,
    )
    _verify_tracked_file(
        root, CALIBRATION_DEPENDENCY_PATH,
        expected_blob=CALIBRATION_DEPENDENCY_BLOB, expected_raw=CALIBRATION_DEPENDENCY_RAW_SHA256,
    )
    _verify_tracked_file(root, V3_SOURCE_PATH, expected_blob=V3_SOURCE_BLOB, expected_raw=V3_SOURCE_RAW_SHA256)
    _verify_tracked_file(root, V4_R1_SOURCE_PATH, expected_blob=V4_R1_SOURCE_BLOB, expected_raw=V4_R1_SOURCE_RAW_SHA256)
    return document


def _load_committed_authorization_for_final_custody_v1(
    repository_root: Path,
) -> dict[str, Any]:
    """Replay the fixed authorization at its commit and any unchanged descendant."""

    root = repository_root.resolve(strict=True)
    module_root = Path(__file__).resolve(strict=True).parents[3]
    if repository_root.is_symlink() or root != module_root:
        raise SourceCensusSupplementV1Error("repository root does not own supplement implementation")
    path = root / AUTHORIZATION_RELATIVE_PATH
    if path.is_symlink() or not path.is_file() or root not in path.resolve(strict=True).parents:
        raise SourceCensusSupplementV1Error("committed supplement authorization is unavailable")
    if _git_output(root, "status", "--porcelain", "--", AUTHORIZATION_RELATIVE_PATH):
        raise SourceCensusSupplementV1Error("supplement authorization working bytes are dirty")
    working = path.read_bytes()
    if _git_output(root, "show", f"HEAD:{AUTHORIZATION_RELATIVE_PATH}", binary=True) != working:
        raise SourceCensusSupplementV1Error("supplement authorization differs from HEAD")
    document = json.loads(working.decode("utf-8"))
    validate_materialization_authorization_document_v1(document)
    authorization_commit = str(
        _git_output(root, "log", "-1", "--format=%H", "--", AUTHORIZATION_RELATIVE_PATH)
    )
    if not authorization_commit:
        raise SourceCensusSupplementV1Error("supplement authorization commit is unavailable")
    if str(_git_output(root, "rev-parse", f"{authorization_commit}^")) != document["independent_audit_commit"]:
        raise SourceCensusSupplementV1Error("supplement authorization lineage differs")
    head = str(_git_output(root, "rev-parse", "HEAD"))
    for ancestor, descendant in (
        (document["implementation_commit"], authorization_commit),
        (authorization_commit, head),
    ):
        if subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
            check=False, capture_output=True,
        ).returncode != 0:
            raise SourceCensusSupplementV1Error("supplement authorization lineage differs")
    implementation_blob = str(
        _git_output(root, "rev-parse", f"{document['implementation_commit']}:{SUPPLEMENT_SOURCE_PATH}")
    )
    if (
        implementation_blob != document["implementation_source_git_blob"]
        or str(_git_output(root, "rev-parse", f"HEAD:{SUPPLEMENT_SOURCE_PATH}")) != implementation_blob
        or _file_sha256(root / SUPPLEMENT_SOURCE_PATH) != document["implementation_source_raw_sha256"]
        or _git_output(root, "status", "--porcelain", "--", SUPPLEMENT_SOURCE_PATH)
        or str(_git_output(root, "rev-parse", f"HEAD:{INDEPENDENT_TEST_PATH}"))
        != document["independent_test_git_blob"]
        or _file_sha256(root / INDEPENDENT_TEST_PATH) != document["independent_test_raw_sha256"]
        or _git_output(root, "status", "--porcelain", "--", INDEPENDENT_TEST_PATH)
    ):
        raise SourceCensusSupplementV1Error("supplement final custody implementation differs")
    return document


def _validate_authorization_cross_custody_v1(
    locator: Mapping[str, Any], public: Mapping[str, Any], authorization: Mapping[str, Any]
) -> str:
    authorization_hash = validate_materialization_authorization_document_v1(authorization)
    if (
        locator.get("authorization_hash") != authorization_hash
        or public.get("authorization_hash") != authorization_hash
    ):
        raise SourceCensusSupplementV1Error("supplement authorization custody differs")
    return authorization_hash


def _require_outside_repository(path: Path, root: Path, name: str) -> Path:
    resolved = path.resolve(strict=False)
    if not resolved.is_absolute() or resolved == root or root in resolved.parents:
        raise SourceCensusSupplementV1Error(f"{name} must remain outside Git")
    cursor = resolved if resolved.is_dir() else resolved.parent
    while True:
        git_marker = cursor / ".git"
        if git_marker.exists() or git_marker.is_symlink():
            raise SourceCensusSupplementV1Error(f"{name} must remain outside Git")
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    return resolved


def validate_materialization_output_preflight_v1(
    *, private_destination: Path, local_locator_path: Path,
    public_receipt_path: Path, repository_root: Path,
) -> tuple[Path, Path, Path]:
    root = repository_root.resolve(strict=True)
    configured = os.environ.get(PRIVATE_AUTHORITY_ENV)
    if not configured or not Path(configured).is_absolute():
        raise SourceCensusSupplementV1Error("explicit supplement private destination is absent")
    private = _require_outside_repository(private_destination, root, "supplement private authority")
    locator = _require_outside_repository(local_locator_path, root, "supplement local locator")
    receipt = public_receipt_path.resolve(strict=False)
    if Path(configured).resolve(strict=False) != private:
        raise SourceCensusSupplementV1Error("supplement private environment destination differs")
    expected_receipt = (root / PUBLIC_RECEIPT_RELATIVE_PATH).resolve(strict=False)
    if receipt != expected_receipt or len({private, locator, receipt}) != 3:
        raise SourceCensusSupplementV1Error("supplement output paths differ")
    for original, resolved, name in (
        (private_destination, private, "private authority"),
        (local_locator_path, locator, "local locator"),
        (public_receipt_path, receipt, "public receipt"),
    ):
        if original.is_symlink() or resolved.exists() or original.parent.is_symlink():
            raise SourceCensusSupplementV1Error(f"supplement {name} exists or is unsafe")
        if not resolved.parent.is_dir() or resolved.parent.is_symlink():
            raise SourceCensusSupplementV1Error(f"supplement {name} parent is unsafe")
    return private, locator, receipt


def _atomic_write_new_json(path: Path, document: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise SourceCensusSupplementV1Error("authoritative output already exists")
    partial = path.with_name(f".{path.name}.partial-{uuid4().hex}")
    try:
        with partial.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json_v1(document))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(partial, path)
    finally:
        if partial.exists():
            partial.unlink()


LOCATOR_KEYS = frozenset(
    {
        "artifact_type", "schema_version", "authority_version", "purpose",
        "absolute_private_authority_path", "private_registry_hash",
        "supplement_descriptor_hash", "authorization_hash", "created_at",
        "local_only", "must_not_be_committed", "artifact_hash",
    }
)
PUBLIC_RECEIPT_KEYS = frozenset(
    {
        "artifact_type", "schema_version", "task_id", "authority_version", "purpose",
        "supplement_descriptor_hash", "private_registry_hash", "local_locator_hash",
        "authorization_hash", "normal_train1_identity", "normal_train2_identity",
        "normal_input_identity_set_hash", "calibration_policy_hash", "event_policy_hash",
        "source_count", "role_count", "record_count", "reference_count",
        "record_hash_matches", "provenance_matches", "numeric_domain_failures",
        "train1_scientific_parse_count", "train2_scientific_parse_count",
        "scientific_retries", "public_receipt_written_last", "numeric_values_exposed",
        "absolute_private_paths_exposed", "created_at", "artifact_hash",
    }
)


def _build_locator(
    *, private_path: Path, registry_hash: str, authorization_hash: str, created_at: str
) -> dict[str, Any]:
    document: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_utility_source_census_supplement_local_locator_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "purpose": PURPOSE,
        "absolute_private_authority_path": str(private_path),
        "private_registry_hash": registry_hash,
        "supplement_descriptor_hash": SUPPLEMENT_DESCRIPTOR_HASH,
        "authorization_hash": authorization_hash,
        "created_at": created_at,
        "local_only": True,
        "must_not_be_committed": True,
    }
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def validate_local_locator_document_v1(
    document: Mapping[str, Any], *, repository_root: Path,
) -> str:
    observed = _validate_self_hashed_dict(document, allowed_keys=LOCATOR_KEYS, name="supplement locator")
    if (
        document.get("artifact_type") != "task039e3_r2r_utility_source_census_supplement_local_locator_v1"
        or document.get("schema_version") != SCHEMA_VERSION
        or document.get("authority_version") != AUTHORITY_VERSION
        or document.get("purpose") != PURPOSE
        or document.get("supplement_descriptor_hash") != SUPPLEMENT_DESCRIPTOR_HASH
        or document.get("local_only") is not True
        or document.get("must_not_be_committed") is not True
    ):
        raise SourceCensusSupplementV1Error("supplement locator authority differs")
    path = Path(_strict_str(document.get("absolute_private_authority_path"), "private path"))
    _require_outside_repository(path, repository_root.resolve(strict=True), "supplement private authority")
    _sha(document.get("private_registry_hash"), "private registry hash")
    _sha(document.get("authorization_hash"), "authorization hash")
    _timezone_aware(document.get("created_at"), "locator creation time")
    return observed


def _build_public_receipt(
    *, registry_hash: str, locator_hash: str, authorization_hash: str, created_at: str
) -> dict[str, Any]:
    document: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_utility_source_census_supplement_public_receipt_v1",
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "authority_version": AUTHORITY_VERSION,
        "purpose": PURPOSE,
        "supplement_descriptor_hash": SUPPLEMENT_DESCRIPTOR_HASH,
        "private_registry_hash": registry_hash,
        "local_locator_hash": locator_hash,
        "authorization_hash": authorization_hash,
        "normal_train1_identity": NORMAL_TRAIN1_IDENTITY.sha256,
        "normal_train2_identity": NORMAL_TRAIN2_IDENTITY.sha256,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "event_policy_hash": SOURCE_CENSUS_EVENT_POLICY_HASH,
        "source_count": 3,
        "role_count": 2,
        "record_count": 6,
        "reference_count": 6,
        "record_hash_matches": 6,
        "provenance_matches": 6,
        "numeric_domain_failures": 0,
        "train1_scientific_parse_count": 1,
        "train2_scientific_parse_count": 1,
        "scientific_retries": 0,
        "public_receipt_written_last": True,
        "numeric_values_exposed": 0,
        "absolute_private_paths_exposed": 0,
        "created_at": created_at,
    }
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def validate_public_receipt_document_v1(document: Mapping[str, Any]) -> str:
    observed = _validate_self_hashed_dict(
        document, allowed_keys=PUBLIC_RECEIPT_KEYS, name="supplement public receipt"
    )
    expected_scalars = {
        "artifact_type": "task039e3_r2r_utility_source_census_supplement_public_receipt_v1",
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "authority_version": AUTHORITY_VERSION,
        "purpose": PURPOSE,
        "supplement_descriptor_hash": SUPPLEMENT_DESCRIPTOR_HASH,
        "normal_train1_identity": NORMAL_TRAIN1_IDENTITY.sha256,
        "normal_train2_identity": NORMAL_TRAIN2_IDENTITY.sha256,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "event_policy_hash": SOURCE_CENSUS_EVENT_POLICY_HASH,
    }
    if any(document.get(key) != value for key, value in expected_scalars.items()):
        raise SourceCensusSupplementV1Error("supplement public receipt authority differs")
    for name in ("private_registry_hash", "local_locator_hash", "authorization_hash"):
        _sha(document.get(name), name)
    for name, expected in {
        "source_count": 3, "role_count": 2, "record_count": 6, "reference_count": 6,
        "record_hash_matches": 6, "provenance_matches": 6, "numeric_domain_failures": 0,
        "train1_scientific_parse_count": 1, "train2_scientific_parse_count": 1,
        "scientific_retries": 0, "numeric_values_exposed": 0,
        "absolute_private_paths_exposed": 0,
    }.items():
        if type(document.get(name)) is not int or document.get(name) != expected:
            raise SourceCensusSupplementV1Error("supplement public receipt count differs")
    if document.get("public_receipt_written_last") is not True:
        raise SourceCensusSupplementV1Error("supplement public receipt order differs")
    _timezone_aware(document.get("created_at"), "public receipt creation time")
    return observed


@dataclass(frozen=True)
class SupplementMaterializationResultV1:
    private_registry_hash: str
    local_locator_hash: str
    public_receipt_hash: str
    authorization_hash: str
    record_count: int


def materialize_source_census_supplement_v1(
    *, train1_path: Path, train2_path: Path, private_destination: Path,
    local_locator_path: Path, public_receipt_path: Path,
    repository_root: Path, execution_timestamp: str,
) -> SupplementMaterializationResultV1:
    """Perform the one authorized three-source normal-only materialization."""

    authorization = load_committed_materialization_authorization_v1(repository_root)
    authorization_hash = validate_materialization_authorization_document_v1(authorization)
    private, locator, receipt = validate_materialization_output_preflight_v1(
        private_destination=private_destination,
        local_locator_path=local_locator_path,
        public_receipt_path=public_receipt_path,
        repository_root=repository_root,
    )
    timestamp = _timezone_aware(execution_timestamp, "execution timestamp")
    train1, train2 = load_verified_normal_features_v1(
        train1_path=train1_path,
        train2_path=train2_path,
        required_features=frozenset(SUPPLEMENT_SOURCES),
    )
    role_values = derive_supplement_role_values_v1(train1, train2)
    definition = build_supplement_authority_definition_v1()
    registry = build_supplement_private_registry_document_v1(definition, role_values)
    registry_hash = validate_supplement_private_registry_document_v1(registry, definition)
    _atomic_write_new_json(private, registry)
    reopened = json.loads(private.read_text(encoding="utf-8"))
    if validate_supplement_private_registry_document_v1(reopened, definition) != registry_hash:
        raise SourceCensusSupplementV1Error("authoritative supplement private reopen differs")
    locator_document = _build_locator(
        private_path=private, registry_hash=registry_hash,
        authorization_hash=authorization_hash, created_at=timestamp,
    )
    locator_hash = validate_local_locator_document_v1(
        locator_document, repository_root=repository_root
    )
    _atomic_write_new_json(locator, locator_document)
    reopened_locator = json.loads(locator.read_text(encoding="utf-8"))
    if validate_local_locator_document_v1(reopened_locator, repository_root=repository_root) != locator_hash:
        raise SourceCensusSupplementV1Error("authoritative supplement locator reopen differs")
    reopened_again = json.loads(private.read_text(encoding="utf-8"))
    if validate_supplement_private_registry_document_v1(reopened_again, definition) != registry_hash:
        raise SourceCensusSupplementV1Error("supplement private custody changed before receipt")
    public_document = _build_public_receipt(
        registry_hash=registry_hash, locator_hash=locator_hash,
        authorization_hash=authorization_hash, created_at=timestamp,
    )
    public_hash = validate_public_receipt_document_v1(public_document)
    _atomic_write_new_json(receipt, public_document)
    return SupplementMaterializationResultV1(
        registry_hash, locator_hash, public_hash, authorization_hash, 6
    )


def validate_finalized_supplement_authority_v1(
    *, local_locator_path: Path, public_receipt_path: Path, repository_root: Path,
) -> SupplementMaterializationResultV1:
    """Validate finalized custody without reading any HAI file."""

    root = repository_root.resolve(strict=True)
    if local_locator_path.is_symlink() or not local_locator_path.is_file():
        raise SourceCensusSupplementV1Error("supplement locator file is unavailable")
    _require_outside_repository(local_locator_path, root, "supplement local locator")
    locator = json.loads(local_locator_path.read_text(encoding="utf-8"))
    locator_hash = validate_local_locator_document_v1(locator, repository_root=root)
    private_path = Path(locator["absolute_private_authority_path"])
    if private_path.is_symlink() or not private_path.is_file():
        raise SourceCensusSupplementV1Error("supplement private authority is unavailable")
    _require_outside_repository(private_path, root, "supplement private authority")
    registry = json.loads(private_path.read_text(encoding="utf-8"))
    registry_hash = validate_supplement_private_registry_document_v1(registry)
    if registry_hash != locator["private_registry_hash"]:
        raise SourceCensusSupplementV1Error("supplement locator/private hash differs")
    if public_receipt_path.is_symlink() or not public_receipt_path.is_file():
        raise SourceCensusSupplementV1Error("supplement public receipt is unavailable")
    if public_receipt_path.resolve(strict=True) != (root / PUBLIC_RECEIPT_RELATIVE_PATH).resolve(strict=True):
        raise SourceCensusSupplementV1Error("supplement public receipt path differs")
    public = json.loads(public_receipt_path.read_text(encoding="utf-8"))
    public_hash = validate_public_receipt_document_v1(public)
    authorization = _load_committed_authorization_for_final_custody_v1(root)
    authorization_hash = _validate_authorization_cross_custody_v1(
        locator, public, authorization
    )
    if (
        public["private_registry_hash"] != registry_hash
        or public["local_locator_hash"] != locator_hash
        or public["authorization_hash"] != locator["authorization_hash"]
    ):
        raise SourceCensusSupplementV1Error("supplement public/private/locator custody differs")
    return SupplementMaterializationResultV1(
        registry_hash, locator_hash, public_hash, authorization_hash, 6
    )


__all__ = [
    "AUTHORITY_VERSION", "PURPOSE", "SUPPLEMENT_SOURCES", "SUPPLEMENT_ROLES",
    "SUPPLEMENT_RECORD_COUNT", "SUPPLEMENT_DESCRIPTOR_HASH",
    "SUPPLEMENT_REFERENCE_SET_HASH", "SOURCE_CENSUS_EVENT_POLICY_HASH",
    "CROSS_SOURCE_ISOLATION_POLICY_HASH", "SourceCensusSupplementV1Error",
    "SourceCensusCoverageDecisionV1", "SupplementAuthorityDefinitionV1",
    "CombinedSourceCensusNumericContractV1", "SupplementMaterializationResultV1",
    "build_source_census_coverage_decision_v1", "validate_source_census_coverage_decision_v1",
    "build_supplement_authority_definition_v1", "validate_supplement_authority_definition_v1",
    "supplement_reference_identity_v1", "supplement_provenance_identity_v1",
    "derive_supplement_role_values_v1", "build_supplement_private_registry_document_v1",
    "validate_supplement_private_registry_document_v1",
    "build_combined_source_census_numeric_contract_v1",
    "validate_combined_source_census_numeric_contract_v1", "collapse_main_source_role_v1",
    "validate_materialization_authorization_document_v1",
    "load_committed_materialization_authorization_v1",
    "validate_materialization_output_preflight_v1",
    "materialize_source_census_supplement_v1",
    "validate_finalized_supplement_authority_v1",
]
