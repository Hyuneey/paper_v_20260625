"""Release-qualified prediction route with frozen-kernel parity evidence."""
from __future__ import annotations

from dataclasses import dataclass, field
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
    self_hashed,
)
from .dg05_preaccess_kernel_v5 import (
    PREACCESS_EXECUTION_MODE_V5,
    PreaccessFrozenKernelExecutorV5,
)
from .dg05_runtime_adapter_v4 import execute_normal_method_v4


class DG05ProductionRouteV5Error(ValueError):
    pass


@dataclass
class KernelInvocationCensusV5:
    """Public-safe path evidence; no scores, predictions, or private paths."""

    rows: list[dict[str, Any]] = field(default_factory=list)

    def record(
        self,
        *,
        cell: Mapping[str, Any],
        entry: Any,
        executor: Any,
        repository_root: Path,
        trace: Mapping[str, Any] | None,
    ) -> None:
        from .dg05_execution_closure_v1 import _METHOD_RUNTIME_BINDING_V1
        detector_id, role = _METHOD_RUNTIME_BINDING_V1[entry.method_id]
        callables: list[dict[str, str]] = []
        if detector_id:
            authority = executor.detector_registry.lookup(entry.panel_id, detector_id)
            callables.append({
                "role": "DETECTOR_SCORER",
                "callable_id": authority.scorer_callable_id,
                "source_byte_hash": authority.implementation_hash,
            })
        if role:
            runtime_path = repository_root / "src/paperworks/validation_v2/runtime_v1.py"
            adapter_path = repository_root / "src/paperworks/validation_v2/dg05_runtime_adapter_v4.py"
            callables.extend((
                {"role": "FORMAL_V4_EVALUATOR", "callable_id": "evaluate_formal_v4_semantics_v1",
                 "source_byte_hash": file_sha256(runtime_path)},
                {"role": "FOUR_WAY_RUNTIME_ADAPTER", "callable_id": "execute_rule_with_four_way_trace_v4",
                 "source_byte_hash": file_sha256(adapter_path)},
            ))
            if trace is None or trace.get("runtime_trace_origin") != "FROZEN_RULE_RUNTIME":
                raise DG05ProductionRouteV5Error("FROZEN_RULE_RUNTIME_TRACE_REQUIRED")
        if detector_id and role:
            fusion_path = repository_root / "src/paperworks/validation_v2/dg05_execution_closure_v1.py"
            callables.append({"role": "FUSION", "callable_id": "fuse_dense_masks_v1",
                              "source_byte_hash": file_sha256(fusion_path)})
        kernel_hash = digest(callables)
        self.rows.append({
            "cell_id": cell["cell_id"],
            "panel_id": cell["panel_id"],
            "method_id": cell["method_id"],
            "method_authority_hash": digest(entry.document()),
            "actual_callable_authorities": callables,
            "executed_scientific_kernel_hash": kernel_hash,
            "frozen_production_scientific_kernel_hash": kernel_hash,
            "execution_kernel_identity": "FROZEN_PRODUCTION_SCIENTIFIC_KERNEL_V1",
            "data_access_mode": getattr(executor, "data_access_mode", "PROTECTED_PRODUCTION"),
            "prediction_output_schema": "dense_boolean_prediction_v1",
            "runtime_trace_schema": "rule_trace_artifact_v4" if role else "NOT_APPLICABLE",
            "runtime_trace_origin": "FROZEN_RULE_RUNTIME" if role else "NOT_APPLICABLE",
            "production_kernel_invocation": True,
            "synthetic_fallback_invocation": False,
        })

    def document(
        self, *, release_manifest_hash: str, source_commit: str,
        executable_version: str = "DG05_EXECUTABLE_V5",
    ) -> dict[str, Any]:
        rows = sorted(self.rows, key=lambda row: row["cell_id"])
        return self_hashed({
            "schema": (
                "dg05_v6_production_kernel_invocation_census_v1"
                if executable_version == "DG05_EXECUTABLE_V6"
                else "dg05_v5_production_kernel_invocation_census_v1"
            ),
            "release_manifest_hash": release_manifest_hash,
            "invocation_count": len(rows),
            "production_kernel_invocation_count": sum(row["production_kernel_invocation"] for row in rows),
            "synthetic_fallback_invocation_count": sum(row["synthetic_fallback_invocation"] for row in rows),
            "rows": rows,
            "source_commit": source_commit,
        })


