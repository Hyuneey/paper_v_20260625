"""Release-bound DEC-031 prediction and terminal-result adapters.

The frozen V1 execution kernel remains the scientific method implementation.
This prospective adapter binds it to the new release root, gates the physical
timeline before scorer invocation, and emits V4 runtime evidence without
altering detector, Rule, or Fusion semantics.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from .dg05_dec031_v1 import build_physical_timeline_authority_v1, require_valid_physical_timeline_v1
from .dg05_execution_closure_v1 import (
    DG05ClosureError,
    DG05ProductionExecutorV1,
    MethodDispatchRegistryV1,
    PredictionTerminalReceiptV1,
    canonical_bytes,
    digest,
    file_sha256,
    publish_new,
)
from .dg05_runtime_adapter_v4 import execute_normal_method_v4
from .dg05_production_chain_v1 import REQUIRED_IMPLEMENTATION_ROLES_V4, digest_v1


class DG05ProductionRouteV4Error(ValueError):
    pass


def validate_release_execution_kernel_v4(
    *, release: Mapping[str, Any], predecessor_v3: Mapping[str, Any],
    initialized_release_state: Mapping[str, Any], executor: DG05ProductionExecutorV1,
) -> None:
    for value, schema in ((release, "dg05_production_release_manifest_v1"),
                          (predecessor_v3, "dg05_executable_authority_manifest_v3")):
        if value.get("schema") != schema or value.get("self_hash") != digest_v1({key: item for key, item in value.items() if key != "self_hash"}):
            raise DG05ProductionRouteV4Error("RELEASE_OR_PREDECESSOR_REPLAY_FAILED")
    if (release.get("predecessor_v3_manifest_hash") != predecessor_v3["self_hash"]
            or predecessor_v3.get("historical_prediction_executable_manifest_hash") != executor.executable_manifest_hash):
        raise DG05ProductionRouteV4Error("RELEASE_EXECUTION_KERNEL_BINDING_MISMATCH")
    implementation_names = [row.get("logical_name") for row in release.get("implementation_authorities", ())]
    if (
        release.get("executable_version") != "DG05_EXECUTABLE_V4"
        or release.get("readiness") != "READY_FOR_USER_REAPPROVAL"
        or release.get("semantic_binding_status") != "APPROVED"
        or release.get("normal_burden_source_status") != "COMPLETE"
        or len(implementation_names) != len(set(implementation_names))
        or set(implementation_names) != REQUIRED_IMPLEMENTATION_ROLES_V4
    ):
        raise DG05ProductionRouteV4Error("V4_RELEASE_READINESS_REPLAY_FAILED")
    if (
        initialized_release_state.get("schema") != "dg05_production_chain_state_v1"
        or initialized_release_state.get("self_hash")
        != digest_v1({key: value for key, value in initialized_release_state.items() if key != "self_hash"})
        or initialized_release_state.get("release_manifest_hash") != release["self_hash"]
        or initialized_release_state.get("implementation_authority_hash")
        != digest_v1(release["implementation_authorities"])
        or initialized_release_state.get("nested_authority_hash")
        != digest_v1(release["nested_authority_hashes"])
        or initialized_release_state.get("state")
        not in ("SYNTHETIC_RELEASE_INITIALIZED", "APPROVED_PRODUCTION_RELEASE_INITIALIZED")
        or initialized_release_state.get("authority_mode")
        not in ("SYNTHETIC_REHEARSAL", "PRODUCTION")
    ):
        raise DG05ProductionRouteV4Error("INITIALIZED_RELEASE_STATE_REQUIRED")
    executor.validate()


def _projection_timestamps(path: Path, expected_hash: str) -> tuple[str, ...]:
    if file_sha256(path) != expected_hash:
        raise DG05ProductionRouteV4Error("PROJECTION_ARTIFACT_BYTE_REPLAY_MISMATCH")
    try:
        return tuple(str(json.loads(line.decode("ascii"))[0]) for line in path.read_bytes().splitlines()[1:])
    except (UnicodeDecodeError, json.JSONDecodeError, IndexError, TypeError) as exc:
        raise DG05ProductionRouteV4Error("PROJECTION_TIMESTAMP_REPLAY_FAILED") from exc


def _synthetic_four_way_trace(trace: Mapping[str, Any], *, file_id: str, timestamps: tuple[str, ...]) -> dict[str, Any]:
    rule_ids = tuple(trace.get("rule_ids", ()))
    sources = tuple(trace.get("physical_source_ids", ()))
    if not rule_ids or not sources:
        raise DG05ProductionRouteV4Error("SYNTHETIC_RULE_IDENTITY_REQUIRED")
    fail_rows = sorted(int(index) for index in trace.get("fail_sources_by_row", {}))
    if len(fail_rows) != int(trace["fail"]):
        raise DG05ProductionRouteV4Error("SYNTHETIC_FAIL_ROW_CENSUS_MISMATCH")
    # The historical synthetic Fusion kernel proves distinct-source support.
    # Preserve that provenance with one typed synthetic Rule per physical
    # source.  Counts are evidence records, so Rule multiplicity is retained;
    # alarm seconds/episodes are still derived from the physical-row union.
    configured = {
        f"{rule_ids[0]}::{ordinal}": source_id
        for ordinal, source_id in enumerate(sources, start=1)
    }
    rows = []
    for rule_id, source_id in configured.items():
        rows.append({
            "rule_id": rule_id,
            "source_id": source_id,
            "opportunities": len(fail_rows),
            "pass": 0,
            "fail": len(fail_rows),
            "abstain": 0,
            "system_errors": 0,
            "evaluation_invocations": len(fail_rows),
            "evaluated_system_errors": 0,
            "fail_rows": fail_rows,
        })
    totals = {
        field: sum(row[field] for row in rows)
        for field in ("opportunities", "pass", "fail", "abstain", "system_errors",
                      "evaluation_invocations", "evaluated_system_errors")
    }
    from .dg05_dec031_v1 import derive_four_way_runtime_census_v1
    body = {"file_id": file_id, "per_rule_runtime": rows, "rule_alarm_rows": fail_rows,
            **totals,
            "configured_rule_sources": configured,
            "fail_sources_by_row": {str(index): sorted(sources) for index in fail_rows},
            "rule_component_alarm_rows": fail_rows}
    body["four_way_runtime_census"] = derive_four_way_runtime_census_v1(
        configured_rule_sources=configured, file_timestamps={file_id: timestamps}, traces=[body])
    return body


def execute_prediction_cell_v4(
    *, cell: Mapping[str, Any], dispatch: MethodDispatchRegistryV1, projection: Any,
    timestamp: Any, release: Mapping[str, Any], predecessor_v3: Mapping[str, Any],
    initialized_release_state: Mapping[str, Any], executor: DG05ProductionExecutorV1,
    projection_path: Path, output_directory: Path,
    source_commit: str,
) -> PredictionTerminalReceiptV1:
    """Execute one cell only after release and physical-time replay."""
    validate_release_execution_kernel_v4(
        release=release, predecessor_v3=predecessor_v3,
        initialized_release_state=initialized_release_state, executor=executor)
    if release.get("source_commit") != source_commit:
        raise DG05ProductionRouteV4Error("RELEASE_SOURCE_COMMIT_MISMATCH")
    entry = dispatch.lookup(str(cell["panel_id"]), str(cell["method_id"]))
    expected_cell_id = digest({key: cell[key] for key in ("panel_id", "file_id", "method_id", "dispatch_authority_hash")})
    if cell.get("cell_id") != expected_cell_id or projection.panel_id != cell["panel_id"] or projection.file_id != cell["file_id"]:
        raise DG05ProductionRouteV4Error("CELL_PROJECTION_BINDING_MISMATCH")
    timestamps = _projection_timestamps(projection_path, projection.projection_hash)
    timeline = build_physical_timeline_authority_v1(
        panel_id=cell["panel_id"], file_id=cell["file_id"], timestamps=timestamps,
        physical_file_authority_hash=projection.raw_physical_file_hash,
        projection_authority_hash=projection.projection_hash, source_commit=source_commit)
    method_hash = digest(entry.document())
    release_hash = release["self_hash"]
    try:
        require_valid_physical_timeline_v1(timeline)
    except ValueError as exc:
        failure = PredictionTerminalReceiptV1(expected_cell_id, entry.panel_id, projection.file_id, entry.method_id,
            method_hash, projection.raw_physical_file_hash, projection.projection_hash, timestamp.document()["self_hash"],
            projection.row_count, None, None, "NOT_APPLICABLE", "METHOD_FAILURE", str(exc),
            digest({"schema": "dense_boolean_prediction_v1"}), release_hash, source_commit)
        failure.validate(); return failure
    try:
        if executor.authority_mode == "PRODUCTION":
            feature_order, matrix = executor._projection_matrix(projection_path, projection)
            alarms, trace = execute_normal_method_v4(
                executor=executor, entry=entry, feature_order=feature_order, matrix=matrix,
                file_id=projection.file_id, projection_hash=projection.projection_hash, timestamps=timestamps)
        else:
            alarms, old_trace = executor.execute(cell_id=expected_cell_id, entry=entry,
                                                  projection_path=projection_path, projection=projection)
            trace = None if old_trace is None else _synthetic_four_way_trace(old_trace, file_id=projection.file_id,
                                                                             timestamps=timestamps)
        if len(alarms) != projection.row_count or any(type(value) is not bool for value in alarms):
            raise DG05ProductionRouteV4Error("EXECUTOR_OUTPUT_SCHEMA_MISMATCH")
    except (DG05ClosureError, DG05ProductionRouteV4Error, ValueError) as exc:
        failure = PredictionTerminalReceiptV1(expected_cell_id, entry.panel_id, projection.file_id, entry.method_id,
            method_hash, projection.raw_physical_file_hash, projection.projection_hash, timestamp.document()["self_hash"],
            projection.row_count, None, None, "NOT_APPLICABLE", "METHOD_FAILURE", str(exc),
            digest({"schema": "dense_boolean_prediction_v1"}), release_hash, source_commit)
        failure.validate(); return failure
    prediction = {"schema": "dense_boolean_prediction_v1", "cell_id": expected_cell_id,
                  "row_count": len(alarms), "alarms": list(alarms)}
    prediction_hash = publish_new(output_directory / f"{expected_cell_id}.prediction.json",
                                  canonical_bytes(prediction) + b"\n")
    trace_hash = None; trace_status = "NOT_APPLICABLE"
    if trace is not None:
        trace_doc = {"schema": "rule_trace_artifact_v4", "cell_id": expected_cell_id,
                     "prediction_hash": prediction_hash, "projection_hash": projection.projection_hash,
                     "timestamp_authority_hash": timestamp.document()["self_hash"], **dict(trace)}
        from .dg05_execution_closure_v1 import self_hashed
        trace_hash = publish_new(output_directory / f"{expected_cell_id}.trace.json",
                                 canonical_bytes(self_hashed(trace_doc)) + b"\n")
        trace_status = "BOUND"
    receipt = PredictionTerminalReceiptV1(expected_cell_id, entry.panel_id, projection.file_id, entry.method_id,
        method_hash, projection.raw_physical_file_hash, projection.projection_hash, timestamp.document()["self_hash"],
        projection.row_count, prediction_hash, trace_hash, trace_status, "SUCCESS", None,
        digest({"schema": "dense_boolean_prediction_v1"}), release_hash, source_commit)
    receipt.validate(); return receipt


__all__ = ["DG05ProductionRouteV4Error", "execute_prediction_cell_v4", "validate_release_execution_kernel_v4"]
