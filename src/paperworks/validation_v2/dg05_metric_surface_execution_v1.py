"""Production-path bridge from frozen DG-05 predictions to metric surfaces.

This module performs orchestration and primitive extraction only.  Scientific
metric arithmetic remains in ``dg05_metric_surface_v1`` and is independently
recomputed by ``dg05_metric_surface_oracle_v1`` from persisted paths.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from paperworks.validation_v2.dg05_execution_closure_v1 import (
    FROZEN_DATASET_VERSION_BY_PANEL_V1,
    FROZEN_METHOD_IDS_BY_PANEL_V1,
    validate_self_hashed,
)
from paperworks.validation_v2.dg05_metric_surface_oracle_v1 import (
    verify_complete_metric_surface_from_paths_v1,
)
from paperworks.validation_v2.dg05_metric_surface_v1 import (
    FROZEN_PANEL_ORDER,
    build_metric_primitives_v1,
    canonical_bytes,
    self_hashed,
)


class DG05MetricExecutionError(ValueError):
    pass


def _load_canonical(path: Path, schema: str, *, self_hash: bool) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05MetricExecutionError("CANONICAL_ARTIFACT_REQUIRED") from exc
    if raw != canonical_bytes(value) + b"\n" or value.get("schema") != schema:
        raise DG05MetricExecutionError("CANONICAL_SCHEMA_REPLAY_FAILED")
    if self_hash:
        validate_self_hashed(value)
    return value


def _projection_coordinates(path: Path, expected_hash: str) -> tuple[tuple[str, ...], int]:
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_hash:
        raise DG05MetricExecutionError("PROJECTION_BYTE_REPLAY_MISMATCH")
    lines = raw.splitlines()
    if len(lines) < 2:
        raise DG05MetricExecutionError("EMPTY_PROJECTION")
    try:
        timestamps = tuple(str(json.loads(line.decode("ascii"))[0]) for line in lines[1:])
    except (UnicodeDecodeError, json.JSONDecodeError, IndexError, TypeError) as exc:
        raise DG05MetricExecutionError("PROJECTION_COORDINATE_REPLAY_FAILED") from exc
    if len(timestamps) != len(set(timestamps)):
        raise DG05MetricExecutionError("SYNTHETIC_OR_PRODUCTION_TIMESTAMP_AMBIGUITY")
    return timestamps, len(timestamps)


def build_metric_primitives_from_frozen_execution_v1(
    *,
    panel_id: str,
    global_prediction_manifest: Mapping[str, Any],
    global_prediction_freeze: Mapping[str, Any],
    scenario_authority: Mapping[str, Any],
    denominator_authority: Mapping[str, Any],
    projection_paths: Mapping[str, Path],
    prediction_paths: Mapping[str, Path],
    trace_paths: Mapping[str, Path],
    method_normal_burden: Mapping[str, Mapping[str, Any]],
    normal_burden_authority_hash: str,
) -> dict[str, Any]:
    """Extract typed metric primitives from frozen, replayed artifacts.

    No labels or scenario source is read here.  Only already-frozen method-blind
    scenario and denominator authorities are accepted.
    """
    for authority in (global_prediction_manifest, global_prediction_freeze,
                      scenario_authority, denominator_authority):
        validate_self_hashed(authority)
    if panel_id not in FROZEN_PANEL_ORDER:
        raise DG05MetricExecutionError("FROZEN_PANEL_REQUIRED")
    executable_hash = global_prediction_manifest.get("executable_approval_manifest_hash")
    if (global_prediction_freeze.get("manifest_hash") != global_prediction_manifest.get("self_hash")
            or global_prediction_freeze.get("executable_approval_manifest_hash") != executable_hash
            or scenario_authority.get("global_freeze_hash") != global_prediction_freeze.get("self_hash")
            or denominator_authority.get("scenario_authority_hash") != scenario_authority.get("self_hash")):
        raise DG05MetricExecutionError("FROZEN_AUTHORITY_CHAIN_MISMATCH")

    receipts = [row for row in global_prediction_manifest.get("receipts", ())
                if row.get("panel_id") == panel_id]
    expected_methods = tuple(FROZEN_METHOD_IDS_BY_PANEL_V1[panel_id])
    if {row.get("method_id") for row in receipts} != set(expected_methods):
        raise DG05MetricExecutionError("PANEL_METHOD_CENSUS_MISMATCH")
    file_ids = tuple(sorted({str(row["file_id"]) for row in receipts}))
    if set(projection_paths) != set(file_ids):
        raise DG05MetricExecutionError("PROJECTION_FILE_CENSUS_MISMATCH")

    projection_coordinates: dict[str, tuple[str, ...]] = {}
    row_counts: dict[str, int] = {}
    projection_hash_by_file: dict[str, str] = {}
    for file_id in file_ids:
        local = [row for row in receipts if row["file_id"] == file_id]
        hashes = {row["projection_hash"] for row in local}
        if len(hashes) != 1:
            raise DG05MetricExecutionError("PROJECTION_AUTHORITY_DISAGREEMENT")
        projection_hash = hashes.pop()
        coordinates, count = _projection_coordinates(projection_paths[file_id], projection_hash)
        if any(row["row_count"] != count for row in local):
            raise DG05MetricExecutionError("PREDICTION_ROW_COUNT_MISMATCH")
        projection_coordinates[file_id] = coordinates
        row_counts[file_id] = count
        projection_hash_by_file[file_id] = projection_hash

    scenario_docs = {(row["panel_id"], row["scenario_id"]): row
                     for row in scenario_authority.get("records", ())}
    denominator_docs = {(row["panel_id"], row["scenario_id"]): row
                        for row in denominator_authority.get("records", ())}
    if set(scenario_docs) != set(denominator_docs):
        raise DG05MetricExecutionError("SCENARIO_DENOMINATOR_CENSUS_MISMATCH")
    scenarios: list[dict[str, Any]] = []
    for key in sorted(k for k in scenario_docs if k[0] == panel_id):
        scenario = scenario_docs[key]
        eligibility = denominator_docs[key]
        if eligibility.get("scenario_record_hash") != scenario.get("self_hash"):
            raise DG05MetricExecutionError("ELIGIBILITY_SCENARIO_BINDING_MISMATCH")
        intervals = scenario.get("closed_intervals")
        if not isinstance(intervals, list) or len(intervals) != 1 or len(intervals[0]) != 2:
            raise DG05MetricExecutionError("EXACT_SINGLE_CLOSED_INTERVAL_REQUIRED")
        file_id = str(scenario["file_id"])
        try:
            start = projection_coordinates[file_id].index(intervals[0][0])
            end = projection_coordinates[file_id].index(intervals[0][1])
        except (KeyError, ValueError) as exc:
            raise DG05MetricExecutionError("SCENARIO_TIMESTAMP_COORDINATE_MISMATCH") from exc
        if start > end:
            raise DG05MetricExecutionError("SCENARIO_INTERVAL_ORDER_MISMATCH")
        scenarios.append({"scenario_id": scenario["scenario_id"], "file_id": file_id,
                          "start": start, "end": end,
                          "eligibility": eligibility["primary_status"],
                          "scenario_authority_hash": scenario["self_hash"],
                          "eligibility_authority_hash": eligibility["self_hash"]})

    methods: dict[str, dict[str, Any]] = {}
    for method_id in expected_methods:
        local = [row for row in receipts if row["method_id"] == method_id]
        if {row["file_id"] for row in local} != set(file_ids):
            raise DG05MetricExecutionError("METHOD_FILE_CENSUS_MISMATCH")
        alarms_by_file: dict[str, list[int]] = {}
        traces: list[dict[str, Any]] = []
        failed = False
        for receipt in local:
            if receipt["status"] == "METHOD_FAILURE":
                failed = True
                continue
            if receipt["status"] != "SUCCESS":
                raise DG05MetricExecutionError("UNKNOWN_TERMINAL_PREDICTION_STATUS")
            path = prediction_paths.get(receipt["cell_id"])
            if path is None or sha256(path.read_bytes()).hexdigest() != receipt["prediction_artifact_hash"]:
                raise DG05MetricExecutionError("PREDICTION_BYTE_REPLAY_MISMATCH")
            prediction = _load_canonical(path, "dense_boolean_prediction_v1", self_hash=False)
            if prediction.get("cell_id") != receipt["cell_id"] or prediction.get("row_count") != receipt["row_count"]:
                raise DG05MetricExecutionError("PREDICTION_RECEIPT_BINDING_MISMATCH")
            values = prediction.get("alarms")
            if not isinstance(values, list) or any(type(value) is not bool for value in values):
                raise DG05MetricExecutionError("DENSE_BOOLEAN_PREDICTION_REQUIRED")
            alarms_by_file[receipt["file_id"]] = [index for index, value in enumerate(values) if value]
            if receipt["trace_status"] == "BOUND":
                trace_path = trace_paths.get(receipt["cell_id"])
                if trace_path is None or sha256(trace_path.read_bytes()).hexdigest() != receipt["trace_artifact_hash"]:
                    raise DG05MetricExecutionError("TRACE_BYTE_REPLAY_MISMATCH")
                trace = _load_canonical(trace_path, "rule_trace_artifact_v1", self_hash=True)
                if trace.get("cell_id") != receipt["cell_id"] or trace.get("prediction_hash") != receipt["prediction_artifact_hash"]:
                    raise DG05MetricExecutionError("TRACE_PREDICTION_BINDING_MISMATCH")
                traces.append(trace)
        if set(method_normal_burden) != set(expected_methods):
            raise DG05MetricExecutionError("NORMAL_BURDEN_METHOD_CENSUS_MISMATCH")
        methods[method_id] = {
            "status": "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE" if failed else "COMPLETE",
            "row_counts": dict(row_counts),
            "alarms_by_file": alarms_by_file,
            "normal_burden": dict(method_normal_burden[method_id]),
            "runtime_traces": traces,
        }

    return build_metric_primitives_v1(
        panel_id=panel_id,
        dataset_version=FROZEN_DATASET_VERSION_BY_PANEL_V1[panel_id],
        scenarios=scenarios,
        methods=methods,
        authority_hashes={"executable": str(executable_hash),
                          "prediction_manifest": global_prediction_manifest["self_hash"],
                          "scenario": scenario_authority["self_hash"],
                          "denominator": denominator_authority["self_hash"],
                          "normal_burden": normal_burden_authority_hash},
    )


def close_complete_metric_results_v1(
    *, predecessor_state: Mapping[str, Any], executable_manifest_hash: str,
    contract_path: Path, primitive_paths: Sequence[Path], result_paths: Sequence[Path],
    wrapper: Any,
) -> dict[str, Any]:
    """Path-replay all panels and emit the V3 result-integrity terminal state."""
    validate_self_hashed(predecessor_state)
    if predecessor_state.get("state") != "DENOMINATOR_AUTHORITY_FROZEN" or predecessor_state.get("executable_approval_manifest_hash") != executable_manifest_hash:
        raise DG05MetricExecutionError("DENOMINATOR_FROZEN_PREDECESSOR_REQUIRED")
    if len(primitive_paths) != 3 or len(result_paths) != 3:
        raise DG05MetricExecutionError("THREE_PANEL_RESULT_PATHS_REQUIRED")
    contract = _load_canonical(contract_path, "metric_surface_contract_v1", self_hash=True)
    panels: list[str] = []
    result_hashes: list[str] = []
    verified_ids: set[str] = set()
    verifier_receipts = []
    for primitive_path, result_path in zip(primitive_paths, result_paths, strict=True):
        receipt = verify_complete_metric_surface_from_paths_v1(
            primitive_path=primitive_path, result_path=result_path, contract_path=contract_path,
            wrapper=wrapper, expected_executable_hash=executable_manifest_hash)
        primitive = _load_canonical(primitive_path, "metric_surface_primitives_v1", self_hash=True)
        result = _load_canonical(result_path, "complete_panel_metric_surface_v1", self_hash=True)
        if result["panel_id"] != primitive["panel_id"] or receipt["result_self_hash"] != result["self_hash"]:
            raise DG05MetricExecutionError("RESULT_VERIFIER_BINDING_MISMATCH")
        panels.append(result["panel_id"])
        result_hashes.append(result["self_hash"])
        verified_ids.update(row["surface_id"] for row in result["surfaces"])
        verifier_receipts.append(receipt)
    expected_ids = {row["surface_id"] for row in contract["surfaces"]}
    if tuple(panels) != tuple(FROZEN_PANEL_ORDER) or verified_ids != expected_ids:
        raise DG05MetricExecutionError("BLOCKED_METRIC_SURFACE_INCOMPLETE")
    return self_hashed({"schema": "dg05_v3_result_integrity_state_v1",
                        "state": "RESULT_INTEGRITY_AUDITED",
                        "predecessor_state_hash": predecessor_state["self_hash"],
                        "executable_approval_manifest_hash": executable_manifest_hash,
                        "contract_hash": contract["self_hash"],
                        "panel_result_hashes": result_hashes,
                        "verifier_receipts": verifier_receipts,
                        "verified_surface_count": len(verified_ids),
                        "cross_version_pooled_result": False})


__all__ = ["DG05MetricExecutionError", "build_metric_primitives_from_frozen_execution_v1",
           "close_complete_metric_results_v1"]
