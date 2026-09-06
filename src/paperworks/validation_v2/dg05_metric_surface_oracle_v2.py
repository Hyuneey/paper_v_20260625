"""Independent arithmetic oracle for the DEC-031 metric surface."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from math import comb, sqrt
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence
import json

from .dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1
from .dg05_metric_surface_v1 import FROZEN_CONTRASTS, NONVALUE_STATUSES, SCIENTIFIC_HASHES, canonical_bytes, expected_surface_rows_v1, validate_self_hashed
from .dg05_metric_surface_oracle_v1 import _ranges, _score_engine
from .etapr_exchange_v1 import OfficialEtaprV1


class MetricSurfaceOracleV2Error(ValueError):
    pass


RULE_METHODS = {"M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2",
                "ISOLATION_FOREST_PLUS_T2", "V2A_RULE_ONLY_REFERENCE", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY"}


def _load(path: Path, schema: str) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MetricSurfaceOracleV2Error("CANONICAL_RESULT_ARTIFACT_REQUIRED") from exc
    if raw != canonical_bytes(value) + b"\n" or value.get("schema") != schema:
        raise MetricSurfaceOracleV2Error("RESULT_ARTIFACT_SCHEMA_REPLAY_FAILED")
    validate_self_hashed(value)
    return value


def _hits(scenarios: Sequence[Mapping[str, Any]], method: Mapping[str, Any]) -> list[dict[str, Any]]:
    output = []
    for scenario in sorted((row for row in scenarios if row["eligibility"] == "P1_ELIGIBLE"), key=lambda row: row["scenario_id"]):
        alarms = sorted(datetime.fromisoformat(value) for value in method["alarm_timestamps_by_file"][scenario["file_id"]])
        intervals = [(index, datetime.fromisoformat(value[0]), datetime.fromisoformat(value[1]))
                     for index, value in enumerate(scenario["closed_intervals"])]
        earliest = None; containing = []
        for alarm in alarms:
            local = [row for row in intervals if row[1] <= alarm <= row[2]]
            if local:
                earliest, containing = alarm, local; break
        if earliest is None:
            index = start = delay = None
        else:
            index, start_dt, _ = min(containing, key=lambda row: (row[1], row[0]))
            start = start_dt.isoformat()
            delay = format(Decimal(str((earliest - start_dt).total_seconds())), ".6f")
        output.append({"scenario_id": scenario["scenario_id"], "file_id": scenario["file_id"],
                       "scenario_authority_hash": scenario["scenario_authority_hash"],
                       "eligibility_authority_hash": scenario["eligibility_authority_hash"],
                       "hit": earliest is not None, "earliest_hit_timestamp": None if earliest is None else earliest.isoformat(),
                       "containing_interval_index": index, "containing_interval_start": start,
                       "interval_local_delay_seconds": delay,
                       "detection_delay_status": "NOT_DETECTED" if earliest is None else "DEFINED",
                       "delay_terminology": "INTERVAL_LOCAL_DETECTION_DELAY"})
    return output


def _delay(hits: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    values = sorted(Decimal(row["interval_local_delay_seconds"]) for row in hits if row["hit"])
    individual = [{"scenario_id": row["scenario_id"], "status": "PASS" if row["hit"] else "NOT_DETECTED",
                   "earliest_hit_timestamp": row["earliest_hit_timestamp"],
                   "containing_interval_index": row["containing_interval_index"],
                   "containing_interval_start": row["containing_interval_start"],
                   "interval_local_delay_seconds": row["interval_local_delay_seconds"],
                   "terminology": "INTERVAL_LOCAL_DETECTION_DELAY"} for row in hits]
    if not values:
        return individual, {"detected": 0, "not_detected": len(hits), "median_seconds": None,
                            "iqr_seconds": None, "terminology": "INTERVAL_LOCAL_DETECTION_DELAY"}
    def q(fraction: Decimal) -> Decimal:
        position = Decimal(len(values) - 1) * fraction; low = int(position); high = min(low + 1, len(values) - 1)
        return values[low] * (1 - (position - low)) + values[high] * (position - low)
    return individual, {"detected": len(values), "not_detected": len(hits) - len(values),
                        "median_seconds": format(median(values), ".6f"),
                        "iqr_seconds": format(q(Decimal("0.75")) - q(Decimal("0.25")), ".6f"),
                        "terminology": "INTERVAL_LOCAL_DETECTION_DELAY"}


def _wilson(k: int, n: int) -> list[float] | None:
    if n == 0: return None
    z = 1.959963984540054; p = k / n; d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, centre - half), min(1.0, centre + half)]


def _burden(value: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    components = value["components"]
    seconds = sum(row["false_seconds"] for row in components); episodes = sum(row["false_episodes"] for row in components)
    exposure = sum(row["exposure_seconds"] for row in components)
    if (seconds, episodes, exposure) != (value["false_seconds"], value["false_episodes"], value["exposure_seconds"]):
        raise MetricSurfaceOracleV2Error("ORACLE_NORMAL_BURDEN_ARITHMETIC_MISMATCH")
    if value["false_seconds_per_hour"] != seconds * 3600 / exposure or value["false_episodes_per_hour"] != episodes * 3600 / exposure:
        raise MetricSurfaceOracleV2Error("ORACLE_NORMAL_BURDEN_RATE_MISMATCH")
    payload = dict(value); payload["source_bytes_reopened"] = True
    return ("ZERO" if seconds == episodes == 0 else "PASS"), payload


def _etapr(wrapper: OfficialEtaprV1, scenarios: Sequence[Mapping[str, Any]], method: Mapping[str, Any]) -> dict[str, Any]:
    references = {file_id: [] for file_id in method["timestamps_by_file"]}
    for scenario in scenarios:
        if scenario["eligibility"] != "P1_ELIGIBLE": continue
        file_id = scenario["file_id"]
        timeline = [datetime.fromisoformat(value) for value in method["timestamps_by_file"][file_id]]
        for a, b in scenario["closed_intervals"]:
            start, end = datetime.fromisoformat(a), datetime.fromisoformat(b)
            inside = [index for index, value in enumerate(timeline) if start <= value <= end]
            if inside: references[file_id].append((inside[0], inside[-1]))
    per_file = []
    for file_id in sorted(references):
        refs = tuple(sorted(references[file_id])); preds = _ranges(method["alarm_rows_by_file"][file_id])
        base = {"file_id": file_id, "reference_range_count": len(refs), "prediction_range_count": len(preds)}
        if not refs: per_file.append({**base, "status": "NOT_APPLICABLE", "eTaP": None, "eTaR": None, "F1": None})
        elif not preds: per_file.append({**base, "status": "PASS_EMPTY_PREDICTION", "eTaP": 0.0, "eTaR": 0.0, "F1": 0.0})
        else:
            p, r, f = _score_engine(wrapper, refs, preds, file_id)
            per_file.append({**base, "status": "PASS", "eTaP": p, "eTaR": r, "F1": f})
    count = sum(row["prediction_range_count"] for row in per_file)
    scope = "P1_ELIGIBLE_OFFICIAL_SCENARIO_RANGES_WITH_ALL_FILE_LOCAL_PREDICTION_RANGES"
    if not any(references.values()): return {"status": "NOT_APPLICABLE", "eTaP": None, "eTaR": None, "F1": None, "prediction_range_count": count, "per_file": per_file, "target_scope": scope}
    if count == 0: return {"status": "PASS_EMPTY_PREDICTION", "eTaP": 0.0, "eTaR": 0.0, "F1": 0.0, "prediction_range_count": 0, "per_file": per_file, "target_scope": scope}
    refs_union = []; preds_union = []; offset = 0
    for file_id in sorted(references):
        refs_union.extend((offset + a, offset + b) for a, b in sorted(references[file_id]))
        preds_union.extend((offset + a, offset + b) for a, b in _ranges(method["alarm_rows_by_file"][file_id]))
        offset += len(method["timestamps_by_file"][file_id]) + 1024
    p, r, f = _score_engine(wrapper, refs_union, preds_union, "union")
    return {"status": "PASS", "eTaP": p, "eTaR": r, "F1": f, "prediction_range_count": count,
            "file_count": len(references), "separator": 1024, "file_order": "LEXICAL_FILE_ID", "per_file": per_file,
            "target_scope": scope}


def _expected(primitive: Mapping[str, Any], wrapper: OfficialEtaprV1) -> dict[str, tuple[str, Any]]:
    panel = primitive["panel_id"]; output = {}; all_hits = {}; burdens = {}
    method_kinds = ("SCENARIO_HIT_MISS", "SCENARIO_RECALL", "WILSON95", "DETECTION_DELAY", "DELAY_SUMMARY", "NORMAL_BURDEN", "ETAPR_PER_FILE", "ETAPR_VERSION_UNION")
    for method_id in FROZEN_METHOD_IDS_BY_PANEL_V1[panel]:
        method = primitive["methods"][method_id]; prefix = f"{panel}|METHOD|{method_id}|"
        if method["status"] == "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE":
            for kind in method_kinds + (("RULE_RUNTIME_CENSUS",) if method_id in RULE_METHODS else ()): output[prefix + kind] = (method["status"], None)
            all_hits[method_id] = []; burdens[method_id] = None; continue
        hits = _hits(primitive["scenarios"], method); all_hits[method_id] = hits
        n = len(hits); k = sum(row["hit"] for row in hits)
        output[prefix + "SCENARIO_HIT_MISS"] = ("NOT_EVALUABLE", None) if n == 0 else ("PASS", hits)
        output[prefix + "SCENARIO_RECALL"] = (("NOT_EVALUABLE", None) if n == 0 else (("ZERO" if k == 0 else "PASS"), {"hits": k, "eligible": n, "recall": k/n, "denominator_authority_hash": primitive["authority_hashes"]["denominator"]}))
        output[prefix + "WILSON95"] = ("NOT_EVALUABLE", None) if n == 0 else ("PASS", {"hits": k, "eligible": n, "interval": _wilson(k, n)})
        individual, summary = _delay(hits)
        output[prefix + "DETECTION_DELAY"] = ("NOT_EVALUABLE", None) if n == 0 else ("PASS", individual)
        output[prefix + "DELAY_SUMMARY"] = ("NOT_EVALUABLE", None) if n == 0 else ("PASS", summary)
        burden_status, burden = _burden(method["normal_burden"]); burdens[method_id] = burden
        output[prefix + "NORMAL_BURDEN"] = (burden_status, burden)
        eta = _etapr(wrapper, primitive["scenarios"], method)
        per_status = "NOT_APPLICABLE" if all(row["status"] == "NOT_APPLICABLE" for row in eta["per_file"]) else "PASS"
        output[prefix + "ETAPR_PER_FILE"] = (per_status, None if per_status == "NOT_APPLICABLE" else eta["per_file"])
        union_status = "NOT_APPLICABLE" if eta["status"] == "NOT_APPLICABLE" else ("ZERO" if eta["F1"] == 0 else "PASS")
        output[prefix + "ETAPR_VERSION_UNION"] = (union_status, None if union_status == "NOT_APPLICABLE" else eta)
        if method_id in RULE_METHODS:
            census = method["runtime_census"]
            output[prefix + "RULE_RUNTIME_CENSUS"] = ("ZERO" if census["opportunities"] == 0 else "PASS", census)
    for cid, (a, b) in FROZEN_CONTRASTS.items():
        prefix = f"{panel}|CONTRAST|{cid}|"
        if not all_hits[a] or not all_hits[b]:
            output[prefix + "PAIRED_TABLE"] = ("NOT_EVALUABLE", None); output[prefix + "MCNEMAR_EXACT"] = ("NOT_EVALUABLE", None); continue
        left = {row["scenario_id"]: row for row in all_hits[a]}; right = {row["scenario_id"]: row for row in all_hits[b]}
        table = {"both_hit": sum(left[k]["hit"] and right[k]["hit"] for k in left), "a_only": sum(left[k]["hit"] and not right[k]["hit"] for k in left), "b_only": sum(not left[k]["hit"] and right[k]["hit"] for k in left), "neither": sum(not left[k]["hit"] and not right[k]["hit"] for k in left), "eligible": len(left), "hit_count_difference": sum(v["hit"] for v in left.values()) - sum(v["hit"] for v in right.values()), "method_a": a, "method_b": b}
        output[prefix + "PAIRED_TABLE"] = ("PASS", table)
        n = table["a_only"] + table["b_only"]
        output[prefix + "MCNEMAR_EXACT"] = ("NOT_APPLICABLE", None) if n == 0 else ("PASS", {"p_value": min(1.0, 2 * sum(comb(n, i) for i in range(min(table["a_only"], table["b_only"]) + 1)) / (2 ** n)), "discordant": n, "implementation": "EXACT_TWO_SIDED_BINOMIAL"})
    core = ("M0_PCA_SPE", "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2"); rid = f"{panel}|PANEL|RECOVERY|RULE_FUSION_RECOVERY"
    if any(not all_hits[name] for name in core): output[rid] = ("NOT_EVALUABLE", None)
    else:
        maps = {name: {row["scenario_id"]: row["hit"] for row in all_hits[name]} for name in core}; misses = sorted(key for key, value in maps["M0_PCA_SPE"].items() if not value)
        payload = {"pca_miss_scenario_ids": misses, "t0_rule_response_ids": [k for k in misses if maps["M1_T0_RULE_ONLY"][k]], "t2_rule_response_ids": [k for k in misses if maps["M2_T2_RULE_ONLY"][k]], "pca_t0_actual_recovery_ids": [k for k in misses if maps["M3_PCA_PLUS_T0"][k]], "pca_t2_actual_recovery_ids": [k for k in misses if maps["M4_PCA_PLUS_T2"][k]], "incremental_recall_t0": (sum(maps["M3_PCA_PLUS_T0"].values()) - sum(maps["M0_PCA_SPE"].values())) / len(maps["M0_PCA_SPE"]), "incremental_recall_t2": (sum(maps["M4_PCA_PLUS_T2"].values()) - sum(maps["M0_PCA_SPE"].values())) / len(maps["M0_PCA_SPE"]), "incremental_false_seconds_per_hour_t0": burdens["M3_PCA_PLUS_T0"]["false_seconds_per_hour"] - burdens["M0_PCA_SPE"]["false_seconds_per_hour"], "incremental_false_seconds_per_hour_t2": burdens["M4_PCA_PLUS_T2"]["false_seconds_per_hour"] - burdens["M0_PCA_SPE"]["false_seconds_per_hour"]}
        output[rid] = ("ZERO" if not misses else "PASS", payload)
    return output


def verify_complete_metric_surface_from_paths_v2(*, primitive_path: Path, result_path: Path,
                                                  contract_path: Path, wrapper: OfficialEtaprV1,
                                                  expected_executable_hash: str) -> dict[str, Any]:
    primitive = _load(primitive_path, "metric_surface_primitives_v2"); result = _load(result_path, "complete_panel_metric_surface_v2"); contract = _load(contract_path, "metric_surface_contract_v2")
    if primitive["authority_hashes"]["executable"] != expected_executable_hash or result["executable_manifest_hash"] != expected_executable_hash or result["primitive_authority_hash"] != primitive["self_hash"] or result["contract_hash"] != contract["self_hash"]:
        raise MetricSurfaceOracleV2Error("RESULT_ROOT_BINDING_MISMATCH")
    contract_ids = {row["surface_id"] for row in contract["surfaces"]}; expected_all = {row["surface_id"] for row in expected_surface_rows_v1()}
    if contract_ids != expected_all: raise MetricSurfaceOracleV2Error("CONTRACT_SURFACE_CENSUS_MISMATCH")
    rows = result["surfaces"]; actual = {row["surface_id"]: row for row in rows}; expected = _expected(primitive, wrapper)
    if len(actual) != len(rows) or set(actual) != set(expected): raise MetricSurfaceOracleV2Error("RESULT_SURFACE_CENSUS_MISMATCH")
    bindings = {**primitive["authority_hashes"], **SCIENTIFIC_HASHES, "contract": contract["self_hash"]}
    for surface_id, (status, payload) in expected.items():
        row = actual[surface_id]
        if row != {"surface_id": surface_id, "status": status, "payload": payload, "authority_bindings": bindings}:
            raise MetricSurfaceOracleV2Error(f"RECOMPUTED_SURFACE_MISMATCH:{surface_id}")
        if status in NONVALUE_STATUSES and payload is not None: raise MetricSurfaceOracleV2Error("NONVALUE_PAYLOAD_CONFLICT")
    return {"schema": "independent_metric_surface_verification_v2", "status": "PASS", "panel_id": primitive["panel_id"],
            "primitive_hash": primitive["self_hash"], "result_hash": result["self_hash"], "contract_hash": contract["self_hash"],
            "verified_surface_count": len(expected), "production_builder_called": False}


__all__ = ["MetricSurfaceOracleV2Error", "verify_complete_metric_surface_from_paths_v2"]
