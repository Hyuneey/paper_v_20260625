"""Canonical Utility Protocol V4 authority closure for TASK-039E3 R2R.

This module is deliberately metadata-only.  It binds the frozen COMMON-42
portfolio to the independently audited normal-only numeric authority without
opening the private registry, HAI data, labels, or attack intervals.  It also
defines fail-closed planning and provenance contracts for a later evaluator;
it does not implement or authorize utility execution.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timedelta
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
    FILE_COORDINATES,
    INNER_SPLIT_ID,
    OUTER_SPLIT_ID,
    SOURCE_POST_WINDOW,
    SOURCE_PRE_WINDOW,
    TARGET_BASELINE_WINDOW,
    TARGET_RESPONSE_WINDOW,
    VIRTUAL_PURGE_RANGE,
    physical_to_logical_v2,
)
from paperworks.v6.task039e3_r2r_utility_protocol_v3 import (
    FILE_ROW_COUNTS,
    FILE_SPLITS,
    UTILITY_SOURCE_UNIVERSE_V3,
    build_p1_utility_feature_schema_v3,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-PROTOCOL-V4-NORMAL-ONLY-AUTHORITY-REBIND-AND-CANONICAL-CLOSURE"
R1_TASK_ID = "TASK-039E3-R2R-UTILITY-PROTOCOL-V4-BOUNDED-REMEDIATION-R1"
PROTOCOL_VERSION = "TASK039E3_R2R_UTILITY_PROTOCOL_V4"
SCHEMA_VERSION = "4.0.0"
BASE_COMMIT = "e971c8c8543f49b31aba2a57cf60257d190b76d5"
R1_BASE_COMMIT = "11a0392246ec34ea6158a08b0790c7bb32092d81"
V3_LINEAGE = "BASE_V1_PLUS_REMEDIATION_V2_PLUS_FINAL_CLOSURE_V3"
UTILITY_PROTOCOL_V4_CONTROL_REVISION = "R1"

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
CSV_STRUCTURE_REPORT_HASH = "d4f43034e9402806a4f34da943a1e39191503f8f54465d6d1f98b9cdc31bb7c9"

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
    ("BLOCKER_V3_OPPORTUNITY_RECORD_SEMANTIC_IDENTITY_UNCHECKED", "CLOSED_BY_PUBLIC_COORDINATE_REPLAY_R1"),
    ("BLOCKER_V3_FULL_CENSUS_NUMERIC_REFERENCE_AUTHORITY_UNBOUND", "CLOSED_BY_AUDITED_V1_420_REFERENCE_AUTHORITY"),
    ("BLOCKER_V3_CANONICAL_FULL_CENSUS_PROVENANCE_BYPASS", "CLOSED_BY_CALLER_CENSUS_AUTHORITY_REMOVAL_R1"),
    ("BLOCKER_V3_SERIALIZED_FEATURE_SCHEMA_AUTHORITY_SUBSTITUTION", "CLOSED_BY_V4_COMMITTED_METADATA_REPLAY"),
    ("BLOCKER_V3_CANONICAL_SCALAR_TYPE_POLICY_NOT_ENFORCED", "CLOSED_BY_RECURSIVE_CANONICAL_TYPE_REPLAY_R1"),
    ("BLOCKER_V3_TARGET_TERMINAL_STATE_PROVENANCE_UNBOUND", "CLOSED_BY_EVALUATOR_EVIDENCE_AUTHORITY_BOUNDARY_R1"),
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
DENOMINATOR_POLICY_V4_R1 = "ALL_AUTOMATICALLY_ENUMERATED_APPLICABLE_CANONICAL_OPPORTUNITIES"
REAL_ENUMERATION_AUTHORITY_AVAILABLE = False
REAL_SOURCE_EVIDENCE_AUTHORITY_AVAILABLE = False
REAL_RESPONSE_EVIDENCE_AUTHORITY_AVAILABLE = False
CALLER_RESPONSE_MATCHED_AUTHORIZED = False
SYNTHETIC_TRANSITION_AUTHORITY_SCOPE = "SYNTHETIC_CONTRACT_ONLY"
FROZEN_SOURCE_TRIGGER_POLICY_HASH = "6049632b103559e1fc7fe8de4d0824581f7204f8fdf5142a9944f29debc83acc"
FROZEN_RESPONSE_POLICY_HASH = "92674c55757cc7d49700ce081972640b597b2ab5ad1f616f0a04315a012a1cf1"
SOURCE_EVIDENCE_REQUIRED_BINDINGS_V4_R1 = (
    "opportunity_id",
    "rule_descriptor_hash",
    "source_window_coordinate_identity",
    "source_step_reference_identity",
    "source_stability_reference_identity",
    "numeric_authority_descriptor_hash",
    "retained_source_event_identity",
    "canonical_source_event_enumeration_receipt_hash",
    "event_policy_hash",
    "frozen_trigger_policy_hash",
    "evaluator_implementation_authority_hash",
    "evaluator_computation_identity",
)
RESPONSE_EVIDENCE_REQUIRED_BINDINGS_V4_R1 = (
    "opportunity_id",
    "rule_descriptor_hash",
    "source_evidence_identity",
    "target_window_coordinate_identity",
    "target_noise_reference_identity",
    "numeric_authority_descriptor_hash",
    "expected_target_direction",
    "frozen_response_policy_hash",
    "evaluator_implementation_authority_hash",
    "evaluator_computation_identity",
    "response_evidence_identity",
)
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
RECURSIVE_CANONICAL_TYPE_POLICY_HASH_R1 = stable_hash_v1(
    {
        "policy_version": "TASK039E3_V4_R1_RECURSIVE_CANONICAL_TYPE_POLICY",
        "authority_dataclasses": "exact concrete class",
        "canonical_containers": "type(value) is tuple",
        "inner_pairs": "exact 2-tuple[str, str]",
        "integer": "type(value) is int",
        "boolean": "type(value) is bool",
        "float": "type(value) is float and finite",
        "string": "type(value) is str",
        "list_widening": False,
        "generator_widening": False,
        "set_widening": False,
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

HISTORICAL_CANONICAL_V4_AUTHORITY_HASH = "2864c99017dcea576437efe9f9c5d531cc0d7810504cb2bd8e8585643d2fa0a1"
CANONICAL_V4_AUTHORITY_HASH = "1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343"


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


@dataclass(frozen=True)
class CanonicalFileCoordinateSpecV4R1:
    source_file_identity: str
    relative_path: str
    file_sha256: str
    split_identity: str
    row_count: int
    first_timestamp: str
    last_timestamp: str
    nominal_delta_seconds: int
    timestamps_strictly_increasing: bool
    duplicate_timestamp_count: int

    def __post_init__(self) -> None:
        file_identity = _strict_str(self.source_file_identity, "source_file_identity")
        if file_identity not in FILE_ROW_COUNTS:
            raise UtilityProtocolV4Error("coordinate file is outside INNER/OUTER authority")
        if self.relative_path != f"hai-23.05/{file_identity}":
            raise UtilityProtocolV4Error("coordinate relative path differs")
        _sha(self.file_sha256, "file_sha256")
        if self.split_identity != FILE_SPLITS[file_identity]:
            raise UtilityProtocolV4Error("coordinate split identity differs")
        if _strict_int(self.row_count, "row_count", minimum=1) != FILE_ROW_COUNTS[file_identity]:
            raise UtilityProtocolV4Error("coordinate row count differs")
        first = datetime.strptime(_strict_str(self.first_timestamp, "first_timestamp"), "%Y-%m-%d %H:%M:%S")
        last = datetime.strptime(_strict_str(self.last_timestamp, "last_timestamp"), "%Y-%m-%d %H:%M:%S")
        if _strict_int(self.nominal_delta_seconds, "nominal_delta_seconds", minimum=1) != 1:
            raise UtilityProtocolV4Error("coordinate sampling interval differs")
        if _strict_bool(self.timestamps_strictly_increasing, "timestamps_strictly_increasing") is not True:
            raise UtilityProtocolV4Error("coordinate timestamps are not strictly increasing")
        if _strict_int(self.duplicate_timestamp_count, "duplicate_timestamp_count") != 0:
            raise UtilityProtocolV4Error("coordinate timestamps contain duplicates")
        expected_last = first + timedelta(seconds=(self.row_count - 1) * self.nominal_delta_seconds)
        if expected_last != last:
            raise UtilityProtocolV4Error("coordinate first/last timestamp replay differs")

    def _payload(self) -> dict[str, Any]:
        return {
            "duplicate_timestamp_count": self.duplicate_timestamp_count,
            "file_sha256": self.file_sha256,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "nominal_delta_seconds": self.nominal_delta_seconds,
            "relative_path": self.relative_path,
            "row_count": self.row_count,
            "source_file_identity": self.source_file_identity,
            "split_identity": self.split_identity,
            "timestamps_strictly_increasing": self.timestamps_strictly_increasing,
        }

    @property
    def spec_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "spec_hash": self.spec_hash}


@dataclass(frozen=True)
class CanonicalFileCoordinateAuthorityV4R1:
    csv_structure_report_hash: str
    file_specs: tuple[CanonicalFileCoordinateSpecV4R1, ...]

    def __post_init__(self) -> None:
        if _sha(self.csv_structure_report_hash, "csv_structure_report_hash") != CSV_STRUCTURE_REPORT_HASH:
            raise UtilityProtocolV4Error("CSV structure authority differs")
        specs = _strict_tuple(self.file_specs, "file coordinate specs")
        if len(specs) != 2 or any(type(item) is not CanonicalFileCoordinateSpecV4R1 for item in specs):
            raise UtilityProtocolV4Error("coordinate authority must contain exact test1/test2 specs")
        if tuple(item.source_file_identity for item in specs) != ("hai-test1.csv", "hai-test2.csv"):
            raise UtilityProtocolV4Error("coordinate file ordering differs")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_file_coordinate_authority",
            "control_revision": UTILITY_PROTOCOL_V4_CONTROL_REVISION,
            "csv_structure_report_hash": self.csv_structure_report_hash,
            "file_specs": [item.to_dict() for item in self.file_specs],
            "schema_version": SCHEMA_VERSION,
        }

    @property
    def authority_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "authority_hash": self.authority_hash}

    def spec_for(self, source_file_identity: str) -> CanonicalFileCoordinateSpecV4R1:
        matches = [item for item in self.file_specs if item.source_file_identity == source_file_identity]
        if len(matches) != 1:
            raise UtilityProtocolV4Error("coordinate file identity is not canonical")
        return matches[0]


def _canonical_file_coordinate_specs_v4_r1() -> tuple[CanonicalFileCoordinateSpecV4R1, ...]:
    return (
        CanonicalFileCoordinateSpecV4R1(
            "hai-test1.csv",
            "hai-23.05/hai-test1.csv",
            "78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be",
            INNER_SPLIT_ID,
            54_000,
            "2022-08-12 16:00:01",
            "2022-08-13 07:00:00",
            1,
            True,
            0,
        ),
        CanonicalFileCoordinateSpecV4R1(
            "hai-test2.csv",
            "hai-23.05/hai-test2.csv",
            "b2b8dd295aefd87e39260fe43cb4c73ee86d6264b0ac4b0761e7efb0c2b545c3",
            OUTER_SPLIT_ID,
            230_400,
            "2022-08-17 00:00:01",
            "2022-08-19 16:00:00",
            1,
            True,
            0,
        ),
    )


def _canonical_file_coordinate_authority_value_v4_r1() -> CanonicalFileCoordinateAuthorityV4R1:
    return CanonicalFileCoordinateAuthorityV4R1(
        CSV_STRUCTURE_REPORT_HASH,
        _canonical_file_coordinate_specs_v4_r1(),
    )


def validate_canonical_file_coordinate_authority_v4_r1(
    authority: CanonicalFileCoordinateAuthorityV4R1,
) -> str:
    if type(authority) is not CanonicalFileCoordinateAuthorityV4R1:
        raise UtilityProtocolV4Error("file coordinate authority type differs")
    expected = _canonical_file_coordinate_authority_value_v4_r1()
    if authority != expected or authority.to_dict() != expected.to_dict():
        raise UtilityProtocolV4Error("file coordinate authority replay differs")
    return authority.authority_hash


def build_canonical_file_coordinate_authority_v4_r1(
    csv_structure_report: Mapping[str, Any],
) -> CanonicalFileCoordinateAuthorityV4R1:
    if type(csv_structure_report) is not dict:
        raise UtilityProtocolV4Error("CSV structure report must be an exact dictionary")
    observed = _sha(csv_structure_report.get("report_hash"), "report_hash")
    payload = {key: value for key, value in csv_structure_report.items() if key != "report_hash"}
    if observed != CSV_STRUCTURE_REPORT_HASH or stable_hash_v1(payload) != observed:
        raise UtilityProtocolV4Error("CSV structure report self-hash differs")
    records = csv_structure_report.get("records")
    if type(records) is not list:
        raise UtilityProtocolV4Error("CSV structure report records must be a JSON list")
    expected_specs = _canonical_file_coordinate_specs_v4_r1()
    for spec in expected_specs:
        matches = [record for record in records if type(record) is dict and record.get("relative_path") == spec.relative_path]
        if len(matches) != 1:
            raise UtilityProtocolV4Error("canonical coordinate record is missing or ambiguous")
        record = matches[0]
        record_hash = _sha(record.get("artifact_hash"), "coordinate record artifact_hash")
        if stable_hash_v1({key: value for key, value in record.items() if key != "artifact_hash"}) != record_hash:
            raise UtilityProtocolV4Error("coordinate record self-hash differs")
        expected_record_fields = {
            "duplicate_timestamp_count": spec.duplicate_timestamp_count,
            "file_sha256": spec.file_sha256,
            "first_timestamp": spec.first_timestamp,
            "last_timestamp": spec.last_timestamp,
            "nominal_timestamp_delta_seconds": float(spec.nominal_delta_seconds),
            "row_count": spec.row_count,
            "test_file_structural_only": True,
            "timestamps_strictly_increasing": spec.timestamps_strictly_increasing,
        }
        if any(record.get(key) != value for key, value in expected_record_fields.items()):
            raise UtilityProtocolV4Error("coordinate record differs from frozen public provenance")
    return _canonical_file_coordinate_authority_value_v4_r1()


def _canonical_timestamp_v4_r1(spec: CanonicalFileCoordinateSpecV4R1, physical_row_index: int) -> str:
    index = _strict_int(physical_row_index, "physical_row_index")
    if index >= spec.row_count:
        raise UtilityProtocolV4Error("row coordinate is outside the physical file")
    first = datetime.strptime(spec.first_timestamp, "%Y-%m-%d %H:%M:%S")
    value = first + timedelta(seconds=index * spec.nominal_delta_seconds)
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _canonical_timestamp_identity_v4_r1(
    spec: CanonicalFileCoordinateSpecV4R1,
    physical_row_index: int,
) -> str:
    return stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_canonical_timestamp_identity",
            "canonical_timestamp": _canonical_timestamp_v4_r1(spec, physical_row_index),
            "control_revision": UTILITY_PROTOCOL_V4_CONTROL_REVISION,
            "csv_structure_report_hash": CSV_STRUCTURE_REPORT_HASH,
            "nominal_delta_seconds": spec.nominal_delta_seconds,
            "physical_row_index": physical_row_index,
            "source_file_identity": spec.source_file_identity,
            "source_file_sha256": spec.file_sha256,
            "split_identity": spec.split_identity,
        }
    )


@dataclass(frozen=True)
class CanonicalWindowCoordinateAuthorityV4R1:
    opportunity_id: str
    rule_descriptor_hash: str
    file_coordinate_authority_hash: str
    source_file_identity: str
    source_file_sha256: str
    split_identity: str
    physical_row_count: int
    source_feature_identity: str
    target_feature_identity: str
    source_event_physical_row_index: int
    selected_horizon_seconds: int
    source_pre_range: tuple[int, int]
    source_post_range: tuple[int, int]
    target_baseline_range: tuple[int, int]
    target_response_range: tuple[int, int]
    decision_physical_row_index: int
    source_boundary_reason: str | None
    target_boundary_reason: str | None
    within_split_derived: bool
    boundary_window_policy_hash: str
    purge_policy_hash: str
    event_policy_hash: str
    terminal_transition_policy_hash: str
    source_window_coordinate_identity: str
    target_window_coordinate_identity: str
    boundary_decision_identity: str

    def __post_init__(self) -> None:
        for name in (
            "opportunity_id",
            "rule_descriptor_hash",
            "file_coordinate_authority_hash",
            "source_file_sha256",
            "split_identity",
            "boundary_window_policy_hash",
            "purge_policy_hash",
            "event_policy_hash",
            "terminal_transition_policy_hash",
            "source_window_coordinate_identity",
            "target_window_coordinate_identity",
            "boundary_decision_identity",
        ):
            _sha(getattr(self, name), name)
        for name in ("source_file_identity", "source_feature_identity", "target_feature_identity"):
            _strict_str(getattr(self, name), name)
        for name in (
            "physical_row_count",
            "source_event_physical_row_index",
            "selected_horizon_seconds",
            "decision_physical_row_index",
        ):
            _strict_int(getattr(self, name), name, minimum=0)
        for name in (
            "source_pre_range",
            "source_post_range",
            "target_baseline_range",
            "target_response_range",
        ):
            value = _strict_tuple(getattr(self, name), name)
            if len(value) != 2 or any(type(item) is not int for item in value):
                raise UtilityProtocolV4Error(f"{name} must be an exact integer pair")
        if self.source_boundary_reason not in {None, "insufficient_source_pre_window", "incomplete_source_post_window"}:
            raise UtilityProtocolV4Error("source boundary reason differs")
        if self.source_boundary_reason is not None and type(self.source_boundary_reason) is not str:
            raise UtilityProtocolV4Error("source boundary reason type differs")
        if self.target_boundary_reason not in {None, "file_boundary", "split_boundary"}:
            raise UtilityProtocolV4Error("target boundary reason differs")
        if self.target_boundary_reason is not None and type(self.target_boundary_reason) is not str:
            raise UtilityProtocolV4Error("target boundary reason type differs")
        _strict_bool(self.within_split_derived, "within_split_derived")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_window_coordinate_authority",
            "boundary_decision_identity": self.boundary_decision_identity,
            "boundary_window_policy_hash": self.boundary_window_policy_hash,
            "control_revision": UTILITY_PROTOCOL_V4_CONTROL_REVISION,
            "decision_physical_row_index": self.decision_physical_row_index,
            "event_policy_hash": self.event_policy_hash,
            "file_coordinate_authority_hash": self.file_coordinate_authority_hash,
            "opportunity_id": self.opportunity_id,
            "physical_row_count": self.physical_row_count,
            "purge_policy_hash": self.purge_policy_hash,
            "rule_descriptor_hash": self.rule_descriptor_hash,
            "selected_horizon_seconds": self.selected_horizon_seconds,
            "source_boundary_reason": self.source_boundary_reason,
            "source_event_physical_row_index": self.source_event_physical_row_index,
            "source_feature_identity": self.source_feature_identity,
            "source_file_identity": self.source_file_identity,
            "source_file_sha256": self.source_file_sha256,
            "source_post_range": list(self.source_post_range),
            "source_pre_range": list(self.source_pre_range),
            "source_window_coordinate_identity": self.source_window_coordinate_identity,
            "split_identity": self.split_identity,
            "target_baseline_range": list(self.target_baseline_range),
            "target_boundary_reason": self.target_boundary_reason,
            "target_feature_identity": self.target_feature_identity,
            "target_response_range": list(self.target_response_range),
            "target_window_coordinate_identity": self.target_window_coordinate_identity,
            "terminal_transition_policy_hash": self.terminal_transition_policy_hash,
            "within_split_derived": self.within_split_derived,
        }

    @property
    def coordinate_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "coordinate_hash": self.coordinate_hash}


def _window_coordinate_components_v4_r1(
    opportunity: "CanonicalOpportunityV4",
    rule: "CanonicalRuleDescriptorV4",
    coordinate_authority: CanonicalFileCoordinateAuthorityV4R1,
) -> dict[str, Any]:
    spec = coordinate_authority.spec_for(opportunity.source_file_identity)
    index = _strict_int(opportunity.physical_row_index, "physical_row_index")
    horizon = _strict_int(rule.selected_horizon_seconds, "selected_horizon_seconds", minimum=1)
    source_pre = (index - SOURCE_PRE_WINDOW, index)
    source_post = (index, index + SOURCE_POST_WINDOW)
    target_baseline = (index - TARGET_BASELINE_WINDOW, index)
    target_response = (index + horizon, index + horizon + TARGET_RESPONSE_WINDOW)
    decision = target_response[1] - 1
    source_reason = (
        "insufficient_source_pre_window"
        if source_pre[0] < 0
        else "incomplete_source_post_window"
        if source_post[1] > spec.row_count
        else None
    )
    target_reason = "file_boundary" if target_baseline[0] < 0 or target_response[1] > spec.row_count else None

    coordinate = next(item for item in FILE_COORDINATES if item.feature_file == spec.source_file_identity)
    if coordinate.feature_sha256 != spec.file_sha256 or coordinate.split_id != spec.split_identity:
        raise UtilityProtocolV4Error("V2 file/split coordinate authority differs")
    if not (coordinate.logical_end <= VIRTUAL_PURGE_RANGE[0] or coordinate.logical_start >= VIRTUAL_PURGE_RANGE[1]):
        raise UtilityProtocolV4Error("canonical file coordinate overlaps the virtual purge")
    logical_index = physical_to_logical_v2(spec.source_file_identity, index)
    if target_reason is None:
        logical_decision = physical_to_logical_v2(spec.source_file_identity, decision)
        if not coordinate.logical_start <= logical_decision < coordinate.logical_end:
            raise UtilityProtocolV4Error("target decision leaves canonical split authority")
        if VIRTUAL_PURGE_RANGE[0] <= logical_decision < VIRTUAL_PURGE_RANGE[1]:
            raise UtilityProtocolV4Error("target decision enters the virtual purge")
    else:
        logical_decision = None
    within_split = target_reason is None
    source_window_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_source_window_coordinate_identity",
            "boundary_window_policy_hash": BOUNDARY_WINDOW_POLICY_HASH,
            "control_revision": UTILITY_PROTOCOL_V4_CONTROL_REVISION,
            "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
            "file_coordinate_authority_hash": coordinate_authority.authority_hash,
            "opportunity_id": opportunity.opportunity_id,
            "physical_row_index": index,
            "source_feature_identity": rule.source,
            "source_file_sha256": spec.file_sha256,
            "source_post_range": list(source_post),
            "source_pre_range": list(source_pre),
        }
    )
    target_window_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_target_window_coordinate_identity",
            "boundary_window_policy_hash": BOUNDARY_WINDOW_POLICY_HASH,
            "control_revision": UTILITY_PROTOCOL_V4_CONTROL_REVISION,
            "file_coordinate_authority_hash": coordinate_authority.authority_hash,
            "opportunity_id": opportunity.opportunity_id,
            "selected_horizon_seconds": horizon,
            "source_file_sha256": spec.file_sha256,
            "target_baseline_range": list(target_baseline),
            "target_feature_identity": rule.target,
            "target_response_range": list(target_response),
            "terminal_transition_policy_hash": TERMINAL_TRANSITION_POLICY_HASH,
        }
    )
    boundary_identity = stable_hash_v1(
        {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_boundary_decision_identity",
            "control_revision": UTILITY_PROTOCOL_V4_CONTROL_REVISION,
            "logical_source_row_index": logical_index,
            "logical_target_decision_index": logical_decision,
            "purge_policy_hash": PURGE_POLICY_HASH,
            "source_boundary_reason": source_reason,
            "target_boundary_reason": target_reason,
            "within_split_derived": within_split,
        }
    )
    return {
        "opportunity_id": opportunity.opportunity_id,
        "rule_descriptor_hash": rule.descriptor_hash,
        "file_coordinate_authority_hash": coordinate_authority.authority_hash,
        "source_file_identity": spec.source_file_identity,
        "source_file_sha256": spec.file_sha256,
        "split_identity": spec.split_identity,
        "physical_row_count": spec.row_count,
        "source_feature_identity": rule.source,
        "target_feature_identity": rule.target,
        "source_event_physical_row_index": index,
        "selected_horizon_seconds": horizon,
        "source_pre_range": source_pre,
        "source_post_range": source_post,
        "target_baseline_range": target_baseline,
        "target_response_range": target_response,
        "decision_physical_row_index": decision,
        "source_boundary_reason": source_reason,
        "target_boundary_reason": target_reason,
        "within_split_derived": within_split,
        "boundary_window_policy_hash": BOUNDARY_WINDOW_POLICY_HASH,
        "purge_policy_hash": PURGE_POLICY_HASH,
        "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
        "terminal_transition_policy_hash": TERMINAL_TRANSITION_POLICY_HASH,
        "source_window_coordinate_identity": source_window_identity,
        "target_window_coordinate_identity": target_window_identity,
        "boundary_decision_identity": boundary_identity,
    }


def build_canonical_window_coordinate_authority_v4_r1(
    opportunity: "CanonicalOpportunityV4",
    authority: "UtilityProtocolV4CanonicalAuthority",
) -> CanonicalWindowCoordinateAuthorityV4R1:
    validate_canonical_opportunity_v4(opportunity, authority)
    rule = authority.rule_by_binding(opportunity.relation_binding_hash)
    return CanonicalWindowCoordinateAuthorityV4R1(
        **_window_coordinate_components_v4_r1(opportunity, rule, authority.file_coordinate_authority)
    )


def validate_canonical_window_coordinate_authority_v4_r1(
    coordinate: CanonicalWindowCoordinateAuthorityV4R1,
    opportunity: "CanonicalOpportunityV4",
    authority: "UtilityProtocolV4CanonicalAuthority",
) -> str:
    if type(coordinate) is not CanonicalWindowCoordinateAuthorityV4R1:
        raise UtilityProtocolV4Error("window coordinate authority type differs")
    for field in fields(CanonicalWindowCoordinateAuthorityV4R1):
        value = getattr(coordinate, field.name)
        if field.name in {
            "physical_row_count",
            "source_event_physical_row_index",
            "selected_horizon_seconds",
            "decision_physical_row_index",
        }:
            _strict_int(value, field.name)
        elif field.name in {
            "source_pre_range",
            "source_post_range",
            "target_baseline_range",
            "target_response_range",
        }:
            pair = _strict_tuple(value, field.name)
            if len(pair) != 2 or any(type(item) is not int for item in pair):
                raise UtilityProtocolV4Error(f"{field.name} must be an exact integer pair")
        elif field.name == "within_split_derived":
            _strict_bool(value, field.name)
        elif field.name in {"source_boundary_reason", "target_boundary_reason"}:
            if value is not None and type(value) is not str:
                raise UtilityProtocolV4Error(f"{field.name} type differs")
        else:
            _strict_str(value, field.name)
    expected = build_canonical_window_coordinate_authority_v4_r1(opportunity, authority)
    if coordinate != expected or coordinate.to_dict() != expected.to_dict():
        raise UtilityProtocolV4Error("window coordinate authority replay differs")
    return coordinate.coordinate_hash


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
class CanonicalEnumerationAuthorityContractV4R1:
    protocol_version: str
    control_revision: str
    historical_v4_authority_hash: str
    full_census_plan_hash: str
    portfolio_identity: str
    common_portfolio_hash: str
    rule_descriptor_count: int
    numeric_authority_descriptor_hash: str
    feature_schema_authority_hash: str
    dataset_manifest_identity: str
    split_identities: tuple[str, str]
    opportunity_enumeration_policy_hash: str
    source_event_policy_hash: str
    file_coordinate_authority_hash: str
    denominator_policy: str
    caller_opportunity_set_authorized: bool
    caller_denominator_authorized: bool
    caller_opportunity_count_authorized: bool
    caller_relation_subset_authorized: bool
    real_enumeration_authority_available: bool

    def __post_init__(self) -> None:
        if self.protocol_version != PROTOCOL_VERSION or self.control_revision != UTILITY_PROTOCOL_V4_CONTROL_REVISION:
            raise UtilityProtocolV4Error("enumeration protocol/control revision differs")
        for name in (
            "historical_v4_authority_hash",
            "full_census_plan_hash",
            "common_portfolio_hash",
            "numeric_authority_descriptor_hash",
            "feature_schema_authority_hash",
            "dataset_manifest_identity",
            "opportunity_enumeration_policy_hash",
            "source_event_policy_hash",
            "file_coordinate_authority_hash",
        ):
            _sha(getattr(self, name), name)
        if self.historical_v4_authority_hash != HISTORICAL_CANONICAL_V4_AUTHORITY_HASH:
            raise UtilityProtocolV4Error("enumeration historical V4 lineage differs")
        if self.portfolio_identity != UTILITY_MAIN_PORTFOLIO:
            raise UtilityProtocolV4Error("enumeration portfolio differs")
        if _strict_int(self.rule_descriptor_count, "rule_descriptor_count", minimum=1) != 42:
            raise UtilityProtocolV4Error("enumeration rule count differs")
        if _strict_tuple(self.split_identities, "split_identities") != (INNER_SPLIT_ID, OUTER_SPLIT_ID):
            raise UtilityProtocolV4Error("enumeration split identities differ")
        if self.denominator_policy != DENOMINATOR_POLICY_V4_R1:
            raise UtilityProtocolV4Error("enumeration denominator policy differs")
        for name in (
            "caller_opportunity_set_authorized",
            "caller_denominator_authorized",
            "caller_opportunity_count_authorized",
            "caller_relation_subset_authorized",
            "real_enumeration_authority_available",
        ):
            if _strict_bool(getattr(self, name), name) is not False:
                raise UtilityProtocolV4Error("enumeration contract grants caller or real authority")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_enumeration_authority_contract",
            "caller_denominator_authorized": self.caller_denominator_authorized,
            "caller_opportunity_count_authorized": self.caller_opportunity_count_authorized,
            "caller_opportunity_set_authorized": self.caller_opportunity_set_authorized,
            "caller_relation_subset_authorized": self.caller_relation_subset_authorized,
            "common_portfolio_hash": self.common_portfolio_hash,
            "control_revision": self.control_revision,
            "dataset_manifest_identity": self.dataset_manifest_identity,
            "denominator_policy": self.denominator_policy,
            "feature_schema_authority_hash": self.feature_schema_authority_hash,
            "file_coordinate_authority_hash": self.file_coordinate_authority_hash,
            "full_census_plan_hash": self.full_census_plan_hash,
            "historical_v4_authority_hash": self.historical_v4_authority_hash,
            "numeric_authority_descriptor_hash": self.numeric_authority_descriptor_hash,
            "opportunity_enumeration_policy_hash": self.opportunity_enumeration_policy_hash,
            "portfolio_identity": self.portfolio_identity,
            "protocol_version": self.protocol_version,
            "real_enumeration_authority_available": self.real_enumeration_authority_available,
            "rule_descriptor_count": self.rule_descriptor_count,
            "schema_version": SCHEMA_VERSION,
            "source_event_policy_hash": self.source_event_policy_hash,
            "split_identities": list(self.split_identities),
        }

    @property
    def contract_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "contract_hash": self.contract_hash}


def build_canonical_enumeration_authority_contract_v4_r1(
    plan: CanonicalFullCensusPlanV4,
    coordinate_authority: CanonicalFileCoordinateAuthorityV4R1,
) -> CanonicalEnumerationAuthorityContractV4R1:
    return CanonicalEnumerationAuthorityContractV4R1(
        PROTOCOL_VERSION,
        UTILITY_PROTOCOL_V4_CONTROL_REVISION,
        HISTORICAL_CANONICAL_V4_AUTHORITY_HASH,
        plan.plan_hash,
        UTILITY_MAIN_PORTFOLIO,
        plan.common_portfolio_hash,
        42,
        plan.numeric_authority_descriptor_hash,
        plan.feature_schema_authority_hash,
        DATASET_MANIFEST_ID,
        (INNER_SPLIT_ID, OUTER_SPLIT_ID),
        OPPORTUNITY_ENUMERATION_POLICY_HASH,
        CORRECTED_EVENT_POLICY_HASH,
        coordinate_authority.authority_hash,
        DENOMINATOR_POLICY_V4_R1,
        False,
        False,
        False,
        False,
        REAL_ENUMERATION_AUTHORITY_AVAILABLE,
    )


def validate_canonical_enumeration_authority_contract_v4_r1(
    contract: CanonicalEnumerationAuthorityContractV4R1,
    authority: "UtilityProtocolV4CanonicalAuthority",
) -> str:
    validate_utility_protocol_v4_authority(authority)
    if type(contract) is not CanonicalEnumerationAuthorityContractV4R1:
        raise UtilityProtocolV4Error("enumeration authority contract type differs")
    expected = build_canonical_enumeration_authority_contract_v4_r1(
        authority.full_census_plan, authority.file_coordinate_authority
    )
    if contract != expected or contract.to_dict() != expected.to_dict():
        raise UtilityProtocolV4Error("enumeration authority contract replay differs")
    return contract.contract_hash


@dataclass(frozen=True)
class RuntimeEvidenceAuthorityContractV4R1:
    protocol_version: str
    control_revision: str
    historical_v4_authority_hash: str
    file_coordinate_authority_hash: str
    enumeration_authority_contract_hash: str
    numeric_authority_descriptor_hash: str
    boundary_window_policy_hash: str
    purge_policy_hash: str
    event_policy_hash: str
    transition_policy_hash: str
    frozen_source_trigger_policy_hash: str
    frozen_response_policy_hash: str
    source_evidence_required_bindings: tuple[str, ...]
    response_evidence_required_bindings: tuple[str, ...]
    synthetic_helper_authority_scope: str
    caller_source_window_authorized: bool
    caller_target_window_authorized: bool
    caller_within_split_authorized: bool
    caller_response_matched_authorized: bool
    deterministic_coordinate_boundary_abstention_authorized: bool
    synthetic_helper_metric_custody_authorized: bool
    evaluator_evidence_required: bool
    real_source_evidence_authority_available: bool
    real_response_evidence_authority_available: bool

    def __post_init__(self) -> None:
        if self.protocol_version != PROTOCOL_VERSION or self.control_revision != UTILITY_PROTOCOL_V4_CONTROL_REVISION:
            raise UtilityProtocolV4Error("runtime evidence protocol/control revision differs")
        for name in (
            "historical_v4_authority_hash",
            "file_coordinate_authority_hash",
            "enumeration_authority_contract_hash",
            "numeric_authority_descriptor_hash",
            "boundary_window_policy_hash",
            "purge_policy_hash",
            "event_policy_hash",
            "transition_policy_hash",
            "frozen_source_trigger_policy_hash",
            "frozen_response_policy_hash",
        ):
            _sha(getattr(self, name), name)
        if self.historical_v4_authority_hash != HISTORICAL_CANONICAL_V4_AUTHORITY_HASH:
            raise UtilityProtocolV4Error("runtime evidence historical V4 lineage differs")
        if self.synthetic_helper_authority_scope != SYNTHETIC_TRANSITION_AUTHORITY_SCOPE:
            raise UtilityProtocolV4Error("synthetic helper authority scope differs")
        if _strict_tuple(self.source_evidence_required_bindings, "source_evidence_required_bindings") != SOURCE_EVIDENCE_REQUIRED_BINDINGS_V4_R1:
            raise UtilityProtocolV4Error("source evidence binding schema differs")
        if _strict_tuple(self.response_evidence_required_bindings, "response_evidence_required_bindings") != RESPONSE_EVIDENCE_REQUIRED_BINDINGS_V4_R1:
            raise UtilityProtocolV4Error("response evidence binding schema differs")
        for name in (
            "caller_source_window_authorized",
            "caller_target_window_authorized",
            "caller_within_split_authorized",
            "caller_response_matched_authorized",
            "synthetic_helper_metric_custody_authorized",
            "real_source_evidence_authority_available",
            "real_response_evidence_authority_available",
        ):
            if _strict_bool(getattr(self, name), name) is not False:
                raise UtilityProtocolV4Error("runtime evidence contract grants prohibited authority")
        if _strict_bool(
            self.deterministic_coordinate_boundary_abstention_authorized,
            "deterministic_coordinate_boundary_abstention_authorized",
        ) is not True:
            raise UtilityProtocolV4Error("coordinate-derived boundary abstention must remain authorized")
        if _strict_bool(self.evaluator_evidence_required, "evaluator_evidence_required") is not True:
            raise UtilityProtocolV4Error("runtime evaluator evidence must be required")

    def _payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_runtime_evidence_authority_contract",
            "boundary_window_policy_hash": self.boundary_window_policy_hash,
            "caller_response_matched_authorized": self.caller_response_matched_authorized,
            "caller_source_window_authorized": self.caller_source_window_authorized,
            "caller_target_window_authorized": self.caller_target_window_authorized,
            "caller_within_split_authorized": self.caller_within_split_authorized,
            "control_revision": self.control_revision,
            "deterministic_coordinate_boundary_abstention_authorized": self.deterministic_coordinate_boundary_abstention_authorized,
            "enumeration_authority_contract_hash": self.enumeration_authority_contract_hash,
            "evaluator_evidence_required": self.evaluator_evidence_required,
            "event_policy_hash": self.event_policy_hash,
            "file_coordinate_authority_hash": self.file_coordinate_authority_hash,
            "frozen_response_policy_hash": self.frozen_response_policy_hash,
            "frozen_source_trigger_policy_hash": self.frozen_source_trigger_policy_hash,
            "historical_v4_authority_hash": self.historical_v4_authority_hash,
            "numeric_authority_descriptor_hash": self.numeric_authority_descriptor_hash,
            "protocol_version": self.protocol_version,
            "purge_policy_hash": self.purge_policy_hash,
            "real_response_evidence_authority_available": self.real_response_evidence_authority_available,
            "real_source_evidence_authority_available": self.real_source_evidence_authority_available,
            "response_evidence_required_bindings": list(self.response_evidence_required_bindings),
            "schema_version": SCHEMA_VERSION,
            "source_evidence_required_bindings": list(self.source_evidence_required_bindings),
            "synthetic_helper_authority_scope": self.synthetic_helper_authority_scope,
            "synthetic_helper_metric_custody_authorized": self.synthetic_helper_metric_custody_authorized,
            "transition_policy_hash": self.transition_policy_hash,
        }

    @property
    def contract_hash(self) -> str:
        return stable_hash_v1(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "contract_hash": self.contract_hash}


def build_runtime_evidence_authority_contract_v4_r1(
    numeric_authority: NumericAuthorityDescriptorV4,
    coordinate_authority: CanonicalFileCoordinateAuthorityV4R1,
    enumeration_authority_contract: CanonicalEnumerationAuthorityContractV4R1,
) -> RuntimeEvidenceAuthorityContractV4R1:
    return RuntimeEvidenceAuthorityContractV4R1(
        PROTOCOL_VERSION,
        UTILITY_PROTOCOL_V4_CONTROL_REVISION,
        HISTORICAL_CANONICAL_V4_AUTHORITY_HASH,
        coordinate_authority.authority_hash,
        enumeration_authority_contract.contract_hash,
        numeric_authority.descriptor_hash,
        BOUNDARY_WINDOW_POLICY_HASH,
        PURGE_POLICY_HASH,
        CORRECTED_EVENT_POLICY_HASH,
        TERMINAL_TRANSITION_POLICY_HASH,
        FROZEN_SOURCE_TRIGGER_POLICY_HASH,
        FROZEN_RESPONSE_POLICY_HASH,
        SOURCE_EVIDENCE_REQUIRED_BINDINGS_V4_R1,
        RESPONSE_EVIDENCE_REQUIRED_BINDINGS_V4_R1,
        SYNTHETIC_TRANSITION_AUTHORITY_SCOPE,
        False,
        False,
        False,
        CALLER_RESPONSE_MATCHED_AUTHORIZED,
        True,
        False,
        True,
        REAL_SOURCE_EVIDENCE_AUTHORITY_AVAILABLE,
        REAL_RESPONSE_EVIDENCE_AUTHORITY_AVAILABLE,
    )


def validate_runtime_evidence_authority_contract_v4_r1(
    contract: RuntimeEvidenceAuthorityContractV4R1,
    authority: "UtilityProtocolV4CanonicalAuthority",
) -> str:
    validate_utility_protocol_v4_authority(authority)
    if type(contract) is not RuntimeEvidenceAuthorityContractV4R1:
        raise UtilityProtocolV4Error("runtime evidence authority contract type differs")
    expected = build_runtime_evidence_authority_contract_v4_r1(
        authority.numeric_authority,
        authority.file_coordinate_authority,
        authority.enumeration_authority_contract,
    )
    if contract != expected or contract.to_dict() != expected.to_dict():
        raise UtilityProtocolV4Error("runtime evidence authority contract replay differs")
    return contract.contract_hash


@dataclass(frozen=True)
class UtilityProtocolV4CanonicalAuthority:
    numeric_authority: NumericAuthorityDescriptorV4
    rule_descriptors: tuple[CanonicalRuleDescriptorV4, ...]
    feature_schema: CanonicalFeatureSchemaV4
    full_census_plan: CanonicalFullCensusPlanV4
    private_resolver_contract: PrivateNumericResolverContractV4
    file_coordinate_authority: CanonicalFileCoordinateAuthorityV4R1
    enumeration_authority_contract: CanonicalEnumerationAuthorityContractV4R1
    runtime_evidence_authority_contract: RuntimeEvidenceAuthorityContractV4R1
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
        if self.enumeration_authority_contract.full_census_plan_hash != self.full_census_plan.plan_hash:
            raise UtilityProtocolV4Error("enumeration contract and census plan differ")
        if self.enumeration_authority_contract.file_coordinate_authority_hash != self.file_coordinate_authority.authority_hash:
            raise UtilityProtocolV4Error("enumeration and coordinate authorities differ")
        if self.runtime_evidence_authority_contract.file_coordinate_authority_hash != self.file_coordinate_authority.authority_hash:
            raise UtilityProtocolV4Error("runtime evidence and coordinate authorities differ")
        if self.runtime_evidence_authority_contract.numeric_authority_descriptor_hash != self.numeric_authority.descriptor_hash:
            raise UtilityProtocolV4Error("runtime evidence and numeric authorities differ")
        if self.runtime_evidence_authority_contract.enumeration_authority_contract_hash != self.enumeration_authority_contract.contract_hash:
            raise UtilityProtocolV4Error("runtime evidence and enumeration authorities differ")

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
            "control_revision": UTILITY_PROTOCOL_V4_CONTROL_REVISION,
            "caller_opportunity_set_authorized": False,
            "caller_response_outcome_authorized": False,
            "canonical_enumeration_authority_contract_hash": self.enumeration_authority_contract.contract_hash,
            "canonical_file_coordinate_authority_hash": self.file_coordinate_authority.authority_hash,
            "event_policy_hash": CORRECTED_EVENT_POLICY_HASH,
            "feature_schema": self.feature_schema.to_dict(),
            "full_census_plan": self.full_census_plan.to_dict(),
            "historical_v3_focused_audit_hashes": dict(V3_FOCUSED_AUDIT_HASHES),
            "historical_v4_authority_hash": HISTORICAL_CANONICAL_V4_AUTHORITY_HASH,
            "main_portfolio": UTILITY_MAIN_PORTFOLIO,
            "metric_policy_hash": CORRECTED_METRIC_POLICY_HASH,
            "numeric_authority": self.numeric_authority.to_dict(),
            "private_resolver_contract_hash": self.private_resolver_contract.contract_hash,
            "protocol_version": PROTOCOL_VERSION,
            "real_enumeration_authority_available": REAL_ENUMERATION_AUTHORITY_AVAILABLE,
            "real_response_evidence_authority_available": REAL_RESPONSE_EVIDENCE_AUTHORITY_AVAILABLE,
            "real_source_evidence_authority_available": REAL_SOURCE_EVIDENCE_AUTHORITY_AVAILABLE,
            "recursive_canonical_type_policy_hash": RECURSIVE_CANONICAL_TYPE_POLICY_HASH_R1,
            "regression_authority_hashes": list(self.regression_authority_hashes),
            "runtime_evidence_authority_contract_hash": self.runtime_evidence_authority_contract.contract_hash,
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
    coordinate = build_canonical_file_coordinate_authority_v4_r1(csv_structure_report)
    enumeration_contract = build_canonical_enumeration_authority_contract_v4_r1(plan, coordinate)
    runtime_evidence_contract = build_runtime_evidence_authority_contract_v4_r1(
        numeric, coordinate, enumeration_contract
    )
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
        coordinate,
        enumeration_contract,
        runtime_evidence_contract,
        BLOCKER_CLOSURES,
        (
            CORRECTED_REGRESSION_NUMERIC_REFERENCE_AUTHORITY_HASH,
            CORRECTED_EVENT_POLICY_HASH,
            CORRECTED_METRIC_POLICY_HASH,
        ),
    )


def _reconstruct_exact_dataclass_v4_r1(value: object, expected_type: type[Any], name: str) -> object:
    if type(value) is not expected_type:
        raise UtilityProtocolV4Error(f"{name} must use its exact canonical dataclass")
    return expected_type(*(getattr(value, field.name) for field in fields(expected_type)))


def _exact_string_tuple_v4_r1(value: object, name: str, *, length: int | None = None) -> tuple[str, ...]:
    result = _strict_tuple(value, name)
    if length is not None and len(result) != length:
        raise UtilityProtocolV4Error(f"{name} length differs")
    if any(type(item) is not str for item in result):
        raise UtilityProtocolV4Error(f"{name} must contain exact strings")
    return result


def _exact_string_pairs_v4_r1(value: object, name: str, *, length: int | None = None) -> tuple[tuple[str, str], ...]:
    result = _strict_tuple(value, name)
    if length is not None and len(result) != length:
        raise UtilityProtocolV4Error(f"{name} length differs")
    for item in result:
        if type(item) is not tuple or len(item) != 2 or any(type(member) is not str for member in item):
            raise UtilityProtocolV4Error(f"{name} must contain exact 2-tuples of strings")
    return result


def validate_recursive_canonical_types_v4_r1(
    authority: UtilityProtocolV4CanonicalAuthority,
) -> str:
    """Replay the complete internal object graph before JSON hashing.

    JSON arrays intentionally serialize tuples and lists alike.  This exact
    internal-type boundary therefore runs before any ``to_dict`` or authority
    hash calculation.
    """

    if type(authority) is not UtilityProtocolV4CanonicalAuthority:
        raise UtilityProtocolV4Error("canonical V4 authority type differs")

    numeric = authority.numeric_authority
    _strict_str(numeric.authority_version, "numeric authority_version")
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
        _sha(getattr(numeric, name), name)
    for name in ("record_count", "reference_count", "relation_count", "role_count"):
        _strict_int(getattr(numeric, name), name, minimum=1)
    for name in (
        "historical_e1_identity_restored",
        "historical_numeric_identity_restored",
        "t2_utility_scope_authorized",
    ):
        _strict_bool(getattr(numeric, name), name)
    _reconstruct_exact_dataclass_v4_r1(numeric, NumericAuthorityDescriptorV4, "numeric authority")

    rules = _strict_tuple(authority.rule_descriptors, "rule_descriptors")
    if len(rules) != 42:
        raise UtilityProtocolV4Error("rule descriptor tuple length differs")
    for rule in rules:
        if type(rule) is not CanonicalRuleDescriptorV4:
            raise UtilityProtocolV4Error("rule descriptor class differs")
        for name in (
            "relation_identity",
            "relation_binding_hash",
            "semantic_execution_hash",
            "source",
            "target",
            "source_direction",
            "target_direction",
            "numeric_authority_descriptor_hash",
        ):
            _strict_str(getattr(rule, name), name)
        _strict_int(rule.selected_horizon_seconds, "selected_horizon_seconds", minimum=1)
        _exact_string_pairs_v4_r1(rule.numeric_reference_bindings, "numeric_reference_bindings", length=10)
        _reconstruct_exact_dataclass_v4_r1(rule, CanonicalRuleDescriptorV4, "rule descriptor")

    schema = authority.feature_schema
    if type(schema) is not CanonicalFeatureSchemaV4:
        raise UtilityProtocolV4Error("feature schema class differs")
    for name in (
        "source_features",
        "target_features",
        "union_features",
        "common_source_footprint",
        "common_target_footprint",
        "common_feature_footprint",
    ):
        _exact_string_tuple_v4_r1(getattr(schema, name), name)
    _exact_string_pairs_v4_r1(schema.metadata_authorities, "metadata_authorities")
    _sha(schema.canonical_v3_schema_report_hash, "canonical_v3_schema_report_hash")
    _sha(schema.canonical_runtime_schema_hash, "canonical_runtime_schema_hash")
    _reconstruct_exact_dataclass_v4_r1(schema, CanonicalFeatureSchemaV4, "feature schema")

    plan = authority.full_census_plan
    if type(plan) is not CanonicalFullCensusPlanV4:
        raise UtilityProtocolV4Error("full census plan class differs")
    _exact_string_tuple_v4_r1(plan.rule_descriptor_hashes, "rule_descriptor_hashes", length=42)
    for name in (
        "portfolio_identity",
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
        _strict_str(getattr(plan, name), name)
    _reconstruct_exact_dataclass_v4_r1(plan, CanonicalFullCensusPlanV4, "full census plan")

    resolver = authority.private_resolver_contract
    if type(resolver) is not PrivateNumericResolverContractV4:
        raise UtilityProtocolV4Error("private resolver contract class differs")
    _exact_string_tuple_v4_r1(resolver.lookup_key_fields, "lookup_key_fields", length=2)
    for name in (
        "numeric_authority_descriptor_hash",
        "private_registry_content_hash",
        "materialized_authority_audit_receipt_hash",
        "exact_local_locator_hash",
    ):
        _sha(getattr(resolver, name), name)
    _strict_int(resolver.expected_records, "expected_records", minimum=1)
    for name in (
        "returns_partial_lookup_on_failure",
        "historical_private_authority_required",
        "exposes_private_serialization",
    ):
        _strict_bool(getattr(resolver, name), name)
    _reconstruct_exact_dataclass_v4_r1(resolver, PrivateNumericResolverContractV4, "private resolver contract")

    coordinate = authority.file_coordinate_authority
    if type(coordinate) is not CanonicalFileCoordinateAuthorityV4R1:
        raise UtilityProtocolV4Error("file coordinate authority class differs")
    coordinate_specs = _strict_tuple(coordinate.file_specs, "file coordinate specs")
    _sha(coordinate.csv_structure_report_hash, "csv_structure_report_hash")
    for spec in coordinate_specs:
        if type(spec) is not CanonicalFileCoordinateSpecV4R1:
            raise UtilityProtocolV4Error("file coordinate spec class differs")
        for name in (
            "source_file_identity",
            "relative_path",
            "file_sha256",
            "split_identity",
            "first_timestamp",
            "last_timestamp",
        ):
            _strict_str(getattr(spec, name), name)
        _strict_int(spec.row_count, "row_count", minimum=1)
        _strict_int(spec.nominal_delta_seconds, "nominal_delta_seconds", minimum=1)
        _strict_bool(spec.timestamps_strictly_increasing, "timestamps_strictly_increasing")
        _strict_int(spec.duplicate_timestamp_count, "duplicate_timestamp_count")
        _reconstruct_exact_dataclass_v4_r1(spec, CanonicalFileCoordinateSpecV4R1, "file coordinate spec")
    _reconstruct_exact_dataclass_v4_r1(
        coordinate, CanonicalFileCoordinateAuthorityV4R1, "file coordinate authority"
    )

    enumeration = authority.enumeration_authority_contract
    if type(enumeration) is not CanonicalEnumerationAuthorityContractV4R1:
        raise UtilityProtocolV4Error("enumeration authority contract class differs")
    _exact_string_tuple_v4_r1(enumeration.split_identities, "enumeration split identities", length=2)
    for field in fields(CanonicalEnumerationAuthorityContractV4R1):
        value = getattr(enumeration, field.name)
        if field.name in {
            "rule_descriptor_count",
        }:
            _strict_int(value, field.name, minimum=1)
        elif field.name in {
            "caller_opportunity_set_authorized",
            "caller_denominator_authorized",
            "caller_opportunity_count_authorized",
            "caller_relation_subset_authorized",
            "real_enumeration_authority_available",
        }:
            _strict_bool(value, field.name)
        elif field.name != "split_identities":
            _strict_str(value, field.name)
    _reconstruct_exact_dataclass_v4_r1(
        enumeration, CanonicalEnumerationAuthorityContractV4R1, "enumeration authority contract"
    )

    runtime = authority.runtime_evidence_authority_contract
    _exact_string_tuple_v4_r1(
        runtime.source_evidence_required_bindings,
        "source_evidence_required_bindings",
        length=len(SOURCE_EVIDENCE_REQUIRED_BINDINGS_V4_R1),
    )
    _exact_string_tuple_v4_r1(
        runtime.response_evidence_required_bindings,
        "response_evidence_required_bindings",
        length=len(RESPONSE_EVIDENCE_REQUIRED_BINDINGS_V4_R1),
    )
    for field in fields(RuntimeEvidenceAuthorityContractV4R1):
        value = getattr(runtime, field.name)
        if field.name in {
            "caller_source_window_authorized",
            "caller_target_window_authorized",
            "caller_within_split_authorized",
            "caller_response_matched_authorized",
            "deterministic_coordinate_boundary_abstention_authorized",
            "synthetic_helper_metric_custody_authorized",
            "evaluator_evidence_required",
            "real_source_evidence_authority_available",
            "real_response_evidence_authority_available",
        }:
            _strict_bool(value, field.name)
        elif field.name not in {
            "source_evidence_required_bindings",
            "response_evidence_required_bindings",
        }:
            _strict_str(value, field.name)
    _reconstruct_exact_dataclass_v4_r1(
        runtime, RuntimeEvidenceAuthorityContractV4R1, "runtime evidence authority contract"
    )

    _exact_string_pairs_v4_r1(authority.blocker_closures, "blocker_closures", length=8)
    regression = _exact_string_tuple_v4_r1(
        authority.regression_authority_hashes, "regression_authority_hashes", length=3
    )
    for value in regression:
        _sha(value, "regression authority hash")

    UtilityProtocolV4CanonicalAuthority(
        numeric,
        rules,
        schema,
        plan,
        resolver,
        coordinate,
        enumeration,
        runtime,
        authority.blocker_closures,
        authority.regression_authority_hashes,
    )
    return RECURSIVE_CANONICAL_TYPE_POLICY_HASH_R1


def validate_utility_protocol_v4_authority(authority: UtilityProtocolV4CanonicalAuthority) -> str:
    validate_recursive_canonical_types_v4_r1(authority)
    if CANONICAL_V4_AUTHORITY_HASH == "__TO_BE_FROZEN_R1__":
        raise UtilityProtocolV4Error("canonical V4 authority hash is not frozen")
    if authority.authority_hash != CANONICAL_V4_AUTHORITY_HASH:
        raise UtilityProtocolV4Error("canonical V4 authority identity differs")
    UtilityProtocolV4CanonicalAuthority(
        authority.numeric_authority,
        authority.rule_descriptors,
        authority.feature_schema,
        authority.full_census_plan,
        authority.private_resolver_contract,
        authority.file_coordinate_authority,
        authority.enumeration_authority_contract,
        authority.runtime_evidence_authority_contract,
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
        "artifact_type": "task039e3_r2r_utility_protocol_v4_r1_canonical_row_time_identity",
        "control_revision": UTILITY_PROTOCOL_V4_CONTROL_REVISION,
        "dataset_manifest_identity": row_time.dataset_manifest_identity,
        "file_coordinate_authority_hash": _canonical_file_coordinate_authority_value_v4_r1().authority_hash,
        "physical_row_index": row_time.physical_row_index,
        "source_file_identity": row_time.source_file_identity,
        "split_identity": row_time.split_identity,
        "timestamp_identity": row_time.timestamp_identity,
    }


def build_canonical_row_time_identity_v4(
    *, source_file_identity: str, physical_row_index: int, timestamp_identity: str | None = None
) -> CanonicalRowTimeIdentityV4:
    file_identity = _strict_str(source_file_identity, "source_file_identity")
    coordinate_authority = _canonical_file_coordinate_authority_value_v4_r1()
    spec = coordinate_authority.spec_for(file_identity)
    index = _strict_int(physical_row_index, "physical_row_index")
    if index >= spec.row_count:
        raise UtilityProtocolV4Error("row coordinate is outside the physical file")
    if timestamp_identity is not None:
        _sha(timestamp_identity, "deprecated timestamp_identity")
    timestamp = _canonical_timestamp_identity_v4_r1(spec, index)
    values = {
        "dataset_manifest_identity": DATASET_MANIFEST_ID,
        "split_identity": spec.split_identity,
        "source_file_identity": file_identity,
        "physical_row_index": index,
        "timestamp_identity": timestamp,
    }
    provisional = _construct(CanonicalRowTimeIdentityV4, **values, row_time_identity="")
    return _construct(
        CanonicalRowTimeIdentityV4,
        **values,
        row_time_identity=stable_hash_v1(_row_time_payload(provisional)),
    )


def validate_canonical_row_time_identity_v4(row_time: CanonicalRowTimeIdentityV4) -> str:
    if type(row_time) is not CanonicalRowTimeIdentityV4:
        raise UtilityProtocolV4Error("canonical row/time identity type differs")
    _strict_str(row_time.dataset_manifest_identity, "dataset_manifest_identity")
    _strict_str(row_time.split_identity, "split_identity")
    _strict_str(row_time.source_file_identity, "source_file_identity")
    _strict_int(row_time.physical_row_index, "physical_row_index")
    _sha(row_time.timestamp_identity, "timestamp_identity")
    _sha(row_time.row_time_identity, "row_time_identity")
    expected = build_canonical_row_time_identity_v4(
        source_file_identity=row_time.source_file_identity,
        physical_row_index=row_time.physical_row_index,
    )
    observed = tuple(getattr(row_time, field.name) for field in fields(CanonicalRowTimeIdentityV4))
    canonical = tuple(getattr(expected, field.name) for field in fields(CanonicalRowTimeIdentityV4))
    if observed != canonical:
        raise UtilityProtocolV4Error("canonical row/time coordinate replay differs")
    return row_time.row_time_identity


def _opportunity_payload(opportunity: CanonicalOpportunityV4) -> dict[str, Any]:
    return {
        "control_revision": UTILITY_PROTOCOL_V4_CONTROL_REVISION,
        "file_coordinate_authority_hash": _canonical_file_coordinate_authority_value_v4_r1().authority_hash,
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
    validate_canonical_row_time_identity_v4(row_time)
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
    for field in fields(CanonicalOpportunityV4):
        value = getattr(opportunity, field.name)
        if field.name in {"selected_horizon_seconds", "physical_row_index"}:
            _strict_int(value, field.name)
        else:
            _strict_str(value, field.name)
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
    expected_row = build_canonical_row_time_identity_v4(
        source_file_identity=opportunity.source_file_identity,
        physical_row_index=index,
    )
    if (
        opportunity.dataset_manifest_identity != expected_row.dataset_manifest_identity
        or opportunity.split_identity != expected_row.split_identity
        or opportunity.timestamp_identity != expected_row.timestamp_identity
        or opportunity.canonical_row_time_identity != expected_row.row_time_identity
    ):
        raise UtilityProtocolV4Error("opportunity row/time provenance differs")
    if stable_hash_v1(_opportunity_payload(opportunity)) != opportunity.opportunity_id:
        raise UtilityProtocolV4Error("opportunity identity preimage differs")
    return opportunity.opportunity_id


def _validate_non_authoritative_opportunity_tuple_structure_v4_r1(
    opportunities: object,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> None:
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
    return None


def validate_canonical_opportunity_set_v4(
    opportunities: object,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> str:
    """Compatibility entrypoint that never grants full-census authority."""

    _validate_non_authoritative_opportunity_tuple_structure_v4_r1(opportunities, authority)
    raise UtilityProtocolV4Error(
        "caller opportunity tuples cannot establish authoritative full-census custody"
    )


def build_source_qualification_state_v4(
    opportunity: CanonicalOpportunityV4,
    authority: UtilityProtocolV4CanonicalAuthority,
    *,
    source_window_identity: str,
    retained_source_event_identity: str,
    retained_source_event_census_hash: str,
) -> SourceQualificationStateV4:
    """Build a ``SYNTHETIC_CONTRACT_ONLY`` source-state fixture.

    This compatibility helper is not evaluator evidence and cannot enter R1
    metric custody.
    """
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
    """Validate synthetic structure only; this does not grant evidence authority."""
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
    """Exercise ``SYNTHETIC_CONTRACT_ONLY`` transition semantics.

    Caller booleans are retained for historical synthetic tests only.  They
    are never accepted by the R1 authoritative metric-custody boundary.
    """
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
    """Validate a synthetic transition object, never authoritative evidence."""
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


def validate_authoritative_terminal_metric_custody_v4_r1(
    terminal_state: object,
    source_evidence: object,
    opportunity: CanonicalOpportunityV4,
    window_coordinate: CanonicalWindowCoordinateAuthorityV4R1,
    authority: UtilityProtocolV4CanonicalAuthority,
) -> str:
    """Fail closed until an audited evaluator can issue real evidence.

    Coordinate and contract replay are available in R1.  Empirical source and
    response evidence are deliberately unavailable, so neither legacy helper
    objects nor caller-created replacements may enter metric custody.
    """

    validate_utility_protocol_v4_authority(authority)
    validate_runtime_evidence_authority_contract_v4_r1(
        authority.runtime_evidence_authority_contract, authority
    )
    validate_canonical_opportunity_v4(opportunity, authority)
    validate_canonical_window_coordinate_authority_v4_r1(
        window_coordinate, opportunity, authority
    )
    if type(source_evidence) is SourceQualificationStateV4:
        raise UtilityProtocolV4Error("synthetic source state cannot enter authoritative metric custody")
    if type(terminal_state) is TargetEvaluationStateV4:
        raise UtilityProtocolV4Error("synthetic terminal state cannot enter authoritative metric custody")
    if (
        not REAL_SOURCE_EVIDENCE_AUTHORITY_AVAILABLE
        or not REAL_RESPONSE_EVIDENCE_AUTHORITY_AVAILABLE
    ):
        raise UtilityProtocolV4Error("real evaluator evidence authority is not available")
    raise UtilityProtocolV4Error("authoritative terminal evidence schema is not implemented")


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