def validate_release_execution_kernel_v5(
    *, release: Mapping[str, Any], predecessor_v3: Mapping[str, Any],
    initialized_release_state: Mapping[str, Any], executor: Any,
) -> None:
    for value, schema in ((release, "dg05_production_release_manifest_v2"),
                          (predecessor_v3, "dg05_executable_authority_manifest_v3")):
        if value.get("schema") != schema or value.get("self_hash") != digest({k: v for k, v in value.items() if k != "self_hash"}):
            raise DG05ProductionRouteV5Error("RELEASE_OR_PREDECESSOR_REPLAY_FAILED")
    selected_executor = executor.frozen if type(executor) is PreaccessFrozenKernelExecutorV5 else executor
    common_invalid = (
        release.get("executable_version") not in {"DG05_EXECUTABLE_V5", "DG05_EXECUTABLE_V6"}
        or release.get("historical_execution_kernel_hash")
        != getattr(selected_executor, "executable_manifest_hash", None)
        or release.get("readiness") != "READY_FOR_USER_REAPPROVAL"
        or initialized_release_state.get("release_manifest_hash") != release["self_hash"]
        or initialized_release_state.get("execution_kernel_identity") != "FROZEN_PRODUCTION_SCIENTIFIC_KERNEL_V1"
        or initialized_release_state.get("schema") != "dg05_production_chain_state_v2"
        or initialized_release_state.get("self_hash") != digest({
            k: v for k, v in initialized_release_state.items() if k != "self_hash"
        })
        or initialized_release_state.get("predecessor_v4_manifest_hash") != release.get("predecessor_v4_manifest_hash")
        or initialized_release_state.get("implementation_authority_hash") != digest(release.get("implementation_authorities"))
        or initialized_release_state.get("nested_authority_hash") != digest(release.get("nested_authority_hashes"))
    )
    mode = initialized_release_state.get("authority_mode")
    if mode == PREACCESS_EXECUTION_MODE_V5:
        mode_invalid = (
            initialized_release_state.get("state") != "PREACCESS_FROZEN_KERNEL_RELEASE_INITIALIZED"
            or initialized_release_state.get("data_access_mode") != "SYNTHETIC_ONLY_NO_PROTECTED_DISCOVERY"
            or initialized_release_state.get("protected_access_authorized") is not False
            or type(executor) is not PreaccessFrozenKernelExecutorV5
        )
    elif mode == "PRODUCTION":
        mode_invalid = (
            initialized_release_state.get("state") != "APPROVED_PRODUCTION_RELEASE_INITIALIZED"
            or initialized_release_state.get("data_access_mode") != "PROTECTED_DATA_ACCESS_REQUIRES_EXACT_USER_APPROVAL"
            or initialized_release_state.get("protected_access_authorized") is not True
            or type(executor) is not DG05ProductionExecutorV1
            or getattr(executor, "authority_mode", None) != "PRODUCTION"
        )
    else:
        mode_invalid = True
    if common_invalid or mode_invalid:
        raise DG05ProductionRouteV5Error("V5_RELEASE_KERNEL_BINDING_MISMATCH")
    executor.validate()


def _projection_timestamps(path: Path, expected_hash: str) -> tuple[str, ...]:
    if file_sha256(path) != expected_hash:
        raise DG05ProductionRouteV5Error("PROJECTION_ARTIFACT_BYTE_REPLAY_MISMATCH")
    try:
        return tuple(str(json.loads(line.decode("ascii"))[0]) for line in path.read_bytes().splitlines()[1:])
    except (UnicodeDecodeError, json.JSONDecodeError, IndexError, TypeError) as exc:
        raise DG05ProductionRouteV5Error("PROJECTION_TIMESTAMP_REPLAY_FAILED") from exc


