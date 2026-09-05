"""Independent path-only recomputation oracle for DG-05 V3 surfaces.

This module intentionally does not import the production metric-surface
builder, its helpers, or multipanel metric wrappers.  It reopens canonical
primitive/result bytes and independently implements the frozen arithmetic.
"""
from __future__ import annotations

from hashlib import sha256
import json
from math import comb, isfinite, sqrt
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

from .dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1
from .etapr_exchange_v1 import OfficialEtaprV1


class MetricSurfaceOracleError(ValueError):
    pass


PANELS = (
    "HAI23_TEST2_PRIMARY_HELDOUT_V1", "HAI22_EXTERNAL_REPLICATION_V1", "HAI21_EXTERNAL_REPLICATION_V1",
)
CONTRASTS = {"C1": ("M2_T2_RULE_ONLY", "M1_T0_RULE_ONLY"),
             "C2": ("M4_PCA_PLUS_T2", "M0_PCA_SPE"),
             "C3": ("M3_PCA_PLUS_T0", "M0_PCA_SPE"),
             "C4": ("M4_PCA_PLUS_T2", "M3_PCA_PLUS_T0")}
METHOD_KINDS = ("SCENARIO_HIT_MISS", "SCENARIO_RECALL", "WILSON95", "DETECTION_DELAY", "DELAY_SUMMARY",
                "NORMAL_BURDEN", "ETAPR_PER_FILE", "ETAPR_VERSION_UNION")
RULE_METHODS = {"M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2",
                "ISOLATION_FOREST_PLUS_T2", "V2A_RULE_ONLY_REFERENCE", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY"}
NONVALUES = {"NOT_DETECTED", "NOT_EVALUABLE", "NOT_APPLICABLE", "INVALID_AUTHORITY",
             "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE"}


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise MetricSurfaceOracleError("NONCANONICAL_OR_NONFINITE") from exc


def _digest(value: Any) -> str:
    return sha256(_canonical(value)).hexdigest()


def _load(path: Path, schema: str) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MetricSurfaceOracleError("INVALID_CANONICAL_JSON") from exc
    if type(value) is not dict or value.get("schema") != schema:
        raise MetricSurfaceOracleError("SCHEMA_MISMATCH")
    if value.get("self_hash") != _digest({k: v for k, v in value.items() if k != "self_hash"}):
        raise MetricSurfaceOracleError("SELF_HASH_MISMATCH")
    if raw != _canonical(value) + b"\n":
        raise MetricSurfaceOracleError("CANONICAL_BYTE_MISMATCH")
    return value


def _surface_ids() -> set[str]:
    output = set()
    for panel in PANELS:
        for method in FROZEN_METHOD_IDS_BY_PANEL_V1[panel]:
            output.update(f"{panel}|METHOD|{method}|{kind}" for kind in METHOD_KINDS)
            if method in RULE_METHODS:
                output.add(f"{panel}|METHOD|{method}|RULE_RUNTIME_CENSUS")
        for contrast in CONTRASTS:
            output.add(f"{panel}|CONTRAST|{contrast}|PAIRED_TABLE")
            output.add(f"{panel}|CONTRAST|{contrast}|MCNEMAR_EXACT")
        output.add(f"{panel}|PANEL|RECOVERY|RULE_FUSION_RECOVERY")
    return output


def independent_supported_surface_ids_v1() -> tuple[str, ...]:
    return tuple(sorted(_surface_ids()))


def _hits(scenarios: Sequence[Mapping[str, Any]], alarms: Mapping[str, Sequence[int]]) -> list[dict[str, Any]]:
    output = []
    for scenario in sorted((v for v in scenarios if v["eligibility"] == "P1_ELIGIBLE"), key=lambda v: v["scenario_id"]):
        values = tuple(alarms[scenario["file_id"]])
        if values != tuple(sorted(set(values))):
            raise MetricSurfaceOracleError("INVALID_ALARM_COORDINATES")
        inside = [v for v in values if scenario["start"] <= v <= scenario["end"]]
        output.append({"scenario_id": scenario["scenario_id"], "file_id": scenario["file_id"],
                       "scenario_authority_hash": scenario["scenario_authority_hash"],
                       "eligibility_authority_hash": scenario["eligibility_authority_hash"],
                       "hit": bool(inside), "delay": None if not inside else min(inside) - scenario["start"]})
    return output


def _wilson(k: int, n: int) -> list[float] | None:
    if n == 0:
        return None
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, centre - half), min(1.0, centre + half)]


