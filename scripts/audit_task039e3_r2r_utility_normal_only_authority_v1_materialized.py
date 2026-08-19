"""Independent audit for the materialized TASK039E3 normal-only authority.

The primary oracle in this module is deliberately standard-library-only.  It
does not import the production authority implementation and never emits private
paths, registry records, or numeric calibration values.  Failures are reported
only through stable, sanitized error codes.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping, Sequence


AUTHORITY_VERSION = "TASK039E3_UTILITY_NORMAL_ONLY_AUTHORITY_V1"
AUTHORITY_LINEAGE = "NEW_VERSION_FROM_FROZEN_METHOD_AND_NORMAL_DATA"
SCHEMA_VERSION = "1.0.0"
CONTROL_REVISION = "R1"
CALIBRATION_POLICY_VERSION = "TASK039D0_CONTINUOUS_STEP_CALIBRATION_V1"

AUTHORITY_DEFINITION_HASH = "6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de"
CALIBRATION_POLICY_HASH = "4f2622050637e3e83205dec59400fa6bf9ed2bd1a41f6b8ceb1900dc9f69b881"
EXECUTABLE_EQUIVALENCE_HASH = "3efdce159bc5ac39825d4e4654428237e47205307f83aae7a133db6c5789f60f"
COMMON42_AUTHORITY_HASH = "3bd07e1c2baf375bde86a2310b529dda40962e027edbd77485f431dc244730ff"
E1_PUBLIC_MANIFEST_HASH = "ee8c5b7e9895f5f6afdd1be2563244e3b82dca9c3eadca502dd522940931e3ae"
NORMAL_INPUT_IDENTITY_SET_HASH = "cc502d87daf19a1511f868c1c767045a4457d505d195b0214f244d1910fe0cda"
CANONICAL_UTILITY_BINDING_SET_HASH = "55c315b463b60d44f43dfc8058bd85cea2dd6ef865eba421c8953cf7a808a089"

HISTORICAL_E1_HASH = "0998c6600078b8a0aca7263b6e0b702808cc141b1cbcfe3d0026fddb98c408a7"
HISTORICAL_NUMERIC_REGISTRY_HASH = "59e81b261801f28eefc917256dc628af704a14b4064161972d01545968555271"
EXPECTED_PRIVATE_REGISTRY_HASH = "9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0"
EXPECTED_LOCATOR_HASH = "b5588c04d08d88d4ee2a2d319708e62d10bc04330baeb7591876f076270e4ac4"
EXPECTED_PUBLIC_RECEIPT_HASH = "3054bf3eaf50bdc4297652a475b3b465e59b449810493ac775fed0bcf7567ced"

AUTHORIZATION_ARTIFACT_HASH = "dad4d6c39d5f317bed41fe3f780d4bb20bd7b33aea047b9a166614ac4acf42b9"
AUTHORIZATION_RECEIPT_HASH = "3b19a827a77388b9c227910f6485edb5f490c611db6dbb3cd9fba692fd062bac"
CONTROL_SOURCE_COMMIT = "216783ac6b3c77376b4e56b92ddc655907ce3668"
CONTROL_SOURCE_BLOB = "5e6d52fdfadada7373c50c382a347930f3384e24"
CONTROL_SOURCE_RAW_SHA256 = "1b15098e9f8c75a76ad98f7a0ef998af86470b195d035ffab08e9f185fe1a3d9"
SCIENTIFIC_V1_COMMIT = "d58757b63d21519bc39398ddcf96be1682e8b01a"
SCIENTIFIC_V1_SOURCE_BLOB = "b071678a151161f9585301472f5eb23d7ce2c246"
SCIENTIFIC_V1_SOURCE_RAW_SHA256 = "f18eceabd1f0f5aee7755bff964b985014411b6a0b98425e424863a59256b30e"

TRAIN1_SHA256 = "53007b0ba604fbf338e7ac2e08cd81d874b5d1388f3aecb213ddcba5bf2bec4a"
TRAIN2_SHA256 = "0e520e82bf78a661ab19ce4967f3c766bd809820f457a9c90c365102d4534c56"
HEADER_SHA256 = "95968d825d1c9caab778a857cec618b64674ec5a85d94e6952d99c2cab08d16a"

SUCCESS_EXECUTION_RECEIPT = "d164f00da3121e345907fe9076e62f4697493f26dde7448cc8527b895cbffa6e"
SUCCESS_EXECUTION_ACCOUNTING = "0e18526c8dbcaec26d67385b89c60826dc4388cac08727cd61a2c60b1b812ae2"
TERMINAL_CUSTODY_SUPPLEMENT = "54d71edb6357e8c4d4a5479a9f0b130ca0f89f10ed4ff04ad9ba90122f3ff7c2"
TERMINAL_AUDIT_A = "3abf1651dd81554a990c26b7b46512ac75fc63e4"
TERMINAL_AUDIT_B = "a431dd88866e0f65439e3fad567894e0e9058713"

UTILITY_ROLES = (
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
HISTORICAL_ROLES = UTILITY_ROLES[:3] + ("selected_delay_horizon_seconds",) + UTILITY_ROLES[3:]
FROZEN_CONSTANTS: dict[str, int | float] = {
    "source_pre_window_seconds": 5,
    "source_post_window_seconds": 5,
    "minimum_source_stability_fraction": 0.8,
    "source_refractory_seconds": 10,
    "cross_source_isolation_radius_seconds": 2,
    "target_baseline_window_seconds": 5,
    "target_response_window_seconds": 3,
}

NORMAL_INPUT_IDENTITIES = (
    {
        "logical_role": "normal_train1",
        "relative_path": "hai-23.05/hai-train1.csv",
        "sha256": TRAIN1_SHA256,
        "byte_size": 162418984,
        "row_count": 280800,
        "header_sha256": HEADER_SHA256,
    },
    {
        "logical_role": "normal_train2",
        "relative_path": "hai-23.05/hai-train2.csv",
        "sha256": TRAIN2_SHA256,
        "byte_size": 169121615,
        "row_count": 291600,
        "header_sha256": HEADER_SHA256,
    },
)

REGISTRY_KEYS = frozenset(
    {
        "artifact_hash",
        "artifact_type",
        "schema_version",
        "authority_version",
        "authority_lineage",
        "execution_control_revision",
        "historical_e1_identity_restored",
        "historical_numeric_identity_restored",
        "construction_result_validity",
        "terminal_custody_validity",
        "common42_authority_hash",
        "executable_equivalence_hash",
        "authority_definition_hash",
        "normal_input_identity_set_hash",
        "calibration_policy_version",
        "calibration_policy_hash",
        "relation_count",
        "record_count",
        "unique_logical_key_count",
        "status",
        "records",
    }
)
RECORD_KEYS = frozenset(
    {
        "schema_version",
        "authority_version",
        "relation_identity",
        "relation_binding_hash",
        "semantic_execution_hash",
        "numeric_role",
        "new_reference_identity",
        "numeric_value",
        "calibration_policy_version",
        "normal_train1_identity",
        "normal_train2_identity",
        "provenance_identity",
        "record_hash",
    }
)
PUBLIC_RECEIPT_KEYS = frozenset(
    {
        "artifact_hash",
        "artifact_type",
        "schema_version",
        "authority_version",
        "authority_lineage",
        "historical_e1_identity_restored",
        "historical_numeric_identity_restored",
        "private_registry_content_hash",
        "record_count",
        "unique_key_count",
        "relation_count",
        "common42_authority_hash",
        "executable_equivalence_hash",
        "authority_definition_hash",
        "normal_input_identities",
        "normal_input_identity_set_hash",
        "calibration_policy_version",
        "calibration_policy_hash",
        "builder_commit",
        "builder_git_blob",
        "builder_source_sha256",
        "execution_timestamp",
        "validation_counts",
        "construction_provenance",
        "t2_utility_scope_authorized",
        "public_receipt_written_last",
        "control_revision",
        "scientific_v1_commit",
        "control_source_commit",
        "control_source_git_blob",
        "control_source_raw_sha256",
        "execution_authorization_hash",
        "materialization_authorized",
    }
)
LOCATOR_KEYS = frozenset(
    {
        "artifact_hash",
        "artifact_type",
        "schema_version",
        "authority_version",
        "absolute_private_authority_path",
        "private_authority_hash",
        "public_receipt_hash",
        "created_at",
        "builder_commit",
        "local_only",
        "must_not_be_committed",
        "control_revision",
        "scientific_v1_commit",
        "control_source_commit",
        "control_source_git_blob",
        "control_source_raw_sha256",
        "execution_authorization_hash",
        "materialization_authorized",
    }
)
AUTHORIZATION_KEYS = frozenset(
    {
        "artifact_hash",
        "artifact_type",
        "schema_version",
        "authority_version",
        "control_revision",
        "scientific_v1_commit",
        "scientific_v1_source_blob",
        "scientific_v1_source_raw_sha256",
        "common42_authority_definition_hash",
        "calibration_policy_hash",
        "executable_equivalence_hash",
        "normal_input_identity_set_hash",
        "authorized_control_commit",
        "authorized_control_source_blob",
        "authorized_control_source_raw_sha256",
        "focused_independent_reaudit_receipt_hash",
        "protocol_audit_closure_hash",
        "protocol_audit_receipt_hash",
        "scope",
        "normal_train1_sha256",
        "normal_train2_sha256",
        "private_locator_environment",
        "train3_access",
        "test_access",
        "label_access",
        "provider_access",
        "utility_execution",
        "materialization_authorized",
    }
)

PUBLIC_FILES = (
    "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION.json",
    "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION_BUNDLE.json",
    "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION_PUBLIC_RECEIPT.json",
    "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION_RECEIPT.json",
    "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION_REPORT.md",
    "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION_VALIDATION.json",
)
PUBLIC_JSON_HASHES = {
    PUBLIC_FILES[0]: "9c509382474068a049bc0837392d6a230801fec8f6cfa2f38d425299054aec06",
    PUBLIC_FILES[1]: "ee50021f125cabb23028991e41ef7faf5692b6151559722bee37ecb7dca66a82",
    PUBLIC_FILES[2]: EXPECTED_PUBLIC_RECEIPT_HASH,
    PUBLIC_FILES[3]: "96aee01d66063487e5997fe0294969c413b14159774e99a36289fcd3d8dab8c9",
    PUBLIC_FILES[5]: "9c69a9863d1c74c211ea026eaabb7cff99f0206c37677db7a137a6dba3ac360f",
}


class AuditError(ValueError):
    """Sanitized independent audit failure."""


def fail(code: str) -> None:
    raise AuditError(code)


def require(condition: bool, code: str) -> None:
    if not condition:
        fail(code)


def canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def stable_hash(payload: object) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def is_sha(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def is_git_oid(value: object) -> bool:
    return type(value) is str and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def is_absolute_string(value: str) -> bool:
    return PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()


def load_json(path: Path, code: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            document = json.load(stream)
    except Exception as exc:  # never expose paths or private content
        raise AuditError(code) from exc
    require(type(document) is dict, code)
    return document


def verify_self_hash(document: Mapping[str, Any], expected: str, code: str) -> str:
    observed = document.get("artifact_hash")
    require(is_sha(observed), code)
    payload = {key: value for key, value in document.items() if key != "artifact_hash"}
    try:
        replayed = stable_hash(payload)
    except Exception as exc:
        raise AuditError(code) from exc
    require(replayed == observed == expected, code)
    return str(observed)


def reference_identity(relation: Mapping[str, Any], role: str) -> str:
    preimage = {
        "authority_version": AUTHORITY_VERSION,
        "relation_binding_hash": relation["relation_binding_hash"],
        "semantic_execution_hash": relation["semantic_execution_hash"],
        "numeric_role": role,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "normal_input_identity_set": NORMAL_INPUT_IDENTITY_SET_HASH,
        "common42_authority_hash": COMMON42_AUTHORITY_HASH,
    }
    return f"{AUTHORITY_VERSION}:{stable_hash(preimage)}"


def provenance_identity(relation: Mapping[str, Any], role: str) -> str:
    if role in {"source_step_threshold", "source_stability_tolerance"}:
        dependency = {"source": relation["source"]}
    elif role == "target_noise_scale":
        dependency = {"target": relation["target"]}
    else:
        dependency = {"frozen_constant_role": role}
    return stable_hash(
        {
            "authority_version": AUTHORITY_VERSION,
            "calibration_policy_version": CALIBRATION_POLICY_VERSION,
            "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
            "numeric_role": role,
            "dependency": dependency,
        }
    )


def reconstruct_common42(repo_root: Path) -> dict[str, Any]:
    reports = repo_root / "docs" / "task_reports"
    equivalence = load_json(
        reports / "TASK-039E3_R2R_UTILITY_PROTOCOL_EXECUTABLE_EQUIVALENCE.json",
        "AUDIT_COMMON_PUBLIC_READ",
    )
    evidence = load_json(
        reports / "TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json",
        "AUDIT_E1_PUBLIC_READ",
    )
    verify_self_hash(equivalence, EXECUTABLE_EQUIVALENCE_HASH, "AUDIT_COMMON_PUBLIC_HASH")
    verify_self_hash(evidence, E1_PUBLIC_MANIFEST_HASH, "AUDIT_E1_PUBLIC_HASH")
    records = equivalence.get("relation_records")
    entries = evidence.get("entries")
    require(type(records) is list and len(records) == 42, "AUDIT_COMMON_RELATION_COUNT")
    require(type(entries) is list and len(entries) == 42, "AUDIT_E1_RELATION_COUNT")
    require(
        type(equivalence.get("relation_equivalence_class_count")) is int
        and equivalence["relation_equivalence_class_count"] == 42
        and type(evidence.get("numeric_binding_count")) is int
        and evidence["numeric_binding_count"] == 462,
        "AUDIT_HISTORICAL_BINDING_COUNT",
    )
    by_binding: dict[str, dict[str, Any]] = {}
    for entry in entries:
        require(type(entry) is dict, "AUDIT_E1_ENTRY_SCHEMA")
        entry_hash = entry.get("artifact_hash")
        require(is_sha(entry_hash), "AUDIT_E1_ENTRY_HASH")
        require(
            stable_hash({key: value for key, value in entry.items() if key != "artifact_hash"})
            == entry_hash,
            "AUDIT_E1_ENTRY_HASH",
        )
        binding = entry.get("relation_binding_hash")
        require(is_sha(binding) and binding not in by_binding, "AUDIT_E1_BINDING")
        by_binding[str(binding)] = entry

    relations: list[dict[str, Any]] = []
    historical_utility_references: list[str] = []
    for record in records:
        require(type(record) is dict, "AUDIT_COMMON_RECORD_SCHEMA")
        binding = record.get("relation_binding_hash")
        semantic = record.get("semantic_execution_hash")
        signature = record.get("executable_signature")
        require(is_sha(binding) and is_sha(semantic), "AUDIT_COMMON_IDENTITY_FORMAT")
        require(type(signature) is dict and stable_hash(signature) == semantic, "AUDIT_COMMON_SEMANTIC_HASH")
        require(record.get("common_arm_cells") == ["T0", "T1", "T1-B"], "AUDIT_COMMON_ARM_SCOPE")
        entry = by_binding.get(str(binding))
        require(entry is not None, "AUDIT_COMMON_E1_JOIN")
        rows = entry.get("numeric_references")
        require(type(rows) is list and len(rows) == 11, "AUDIT_HISTORICAL_ROLE_COUNT")
        manifest_refs: dict[str, str] = {}
        for row in rows:
            require(type(row) is dict and row.get("numeric_role") in HISTORICAL_ROLES, "AUDIT_HISTORICAL_ROLE")
            role = str(row["numeric_role"])
            reference = row.get("numeric_reference")
            require(is_sha(reference) and role not in manifest_refs, "AUDIT_HISTORICAL_REFERENCE")
            manifest_refs[role] = str(reference)
        require(set(manifest_refs) == set(HISTORICAL_ROLES), "AUDIT_HISTORICAL_ROLE_CLOSURE")
        windows = signature.get("window_constant_references")
        require(type(windows) is dict and set(windows) == set(UTILITY_ROLES[3:]), "AUDIT_WINDOW_REFERENCE_SCHEMA")
        signature_refs = {
            "source_step_threshold": signature.get("source_threshold_reference"),
            "source_stability_tolerance": signature.get("source_stability_reference"),
            "target_noise_scale": signature.get("target_scale_reference"),
            **windows,
        }
        require(set(signature_refs) == set(UTILITY_ROLES), "AUDIT_UTILITY_ROLE_CLOSURE")
        for role in UTILITY_ROLES:
            require(
                is_sha(signature_refs[role]) and signature_refs[role] == manifest_refs[role],
                "AUDIT_HISTORICAL_REFERENCE_BINDING",
            )
            historical_utility_references.append(str(signature_refs[role]))
        horizon = signature.get("selected_delay_horizon_seconds")
        require(type(horizon) is int and horizon in {1, 5, 10, 30, 60}, "AUDIT_SELECTED_HORIZON")
        expected_fields = {
            "source": signature.get("source"),
            "target": signature.get("target"),
            "source_step_direction": signature.get("source_step_direction"),
            "target_response_direction": signature.get("target_response_direction"),
            "selected_horizon_seconds": horizon,
        }
        require(all(entry.get(key) == value for key, value in expected_fields.items()), "AUDIT_RELATION_SEMANTICS")
        relation = {
            "relation_identity": entry.get("relation_identity"),
            "relation_binding_hash": binding,
            "semantic_execution_hash": semantic,
            "source": signature.get("source"),
            "target": signature.get("target"),
            "source_direction": signature.get("source_step_direction"),
            "target_direction": signature.get("target_response_direction"),
            "selected_horizon_seconds": horizon,
            "historical_references": {role: str(signature_refs[role]) for role in UTILITY_ROLES},
        }
        require(
            type(relation["relation_identity"]) is str
            and str(relation["relation_identity"]).startswith("directional_relation:")
            and type(relation["source"]) is str
            and bool(relation["source"])
            and type(relation["target"]) is str
            and bool(relation["target"])
            and relation["source_direction"] in {"step_up", "step_down"}
            and relation["target_direction"] in {"increase", "decrease"},
            "AUDIT_RELATION_IDENTITY",
        )
        relations.append(relation)

    relations.sort(key=lambda item: str(item["relation_binding_hash"]))
    for key in ("relation_identity", "relation_binding_hash", "semantic_execution_hash"):
        observed = [str(item[key]) for item in relations]
        require(len(observed) == len(set(observed)) == 42, "AUDIT_COMMON_UNIQUENESS")
    require(
        len(historical_utility_references) == len(set(historical_utility_references)) == 420,
        "AUDIT_HISTORICAL_UTILITY_REFERENCE_COUNT",
    )
    binding_set_hash = stable_hash(
        {
            "historical_utility_reference_bindings": sorted(historical_utility_references),
            "count": 420,
        }
    )
    require(binding_set_hash == CANONICAL_UTILITY_BINDING_SET_HASH, "AUDIT_UTILITY_BINDING_SET_HASH")
    references = [reference_identity(relation, role) for relation in relations for role in UTILITY_ROLES]
    require(len(references) == len(set(references)) == 420, "AUDIT_REFERENCE_UNIVERSE")
    identity_relations = [
        {
            key: relation[key]
            for key in (
                "relation_identity",
                "relation_binding_hash",
                "semantic_execution_hash",
                "source",
                "target",
                "source_direction",
                "target_direction",
                "selected_horizon_seconds",
            )
        }
        for relation in relations
    ]
    definition_hash = stable_hash(
        {
            "authority_version": AUTHORITY_VERSION,
            "authority_lineage": AUTHORITY_LINEAGE,
            "common42_authority_hash": COMMON42_AUTHORITY_HASH,
            "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
            "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
            "calibration_policy_version": CALIBRATION_POLICY_VERSION,
            "relations": identity_relations,
            "new_reference_identities": references,
        }
    )
    require(definition_hash == AUTHORITY_DEFINITION_HASH, "AUDIT_AUTHORITY_DEFINITION_HASH")
    sources = sorted({str(item["source"]) for item in relations})
    targets = sorted({str(item["target"]) for item in relations})
    feature_union = sorted(set(sources) | set(targets))
    require((len(sources), len(targets), len(feature_union)) == (9, 10, 19), "AUDIT_COMMON_FEATURE_SCOPE")
    return {
        "relations": relations,
        "references": references,
        "sources": sources,
        "targets": targets,
        "feature_union": feature_union,
        "utility_binding_set_hash": binding_set_hash,
        "authority_definition_hash": definition_hash,
    }


def audit_numeric_value(role: str, value: object) -> None:
    if role in FROZEN_CONSTANTS:
        expected = FROZEN_CONSTANTS[role]
        require(type(value) is type(expected) and value == expected, "AUDIT_FROZEN_CONSTANT_DOMAIN")
        return
    require(type(value) is float and math.isfinite(value), "AUDIT_NUMERIC_TYPE_DOMAIN")
    if role in {"source_step_threshold", "target_noise_scale"}:
        require(value > 0.0, "AUDIT_NUMERIC_TYPE_DOMAIN")
    elif role == "source_stability_tolerance":
        require(value >= 0.0, "AUDIT_NUMERIC_TYPE_DOMAIN")
    else:
        fail("AUDIT_NUMERIC_ROLE")


def audit_registry_document(
    document: Mapping[str, Any],
    common: Mapping[str, Any],
    *,
    expected_artifact_hash: str | None = EXPECTED_PRIVATE_REGISTRY_HASH,
) -> dict[str, Any]:
    require(type(document) is dict and set(document) == REGISTRY_KEYS, "AUDIT_REGISTRY_SCHEMA")
    observed_hash = document.get("artifact_hash")
    require(is_sha(observed_hash), "AUDIT_REGISTRY_HASH")
    try:
        replayed_hash = stable_hash({key: value for key, value in document.items() if key != "artifact_hash"})
    except Exception as exc:
        raise AuditError("AUDIT_REGISTRY_HASH") from exc
    require(replayed_hash == observed_hash, "AUDIT_REGISTRY_HASH")
    if expected_artifact_hash is not None:
        require(observed_hash == expected_artifact_hash, "AUDIT_REGISTRY_EXPECTED_HASH")
    expected_header = {
        "artifact_type": "task039e3_r2r_utility_normal_only_private_registry_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "authority_lineage": AUTHORITY_LINEAGE,
        "execution_control_revision": CONTROL_REVISION,
        "historical_e1_identity_restored": False,
        "historical_numeric_identity_restored": False,
        "construction_result_validity": "UNCHANGED",
        "terminal_custody_validity": "UNCHANGED",
        "common42_authority_hash": COMMON42_AUTHORITY_HASH,
        "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "authority_definition_hash": AUTHORITY_DEFINITION_HASH,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "relation_count": 42,
        "record_count": 420,
        "unique_logical_key_count": 420,
        "status": "complete_private_registry_pending_public_receipt",
    }
    require(all(document.get(key) == value for key, value in expected_header.items()), "AUDIT_REGISTRY_HEADER")
    require(
        type(document.get("historical_e1_identity_restored")) is bool
        and document["historical_e1_identity_restored"] is False
        and type(document.get("historical_numeric_identity_restored")) is bool
        and document["historical_numeric_identity_restored"] is False
        and all(type(document[key]) is int for key in ("relation_count", "record_count", "unique_logical_key_count")),
        "AUDIT_REGISTRY_HEADER_TYPES",
    )
    records = document.get("records")
    require(type(records) is list and len(records) == 420, "AUDIT_RECORD_COUNT")
    relation_by_binding = {str(item["relation_binding_hash"]): item for item in common["relations"]}
    expected_keys = {(binding, role) for binding in relation_by_binding for role in UTILITY_ROLES}
    keys: set[tuple[str, str]] = set()
    references: set[str] = set()
    record_hash_matches = 0
    provenance_matches = 0
    source_values: dict[str, dict[str, set[float]]] = {}
    target_values: dict[str, set[float]] = {}
    numeric_failures = {"source_step_threshold": 0, "source_stability_tolerance": 0, "target_noise_scale": 0}
    frozen_constant_mismatches = 0
    for record in records:
        require(type(record) is dict and set(record) == RECORD_KEYS, "AUDIT_RECORD_SCHEMA")
        record_hash = record.get("record_hash")
        require(is_sha(record_hash), "AUDIT_RECORD_HASH_MISMATCH")
        try:
            replayed_record_hash = stable_hash(
                {key: value for key, value in record.items() if key != "record_hash"}
            )
        except Exception as exc:
            raise AuditError("AUDIT_RECORD_HASH_MISMATCH") from exc
        require(replayed_record_hash == record_hash, "AUDIT_RECORD_HASH_MISMATCH")
        record_hash_matches += 1
        binding = record.get("relation_binding_hash")
        role = record.get("numeric_role")
        require(type(binding) is str and binding in relation_by_binding, "AUDIT_FOREIGN_RELATION")
        require(type(role) is str and role in UTILITY_ROLES, "AUDIT_UNEXPECTED_ROLE")
        relation = relation_by_binding[binding]
        logical_key = (binding, role)
        require(logical_key not in keys, "AUDIT_DUPLICATE_LOGICAL_KEY")
        keys.add(logical_key)
        expected_reference = reference_identity(relation, role)
        observed_reference = record.get("new_reference_identity")
        require(
            observed_reference == expected_reference and observed_reference not in references,
            "AUDIT_REFERENCE_BINDING",
        )
        references.add(str(observed_reference))
        require(
            observed_reference
            not in {
                relation["historical_references"][role],
                HISTORICAL_E1_HASH,
                HISTORICAL_NUMERIC_REGISTRY_HASH,
            },
            "AUDIT_HISTORICAL_IDENTITY_COLLISION",
        )
        require(
            record.get("schema_version") == SCHEMA_VERSION
            and record.get("authority_version") == AUTHORITY_VERSION
            and record.get("relation_identity") == relation["relation_identity"]
            and record.get("semantic_execution_hash") == relation["semantic_execution_hash"]
            and record.get("calibration_policy_version") == CALIBRATION_POLICY_VERSION
            and record.get("normal_train1_identity") == TRAIN1_SHA256
            and record.get("normal_train2_identity") == TRAIN2_SHA256,
            "AUDIT_RECORD_AUTHORITY_BINDING",
        )
        expected_provenance = provenance_identity(relation, role)
        require(record.get("provenance_identity") == expected_provenance, "AUDIT_PROVENANCE_BINDING")
        provenance_matches += 1
        value = record.get("numeric_value")
        try:
            audit_numeric_value(role, value)
        except AuditError:
            if role in numeric_failures:
                numeric_failures[role] += 1
            else:
                frozen_constant_mismatches += 1
            raise
        if role in {"source_step_threshold", "source_stability_tolerance"}:
            source = str(relation["source"])
            source_values.setdefault(source, {}).setdefault(role, set()).add(value)
        elif role == "target_noise_scale":
            target = str(relation["target"])
            target_values.setdefault(target, set()).add(value)
    require(keys == expected_keys and len(keys) == 420, "AUDIT_LOGICAL_KEY_CLOSURE")
    require(references == set(common["references"]) and len(references) == 420, "AUDIT_REFERENCE_CLOSURE")
    source_inconsistencies = sum(
        1
        for role_sets in source_values.values()
        for role in ("source_step_threshold", "source_stability_tolerance")
        if len(role_sets.get(role, set())) != 1
    )
    target_inconsistencies = sum(1 for values in target_values.values() if len(values) != 1)
    require(len(source_values) == 9 and source_inconsistencies == 0, "AUDIT_SOURCE_SHARING")
    require(len(target_values) == 10 and target_inconsistencies == 0, "AUDIT_TARGET_SHARING")
    require(observed_hash not in {HISTORICAL_E1_HASH, HISTORICAL_NUMERIC_REGISTRY_HASH}, "AUDIT_HISTORICAL_IDENTITY_COLLISION")
    return {
        "private_registry_hash": observed_hash,
        "relations": 42,
        "roles": 10,
        "records": len(records),
        "logical_keys": len(keys),
        "references": len(references),
        "record_hash_matches": record_hash_matches,
        "provenance_identity_matches": provenance_matches,
        "missing": 0,
        "duplicates": 0,
        "unexpected": 0,
        "foreign_relations": 0,
        "semantic_mismatches": 0,
        "reference_mismatches": 0,
        "authority_mismatches": 0,
        "calibration_policy_mismatches": 0,
        "normal_input_mismatches": 0,
        "numeric_type_domain_failures": numeric_failures,
        "frozen_constant_mismatches": frozen_constant_mismatches,
        "frozen_constant_records": 294,
        "source_groups": len(source_values),
        "source_sharing_inconsistencies": source_inconsistencies,
        "target_groups": len(target_values),
        "target_sharing_inconsistencies": target_inconsistencies,
        "historical_identity_collisions": 0,
    }


def _rehash_record_and_registry(document: dict[str, Any], index: int) -> None:
    record = document["records"][index]
    record["record_hash"] = stable_hash({key: value for key, value in record.items() if key != "record_hash"})
    document["artifact_hash"] = stable_hash(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )


def _rehash_registry(document: dict[str, Any]) -> None:
    document["artifact_hash"] = stable_hash(
        {key: value for key, value in document.items() if key != "artifact_hash"}
    )


def run_mutation_audit(document: Mapping[str, Any], common: Mapping[str, Any]) -> dict[str, Any]:
    cases: list[tuple[str, Any]] = []

    def case(name: str, mutate: Any) -> None:
        candidate = deepcopy(document)
        mutate(candidate)
        cases.append((name, candidate))

    case("remove_record", lambda doc: (doc["records"].pop(), _rehash_registry(doc)))
    case("duplicate_record", lambda doc: (doc["records"].append(deepcopy(doc["records"][0])), _rehash_registry(doc)))
    case("relation_binding", lambda doc: (doc["records"][0].__setitem__("relation_binding_hash", "0" * 64), _rehash_record_and_registry(doc, 0)))
    case("semantic_hash", lambda doc: (doc["records"][0].__setitem__("semantic_execution_hash", "0" * 64), _rehash_record_and_registry(doc, 0)))
    case("relation_identity", lambda doc: (doc["records"][0].__setitem__("relation_identity", "directional_relation:mutated"), _rehash_record_and_registry(doc, 0)))
    case("numeric_role", lambda doc: (doc["records"][0].__setitem__("numeric_role", "unexpected_role"), _rehash_record_and_registry(doc, 0)))
    case("reference_identity", lambda doc: (doc["records"][0].__setitem__("new_reference_identity", f"{AUTHORITY_VERSION}:{'0' * 64}"), _rehash_record_and_registry(doc, 0)))
    case("provenance_identity", lambda doc: (doc["records"][0].__setitem__("provenance_identity", "0" * 64), _rehash_record_and_registry(doc, 0)))
    case("normal_train1_binding", lambda doc: (doc["records"][0].__setitem__("normal_train1_identity", "0" * 64), _rehash_record_and_registry(doc, 0)))
    case("normal_train2_binding", lambda doc: (doc["records"][0].__setitem__("normal_train2_identity", "0" * 64), _rehash_record_and_registry(doc, 0)))
    case("calibration_policy_binding", lambda doc: (doc["records"][0].__setitem__("calibration_policy_version", "MUTATED"), _rehash_record_and_registry(doc, 0)))
    case("record_authority_version", lambda doc: (doc["records"][0].__setitem__("authority_version", "MUTATED"), _rehash_record_and_registry(doc, 0)))
    case("record_hash", lambda doc: (doc["records"][0].__setitem__("record_hash", "0" * 64), _rehash_registry(doc)))
    case("registry_artifact_hash", lambda doc: doc.__setitem__("artifact_hash", "0" * 64))
    case("positive_float_to_int", lambda doc: (doc["records"][0].__setitem__("numeric_value", 1), _rehash_record_and_registry(doc, 0)))
    case("positive_float_to_bool", lambda doc: (doc["records"][0].__setitem__("numeric_value", True), _rehash_record_and_registry(doc, 0)))

    def nonfinite(doc: dict[str, Any]) -> None:
        doc["records"][0]["numeric_value"] = float("inf")

    case("numeric_nonfinite", nonfinite)

    constant_index = next(
        index
        for index, record in enumerate(document["records"])
        if record["numeric_role"] == "source_pre_window_seconds"
    )
    case(
        "frozen_constant",
        lambda doc: (
            doc["records"][constant_index].__setitem__("numeric_value", 6),
            _rehash_record_and_registry(doc, constant_index),
        ),
    )
    case("registry_authority_version", lambda doc: (doc.__setitem__("authority_version", "MUTATED"), _rehash_registry(doc)))
    case("header_record_count", lambda doc: (doc.__setitem__("record_count", 419), _rehash_registry(doc)))

    rejected: list[str] = []
    accepted: list[str] = []
    for name, candidate in cases:
        try:
            audit_registry_document(candidate, common, expected_artifact_hash=None)
        except Exception:
            rejected.append(name)
        else:
            accepted.append(name)
    require(len(cases) >= 16 and not accepted, "AUDIT_MUTATION_ACCEPTED")
    return {"cases": len(cases), "rejected": len(rejected), "accepted": len(accepted), "case_results": {name: "REJECTED" for name in rejected}}


def audit_authorization(repo_root: Path) -> dict[str, Any]:
    reports = repo_root / "docs" / "task_reports"
    authorization = load_json(
        reports / "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION_AUTHORIZATION.json",
        "AUDIT_AUTHORIZATION_READ",
    )
    require(set(authorization) == AUTHORIZATION_KEYS, "AUDIT_AUTHORIZATION_SCHEMA")
    verify_self_hash(authorization, AUTHORIZATION_ARTIFACT_HASH, "AUDIT_AUTHORIZATION_HASH")
    expected = {
        "artifact_type": "task039e3_r2r_utility_normal_only_authority_v1_materialization_authorization",
        "schema_version": "1.0.0",
        "authority_version": AUTHORITY_VERSION,
        "control_revision": CONTROL_REVISION,
        "scientific_v1_commit": SCIENTIFIC_V1_COMMIT,
        "scientific_v1_source_blob": SCIENTIFIC_V1_SOURCE_BLOB,
        "scientific_v1_source_raw_sha256": SCIENTIFIC_V1_SOURCE_RAW_SHA256,
        "common42_authority_definition_hash": AUTHORITY_DEFINITION_HASH,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "authorized_control_commit": CONTROL_SOURCE_COMMIT,
        "authorized_control_source_blob": CONTROL_SOURCE_BLOB,
        "authorized_control_source_raw_sha256": CONTROL_SOURCE_RAW_SHA256,
        "scope": "NORMAL_TRAIN1_TRAIN2_NUMERIC_AUTHORITY_MATERIALIZATION_ONLY",
        "normal_train1_sha256": TRAIN1_SHA256,
        "normal_train2_sha256": TRAIN2_SHA256,
        "private_locator_environment": AUTHORITY_VERSION,
        "train3_access": False,
        "test_access": False,
        "label_access": False,
        "provider_access": False,
        "utility_execution": False,
        "materialization_authorized": True,
    }
    require(all(authorization.get(key) == value for key, value in expected.items()), "AUDIT_AUTHORIZATION_BINDING")
    for key in ("train3_access", "test_access", "label_access", "provider_access", "utility_execution", "materialization_authorized"):
        require(type(authorization.get(key)) is bool, "AUDIT_AUTHORIZATION_TYPE")
    authorization_receipt = load_json(
        reports / "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION_AUTHORIZATION_RECEIPT.json",
        "AUDIT_AUTHORIZATION_RECEIPT_READ",
    )
    verify_self_hash(authorization_receipt, AUTHORIZATION_RECEIPT_HASH, "AUDIT_AUTHORIZATION_RECEIPT_HASH")
    require(
        authorization_receipt.get("authorization_artifact_hash") == AUTHORIZATION_ARTIFACT_HASH
        and authorization_receipt.get("authority_definition_hash") == AUTHORITY_DEFINITION_HASH
        and authorization_receipt.get("calibration_policy_hash") == CALIBRATION_POLICY_HASH
        and authorization_receipt.get("common_executable_equivalence_hash") == EXECUTABLE_EQUIVALENCE_HASH
        and authorization_receipt.get("normal_input_identity_set_hash") == NORMAL_INPUT_IDENTITY_SET_HASH
        and authorization_receipt.get("materialization_authorized") is True,
        "AUDIT_AUTHORIZATION_RECEIPT_BINDING",
    )
    return {"authorization": authorization, "authorization_receipt_hash": AUTHORIZATION_RECEIPT_HASH}


def audit_public_receipt(repo_root: Path, authorization: Mapping[str, Any]) -> dict[str, Any]:
    path = (
        repo_root
        / "docs"
        / "task_reports"
        / "TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION_PUBLIC_RECEIPT.json"
    )
    receipt = load_json(path, "AUDIT_PUBLIC_RECEIPT_READ")
    require(set(receipt) == PUBLIC_RECEIPT_KEYS, "AUDIT_PUBLIC_RECEIPT_SCHEMA")
    verify_self_hash(receipt, EXPECTED_PUBLIC_RECEIPT_HASH, "AUDIT_PUBLIC_RECEIPT_HASH")
    expected = {
        "artifact_type": "task039e3_r2r_utility_normal_only_public_receipt_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "authority_lineage": AUTHORITY_LINEAGE,
        "historical_e1_identity_restored": False,
        "historical_numeric_identity_restored": False,
        "private_registry_content_hash": EXPECTED_PRIVATE_REGISTRY_HASH,
        "record_count": 420,
        "unique_key_count": 420,
        "relation_count": 42,
        "common42_authority_hash": COMMON42_AUTHORITY_HASH,
        "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "authority_definition_hash": AUTHORITY_DEFINITION_HASH,
        "normal_input_identities": list(NORMAL_INPUT_IDENTITIES),
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "builder_commit": CONTROL_SOURCE_COMMIT,
        "builder_git_blob": CONTROL_SOURCE_BLOB,
        "builder_source_sha256": CONTROL_SOURCE_RAW_SHA256,
        "t2_utility_scope_authorized": False,
        "public_receipt_written_last": True,
        "control_revision": CONTROL_REVISION,
        "scientific_v1_commit": SCIENTIFIC_V1_COMMIT,
        "control_source_commit": CONTROL_SOURCE_COMMIT,
        "control_source_git_blob": CONTROL_SOURCE_BLOB,
        "control_source_raw_sha256": CONTROL_SOURCE_RAW_SHA256,
        "execution_authorization_hash": AUTHORIZATION_ARTIFACT_HASH,
        "materialization_authorized": True,
    }
    require(all(receipt.get(key) == value for key, value in expected.items()), "AUDIT_PUBLIC_RECEIPT_BINDING")
    for key in (
        "historical_e1_identity_restored",
        "historical_numeric_identity_restored",
        "t2_utility_scope_authorized",
        "public_receipt_written_last",
        "materialization_authorized",
    ):
        require(type(receipt.get(key)) is bool, "AUDIT_PUBLIC_RECEIPT_TYPE")
    for key in ("record_count", "unique_key_count", "relation_count"):
        require(type(receipt.get(key)) is int, "AUDIT_PUBLIC_RECEIPT_TYPE")
    counts = receipt.get("validation_counts")
    require(
        type(counts) is dict
        and set(counts) == {"records", "unique_keys", "missing", "duplicates", "unexpected", "nonfinite"}
        and all(type(value) is int for value in counts.values())
        and counts == {"records": 420, "unique_keys": 420, "missing": 0, "duplicates": 0, "unexpected": 0, "nonfinite": 0},
        "AUDIT_PUBLIC_RECEIPT_COUNTS",
    )
    provenance = receipt.get("construction_provenance")
    expected_provenance = {
        "successful_execution_receipt": SUCCESS_EXECUTION_RECEIPT,
        "successful_execution_accounting": SUCCESS_EXECUTION_ACCOUNTING,
        "terminal_custody_supplement": TERMINAL_CUSTODY_SUPPLEMENT,
        "terminal_audit_a": TERMINAL_AUDIT_A,
        "terminal_audit_b": TERMINAL_AUDIT_B,
        "scientific_result_evaluable": True,
    }
    require(
        type(provenance) is dict
        and provenance == expected_provenance
        and type(provenance.get("scientific_result_evaluable")) is bool,
        "AUDIT_PUBLIC_RECEIPT_PROVENANCE",
    )
    try:
        timestamp = datetime.fromisoformat(str(receipt.get("execution_timestamp")))
    except Exception as exc:
        raise AuditError("AUDIT_PUBLIC_RECEIPT_TIMESTAMP") from exc
    require(timestamp.tzinfo is not None, "AUDIT_PUBLIC_RECEIPT_TIMESTAMP")
    require(
        receipt["builder_commit"] == authorization["authorized_control_commit"]
        and receipt["builder_git_blob"] == authorization["authorized_control_source_blob"]
        and receipt["builder_source_sha256"] == authorization["authorized_control_source_raw_sha256"],
        "AUDIT_CONTROL_CROSS_BINDING",
    )
    return receipt


def audit_locator_before_private(
    repo_root: Path,
    private_path: Path,
    locator_path: Path,
    public_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    repo = repo_root.resolve(strict=True)
    require(not private_path.is_symlink() and private_path.is_file(), "AUDIT_PRIVATE_CUSTODY")
    require(not locator_path.is_symlink() and locator_path.is_file(), "AUDIT_LOCATOR_CUSTODY")
    private = private_path.resolve(strict=True)
    locator_resolved = locator_path.resolve(strict=True)
    require(private != repo and repo not in private.parents, "AUDIT_PRIVATE_INSIDE_GIT")
    require(locator_resolved != repo and repo not in locator_resolved.parents, "AUDIT_LOCATOR_INSIDE_GIT")
    locator = load_json(locator_resolved, "AUDIT_LOCATOR_READ")
    require(set(locator) == LOCATOR_KEYS, "AUDIT_LOCATOR_SCHEMA")
    verify_self_hash(locator, EXPECTED_LOCATOR_HASH, "AUDIT_LOCATOR_HASH")
    try:
        embedded_private = Path(str(locator.get("absolute_private_authority_path"))).resolve(strict=True)
    except Exception as exc:
        raise AuditError("AUDIT_LOCATOR_CUSTODY") from exc
    expected = {
        "artifact_type": "task039e3_r2r_utility_normal_only_local_locator_manifest_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "private_authority_hash": EXPECTED_PRIVATE_REGISTRY_HASH,
        "public_receipt_hash": EXPECTED_PUBLIC_RECEIPT_HASH,
        "builder_commit": CONTROL_SOURCE_COMMIT,
        "local_only": True,
        "must_not_be_committed": True,
        "control_revision": CONTROL_REVISION,
        "scientific_v1_commit": SCIENTIFIC_V1_COMMIT,
        "control_source_commit": CONTROL_SOURCE_COMMIT,
        "control_source_git_blob": CONTROL_SOURCE_BLOB,
        "control_source_raw_sha256": CONTROL_SOURCE_RAW_SHA256,
        "execution_authorization_hash": AUTHORIZATION_ARTIFACT_HASH,
        "materialization_authorized": True,
    }
    require(all(locator.get(key) == value for key, value in expected.items()), "AUDIT_LOCATOR_BINDING")
    require(
        embedded_private == private
        and private != repo
        and repo not in private.parents
        and locator.get("created_at") == public_receipt.get("execution_timestamp")
        and locator.get("builder_commit") == public_receipt.get("builder_commit")
        and locator.get("control_source_commit") == public_receipt.get("control_source_commit")
        and locator.get("control_source_git_blob") == public_receipt.get("control_source_git_blob")
        and locator.get("control_source_raw_sha256") == public_receipt.get("control_source_raw_sha256")
        and locator.get("execution_authorization_hash") == public_receipt.get("execution_authorization_hash")
        and locator.get("materialization_authorized") is public_receipt.get("materialization_authorized"),
        "AUDIT_LOCATOR_CROSS_BINDING",
    )
    require(
        type(locator.get("local_only")) is bool
        and type(locator.get("must_not_be_committed")) is bool
        and type(locator.get("materialization_authorized")) is bool,
        "AUDIT_LOCATOR_TYPE",
    )
    return locator


def _walk_keys_and_values(value: object) -> tuple[list[str], list[str]]:
    keys: list[str] = []
    strings: list[str] = []
    if type(value) is dict:
        for key, child in value.items():
            keys.append(str(key))
            child_keys, child_strings = _walk_keys_and_values(child)
            keys.extend(child_keys)
            strings.extend(child_strings)
    elif type(value) is list:
        for child in value:
            child_keys, child_strings = _walk_keys_and_values(child)
            keys.extend(child_keys)
            strings.extend(child_strings)
    elif type(value) is str:
        strings.append(value)
    return keys, strings


def audit_public_artifact_leakage(repo_root: Path) -> dict[str, Any]:
    reports = repo_root / "docs" / "task_reports"
    forbidden_keys = {
        "numeric_value",
        "raw_values",
        "registry_records",
        "absolute_private_authority_path",
        "private_path",
        "attack_intervals",
        "credentials",
    }

    def schema_findings(value: object) -> int:
        observed = 0
        if type(value) is dict:
            for key, child in value.items():
                if key in forbidden_keys:
                    observed += 1
                # Role names and the word ``records`` are allowed only as
                # structural count fields; they may not carry values or rows.
                if key in {
                    "source_step_threshold",
                    "source_stability_tolerance",
                    "target_noise_scale",
                } and not (type(child) is int and child == 42):
                    observed += 1
                if key == "records" and type(child) is not int:
                    observed += 1
                observed += schema_findings(child)
        elif type(value) is list:
            observed += sum(schema_findings(child) for child in value)
        return observed

    findings = 0
    checked = 0
    for name in PUBLIC_FILES:
        path = reports / name
        require(path.is_file(), "AUDIT_PUBLIC_ARTIFACT_MISSING")
        checked += 1
        if path.suffix == ".json":
            document = load_json(path, "AUDIT_PUBLIC_ARTIFACT_READ")
            verify_self_hash(document, PUBLIC_JSON_HASHES[name], "AUDIT_PUBLIC_ARTIFACT_HASH")
            keys, strings = _walk_keys_and_values(document)
            findings += schema_findings(document)
            findings += sum(1 for value in strings if is_absolute_string(value))
        else:
            text = path.read_text(encoding="utf-8")
            findings += int("numeric_value" in text)
            findings += int("absolute_private_authority_path" in text)
            findings += int(any(marker in text for marker in ("C:\\\\", "C:/Users/", "/home/")))
    require(findings == 0, "AUDIT_PUBLIC_LEAKAGE")
    return {"files_checked": checked, "findings": findings}


def run_independent_audit(
    repo_root: Path,
    private_path: Path,
    locator_path: Path,
) -> dict[str, Any]:
    repo = repo_root.resolve(strict=True)
    common = reconstruct_common42(repo)
    authorization_bundle = audit_authorization(repo)
    authorization = authorization_bundle["authorization"]
    public_receipt = audit_public_receipt(repo, authorization)
    locator = audit_locator_before_private(repo, private_path, locator_path, public_receipt)

    # The authoritative private registry is opened exactly once by the
    # independent oracle, only after the public and locator custody gates pass.
    registry = load_json(private_path.resolve(strict=True), "AUDIT_PRIVATE_REGISTRY_READ")
    registry_summary = audit_registry_document(registry, common)
    require(
        registry_summary["private_registry_hash"] == locator["private_authority_hash"]
        == public_receipt["private_registry_content_hash"],
        "AUDIT_PRIVATE_PUBLIC_LOCATOR_CROSS_BINDING",
    )
    mutations = run_mutation_audit(registry, common)
    leakage = audit_public_artifact_leakage(repo)
    return {
        "status": "passed_independent_materialized_authority_oracle",
        "private_registry": registry_summary,
        "locator": {
            "resolved": True,
            "artifact_hash": EXPECTED_LOCATOR_HASH,
            "outside_git": True,
            "cross_binding": "PASS",
        },
        "public_receipt": {
            "artifact_hash": EXPECTED_PUBLIC_RECEIPT_HASH,
            "cross_binding": "PASS",
            "written_last": True,
        },
        "common": {
            "relations": len(common["relations"]),
            "sources": len(common["sources"]),
            "targets": len(common["targets"]),
            "feature_union": len(common["feature_union"]),
            "references": len(common["references"]),
            "authority_definition_hash": common["authority_definition_hash"],
            "utility_binding_set_hash": common["utility_binding_set_hash"],
        },
        "authorization": {
            "artifact_hash": AUTHORIZATION_ARTIFACT_HASH,
            "receipt_hash": authorization_bundle["authorization_receipt_hash"],
            "control_source_commit": CONTROL_SOURCE_COMMIT,
            "control_source_blob": CONTROL_SOURCE_BLOB,
            "control_source_raw_sha256": CONTROL_SOURCE_RAW_SHA256,
            "cross_binding": "PASS",
        },
        "normal_input_provenance": {"train1": "PASS", "train2": "PASS", "raw_files_read": 0},
        "mutation_audit": mutations,
        "public_leakage": leakage,
        "access_counters": {
            "private_registry_reads": 1,
            "private_numeric_values_inspected": True,
            "hai_train_value_accesses": 0,
            "hai_test_accesses": 0,
            "label_accesses": 0,
            "attack_interval_accesses": 0,
            "utility_computations": 0,
            "provider_calls": 0,
            "api_key_access": False,
            "scientific_llm_calls": 0,
            "materializer_invocations": 0,
            "recalibrations": 0,
            "network_requests": 0,
        },
    }


def build_synthetic_registry(common: Mapping[str, Any]) -> dict[str, Any]:
    """Build public synthetic data for unit tests; never uses private values."""

    records: list[dict[str, Any]] = []
    for relation in common["relations"]:
        for role in UTILITY_ROLES:
            if role == "source_step_threshold":
                value: int | float = 1.0
            elif role == "source_stability_tolerance":
                value = 0.5
            elif role == "target_noise_scale":
                value = 2.0
            else:
                value = FROZEN_CONSTANTS[role]
            record = {
                "schema_version": SCHEMA_VERSION,
                "authority_version": AUTHORITY_VERSION,
                "relation_identity": relation["relation_identity"],
                "relation_binding_hash": relation["relation_binding_hash"],
                "semantic_execution_hash": relation["semantic_execution_hash"],
                "numeric_role": role,
                "new_reference_identity": reference_identity(relation, role),
                "numeric_value": value,
                "calibration_policy_version": CALIBRATION_POLICY_VERSION,
                "normal_train1_identity": TRAIN1_SHA256,
                "normal_train2_identity": TRAIN2_SHA256,
                "provenance_identity": provenance_identity(relation, role),
            }
            record["record_hash"] = stable_hash(record)
            records.append(record)
    document = {
        "artifact_type": "task039e3_r2r_utility_normal_only_private_registry_v1",
        "schema_version": SCHEMA_VERSION,
        "authority_version": AUTHORITY_VERSION,
        "authority_lineage": AUTHORITY_LINEAGE,
        "execution_control_revision": CONTROL_REVISION,
        "historical_e1_identity_restored": False,
        "historical_numeric_identity_restored": False,
        "construction_result_validity": "UNCHANGED",
        "terminal_custody_validity": "UNCHANGED",
        "common42_authority_hash": COMMON42_AUTHORITY_HASH,
        "executable_equivalence_hash": EXECUTABLE_EQUIVALENCE_HASH,
        "authority_definition_hash": AUTHORITY_DEFINITION_HASH,
        "normal_input_identity_set_hash": NORMAL_INPUT_IDENTITY_SET_HASH,
        "calibration_policy_version": CALIBRATION_POLICY_VERSION,
        "calibration_policy_hash": CALIBRATION_POLICY_HASH,
        "relation_count": 42,
        "record_count": 420,
        "unique_logical_key_count": 420,
        "status": "complete_private_registry_pending_public_receipt",
        "records": records,
    }
    document["artifact_hash"] = stable_hash(document)
    return document


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the sanitized independent materialized-authority audit")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--private-registry", type=Path, required=True)
    parser.add_argument("--locator", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run_independent_audit(args.repository_root, args.private_registry, args.locator)
    except AuditError as exc:
        print(canonical_json({"status": "blocked", "error_code": str(exc)}))
        return 1
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
