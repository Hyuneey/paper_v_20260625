"""Additive authority closure for the TASK-039E3 R2R utility protocol.

Protocol V1 remains immutable historical input.  This module closes only the
ten findings frozen by the independent audit.  It contains metadata and pure
synthetic/custody helpers; it cannot load HAI test rows or labels, execute real
utility, grant Rule v2/runtime authority, or contact a provider.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Any, Mapping, Sequence

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.relation_profiling_protocol_v1 import (
    FROZEN_SOURCES,
    SOURCE_IDENTITY_HASH,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-PROTOCOL-REMEDIATION"
PROTOCOL_ID = "BASE_V1_PLUS_REMEDIATION_V2"
SCHEMA_VERSION = "2.0.0"

BASE_PROTOCOL_A = "0eec09c662ecc1c78daa5f661c2471aba69cf905"
BASE_PROTOCOL_B = "c021768fc29a4560bd1bc52f5ed61462731be1c7"
BASE_PROTOCOL_BUNDLE = "189c662b83e82ed47137d7e67f52ff97580662ef65e696a5d5715d2dddaae86d"
BASE_PROTOCOL_RECEIPT = "f6db67c4ec4c3f64f0acc8031e27f583fc3192029170184e42dd721dbaf15949"
BLOCKED_AUDIT_A = "de5dd26eb2c052f01560627e23dc4041b61ef307"
BLOCKED_AUDIT_B = "65f3e651947c36f21322612b85a6337c3cbded67"
BLOCKED_AUDIT_BUNDLE = "4bac5875b2806d9cdf14500fdca08a8131bf6e75fef9ca28d0ea593aef77525"
BLOCKED_AUDIT_RECEIPT = "8f341b8e50c82a7db9deb347dde66c044734510e4c7e21671828ae7abd06b650"

DATASET_MANIFEST_ID = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
UTILITY_VIEW_ID = "4445c98c0a22e4f53a5679b39b52a984adf342eb02fe893d5d53256ea2133e24"
INNER_SPLIT_ID = "30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0"
OUTER_SPLIT_ID = "9d76358ff109e4a6d2a712a1ff679c199d08e9cc92239160c8016e9efa063203"

E1_PRIVATE_LEDGER_HASH = "0998c6600078b8a0aca7263b6e0b702808cc141b1cbcfe3d0026fddb98c408a7"
E1_COHORT_HASH = "4eb4da843a61a9c72aba59edcdf90e49766fc571af7eade14d500b3d04d363d4"
E0_RELATION_COHORT_HASH = "e71fa69999dbc18310ebb1730fd1d0ea36403763e891b99841ab8cef7ec18732"
E1_MATERIALIZATION_RESULT_HASH = "2831f175f777bc0544513c35926269e05b6360c17e13f70b89d1768f1c7aa164"
EXECUTABLE_EQUIVALENCE_HASH = "3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f"
AUTHORIZED_REFERENCE_SET_HASH = "b65dca687cfbd80471305dd79a9f0fa43b8b72c4959ddf67a3c42a4b9513e079"
AUTHORIZED_REFERENCE_COUNT = 420

HISTORICAL_SOURCE_AUTHORITY_COMMIT = "b6522fb83c4cb92d355f98af778f9a6a3c73362f"
HISTORICAL_SOURCE_IDENTITY_HASH = "0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234"
HISTORICAL_SOURCE_CONFIG_GIT_BLOB = "3daed02833954c72427985145d14b5999f83af66"
HISTORICAL_SOURCE_CONFIG_BYTE_SHA256 = "f02182816190f3f7097a1a7200dbd45ed2a72aad2a2cea3f78a1f47f9d3f2406"
HISTORICAL_SOURCE_MODULE_COMMIT = "c622c082c053176eab170b6176a343eb2cb35384"
HISTORICAL_SOURCE_MODULE_GIT_BLOB = "7d7da2c07cbd5207edc223b4a854885f30b584b3"
HISTORICAL_SOURCE_MODULE_BYTE_SHA256 = "ba7a7ea29eb0d68077a51442691d201915470d16dca751dff3c214a7ead3c529"
UTILITY_SOURCE_UNIVERSE_V2 = (
    "P1_FCV01D", "P1_FCV01Z", "P1_FCV02D", "P1_FCV02Z",
    "P1_FCV03D", "P1_FCV03Z", "P1_LCV01D", "P1_LCV01Z",
    "P1_PCV01D", "P1_PCV01Z", "P1_PCV02Z", "P1_PP04",
)
if tuple(FROZEN_SOURCES) != UTILITY_SOURCE_UNIVERSE_V2 or SOURCE_IDENTITY_HASH != HISTORICAL_SOURCE_IDENTITY_HASH:
    raise RuntimeError("historical 12-source utility authority differs")


class UtilityProtocolV2Error(ValueError):
    """A fail-closed Protocol V2 boundary violation."""


@dataclass(frozen=True)
class FileCoordinateAuthorityV2:
    feature_file: str
    feature_sha256: str
    label_file: str
    label_sha256: str
    logical_start: int
    logical_end: int
    physical_start: int
    physical_end: int
    split_id: str

    def __post_init__(self) -> None:
        if self.logical_end - self.logical_start != self.physical_end - self.physical_start:
            raise UtilityProtocolV2Error("logical and physical coordinate lengths differ")


TEST1_COORDINATE_AUTHORITY = FileCoordinateAuthorityV2(
    feature_file="hai-test1.csv",
    feature_sha256="78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be",
    label_file="label-test1.csv",
    label_sha256="eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc",
    logical_start=0,
    logical_end=54_000,
    physical_start=0,
    physical_end=54_000,
    split_id=INNER_SPLIT_ID,
)
TEST2_COORDINATE_AUTHORITY = FileCoordinateAuthorityV2(
    feature_file="hai-test2.csv",
    feature_sha256="b2b8dd295aefd87e39260fe43cb4c73ee86d6264b0ac4b0761e7efb0c2b545c3",
    label_file="label-test2.csv",
    label_sha256="8090c44981176e39b0f01a7126a80248ac0b93355c00f9db4d4e2f2106452b92",
    logical_start=54_120,
    logical_end=284_520,
    physical_start=0,
    physical_end=230_400,
    split_id=OUTER_SPLIT_ID,
)
VIRTUAL_PURGE_RANGE = (54_000, 54_120)
FILE_COORDINATES = (TEST1_COORDINATE_AUTHORITY, TEST2_COORDINATE_AUTHORITY)


def _strict_int(value: object, name: str, *, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise UtilityProtocolV2Error(f"{name} must be an integer object")
    if minimum is not None and value < minimum:
        raise UtilityProtocolV2Error(f"{name} is below its minimum")
    return value


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UtilityProtocolV2Error(f"{name} must be a numeric object")
    result = float(value)
    if not math.isfinite(result):
        raise UtilityProtocolV2Error(f"{name} must be finite")
    return result


def _require_sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise UtilityProtocolV2Error(f"{name} must be a SHA-256 identity")
    try:
        int(value, 16)
    except ValueError as exc:
        raise UtilityProtocolV2Error(f"{name} must be hexadecimal") from exc
    return value


def _coordinate_authority(file_identity: str) -> FileCoordinateAuthorityV2:
    if not isinstance(file_identity, str):
        raise UtilityProtocolV2Error("file identity must be a string")
    matches = [
        item
        for item in FILE_COORDINATES
        if file_identity in {item.feature_file, item.label_file}
    ]
    if len(matches) != 1:
        raise UtilityProtocolV2Error("file identity is not authority-bound")
    return matches[0]


def logical_to_physical_v2(file_identity: str, logical_index: int) -> int:
    authority = _coordinate_authority(file_identity)
    index = _strict_int(logical_index, "logical_index", minimum=0)
    if VIRTUAL_PURGE_RANGE[0] <= index < VIRTUAL_PURGE_RANGE[1]:
        raise UtilityProtocolV2Error("virtual purge coordinates map to no physical row")
    if not authority.logical_start <= index < authority.logical_end:
        raise UtilityProtocolV2Error("logical index is outside the bound file range")
    return authority.physical_start + index - authority.logical_start


def physical_to_logical_v2(file_identity: str, physical_row: int) -> int:
    authority = _coordinate_authority(file_identity)
    row = _strict_int(physical_row, "physical_row", minimum=0)
    if not authority.physical_start <= row < authority.physical_end:
        raise UtilityProtocolV2Error("physical row is outside the bound file range")
    return authority.logical_start + row - authority.physical_start


NUMERIC_ROLES = (
    "source_step_threshold",
    "source_stability_tolerance",
    "target_noise_scale",
    "source_pre_window_seconds",
    "source_post_window_seconds",
    "minimum_source_stability_fraction",
    "source_refractory_seconds",
    "cross_source_isolation_radius_seconds",
    "target_baseline_window_seconds",
    "target_response_window_seconds",
)
WINDOW_CONSTANT_VALUES: Mapping[str, float] = {
    "source_pre_window_seconds": 5.0,
    "source_post_window_seconds": 5.0,
    "minimum_source_stability_fraction": 0.8,
    "source_refractory_seconds": 10.0,
    "cross_source_isolation_radius_seconds": 2.0,
    "target_baseline_window_seconds": 5.0,
    "target_response_window_seconds": 3.0,
}
NUMERIC_ROLE_ORIGINS: Mapping[str, str] = {
    "source_step_threshold": "d1_fit_derived_source_parameter",
    "source_stability_tolerance": "d1_fit_derived_source_parameter",
    "target_noise_scale": "d1_fit_derived_target_parameter",
    **{role: "d0_preregistered_window_constant" for role in WINDOW_CONSTANT_VALUES},
}
E1_BINDING_FIELDS = frozenset(
    {
        "schema_version", "artifact_type", "relation_identity", "numeric_role",
        "numeric_value", "value_origin", "source_parameter_record_hash",
        "target_parameter_record_hash", "d1_fit_evidence_hash",
        "d2_confirmation_evidence_hash", "window_constant_bundle_hash",
        "evidence_authority", "llm_generated", "runtime_authority",
        "numeric_reference",
    }
)
E1_RECORD_FIELDS = frozenset(
    {
        "schema_version", "artifact_type", "relation_binding_hash",
        "relation_identity", "source", "source_step_direction", "target",
        "target_response_direction", "selected_horizon_seconds",
        "source_parameter_record_hash", "target_parameter_record_hash",
        "d1_fit_evidence_hash", "d2_confirmation_evidence_hash",
        "window_constant_bundle_hash", "numeric_bindings", "evidence_authority",
        "construction_evidence_status", "private_record", "rule_generated",
        "runtime_authority", "artifact_hash",
    }
)


def _verify_self_hash(document: Mapping[str, Any], expected: str | None = None) -> str:
    observed = document.get("artifact_hash")
    if not isinstance(observed, str):
        raise UtilityProtocolV2Error("artifact hash is required")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != observed or (expected is not None and observed != expected):
        raise UtilityProtocolV2Error("artifact self-hash or authority differs")
    return observed


def authorized_reference_specs_v2(
    executable_equivalence: Mapping[str, Any],
) -> tuple[dict[str, str], ...]:
    _verify_self_hash(executable_equivalence, EXECUTABLE_EQUIVALENCE_HASH)
    records = executable_equivalence.get("relation_records")
    if not isinstance(records, list) or len(records) != 42:
        raise UtilityProtocolV2Error("executable equivalence must contain 42 relations")
    result: list[dict[str, str]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise UtilityProtocolV2Error("equivalence record must be a mapping")
        relation_binding = record.get("relation_binding_hash")
        signature = record.get("executable_signature")
        if not isinstance(relation_binding, str) or not isinstance(signature, Mapping):
            raise UtilityProtocolV2Error("equivalence binding is malformed")
        windows = signature.get("window_constant_references")
        if not isinstance(windows, Mapping) or set(windows) != set(WINDOW_CONSTANT_VALUES):
            raise UtilityProtocolV2Error("window reference roles differ")
        pairs = (
            ("source_step_threshold", signature.get("source_threshold_reference")),
            ("source_stability_tolerance", signature.get("source_stability_reference")),
            ("target_noise_scale", signature.get("target_scale_reference")),
            *((role, windows[role]) for role in WINDOW_CONSTANT_VALUES),
        )
        for role, reference in pairs:
            if not isinstance(reference, str) or not reference:
                raise UtilityProtocolV2Error("numeric reference is malformed")
            result.append(
                {
                    "reference": reference,
                    "numeric_role": role,
                    "relation_binding_hash": relation_binding,
                }
            )
    if len(result) != AUTHORIZED_REFERENCE_COUNT or len({item["reference"] for item in result}) != AUTHORIZED_REFERENCE_COUNT:
        raise UtilityProtocolV2Error("authorized reference set is not 420 unique records")
    observed_hash = stable_hash_v1({"records": sorted(result, key=lambda item: item["reference"])})
    if observed_hash != AUTHORIZED_REFERENCE_SET_HASH:
        raise UtilityProtocolV2Error("authorized reference set hash differs")
    return tuple(result)


def _binding_provenance_identity(binding: Mapping[str, Any]) -> str:
    fields = (
        "numeric_reference",
        "numeric_role",
        "relation_identity",
        "evidence_authority",
        "value_origin",
        "d1_fit_evidence_hash",
        "d2_confirmation_evidence_hash",
        "source_parameter_record_hash",
        "target_parameter_record_hash",
        "window_constant_bundle_hash",
    )
    return stable_hash_v1({field: binding.get(field) for field in fields})


def _verified_e1_binding_preimage(binding: Mapping[str, Any]) -> dict[str, Any]:
    if set(binding) != E1_BINDING_FIELDS:
        raise UtilityProtocolV2Error("E1 numeric binding fields differ")
    role = binding.get("numeric_role")
    if role not in (*NUMERIC_ROLES, "selected_delay_horizon_seconds"):
        raise UtilityProtocolV2Error("E1 numeric binding role is unknown")
    expected_origin = (
        "d1_fit_selected_horizon"
        if role == "selected_delay_horizon_seconds"
        else NUMERIC_ROLE_ORIGINS[role]
    )
    if (
        binding.get("artifact_type") != "task039e1_real_private_numeric_binding_v1"
        or binding.get("value_origin") != expected_origin
        or binding.get("evidence_authority") != "approved_construction_evidence"
        or binding.get("llm_generated") is not False
        or binding.get("runtime_authority") is not False
    ):
        raise UtilityProtocolV2Error("E1 numeric binding authority differs")
    _finite_number(binding.get("numeric_value"), "numeric_value")
    preimage = {key: value for key, value in binding.items() if key != "numeric_reference"}
    if stable_hash_v1(preimage) != binding.get("numeric_reference"):
        raise UtilityProtocolV2Error("E1 numeric-reference preimage differs")
    return preimage


def _verify_e1_record(record: Mapping[str, Any]) -> None:
    if set(record) != E1_RECORD_FIELDS:
        raise UtilityProtocolV2Error("E1 parent evidence fields differ")
    if (
        record.get("artifact_type") != "task039e1_real_private_construction_evidence_v1"
        or record.get("evidence_authority") != "approved_construction_evidence"
        or record.get("construction_evidence_status") != "approved"
        or record.get("private_record") is not True
        or record.get("rule_generated") is not False
        or record.get("runtime_authority") is not False
    ):
        raise UtilityProtocolV2Error("E1 parent evidence authority differs")
    if stable_hash_v1({key: value for key, value in record.items() if key != "artifact_hash"}) != record.get("artifact_hash"):
        raise UtilityProtocolV2Error("E1 parent evidence self-hash differs")
    numeric_bindings = record.get("numeric_bindings")
    if not isinstance(numeric_bindings, list) or len(numeric_bindings) != 11:
        raise UtilityProtocolV2Error("E1 parent evidence must contain eleven bindings")
    for binding in numeric_bindings:
        if not isinstance(binding, Mapping):
            raise UtilityProtocolV2Error("E1 numeric binding must be a mapping")
        _verified_e1_binding_preimage(binding)
        if binding.get("relation_identity") != record.get("relation_identity"):
            raise UtilityProtocolV2Error("E1 binding relation identity differs")


def build_private_numeric_registry_v2(
    e1_private_ledger: Mapping[str, Any],
    executable_equivalence: Mapping[str, Any],
) -> dict[str, Any]:
    _verify_self_hash(e1_private_ledger, E1_PRIVATE_LEDGER_HASH)
    if (
        e1_private_ledger.get("artifact_type") != "task039e1_private_construction_evidence_ledger_v1"
        or e1_private_ledger.get("status") != "frozen_task039e1_private_construction_evidence"
        or e1_private_ledger.get("e0_cohort_hash") != E0_RELATION_COHORT_HASH
        or e1_private_ledger.get("record_count") != 42
        or e1_private_ledger.get("numeric_binding_count") != 462
        or e1_private_ledger.get("raw_hai_included") is not False
        or e1_private_ledger.get("attack_test_label_information_included") is not False
        or e1_private_ledger.get("absolute_paths_included") is not False
        or e1_private_ledger.get("rule_generated") is not False
        or e1_private_ledger.get("runtime_authority") is not False
    ):
        raise UtilityProtocolV2Error("E1 private ledger counts differ")
    specs = authorized_reference_specs_v2(executable_equivalence)
    relations = e1_private_ledger.get("records")
    if not isinstance(relations, list) or len(relations) != 42:
        raise UtilityProtocolV2Error("E1 relation records differ")
    bindings: dict[str, list[tuple[Mapping[str, Any], Mapping[str, Any]]]] = {}
    for relation in relations:
        if not isinstance(relation, Mapping):
            raise UtilityProtocolV2Error("E1 relation record is malformed")
        _verify_e1_record(relation)
        for binding in relation.get("numeric_bindings", ()):
            if not isinstance(binding, Mapping) or not isinstance(binding.get("numeric_reference"), str):
                raise UtilityProtocolV2Error("E1 numeric binding is malformed")
            bindings.setdefault(binding["numeric_reference"], []).append((relation, binding))
    output_records: list[dict[str, Any]] = []
    for spec in specs:
        candidates = bindings.get(spec["reference"], ())
        if len(candidates) != 1:
            raise UtilityProtocolV2Error("numeric reference resolution is missing or ambiguous")
        relation, binding = candidates[0]
        if binding.get("numeric_role") != spec["numeric_role"]:
            raise UtilityProtocolV2Error("numeric reference role differs")
        if relation.get("relation_binding_hash") != spec["relation_binding_hash"]:
            raise UtilityProtocolV2Error("numeric reference relation binding differs")
        value = _finite_number(binding.get("numeric_value"), "numeric_value")
        if binding.get("llm_generated") is not False or binding.get("runtime_authority") is not False:
            raise UtilityProtocolV2Error("numeric binding authority differs")
        provenance_text = " ".join(
            str(binding.get(field, "")).lower()
            for field in ("evidence_authority", "value_origin", "artifact_type")
        )
        if any(marker in provenance_text for marker in ("direct_number", "test_label", "utility_label")):
            raise UtilityProtocolV2Error("prohibited numeric provenance")
        if spec["numeric_role"] in WINDOW_CONSTANT_VALUES and value != WINDOW_CONSTANT_VALUES[spec["numeric_role"]]:
            raise UtilityProtocolV2Error("window constant value differs")
        if spec["numeric_role"] in {"source_step_threshold", "target_noise_scale"} and value <= 0:
            raise UtilityProtocolV2Error("positive numeric parameter is outside its domain")
        if spec["numeric_role"] == "source_stability_tolerance" and value < 0:
            raise UtilityProtocolV2Error("stability tolerance is outside its domain")
        binding_preimage = _verified_e1_binding_preimage(binding)
        record = {
            "artifact_type": "task039e3_r2r_utility_numeric_reference_registry_record_v2",
            "schema_version": SCHEMA_VERSION,
            "reference": spec["reference"],
            "numeric_role": spec["numeric_role"],
            "numeric_value": value,
            "authoritative_e1_ledger_hash": E1_PRIVATE_LEDGER_HASH,
            "authoritative_e1_record_hash": relation.get("artifact_hash"),
            "authoritative_e1_binding_hash": stable_hash_v1(dict(binding)),
            "authoritative_e1_binding_preimage": binding_preimage,
            "provenance_identity": _binding_provenance_identity(binding),
            "relation_binding_hash": spec["relation_binding_hash"],
            "relation_identity": binding.get("relation_identity"),
            "evidence_authority": binding.get("evidence_authority"),
            "value_origin": binding.get("value_origin"),
        }
        record["record_hash"] = stable_hash_v1(record)
        output_records.append(record)
    output_records.sort(key=lambda item: item["reference"])
    role_counts = {role: sum(item["numeric_role"] == role for item in output_records) for role in NUMERIC_ROLES}
    result: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_utility_numeric_reference_registry_v2",
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "e1_private_ledger_hash": E1_PRIVATE_LEDGER_HASH,
        "e1_cohort_hash": E1_COHORT_HASH,
        "e1_materialization_result_hash": E1_MATERIALIZATION_RESULT_HASH,
        "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "authorized_reference_set_hash": AUTHORIZED_REFERENCE_SET_HASH,
        "references_requested": AUTHORIZED_REFERENCE_COUNT,
        "unique_resolutions": AUTHORIZED_REFERENCE_COUNT,
        "missing": 0,
        "ambiguous": 0,
        "nonfinite": 0,
        "test_provenance": 0,
        "label_provenance": 0,
        "direct_number_provenance": 0,
        "role_counts": role_counts,
        "record_count": len(output_records),
        "records": output_records,
        "raw_test_values_included": False,
        "label_values_included": False,
        "private_paths_included": False,
    }
    result["artifact_hash"] = stable_hash_v1(result)
    verify_private_numeric_registry_v2(result)
    return result


def verify_private_numeric_registry_v2(registry: Mapping[str, Any]) -> str:
    observed = _verify_self_hash(registry)
    if (
        registry.get("artifact_type") != "task039e3_r2r_utility_numeric_reference_registry_v2"
        or registry.get("schema_version") != SCHEMA_VERSION
        or registry.get("task_id") != TASK_ID
        or registry.get("e1_private_ledger_hash") != E1_PRIVATE_LEDGER_HASH
        or registry.get("e1_cohort_hash") != E1_COHORT_HASH
        or registry.get("e1_materialization_result_hash") != E1_MATERIALIZATION_RESULT_HASH
        or registry.get("executable_equivalence_hash") != EXECUTABLE_EQUIVALENCE_HASH
        or registry.get("references_requested") != AUTHORIZED_REFERENCE_COUNT
        or registry.get("unique_resolutions") != AUTHORIZED_REFERENCE_COUNT
        or registry.get("record_count") != AUTHORIZED_REFERENCE_COUNT
    ):
        raise UtilityProtocolV2Error("registry E1 authority differs")
    if registry.get("authorized_reference_set_hash") != AUTHORIZED_REFERENCE_SET_HASH:
        raise UtilityProtocolV2Error("registry reference authority differs")
    for field in (
        "missing", "ambiguous", "nonfinite", "test_provenance",
        "label_provenance", "direct_number_provenance",
    ):
        if registry.get(field) != 0:
            raise UtilityProtocolV2Error("registry reports a failed authority closure")
    records = registry.get("records")
    if not isinstance(records, list) or len(records) != AUTHORIZED_REFERENCE_COUNT:
        raise UtilityProtocolV2Error("registry must contain 420 records")
    references: set[str] = set()
    role_counts = {role: 0 for role in NUMERIC_ROLES}
    for record in records:
        if not isinstance(record, Mapping):
            raise UtilityProtocolV2Error("registry record must be a mapping")
        expected_hash = stable_hash_v1({key: value for key, value in record.items() if key != "record_hash"})
        if record.get("record_hash") != expected_hash:
            raise UtilityProtocolV2Error("registry record hash differs")
        reference = record.get("reference")
        role = record.get("numeric_role")
        if not isinstance(reference, str) or reference in references or role not in role_counts:
            raise UtilityProtocolV2Error("registry identity or role differs")
        references.add(reference)
        role_counts[role] += 1
        if record.get("authoritative_e1_ledger_hash") != E1_PRIVATE_LEDGER_HASH:
            raise UtilityProtocolV2Error("registry record E1 authority differs")
        binding_preimage = record.get("authoritative_e1_binding_preimage")
        if not isinstance(binding_preimage, Mapping):
            raise UtilityProtocolV2Error("registry record lacks its E1 binding preimage")
        if set(binding_preimage) != E1_BINDING_FIELDS - {"numeric_reference"}:
            raise UtilityProtocolV2Error("registry E1 binding preimage fields differ")
        if stable_hash_v1(dict(binding_preimage)) != reference:
            raise UtilityProtocolV2Error("registry reference differs from its E1 binding preimage")
        if stable_hash_v1({**dict(binding_preimage), "numeric_reference": reference}) != record.get("authoritative_e1_binding_hash"):
            raise UtilityProtocolV2Error("registry E1 binding document hash differs")
        if (
            binding_preimage.get("numeric_role") != role
            or binding_preimage.get("numeric_value") != record.get("numeric_value")
            or binding_preimage.get("relation_identity") != record.get("relation_identity")
            or binding_preimage.get("value_origin") != record.get("value_origin")
            or binding_preimage.get("evidence_authority") != record.get("evidence_authority")
        ):
            raise UtilityProtocolV2Error("registry record differs from its E1 binding preimage")
        if (
            binding_preimage.get("artifact_type") != "task039e1_real_private_numeric_binding_v1"
            or binding_preimage.get("value_origin") != NUMERIC_ROLE_ORIGINS[role]
            or binding_preimage.get("llm_generated") is not False
            or binding_preimage.get("runtime_authority") is not False
            or record.get("provenance_identity")
            != _binding_provenance_identity({**dict(binding_preimage), "numeric_reference": reference})
        ):
            raise UtilityProtocolV2Error("registry record provenance differs")
        _require_sha256(record.get("authoritative_e1_record_hash"), "authoritative_e1_record_hash")
        if record.get("evidence_authority") != "approved_construction_evidence":
            raise UtilityProtocolV2Error("registry record evidence authority differs")
        provenance_text = f"{record.get('value_origin', '')} {record.get('evidence_authority', '')}".lower()
        if any(marker in provenance_text for marker in ("direct_number", "test_label", "utility_label")):
            raise UtilityProtocolV2Error("registry record contains prohibited provenance")
        value = _finite_number(record.get("numeric_value"), "numeric_value")
        if role in WINDOW_CONSTANT_VALUES and value != WINDOW_CONSTANT_VALUES[role]:
            raise UtilityProtocolV2Error("registry window constant differs")
        if role in {"source_step_threshold", "target_noise_scale"} and value <= 0:
            raise UtilityProtocolV2Error("registry positive parameter is outside its domain")
        if role == "source_stability_tolerance" and value < 0:
            raise UtilityProtocolV2Error("registry tolerance is outside its domain")
    if any(count != 42 for count in role_counts.values()) or registry.get("role_counts") != role_counts:
        raise UtilityProtocolV2Error("registry role counts differ")
    observed_reference_set_hash = stable_hash_v1(
        {
            "records": sorted(
                [
                    {
                        "reference": record["reference"],
                        "numeric_role": record["numeric_role"],
                        "relation_binding_hash": record["relation_binding_hash"],
                    }
                    for record in records
                ],
                key=lambda item: item["reference"],
            )
        }
    )
    if observed_reference_set_hash != AUTHORIZED_REFERENCE_SET_HASH:
        raise UtilityProtocolV2Error("registry records differ from the authorized 420-reference set")
    return observed


def resolve_numeric_reference_v2(
    reference: str,
    expected_role: str,
    registry: Mapping[str, Any],
) -> float:
    if not isinstance(reference, str) or not reference or expected_role not in NUMERIC_ROLES:
        raise UtilityProtocolV2Error("reference or expected role is unknown")
    verify_private_numeric_registry_v2(registry)
    matches = [record for record in registry["records"] if record["reference"] == reference]
    if len(matches) != 1 or matches[0]["numeric_role"] != expected_role:
        raise UtilityProtocolV2Error("reference is missing, ambiguous, or role-mismatched")
    return _finite_number(matches[0]["numeric_value"], "numeric_value")


SOURCE_PRE_WINDOW = 5
SOURCE_POST_WINDOW = 5
TARGET_BASELINE_WINDOW = 5
TARGET_RESPONSE_WINDOW = 3
MINIMUM_STABILITY_FRACTION = 0.8
SOURCE_REFRACTORY_SECONDS = 10
CROSS_SOURCE_ISOLATION_RADIUS_SECONDS = 2
SUPPORTED_HORIZONS = frozenset({1, 5, 10, 30, 60})

SOURCE_NOT_FORMED_REASONS = frozenset(
    {"insufficient_source_pre_window", "incomplete_source_post_window", "nonfinite_source_window"}
)
TARGET_ABSTENTION_REASONS = frozenset(
    {"incomplete_target_response_window", "nonfinite_target_window", "file_boundary", "split_boundary"}
)


@dataclass(frozen=True)
class ApplicableRuleEvaluationOpportunityV2:
    relation_binding_hash: str
    source: str
    event_index: int
    horizon_seconds: int
    file_identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.relation_binding_hash, str) or not self.relation_binding_hash:
            raise UtilityProtocolV2Error("relation binding is required")
        if self.source not in UTILITY_SOURCE_UNIVERSE_V2:
            raise UtilityProtocolV2Error("opportunity source is outside the frozen universe")
        _strict_int(self.event_index, "event_index", minimum=0)
        if type(self.horizon_seconds) is not int or self.horizon_seconds not in SUPPORTED_HORIZONS:
            raise UtilityProtocolV2Error("opportunity horizon is unsupported")
        _coordinate_authority(self.file_identity)


@dataclass(frozen=True)
class CandidateDecisionV2:
    status: str
    anomaly: bool | None
    decision_index: int | None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status == "source_opportunity_not_formed":
            valid = self.anomaly is None and self.decision_index is None and self.reason in SOURCE_NOT_FORMED_REASONS
        elif self.status == "no_trigger":
            valid = self.anomaly is False and self.decision_index is None and self.reason is None
        elif self.status == "expected_response":
            valid = self.anomaly is False and type(self.decision_index) is int and self.decision_index >= 0 and self.reason is None
        elif self.status == "anomaly":
            valid = self.anomaly is True and type(self.decision_index) is int and self.decision_index >= 0 and self.reason is None
        elif self.status == "abstain":
            valid = self.anomaly is None and self.decision_index is None and self.reason in TARGET_ABSTENTION_REASONS
        else:
            valid = False
        if not valid:
            raise UtilityProtocolV2Error("candidate decision state is inconsistent")


def source_candidate_indices_v2(physical_row_count: int) -> tuple[int, ...]:
    count = _strict_int(physical_row_count, "physical_row_count", minimum=0)
    if count < SOURCE_PRE_WINDOW + SOURCE_POST_WINDOW:
        return ()
    return tuple(range(SOURCE_PRE_WINDOW, count - SOURCE_POST_WINDOW + 1))


def source_context_state_v2(event_index: int, physical_row_count: int) -> CandidateDecisionV2 | None:
    index = _strict_int(event_index, "event_index", minimum=0)
    count = _strict_int(physical_row_count, "physical_row_count", minimum=0)
    if index < SOURCE_PRE_WINDOW:
        return CandidateDecisionV2("source_opportunity_not_formed", None, None, "insufficient_source_pre_window")
    if index + SOURCE_POST_WINDOW > count:
        return CandidateDecisionV2("source_opportunity_not_formed", None, None, "incomplete_source_post_window")
    return None


def cluster_source_candidates_v2(
    candidates: Sequence[tuple[int, float]],
) -> tuple[tuple[int, float], ...]:
    normalized: list[tuple[int, float]] = []
    for index, amplitude in candidates:
        normalized.append((_strict_int(index, "candidate index", minimum=0), _finite_number(amplitude, "amplitude")))
    ordered = sorted(normalized)
    if not ordered:
        return ()
    clusters: list[list[tuple[int, float]]] = [[ordered[0]]]
    for candidate in ordered[1:]:
        if candidate[0] - clusters[-1][-1][0] <= SOURCE_REFRACTORY_SECONDS:
            clusters[-1].append(candidate)
        else:
            clusters.append([candidate])
    return tuple(min(cluster, key=lambda item: (-abs(item[1]), item[0])) for cluster in clusters)


def is_event_isolated_v2(
    source: str,
    event_index: int,
    retained_events_by_source: Mapping[str, Sequence[int]],
) -> bool:
    if source not in UTILITY_SOURCE_UNIVERSE_V2:
        raise UtilityProtocolV2Error("event source is outside the frozen universe")
    if set(retained_events_by_source) != set(UTILITY_SOURCE_UNIVERSE_V2):
        raise UtilityProtocolV2Error("event mapping must use the exact 12-source universe")
    index = _strict_int(event_index, "event_index", minimum=0)
    normalized: dict[str, tuple[int, ...]] = {}
    for item_source, indices in retained_events_by_source.items():
        normalized[item_source] = tuple(_strict_int(value, "retained event index", minimum=0) for value in indices)
    if index not in normalized[source]:
        raise UtilityProtocolV2Error("evaluated source event is not a retained clustered event")
    return not any(
        abs(index - other_index) <= CROSS_SOURCE_ISOLATION_RADIUS_SECONDS
        for item_source, indices in normalized.items()
        if item_source != source
        for other_index in indices
    )


def form_source_opportunity_v2(
    *,
    relation_binding_hash: str,
    source: str,
    event_index: int,
    horizon_seconds: int,
    file_identity: str,
    physical_row_count: int,
    source_pre: Sequence[float],
    source_post: Sequence[float],
    expected_direction: str,
    source_step_threshold: float,
    source_stability_tolerance: float,
    retained_events_by_source: Mapping[str, Sequence[int]],
) -> ApplicableRuleEvaluationOpportunityV2 | CandidateDecisionV2:
    context = source_context_state_v2(event_index, physical_row_count)
    if context is not None:
        return context
    if len(source_pre) != SOURCE_PRE_WINDOW or len(source_post) != SOURCE_POST_WINDOW:
        raise UtilityProtocolV2Error("source windows must have exact length five")
    threshold = _finite_number(source_step_threshold, "source_step_threshold")
    tolerance = _finite_number(source_stability_tolerance, "source_stability_tolerance")
    if threshold <= 0 or tolerance < 0:
        raise UtilityProtocolV2Error("source numeric parameters are outside their domain")
    if expected_direction not in {"step_up", "step_down"}:
        raise UtilityProtocolV2Error("source direction is unknown")
    source_values: list[float] = []
    try:
        source_values = [_finite_number(value, "source window value") for value in (*source_pre, *source_post)]
    except UtilityProtocolV2Error:
        return CandidateDecisionV2("source_opportunity_not_formed", None, None, "nonfinite_source_window")
    pre_level = float(statistics.median(source_values[:5]))
    post_level = float(statistics.median(source_values[5:]))
    amplitude = post_level - pre_level
    observed_direction = "step_up" if amplitude > 0 else "step_down"
    pre_fraction = sum(abs(value - pre_level) <= tolerance for value in source_values[:5]) / 5.0
    post_fraction = sum(abs(value - post_level) <= tolerance for value in source_values[5:]) / 5.0
    trigger = (
        amplitude != 0
        and abs(amplitude) >= threshold
        and pre_fraction >= MINIMUM_STABILITY_FRACTION
        and post_fraction >= MINIMUM_STABILITY_FRACTION
    )
    if not trigger or not is_event_isolated_v2(source, event_index, retained_events_by_source):
        return CandidateDecisionV2("no_trigger", False, None)
    if observed_direction != expected_direction:
        return CandidateDecisionV2("no_trigger", False, None)
    return ApplicableRuleEvaluationOpportunityV2(
        relation_binding_hash=relation_binding_hash,
        source=source,
        event_index=event_index,
        horizon_seconds=horizon_seconds,
        file_identity=file_identity,
    )


def decision_index_v2(event_index: int, horizon_seconds: int) -> int:
    index = _strict_int(event_index, "event_index", minimum=0)
    if type(horizon_seconds) is not int or horizon_seconds not in SUPPORTED_HORIZONS:
        raise UtilityProtocolV2Error("response horizon is unknown")
    return index + horizon_seconds + TARGET_RESPONSE_WINDOW - 1


def evaluate_target_opportunity_v2(
    opportunity: ApplicableRuleEvaluationOpportunityV2,
    *,
    physical_row_count: int,
    target_baseline: Sequence[float],
    target_response: Sequence[float],
    expected_direction: str,
    target_noise_scale: float,
    within_split: bool = True,
    response_window_complete: bool = True,
) -> CandidateDecisionV2:
    if not isinstance(opportunity, ApplicableRuleEvaluationOpportunityV2):
        raise UtilityProtocolV2Error("an applicable opportunity is required")
    count = _strict_int(physical_row_count, "physical_row_count", minimum=0)
    decision = decision_index_v2(opportunity.event_index, opportunity.horizon_seconds)
    if decision >= count:
        return CandidateDecisionV2("abstain", None, None, "file_boundary")
    if type(within_split) is not bool:
        raise UtilityProtocolV2Error("within_split must be boolean")
    if not within_split:
        return CandidateDecisionV2("abstain", None, None, "split_boundary")
    if type(response_window_complete) is not bool:
        raise UtilityProtocolV2Error("response_window_complete must be boolean")
    if not response_window_complete:
        return CandidateDecisionV2("abstain", None, None, "incomplete_target_response_window")
    if len(target_baseline) != TARGET_BASELINE_WINDOW or len(target_response) != TARGET_RESPONSE_WINDOW:
        raise UtilityProtocolV2Error("target windows must have exact frozen lengths")
    try:
        baseline_values = [_finite_number(value, "target baseline value") for value in target_baseline]
        response_values = [_finite_number(value, "target response value") for value in target_response]
    except UtilityProtocolV2Error:
        return CandidateDecisionV2("abstain", None, None, "nonfinite_target_window")
    noise = _finite_number(target_noise_scale, "target_noise_scale")
    if noise <= 0:
        raise UtilityProtocolV2Error("target noise scale is outside its domain")
    if expected_direction not in {"increase", "decrease"}:
        raise UtilityProtocolV2Error("target direction is unknown")
    baseline = float(statistics.median(baseline_values))
    response = float(statistics.median(response_values)) - baseline
    matches = response > noise if expected_direction == "increase" else response < -noise
    return CandidateDecisionV2("expected_response" if matches else "anomaly", not matches, decision)


def no_rule_diagnostic_v2() -> dict[str, Any]:
    return {
        "no_rule_relation_diagnostic_only": True,
        "interpreter_instances": 0,
        "applicable_opportunities": 0,
        "alarms": 0,
        "abstentions": 0,
        "construction_coverage_contribution": 0,
        "primary_system_attack_event_recall_aggregation": "UNION_DEDUPLICATED_PORTFOLIO_ALARMS_ONLY",
    }


def abstention_rate_v2(
    abstained_applicable_opportunities: int,
    all_applicable_rule_evaluation_opportunities: int,
) -> dict[str, Any]:
    numerator = _strict_int(
        abstained_applicable_opportunities,
        "abstained_applicable_opportunities",
        minimum=0,
    )
    denominator = _strict_int(
        all_applicable_rule_evaluation_opportunities,
        "all_applicable_rule_evaluation_opportunities",
        minimum=0,
    )
    if numerator > denominator:
        raise UtilityProtocolV2Error("abstentions must be a subset of applicable opportunities")
    return {
        "formula_identity": "abstained_applicable_opportunities_over_all_applicable_opportunities_v2",
        "numerator": numerator,
        "denominator": denominator,
        "value": None if denominator == 0 else numerator / denominator,
        "defined": denominator != 0,
        "undefined_reason": "no_applicable_opportunities" if denominator == 0 else None,
        "no_rule_cells_included": False,
    }


@dataclass(frozen=True)
class IntervalV2:
    start: int
    end: int

    def __post_init__(self) -> None:
        _strict_int(self.start, "interval start", minimum=0)
        _strict_int(self.end, "interval end", minimum=0)
        if self.end <= self.start:
            raise UtilityProtocolV2Error("interval must be nonempty and half-open")

    def to_dict(self) -> dict[str, int]:
        return {"start": self.start, "end": self.end}


def strict_binary_labels_v2(labels: Sequence[object]) -> tuple[int, ...]:
    result: list[int] = []
    for value in labels:
        if type(value) is not int or value not in {0, 1}:
            raise UtilityProtocolV2Error("label must be an actual integer 0 or 1")
        result.append(value)
    return tuple(result)


def derive_attack_events_v2(labels: Sequence[object]) -> tuple[IntervalV2, ...]:
    values = strict_binary_labels_v2(labels)
    result: list[IntervalV2] = []
    start: int | None = None
    for index, value in enumerate((*values, 0)):
        if value == 1 and start is None:
            start = index
        elif value == 0 and start is not None:
            result.append(IntervalV2(start, index))
            start = None
    return tuple(result)


def form_alarm_episodes_v2(raw_alarm_timestamps: Sequence[int]) -> tuple[IntervalV2, ...]:
    values = sorted({_strict_int(value, "alarm timestamp", minimum=0) for value in raw_alarm_timestamps})
    if not values:
        return ()
    result: list[IntervalV2] = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
        else:
            result.append(IntervalV2(start, previous + 1))
            start = previous = value
    result.append(IntervalV2(start, previous + 1))
    return tuple(result)


def _event_set_hash(events: Sequence[IntervalV2], strict_label_vector_hash: str) -> str:
    return stable_hash_v1(
        {
            "strict_label_vector_hash": strict_label_vector_hash,
            "interval_semantics": "half_open_file_local_v2",
            "events": [event.to_dict() for event in events],
        }
    )


def _alarm_episode_set_hash(alarm_episodes: Sequence[IntervalV2]) -> str:
    return stable_hash_v1(
        {
            "interval_semantics": "half_open_file_local_v2",
            "alarm_episodes": [episode.to_dict() for episode in alarm_episodes],
        }
    )


@dataclass(frozen=True)
class LabelEventCustodyV2:
    dataset_manifest_id: str
    split_id: str
    feature_file: str
    feature_file_sha256: str
    label_file: str
    label_file_sha256: str
    physical_row_count: int
    strict_label_vector_hash: str
    attack_event_set_hash: str
    attack_event_count: int
    attack_labeled_seconds: int
    normal_labeled_seconds: int
    timestamp_alignment_policy: str

    def __post_init__(self) -> None:
        authority = _coordinate_authority(self.feature_file)
        if self.label_file != authority.label_file:
            raise UtilityProtocolV2Error("feature/label file pairing differs")
        if (
            self.dataset_manifest_id != DATASET_MANIFEST_ID
            or self.split_id != authority.split_id
            or self.feature_file_sha256 != authority.feature_sha256
            or self.label_file_sha256 != authority.label_sha256
            or self.physical_row_count != authority.physical_end
        ):
            raise UtilityProtocolV2Error("label/event custody authority differs")
        for name in ("attack_event_count", "attack_labeled_seconds", "normal_labeled_seconds"):
            _strict_int(getattr(self, name), name, minimum=0)
        if self.attack_labeled_seconds + self.normal_labeled_seconds != self.physical_row_count:
            raise UtilityProtocolV2Error("label exposure counts do not cover the physical file")
        if self.timestamp_alignment_policy != "EXACT_ROW_WISE_AFTER_FROZEN_NORMALIZATION_NO_SHIFT_INTERPOLATION_OR_NEAREST_NEIGHBOR":
            raise UtilityProtocolV2Error("timestamp alignment policy differs")
        for name in ("strict_label_vector_hash", "attack_event_set_hash"):
            _require_sha256(getattr(self, name), name)

    def payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_label_event_custody_v2",
            "schema_version": SCHEMA_VERSION,
            **self.__dict__,
            "virtual_purge_rows_included": False,
            "raw_label_values_included": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self.payload())

    def to_dict(self) -> dict[str, Any]:
        result = self.payload()
        result["artifact_hash"] = self.artifact_hash
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LabelEventCustodyV2":
        observed = value.get("artifact_hash")
        allowed = {
            "artifact_type", "schema_version", "dataset_manifest_id", "split_id",
            "feature_file", "feature_file_sha256", "label_file", "label_file_sha256",
            "physical_row_count", "strict_label_vector_hash", "attack_event_set_hash",
            "attack_event_count", "attack_labeled_seconds", "normal_labeled_seconds",
            "timestamp_alignment_policy", "virtual_purge_rows_included",
            "raw_label_values_included", "artifact_hash",
        }
        if set(value) != allowed:
            raise UtilityProtocolV2Error("label/event custody fields differ")
        result = cls(
            dataset_manifest_id=value["dataset_manifest_id"],
            split_id=value["split_id"],
            feature_file=value["feature_file"],
            feature_file_sha256=value["feature_file_sha256"],
            label_file=value["label_file"],
            label_file_sha256=value["label_file_sha256"],
            physical_row_count=value["physical_row_count"],
            strict_label_vector_hash=value["strict_label_vector_hash"],
            attack_event_set_hash=value["attack_event_set_hash"],
            attack_event_count=value["attack_event_count"],
            attack_labeled_seconds=value["attack_labeled_seconds"],
            normal_labeled_seconds=value["normal_labeled_seconds"],
            timestamp_alignment_policy=value["timestamp_alignment_policy"],
        )
        if observed != result.artifact_hash or value.get("virtual_purge_rows_included") is not False or value.get("raw_label_values_included") is not False:
            raise UtilityProtocolV2Error("label/event custody self-hash or privacy flags differ")
        return result


def build_label_event_custody_v2(
    *,
    labels: Sequence[object],
    feature_file: str,
    feature_file_sha256: str,
    label_file: str,
    label_file_sha256: str,
    split_id: str,
    timestamps_aligned: bool,
) -> tuple[LabelEventCustodyV2, tuple[IntervalV2, ...]]:
    if timestamps_aligned is not True:
        raise UtilityProtocolV2Error("feature/label timestamps must align exactly")
    values = strict_binary_labels_v2(labels)
    authority = _coordinate_authority(feature_file)
    if len(values) != authority.physical_end:
        raise UtilityProtocolV2Error("label row count differs from the physical file authority")
    events = derive_attack_events_v2(values)
    attack_seconds = sum(values)
    label_vector_hash = stable_hash_v1({"encoding": "strict_integer_binary_v2", "labels": list(values)})
    custody = LabelEventCustodyV2(
        dataset_manifest_id=DATASET_MANIFEST_ID,
        split_id=split_id,
        feature_file=feature_file,
        feature_file_sha256=feature_file_sha256,
        label_file=label_file,
        label_file_sha256=label_file_sha256,
        physical_row_count=len(values),
        strict_label_vector_hash=label_vector_hash,
        attack_event_set_hash=_event_set_hash(events, label_vector_hash),
        attack_event_count=len(events),
        attack_labeled_seconds=attack_seconds,
        normal_labeled_seconds=len(values) - attack_seconds,
        timestamp_alignment_policy="EXACT_ROW_WISE_AFTER_FROZEN_NORMALIZATION_NO_SHIFT_INTERPOLATION_OR_NEAREST_NEIGHBOR",
    )
    return custody, events


def _overlap(left: IntervalV2, right: IntervalV2) -> bool:
    return left.start < right.end and right.start < left.end


@dataclass(frozen=True)
class BoundMetricV2:
    metric_name: str
    value: float | None
    numerator: int
    denominator: float
    defined: bool
    undefined_reason: str | None
    label_custody_hash: str
    alarm_episode_set_hash: str

    def __post_init__(self) -> None:
        _strict_int(self.numerator, "metric numerator", minimum=0)
        denominator = _finite_number(self.denominator, "metric denominator")
        if denominator < 0:
            raise UtilityProtocolV2Error("metric denominator must be nonnegative")
        if self.defined:
            if self.value is None or self.undefined_reason is not None or denominator == 0:
                raise UtilityProtocolV2Error("defined metric state is inconsistent")
            observed = _finite_number(self.value, "metric value")
            if not math.isclose(observed, self.numerator / denominator, rel_tol=0, abs_tol=1e-15):
                raise UtilityProtocolV2Error("metric value does not match its count preimage")
        elif self.value is not None or not self.undefined_reason or denominator != 0:
            raise UtilityProtocolV2Error("undefined metric state is inconsistent")

    def payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_bound_metric_v2",
            "schema_version": SCHEMA_VERSION,
            **self.__dict__,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self.payload())

    def to_dict(self) -> dict[str, Any]:
        result = self.payload()
        result["artifact_hash"] = self.artifact_hash
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "BoundMetricV2":
        observed = value.get("artifact_hash")
        allowed = {
            "artifact_type", "schema_version", "metric_name", "value", "numerator",
            "denominator", "defined", "undefined_reason", "label_custody_hash",
            "alarm_episode_set_hash", "artifact_hash",
        }
        if set(value) != allowed:
            raise UtilityProtocolV2Error("bound metric fields differ")
        result = cls(
            metric_name=value["metric_name"], value=value["value"],
            numerator=value["numerator"], denominator=value["denominator"],
            defined=value["defined"], undefined_reason=value["undefined_reason"],
            label_custody_hash=value["label_custody_hash"],
            alarm_episode_set_hash=value["alarm_episode_set_hash"],
        )
        if observed != result.artifact_hash:
            raise UtilityProtocolV2Error("bound metric self-hash differs")
        return result


def _bound_ratio(
    metric_name: str,
    numerator: int,
    denominator: float,
    reason: str,
    custody: LabelEventCustodyV2,
    alarm_episodes: Sequence[IntervalV2],
) -> BoundMetricV2:
    if denominator == 0:
        return BoundMetricV2(
            metric_name, None, numerator, denominator, False, reason,
            custody.artifact_hash, _alarm_episode_set_hash(alarm_episodes),
        )
    return BoundMetricV2(
        metric_name, numerator / denominator, numerator, denominator, True, None,
        custody.artifact_hash, _alarm_episode_set_hash(alarm_episodes),
    )


def _verify_events_match_custody(custody: LabelEventCustodyV2, events: Sequence[IntervalV2]) -> None:
    if _event_set_hash(events, custody.strict_label_vector_hash) != custody.attack_event_set_hash or len(events) != custody.attack_event_count:
        raise UtilityProtocolV2Error("attack events do not match label custody")
    if sum(event.end - event.start for event in events) != custody.attack_labeled_seconds:
        raise UtilityProtocolV2Error("attack-event seconds do not match label custody")


def attack_event_recall_v2(
    custody: LabelEventCustodyV2,
    attack_events: Sequence[IntervalV2],
    alarm_episodes: Sequence[IntervalV2],
) -> BoundMetricV2:
    _verify_events_match_custody(custody, attack_events)
    covered = sum(any(_overlap(event, alarm) for alarm in alarm_episodes) for event in attack_events)
    return _bound_ratio("attack_event_recall", covered, len(attack_events), "no_attack_events", custody, alarm_episodes)


def alarm_episode_precision_v2(
    custody: LabelEventCustodyV2,
    attack_events: Sequence[IntervalV2],
    alarm_episodes: Sequence[IntervalV2],
) -> BoundMetricV2:
    _verify_events_match_custody(custody, attack_events)
    overlapping = sum(any(_overlap(event, alarm) for event in attack_events) for alarm in alarm_episodes)
    return _bound_ratio("alarm_episode_precision", overlapping, len(alarm_episodes), "no_alarm_episodes", custody, alarm_episodes)


def normal_false_alarm_rate_per_hour_v2(
    custody: LabelEventCustodyV2,
    attack_events: Sequence[IntervalV2],
    alarm_episodes: Sequence[IntervalV2],
) -> BoundMetricV2:
    _verify_events_match_custody(custody, attack_events)
    false_alarms = sum(not any(_overlap(event, alarm) for event in attack_events) for alarm in alarm_episodes)
    return _bound_ratio(
        "normal_false_alarm_rate_per_hour",
        false_alarms,
        custody.normal_labeled_seconds / 3600.0,
        "no_normal_exposure",
        custody,
        alarm_episodes,
    )


@dataclass(frozen=True)
class EventF1CustodyV2:
    precision: BoundMetricV2
    recall: BoundMetricV2
    value: float | None
    defined: bool
    undefined_reason: str | None
    formula_identity: str = "harmonic_mean_alarm_episode_precision_attack_event_recall_v2"

    def __post_init__(self) -> None:
        if self.formula_identity != "harmonic_mean_alarm_episode_precision_attack_event_recall_v2":
            raise UtilityProtocolV2Error("Event F1 formula identity differs")
        if self.precision.label_custody_hash != self.recall.label_custody_hash:
            raise UtilityProtocolV2Error("F1 components use different label custody")
        if self.precision.alarm_episode_set_hash != self.recall.alarm_episode_set_hash:
            raise UtilityProtocolV2Error("F1 components use different alarm episodes")
        if not self.precision.defined or not self.recall.defined:
            valid = self.value is None and not self.defined and self.undefined_reason == "precision_or_recall_undefined"
        else:
            assert self.precision.value is not None and self.recall.value is not None
            denominator = self.precision.value + self.recall.value
            expected = 0.0 if denominator == 0 else 2 * self.precision.value * self.recall.value / denominator
            valid = self.defined and self.undefined_reason is None and self.value is not None and math.isclose(self.value, expected, rel_tol=0, abs_tol=1e-15)
        if not valid:
            raise UtilityProtocolV2Error("Event F1 custody is inconsistent")

    def payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "task039e3_r2r_event_f1_custody_v2",
            "schema_version": SCHEMA_VERSION,
            "formula_identity": self.formula_identity,
            "precision_component": self.precision.to_dict(),
            "recall_component": self.recall.to_dict(),
            "value": self.value,
            "defined": self.defined,
            "undefined_reason": self.undefined_reason,
            "fabricated_single_count_preimage": False,
        }

    @property
    def artifact_hash(self) -> str:
        return stable_hash_v1(self.payload())

    def to_dict(self) -> dict[str, Any]:
        result = self.payload()
        result["artifact_hash"] = self.artifact_hash
        return result

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EventF1CustodyV2":
        observed = value.get("artifact_hash")
        allowed = {
            "artifact_type", "schema_version", "formula_identity",
            "precision_component", "recall_component", "value", "defined",
            "undefined_reason", "fabricated_single_count_preimage", "artifact_hash",
        }
        if set(value) != allowed:
            raise UtilityProtocolV2Error("Event F1 custody fields differ")
        precision = BoundMetricV2.from_mapping(value["precision_component"])
        recall = BoundMetricV2.from_mapping(value["recall_component"])
        result = cls(
            precision=precision,
            recall=recall,
            value=value["value"],
            defined=value["defined"],
            undefined_reason=value["undefined_reason"],
            formula_identity=value["formula_identity"],
        )
        if observed != result.artifact_hash or value.get("fabricated_single_count_preimage") is not False:
            raise UtilityProtocolV2Error("Event F1 custody self-hash differs")
        return result


def event_f1_custody_v2(precision: BoundMetricV2, recall: BoundMetricV2) -> EventF1CustodyV2:
    if not precision.defined or not recall.defined:
        return EventF1CustodyV2(precision, recall, None, False, "precision_or_recall_undefined")
    assert precision.value is not None and recall.value is not None
    denominator = precision.value + recall.value
    value = 0.0 if denominator == 0 else 2 * precision.value * recall.value / denominator
    return EventF1CustodyV2(precision, recall, value, True, None)


DELTA_SIGNS = ("NEGATIVE", "ZERO", "POSITIVE")
CONSTRUCTION_PROVIDER_CALLS: Mapping[str, int] = {"T0": 0, "T1": 42, "T1-B": 126, "T2": 42}
U6_STATUS = "COMPARATOR_SPECIFIC_COST_UTILITY_CONTEXT_ONLY"


def exact_delta_sign_v2(value: float) -> str:
    observed = _finite_number(value, "delta")
    return "NEGATIVE" if observed < 0 else "POSITIVE" if observed > 0 else "ZERO"


def classify_t2_tradeoff_v2(
    delta_attack_event_recall: float,
    delta_normal_far_per_hour: float,
) -> dict[str, str]:
    return {
        "delta_attack_event_recall_sign": exact_delta_sign_v2(delta_attack_event_recall),
        "delta_normal_far_per_hour_sign": exact_delta_sign_v2(delta_normal_far_per_hour),
        "classification_basis": "EXACT_TWO_DIMENSIONAL_SIGN_NO_MARGIN_NO_WEIGHTED_SCORE",
    }


def t2_construction_cost_delta_v2(comparator: str) -> int:
    if comparator == "COMMON-42":
        raise UtilityProtocolV2Error("COMMON-42 is a prediction identity and has no single construction cost")
    if comparator not in {"T0", "T1", "T1-B"}:
        raise UtilityProtocolV2Error("T2 cost comparator is unknown")
    return CONSTRUCTION_PROVIDER_CALLS["T2"] - CONSTRUCTION_PROVIDER_CALLS[comparator]


def authority_snapshot_v2() -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "canonical_protocol": PROTOCOL_ID,
        "original_v1_status": "FROZEN_BUT_BLOCKED_BY_INDEPENDENT_AUDIT",
        "utility_source_universe_hash": HISTORICAL_SOURCE_IDENTITY_HASH,
        "utility_source_universe_count": len(UTILITY_SOURCE_UNIVERSE_V2),
        "virtual_purge_non_observation": True,
        "no_rule_relation_diagnostic_only": True,
        "outside_authorized_operating_regime": "NOT_APPLICABLE_FOR_THIS_UTILITY_PROTOCOL",
        "materiality_margin": None,
        "common_prediction_identity_has_single_cost": False,
        "u6_status": U6_STATUS,
        "utility_protocol_audited": False,
        "utility_evaluator_implementation_ready": False,
        "utility_execution_authorization_ready": False,
        "inner_label_access": False,
        "outer_label_access": False,
        "sealed": False,
        "rule_v2": False,
        "production_runtime": False,
        "winner": False,
        "provider": False,
    }


__all__ = [
    "ApplicableRuleEvaluationOpportunityV2",
    "BoundMetricV2",
    "CandidateDecisionV2",
    "CONSTRUCTION_PROVIDER_CALLS",
    "EventF1CustodyV2",
    "FileCoordinateAuthorityV2",
    "IntervalV2",
    "LabelEventCustodyV2",
    "UTILITY_SOURCE_UNIVERSE_V2",
    "UtilityProtocolV2Error",
    "abstention_rate_v2",
    "alarm_episode_precision_v2",
    "attack_event_recall_v2",
    "authority_snapshot_v2",
    "authorized_reference_specs_v2",
    "build_label_event_custody_v2",
    "build_private_numeric_registry_v2",
    "classify_t2_tradeoff_v2",
    "cluster_source_candidates_v2",
    "decision_index_v2",
    "derive_attack_events_v2",
    "evaluate_target_opportunity_v2",
    "event_f1_custody_v2",
    "exact_delta_sign_v2",
    "form_alarm_episodes_v2",
    "form_source_opportunity_v2",
    "is_event_isolated_v2",
    "logical_to_physical_v2",
    "no_rule_diagnostic_v2",
    "normal_false_alarm_rate_per_hour_v2",
    "physical_to_logical_v2",
    "resolve_numeric_reference_v2",
    "source_candidate_indices_v2",
    "source_context_state_v2",
    "strict_binary_labels_v2",
    "t2_construction_cost_delta_v2",
    "verify_private_numeric_registry_v2",
]
