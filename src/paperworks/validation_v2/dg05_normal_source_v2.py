"""DEC-031 normal-burden source bundles and independent replay.

The persisted bundle is deliberately upstream of metric decimals: it contains
the exact normal timestamp vector, dense method alarms, and (for Rule-capable
methods) complete per-Rule runtime evidence.  Callers cannot inject a burden
value.  This module has no data discovery, fitting, provider, or attack-data
interface.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from .dg05_dec031_v1 import (
    DG05Dec031Error,
    build_physical_timeline_authority_v1,
    derive_four_way_runtime_census_v1,
    require_valid_physical_timeline_v1,
)
from .dg05_production_chain_v1 import canonical_bytes_v1, digest_v1, self_hashed_v1


class DG05NormalSourceError(ValueError):
    """Raised when immutable normal-source lineage is incomplete or altered."""


RULE_CAPABLE_METHODS = frozenset(
    {
        "M1_T0_RULE_ONLY",
        "M2_T2_RULE_ONLY",
        "M3_PCA_PLUS_T0",
        "M4_PCA_PLUS_T2",
        "ISOLATION_FOREST_PLUS_T2",
        "V2A_RULE_ONLY_REFERENCE",
        "HISTORICAL_PCA_PLUS_V2A_CONTINUITY",
    }
)


def _hash(value: Any, field: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise DG05NormalSourceError(f"SHA256_REQUIRED:{field}")
    return value


def build_normal_source_bundle_v2(
    *,
    component_id: str,
    panel_id: str,
    dataset_version: str,
    method_id: str,
    file_id: str,
    component_role: str,
    authority_class: str,
    method_authority_hash: str,
    physical_file_authority_hash: str,
    projection_authority_hash: str,
    timestamps: Sequence[str],
    alarms: Sequence[bool],
    configured_rule_sources: Mapping[str, str] | None,
    runtime_trace: Mapping[str, Any] | None,
    source_commit: str,
) -> dict[str, Any]:
    """Create the exact private source object; no metric rate is accepted."""
    if any(type(value) is not str or not value for value in (
        component_id, panel_id, dataset_version, method_id, file_id,
        component_role, authority_class, source_commit,
    )):
        raise DG05NormalSourceError("NORMAL_SOURCE_IDENTITY_REQUIRED")
    for field, value in (
        ("method_authority_hash", method_authority_hash),
        ("physical_file_authority_hash", physical_file_authority_hash),
        ("projection_authority_hash", projection_authority_hash),
    ):
        _hash(value, field)
    if len(timestamps) != len(alarms) or not timestamps:
        raise DG05NormalSourceError("NORMAL_SOURCE_ROW_CENSUS_MISMATCH")
    if any(type(value) is not bool for value in alarms):
        raise DG05NormalSourceError("DENSE_BOOLEAN_NORMAL_ALARMS_REQUIRED")
    timeline = build_physical_timeline_authority_v1(
        panel_id=panel_id,
        file_id=file_id,
        timestamps=timestamps,
        physical_file_authority_hash=physical_file_authority_hash,
        projection_authority_hash=projection_authority_hash,
        source_commit=source_commit,
    )
    try:
        require_valid_physical_timeline_v1(timeline)
    except DG05Dec031Error as exc:
        raise DG05NormalSourceError(str(exc)) from exc

    rule_capable = method_id in RULE_CAPABLE_METHODS
    if rule_capable:
        if type(runtime_trace) is not dict or not configured_rule_sources:
            raise DG05NormalSourceError("EVIDENCE_MISSING:RULE_RUNTIME_SOURCE")
        trace = dict(runtime_trace)
        trace["file_id"] = file_id
        census = derive_four_way_runtime_census_v1(
            configured_rule_sources=configured_rule_sources,
            file_timestamps={file_id: timestamps},
            traces=[trace],
        )
        alarm_rows = [index for index, value in enumerate(alarms) if value]
        if trace["rule_alarm_rows"] != alarm_rows and method_id not in {
            "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2",
            "ISOLATION_FOREST_PLUS_T2", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY",
        }:
            raise DG05NormalSourceError("RULE_ONLY_ALARM_TRACE_MISMATCH")
        if method_id in {
            "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2",
            "ISOLATION_FOREST_PLUS_T2", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY",
        } and trace.get("rule_component_alarm_rows") != trace.get("rule_alarm_rows"):
            raise DG05NormalSourceError("FUSION_RULE_COMPONENT_PROVENANCE_REQUIRED")
    else:
        if runtime_trace is not None or configured_rule_sources not in (None, {}):
            raise DG05NormalSourceError("DETECTOR_RUNTIME_TRACE_PROHIBITED")
        trace = None
        census = None

    return self_hashed_v1(
        {
            "schema": "normal_burden_source_bundle_v2",
            "component_id": component_id,
            "panel_id": panel_id,
            "dataset_version": dataset_version,
            "method_id": method_id,
            "file_id": file_id,
            "component_role": component_role,
            "authority_class": authority_class,
            "method_authority_hash": method_authority_hash,
            "physical_file_authority_hash": physical_file_authority_hash,
            "projection_authority_hash": projection_authority_hash,
            "timeline_authority": timeline,
            "timestamps": list(timestamps),
            "alarms": list(alarms),
            "configured_rule_sources": None if configured_rule_sources is None else dict(sorted(configured_rule_sources.items())),
            "runtime_trace": trace,
            "runtime_census": census,
            "exposure_seconds": len(timestamps),
            "normal_label_values_parsed": 0,
            "normal_label_values_inspected": 0,
            "normal_label_values_validated": 0,
            "normal_label_values_filtered_on": 0,
            "normal_label_values_used": 0,
            "source_commit": source_commit,
        }
    )


def persist_normal_source_bundle_v2(path: Path, bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Atomically create, close, reopen, and hash one private source bundle."""
    _replay_bundle_document(bundle)
    if path.exists() or path.is_symlink():
        raise DG05NormalSourceError("APPEND_ONLY_NORMAL_SOURCE_CONFLICT")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    if temporary.exists():
        raise DG05NormalSourceError("STALE_NORMAL_SOURCE_TEMPORARY")
    payload = canonical_bytes_v1(bundle) + b"\n"
    with temporary.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    except FileExistsError as exc:
        raise DG05NormalSourceError("APPEND_ONLY_NORMAL_SOURCE_CONFLICT") from exc
    finally:
        if temporary.exists():
            temporary.unlink()
    if path.read_bytes() != payload:
        raise DG05NormalSourceError("NORMAL_SOURCE_REOPEN_MISMATCH")
    return self_hashed_v1(
        {
            "schema": "normal_burden_source_bundle_receipt_v2",
            "component_id": bundle["component_id"],
            "document_self_hash": bundle["self_hash"],
            "artifact_byte_hash": sha256(payload).hexdigest(),
            "byte_count": len(payload),
        }
    )


