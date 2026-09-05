"""Independent upstream-to-primitive replay for prospective DG-05 production.

This verifier never calls the production metric-primitive builder.  It reopens
the frozen prediction/scenario/denominator/trace/normal-source chain and
constructs the primitive document independently.  Production use remains
disabled until the scenario/time/runtime binding and normal source registry
are approved and complete.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from paperworks.validation_v2.dg05_execution_closure_v1 import (
    FROZEN_DATASET_VERSION_BY_PANEL_V1,
    FROZEN_METHOD_IDS_BY_PANEL_V1,
)
from paperworks.validation_v2.dg05_normal_burden_replay_v1 import replay_method_normal_burden_v1
from paperworks.validation_v2.dg05_production_chain_v1 import (
    canonical_bytes_v1,
    derive_runtime_census_strict_v1,
    digest_v1,
    file_sha256_v1,
    self_hashed_v1,
    validate_strict_one_second_coordinates_v1,
)


class DG05UpstreamVerifierError(ValueError):
    """Raised when an asserted primitive does not replay from upstream."""


@dataclass(frozen=True)
class UpstreamPanelReplayPathsV1:
    global_manifest_path: Path
    global_freeze_path: Path
    scenario_authority_path: Path
    denominator_authority_path: Path
    projection_paths: Mapping[str, Path]
    prediction_paths: Mapping[str, Path]
    trace_paths: Mapping[str, Path]
    normal_source_registry_path: Path
    normal_prediction_paths: Mapping[str, Path]
    normal_timestamp_paths: Mapping[str, Path]
    normal_coverage_paths: Mapping[str, Path]
    asserted_primitive_path: Path


def _load(path: Path, schema: str, *, self_hash: bool) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05UpstreamVerifierError("CANONICAL_UPSTREAM_JSON_REQUIRED") from exc
    if type(value) is not dict or value.get("schema") != schema or raw != canonical_bytes_v1(value) + b"\n":
        raise DG05UpstreamVerifierError(f"UPSTREAM_SCHEMA_OR_BYTE_REPLAY_FAILED:{schema}")
    if self_hash:
        body = {key: item for key, item in value.items() if key != "self_hash"}
        if value.get("self_hash") != digest_v1(body):
            raise DG05UpstreamVerifierError(f"UPSTREAM_SELF_HASH_REPLAY_FAILED:{schema}")
    return value


def _projection_coordinates(path: Path, expected_hash: str) -> tuple[str, ...]:
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_hash:
        raise DG05UpstreamVerifierError("PROJECTION_BYTE_REPLAY_MISMATCH")
    lines = raw.splitlines()
    if len(lines) < 2:
        raise DG05UpstreamVerifierError("EMPTY_PROJECTION")
    try:
        values = tuple(str(json.loads(line.decode("ascii"))[0]) for line in lines[1:])
    except (UnicodeDecodeError, json.JSONDecodeError, IndexError, TypeError) as exc:
        raise DG05UpstreamVerifierError("PROJECTION_COORDINATE_REPLAY_FAILED") from exc
    try:
        validate_strict_one_second_coordinates_v1(values)
    except ValueError as exc:
        raise DG05UpstreamVerifierError(str(exc)) from exc
    return values


def reconstruct_metric_primitive_from_upstream_v1(
    *,
    panel_id: str,
    paths: UpstreamPanelReplayPathsV1,
    expected_release_manifest_hash: str,
    approved_semantic_binding_hash: str,
) -> dict[str, Any]:
    """Rebuild one primitive solely from immutable upstream artifacts."""
    if len(expected_release_manifest_hash) != 64 or len(approved_semantic_binding_hash) != 64:
        raise DG05UpstreamVerifierError("APPROVED_RELEASE_AND_SEMANTIC_BINDING_REQUIRED")
    manifest = _load(paths.global_manifest_path, "global_prediction_manifest_v3", self_hash=True)
    freeze = _load(paths.global_freeze_path, "global_prediction_freeze_v3", self_hash=True)
    scenario = _load(paths.scenario_authority_path, "frozen_scenario_authority_v1", self_hash=True)
    denominator = _load(paths.denominator_authority_path, "denominator_authority_v1", self_hash=True)
    if (
        manifest.get("executable_approval_manifest_hash") != expected_release_manifest_hash
        or freeze.get("manifest_hash") != manifest["self_hash"]
        or freeze.get("executable_approval_manifest_hash") != expected_release_manifest_hash
        or scenario.get("global_freeze_hash") != freeze["self_hash"]
        or denominator.get("scenario_authority_hash") != scenario["self_hash"]
    ):
        raise DG05UpstreamVerifierError("UPSTREAM_AUTHORITY_CHAIN_MISMATCH")
    expected_methods = tuple(FROZEN_METHOD_IDS_BY_PANEL_V1[panel_id])
    receipts = [row for row in manifest.get("receipts", ()) if row.get("panel_id") == panel_id]
    for receipt in receipts:
        body = {key: item for key, item in receipt.items() if key != "self_hash"}
        if receipt.get("self_hash") != digest_v1(body):
            raise DG05UpstreamVerifierError("UPSTREAM_TERMINAL_RECEIPT_SELF_HASH_MISMATCH")
    if len({row.get("cell_id") for row in receipts}) != len(receipts):
        raise DG05UpstreamVerifierError("UPSTREAM_DUPLICATE_CELL_RECEIPT")
    if {row.get("method_id") for row in receipts} != set(expected_methods):
        raise DG05UpstreamVerifierError("UPSTREAM_PANEL_METHOD_CENSUS_MISMATCH")
    file_ids = tuple(sorted({str(row["file_id"]) for row in receipts}))
    if set(paths.projection_paths) != set(file_ids):
        raise DG05UpstreamVerifierError("UPSTREAM_PROJECTION_CENSUS_MISMATCH")

    coordinates: dict[str, tuple[str, ...]] = {}
    row_counts: dict[str, int] = {}
    for file_id in file_ids:
        local = [row for row in receipts if row["file_id"] == file_id]
        hashes = {str(row["projection_hash"]) for row in local}
        if len(hashes) != 1:
            raise DG05UpstreamVerifierError("UPSTREAM_PROJECTION_AUTHORITY_DISAGREEMENT")
        coordinates[file_id] = _projection_coordinates(paths.projection_paths[file_id], hashes.pop())
        row_counts[file_id] = len(coordinates[file_id])
        if any(row.get("row_count") != row_counts[file_id] for row in local):
            raise DG05UpstreamVerifierError("UPSTREAM_ROW_COUNT_MISMATCH")

    scenario_rows = {(row["panel_id"], row["scenario_id"]): row for row in scenario.get("records", ())}
    denominator_rows = {(row["panel_id"], row["scenario_id"]): row for row in denominator.get("records", ())}
    if len(scenario_rows) != len(scenario.get("records", ())) or set(scenario_rows) != set(denominator_rows):
        raise DG05UpstreamVerifierError("UPSTREAM_SCENARIO_DENOMINATOR_CENSUS_MISMATCH")
    primitive_scenarios: list[dict[str, Any]] = []
    for key in sorted(value for value in scenario_rows if value[0] == panel_id):
        record, eligibility = scenario_rows[key], denominator_rows[key]
        if eligibility.get("scenario_record_hash") != record.get("self_hash"):
            raise DG05UpstreamVerifierError("UPSTREAM_ELIGIBILITY_BINDING_MISMATCH")
        intervals = record.get("closed_intervals")
        if type(intervals) is not list or len(intervals) != 1 or type(intervals[0]) is not list or len(intervals[0]) != 2:
            raise DG05UpstreamVerifierError("SCIENTIFIC_BINDING_REQUIRED:MULTI_INTERVAL_PRIMITIVE_V2")
        try:
            start = coordinates[record["file_id"]].index(intervals[0][0])
            end = coordinates[record["file_id"]].index(intervals[0][1])
        except (KeyError, ValueError) as exc:
            raise DG05UpstreamVerifierError("SCENARIO_COORDINATE_REPLAY_MISMATCH") from exc
        primitive_scenarios.append(
            {
                "scenario_id": record["scenario_id"],
                "file_id": record["file_id"],
                "start": start,
                "end": end,
                "eligibility": eligibility["primary_status"],
                "scenario_authority_hash": record["self_hash"],
                "eligibility_authority_hash": eligibility["self_hash"],
            }
        )

    normal_registry = _load(paths.normal_source_registry_path, "normal_burden_source_registry_v1", self_hash=True)
    burden = replay_method_normal_burden_v1(
        source_registry=normal_registry,
        prediction_paths=paths.normal_prediction_paths,
        timestamp_paths=paths.normal_timestamp_paths,
        coverage_paths=paths.normal_coverage_paths,
        approved_time_binding_hash=approved_semantic_binding_hash,
    )
    burden_by_method = {
        row["method_id"]: {
            "authority_class": row["authority_class"],
            "opportunity_coverage": row["opportunity_coverage"],
            "components": row["components"],
        }
        for row in burden["methods"]
        if row["panel_id"] == panel_id
    }
    if set(burden_by_method) != set(expected_methods):
        raise DG05UpstreamVerifierError("UPSTREAM_NORMAL_BURDEN_METHOD_CENSUS_MISMATCH")

    methods: dict[str, dict[str, Any]] = {}
    for method_id in expected_methods:
        local = [row for row in receipts if row["method_id"] == method_id]
        if {row["file_id"] for row in local} != set(file_ids):
            raise DG05UpstreamVerifierError("UPSTREAM_METHOD_FILE_CENSUS_MISMATCH")
        alarms_by_file: dict[str, list[int]] = {}
        traces = []
        failure = False
        for receipt in local:
            if receipt["status"] == "METHOD_FAILURE":
                failure = True
                continue
            if receipt["status"] != "SUCCESS":
                raise DG05UpstreamVerifierError("UPSTREAM_TERMINAL_STATUS_INVALID")
            prediction_path = paths.prediction_paths.get(receipt["cell_id"])
            if prediction_path is None or file_sha256_v1(prediction_path) != receipt["prediction_artifact_hash"]:
                raise DG05UpstreamVerifierError("UPSTREAM_PREDICTION_BYTE_REPLAY_MISMATCH")
            prediction = _load(prediction_path, "dense_boolean_prediction_v1", self_hash=False)
            values = prediction.get("alarms")
            if prediction.get("cell_id") != receipt["cell_id"] or type(values) is not list or len(values) != receipt["row_count"] or any(type(v) is not bool for v in values):
                raise DG05UpstreamVerifierError("UPSTREAM_PREDICTION_RECEIPT_MISMATCH")
            alarms_by_file[receipt["file_id"]] = [index for index, value in enumerate(values) if value]
            if receipt.get("trace_status") == "BOUND":
                trace_path = paths.trace_paths.get(receipt["cell_id"])
                if trace_path is None or file_sha256_v1(trace_path) != receipt.get("trace_artifact_hash"):
                    raise DG05UpstreamVerifierError("UPSTREAM_TRACE_BYTE_REPLAY_MISMATCH")
                trace = _load(trace_path, "rule_trace_artifact_v2", self_hash=True)
                if trace.get("cell_id") != receipt["cell_id"] or trace.get("prediction_hash") != receipt["prediction_artifact_hash"]:
                    raise DG05UpstreamVerifierError("UPSTREAM_TRACE_PREDICTION_BINDING_MISMATCH")
                if method_id.endswith("RULE_ONLY") and trace.get("rule_alarm_rows") != alarms_by_file[receipt["file_id"]]:
                    raise DG05UpstreamVerifierError("RULE_ONLY_TRACE_ALARM_MISMATCH")
                traces.append(trace)
        if traces:
            derive_runtime_census_strict_v1(traces)
        methods[method_id] = {
            "status": "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE" if failure else "COMPLETE",
            "row_counts": dict(row_counts),
            "alarms_by_file": alarms_by_file,
            "normal_burden": burden_by_method[method_id],
            "runtime_traces": traces,
        }

    primitive = self_hashed_v1(
        {
            "schema": "metric_surface_primitives_v1",
            "panel_id": panel_id,
            "dataset_version": FROZEN_DATASET_VERSION_BY_PANEL_V1[panel_id],
            "scenarios": primitive_scenarios,
            "methods": {key: methods[key] for key in sorted(methods)},
            "authority_hashes": {
                "executable": expected_release_manifest_hash,
                "prediction_manifest": manifest["self_hash"],
                "scenario": scenario["self_hash"],
                "denominator": denominator["self_hash"],
                "normal_burden": normal_registry["self_hash"],
            },
            "label_or_attack_resource_paths": False,
        }
    )
    return primitive


def verify_asserted_primitive_from_upstream_v1(
    *,
    panel_id: str,
    paths: UpstreamPanelReplayPathsV1,
    expected_release_manifest_hash: str,
    approved_semantic_binding_hash: str,
) -> dict[str, Any]:
    asserted = _load(paths.asserted_primitive_path, "metric_surface_primitives_v1", self_hash=True)
    replayed = reconstruct_metric_primitive_from_upstream_v1(
        panel_id=panel_id,
        paths=paths,
        expected_release_manifest_hash=expected_release_manifest_hash,
        approved_semantic_binding_hash=approved_semantic_binding_hash,
    )
    if canonical_bytes_v1(asserted) != canonical_bytes_v1(replayed):
        raise DG05UpstreamVerifierError("ASSERTED_PRIMITIVE_DISAGREES_WITH_FROZEN_UPSTREAM")
    return self_hashed_v1(
        {
            "schema": "dg05_upstream_metric_primitive_verification_v1",
            "status": "PASS",
            "panel_id": panel_id,
            "asserted_primitive_hash": asserted["self_hash"],
            "global_manifest_byte_hash": file_sha256_v1(paths.global_manifest_path),
            "scenario_authority_byte_hash": file_sha256_v1(paths.scenario_authority_path),
            "denominator_authority_byte_hash": file_sha256_v1(paths.denominator_authority_path),
            "normal_source_registry_byte_hash": file_sha256_v1(paths.normal_source_registry_path),
            "production_primitive_builder_called": False,
        }
    )


__all__ = [
    "DG05UpstreamVerifierError",
    "UpstreamPanelReplayPathsV1",
    "reconstruct_metric_primitive_from_upstream_v1",
    "verify_asserted_primitive_from_upstream_v1",
]
