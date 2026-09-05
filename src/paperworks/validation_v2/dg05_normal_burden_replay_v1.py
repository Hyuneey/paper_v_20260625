"""Independent normal-burden replay from immutable method-specific sources."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from paperworks.validation_v2.dg05_production_chain_v1 import (
    DG05ProductionChainError,
    canonical_bytes_v1,
    digest_v1,
    validate_strict_one_second_coordinates_v1,
)


class NormalBurdenReplayError(ValueError):
    """Raised when a burden value lacks replayable source evidence."""


def _load_canonical(path: Path, schema: str, expected_hash: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_hash:
        raise NormalBurdenReplayError("SOURCE_ARTIFACT_BYTE_HASH_MISMATCH")
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NormalBurdenReplayError("CANONICAL_SOURCE_JSON_REQUIRED") from exc
    if raw != canonical_bytes_v1(value) + b"\n" or value.get("schema") != schema:
        raise NormalBurdenReplayError("CANONICAL_SOURCE_SCHEMA_REQUIRED")
    return value


def _episodes(alarms: list[bool]) -> int:
    return sum(value and (index == 0 or not alarms[index - 1]) for index, value in enumerate(alarms))


def replay_method_normal_burden_v1(
    *,
    source_registry: Mapping[str, Any],
    prediction_paths: Mapping[str, Path],
    timestamp_paths: Mapping[str, Path],
    coverage_paths: Mapping[str, Path],
    approved_time_binding_hash: str,
) -> dict[str, Any]:
    """Derive counts and denominators; no caller-supplied metric numbers."""
    body = {key: value for key, value in source_registry.items() if key != "self_hash"}
    if (
        source_registry.get("schema") != "normal_burden_source_registry_v1"
        or source_registry.get("self_hash") != digest_v1(body)
        or source_registry.get("time_binding_status") != "APPROVED"
        or source_registry.get("time_binding_hash") != approved_time_binding_hash
    ):
        raise NormalBurdenReplayError("APPROVED_NORMAL_BURDEN_SOURCE_REGISTRY_REQUIRED")
    components = source_registry.get("components")
    if type(components) is not list or not components:
        raise NormalBurdenReplayError("EVIDENCE_MISSING:NORMAL_BURDEN_COMPONENTS")
    component_ids = {str(row.get("component_id")) for row in components}
    if len(component_ids) != len(components) or set(prediction_paths) != component_ids or set(timestamp_paths) != component_ids or set(coverage_paths) != component_ids:
        raise NormalBurdenReplayError("COMPLETE_NORMAL_BURDEN_PATH_CENSUS_REQUIRED")
    methods: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in components:
        required = {
            "component_id",
            "panel_id",
            "method_id",
            "file_id",
            "prediction_byte_hash",
            "timestamp_byte_hash",
            "coverage_byte_hash",
            "method_authority_hash",
            "physical_file_authority_hash",
            "authority_class",
        }
        if type(row) is not dict or set(row) != required:
            raise NormalBurdenReplayError("NORMAL_BURDEN_COMPONENT_SCHEMA_REQUIRED")
        component_id = row["component_id"]
        prediction = _load_canonical(prediction_paths[component_id], "dense_boolean_normal_prediction_v1", row["prediction_byte_hash"])
        timestamp = _load_canonical(timestamp_paths[component_id], "normal_timestamp_vector_v1", row["timestamp_byte_hash"])
        coverage = _load_canonical(coverage_paths[component_id], "normal_method_coverage_v1", row["coverage_byte_hash"])
        alarms = prediction.get("alarms")
        timestamps = timestamp.get("timestamps")
        if type(alarms) is not list or any(type(value) is not bool for value in alarms):
            raise NormalBurdenReplayError("DENSE_BOOLEAN_NORMAL_PREDICTION_REQUIRED")
        if type(timestamps) is not list or len(timestamps) != len(alarms):
            raise NormalBurdenReplayError("NORMAL_TIMESTAMP_VECTOR_MISMATCH")
        try:
            validate_strict_one_second_coordinates_v1(timestamps)
        except DG05ProductionChainError as exc:
            raise NormalBurdenReplayError(str(exc)) from exc
        required_coverage = {"schema", "component_id", "opportunities", "evaluated", "abstain"}
        if set(coverage) != required_coverage or coverage["component_id"] != component_id:
            raise NormalBurdenReplayError("NORMAL_COVERAGE_SCHEMA_REQUIRED")
        if any(type(coverage[field]) is not int or coverage[field] < 0 for field in ("opportunities", "evaluated", "abstain")):
            raise NormalBurdenReplayError("NORMAL_COVERAGE_COUNT_INVALID")
        if coverage["evaluated"] > coverage["opportunities"] or coverage["abstain"] > coverage["opportunities"]:
            raise NormalBurdenReplayError("NORMAL_COVERAGE_COUNT_INCONSISTENT")
        derived = {
            "component_id": component_id,
            "file_id": row["file_id"],
            "false_seconds": sum(alarms),
            "false_episodes": _episodes(alarms),
            "exposure_seconds": len(timestamps),
            "opportunities": coverage["opportunities"],
            "evaluated": coverage["evaluated"],
            "abstain": coverage["abstain"],
            "prediction_byte_hash": row["prediction_byte_hash"],
            "timestamp_byte_hash": row["timestamp_byte_hash"],
            "coverage_byte_hash": row["coverage_byte_hash"],
            "method_authority_hash": row["method_authority_hash"],
            "physical_file_authority_hash": row["physical_file_authority_hash"],
        }
        methods.setdefault((row["panel_id"], row["method_id"]), []).append(derived)
    output = []
    for (panel_id, method_id), rows in sorted(methods.items()):
        authority_classes = {next(row["authority_class"] for row in components if row["component_id"] == value["component_id"]) for value in rows}
        if len(authority_classes) != 1:
            raise NormalBurdenReplayError("ONE_AUTHORITY_CLASS_PER_PANEL_METHOD_REQUIRED")
        seconds = sum(row["false_seconds"] for row in rows)
        episodes = sum(row["false_episodes"] for row in rows)
        exposure = sum(row["exposure_seconds"] for row in rows)
        opportunities = sum(row["opportunities"] for row in rows)
        evaluated = sum(row["evaluated"] for row in rows)
        abstain = sum(row["abstain"] for row in rows)
        output.append(
            {
                "panel_id": panel_id,
                "method_id": method_id,
                "authority_class": next(iter(authority_classes)),
                "components": sorted(rows, key=lambda value: value["component_id"]),
                "false_seconds": seconds,
                "false_episodes": episodes,
                "exposure_seconds": exposure,
                "false_seconds_per_hour": seconds * 3600 / exposure,
                "false_episodes_per_hour": episodes * 3600 / exposure,
                "opportunity_coverage": None if opportunities == 0 else evaluated / opportunities,
                "abstain_rate": None if opportunities == 0 else abstain / opportunities,
            }
        )
    return {
        "schema": "replayed_method_normal_burden_v1",
        "source_registry_hash": source_registry["self_hash"],
        "time_binding_hash": approved_time_binding_hash,
        "methods": output,
        "caller_supplied_metric_values": False,
    }


__all__ = ["NormalBurdenReplayError", "replay_method_normal_burden_v1"]