def build_normal_source_registry_v2(
    *,
    component_receipts: Sequence[Mapping[str, Any]],
    component_metadata: Sequence[Mapping[str, Any]],
    dec031_binding_hash: str,
    required_components: Sequence[Mapping[str, str]],
    source_commit: str,
) -> dict[str, Any]:
    """Build the public-safe complete component census."""
    _hash(dec031_binding_hash, "dec031_binding_hash")
    receipts = {row.get("component_id"): row for row in component_receipts}
    if len(receipts) != len(component_receipts) or None in receipts:
        raise DG05NormalSourceError("UNIQUE_NORMAL_SOURCE_RECEIPTS_REQUIRED")
    for receipt in component_receipts:
        if (
            receipt.get("schema") != "normal_burden_source_bundle_receipt_v2"
            or receipt.get("self_hash") != digest_v1({key: item for key, item in receipt.items() if key != "self_hash"})
        ):
            raise DG05NormalSourceError("NORMAL_SOURCE_RECEIPT_REPLAY_FAILED")
    rows = []
    for metadata in component_metadata:
        required = {
            "component_id", "panel_id", "dataset_version", "method_id",
            "file_id", "component_role", "authority_class",
            "method_authority_hash", "physical_file_authority_hash",
            "projection_authority_hash", "timeline_authority_hash",
        }
        if type(metadata) is not dict or set(metadata) != required:
            raise DG05NormalSourceError("NORMAL_SOURCE_METADATA_SCHEMA_REQUIRED")
        receipt = receipts.get(metadata["component_id"])
        if type(receipt) is not dict:
            raise DG05NormalSourceError("NORMAL_SOURCE_RECEIPT_CENSUS_MISMATCH")
        rows.append(
            {
                **dict(metadata),
                "document_self_hash": receipt["document_self_hash"],
                "artifact_byte_hash": receipt["artifact_byte_hash"],
                "artifact_byte_count": receipt["byte_count"],
            }
        )
    if len(rows) != len(receipts) or len({row["component_id"] for row in rows}) != len(rows):
        raise DG05NormalSourceError("NORMAL_SOURCE_RECEIPT_CENSUS_MISMATCH")
    roster_fields = ("component_id", "panel_id", "dataset_version", "method_id", "file_id", "component_role", "authority_class")
    required_roster = [dict(row) for row in required_components]
    if any(type(row) is not dict or set(row) != set(roster_fields) for row in required_roster):
        raise DG05NormalSourceError("EXACT_NORMAL_SOURCE_ROSTER_SCHEMA_REQUIRED")
    observed_roster = sorted(({field: row[field] for field in roster_fields} for row in rows), key=lambda row: row["component_id"])
    required_roster = sorted(required_roster, key=lambda row: row["component_id"])
    if (
        observed_roster != required_roster
        or len({row["component_id"] for row in required_roster}) != len(required_roster)
        or len({tuple(row[field] for field in roster_fields[1:]) for row in required_roster}) != len(required_roster)
    ):
        raise DG05NormalSourceError("COMPLETE_NORMAL_COMPONENT_ROSTER_REQUIRED")
    return self_hashed_v1(
        {
            "schema": "normal_burden_source_registry_v2",
            "status": "COMPLETE_SOURCE_LINEAGE",
            "dec031_binding_hash": dec031_binding_hash,
            "required_components": required_roster,
            "components": sorted(rows, key=lambda row: row["component_id"]),
            "component_count": len(rows),
            "private_paths_published": False,
            "normal_label_values_parsed": 0,
            "normal_label_values_used": 0,
            "attack_test_accesses": 0,
            "label_scenario_accesses": 0,
            "source_commit": source_commit,
        }
    )


