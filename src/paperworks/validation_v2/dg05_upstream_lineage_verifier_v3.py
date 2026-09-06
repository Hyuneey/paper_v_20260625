"""Independent raw-root-to-result replay for DG05 Executable V5.

This module never calls the production projection, scenario, denominator, or
metric-primitive I/O builders.  It authenticates their immutable roots,
independently reconstructs projection/scenario/eligibility content, then uses
the pure frozen metric arithmetic for the final comparison target.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Mapping

from .dg05_dec031_v1 import build_physical_timeline_authority_v1, require_valid_physical_timeline_v1
from .dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1, validate_self_hashed
from .dg05_metric_surface_v1 import canonical_bytes, self_hashed
from .dg05_upstream_lineage_verifier_v2 import (
    UpstreamPanelReplayPathsV2,
    reconstruct_metric_primitive_from_upstream_v2,
)
from .multipanel_custody_v1 import (
    FROZEN_DATASET_VERSIONS_V2,
    FROZEN_PANEL_ORDER_V2,
    frozen_feature_allowlist_authorities_v2,
)


class DG05UpstreamVerifierV3Error(ValueError):
    pass


@dataclass(frozen=True)
class RootToResultReplayPathsV3:
    intermediate: UpstreamPanelReplayPathsV2
    physical_file_authority_path: Path
    raw_physical_paths: Mapping[str, Path]
    projection_authority_paths: Mapping[str, Path]
    timestamp_authority_paths: Mapping[str, Path]
    raw_scenario_source_paths: Mapping[str, Path]
    custodian_policy_path: Path
    custodian_request_path: Path
    lease_issued_state_path: Path
    lease_consumed_path: Path
    custodian_invocation_path: Path
    custodian_output_path: Path
    full_process_scope_path: Path


def _load(path: Path, schema: str, *, hashed: bool = True) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05UpstreamVerifierV3Error("CANONICAL_ROOT_JSON_REQUIRED") from exc
    if type(value) is not dict or value.get("schema") != schema or raw != canonical_bytes(value) + b"\n":
        raise DG05UpstreamVerifierV3Error(f"ROOT_SCHEMA_REPLAY_FAILED:{schema}")
    if hashed:
        try:
            validate_self_hashed(value)
        except ValueError as exc:
            raise DG05UpstreamVerifierV3Error(f"ROOT_SELF_HASH_REPLAY_FAILED:{schema}") from exc
    return value


def _byte_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _independent_projection(
    *, raw_path: Path, projection_path: Path, physical: Mapping[str, Any],
    projection: Mapping[str, Any], timestamp: Mapping[str, Any], panel_id: str,
    source_commit: str,
) -> tuple[str, ...]:
    if raw_path.is_symlink() or projection_path.is_symlink() or _byte_hash(raw_path) != physical["raw_container_hash"]:
        raise DG05UpstreamVerifierV3Error("RAW_PHYSICAL_SOURCE_BYTE_MISMATCH")
    allowlist = frozen_feature_allowlist_authorities_v2()[panel_id]
    allowlist.validate()
    if projection.get("allowlist_authority_hash") != allowlist.document()["self_hash"]:
        raise DG05UpstreamVerifierV3Error("FROZEN_ALLOWLIST_AUTHORITY_MISMATCH")
    raw_bytes = raw_path.read_bytes()
    lines = raw_bytes.splitlines()
    if not lines:
        raise DG05UpstreamVerifierV3Error("RAW_PHYSICAL_SCHEMA_REPLAY_FAILED")
    delimiter = b"," if lines[0].count(b",") >= lines[0].count(b";") else b";"
    try:
        header = [field.decode("utf-8") for field in lines[0].split(delimiter)]
    except UnicodeDecodeError as exc:
        raise DG05UpstreamVerifierV3Error("RAW_PHYSICAL_SCHEMA_REPLAY_FAILED") from exc
    selected = (allowlist.timestamp_id, *allowlist.feature_ids)
    if len(header) != len(set(header)) or any(name not in header for name in selected):
        raise DG05UpstreamVerifierV3Error("RAW_ALLOWLIST_FIELD_AUTHORITY_MISMATCH")
    indices = tuple(header.index(name) for name in selected)
    output = bytearray(canonical_bytes(list(selected)) + b"\n")
    timestamps: list[str] = []
    for raw_line in lines[1:]:
        fields = raw_line.split(delimiter)
        if len(fields) != len(header):
            raise DG05UpstreamVerifierV3Error("RAW_ROW_WIDTH_MISMATCH")
        try:
            timestamp_value = fields[indices[0]].decode("utf-8")
            numbers = [float(fields[index].decode("ascii")) for index in indices[1:]]
        except (UnicodeDecodeError, ValueError) as exc:
            raise DG05UpstreamVerifierV3Error("APPROVED_FEATURE_NUMERIC_REPLAY_FAILED") from exc
        if not all(math.isfinite(value) for value in numbers):
            raise DG05UpstreamVerifierV3Error("APPROVED_FEATURE_NONFINITE")
        output.extend(canonical_bytes([timestamp_value, *numbers]) + b"\n")
        timestamps.append(timestamp_value)
    expected_projection = bytes(output)
    physical_identity_hash = sha256(canonical_bytes(dict(physical))).hexdigest()
    if (
        sha256(canonical_bytes(header)).hexdigest() != physical["header_hash"]
        or projection.get("raw_physical_file_hash") != physical_identity_hash
        or projection.get("header_hash") != physical["header_hash"]
        or projection.get("row_count") != len(timestamps)
        or projection.get("feature_order_hash") != sha256(canonical_bytes(list(allowlist.feature_ids))).hexdigest()
        or projection.get("projection_hash") != sha256(expected_projection).hexdigest()
        or projection_path.read_bytes() != expected_projection
        or timestamp.get("physical_file_authority_hash") != physical_identity_hash
        or timestamp.get("projection_hash") != projection["projection_hash"]
        or timestamp.get("row_count") != len(timestamps)
        or projection.get("timestamp_authority_hash") != timestamp["self_hash"]
        or projection.get("panel_id") != panel_id
        or projection.get("file_id") != physical["file_id"]
        or timestamp.get("panel_id") != panel_id
        or timestamp.get("file_id") != physical["file_id"]
        or projection.get("source_commit") != source_commit
        or timestamp.get("source_commit") != source_commit
    ):
        raise DG05UpstreamVerifierV3Error("RAW_TO_PROJECTION_LINEAGE_MISMATCH")
    timeline = build_physical_timeline_authority_v1(
        panel_id=panel_id, file_id=physical["file_id"], timestamps=timestamps,
        physical_file_authority_hash=physical_identity_hash,
        projection_authority_hash=projection["projection_hash"], source_commit=source_commit)
    try:
        require_valid_physical_timeline_v1(timeline)
    except ValueError as exc:
        raise DG05UpstreamVerifierV3Error(str(exc)) from exc
    return tuple(timestamps)


def _replay_custodian_roots(
    *, paths: RootToResultReplayPathsV3, expected_release_manifest_hash: str,
    expected_global_freeze_hash: str, expected_invocation_hash: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    policy = _load(paths.custodian_policy_path, "custodian_resource_policy_authority_v2")
    issued = _load(paths.lease_issued_state_path, "dg05_production_chain_state_v4")
    consumed = _load(paths.lease_consumed_path, "label_scenario_lease_consumed_v2")
    invocation = _load(paths.custodian_invocation_path, "dg05_fresh_process_custodian_invocation_v1")
    output = _load(paths.custodian_output_path, "isolated_label_scenario_custodian_output_v2")
    raw_request = paths.custodian_request_path.read_bytes()
    try:
        request = json.loads(raw_request.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05UpstreamVerifierV3Error("CANONICAL_CUSTODIAN_REQUEST_REQUIRED") from exc
    if raw_request != canonical_bytes(request) + b"\n" or request.get("schema") != "isolated_label_scenario_custodian_request_v2":
        raise DG05UpstreamVerifierV3Error("CANONICAL_CUSTODIAN_REQUEST_REQUIRED")
    lease = request.get("lease_receipt")
    if type(lease) is not dict:
        raise DG05UpstreamVerifierV3Error("LEASE_RECEIPT_REQUIRED")
    try:
        validate_self_hashed(lease)
    except ValueError as exc:
        raise DG05UpstreamVerifierV3Error("LEASE_SELF_HASH_REPLAY_FAILED") from exc
    token_hash = sha256(str(request.get("opaque_lease", "")).encode("utf-8")).hexdigest()
    if (
        invocation["self_hash"] != expected_invocation_hash
        or invocation.get("request_byte_hash") != sha256(raw_request).hexdigest()
        or invocation.get("resource_policy_byte_hash") != _byte_hash(paths.custodian_policy_path)
        or invocation.get("resource_policy_hash") != policy["self_hash"]
        or invocation.get("predecessor_state_hash") != issued["self_hash"]
        or invocation.get("global_freeze_hash") != expected_global_freeze_hash
        or invocation.get("release_manifest_hash") != expected_release_manifest_hash
        or invocation.get("output_self_hash") != output["self_hash"]
        or invocation.get("output_byte_hash") != _byte_hash(paths.custodian_output_path)
        or invocation.get("consume_receipt_hash") != consumed["self_hash"]
        or invocation.get("custodian_pid") == invocation.get("custodian_parent_pid")
        or lease.get("token_hash") != token_hash
        or lease.get("issue_count") != 1
        or lease.get("consume_limit") != 1
        or consumed.get("consume_count") != 1
        or consumed.get("token_hash") != token_hash
        or consumed.get("issue_receipt_hash") != lease["self_hash"]
        or request.get("resource_policy_hash") != policy["self_hash"]
        or request.get("global_freeze_hash") != expected_global_freeze_hash
        or request.get("executable_manifest_hash") != expected_release_manifest_hash
        or output.get("prediction_capability") is not False
        or output.get("lease_consumed_hash") != consumed["self_hash"]
    ):
        raise DG05UpstreamVerifierV3Error("CUSTODIAN_ROOT_REPLAY_FAILURE")
    sources = policy.get("approved_sources")
    if type(sources) is not list or set(paths.raw_scenario_source_paths) != {row.get("source_id") for row in sources}:
        raise DG05UpstreamVerifierV3Error("CUSTODIAN_SOURCE_CENSUS_MISMATCH")
    bindings = {
        (row["source_id"], row["panel_id"], row["dataset_version"], row["file_id"]): row
        for row in request.get("allowed_scenario_bindings", ())
    }
    if len(bindings) != len(request.get("allowed_scenario_bindings", ())):
        raise DG05UpstreamVerifierV3Error("CUSTODIAN_BINDING_DUPLICATE")
    reconstructed: list[dict[str, Any]] = []
    source_receipts = []
    for source in sorted(sources, key=lambda row: row["source_id"]):
        path = paths.raw_scenario_source_paths[source["source_id"]]
        if (
            path.is_symlink()
            or path.resolve() != Path(source["path"]).resolve()
            or _byte_hash(path) != source["byte_hash"]
            or source["source_id"] not in request.get("approved_source_ids", ())
        ):
            raise DG05UpstreamVerifierV3Error("RAW_SCENARIO_SOURCE_BYTE_MISMATCH")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DG05UpstreamVerifierV3Error("RAW_SCENARIO_SOURCE_SCHEMA_MISMATCH") from exc
        if type(raw) is not dict or set(raw) != {"schema", "records"} or raw.get("schema") != "synthetic_raw_official_scenario_fixture_v2":
            raise DG05UpstreamVerifierV3Error("RAW_SCENARIO_SOURCE_SCHEMA_MISMATCH")
        for row in raw["records"]:
            key = (source["source_id"], row["panel_id"], row["dataset_version"], row["file_id"])
            binding = bindings.get(key)
            if binding is None:
                raise DG05UpstreamVerifierV3Error("RAW_SCENARIO_BINDING_MISMATCH")
            reconstructed.append({
                **row,
                "physical_file_authority_hash": binding["physical_file_authority_hash"],
                "timestamp_authority_hash": binding["timestamp_authority_hash"],
                "official_source_hash": binding["official_source_hash"],
            })
        source_receipts.append({"source_id": source["source_id"], "byte_hash": source["byte_hash"],
                                "official_source_hash": source["official_source_hash"]})
    reconstructed.sort(key=lambda row: (row["panel_id"], row["file_id"], row["scenario_id"]))
    if (
        output.get("records") != reconstructed
        or output.get("source_receipts") != source_receipts
        or output.get("allowed_scenario_binding_hash") != sha256(canonical_bytes(request["allowed_scenario_bindings"])).hexdigest()
        or output.get("resource_policy_hash") != policy["self_hash"]
        or output.get("nominal_counts") != request.get("nominal_counts")
    ):
        raise DG05UpstreamVerifierV3Error("CUSTODIAN_OUTPUT_ROOT_DIVERGENCE")
    return output, request, invocation


def _scenario_document(
    *, output: Mapping[str, Any], global_freeze_hash: str, source_commit: str,
) -> dict[str, Any]:
    records = []
    for row in output["records"]:
        records.append(self_hashed({
            "schema": "official_scenario_record_v1",
            "panel_id": row["panel_id"], "dataset_version": row["dataset_version"],
            "file_id": row["file_id"], "scenario_id": row["scenario_id"],
            "closed_intervals": row["closed_intervals"],
            "attacked_identities": row["attacked_identities"],
            "explicit_affected_processes": row["explicit_affected_processes"],
            "physical_file_authority_hash": row["physical_file_authority_hash"],
            "timestamp_authority_hash": row["timestamp_authority_hash"],
            "official_source_hash": row["official_source_hash"],
        }))
    records.sort(key=lambda row: (
        row["panel_id"], row["dataset_version"], row["file_id"], row["scenario_id"],
        row["closed_intervals"], row["attacked_identities"], row["explicit_affected_processes"],
        row["physical_file_authority_hash"], row["timestamp_authority_hash"], row["official_source_hash"],
    ))
    return self_hashed({
        "schema": "frozen_scenario_authority_v1",
        "records": records,
        "nominal_counts": output["nominal_counts"],
        "lease_completion_hash": output["self_hash"],
        "global_freeze_hash": global_freeze_hash,
        "source_commit": source_commit,
        "method_inputs": False,
        "authority_mode": output["authority_mode"],
    })


def _denominator_document(
    *, scenario: Mapping[str, Any], scope: Mapping[str, Any], p1_custodian_hash: str,
) -> dict[str, Any]:
    membership = {
        (row["dataset_version"], row["canonical_identity"]):
        ("P1" if row["p1_membership"] == "YES" else "UNRESOLVED" if row["p1_membership"] == "UNRESOLVED" else row["official_process"])
        for row in scope["points"]
    }
    records = []
    for row in scenario["records"]:
        observed = [membership.get((row["dataset_version"], identity), "UNRESOLVED")
                    for identity in row["attacked_identities"]]
        if "P1" in observed:
            primary, reason = "P1_ELIGIBLE", "DIRECT_VERIFIED_P1_IDENTITY"
        elif "UNRESOLVED" in observed:
            primary, reason = "UNRESOLVED", "AT_LEAST_ONE_IDENTITY_UNRESOLVED"
        else:
            primary, reason = "OUT_OF_SCOPE", "ALL_IDENTITIES_VERIFIED_NON_P1"
        records.append(self_hashed({
            "schema": "p1_eligibility_record_v3",
            "scenario_record_hash": row["self_hash"],
            "panel_id": row["panel_id"], "scenario_id": row["scenario_id"],
            "primary_status": primary,
            "secondary_cross_process_p1_relevant": "P1" in row["explicit_affected_processes"] and primary != "P1_ELIGIBLE",
            "reason": reason, "unresolved_identity_count": observed.count("UNRESOLVED"),
            "full_scope_hash": scope["self_hash"], "p1_custodian_v3_hash": p1_custodian_hash,
        }))
    panels = []
    for panel in FROZEN_PANEL_ORDER_V2:
        rows = [row for row in records if row["panel_id"] == panel]
        panels.append({
            "panel_id": panel, "nominal_count": len(rows),
            "p1_eligible_ids": [row["scenario_id"] for row in rows if row["primary_status"] == "P1_ELIGIBLE"],
            "out_of_scope_ids": [row["scenario_id"] for row in rows if row["primary_status"] == "OUT_OF_SCOPE"],
            "unresolved_ids": [row["scenario_id"] for row in rows if row["primary_status"] == "UNRESOLVED"],
            "cross_process_secondary_ids": [row["scenario_id"] for row in rows if row["secondary_cross_process_p1_relevant"]],
        })
    return self_hashed({
        "schema": "denominator_authority_v1", "scenario_authority_hash": scenario["self_hash"],
        "full_process_scope_hash": scope["self_hash"], "p1_custodian_v3_hash": p1_custodian_hash,
        "records": records, "panels": panels, "prediction_inputs": False,
    })


def reconstruct_metric_primitive_from_roots_v3(
    *, panel_id: str, paths: RootToResultReplayPathsV3,
    expected_release_manifest_hash: str, expected_dec031_binding_hash: str,
    expected_normal_source_registry_hash: str, expected_global_freeze_hash: str,
    expected_physical_authority_hash: str, expected_custodian_invocation_hash: str,
    expected_full_process_scope_hash: str, expected_p1_custodian_hash: str,
    source_commit: str,
) -> tuple[dict[str, Any], dict[str, bool]]:
    physical = _load(paths.physical_file_authority_path, "multipanel_physical_attack_file_authority_v2")
    if physical["self_hash"] != expected_physical_authority_hash:
        raise DG05UpstreamVerifierV3Error("RAW_PHYSICAL_AUTHORITY_ROOT_MISMATCH")
    physical_rows = {(row["panel_id"], row["file_id"]): row for row in physical["files"]}
    if len(physical_rows) != len(physical["files"]):
        raise DG05UpstreamVerifierV3Error("RAW_PHYSICAL_AUTHORITY_DUPLICATE")
    file_ids = {row["file_id"] for row in physical["files"] if row["panel_id"] == panel_id}
    if set(paths.raw_physical_paths) != file_ids or set(paths.projection_authority_paths) != file_ids or set(paths.timestamp_authority_paths) != file_ids:
        raise DG05UpstreamVerifierV3Error("RAW_PROJECTION_ROOT_CENSUS_MISMATCH")
    for file_id in sorted(file_ids):
        projection = _load(paths.projection_authority_paths[file_id], "feature_only_projection_authority_v1")
        timestamp = _load(paths.timestamp_authority_paths[file_id], "timestamp_coordinate_authority_v1")
        _independent_projection(
            raw_path=paths.raw_physical_paths[file_id],
            projection_path=paths.intermediate.projection_paths[file_id],
            physical=physical_rows[(panel_id, file_id)], projection=projection,
            timestamp=timestamp, panel_id=panel_id, source_commit=source_commit)
    output, _, _ = _replay_custodian_roots(
        paths=paths, expected_release_manifest_hash=expected_release_manifest_hash,
        expected_global_freeze_hash=expected_global_freeze_hash,
        expected_invocation_hash=expected_custodian_invocation_hash)
    scenario_expected = _scenario_document(
        output=output, global_freeze_hash=expected_global_freeze_hash, source_commit=source_commit)
    scenario_actual = _load(paths.intermediate.scenario_authority_path, "frozen_scenario_authority_v1")
    if scenario_actual != scenario_expected:
        raise DG05UpstreamVerifierV3Error("SCENARIO_ROOT_REPLAY_FAILURE")
    scope = _load(paths.full_process_scope_path, "full_process_scope_authority_v1")
    if scope["self_hash"] != expected_full_process_scope_hash:
        raise DG05UpstreamVerifierV3Error("FROZEN_P1_SCOPE_ROOT_MISMATCH")
    denominator_expected = _denominator_document(
        scenario=scenario_expected, scope=scope, p1_custodian_hash=expected_p1_custodian_hash)
    denominator_actual = _load(paths.intermediate.denominator_authority_path, "denominator_authority_v1")
    if denominator_actual != denominator_expected:
        raise DG05UpstreamVerifierV3Error("DENOMINATOR_SCOPE_REPLAY_FAILURE")
    primitive = reconstruct_metric_primitive_from_upstream_v2(
        panel_id=panel_id, paths=paths.intermediate,
        expected_release_manifest_hash=expected_release_manifest_hash,
        expected_dec031_binding_hash=expected_dec031_binding_hash,
        expected_normal_source_registry_hash=expected_normal_source_registry_hash,
        expected_global_freeze_hash=expected_global_freeze_hash, source_commit=source_commit)
    flags = {
        "raw_physical_source_bytes_reopened": True,
        "projection_bytes_reopened": True,
        "projection_independently_replayed": True,
        "timeline_independently_validated": True,
        "prediction_bytes_reopened": True,
        "rule_runtime_traces_reopened": True,
        "global_freeze_reopened": True,
        "raw_official_scenario_source_bytes_reopened": True,
        "custodian_policy_reopened": True,
        "custodian_request_reopened": True,
        "lease_issue_and_consume_reopened": True,
        "fresh_process_invocation_reopened": True,
        "custodian_output_reopened": True,
        "scenario_independently_reconstructed": True,
        "frozen_full_process_scope_reopened": True,
        "denominator_independently_reconstructed": True,
        "normal_source_bytes_reopened": True,
        "final_metric_primitive_reconstructed": True,
    }
    return primitive, flags


def verify_asserted_primitive_from_roots_v3(
    *, panel_id: str, paths: RootToResultReplayPathsV3,
    expected_release_manifest_hash: str, expected_dec031_binding_hash: str,
    expected_normal_source_registry_hash: str, expected_global_freeze_hash: str,
    expected_physical_authority_hash: str, expected_custodian_invocation_hash: str,
    expected_full_process_scope_hash: str, expected_p1_custodian_hash: str,
    source_commit: str,
) -> dict[str, Any]:
    reconstructed, flags = reconstruct_metric_primitive_from_roots_v3(
        panel_id=panel_id, paths=paths,
        expected_release_manifest_hash=expected_release_manifest_hash,
        expected_dec031_binding_hash=expected_dec031_binding_hash,
        expected_normal_source_registry_hash=expected_normal_source_registry_hash,
        expected_global_freeze_hash=expected_global_freeze_hash,
        expected_physical_authority_hash=expected_physical_authority_hash,
        expected_custodian_invocation_hash=expected_custodian_invocation_hash,
        expected_full_process_scope_hash=expected_full_process_scope_hash,
        expected_p1_custodian_hash=expected_p1_custodian_hash,
        source_commit=source_commit)
    asserted = _load(paths.intermediate.asserted_primitive_path, "metric_surface_primitives_v2")
    if asserted != reconstructed:
        raise DG05UpstreamVerifierV3Error("ASSERTED_PRIMITIVE_DISAGREES_WITH_RAW_ROOTS")
    if not all(flags.values()):
        raise DG05UpstreamVerifierV3Error("INCOMPLETE_ROOT_REPLAY")
    return self_hashed({
        "schema": "dg05_root_to_result_upstream_verification_v3",
        "status": "PASS",
        "panel_id": panel_id,
        "release_manifest_hash": expected_release_manifest_hash,
        "physical_authority_hash": expected_physical_authority_hash,
        "custodian_invocation_hash": expected_custodian_invocation_hash,
        "full_process_scope_hash": expected_full_process_scope_hash,
        "normal_source_registry_hash": expected_normal_source_registry_hash,
        "asserted_primitive_hash": asserted["self_hash"],
        "root_replay_flags": flags,
        "source_commit": source_commit,
    })


__all__ = [
    "DG05UpstreamVerifierV3Error",
    "RootToResultReplayPathsV3",
    "reconstruct_metric_primitive_from_roots_v3",
    "verify_asserted_primitive_from_roots_v3",
]
