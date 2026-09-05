"""Independent read-only oracle for persisted DG-05 result authorities.

This module deliberately does not import the primary result builder.  It
replays canonical bytes and recomputes scenario arithmetic from already-frozen
prediction/timestamp inputs.  It never regenerates predictions.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
from typing import Any, Mapping, Sequence


class DG05ResultOracleError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _wilson(hits: int, total: int):
    if total == 0:
        return None
    z = 1.959963984540054
    p = hits / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - half), min(1.0, centre + half)]


def verify_result_from_frozen_inputs_v1(*, result_path: Path, receipt: Mapping[str, Any],
                                        predictions: Mapping[str, tuple[Sequence[str], Sequence[bool], str, str, str]],
                                        scenario_authority: Mapping[str, Any], denominator_authority: Mapping[str, Any],
                                        expected_bindings: Mapping[str, str]) -> dict[str, Any]:
    """Recompute a persisted result from frozen timestamp/alarm sequences.

    Prediction tuples are ``timestamps, alarms, prediction_hash,
    projection_hash, timestamp_authority_hash`` and must have been loaded from
    the frozen artifacts by the closure loader.
    """
    raw = result_path.read_bytes()
    if _file_hash(result_path) != receipt.get("artifact_byte_hash"):
        raise DG05ResultOracleError("RESULT_BYTE_RECEIPT_MISMATCH")
    result = json.loads(raw.decode("ascii"))
    body = {k: v for k, v in result.items() if k != "self_hash"}
    if result.get("self_hash") != sha256(_canonical(body)).hexdigest() or result.get("self_hash") != receipt.get("result_self_hash"):
        raise DG05ResultOracleError("RESULT_SELF_HASH_MISMATCH")
    for field, expected in expected_bindings.items():
        if result.get(field) != expected:
            raise DG05ResultOracleError(f"NESTED_AUTHORITY_MISMATCH:{field}")
    eligible = {row["scenario_id"] for row in denominator_authority["records"]
                if row["panel_id"] == result["panel_id"] and row["primary_status"] == "P1_ELIGIBLE"}
    failures = result["failure_receipt_hashes"]
    if failures:
        if result["completeness_status"] != "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE" or result["scenario_recall"] is not None:
            raise DG05ResultOracleError("INCOMPLETE_RESULT_PARTIAL_RECALL_PROHIBITED")
        return {"schema": "dg05_independent_result_oracle_v1", "status": "PASS", "predictions_regenerated": False,
                "result_self_hash": result["self_hash"], "artifact_byte_hash": receipt["artifact_byte_hash"],
                "recomputed_status": result["completeness_status"]}
    expected_hits = []
    for scenario in scenario_authority["records"]:
        if scenario["panel_id"] != result["panel_id"] or scenario["scenario_id"] not in eligible:
            continue
        if scenario["file_id"] not in predictions:
            raise DG05ResultOracleError("PREDICTION_FILE_MISSING")
        timestamps, alarms, prediction_hash, projection_hash, timestamp_hash = predictions[scenario["file_id"]]
        if len(timestamps) != len(alarms) or timestamp_hash != scenario["timestamp_authority_hash"]:
            raise DG05ResultOracleError("TIMESTAMP_SCENARIO_BINDING_MISMATCH")
        alarm_times = [datetime.fromisoformat(timestamps[i]) for i, alarm in enumerate(alarms) if alarm]
        hit = any(any(datetime.fromisoformat(start) <= alarm <= datetime.fromisoformat(end) for alarm in alarm_times)
                  for start, end in scenario["closed_intervals"])
        expected_hits.append({"scenario_id": scenario["scenario_id"], "scenario_record_hash": scenario["self_hash"],
                              "hit": hit, "physical_file_id": scenario["file_id"], "prediction_hash": prediction_hash,
                              "projection_hash": projection_hash, "timestamp_authority_hash": timestamp_hash})
    hits = sum(row["hit"] for row in expected_hits)
    total = len(expected_hits)
    if result["scenario_hits"] != expected_hits or result["hit_count"] != hits or result["eligible_count"] != total:
        raise DG05ResultOracleError("RECOMPUTED_SCENARIO_RESULT_MISMATCH")
    if result["scenario_recall"] != (None if total == 0 else hits / total) or result["wilson95"] != _wilson(hits, total):
        raise DG05ResultOracleError("RECOMPUTED_METRIC_MISMATCH")
    return {"schema": "dg05_independent_result_oracle_v1", "status": "PASS", "predictions_regenerated": False,
            "result_self_hash": result["self_hash"], "artifact_byte_hash": receipt["artifact_byte_hash"],
            "recomputed_hit_count": hits, "recomputed_eligible_count": total}


__all__ = ["DG05ResultOracleError", "verify_result_from_frozen_inputs_v1"]
