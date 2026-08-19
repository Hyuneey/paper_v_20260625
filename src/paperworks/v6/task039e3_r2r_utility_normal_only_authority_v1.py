"""New normal-only numeric authority for the frozen COMMON-42 utility scope.

This module implements a *new* authority identity.  It deliberately does not
restore, alias, or overwrite historical E1 numeric custody.  The only real-data
capability is a future, explicitly invoked materializer for the two frozen
normal training files.  Importing this module performs no I/O.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import argparse
from typing import Any, Mapping, Sequence
from uuid import uuid4

from paperworks.v6.common import canonical_json_v1, stable_hash_v1
from paperworks.v6.relation_profiling_protocol_v1 import (
    derive_multi_file_source_parameters_v1,
    derive_multi_file_target_scale_v1,
)
from paperworks.v6.task039e1_evidence_materialization_v1 import (
    PreregisteredWindowConstantBundleV1,
)


TASK_ID = "TASK-039E3-R2R-UTILITY-NORMAL-ONLY-AUTHORITY-V1"
AUTHORITY_VERSION = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1"
SCHEMA_VERSION = "1.0.0"
AUTHORITY_LINEAGE = "NEW_VERSION_FROM_FROZEN_METHOD_AND_NORMAL_DATA"
CALIBRATION_POLICY_VERSION = "TASK039D0_CONTINUOUS_STEP_CALIBRATION_V1"
PRIVATE_LOCATOR_ENV = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1"

BASE_COMMIT = "6b3b912aa6b69394a06697c3244589cfe98ecd4a"
ROUTE_C_AUDIT_HASH = "eb2406391e189d3c53613e2c0074d4575cc91403fe047e54066b5a418906e415"
AUTHORITY_DEPENDENCY_MATRIX_HASH = "bbeffb23ec9310f9572e1ab6657d6d18b2ec93e62b18687a70567dcec6ccd74d"
COMMON42_AUTHORITY_CHECK_HASH = "3bd07e1c2baf375bde86a2310b529dda40962e027edbd77485f431dc244730ff"
SELECTED_ROUTE = "ROUTE_C_NEW_NORMAL_ONLY_AUTHORITY_RECONSTITUTION_REQUIRED"

EXECUTABLE_EQUIVALENCE_HASH = "3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f"
E1_PUBLIC_MANIFEST_HASH = "ee8c5b7e9895f5f6afdd1be2563244e3b82dca9c3eadca502dd522940931e3ae"
DATASET_MANIFEST_HASH = "5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2"
D1_DATA_ACCESS_AUDIT_HASH = "b51ec23dd4bad9ed66d7036ec209f6841f99d1e38b0b7766afd16ff75f9004d7"
HISTORICAL_E1_HASH = "0998c6600078b8a0aca7263b6e0b702808cc141b1cbcfe3d0026fddb98c408a7"
HISTORICAL_NUMERIC_REGISTRY_HASH = "59e81b261801f28eefc917256dc628af704a14b4064161972d01545968555271"

SUCCESS_EXECUTION_RECEIPT = "d164f00da3121e345907fe9076e62f4697493f26dde7448cc8527b895cbffa6e"
SUCCESS_EXECUTION_ACCOUNTING = "0e18526c8dbcaec26d67385b89c60826dc4388cac08727cd61a2c60b1b812ae2"
TERMINAL_CUSTODY_SUPPLEMENT = "54d71edb6357e8c4d4a5479a9f0b130ca0f89f10ed4ff04ad9ba90122f3ff7c2"
TERMINAL_AUDIT_A = "3abf1651dd81554a990c26b7b46512ac75fc63e4"
TERMINAL_AUDIT_B = "a431dd88866e0f65439e3fad567894e0e9058713"

COMMON_RELATION_COUNT = 42
UTILITY_NUMERIC_REFERENCE_COUNT = 420
T2_UTILITY_SCOPE_AUTHORIZED = False
HISTORICAL_E1_IDENTITY_RESTORED = False
HISTORICAL_NUMERIC_IDENTITY_RESTORED = False

UTILITY_NUMERIC_ROLES = (
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
HISTORICAL_MANIFEST_ROLES = UTILITY_NUMERIC_ROLES[:3] + (
    "selected_delay_horizon_seconds",
) + UTILITY_NUMERIC_ROLES[3:]

RELATION_PROFILING_SOURCE = "src/paperworks/v6/relation_profiling_protocol_v1.py"
RELATION_PROFILING_GIT_BLOB = "7d7da2c07cbd5207edc223b4a854885f30b584b3"
RELATION_PROFILING_RAW_SHA256 = "ba7a7ea29eb0d68077a51442691d201915470d16dca751dff3c214a7ead3c529"
E1_MATERIALIZATION_SOURCE = "src/paperworks/v6/task039e1_evidence_materialization_v1.py"
E1_MATERIALIZATION_GIT_BLOB = "af4401cbcf2240df8523a36c0ff69a197fdfae4b"
E1_MATERIALIZATION_RAW_SHA256 = "2a6e627fcc95b532fead6619c3aa7d0a6f5781537206cddb2638c736c0856a24"


class NormalOnlyAuthorityV1Error(ValueError):
    """A fail-closed authority, identity, or materialization violation."""


def _strict_int(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise NormalOnlyAuthorityV1Error(f"{name} must be an integer object at least {minimum}")
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise NormalOnlyAuthorityV1Error(f"{name} must be a lowercase SHA-256 identity")
    try:
        int(value, 16)
    except ValueError as exc:
        raise NormalOnlyAuthorityV1Error(f"{name} must be hexadecimal") from exc
    if value != value.lower():
        raise NormalOnlyAuthorityV1Error(f"{name} must be lowercase")
    return value


@dataclass(frozen=True)
class NormalInputIdentityV1:
    logical_role: str
    relative_path: str
    sha256: str
    byte_size: int
    row_count: int
    header_sha256: str

    def __post_init__(self) -> None:
        if self.logical_role not in {"normal_train1", "normal_train2"}:
            raise NormalOnlyAuthorityV1Error("normal input role differs")
        if not self.relative_path.startswith("hai-23.05/hai-train"):
            raise NormalOnlyAuthorityV1Error("normal input path is not frozen")
        _sha(self.sha256, "normal input SHA-256")
        _sha(self.header_sha256, "normal input header SHA-256")
        _strict_int(self.byte_size, "byte_size", minimum=1)
        _strict_int(self.row_count, "row_count", minimum=1)

    def to_dict(self) -> dict[str, object]:
        return {
            "logical_role": self.logical_role,
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "byte_size": self.byte_size,
            "row_count": self.row_count,
            "header_sha256": self.header_sha256,
        }


NORMAL_TRAIN1_IDENTITY = NormalInputIdentityV1(
    logical_role="normal_train1",
    relative_path="hai-23.05/hai-train1.csv",
    sha256="53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a",
    byte_size=162_418_984,
    row_count=280_800,
    header_sha256="95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a",
)
NORMAL_TRAIN2_IDENTITY = NormalInputIdentityV1(
    logical_role="normal_train2",
    relative_path="hai-23.05/hai-train2.csv",
    sha256="0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56",
    byte_size=169_121_615,
    row_count=291_600,
    header_sha256="95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a",
)
NORMAL_INPUT_IDENTITIES = (NORMAL_TRAIN1_IDENTITY, NORMAL_TRAIN2_IDENTITY)
NORMAL_INPUT_IDENTITY_SET_HASH = stable_hash_v1(
    {"normal_input_identities": [item.to_dict() for item in NORMAL_INPUT_IDENTITIES]}
)


@dataclass(frozen=True)
class CalibrationRoleSpecV1:
    numeric_role: str
    source_function: str
    source_path: str
    source_inputs: tuple[str, ...]
    deterministic_formula: str
    normal_split_dependency: str
    relation_dependency: str
    validation: str
    fail_closed_condition: str

    def to_dict(self) -> dict[str, object]:
        return {
            "numeric_role": self.numeric_role,
            "source_function": self.source_function,
            "source_path": self.source_path,
            "source_inputs": list(self.source_inputs),
            "deterministic_formula": self.deterministic_formula,
            "normal_split_dependency": self.normal_split_dependency,
            "relation_dependency": self.relation_dependency,
            "validation": self.validation,
            "fail_closed_condition": self.fail_closed_condition,
        }


CALIBRATION_ROLE_SPECS = (
    CalibrationRoleSpecV1(
        "source_step_threshold",
        "derive_multi_file_source_parameters_v1",
        RELATION_PROFILING_SOURCE,
        ("source values from exact normal train1", "source values from exact normal train2"),
        "noise=max(1.4826*MAD(file-local dx pooled across files),1e-12); "
        "A=abs(median(x[t:t+5])-median(x[t-5:t])); retain A>noise; "
        "threshold=max(5*noise,Q75_linear(A)) with at least 20 retained amplitudes",
        "NORMAL_CANDIDATE_FIT: train1+train2 only; differences and windows file-local",
        "source identity selected by frozen COMMON relation",
        "type float, finite, >0",
        "wrong input identity, nonfinite values, fewer than 20 amplitudes, or unsupported source",
    ),
    CalibrationRoleSpecV1(
        "source_stability_tolerance",
        "derive_multi_file_source_parameters_v1",
        RELATION_PROFILING_SOURCE,
        ("source values from exact normal train1", "source values from exact normal train2"),
        "max(3*source_noise_scale,0.10*source_step_threshold)",
        "NORMAL_CANDIDATE_FIT: train1+train2 only; differences and windows file-local",
        "source identity selected by frozen COMMON relation",
        "type float, finite, >=0",
        "wrong input identity, nonfinite values, unsupported source, or missing threshold preimage",
    ),
    CalibrationRoleSpecV1(
        "target_noise_scale",
        "derive_multi_file_target_scale_v1",
        RELATION_PROFILING_SOURCE,
        ("target values from exact normal train1", "target values from exact normal train2"),
        "max(1.4826*MAD(target file-local one-step changes pooled across files),1e-12)",
        "NORMAL_CANDIDATE_FIT: train1+train2 only; differences file-local",
        "target identity selected by frozen COMMON relation; scale reused per target",
        "type float, finite, >0",
        "wrong input identity, nonfinite values, or missing target",
    ),
    *tuple(
        CalibrationRoleSpecV1(
            role,
            "PreregisteredWindowConstantBundleV1",
            E1_MATERIALIZATION_SOURCE,
            ("frozen committed protocol constant",),
            f"exact PreregisteredWindowConstantBundleV1.{role}",
            "none; no data access",
            "relation-bound reference with one globally frozen constant",
            (
                "type float, finite, exact 0.8"
                if role == "minimum_source_stability_fraction"
                else "type int, exact frozen positive value"
            ),
            "constant differs from the frozen committed implementation",
        )
        for role in UTILITY_NUMERIC_ROLES[3:]
    ),
)
if tuple(item.numeric_role for item in CALIBRATION_ROLE_SPECS) != UTILITY_NUMERIC_ROLES:
    raise RuntimeError("normal-only calibration role map is incomplete")

CALIBRATION_POLICY_HASH = stable_hash_v1(
    {
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "roles": [item.to_dict() for item in CALIBRATION_ROLE_SPECS],
        "relation_profiling_git_blob": RELATION_PROFILING_GIT_BLOB,
        "e1_materialization_git_blob": E1_MATERIALIZATION_GIT_BLOB,
    }
)


@dataclass(frozen=True)
class CommonRelationAuthorityV1:
    relation_identity: str
    relation_binding_hash: str
    semantic_execution_hash: str
    source: str
    target: str
    source_direction: str
    target_direction: str
    selected_horizon_seconds: int
    historical_reference_pairs: tuple[tuple[str, str], ...]

    def historical_reference(self, role: str) -> str:
        matches = [value for observed_role, value in self.historical_reference_pairs if observed_role == role]
        if len(matches) != 1:
            raise NormalOnlyAuthorityV1Error("historical numeric role binding differs")
        return matches[0]

    def to_identity_dict(self) -> dict[str, object]:
        return {
            "relation_identity": self.relation_identity,
            "relation_binding_hash": self.relation_binding_hash,
            "semantic_execution_hash": self.semantic_execution_hash,
            "source": self.source,
            "target": self.target,
            "source_direction": self.source_direction,
            "target_direction": self.target_direction,
            "selected_horizon_seconds": self.selected_horizon_seconds,
        }


@dataclass(frozen=True)
class NormalOnlyAuthorityDefinitionV1:
    relations: tuple[CommonRelationAuthorityV1, ...]
    reference_identities: tuple[str, ...]
    utility_binding_set_hash: str
    authority_definition_hash: str


def _commit(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise NormalOnlyAuthorityV1Error(f"{name} must be a full Git commit")
    _sha(value + "0" * 24, name)
    return value


def _git_oid(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise NormalOnlyAuthorityV1Error(f"{name} must be a 40-character Git object identity")
    try:
        int(value, 16)
    except ValueError as exc:
        raise NormalOnlyAuthorityV1Error(f"{name} must be hexadecimal") from exc
    if value != value.lower():
        raise NormalOnlyAuthorityV1Error(f"{name} must be lowercase")
    return value


def _verify_self_hash(document: Mapping[str, Any], expected: str, name: str) -> str:
    observed = document.get("artifact_hash")
    if observed != expected:
        raise NormalOnlyAuthorityV1Error(f"{name} authority hash differs")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != observed:
        raise NormalOnlyAuthorityV1Error(f"{name} self-hash differs")
    return observed


def validate_route_c_bindings_v1(
    feasibility_audit: Mapping[str, Any],
    dependency_matrix: Mapping[str, Any],
    common42_check: Mapping[str, Any],
) -> None:
    """Bind the exact completed Route-C audit without reinterpreting it."""

    _verify_self_hash(feasibility_audit, ROUTE_C_AUDIT_HASH, "Route-C feasibility audit")
    _verify_self_hash(dependency_matrix, AUTHORITY_DEPENDENCY_MATRIX_HASH, "dependency matrix")
    _verify_self_hash(common42_check, COMMON42_AUTHORITY_CHECK_HASH, "COMMON-42 check")
    route = feasibility_audit.get("route_decision")
    if not isinstance(route, Mapping) or route.get("selected_route") != SELECTED_ROUTE:
        raise NormalOnlyAuthorityV1Error("Route-C selection differs")
    if feasibility_audit.get("common42_authority_check_hash") != COMMON42_AUTHORITY_CHECK_HASH:
        raise NormalOnlyAuthorityV1Error("COMMON-42 audit cross-binding differs")
    if feasibility_audit.get("authority_dependency_matrix_hash") != AUTHORITY_DEPENDENCY_MATRIX_HASH:
        raise NormalOnlyAuthorityV1Error("dependency matrix cross-binding differs")
    if common42_check.get("authority_status") != "FROZEN_EXECUTABLE_AUTHORITY_AVAILABLE":
        raise NormalOnlyAuthorityV1Error("COMMON-42 is not frozen executable authority")


def validate_normal_input_authorities_v1(
    dataset_manifest: Mapping[str, Any], d1_data_access_audit: Mapping[str, Any]
) -> None:
    """Bind train1/train2 identities to two independent committed reports."""

    _verify_self_hash(dataset_manifest, DATASET_MANIFEST_HASH, "HAI dataset manifest")
    _verify_self_hash(d1_data_access_audit, D1_DATA_ACCESS_AUDIT_HASH, "D1 data-access audit")
    dataset_files = dataset_manifest.get("files")
    d1_files = d1_data_access_audit.get("file_records")
    if not isinstance(dataset_files, list) or not isinstance(d1_files, list):
        raise NormalOnlyAuthorityV1Error("normal file authority records are missing")
    dataset_by_path = {
        item.get("relative_local_path"): item
        for item in dataset_files
        if isinstance(item, Mapping)
    }
    d1_by_path = {
        item.get("relative_path"): item
        for item in d1_files
        if isinstance(item, Mapping)
    }
    for expected in NORMAL_INPUT_IDENTITIES:
        dataset = dataset_by_path.get(expected.relative_path)
        d1 = d1_by_path.get(expected.relative_path)
        if not isinstance(dataset, Mapping) or not isinstance(d1, Mapping):
            raise NormalOnlyAuthorityV1Error("expected normal input identity is absent")
        expected_dataset = {
            "sha256": expected.sha256,
            "byte_size": expected.byte_size,
            "row_count": expected.row_count,
            "logical_file_role": "normal_train_time_series",
            "provenance_status": "verified",
        }
        expected_d1 = {
            "sha256": expected.sha256,
            "byte_size": expected.byte_size,
            "row_count": expected.row_count,
            "header_sha256": expected.header_sha256,
            "file_identity_match": True,
            "header_identity_match": True,
        }
        if any(dataset.get(key) != value for key, value in expected_dataset.items()):
            raise NormalOnlyAuthorityV1Error("dataset-manifest normal identity differs")
        if any(d1.get(key) != value for key, value in expected_d1.items()):
            raise NormalOnlyAuthorityV1Error("D1 normal identity differs")
    if (
        d1_data_access_audit.get("labels_accessed") is not False
        or d1_data_access_audit.get("test_accessed") is not False
        or d1_data_access_audit.get("train3_accessed") is not False
        or d1_data_access_audit.get("train4_accessed") is not False
    ):
        raise NormalOnlyAuthorityV1Error("D1 normal-only access boundary differs")


def new_reference_identity_v1(relation: CommonRelationAuthorityV1, numeric_role: str) -> str:
    """Return a value-independent identity for one new authority reference."""

    if numeric_role not in UTILITY_NUMERIC_ROLES:
        raise NormalOnlyAuthorityV1Error("numeric role is outside the utility authority")
    preimage = {
        "authority_version": AUTHORITY_VERSION,
        "relation_binding_hash": relation.relation_binding_hash,
        "semantic_execution_hash": relation.semantic_execution_hash,
        "numeric_role": numeric_role,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "normal_input_identity_set": NORMAL_INPUT_IDENTITY_SET_HASH,
        "common42_authority_hash": COMMON42_AUTHORITY_CHECK_HASH,
    }
    return f"{AUTHORITY_VERSION}:{stable_hash_v1(preimage)}"


def _signature_reference_pairs(signature: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    windows = signature.get("window_constant_references")
    if not isinstance(windows, Mapping):
        raise NormalOnlyAuthorityV1Error("window constant references are missing")
    values: dict[str, object] = {
        "source_step_threshold": signature.get("source_threshold_reference"),
        "source_stability_tolerance": signature.get("source_stability_reference"),
        "target_noise_scale": signature.get("target_scale_reference"),
        **{role: windows.get(role) for role in UTILITY_NUMERIC_ROLES[3:]},
    }
    if set(values) != set(UTILITY_NUMERIC_ROLES):
        raise NormalOnlyAuthorityV1Error("utility reference roles differ")
    return tuple((role, _sha(values[role], role)) for role in UTILITY_NUMERIC_ROLES)


def build_common42_authority_v1(
    executable_equivalence: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
) -> NormalOnlyAuthorityDefinitionV1:
    """Independently derive the exact 42/420 authority from committed metadata."""

    _verify_self_hash(executable_equivalence, EXECUTABLE_EQUIVALENCE_HASH, "executable equivalence")
    _verify_self_hash(evidence_manifest, E1_PUBLIC_MANIFEST_HASH, "E1 public manifest")
    records = executable_equivalence.get("relation_records")
    entries = evidence_manifest.get("entries")
    if not isinstance(records, list) or len(records) != COMMON_RELATION_COUNT:
        raise NormalOnlyAuthorityV1Error("COMMON relation count is not exactly 42")
    if not isinstance(entries, list) or len(entries) != COMMON_RELATION_COUNT:
        raise NormalOnlyAuthorityV1Error("E1 manifest relation count is not exactly 42")
    if (
        executable_equivalence.get("relation_equivalence_class_count") != COMMON_RELATION_COUNT
        or executable_equivalence.get("T0_T1_T1B_equivalent_relation_count") != COMMON_RELATION_COUNT
        or evidence_manifest.get("relation_count") != COMMON_RELATION_COUNT
        or evidence_manifest.get("numeric_binding_count") != 462
    ):
        raise NormalOnlyAuthorityV1Error("COMMON/E1 cardinality authority differs")

    by_binding: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise NormalOnlyAuthorityV1Error("manifest entry must be an object")
        binding = _sha(entry.get("relation_binding_hash"), "manifest relation binding")
        if binding in by_binding:
            raise NormalOnlyAuthorityV1Error("duplicate manifest relation binding")
        by_binding[binding] = entry

    relations: list[CommonRelationAuthorityV1] = []
    historical_utility_references: list[str] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise NormalOnlyAuthorityV1Error("equivalence relation record must be an object")
        binding = _sha(record.get("relation_binding_hash"), "relation binding")
        semantic = _sha(record.get("semantic_execution_hash"), "semantic execution hash")
        signature = record.get("executable_signature")
        if not isinstance(signature, Mapping) or stable_hash_v1(signature) != semantic:
            raise NormalOnlyAuthorityV1Error("semantic execution preimage differs")
        if tuple(record.get("common_arm_cells", ())) != ("T0", "T1", "T1-B"):
            raise NormalOnlyAuthorityV1Error("COMMON arm membership differs")
        entry = by_binding.get(binding)
        if entry is None:
            raise NormalOnlyAuthorityV1Error("COMMON relation has no E1 manifest entry")
        role_rows = entry.get("numeric_references")
        if not isinstance(role_rows, list) or len(role_rows) != 11:
            raise NormalOnlyAuthorityV1Error("historical manifest numeric references differ")
        manifest_refs: dict[str, str] = {}
        for row in role_rows:
            if not isinstance(row, Mapping) or row.get("numeric_role") not in HISTORICAL_MANIFEST_ROLES:
                raise NormalOnlyAuthorityV1Error("manifest numeric role differs")
            role = str(row["numeric_role"])
            if role in manifest_refs:
                raise NormalOnlyAuthorityV1Error("duplicate historical numeric role")
            manifest_refs[role] = _sha(row.get("numeric_reference"), "historical numeric reference")
        if set(manifest_refs) != set(HISTORICAL_MANIFEST_ROLES):
            raise NormalOnlyAuthorityV1Error("historical numeric role set differs")
        reference_pairs = _signature_reference_pairs(signature)
        for role, reference in reference_pairs:
            if manifest_refs[role] != reference:
                raise NormalOnlyAuthorityV1Error("executable and manifest numeric references differ")
            historical_utility_references.append(reference)
        horizon = _strict_int(signature.get("selected_delay_horizon_seconds"), "selected horizon", minimum=1)
        expected_fields = {
            "source": signature.get("source"),
            "target": signature.get("target"),
            "source_step_direction": signature.get("source_step_direction"),
            "target_response_direction": signature.get("target_response_direction"),
            "selected_horizon_seconds": horizon,
        }
        if any(entry.get(key) != value for key, value in expected_fields.items()):
            raise NormalOnlyAuthorityV1Error("COMMON and E1 relation semantics differ")
        relation = CommonRelationAuthorityV1(
            relation_identity=str(entry.get("relation_identity")),
            relation_binding_hash=binding,
            semantic_execution_hash=semantic,
            source=str(signature.get("source")),
            target=str(signature.get("target")),
            source_direction=str(signature.get("source_step_direction")),
            target_direction=str(signature.get("target_response_direction")),
            selected_horizon_seconds=horizon,
            historical_reference_pairs=reference_pairs,
        )
        if not relation.relation_identity.startswith("directional_relation:"):
            raise NormalOnlyAuthorityV1Error("relation identity differs")
        if relation.source_direction not in {"step_up", "step_down"}:
            raise NormalOnlyAuthorityV1Error("source direction differs")
        if relation.target_direction not in {"increase", "decrease"}:
            raise NormalOnlyAuthorityV1Error("target direction differs")
        relations.append(relation)

    ordered = tuple(sorted(relations, key=lambda item: item.relation_binding_hash))
    for field in ("relation_identity", "relation_binding_hash", "semantic_execution_hash"):
        values = [getattr(item, field) for item in ordered]
        if len(values) != len(set(values)):
            raise NormalOnlyAuthorityV1Error(f"duplicate COMMON {field}")
    if len(historical_utility_references) != UTILITY_NUMERIC_REFERENCE_COUNT:
        raise NormalOnlyAuthorityV1Error("utility-required historical binding count is not 420")
    if len(set(historical_utility_references)) != UTILITY_NUMERIC_REFERENCE_COUNT:
        raise NormalOnlyAuthorityV1Error("utility-required historical references are not unique")

    new_references = tuple(
        new_reference_identity_v1(relation, role)
        for relation in ordered
        for role in UTILITY_NUMERIC_ROLES
    )
    if len(new_references) != UTILITY_NUMERIC_REFERENCE_COUNT or len(set(new_references)) != len(new_references):
        raise NormalOnlyAuthorityV1Error("new reference system is not exactly 420 unique identities")
    binding_set_hash = stable_hash_v1(
        {
            "historical_utility_reference_bindings": sorted(historical_utility_references),
            "count": UTILITY_NUMERIC_REFERENCE_COUNT,
        }
    )
    definition_hash = stable_hash_v1(
        {
            "authority_version": AUTHORITY_VERSION,
            "authority_lineage": AUTHORITY_LINEAGE,
            "common42_authority_hash": COMMON42_AUTHORITY_CHECK_HASH,
            "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
            "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
            "calibration_policy_version": CALIBRATION_POLICY_VERSION,
            "relations": [item.to_identity_dict() for item in ordered],
            "new_reference_identities": list(new_references),
        }
    )
    return NormalOnlyAuthorityDefinitionV1(ordered, new_references, binding_set_hash, definition_hash)


def _strict_float_sequence(values: Sequence[float], name: str) -> tuple[float, ...]:
    if not isinstance(values, tuple) or len(values) < 2:
        raise NormalOnlyAuthorityV1Error(f"{name} must be a tuple with at least two values")
    if any(type(value) is not float or not math.isfinite(value) for value in values):
        raise NormalOnlyAuthorityV1Error(f"{name} must contain only finite float objects")
    return values


def derive_source_parameters_normal_only_v1(
    train1_values: Sequence[float], train2_values: Sequence[float]
) -> tuple[float, float]:
    """Apply the frozen multi-file source calibration without reinterpretation."""

    files = (
        _strict_float_sequence(train1_values, "train1 source values"),
        _strict_float_sequence(train2_values, "train2 source values"),
    )
    result = derive_multi_file_source_parameters_v1(files)
    threshold = result.get("source_step_threshold")
    tolerance = result.get("source_stability_tolerance")
    if result.get("status") != "supported" or type(threshold) is not float or type(tolerance) is not float:
        raise NormalOnlyAuthorityV1Error("source lacks frozen supported calibration")
    if not math.isfinite(threshold) or threshold <= 0 or not math.isfinite(tolerance) or tolerance < 0:
        raise NormalOnlyAuthorityV1Error("source calibration is outside its numeric domain")
    return threshold, tolerance


def derive_target_scale_normal_only_v1(
    train1_values: Sequence[float], train2_values: Sequence[float]
) -> float:
    """Apply the frozen multi-file target scale without reinterpretation."""

    files = (
        _strict_float_sequence(train1_values, "train1 target values"),
        _strict_float_sequence(train2_values, "train2 target values"),
    )
    value = derive_multi_file_target_scale_v1(files)
    if type(value) is not float or not math.isfinite(value) or value <= 0:
        raise NormalOnlyAuthorityV1Error("target scale is outside its numeric domain")
    return value


def _frozen_window_values() -> dict[str, int | float]:
    values = PreregisteredWindowConstantBundleV1().to_dict()
    result = {role: values[role] for role in UTILITY_NUMERIC_ROLES[3:]}
    expected: dict[str, int | float] = {
        "source_pre_window_seconds": 5,
        "source_post_window_seconds": 5,
        "minimum_source_stability_fraction": 0.8,
        "source_refractory_seconds": 10,
        "cross_source_isolation_radius_seconds": 2,
        "target_baseline_window_seconds": 5,
        "target_response_window_seconds": 3,
    }
    if result != expected:
        raise NormalOnlyAuthorityV1Error("frozen window constants differ")
    return result


def _provenance_identity(relation: CommonRelationAuthorityV1, role: str) -> str:
    if role in {"source_step_threshold", "source_stability_tolerance"}:
        dependency = {"source": relation.source}
    elif role == "target_noise_scale":
        dependency = {"target": relation.target}
    else:
        dependency = {"frozen_constant_role": role}
    return stable_hash_v1(
        {
            "authority_version": AUTHORITY_VERSION,
            "calibration_policy_version": CALIBRATION_POLICY_VERSION,
            "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
            "numeric_role": role,
            "dependency": dependency,
        }
    )


def _validate_role_value(role: str, value: object) -> int | float:
    windows = _frozen_window_values()
    if role in windows:
        expected = windows[role]
        if type(value) is not type(expected) or value != expected:
            raise NormalOnlyAuthorityV1Error(f"{role} differs from the frozen constant")
        return value
    if type(value) is not float or not math.isfinite(value):
        raise NormalOnlyAuthorityV1Error(f"{role} must be a finite float object")
    if role in {"source_step_threshold", "target_noise_scale"} and value <= 0:
        raise NormalOnlyAuthorityV1Error(f"{role} must be positive")
    if role == "source_stability_tolerance" and value < 0:
        raise NormalOnlyAuthorityV1Error("source_stability_tolerance must be nonnegative")
    if role not in UTILITY_NUMERIC_ROLES:
        raise NormalOnlyAuthorityV1Error("numeric role is unexpected")
    return value


def calibrate_all_role_values_v1(
    authority: NormalOnlyAuthorityDefinitionV1,
    train1_features: Mapping[str, Sequence[float]],
    train2_features: Mapping[str, Sequence[float]],
) -> dict[tuple[str, str], int | float]:
    """Compute all 420 values from exact COMMON identities and normal inputs."""

    required_features = {item.source for item in authority.relations} | {item.target for item in authority.relations}
    if set(train1_features) != required_features or set(train2_features) != required_features:
        raise NormalOnlyAuthorityV1Error("normal feature set differs from exact COMMON requirements")
    sources = sorted({item.source for item in authority.relations})
    targets = sorted({item.target for item in authority.relations})
    source_values = {
        source: derive_source_parameters_normal_only_v1(
            train1_features[source], train2_features[source]
        )
        for source in sources
    }
    target_values = {
        target: derive_target_scale_normal_only_v1(
            train1_features[target], train2_features[target]
        )
        for target in targets
    }
    windows = _frozen_window_values()
    result: dict[tuple[str, str], int | float] = {}
    for relation in authority.relations:
        for role in UTILITY_NUMERIC_ROLES:
            if role == "source_step_threshold":
                value: object = source_values[relation.source][0]
            elif role == "source_stability_tolerance":
                value = source_values[relation.source][1]
            elif role == "target_noise_scale":
                value = target_values[relation.target]
            else:
                value = windows[role]
            result[(relation.relation_binding_hash, role)] = _validate_role_value(role, value)
    if len(result) != UTILITY_NUMERIC_REFERENCE_COUNT:
        raise NormalOnlyAuthorityV1Error("calibration did not produce exactly 420 logical values")
    return result


def build_private_registry_document_v1(
    authority: NormalOnlyAuthorityDefinitionV1,
    role_values: Mapping[tuple[str, str], object],
) -> dict[str, Any]:
    """Build a complete private registry document; performs no filesystem I/O."""

    expected_keys = {
        (relation.relation_binding_hash, role)
        for relation in authority.relations
        for role in UTILITY_NUMERIC_ROLES
    }
    if set(role_values) != expected_keys:
        raise NormalOnlyAuthorityV1Error("registry values have missing or unexpected logical keys")
    records: list[dict[str, Any]] = []
    for relation in authority.relations:
        for role in UTILITY_NUMERIC_ROLES:
            value = _validate_role_value(role, role_values[(relation.relation_binding_hash, role)])
            new_reference = new_reference_identity_v1(relation, role)
            if new_reference in {
                relation.historical_reference(role),
                HISTORICAL_E1_HASH,
                HISTORICAL_NUMERIC_REGISTRY_HASH,
            }:
                raise NormalOnlyAuthorityV1Error("historical authority identity was reused")
            payload: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "authority_version": AUTHORITY_VERSION,
                "relation_identity": relation.relation_identity,
                "relation_binding_hash": relation.relation_binding_hash,
                "semantic_execution_hash": relation.semantic_execution_hash,
                "numeric_role": role,
                "new_reference_identity": new_reference,
                "numeric_value": value,
                "calibration_policy_version": CALIBRATION_POLICY_VERSION,
                "normal_train1_identity": NORMAL_TRAIN1_IDENTITY.sha256,
                "normal_train2_identity": NORMAL_TRAIN2_IDENTITY.sha256,
                "provenance_identity": _provenance_identity(relation, role),
            }
            payload["record_hash"] = stable_hash_v1(payload)
            records.append(payload)
    document: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_utility_normal_only_private_registry_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "authority_lineage": AUTHORITY_LINEAGE,
        "historical_e1_identity_restored": False,
        "historical_numeric_identity_restored": False,
        "construction_result_validity": "UNCHANGED",
        "terminal_custody_validity": "UNCHANGED",
        "common42_authority_hash": COMMON42_AUTHORITY_CHECK_HASH,
        "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "authority_definition_hash": authority.authority_definition_hash,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "relation_count": COMMON_RELATION_COUNT,
        "record_count": UTILITY_NUMERIC_REFERENCE_COUNT,
        "unique_logical_key_count": UTILITY_NUMERIC_REFERENCE_COUNT,
        "status": "complete_private_registry_pending_public_receipt",
        "records": records,
    }
    document["artifact_hash"] = stable_hash_v1(document)
    validate_private_registry_document_v1(document, authority)
    return document


def validate_private_registry_document_v1(
    document: Mapping[str, Any], authority: NormalOnlyAuthorityDefinitionV1
) -> str:
    observed = document.get("artifact_hash")
    _sha(observed, "private registry hash")
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    if stable_hash_v1(payload) != observed:
        raise NormalOnlyAuthorityV1Error("private registry self-hash differs")
    exact = {
        "artifact_type": "task039e3_r2r_utility_normal_only_private_registry_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "authority_lineage": AUTHORITY_LINEAGE,
        "historical_e1_identity_restored": False,
        "historical_numeric_identity_restored": False,
        "construction_result_validity": "UNCHANGED",
        "terminal_custody_validity": "UNCHANGED",
        "common42_authority_hash": COMMON42_AUTHORITY_CHECK_HASH,
        "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "authority_definition_hash": authority.authority_definition_hash,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "relation_count": COMMON_RELATION_COUNT,
        "record_count": UTILITY_NUMERIC_REFERENCE_COUNT,
        "unique_logical_key_count": UTILITY_NUMERIC_REFERENCE_COUNT,
        "status": "complete_private_registry_pending_public_receipt",
    }
    if any(document.get(key) != value for key, value in exact.items()):
        raise NormalOnlyAuthorityV1Error("private registry authority header differs")
    records = document.get("records")
    if not isinstance(records, list) or len(records) != UTILITY_NUMERIC_REFERENCE_COUNT:
        raise NormalOnlyAuthorityV1Error("private registry must contain exactly 420 records")
    relations = {item.relation_binding_hash: item for item in authority.relations}
    keys: set[tuple[str, str]] = set()
    references: set[str] = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise NormalOnlyAuthorityV1Error("private registry record must be an object")
        record_hash = _sha(record.get("record_hash"), "record hash")
        if stable_hash_v1({key: value for key, value in record.items() if key != "record_hash"}) != record_hash:
            raise NormalOnlyAuthorityV1Error("private registry record hash differs")
        binding = _sha(record.get("relation_binding_hash"), "record relation binding")
        relation = relations.get(binding)
        role = record.get("numeric_role")
        if relation is None or role not in UTILITY_NUMERIC_ROLES:
            raise NormalOnlyAuthorityV1Error("registry record relation or role is unexpected")
        key = (binding, str(role))
        if key in keys:
            raise NormalOnlyAuthorityV1Error("duplicate registry logical key")
        keys.add(key)
        expected_reference = new_reference_identity_v1(relation, str(role))
        if record.get("new_reference_identity") != expected_reference or expected_reference in references:
            raise NormalOnlyAuthorityV1Error("registry reference identity differs or duplicates")
        references.add(expected_reference)
        if (
            record.get("schema_version") != SCHEMA_VERSION
            or record.get("authority_version") != AUTHORITY_VERSION
            or record.get("relation_identity") != relation.relation_identity
            or record.get("semantic_execution_hash") != relation.semantic_execution_hash
            or record.get("calibration_policy_version") != CALIBRATION_POLICY_VERSION
            or record.get("normal_train1_identity") != NORMAL_TRAIN1_IDENTITY.sha256
            or record.get("normal_train2_identity") != NORMAL_TRAIN2_IDENTITY.sha256
            or record.get("provenance_identity") != _provenance_identity(relation, str(role))
        ):
            raise NormalOnlyAuthorityV1Error("registry record authority binding differs")
        _validate_role_value(str(role), record.get("numeric_value"))
    expected_keys = {
        (relation.relation_binding_hash, role)
        for relation in authority.relations
        for role in UTILITY_NUMERIC_ROLES
    }
    if keys != expected_keys or len(references) != UTILITY_NUMERIC_REFERENCE_COUNT:
        raise NormalOnlyAuthorityV1Error("registry logical-key closure differs")
    return str(observed)


def public_receipt_document_v1(
    *,
    authority: NormalOnlyAuthorityDefinitionV1,
    private_registry_hash: str,
    builder_commit: str,
    builder_git_blob: str,
    builder_source_sha256: str,
    execution_timestamp: str,
) -> dict[str, Any]:
    _sha(private_registry_hash, "private registry hash")
    _commit(builder_commit, "builder commit")
    _git_oid(builder_git_blob, "builder Git blob")
    _sha(builder_source_sha256, "builder source SHA-256")
    _timezone_aware(execution_timestamp, "execution timestamp")
    document: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_utility_normal_only_public_receipt_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "authority_lineage": AUTHORITY_LINEAGE,
        "historical_e1_identity_restored": False,
        "historical_numeric_identity_restored": False,
        "private_registry_content_hash": private_registry_hash,
        "record_count": UTILITY_NUMERIC_REFERENCE_COUNT,
        "unique_key_count": UTILITY_NUMERIC_REFERENCE_COUNT,
        "relation_count": COMMON_RELATION_COUNT,
        "common42_authority_hash": COMMON42_AUTHORITY_CHECK_HASH,
        "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "authority_definition_hash": authority.authority_definition_hash,
        "normal_input_identities": [item.to_dict() for item in NORMAL_INPUT_IDENTITIES],
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "builder_commit": builder_commit,
        "builder_git_blob": builder_git_blob,
        "builder_source_sha256": builder_source_sha256,
        "execution_timestamp": execution_timestamp,
        "validation_counts": {
            "records": UTILITY_NUMERIC_REFERENCE_COUNT,
            "unique_keys": UTILITY_NUMERIC_REFERENCE_COUNT,
            "missing": 0,
            "duplicates": 0,
            "unexpected": 0,
            "nonfinite": 0,
        },
        "construction_provenance": {
            "successful_execution_receipt": SUCCESS_EXECUTION_RECEIPT,
            "successful_execution_accounting": SUCCESS_EXECUTION_ACCOUNTING,
            "terminal_custody_supplement": TERMINAL_CUSTODY_SUPPLEMENT,
            "terminal_audit_a": TERMINAL_AUDIT_A,
            "terminal_audit_b": TERMINAL_AUDIT_B,
            "scientific_result_evaluable": True,
        },
        "t2_utility_scope_authorized": False,
        "public_receipt_written_last": True,
    }
    document["artifact_hash"] = stable_hash_v1(document)
    validate_public_receipt_v1(document, authority)
    return document


def _contains_forbidden_public_key(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = key.lower()
            if "numeric_value" in lowered or "private_path" in lowered or "absolute_path" in lowered:
                return True
            if _contains_forbidden_public_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_public_key(child) for child in value)
    return False


def _contains_absolute_path_value(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_absolute_path_value(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_absolute_path_value(child) for child in value)
    if isinstance(value, str):
        return Path(value).is_absolute()
    return False


def validate_public_receipt_v1(
    document: Mapping[str, Any], authority: NormalOnlyAuthorityDefinitionV1
) -> str:
    observed = _sha(document.get("artifact_hash"), "public receipt hash")
    if stable_hash_v1({key: value for key, value in document.items() if key != "artifact_hash"}) != observed:
        raise NormalOnlyAuthorityV1Error("public receipt self-hash differs")
    if _contains_forbidden_public_key(document) or _contains_absolute_path_value(document):
        raise NormalOnlyAuthorityV1Error("public receipt exposes a forbidden field")
    if (
        document.get("artifact_type") != "task039e3_r2r_utility_normal_only_public_receipt_v1"
        or document.get("schema_version") != SCHEMA_VERSION
        or document.get("authority_version") != AUTHORITY_VERSION
        or document.get("authority_lineage") != AUTHORITY_LINEAGE
        or document.get("historical_e1_identity_restored") is not False
        or document.get("historical_numeric_identity_restored") is not False
        or document.get("record_count") != UTILITY_NUMERIC_REFERENCE_COUNT
        or document.get("unique_key_count") != UTILITY_NUMERIC_REFERENCE_COUNT
        or document.get("relation_count") != COMMON_RELATION_COUNT
        or document.get("common42_authority_hash") != COMMON42_AUTHORITY_CHECK_HASH
        or document.get("executable_equivalence_hash") != EXECUTABLE_EQUIVALENCE_HASH
        or document.get("authority_definition_hash") != authority.authority_definition_hash
        or document.get("normal_input_identity_set_hash") != NORMAL_INPUT_IDENTITY_SET_HASH
        or document.get("normal_input_identities") != [item.to_dict() for item in NORMAL_INPUT_IDENTITIES]
        or document.get("calibration_policy_version") != CALIBRATION_POLICY_VERSION
        or document.get("calibration_policy_hash") != CALIBRATION_POLICY_HASH
        or document.get("t2_utility_scope_authorized") is not False
        or document.get("public_receipt_written_last") is not True
    ):
        raise NormalOnlyAuthorityV1Error("public receipt authority differs")
    expected_counts = {
        "records": UTILITY_NUMERIC_REFERENCE_COUNT,
        "unique_keys": UTILITY_NUMERIC_REFERENCE_COUNT,
        "missing": 0,
        "duplicates": 0,
        "unexpected": 0,
        "nonfinite": 0,
    }
    expected_provenance = {
        "successful_execution_receipt": SUCCESS_EXECUTION_RECEIPT,
        "successful_execution_accounting": SUCCESS_EXECUTION_ACCOUNTING,
        "terminal_custody_supplement": TERMINAL_CUSTODY_SUPPLEMENT,
        "terminal_audit_a": TERMINAL_AUDIT_A,
        "terminal_audit_b": TERMINAL_AUDIT_B,
        "scientific_result_evaluable": True,
    }
    if document.get("validation_counts") != expected_counts or document.get("construction_provenance") != expected_provenance:
        raise NormalOnlyAuthorityV1Error("public receipt validation or construction provenance differs")
    _sha(document.get("private_registry_content_hash"), "private registry content hash")
    _commit(document.get("builder_commit"), "builder commit")
    _git_oid(document.get("builder_git_blob"), "builder Git blob")
    _sha(document.get("builder_source_sha256"), "builder source SHA-256")
    _timezone_aware(document.get("execution_timestamp"), "execution timestamp")
    return observed


def local_locator_manifest_document_v1(
    *,
    private_authority_path: Path,
    private_authority_hash: str,
    public_receipt_hash: str,
    created_at: str,
    builder_commit: str,
) -> dict[str, Any]:
    path = private_authority_path.resolve(strict=False)
    if not path.is_absolute():
        raise NormalOnlyAuthorityV1Error("private authority locator must be absolute")
    _sha(private_authority_hash, "private authority hash")
    _sha(public_receipt_hash, "public receipt hash")
    _timezone_aware(created_at, "locator creation time")
    _commit(builder_commit, "builder commit")
    document: dict[str, Any] = {
        "artifact_type": "task039e3_r2r_utility_normal_only_local_locator_manifest_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "absolute_private_authority_path": str(path),
        "private_authority_hash": private_authority_hash,
        "public_receipt_hash": public_receipt_hash,
        "created_at": created_at,
        "builder_commit": builder_commit,
        "local_only": True,
        "must_not_be_committed": True,
    }
    document["artifact_hash"] = stable_hash_v1(document)
    return document


def validate_local_locator_manifest_v1(
    document: Mapping[str, Any], *, repository_root: Path
) -> str:
    observed = _sha(document.get("artifact_hash"), "locator manifest hash")
    if stable_hash_v1({key: value for key, value in document.items() if key != "artifact_hash"}) != observed:
        raise NormalOnlyAuthorityV1Error("locator manifest self-hash differs")
    if (
        document.get("artifact_type") != "task039e3_r2r_utility_normal_only_local_locator_manifest_v1"
        or document.get("schema_version") != SCHEMA_VERSION
        or document.get("authority_version") != AUTHORITY_VERSION
        or document.get("local_only") is not True
        or document.get("must_not_be_committed") is not True
    ):
        raise NormalOnlyAuthorityV1Error("locator manifest policy differs")
    path = Path(str(document.get("absolute_private_authority_path", "")))
    _require_outside_repository(path, repository_root, "private authority")
    _sha(document.get("private_authority_hash"), "private authority hash")
    _sha(document.get("public_receipt_hash"), "public receipt hash")
    _timezone_aware(document.get("created_at"), "locator creation time")
    _commit(document.get("builder_commit"), "builder commit")
    return observed


def _timezone_aware(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise NormalOnlyAuthorityV1Error(f"{name} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise NormalOnlyAuthorityV1Error(f"{name} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise NormalOnlyAuthorityV1Error(f"{name} must be timezone-aware")
    return value


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def verify_normal_input_file_v1(path: Path, expected: NormalInputIdentityV1) -> None:
    """Verify exact bytes before a future caller is allowed to parse values."""

    observed = path.resolve(strict=True)
    if path.is_symlink() or not observed.is_file():
        raise NormalOnlyAuthorityV1Error("normal input must be a regular non-symlink file")
    if observed.name != Path(expected.relative_path).name:
        raise NormalOnlyAuthorityV1Error("normal input filename differs")
    if observed.stat().st_size != expected.byte_size:
        raise NormalOnlyAuthorityV1Error("normal input byte size differs before value use")
    if _file_sha256(observed) != expected.sha256:
        raise NormalOnlyAuthorityV1Error("normal input hash differs before value use")


def _read_verified_feature_columns(
    path: Path, required_features: frozenset[str], expected_rows: int
) -> dict[str, tuple[float, ...]]:
    columns = {feature: [] for feature in sorted(required_features)}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames
        if header is None or len(header) != len(set(header)) or not required_features.issubset(header):
            raise NormalOnlyAuthorityV1Error("normal input header lacks exact required features")
        for row in reader:
            for feature in columns:
                token = row.get(feature)
                if not isinstance(token, str):
                    raise NormalOnlyAuthorityV1Error("normal feature token is missing")
                try:
                    value = float(token)
                except ValueError as exc:
                    raise NormalOnlyAuthorityV1Error("normal feature token is not numeric") from exc
                if not math.isfinite(value):
                    raise NormalOnlyAuthorityV1Error("normal feature token is nonfinite")
                columns[feature].append(value)
    if any(len(values) != expected_rows for values in columns.values()):
        raise NormalOnlyAuthorityV1Error("normal input row count differs")
    return {feature: tuple(values) for feature, values in columns.items()}


def load_verified_normal_features_v1(
    *, train1_path: Path, train2_path: Path, required_features: frozenset[str]
) -> tuple[dict[str, tuple[float, ...]], dict[str, tuple[float, ...]]]:
    """Future-only loader: both exact byte identities pass before CSV value parsing."""

    if not required_features or any(not isinstance(item, str) or not item for item in required_features):
        raise NormalOnlyAuthorityV1Error("required feature set is malformed")
    verify_normal_input_file_v1(train1_path, NORMAL_TRAIN1_IDENTITY)
    verify_normal_input_file_v1(train2_path, NORMAL_TRAIN2_IDENTITY)
    train1 = _read_verified_feature_columns(
        train1_path, required_features, NORMAL_TRAIN1_IDENTITY.row_count
    )
    train2 = _read_verified_feature_columns(
        train2_path, required_features, NORMAL_TRAIN2_IDENTITY.row_count
    )
    # Close the hash-then-read race: exact identities must still hold after parsing.
    verify_normal_input_file_v1(train1_path, NORMAL_TRAIN1_IDENTITY)
    verify_normal_input_file_v1(train2_path, NORMAL_TRAIN2_IDENTITY)
    return train1, train2


def _require_outside_repository(path: Path, repository_root: Path, name: str) -> Path:
    resolved = path.resolve(strict=False)
    root = repository_root.resolve(strict=True)
    if not resolved.is_absolute() or resolved == root or root in resolved.parents:
        raise NormalOnlyAuthorityV1Error(f"{name} must be outside Git")
    return resolved


def _atomic_json_write(path: Path, document: Mapping[str, Any], *, private: bool) -> None:
    if path.exists():
        raise NormalOnlyAuthorityV1Error("authoritative output already exists")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise NormalOnlyAuthorityV1Error("authoritative output parent is invalid")
    temporary = path.with_name(f".{path.name}.partial-{uuid4().hex}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json_v1(dict(document)))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if private:
            try:
                temporary.chmod(0o600)
            except OSError:
                pass
        with temporary.open("r", encoding="utf-8") as stream:
            if json.load(stream) != document:
                raise NormalOnlyAuthorityV1Error("temporary output round-trip differs")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class AtomicMaterializationResultV1:
    private_registry_hash: str
    local_locator_manifest_hash: str
    public_receipt_hash: str
    write_order: tuple[str, ...]


def finalize_materialization_atomically_v1(
    *,
    registry: Mapping[str, Any],
    authority: NormalOnlyAuthorityDefinitionV1,
    private_destination: Path,
    local_locator_manifest: Path,
    public_receipt_path: Path,
    repository_root: Path,
    builder_commit: str,
    builder_git_blob: str,
    builder_source_sha256: str,
    execution_timestamp: str,
) -> AtomicMaterializationResultV1:
    """Finalize private authority, local locator, then public receipt last."""

    registry_hash = validate_private_registry_document_v1(registry, authority)
    destination = _require_outside_repository(private_destination, repository_root, "private destination")
    locator_path = _require_outside_repository(local_locator_manifest, repository_root, "local locator manifest")
    configured = os.environ.get(PRIVATE_LOCATOR_ENV)
    if not configured or Path(configured).resolve(strict=False) != destination:
        raise NormalOnlyAuthorityV1Error("explicit private authority environment locator differs")
    if destination == locator_path or public_receipt_path.resolve(strict=False) in {destination, locator_path}:
        raise NormalOnlyAuthorityV1Error("materialization outputs must be distinct")
    receipt = public_receipt_document_v1(
        authority=authority,
        private_registry_hash=registry_hash,
        builder_commit=builder_commit,
        builder_git_blob=builder_git_blob,
        builder_source_sha256=builder_source_sha256,
        execution_timestamp=execution_timestamp,
    )
    receipt_hash = str(receipt["artifact_hash"])
    locator = local_locator_manifest_document_v1(
        private_authority_path=destination,
        private_authority_hash=registry_hash,
        public_receipt_hash=receipt_hash,
        created_at=execution_timestamp,
        builder_commit=builder_commit,
    )
    validate_local_locator_manifest_v1(locator, repository_root=repository_root)

    _atomic_json_write(destination, registry, private=True)
    with destination.open("r", encoding="utf-8") as stream:
        validate_private_registry_document_v1(json.load(stream), authority)
    _atomic_json_write(locator_path, locator, private=True)
    with locator_path.open("r", encoding="utf-8") as stream:
        validate_local_locator_manifest_v1(json.load(stream), repository_root=repository_root)
    with destination.open("r", encoding="utf-8") as stream:
        reopened_hash = validate_private_registry_document_v1(json.load(stream), authority)
    if reopened_hash != registry_hash or _file_sha256(destination) == HISTORICAL_NUMERIC_REGISTRY_HASH:
        raise NormalOnlyAuthorityV1Error("final private authority verification differs")
    _atomic_json_write(public_receipt_path.resolve(strict=False), receipt, private=False)
    with public_receipt_path.open("r", encoding="utf-8") as stream:
        validate_public_receipt_v1(json.load(stream), authority)
    return AtomicMaterializationResultV1(
        private_registry_hash=registry_hash,
        local_locator_manifest_hash=str(locator["artifact_hash"]),
        public_receipt_hash=receipt_hash,
        write_order=(
            "private_registry_atomic_rename",
            "local_locator_manifest_written_and_validated",
            "private_registry_reopened_and_rehashed",
            "public_receipt_written_last",
        ),
    )


def validate_finalized_authority_v1(
    *,
    authority: NormalOnlyAuthorityDefinitionV1,
    private_destination: Path,
    local_locator_manifest: Path,
    public_receipt_path: Path,
    repository_root: Path,
) -> str:
    """Accept only the exact final path plus locator plus write-last receipt."""

    configured = os.environ.get(PRIVATE_LOCATOR_ENV)
    destination = private_destination.resolve(strict=True)
    if not configured or Path(configured).resolve(strict=False) != destination:
        raise NormalOnlyAuthorityV1Error("authoritative private locator differs")
    if ".partial-" in destination.name:
        raise NormalOnlyAuthorityV1Error("partial private output is never authoritative")
    with destination.open("r", encoding="utf-8") as stream:
        registry_hash = validate_private_registry_document_v1(json.load(stream), authority)
    with local_locator_manifest.open("r", encoding="utf-8") as stream:
        locator = json.load(stream)
    validate_local_locator_manifest_v1(locator, repository_root=repository_root)
    with public_receipt_path.open("r", encoding="utf-8") as stream:
        receipt = json.load(stream)
    validate_public_receipt_v1(receipt, authority)
    if (
        Path(locator["absolute_private_authority_path"]).resolve(strict=False) != destination
        or locator["private_authority_hash"] != registry_hash
        or locator["public_receipt_hash"] != receipt["artifact_hash"]
        or receipt["private_registry_content_hash"] != registry_hash
    ):
        raise NormalOnlyAuthorityV1Error("final private/public/locator custody differs")
    return registry_hash


def verify_builder_checkout_v1(
    repository_root: Path, *, expected_builder_commit: str
) -> tuple[str, str]:
    """Future preflight for the exact clean builder commit and source blob."""

    _commit(expected_builder_commit, "expected builder commit")
    relative = "src/paperworks/v6/task039e3_r2r_utility_normal_only_authority_v1.py"
    commands = (
        ("rev-parse", "HEAD"),
        ("rev-parse", f"HEAD:{relative}"),
        ("status", "--porcelain", "--", relative),
    )
    outputs: list[str] = []
    for args in commands:
        completed = subprocess.run(
            ["git", "-C", str(repository_root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        outputs.append(completed.stdout.strip())
    if outputs[0] != expected_builder_commit or outputs[2]:
        raise NormalOnlyAuthorityV1Error("builder checkout is not exact and clean")
    return _git_oid(outputs[1], "builder source Git blob"), _file_sha256(repository_root / relative)


def materialize_normal_only_authority_v1(
    *,
    feasibility_audit: Mapping[str, Any],
    dependency_matrix: Mapping[str, Any],
    common42_check: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    d1_data_access_audit: Mapping[str, Any],
    executable_equivalence: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
    train1_path: Path,
    train2_path: Path,
    private_destination: Path,
    local_locator_manifest: Path,
    public_receipt_path: Path,
    repository_root: Path,
    expected_builder_commit: str,
    execution_timestamp: str,
) -> AtomicMaterializationResultV1:
    """Future explicit real materializer; this task freezes but never calls it."""

    validate_route_c_bindings_v1(feasibility_audit, dependency_matrix, common42_check)
    validate_normal_input_authorities_v1(dataset_manifest, d1_data_access_audit)
    authority = build_common42_authority_v1(executable_equivalence, evidence_manifest)
    builder_git_blob, builder_source_sha256 = verify_builder_checkout_v1(
        repository_root, expected_builder_commit=expected_builder_commit
    )
    required_features = frozenset(
        {item.source for item in authority.relations}
        | {item.target for item in authority.relations}
    )
    train1, train2 = load_verified_normal_features_v1(
        train1_path=train1_path,
        train2_path=train2_path,
        required_features=required_features,
    )
    values = calibrate_all_role_values_v1(authority, train1, train2)
    registry = build_private_registry_document_v1(authority, values)
    return finalize_materialization_atomically_v1(
        registry=registry,
        authority=authority,
        private_destination=private_destination,
        local_locator_manifest=local_locator_manifest,
        public_receipt_path=public_receipt_path,
        repository_root=repository_root,
        builder_commit=expected_builder_commit,
        builder_git_blob=builder_git_blob,
        builder_source_sha256=builder_source_sha256,
        execution_timestamp=execution_timestamp,
    )


def _load_json_document(path: Path, name: str) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise NormalOnlyAuthorityV1Error(f"{name} must be a regular JSON file")
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise NormalOnlyAuthorityV1Error(f"{name} must contain an object")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    """Explicit, no-default future command for authorized materialization."""

    parser = argparse.ArgumentParser(description=TASK_ID)
    for option in (
        "feasibility-audit",
        "dependency-matrix",
        "common42-check",
        "dataset-manifest",
        "d1-data-access-audit",
        "executable-equivalence",
        "evidence-manifest",
        "train1",
        "train2",
        "private-destination",
        "local-locator-manifest",
        "public-receipt",
        "repository-root",
    ):
        parser.add_argument(f"--{option}", type=Path, required=True)
    parser.add_argument("--expected-builder-commit", required=True)
    parser.add_argument("--execution-timestamp", required=True)
    args = parser.parse_args(argv)
    result = materialize_normal_only_authority_v1(
        feasibility_audit=_load_json_document(args.feasibility_audit, "feasibility audit"),
        dependency_matrix=_load_json_document(args.dependency_matrix, "dependency matrix"),
        common42_check=_load_json_document(args.common42_check, "COMMON-42 check"),
        dataset_manifest=_load_json_document(args.dataset_manifest, "dataset manifest"),
        d1_data_access_audit=_load_json_document(args.d1_data_access_audit, "D1 data-access audit"),
        executable_equivalence=_load_json_document(args.executable_equivalence, "executable equivalence"),
        evidence_manifest=_load_json_document(args.evidence_manifest, "evidence manifest"),
        train1_path=args.train1,
        train2_path=args.train2,
        private_destination=args.private_destination,
        local_locator_manifest=args.local_locator_manifest,
        public_receipt_path=args.public_receipt,
        repository_root=args.repository_root,
        expected_builder_commit=args.expected_builder_commit,
        execution_timestamp=args.execution_timestamp,
    )
    print(
        canonical_json_v1(
            {
                "status": "materialized_task039e3_utility_normal_only_authority_v1",
                "private_registry_hash": result.private_registry_hash,
                "local_locator_manifest_hash": result.local_locator_manifest_hash,
                "public_receipt_hash": result.public_receipt_hash,
                "write_order": list(result.write_order),
            }
        )
    )
    return 0


def authority_snapshot_v1() -> dict[str, Any]:
    """Public metadata-only snapshot; contains no values or private paths."""

    return {
        "task_id": TASK_ID,
        "authority_version": AUTHORITY_VERSION,
        "authority_lineage": AUTHORITY_LINEAGE,
        "historical_e1_identity_restored": False,
        "historical_numeric_identity_restored": False,
        "construction_result_validity": "UNCHANGED",
        "terminal_custody_validity": "UNCHANGED",
        "common42": {
            "accepted": COMMON_RELATION_COUNT,
            "no_rule": 0,
            "authority_hash": COMMON42_AUTHORITY_CHECK_HASH,
            "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        },
        "utility_numeric_roles": list(UTILITY_NUMERIC_ROLES),
        "utility_numeric_reference_count": UTILITY_NUMERIC_REFERENCE_COUNT,
        "normal_input_identities": [item.to_dict() for item in NORMAL_INPUT_IDENTITIES],
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "private_locator_environment": PRIVATE_LOCATOR_ENV,
        "t2_utility_scope_authorized": False,
        "real_data_authority_materialized": False,
        "utility_executed": False,
    }


__all__ = [
    "AUTHORITY_LINEAGE",
    "AUTHORITY_VERSION",
    "CALIBRATION_POLICY_HASH",
    "CALIBRATION_POLICY_VERSION",
    "CALIBRATION_ROLE_SPECS",
    "COMMON42_AUTHORITY_CHECK_HASH",
    "COMMON_RELATION_COUNT",
    "EXECUTABLE_EQUIVALENCE_HASH",
    "HISTORICAL_E1_IDENTITY_RESTORED",
    "HISTORICAL_NUMERIC_IDENTITY_RESTORED",
    "NORMAL_INPUT_IDENTITIES",
    "NORMAL_INPUT_IDENTITY_SET_HASH",
    "NORMAL_TRAIN1_IDENTITY",
    "NORMAL_TRAIN2_IDENTITY",
    "PRIVATE_LOCATOR_ENV",
    "T2_UTILITY_SCOPE_AUTHORIZED",
    "UTILITY_NUMERIC_REFERENCE_COUNT",
    "UTILITY_NUMERIC_ROLES",
    "AtomicMaterializationResultV1",
    "CommonRelationAuthorityV1",
    "NormalOnlyAuthorityDefinitionV1",
    "NormalOnlyAuthorityV1Error",
    "authority_snapshot_v1",
    "build_common42_authority_v1",
    "build_private_registry_document_v1",
    "calibrate_all_role_values_v1",
    "derive_source_parameters_normal_only_v1",
    "derive_target_scale_normal_only_v1",
    "finalize_materialization_atomically_v1",
    "load_verified_normal_features_v1",
    "materialize_normal_only_authority_v1",
    "new_reference_identity_v1",
    "public_receipt_document_v1",
    "validate_finalized_authority_v1",
    "validate_local_locator_manifest_v1",
    "validate_normal_input_authorities_v1",
    "validate_private_registry_document_v1",
    "validate_public_receipt_v1",
    "validate_route_c_bindings_v1",
    "verify_builder_checkout_v1",
    "verify_normal_input_file_v1",
]


if __name__ == "__main__":
    raise SystemExit(main())