def _replay_bundle_document(value: Mapping[str, Any]) -> None:
    if type(value) is not dict or value.get("schema") != "normal_burden_source_bundle_v2":
        raise DG05NormalSourceError("NORMAL_SOURCE_BUNDLE_SCHEMA_REQUIRED")
    if value.get("self_hash") != digest_v1({key: item for key, item in value.items() if key != "self_hash"}):
        raise DG05NormalSourceError("NORMAL_SOURCE_BUNDLE_SELF_HASH_MISMATCH")
    try:
        require_valid_physical_timeline_v1(value["timeline_authority"])
    except (KeyError, DG05Dec031Error) as exc:
        raise DG05NormalSourceError("NORMAL_SOURCE_TIMELINE_AUTHORITY_INVALID") from exc
    timestamps, alarms = value.get("timestamps"), value.get("alarms")
    if (
        type(timestamps) is not list
        or type(alarms) is not list
        or len(timestamps) != len(alarms)
        or len(timestamps) != value.get("exposure_seconds")
        or any(type(item) is not bool for item in alarms)
        or value["timeline_authority"].get("timestamp_vector_hash") != digest_v1(timestamps)
        or value["timeline_authority"].get("physical_file_authority_hash") != value.get("physical_file_authority_hash")
        or value["timeline_authority"].get("projection_authority_hash") != value.get("projection_authority_hash")
        or value["timeline_authority"].get("panel_id") != value.get("panel_id")
        or value["timeline_authority"].get("file_id") != value.get("file_id")
    ):
        raise DG05NormalSourceError("NORMAL_SOURCE_TIMESTAMP_PREDICTION_MISMATCH")
    rebuilt_timeline = build_physical_timeline_authority_v1(
        panel_id=value["panel_id"], file_id=value["file_id"], timestamps=timestamps,
        physical_file_authority_hash=value["physical_file_authority_hash"],
        projection_authority_hash=value["projection_authority_hash"],
        source_commit=value["source_commit"],
    )
    if rebuilt_timeline != value["timeline_authority"]:
        raise DG05NormalSourceError("NORMAL_SOURCE_TIMELINE_RECONSTRUCTION_MISMATCH")
    for field in (
        "normal_label_values_parsed", "normal_label_values_inspected",
        "normal_label_values_validated", "normal_label_values_filtered_on",
        "normal_label_values_used",
    ):
        if value.get(field) != 0:
            raise DG05NormalSourceError("NORMAL_LABEL_VALUE_CONTACT")
    method_id = value.get("method_id")
    if method_id in RULE_CAPABLE_METHODS:
        trace = value.get("runtime_trace")
        if type(trace) is not dict:
            raise DG05NormalSourceError("EVIDENCE_MISSING:RULE_RUNTIME_SOURCE")
        rule_rows = trace.get("rule_alarm_rows")
        if type(rule_rows) is not list or rule_rows != sorted(set(rule_rows)):
            raise DG05NormalSourceError("RULE_ALARM_ROW_PROVENANCE_REQUIRED")
        exact_sources: dict[str, set[str]] = {}
        configured_sources = value.get("configured_rule_sources")
        per_rule = trace.get("per_rule_runtime")
        if type(configured_sources) is not dict or type(per_rule) is not list:
            raise DG05NormalSourceError("EXACT_RULE_SOURCE_PROVENANCE_REQUIRED")
        for row in per_rule:
            if type(row) is not dict or row.get("source_id") != configured_sources.get(row.get("rule_id")):
                raise DG05NormalSourceError("EXACT_RULE_SOURCE_PROVENANCE_REQUIRED")
            for index in row.get("fail_rows", []):
                exact_sources.setdefault(str(index), set()).add(row["source_id"])
        exact_source_document = {index: sorted(sources) for index, sources in sorted(exact_sources.items(), key=lambda row: int(row[0]))}
        if trace.get("fail_sources_by_row") != exact_source_document:
            raise DG05NormalSourceError("RULE_FAIL_SOURCE_RECONSTRUCTION_MISMATCH")
        if method_id in {
            "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2",
            "ISOLATION_FOREST_PLUS_T2", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY",
        }:
            base_rows = trace.get("fusion_base_alarm_rows")
            fail_sources = trace.get("fail_sources_by_row")
            output_rows = trace.get("fusion_output_alarm_rows")
            if (
                type(base_rows) is not list
                or base_rows != sorted(set(base_rows))
                or type(fail_sources) is not dict
                or type(output_rows) is not list
            ):
                raise DG05NormalSourceError("FUSION_SOURCE_PROVENANCE_REQUIRED")
            supported = {
                int(index) for index, sources in exact_source_document.items()
                if type(sources) is list and len(set(sources)) >= 2
            }
            reconstructed = sorted(set(base_rows) | supported)
            dense_rows = [index for index, alarm in enumerate(alarms) if alarm]
            if output_rows != reconstructed or dense_rows != reconstructed:
                raise DG05NormalSourceError("FUSION_SOURCE_RECONSTRUCTION_MISMATCH")
        elif [index for index, alarm in enumerate(alarms) if alarm] != rule_rows:
            raise DG05NormalSourceError("RULE_ONLY_ALARM_TRACE_MISMATCH")