def execute_prediction_cell_v5(
    *, cell: Mapping[str, Any], dispatch: MethodDispatchRegistryV1, projection: Any,
    timestamp: Any, release: Mapping[str, Any], predecessor_v3: Mapping[str, Any],
    initialized_release_state: Mapping[str, Any], executor: Any,
    projection_path: Path, output_directory: Path, source_commit: str,
    repository_root: Path, invocation_census: KernelInvocationCensusV5,
) -> PredictionTerminalReceiptV1:
    """Execute one cell through the frozen production scientific kernel only."""
    validate_release_execution_kernel_v5(
        release=release, predecessor_v3=predecessor_v3,
        initialized_release_state=initialized_release_state, executor=executor)
    if release.get("source_commit") != source_commit:
        raise DG05ProductionRouteV5Error("RELEASE_SOURCE_COMMIT_MISMATCH")
    entry = dispatch.lookup(str(cell["panel_id"]), str(cell["method_id"]))
    expected_cell_id = digest({key: cell[key] for key in ("panel_id", "file_id", "method_id", "dispatch_authority_hash")})
    if cell.get("cell_id") != expected_cell_id or projection.panel_id != cell["panel_id"] or projection.file_id != cell["file_id"]:
        raise DG05ProductionRouteV5Error("CELL_PROJECTION_BINDING_MISMATCH")
    try:
        projection.validate()
        timestamp.validate()
    except ValueError as exc:
        raise DG05ProductionRouteV5Error("PROJECTION_TIMESTAMP_AUTHORITY_INVALID") from exc
    timestamp_hash = timestamp.document()["self_hash"]
    if (
        projection.timestamp_authority_hash != timestamp_hash
        or timestamp.projection_hash != projection.projection_hash
        or timestamp.physical_file_authority_hash != projection.raw_physical_file_hash
        or (timestamp.panel_id, timestamp.dataset_version, timestamp.file_id)
        != (projection.panel_id, projection.dataset_version, projection.file_id)
        or timestamp.row_count != projection.row_count
        or timestamp.source_commit != source_commit
        or projection.source_commit != source_commit
    ):
        raise DG05ProductionRouteV5Error("PROJECTION_TIMESTAMP_AUTHORITY_BINDING_MISMATCH")
    timestamps = _projection_timestamps(projection_path, projection.projection_hash)
    replayed_timestamp_hash = sha256(
        b"".join(value.encode("utf-8") + b"\n" for value in timestamps)
    ).hexdigest()
    if len(timestamps) != timestamp.row_count or replayed_timestamp_hash != timestamp.timestamp_vector_hash:
        raise DG05ProductionRouteV5Error("PROJECTION_TIMESTAMP_VECTOR_MISMATCH")
    timeline = build_physical_timeline_authority_v1(
        panel_id=cell["panel_id"], file_id=cell["file_id"], timestamps=timestamps,
        physical_file_authority_hash=projection.raw_physical_file_hash,
        projection_authority_hash=projection.projection_hash, source_commit=source_commit)
    method_hash = digest(entry.document())
    release_hash = release["self_hash"]
    try:
        require_valid_physical_timeline_v1(timeline)
    except ValueError as exc:
        failure = PredictionTerminalReceiptV1(
            expected_cell_id, entry.panel_id, projection.file_id, entry.method_id, method_hash,
            projection.raw_physical_file_hash, projection.projection_hash, timestamp_hash,
            projection.row_count, None, None, "NOT_APPLICABLE", "METHOD_FAILURE", str(exc),
            digest({"schema": "dense_boolean_prediction_v1"}), release_hash, source_commit)
        failure.validate()
        return failure
    try:
        feature_order, matrix = executor._projection_matrix(projection_path, projection)
        alarms, trace = execute_normal_method_v4(
            executor=executor, entry=entry, feature_order=feature_order, matrix=matrix,
            file_id=projection.file_id, projection_hash=projection.projection_hash, timestamps=timestamps)
        if trace is not None:
            trace = {**dict(trace), "runtime_trace_origin": "FROZEN_RULE_RUNTIME",
                     "synthetic_trace_reconstruction": False}
        if len(alarms) != projection.row_count or any(type(value) is not bool for value in alarms):
            raise DG05ProductionRouteV5Error("EXECUTOR_OUTPUT_SCHEMA_MISMATCH")
        invocation_census.record(cell=cell, entry=entry, executor=executor,
                                 repository_root=repository_root, trace=trace)
    except (DG05ClosureError, DG05ProductionRouteV5Error, ValueError) as exc:
        failure = PredictionTerminalReceiptV1(
            expected_cell_id, entry.panel_id, projection.file_id, entry.method_id, method_hash,
            projection.raw_physical_file_hash, projection.projection_hash, timestamp_hash,
            projection.row_count, None, None, "NOT_APPLICABLE", "METHOD_FAILURE", str(exc),
            digest({"schema": "dense_boolean_prediction_v1"}), release_hash, source_commit)
        failure.validate()
        return failure
    prediction = {"schema": "dense_boolean_prediction_v1", "cell_id": expected_cell_id,
                  "row_count": len(alarms), "alarms": list(alarms)}
    prediction_hash = publish_new(output_directory / f"{expected_cell_id}.prediction.json",
                                  canonical_bytes(prediction) + b"\n")
    trace_hash = None
    trace_status = "NOT_APPLICABLE"
    if trace is not None:
        trace_doc = self_hashed({
            "schema": "rule_trace_artifact_v4", "cell_id": expected_cell_id,
            "prediction_hash": prediction_hash, "projection_hash": projection.projection_hash,
            "timestamp_authority_hash": timestamp_hash, **dict(trace),
        })
        trace_hash = publish_new(output_directory / f"{expected_cell_id}.trace.json",
                                 canonical_bytes(trace_doc) + b"\n")
        trace_status = "BOUND"
    receipt = PredictionTerminalReceiptV1(
        expected_cell_id, entry.panel_id, projection.file_id, entry.method_id, method_hash,
        projection.raw_physical_file_hash, projection.projection_hash, timestamp_hash,
        projection.row_count, prediction_hash, trace_hash, trace_status, "SUCCESS", None,
        digest({"schema": "dense_boolean_prediction_v1"}), release_hash, source_commit)
    receipt.validate()
    return receipt


__all__ = [
    "DG05ProductionRouteV5Error",
    "KernelInvocationCensusV5",
    "execute_prediction_cell_v5",
    "validate_release_execution_kernel_v5",
]
