"""Independent, path-only replay oracle for DG-05 result authorities.

The oracle accepts no parsed alarm or timestamp arrays and does not import the
primary result builder/loader. Every scientific input is reopened from a
persisted, hash-bound artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
from typing import Any, Mapping


class DG05ResultOracleError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _file_hash(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_hashed(path: Path, schema: str) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DG05ResultOracleError("NONCANONICAL_JSON_ARTIFACT") from exc
    if type(value) is not dict or value.get("schema") != schema:
        raise DG05ResultOracleError(f"SCHEMA_MISMATCH:{schema}")
    body = {k: v for k, v in value.items() if k != "self_hash"}
    if value.get("self_hash") != sha256(_canonical(body)).hexdigest():
        raise DG05ResultOracleError(f"SELF_HASH_MISMATCH:{schema}")
    if raw != _canonical(value) + b"\n":
        raise DG05ResultOracleError(f"CANONICAL_BYTE_MISMATCH:{schema}")
    return value


def _wilson(hits: int, total: int):
    if total == 0:
        return None
    z = 1.959963984540054
    p = hits / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - half), min(1.0, centre + half)]


@dataclass(frozen=True)
class FrozenResultReplayPathsV1:
    executable_manifest_path: Path
    dispatch_registry_path: Path
    cell_census_path: Path
    result_path: Path
    result_receipt_path: Path
    global_manifest_path: Path
    global_freeze_path: Path
    scenario_authority_path: Path
    denominator_authority_path: Path
    etapr_coordinate_binding_path: Path
    terminal_receipt_paths: Mapping[str, Path]
    prediction_paths: Mapping[str, Path]
    projection_authority_paths: Mapping[str, Path]
    projection_paths: Mapping[str, Path]
    timestamp_authority_paths: Mapping[str, Path]


def verify_result_from_persisted_artifacts_v1(
    *, paths: FrozenResultReplayPathsV1, expected_executable_manifest_hash: str,
    expected_metric_authority_hash: str, expected_p1_custodian_hash: str,
    expected_etapr_authority_hash: str, expected_statistical_authority_hash: str,
    expected_normal_burden_hash: str,
) -> dict[str, Any]:
    result = _load_hashed(paths.result_path, "panel_method_result_authority_v1")
    receipt = _load_hashed(paths.result_receipt_path, "result_authority_artifact_receipt_v1")
    if _file_hash(paths.result_path) != receipt.get("artifact_byte_hash") or result["self_hash"] != receipt.get("result_self_hash"):
        raise DG05ResultOracleError("RESULT_BYTE_RECEIPT_MISMATCH")
    executable = _load_hashed(paths.executable_manifest_path, "dg05_executable_authority_manifest_v1")
    dispatch = _load_hashed(paths.dispatch_registry_path, "method_dispatch_registry_v1")
    census = _load_hashed(paths.cell_census_path, "expected_prediction_cell_census_builder_v1")
    manifest = _load_hashed(paths.global_manifest_path, "global_prediction_manifest_v3")
    freeze = _load_hashed(paths.global_freeze_path, "global_prediction_freeze_v3")
    scenario = _load_hashed(paths.scenario_authority_path, "frozen_scenario_authority_v1")
    denominator = _load_hashed(paths.denominator_authority_path, "denominator_authority_v1")
    etapr_binding = _load_hashed(paths.etapr_coordinate_binding_path, "etapr_coordinate_binding_v1")
    if executable["self_hash"] != expected_executable_manifest_hash or executable.get("dispatch_registry_hash") != dispatch["self_hash"]:
        raise DG05ResultOracleError("EXECUTABLE_DISPATCH_AUTHORITY_MISMATCH")
    if census.get("dispatch_registry_hash") != dispatch["self_hash"] or census.get("count") != len(census.get("cells", ())):
        raise DG05ResultOracleError("CELL_CENSUS_DISPATCH_OR_COUNT_MISMATCH")
    cells = {row["cell_id"]: row for row in census["cells"]}
    if len(cells) != len(census["cells"]):
        raise DG05ResultOracleError("DUPLICATE_CELL_CENSUS")
    for cell_id, row in cells.items():
        expected_cell_id = sha256(_canonical({k: row[k] for k in ("panel_id", "file_id", "method_id", "dispatch_authority_hash")})).hexdigest()
        if cell_id != expected_cell_id or row["dispatch_authority_hash"] != dispatch["self_hash"]:
            raise DG05ResultOracleError("CELL_CENSUS_IDENTITY_MISMATCH")
    if (manifest.get("expected_cell_census_hash") != census["self_hash"]
            or manifest.get("executable_approval_manifest_hash") != expected_executable_manifest_hash
            or len(manifest.get("receipts", ())) != len(cells)):
        raise DG05ResultOracleError("GLOBAL_MANIFEST_CENSUS_OR_EXECUTABLE_MISMATCH")
    if (freeze.get("manifest_hash") != manifest["self_hash"]
            or freeze.get("census_hash") != census["self_hash"]
            or freeze.get("executable_approval_manifest_hash") != expected_executable_manifest_hash):
        raise DG05ResultOracleError("GLOBAL_FREEZE_MANIFEST_MISMATCH")
    dispatch_entries = {(row["panel_id"], row["method_id"]): row for row in dispatch.get("entries", ())}
    if len(dispatch_entries) != len(dispatch.get("entries", ())):
        raise DG05ResultOracleError("DUPLICATE_DISPATCH_ENTRY")
    embedded_by_cell: dict[str, dict[str, Any]] = {}
    for embedded in manifest["receipts"]:
        body = {k: v for k, v in embedded.items() if k != "self_hash"}
        if embedded.get("self_hash") != sha256(_canonical(body)).hexdigest():
            raise DG05ResultOracleError("EMBEDDED_TERMINAL_RECEIPT_SELF_HASH_MISMATCH")
        cell = cells.get(embedded.get("cell_id"))
        entry = dispatch_entries.get((embedded.get("panel_id"), embedded.get("method_id")))
        if cell is None or entry is None or embedded.get("executable_manifest_hash") != expected_executable_manifest_hash:
            raise DG05ResultOracleError("TERMINAL_RECEIPT_AUTHORITY_MISMATCH")
        if (embedded.get("panel_id"), embedded.get("file_id"), embedded.get("method_id")) != (cell["panel_id"], cell["file_id"], cell["method_id"]):
            raise DG05ResultOracleError("TERMINAL_RECEIPT_CELL_BINDING_MISMATCH")
        if embedded.get("method_authority_hash") != sha256(_canonical(entry)).hexdigest():
            raise DG05ResultOracleError("TERMINAL_RECEIPT_METHOD_BINDING_MISMATCH")
        embedded_by_cell[embedded["cell_id"]] = embedded
    if set(embedded_by_cell) != set(cells):
        raise DG05ResultOracleError("GLOBAL_MANIFEST_TERMINAL_CENSUS_MISMATCH")
    if scenario.get("global_freeze_hash") != freeze["self_hash"] or denominator.get("scenario_authority_hash") != scenario["self_hash"]:
        raise DG05ResultOracleError("SCENARIO_DENOMINATOR_CHAIN_MISMATCH")
    expected = {
        "executable_approval_manifest_hash": expected_executable_manifest_hash,
        "prediction_manifest_hash": manifest["self_hash"],
        "scenario_authority_hash": scenario["self_hash"],
        "denominator_authority_hash": denominator["self_hash"],
        "metric_authority_hash": expected_metric_authority_hash,
        "p1_custodian_hash": expected_p1_custodian_hash,
        "etapr_authority_hash": expected_etapr_authority_hash,
        "statistical_authority_hash": expected_statistical_authority_hash,
        "normal_burden_hash": expected_normal_burden_hash,
        "etapr_coordinate_binding_hash": etapr_binding["self_hash"],
    }
    for field, value in expected.items():
        if result.get(field) != value:
            raise DG05ResultOracleError(f"NESTED_AUTHORITY_MISMATCH:{field}")
    if denominator.get("p1_custodian_v3_hash") != expected_p1_custodian_hash:
        raise DG05ResultOracleError("DENOMINATOR_P1_CUSTODIAN_MISMATCH")

    panel, method = result["panel_id"], result["method_id"]
    if etapr_binding.get("panel_id") != panel or etapr_binding.get("etapr_authority_hash") != expected_etapr_authority_hash:
        raise DG05ResultOracleError("ETAPR_PANEL_AUTHORITY_MISMATCH")
    selected = [row for row in manifest["receipts"] if row["panel_id"] == panel and row["method_id"] == method]
    if not selected:
        raise DG05ResultOracleError("NO_TERMINAL_RECEIPTS_FOR_RESULT")
    predictions: dict[str, tuple[tuple[str, ...], tuple[bool, ...], dict[str, Any], dict[str, Any]]] = {}
    failures: dict[str, str] = {}
    for embedded in selected:
        persisted = _load_hashed(paths.terminal_receipt_paths[embedded["cell_id"]], "prediction_terminal_receipt_v1")
        if persisted != embedded:
            raise DG05ResultOracleError("TERMINAL_RECEIPT_MANIFEST_MISMATCH")
        if persisted["status"] == "METHOD_FAILURE":
            failures[persisted["file_id"]] = persisted["self_hash"]
            continue
        prediction_path = paths.prediction_paths[persisted["cell_id"]]
        if _file_hash(prediction_path) != persisted["prediction_artifact_hash"]:
            raise DG05ResultOracleError("PREDICTION_BYTE_HASH_MISMATCH")
        prediction_raw = prediction_path.read_bytes()
        prediction = json.loads(prediction_raw.decode("ascii"))
        if prediction_raw != _canonical(prediction) + b"\n" or prediction.get("schema") != "dense_boolean_prediction_v1":
            raise DG05ResultOracleError("PREDICTION_SCHEMA_OR_CANONICAL_BYTES_MISMATCH")
        if prediction.get("cell_id") != persisted["cell_id"] or prediction.get("row_count") != persisted["row_count"]:
            raise DG05ResultOracleError("PREDICTION_RECEIPT_MISMATCH")
        alarms = tuple(prediction.get("alarms", ()))
        if len(alarms) != persisted["row_count"] or any(type(v) is not bool for v in alarms):
            raise DG05ResultOracleError("PREDICTION_ALARM_VECTOR_INVALID")
        projection = _load_hashed(paths.projection_authority_paths[persisted["file_id"]], "feature_only_projection_authority_v1")
        timestamp = _load_hashed(paths.timestamp_authority_paths[persisted["file_id"]], "timestamp_coordinate_authority_v1")
        projection_path = paths.projection_paths[persisted["file_id"]]
        if _file_hash(projection_path) != projection["projection_hash"] or projection["projection_hash"] != persisted["projection_hash"]:
            raise DG05ResultOracleError("PROJECTION_BYTE_OR_RECEIPT_MISMATCH")
        lines = projection_path.read_bytes().splitlines()
        timestamps = tuple(str(json.loads(line.decode("ascii"))[0]) for line in lines[1:])
        vector_hash = sha256(b"".join(value.encode("utf-8") + b"\n" for value in timestamps)).hexdigest()
        if len(timestamps) != persisted["row_count"] or vector_hash != timestamp["timestamp_vector_hash"]:
            raise DG05ResultOracleError("TIMESTAMP_VECTOR_REPLAY_MISMATCH")
        if timestamp["self_hash"] != persisted["timestamp_authority_hash"] or timestamp["projection_hash"] != projection["projection_hash"]:
            raise DG05ResultOracleError("TIMESTAMP_AUTHORITY_BINDING_MISMATCH")
        if projection.get("timestamp_authority_hash") != timestamp["self_hash"]:
            raise DG05ResultOracleError("PROJECTION_TIMESTAMP_AUTHORITY_BINDING_MISMATCH")
        if projection.get("raw_physical_file_hash") != timestamp.get("physical_file_authority_hash"):
            raise DG05ResultOracleError("PROJECTION_PHYSICAL_FILE_BINDING_MISMATCH")
        if (projection.get("row_count") != timestamp.get("row_count")
                or projection.get("row_count") != persisted.get("row_count")):
            raise DG05ResultOracleError("PROJECTION_TIMESTAMP_ROW_COUNT_BINDING_MISMATCH")
        if (projection["panel_id"], projection["dataset_version"], projection["file_id"]) != (panel, timestamp["dataset_version"], persisted["file_id"]):
            raise DG05ResultOracleError("PANEL_VERSION_FILE_BINDING_MISMATCH")
        predictions[persisted["file_id"]] = (timestamps, alarms, timestamp, projection)

    expected_etapr = {(row["file_id"], row["physical_file_authority_hash"], row["timestamp_authority_hash"],
                       row["prediction_artifact_hash"], row["scenario_authority_hash"])
                      for row in etapr_binding["file_bindings"]}
    actual_etapr = {(file_id, timestamp["physical_file_authority_hash"], timestamp["self_hash"],
                     next(r for r in selected if r["file_id"] == file_id)["prediction_artifact_hash"], scenario["self_hash"])
                    for file_id, (_timestamps, _alarms, timestamp, _projection) in predictions.items()}
    if expected_etapr != actual_etapr:
        raise DG05ResultOracleError("ETAPR_COORDINATE_REPLAY_MISMATCH")

    scenario_by_key = {(row["panel_id"], row["scenario_id"]): row for row in scenario["records"]}
    denominator_by_key = {(row["panel_id"], row["scenario_id"]): row for row in denominator["records"]}
    if len(scenario_by_key) != len(scenario["records"]) or len(denominator_by_key) != len(denominator["records"]) or set(scenario_by_key) != set(denominator_by_key):
        raise DG05ResultOracleError("SCENARIO_DENOMINATOR_CENSUS_MISMATCH")
    for key, scenario_row in scenario_by_key.items():
        body = {k: v for k, v in scenario_row.items() if k != "self_hash"}
        if scenario_row.get("self_hash") != sha256(_canonical(body)).hexdigest() or denominator_by_key[key].get("scenario_record_hash") != scenario_row["self_hash"]:
            raise DG05ResultOracleError("SCENARIO_DENOMINATOR_RECORD_BINDING_MISMATCH")

    if failures:
        if failures != result["failure_receipt_hashes"] or result["completeness_status"] != "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE":
            raise DG05ResultOracleError("FAILURE_COVERAGE_RESULT_MISMATCH")
        expected_eligible = sum(row["panel_id"] == panel and row["primary_status"] == "P1_ELIGIBLE" for row in denominator["records"])
        if (result["scenario_recall"] is not None or result["hit_count"] is not None or result["wilson95"] is not None
                or result["scenario_hits"] or result["eligible_count"] != expected_eligible):
            raise DG05ResultOracleError("PARTIAL_RECALL_PROHIBITED")
        return {"schema": "dg05_independent_result_oracle_v2", "status": "PASS", "inputs_reopened_from_paths": True,
                "result_self_hash": result["self_hash"], "artifact_byte_hash": receipt["artifact_byte_hash"],
                "recomputed_status": result["completeness_status"]}

    eligible_rows = [row for row in denominator["records"] if row["panel_id"] == panel and row["primary_status"] == "P1_ELIGIBLE"]
    expected_hits = []
    for eligibility in eligible_rows:
        record = scenario_by_key.get((panel, eligibility["scenario_id"]))
        if record is None or eligibility["scenario_record_hash"] != record["self_hash"]:
            raise DG05ResultOracleError("ELIGIBILITY_SCENARIO_BINDING_MISMATCH")
        timestamps, alarms, timestamp, projection = predictions[record["file_id"]]
        if record["timestamp_authority_hash"] != timestamp["self_hash"] or record["physical_file_authority_hash"] != timestamp["physical_file_authority_hash"]:
            raise DG05ResultOracleError("SCENARIO_COORDINATE_AUTHORITY_MISMATCH")
        alarm_times = [datetime.fromisoformat(timestamps[i]) for i, alarm in enumerate(alarms) if alarm]
        hit = any(any(datetime.fromisoformat(start) <= alarm <= datetime.fromisoformat(end) for alarm in alarm_times)
                  for start, end in record["closed_intervals"])
        terminal = next(r for r in selected if r["file_id"] == record["file_id"])
        expected_hits.append({"scenario_id": record["scenario_id"], "scenario_record_hash": record["self_hash"],
                              "hit": hit, "physical_file_id": record["file_id"],
                              "prediction_hash": terminal["prediction_artifact_hash"],
                              "projection_hash": projection["projection_hash"],
                              "timestamp_authority_hash": timestamp["self_hash"]})
    hits, total = sum(row["hit"] for row in expected_hits), len(expected_hits)
    if result["scenario_hits"] != expected_hits or result["hit_count"] != hits or result["eligible_count"] != total:
        raise DG05ResultOracleError("RECOMPUTED_SCENARIO_RESULT_MISMATCH")
    if result["scenario_recall"] != (None if total == 0 else hits / total) or result["wilson95"] != _wilson(hits, total):
        raise DG05ResultOracleError("RECOMPUTED_METRIC_MISMATCH")
    return {"schema": "dg05_independent_result_oracle_v2", "status": "PASS", "inputs_reopened_from_paths": True,
            "result_self_hash": result["self_hash"], "artifact_byte_hash": receipt["artifact_byte_hash"],
            "recomputed_hit_count": hits, "recomputed_eligible_count": total}


__all__ = ["DG05ResultOracleError", "FrozenResultReplayPathsV1", "verify_result_from_persisted_artifacts_v1"]