def replay_normal_source_registry_v2(
    *,
    registry: Mapping[str, Any],
    component_paths: Mapping[str, Path],
    expected_dec031_binding_hash: str,
) -> dict[str, Any]:
    """Independently reopen source bytes and recompute burden and census."""
    if (
        registry.get("schema") != "normal_burden_source_registry_v2"
        or registry.get("self_hash") != digest_v1({key: item for key, item in registry.items() if key != "self_hash"})
        or registry.get("dec031_binding_hash") != expected_dec031_binding_hash
        or registry.get("status") != "COMPLETE_SOURCE_LINEAGE"
    ):
        raise DG05NormalSourceError("APPROVED_NORMAL_SOURCE_REGISTRY_REQUIRED")
    rows = registry.get("components")
    required = registry.get("required_components")
    if (
        type(rows) is not list
        or type(required) is not list
        or registry.get("component_count") != len(rows)
        or len({row.get("component_id") for row in rows}) != len(rows)
        or set(component_paths) != {row.get("component_id") for row in rows}
        or sorted(({field: row[field] for field in ("component_id", "panel_id", "dataset_version", "method_id", "file_id", "component_role", "authority_class")} for row in rows), key=lambda row: row["component_id"])
           != sorted(required, key=lambda row: row["component_id"])
    ):
        raise DG05NormalSourceError("COMPLETE_NORMAL_SOURCE_PATH_CENSUS_REQUIRED")
    derived_components: list[dict[str, Any]] = []
    for row in rows:
        path = component_paths[row["component_id"]]
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != row["artifact_byte_hash"]:
            raise DG05NormalSourceError("NORMAL_SOURCE_ARTIFACT_BYTE_HASH_MISMATCH")
        try:
            bundle = json.loads(raw.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DG05NormalSourceError("CANONICAL_NORMAL_SOURCE_JSON_REQUIRED") from exc
        if raw != canonical_bytes_v1(bundle) + b"\n":
            raise DG05NormalSourceError("CANONICAL_NORMAL_SOURCE_BYTES_REQUIRED")
        _replay_bundle_document(bundle)
        for field in (
            "component_id", "panel_id", "dataset_version", "method_id",
            "file_id", "component_role", "authority_class",
            "method_authority_hash", "physical_file_authority_hash",
            "projection_authority_hash",
        ):
            if bundle.get(field) != row.get(field):
                raise DG05NormalSourceError(f"NORMAL_SOURCE_REGISTRY_BINDING_MISMATCH:{field}")
        if bundle["self_hash"] != row["document_self_hash"] or bundle["timeline_authority"]["self_hash"] != row["timeline_authority_hash"]:
            raise DG05NormalSourceError("NORMAL_SOURCE_NESTED_HASH_MISMATCH")
        alarms = bundle["alarms"]
        false_rows = [index for index, value in enumerate(alarms) if value]
        false_episodes = sum(index == 0 or false_rows[index - 1] + 1 != row_index for index, row_index in enumerate(false_rows))
        runtime = bundle["runtime_census"]
        if bundle["method_id"] in RULE_CAPABLE_METHODS:
            trace = dict(bundle["runtime_trace"])
            trace["file_id"] = bundle["file_id"]
            replayed_runtime = derive_four_way_runtime_census_v1(
                configured_rule_sources=bundle["configured_rule_sources"],
                file_timestamps={bundle["file_id"]: bundle["timestamps"]},
                traces=[trace],
            )
            if replayed_runtime != runtime:
                raise DG05NormalSourceError("NORMAL_SOURCE_RUNTIME_CENSUS_REPLAY_MISMATCH")
        elif runtime is not None:
            raise DG05NormalSourceError("DETECTOR_RUNTIME_CENSUS_PROHIBITED")
        derived_components.append(
            {
                "component_id": bundle["component_id"],
                "panel_id": bundle["panel_id"],
                "method_id": bundle["method_id"],
                "file_id": bundle["file_id"],
                "component_role": bundle["component_role"],
                "authority_class": bundle["authority_class"],
                "false_seconds": len(false_rows),
                "false_episodes": false_episodes,
                "exposure_seconds": len(bundle["timestamps"]),
                "runtime_census": runtime,
                "source_artifact_byte_hash": row["artifact_byte_hash"],
            }
        )
    methods = []
    identities = sorted({(row["panel_id"], row["method_id"]) for row in derived_components})
    for panel_id, method_id in identities:
        local = [row for row in derived_components if (row["panel_id"], row["method_id"]) == (panel_id, method_id)]
        classes = {row["authority_class"] for row in local}
        if len(classes) != 1:
            raise DG05NormalSourceError("ONE_NORMAL_AUTHORITY_CLASS_PER_METHOD_REQUIRED")
        seconds = sum(row["false_seconds"] for row in local)
        episodes = sum(row["false_episodes"] for row in local)
        exposure = sum(row["exposure_seconds"] for row in local)
        methods.append(
            {
                "panel_id": panel_id,
                "method_id": method_id,
                "authority_class": next(iter(classes)),
                "components": sorted(local, key=lambda row: row["component_id"]),
                "false_seconds": seconds,
                "false_episodes": episodes,
                "exposure_seconds": exposure,
                "false_seconds_per_hour": seconds * 3600 / exposure,
                "false_episodes_per_hour": episodes * 3600 / exposure,
            }
        )
    return self_hashed_v1(
        {
            "schema": "normal_burden_independent_replay_v2",
            "registry_hash": registry["self_hash"],
            "dec031_binding_hash": expected_dec031_binding_hash,
            "methods": methods,
            "method_count": len(methods),
            "caller_supplied_burden_values": False,
            "source_bytes_reopened": True,
            "status": "PASS",
        }
    )


__all__ = [
    "DG05NormalSourceError",
    "RULE_CAPABLE_METHODS",
    "build_normal_source_bundle_v2",
    "build_normal_source_registry_v2",
    "persist_normal_source_bundle_v2",
    "replay_normal_source_registry_v2",
]
