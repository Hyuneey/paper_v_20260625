"""Production extraction bridge for DEC-031 metric primitives."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from .dg05_dec031_v1 import (
    build_physical_timeline_authority_v1,
    derive_four_way_runtime_census_v1,
    require_valid_physical_timeline_v1,
)
from .dg05_execution_closure_v1 import (
    FROZEN_DATASET_VERSION_BY_PANEL_V1,
    FROZEN_METHOD_IDS_BY_PANEL_V1,
    validate_self_hashed,
)
from .dg05_metric_surface_v1 import canonical_bytes
from .dg05_metric_surface_v2 import build_metric_primitives_v2


class DG05MetricExecutionV2Error(ValueError):
    pass


def _load(path: Path, schema: str, *, self_hash: bool) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05MetricExecutionV2Error("CANONICAL_ARTIFACT_REQUIRED") from exc
    if raw != canonical_bytes(value) + b"\n" or value.get("schema") != schema:
        raise DG05MetricExecutionV2Error("CANONICAL_SCHEMA_REPLAY_FAILED")
    if self_hash:
        validate_self_hashed(value)
    return value


def _projection(path: Path, expected_hash: str, *, panel_id: str, file_id: str,
                source_commit: str) -> tuple[tuple[str, ...], str]:
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_hash:
        raise DG05MetricExecutionV2Error("PROJECTION_BYTE_REPLAY_MISMATCH")
    lines = raw.splitlines()
    try:
        timestamps = tuple(str(json.loads(line.decode("ascii"))[0]) for line in lines[1:])
    except (UnicodeDecodeError, json.JSONDecodeError, IndexError, TypeError) as exc:
        raise DG05MetricExecutionV2Error("PROJECTION_COORDINATE_REPLAY_FAILED") from exc
    timeline = build_physical_timeline_authority_v1(
        panel_id=panel_id, file_id=file_id, timestamps=timestamps,
        physical_file_authority_hash=expected_hash, projection_authority_hash=expected_hash,
        source_commit=source_commit)
    require_valid_physical_timeline_v1(timeline)
    return timestamps, timeline["self_hash"]


def build_metric_primitives_from_frozen_execution_v2(
    *, panel_id: str, global_prediction_manifest: Mapping[str, Any],
    global_prediction_freeze: Mapping[str, Any], scenario_authority: Mapping[str, Any],
    denominator_authority: Mapping[str, Any], projection_paths: Mapping[str, Path],
    prediction_paths: Mapping[str, Path], trace_paths: Mapping[str, Path],
    normal_source_replay: Mapping[str, Any], normal_source_registry_hash: str,
    dec031_binding_hash: str, source_commit: str,
) -> dict[str, Any]:
    for authority in (global_prediction_manifest, global_prediction_freeze, scenario_authority, denominator_authority):
        validate_self_hashed(authority)
    executable_hash = global_prediction_manifest.get("executable_approval_manifest_hash")
    if (global_prediction_freeze.get("manifest_hash") != global_prediction_manifest.get("self_hash")
            or global_prediction_freeze.get("executable_approval_manifest_hash") != executable_hash
            or scenario_authority.get("global_freeze_hash") != global_prediction_freeze.get("self_hash")
            or denominator_authority.get("scenario_authority_hash") != scenario_authority.get("self_hash")):
        raise DG05MetricExecutionV2Error("FROZEN_AUTHORITY_CHAIN_MISMATCH")
    expected_methods = tuple(FROZEN_METHOD_IDS_BY_PANEL_V1[panel_id])
    receipts = [row for row in global_prediction_manifest.get("receipts", ()) if row.get("panel_id") == panel_id]
    if {row.get("method_id") for row in receipts} != set(expected_methods):
        raise DG05MetricExecutionV2Error("PANEL_METHOD_CENSUS_MISMATCH")
    file_ids = tuple(sorted({str(row["file_id"]) for row in receipts}))
    if set(projection_paths) != set(file_ids):
        raise DG05MetricExecutionV2Error("PROJECTION_FILE_CENSUS_MISMATCH")
    timestamps: dict[str, tuple[str, ...]] = {}
    for file_id in file_ids:
        local = [row for row in receipts if row["file_id"] == file_id]
        hashes = {row["projection_hash"] for row in local}
        if len(hashes) != 1:
            raise DG05MetricExecutionV2Error("PROJECTION_AUTHORITY_DISAGREEMENT")
        timestamps[file_id], _ = _projection(projection_paths[file_id], hashes.pop(), panel_id=panel_id,
                                              file_id=file_id, source_commit=source_commit)
        if any(row["row_count"] != len(timestamps[file_id]) for row in local):
            raise DG05MetricExecutionV2Error("PREDICTION_ROW_COUNT_MISMATCH")
    scenario_rows = {(row["panel_id"], row["scenario_id"]): row for row in scenario_authority.get("records", ())}
    denominator_rows = {(row["panel_id"], row["scenario_id"]): row for row in denominator_authority.get("records", ())}
    if len(scenario_rows) != len(scenario_authority.get("records", ())) or set(scenario_rows) != set(denominator_rows):
        raise DG05MetricExecutionV2Error("SCENARIO_DENOMINATOR_CENSUS_MISMATCH")
    scenarios = []
    for key in sorted(value for value in scenario_rows if value[0] == panel_id):
        scenario, eligibility = scenario_rows[key], denominator_rows[key]
        if eligibility.get("scenario_record_hash") != scenario.get("self_hash"):
            raise DG05MetricExecutionV2Error("ELIGIBILITY_SCENARIO_BINDING_MISMATCH")
        intervals = scenario.get("closed_intervals")
        if type(intervals) is not list or not intervals or any(type(row) is not list or len(row) != 2 for row in intervals):
            raise DG05MetricExecutionV2Error("PLURAL_CLOSED_INTERVAL_AUTHORITY_REQUIRED")
        if scenario["file_id"] not in timestamps:
            raise DG05MetricExecutionV2Error("SCENARIO_FILE_AUTHORITY_MISMATCH")
        scenarios.append({"scenario_id": scenario["scenario_id"], "file_id": scenario["file_id"],
                          "closed_intervals": intervals, "eligibility": eligibility["primary_status"],
                          "scenario_authority_hash": scenario["self_hash"],
                          "eligibility_authority_hash": eligibility["self_hash"]})
    if (normal_source_replay.get("schema") != "normal_burden_independent_replay_v2"
            or normal_source_replay.get("status") != "PASS"
            or normal_source_replay.get("registry_hash") != normal_source_registry_hash
            or normal_source_replay.get("dec031_binding_hash") != dec031_binding_hash
            or normal_source_replay.get("source_bytes_reopened") is not True):
        raise DG05MetricExecutionV2Error("INDEPENDENT_NORMAL_SOURCE_REPLAY_REQUIRED")
    burden = {row["method_id"]: row for row in normal_source_replay["methods"] if row["panel_id"] == panel_id}
    if set(burden) != set(expected_methods):
        raise DG05MetricExecutionV2Error("NORMAL_SOURCE_METHOD_CENSUS_MISMATCH")
    methods: dict[str, dict[str, Any]] = {}
    for method_id in expected_methods:
        local = [row for row in receipts if row["method_id"] == method_id]
        if {row["file_id"] for row in local} != set(file_ids):
            raise DG05MetricExecutionV2Error("METHOD_FILE_CENSUS_MISMATCH")
        alarm_rows: dict[str, list[int]] = {}; alarm_times: dict[str, list[str]] = {}; traces = []
        failure = False
        for receipt in local:
            if receipt["status"] == "METHOD_FAILURE":
                failure = True; continue
            path = prediction_paths.get(receipt["cell_id"])
            if path is None or sha256(path.read_bytes()).hexdigest() != receipt["prediction_artifact_hash"]:
                raise DG05MetricExecutionV2Error("PREDICTION_BYTE_REPLAY_MISMATCH")
            prediction = _load(path, "dense_boolean_prediction_v1", self_hash=False)
            values = prediction.get("alarms")
            if type(values) is not list or len(values) != len(timestamps[receipt["file_id"]]) or any(type(value) is not bool for value in values):
                raise DG05MetricExecutionV2Error("DENSE_BOOLEAN_PREDICTION_REQUIRED")
            rows = [index for index, value in enumerate(values) if value]
            alarm_rows[receipt["file_id"]] = rows
            alarm_times[receipt["file_id"]] = [timestamps[receipt["file_id"]][index] for index in rows]
            if receipt.get("trace_status") == "BOUND":
                trace_path = trace_paths.get(receipt["cell_id"])
                if trace_path is None or sha256(trace_path.read_bytes()).hexdigest() != receipt.get("trace_artifact_hash"):
                    raise DG05MetricExecutionV2Error("TRACE_BYTE_REPLAY_MISMATCH")
                trace = _load(trace_path, "rule_trace_artifact_v4", self_hash=True)
                traces.append(trace)
        census = None
        if "RULE" in method_id or "PLUS" in method_id:
            if failure:
                census = None
            else:
                if len(traces) != len(file_ids):
                    raise DG05MetricExecutionV2Error("COMPLETE_RULE_TRACE_CENSUS_REQUIRED")
                configured = traces[0].get("configured_rule_sources")
                if any(trace.get("configured_rule_sources") != configured for trace in traces):
                    raise DG05MetricExecutionV2Error("CONFIGURED_RULE_AUTHORITY_DISAGREEMENT")
                census = derive_four_way_runtime_census_v1(
                    configured_rule_sources=configured,
                    file_timestamps={file_id: timestamps[file_id] for file_id in file_ids}, traces=traces)
        methods[method_id] = {"status": "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE" if failure else "COMPLETE",
                              "timestamps_by_file": {key: list(value) for key, value in timestamps.items()},
                              "alarm_rows_by_file": alarm_rows, "alarm_timestamps_by_file": alarm_times,
                              "normal_burden": burden[method_id], "runtime_census": census}
    return build_metric_primitives_v2(
        panel_id=panel_id, dataset_version=FROZEN_DATASET_VERSION_BY_PANEL_V1[panel_id],
        scenarios=scenarios, methods=methods,
        authority_hashes={"executable": str(executable_hash), "prediction_manifest": global_prediction_manifest["self_hash"],
                          "scenario": scenario_authority["self_hash"], "denominator": denominator_authority["self_hash"],
                          "normal_burden": normal_source_registry_hash, "dec031": dec031_binding_hash})


__all__ = ["DG05MetricExecutionV2Error", "build_metric_primitives_from_frozen_execution_v2"]
