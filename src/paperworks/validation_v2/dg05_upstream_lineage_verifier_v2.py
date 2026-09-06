"""Independent path replay for the DEC-031/V2 upstream lineage.

This verifier does not call the production primitive extractor.  It reopens
projection, prediction, trace, scenario, denominator and normal-source bytes,
then constructs an independently derived primitive for comparison.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from .dg05_dec031_v1 import build_physical_timeline_authority_v1, derive_four_way_runtime_census_v1, require_valid_physical_timeline_v1
from .dg05_execution_closure_v1 import FROZEN_DATASET_VERSION_BY_PANEL_V1, FROZEN_METHOD_IDS_BY_PANEL_V1, validate_self_hashed
from .dg05_metric_surface_v1 import canonical_bytes, self_hashed
from .dg05_metric_surface_v2 import build_metric_primitives_v2
from .dg05_normal_source_v2 import replay_normal_source_registry_v2


class DG05UpstreamVerifierV2Error(ValueError):
    pass


@dataclass(frozen=True)
class UpstreamPanelReplayPathsV2:
    global_manifest_path: Path
    global_freeze_path: Path
    scenario_authority_path: Path
    denominator_authority_path: Path
    projection_paths: Mapping[str, Path]
    prediction_paths: Mapping[str, Path]
    trace_paths: Mapping[str, Path]
    normal_source_registry_path: Path
    normal_component_paths: Mapping[str, Path]
    asserted_primitive_path: Path


def _load(path: Path, schema: str, *, hashed: bool) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05UpstreamVerifierV2Error("CANONICAL_UPSTREAM_JSON_REQUIRED") from exc
    if raw != canonical_bytes(value) + b"\n" or value.get("schema") != schema:
        raise DG05UpstreamVerifierV2Error(f"UPSTREAM_SCHEMA_REPLAY_FAILED:{schema}")
    if hashed:
        validate_self_hashed(value)
    return value


def _coordinates(path: Path, expected_hash: str, panel_id: str, file_id: str,
                 source_commit: str) -> tuple[str, ...]:
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_hash:
        raise DG05UpstreamVerifierV2Error("UPSTREAM_PROJECTION_BYTE_MISMATCH")
    try:
        values = tuple(str(json.loads(line.decode("ascii"))[0]) for line in raw.splitlines()[1:])
    except (UnicodeDecodeError, json.JSONDecodeError, IndexError, TypeError) as exc:
        raise DG05UpstreamVerifierV2Error("UPSTREAM_PROJECTION_COORDINATE_REPLAY_FAILED") from exc
    timeline = build_physical_timeline_authority_v1(
        panel_id=panel_id, file_id=file_id, timestamps=values,
        physical_file_authority_hash=expected_hash, projection_authority_hash=expected_hash,
        source_commit=source_commit)
    require_valid_physical_timeline_v1(timeline)
    return values


def reconstruct_metric_primitive_from_upstream_v2(
    *, panel_id: str, paths: UpstreamPanelReplayPathsV2,
    expected_release_manifest_hash: str, expected_dec031_binding_hash: str,
    expected_normal_source_registry_hash: str, expected_global_freeze_hash: str,
    source_commit: str,
) -> dict[str, Any]:
    manifest = _load(paths.global_manifest_path, "global_prediction_manifest_v3", hashed=True)
    freeze = _load(paths.global_freeze_path, "global_prediction_freeze_v3", hashed=True)
    scenario = _load(paths.scenario_authority_path, "frozen_scenario_authority_v1", hashed=True)
    denominator = _load(paths.denominator_authority_path, "denominator_authority_v1", hashed=True)
    registry = _load(paths.normal_source_registry_path, "normal_burden_source_registry_v2", hashed=True)
    if (freeze.get("self_hash") != expected_global_freeze_hash
            or manifest.get("executable_approval_manifest_hash") != expected_release_manifest_hash
            or freeze.get("manifest_hash") != manifest["self_hash"]
            or freeze.get("executable_approval_manifest_hash") != expected_release_manifest_hash
            or scenario.get("global_freeze_hash") != freeze["self_hash"]
            or denominator.get("scenario_authority_hash") != scenario["self_hash"]
            or registry["self_hash"] != expected_normal_source_registry_hash):
        raise DG05UpstreamVerifierV2Error("UPSTREAM_ROOT_AUTHORITY_MISMATCH")
    normal = replay_normal_source_registry_v2(
        registry=registry, component_paths=paths.normal_component_paths,
        expected_dec031_binding_hash=expected_dec031_binding_hash)
    burden = {row["method_id"]: row for row in normal["methods"] if row["panel_id"] == panel_id}
    expected_methods = tuple(FROZEN_METHOD_IDS_BY_PANEL_V1[panel_id])
    if set(burden) != set(expected_methods):
        raise DG05UpstreamVerifierV2Error("UPSTREAM_NORMAL_METHOD_CENSUS_MISMATCH")
    receipts = [row for row in manifest.get("receipts", ()) if row.get("panel_id") == panel_id]
    if {row.get("method_id") for row in receipts} != set(expected_methods) or len({row.get("cell_id") for row in receipts}) != len(receipts):
        raise DG05UpstreamVerifierV2Error("UPSTREAM_PREDICTION_CENSUS_MISMATCH")
    file_ids = tuple(sorted({str(row["file_id"]) for row in receipts}))
    if set(paths.projection_paths) != set(file_ids):
        raise DG05UpstreamVerifierV2Error("UPSTREAM_PROJECTION_CENSUS_MISMATCH")
    timestamps: dict[str, tuple[str, ...]] = {}
    for file_id in file_ids:
        local = [row for row in receipts if row["file_id"] == file_id]
        hashes = {row["projection_hash"] for row in local}
        if len(hashes) != 1:
            raise DG05UpstreamVerifierV2Error("UPSTREAM_PROJECTION_AUTHORITY_DISAGREEMENT")
        timestamps[file_id] = _coordinates(paths.projection_paths[file_id], hashes.pop(), panel_id, file_id, source_commit)
        if any(row.get("row_count") != len(timestamps[file_id]) for row in local):
            raise DG05UpstreamVerifierV2Error("UPSTREAM_ROW_COUNT_MISMATCH")
    scenario_rows = {(row["panel_id"], row["scenario_id"]): row for row in scenario.get("records", ())}
    denominator_rows = {(row["panel_id"], row["scenario_id"]): row for row in denominator.get("records", ())}
    if len(scenario_rows) != len(scenario.get("records", ())) or set(scenario_rows) != set(denominator_rows):
        raise DG05UpstreamVerifierV2Error("UPSTREAM_SCENARIO_DENOMINATOR_CENSUS_MISMATCH")
    scenarios = []
    for key in sorted(value for value in scenario_rows if value[0] == panel_id):
        record, eligibility = scenario_rows[key], denominator_rows[key]
        intervals = record.get("closed_intervals")
        if (eligibility.get("scenario_record_hash") != record.get("self_hash") or type(intervals) is not list
                or not intervals or any(type(value) is not list or len(value) != 2 for value in intervals)
                or record.get("file_id") not in timestamps):
            raise DG05UpstreamVerifierV2Error("UPSTREAM_SCENARIO_BINDING_MISMATCH")
        scenarios.append({"scenario_id": record["scenario_id"], "file_id": record["file_id"],
                          "closed_intervals": intervals, "eligibility": eligibility["primary_status"],
                          "scenario_authority_hash": record["self_hash"],
                          "eligibility_authority_hash": eligibility["self_hash"]})
    methods: dict[str, dict[str, Any]] = {}
    for method_id in expected_methods:
        local = [row for row in receipts if row["method_id"] == method_id]
        if {row["file_id"] for row in local} != set(file_ids):
            raise DG05UpstreamVerifierV2Error("UPSTREAM_METHOD_FILE_CENSUS_MISMATCH")
        alarm_rows: dict[str, list[int]] = {}; alarm_times: dict[str, list[str]] = {}; traces = []; failed = False
        for receipt in local:
            if receipt["status"] == "METHOD_FAILURE":
                failed = True; continue
            path = paths.prediction_paths.get(receipt["cell_id"])
            if path is None or sha256(path.read_bytes()).hexdigest() != receipt["prediction_artifact_hash"]:
                raise DG05UpstreamVerifierV2Error("UPSTREAM_PREDICTION_BYTE_MISMATCH")
            prediction = _load(path, "dense_boolean_prediction_v1", hashed=False)
            values = prediction.get("alarms")
            if type(values) is not list or len(values) != len(timestamps[receipt["file_id"]]) or any(type(value) is not bool for value in values):
                raise DG05UpstreamVerifierV2Error("UPSTREAM_DENSE_PREDICTION_MISMATCH")
            rows = [index for index, value in enumerate(values) if value]
            alarm_rows[receipt["file_id"]] = rows
            alarm_times[receipt["file_id"]] = [timestamps[receipt["file_id"]][index] for index in rows]
            if receipt.get("trace_status") == "BOUND":
                trace_path = paths.trace_paths.get(receipt["cell_id"])
                if trace_path is None or sha256(trace_path.read_bytes()).hexdigest() != receipt.get("trace_artifact_hash"):
                    raise DG05UpstreamVerifierV2Error("UPSTREAM_TRACE_BYTE_MISMATCH")
                trace = _load(trace_path, "rule_trace_artifact_v4", hashed=True)
                traces.append(trace)
        census = None
        if "RULE" in method_id or "PLUS" in method_id:
            if not failed:
                if len(traces) != len(file_ids):
                    raise DG05UpstreamVerifierV2Error("UPSTREAM_COMPLETE_RULE_TRACE_CENSUS_REQUIRED")
                configured = traces[0].get("configured_rule_sources")
                if any(trace.get("configured_rule_sources") != configured for trace in traces):
                    raise DG05UpstreamVerifierV2Error("UPSTREAM_CONFIGURED_RULE_DISAGREEMENT")
                census = derive_four_way_runtime_census_v1(
                    configured_rule_sources=configured,
                    file_timestamps={file_id: timestamps[file_id] for file_id in file_ids}, traces=traces)
        methods[method_id] = {"status": "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE" if failed else "COMPLETE",
                              "timestamps_by_file": {key: list(value) for key, value in timestamps.items()},
                              "alarm_rows_by_file": alarm_rows, "alarm_timestamps_by_file": alarm_times,
                              "normal_burden": burden[method_id], "runtime_census": census}
    return build_metric_primitives_v2(
        panel_id=panel_id, dataset_version=FROZEN_DATASET_VERSION_BY_PANEL_V1[panel_id], scenarios=scenarios,
        methods=methods, authority_hashes={"executable": expected_release_manifest_hash,
            "prediction_manifest": manifest["self_hash"], "scenario": scenario["self_hash"],
            "denominator": denominator["self_hash"], "normal_burden": registry["self_hash"],
            "dec031": expected_dec031_binding_hash})


def verify_asserted_primitive_from_upstream_v2(
    *, panel_id: str, paths: UpstreamPanelReplayPathsV2,
    expected_release_manifest_hash: str, expected_dec031_binding_hash: str,
    expected_normal_source_registry_hash: str, expected_global_freeze_hash: str,
    source_commit: str,
) -> dict[str, Any]:
    asserted = _load(paths.asserted_primitive_path, "metric_surface_primitives_v2", hashed=True)
    replayed = reconstruct_metric_primitive_from_upstream_v2(
        panel_id=panel_id, paths=paths, expected_release_manifest_hash=expected_release_manifest_hash,
        expected_dec031_binding_hash=expected_dec031_binding_hash,
        expected_normal_source_registry_hash=expected_normal_source_registry_hash,
        expected_global_freeze_hash=expected_global_freeze_hash,
        source_commit=source_commit)
    if canonical_bytes(asserted) != canonical_bytes(replayed):
        raise DG05UpstreamVerifierV2Error("ASSERTED_PRIMITIVE_DISAGREES_WITH_FROZEN_UPSTREAM")
    return self_hashed({"schema": "dg05_upstream_metric_primitive_verification_v2", "status": "PASS",
                        "panel_id": panel_id, "asserted_primitive_hash": asserted["self_hash"],
                        "global_prediction_freeze_hash": expected_global_freeze_hash,
                        "normal_source_registry_hash": expected_normal_source_registry_hash,
                        "source_bytes_reopened": True, "production_primitive_builder_called": False})


__all__ = ["DG05UpstreamVerifierV2Error", "UpstreamPanelReplayPathsV2",
           "reconstruct_metric_primitive_from_upstream_v2", "verify_asserted_primitive_from_upstream_v2"]