def _delay(hits: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    individual = [{"scenario_id": v["scenario_id"], "status": "NOT_DETECTED", "value": None}
                  if v["delay"] is None else {"scenario_id": v["scenario_id"], "status": "PASS", "value": v["delay"]}
                  for v in hits]
    detected = sorted(v["delay"] for v in hits if v["delay"] is not None)
    if not detected:
        return individual, {"detected": 0, "not_detected": len(hits), "median": None, "iqr": None}
    def quantile(fraction: float) -> float:
        position = (len(detected) - 1) * fraction
        lo, hi = int(position), min(int(position) + 1, len(detected) - 1)
        return detected[lo] * (1 - position + lo) + detected[hi] * (position - lo)
    return individual, {"detected": len(detected), "not_detected": len(hits) - len(detected),
                        "median": median(detected), "iqr": quantile(.75) - quantile(.25)}


def _burden(value: Mapping[str, Any]) -> tuple[str, Any]:
    components = value.get("components")
    if type(components) is not list or not components:
        return "INVALID_AUTHORITY", None
    totals = {k: 0 for k in ("false_seconds", "false_episodes", "exposure_seconds", "abstain", "opportunities", "evaluated")}
    for row in components:
        for field in totals:
            if type(row.get(field)) is not int or row[field] < 0:
                return "INVALID_AUTHORITY", None
            totals[field] += row[field]
        if row["exposure_seconds"] == 0 or row["evaluated"] > row["opportunities"]:
            return "INVALID_AUTHORITY", None
    hours = totals["exposure_seconds"] / 3600
    payload = {"authority_class": value["authority_class"], "components": components,
               "false_seconds": totals["false_seconds"], "false_episodes": totals["false_episodes"],
               "exposure_seconds": totals["exposure_seconds"],
               "false_seconds_per_hour": totals["false_seconds"] / hours,
               "false_episodes_per_hour": totals["false_episodes"] / hours,
               "abstain_rate": None if totals["opportunities"] == 0 else totals["abstain"] / totals["opportunities"],
               "opportunity_coverage": value.get("opportunity_coverage"),
               "evaluation_coverage": None if totals["opportunities"] == 0 else totals["evaluated"] / totals["opportunities"]}
    return ("ZERO" if totals["false_seconds"] == totals["false_episodes"] == 0 else "PASS"), payload


def _ranges(values: Sequence[int]) -> tuple[tuple[int, int], ...]:
    values = tuple(sorted(set(values)))
    if not values:
        return ()
    result = []; start = previous = values[0]
    for value in values[1:]:
        if value != previous + 1:
            result.append((start, previous)); start = value
        previous = value
    result.append((start, previous))
    return tuple(result)


def _score_engine(wrapper: OfficialEtaprV1, references: Sequence[tuple[int, int]],
                  predictions: Sequence[tuple[int, int]], prefix: str) -> tuple[float, float, float]:
    engine = wrapper._engine_class(theta_p=.5, theta_r=.1, delta=0.0)
    engine.set([wrapper._range_class(a, b, f"{prefix}:r{i}") for i, (a, b) in enumerate(references)],
               [wrapper._range_class(a, b, f"{prefix}:p{i}") for i, (a, b) in enumerate(predictions)])
    precision, recall = float(engine.eTaP()), float(engine.eTaR())
    if not all(isfinite(v) and 0 <= v <= 1 for v in (precision, recall)):
        raise MetricSurfaceOracleError("INVALID_ETAPR_OUTPUT")
    return precision, recall, 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def _etapr(wrapper: OfficialEtaprV1, scenarios: Sequence[Mapping[str, Any]], method: Mapping[str, Any]) -> dict[str, Any]:
    references = {file_id: [] for file_id in method["row_counts"]}
    for row in scenarios:
        if row["eligibility"] == "P1_ELIGIBLE":
            references[row["file_id"]].append((row["start"], row["end"]))
    ordered = sorted(method["row_counts"])
    per_file = []
    for file_id in ordered:
        refs = tuple(sorted(references[file_id])); preds = _ranges(method["alarms_by_file"][file_id])
        base = {"file_id": file_id, "reference_range_count": len(refs), "prediction_range_count": len(preds)}
        if not refs:
            per_file.append({**base, "status": "NOT_APPLICABLE", "eTaP": None, "eTaR": None, "F1": None})
        elif not preds:
            per_file.append({**base, "status": "PASS_EMPTY_PREDICTION", "eTaP": 0.0, "eTaR": 0.0, "F1": 0.0})
        else:
            p, r, f = _score_engine(wrapper, refs, preds, file_id)
            per_file.append({**base, "status": "PASS", "eTaP": p, "eTaR": r, "F1": f})
    prediction_count = sum(row["prediction_range_count"] for row in per_file)
    target = "P1_ELIGIBLE_OFFICIAL_SCENARIO_RANGES_WITH_ALL_FILE_LOCAL_PREDICTION_RANGES"
    if not any(references.values()):
        return {"status": "NOT_APPLICABLE", "eTaP": None, "eTaR": None, "F1": None,
                "prediction_range_count": prediction_count, "per_file": per_file, "target_scope": target}
    if prediction_count == 0:
        return {"status": "PASS_EMPTY_PREDICTION", "eTaP": 0.0, "eTaR": 0.0, "F1": 0.0,
                "prediction_range_count": 0, "per_file": per_file, "target_scope": target}
    refs_union = []; preds_union = []; offset = 0
    for namespace, file_id in enumerate(ordered):
        refs_union.extend((offset + a, offset + b) for a, b in sorted(references[file_id]))
        preds_union.extend((offset + a, offset + b) for a, b in _ranges(method["alarms_by_file"][file_id]))
        offset += method["row_counts"][file_id] + 1024
    p, r, f = _score_engine(wrapper, refs_union, preds_union, "union")
    return {"status": "PASS", "eTaP": p, "eTaR": r, "F1": f, "prediction_range_count": prediction_count,
            "file_count": len(ordered), "separator": 1024, "file_order": "LEXICAL_FILE_ID", "per_file": per_file,
            "target_scope": target}


def _runtime(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    totals = {k: 0 for k in ("opportunities", "pass", "fail", "abstain", "system_errors")}
    rules = set(); sources = set(); episodes = 0
    for row in traces:
        if row["opportunities"] != row["pass"] + row["fail"] + row["abstain"] + row["system_errors"]:
            raise MetricSurfaceOracleError("RUNTIME_CENSUS_INVARIANT")
        for key in totals:
            totals[key] += row[key]
        rules.update(row.get("rule_ids", ())); sources.update(row.get("physical_source_ids", ()))
        episodes += row.get("rule_alarm_episodes", 0)
    return {**totals, "participating_rules": sorted(rules), "participating_source_identities": sorted(sources),
            "rule_alarm_episodes": episodes}


def _expected_by_id(primitive: Mapping[str, Any], wrapper: OfficialEtaprV1) -> dict[str, tuple[str, Any]]:
    panel = primitive["panel_id"]
    output: dict[str, tuple[str, Any]] = {}
    all_hits: dict[str, list[dict[str, Any]]] = {}; burdens: dict[str, Any] = {}
    for method_id in FROZEN_METHOD_IDS_BY_PANEL_V1[panel]:
        method = primitive["methods"][method_id]; prefix = f"{panel}|METHOD|{method_id}|"
        kinds = METHOD_KINDS + (("RULE_RUNTIME_CENSUS",) if method_id in RULE_METHODS else ())
        if method.get("status") == "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE":
            for kind in kinds:
                output[prefix + kind] = ("NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE", None)
            all_hits[method_id] = []; burdens[method_id] = None
            continue
        hits = _hits(primitive["scenarios"], method["alarms_by_file"]); all_hits[method_id] = hits
        n, k = len(hits), sum(v["hit"] for v in hits)
        output[prefix + "SCENARIO_HIT_MISS"] = ("NOT_EVALUABLE", None) if n == 0 else ("PASS", hits)
        recall = None if n == 0 else {"hits": k, "eligible": n, "recall": k/n,
                                     "denominator_authority_hash": primitive["authority_hashes"]["denominator"]}
        output[prefix + "SCENARIO_RECALL"] = ("NOT_EVALUABLE" if n == 0 else ("ZERO" if k == 0 else "PASS"), recall)
        output[prefix + "WILSON95"] = ("NOT_EVALUABLE", None) if n == 0 else ("PASS", {"hits": k, "eligible": n, "interval": _wilson(k, n)})
        individual, summary = _delay(hits)
        output[prefix + "DETECTION_DELAY"] = ("NOT_EVALUABLE", None) if n == 0 else ("PASS", individual)
        output[prefix + "DELAY_SUMMARY"] = ("NOT_EVALUABLE", None) if n == 0 else ("PASS", summary)
        burden_status, burden = _burden(method["normal_burden"]); burdens[method_id] = burden
        output[prefix + "NORMAL_BURDEN"] = (burden_status, burden)
        eta = _etapr(wrapper, primitive["scenarios"], method)
        per_status = "NOT_APPLICABLE" if all(v["status"] == "NOT_APPLICABLE" for v in eta["per_file"]) else "PASS"
        output[prefix + "ETAPR_PER_FILE"] = (per_status, None if per_status == "NOT_APPLICABLE" else eta["per_file"])
        union_status = "NOT_APPLICABLE" if eta["status"] == "NOT_APPLICABLE" else ("ZERO" if eta["F1"] == 0 else "PASS")
        output[prefix + "ETAPR_VERSION_UNION"] = (union_status, None if union_status == "NOT_APPLICABLE" else eta)
        if method_id in RULE_METHODS:
            census = _runtime(method["runtime_traces"])
            output[prefix + "RULE_RUNTIME_CENSUS"] = ("ZERO" if census["opportunities"] == 0 else "PASS", census)
    for cid, (a, b) in CONTRASTS.items():
        prefix = f"{panel}|CONTRAST|{cid}|"
        if not all_hits[a] or not all_hits[b]:
            output[prefix + "PAIRED_TABLE"] = ("NOT_EVALUABLE", None)
            output[prefix + "MCNEMAR_EXACT"] = ("NOT_EVALUABLE", None)
            continue
        left = {v["scenario_id"]: v for v in all_hits[a]}; right = {v["scenario_id"]: v for v in all_hits[b]}
        if set(left) != set(right) or any((left[k]["file_id"], left[k]["scenario_authority_hash"], left[k]["eligibility_authority_hash"]) !=
                                          (right[k]["file_id"], right[k]["scenario_authority_hash"], right[k]["eligibility_authority_hash"]) for k in left):
            raise MetricSurfaceOracleError("PAIRED_AUTHORITY_MISMATCH")
        table = {"both_hit": sum(left[k]["hit"] and right[k]["hit"] for k in left),
                 "a_only": sum(left[k]["hit"] and not right[k]["hit"] for k in left),
                 "b_only": sum(not left[k]["hit"] and right[k]["hit"] for k in left),
                 "neither": sum(not left[k]["hit"] and not right[k]["hit"] for k in left),
                 "eligible": len(left), "hit_count_difference": sum(v["hit"] for v in left.values()) - sum(v["hit"] for v in right.values()),
                 "method_a": a, "method_b": b}
        output[prefix + "PAIRED_TABLE"] = ("PASS", table)
        discordant = table["a_only"] + table["b_only"]
        if discordant == 0:
            output[prefix + "MCNEMAR_EXACT"] = ("NOT_APPLICABLE", None)
        else:
            p = min(1.0, 2 * sum(comb(discordant, k) for k in range(min(table["a_only"], table["b_only"]) + 1)) / (2 ** discordant))
            output[prefix + "MCNEMAR_EXACT"] = ("PASS", {"p_value": p, "discordant": discordant, "implementation": "EXACT_TWO_SIDED_BINOMIAL"})
    core = ("M0_PCA_SPE", "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2")
    rid = f"{panel}|PANEL|RECOVERY|RULE_FUSION_RECOVERY"
    if any(not all_hits[v] for v in core):
        output[rid] = ("NOT_EVALUABLE", None)
    elif any(burdens[v] is None for v in ("M0_PCA_SPE", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2")):
        output[rid] = ("INVALID_AUTHORITY", None)
    else:
        maps = {name: {v["scenario_id"]: v["hit"] for v in all_hits[name]} for name in core}
        misses = sorted(k for k, hit in maps["M0_PCA_SPE"].items() if not hit)
        payload = {"pca_miss_scenario_ids": misses,
                   "t0_rule_response_ids": [k for k in misses if maps["M1_T0_RULE_ONLY"][k]],
                   "t2_rule_response_ids": [k for k in misses if maps["M2_T2_RULE_ONLY"][k]],
                   "pca_t0_actual_recovery_ids": [k for k in misses if maps["M3_PCA_PLUS_T0"][k]],
                   "pca_t2_actual_recovery_ids": [k for k in misses if maps["M4_PCA_PLUS_T2"][k]],
                   "incremental_recall_t0": (sum(maps["M3_PCA_PLUS_T0"].values()) - sum(maps["M0_PCA_SPE"].values())) / len(maps["M0_PCA_SPE"]),
                   "incremental_recall_t2": (sum(maps["M4_PCA_PLUS_T2"].values()) - sum(maps["M0_PCA_SPE"].values())) / len(maps["M0_PCA_SPE"]),
                   "incremental_false_seconds_per_hour_t0": burdens["M3_PCA_PLUS_T0"]["false_seconds_per_hour"] - burdens["M0_PCA_SPE"]["false_seconds_per_hour"],
                   "incremental_false_seconds_per_hour_t2": burdens["M4_PCA_PLUS_T2"]["false_seconds_per_hour"] - burdens["M0_PCA_SPE"]["false_seconds_per_hour"]}
        output[rid] = ("ZERO" if not misses else "PASS", payload)
    return output


def verify_complete_metric_surface_from_paths_v1(*, primitive_path: Path, result_path: Path,
                                                  contract_path: Path, wrapper: OfficialEtaprV1,
                                                  expected_executable_hash: str) -> dict[str, Any]:
    primitive = _load(primitive_path, "metric_surface_primitives_v1")
    result = _load(result_path, "complete_panel_metric_surface_v1")
    contract = _load(contract_path, "metric_surface_contract_v1")
    expected_contract_ids = {v["surface_id"] for v in contract["surfaces"]}
    if expected_contract_ids != _surface_ids():
        raise MetricSurfaceOracleError("CONTRACT_SURFACE_CENSUS_MISMATCH")
    if primitive["authority_hashes"]["executable"] != expected_executable_hash or result["executable_manifest_hash"] != expected_executable_hash:
        raise MetricSurfaceOracleError("EXECUTABLE_BINDING_MISMATCH")
    if result["primitive_authority_hash"] != primitive["self_hash"] or result["contract_hash"] != contract["self_hash"]:
        raise MetricSurfaceOracleError("PRIMITIVE_OR_CONTRACT_BINDING_MISMATCH")
    rows = result["surfaces"]
    actual = {v["surface_id"]: v for v in rows}
    expected_panel_ids = {v for v in _surface_ids() if v.startswith(primitive["panel_id"] + "|")}
    if len(actual) != len(rows) or set(actual) != expected_panel_ids:
        raise MetricSurfaceOracleError("MISSING_DUPLICATE_OR_UNEXPECTED_SURFACE")
    expected = _expected_by_id(primitive, wrapper)
    if set(expected) != expected_panel_ids:
        raise MetricSurfaceOracleError("VERIFIER_IMPLEMENTATION_SURFACE_GAP")
    required_bindings = {**primitive["authority_hashes"], **result["scientific_authorities"], "contract": contract["self_hash"]}
    for surface_id, (status, payload) in expected.items():
        row = actual[surface_id]
        if set(row) != {"surface_id", "status", "payload", "authority_bindings"}:
            raise MetricSurfaceOracleError("SURFACE_SCHEMA_MISMATCH")
        if row["status"] != status or row["payload"] != payload:
            raise MetricSurfaceOracleError(f"RECOMPUTED_SURFACE_MISMATCH:{surface_id}")
        if row["authority_bindings"] != required_bindings:
            raise MetricSurfaceOracleError("SURFACE_AUTHORITY_BINDING_MISMATCH")
        if status in NONVALUES and payload is not None:
            raise MetricSurfaceOracleError("NONVALUE_STATUS_PAYLOAD_CONFLICT")
    return {"schema": "independent_complete_metric_surface_oracle_v1", "status": "PASS",
            "inputs_reopened_from_paths": True, "builder_imported": False,
            "surface_count": len(actual), "result_self_hash": result["self_hash"]}


__all__ = ["MetricSurfaceOracleError", "independent_supported_surface_ids_v1",
           "verify_complete_metric_surface_from_paths_v1"]
