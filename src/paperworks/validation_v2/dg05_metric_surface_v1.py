"""Complete DG-05 V3 metric-surface production builder.

This module is additive.  Historical DG-05 V2 result authorities remain
unchanged.  Inputs are typed, canonical, pre-frozen primitive authorities;
the module contains no data discovery or label-access capability.
"""
from __future__ import annotations

from hashlib import sha256
import json
from math import comb, sqrt
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

from .dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1
from .etapr_exchange_v1 import EtaprFileExchangeV1, OfficialEtaprV1
from .multipanel_etapr_v2 import score_namespaced_union_v2


class MetricSurfaceError(ValueError):
    """Fail-closed metric-surface contract violation."""


FROZEN_PANEL_ORDER = (
    "HAI23_TEST2_PRIMARY_HELDOUT_V1",
    "HAI22_EXTERNAL_REPLICATION_V1",
    "HAI21_EXTERNAL_REPLICATION_V1",
)
FROZEN_CONTRASTS = {
    "C1": ("M2_T2_RULE_ONLY", "M1_T0_RULE_ONLY"),
    "C2": ("M4_PCA_PLUS_T2", "M0_PCA_SPE"),
    "C3": ("M3_PCA_PLUS_T0", "M0_PCA_SPE"),
    "C4": ("M4_PCA_PLUS_T2", "M3_PCA_PLUS_T0"),
}
METHOD_SURFACES = (
    "SCENARIO_HIT_MISS", "SCENARIO_RECALL", "WILSON95",
    "DETECTION_DELAY", "DELAY_SUMMARY", "NORMAL_BURDEN",
    "ETAPR_PER_FILE", "ETAPR_VERSION_UNION",
)
CONTRAST_SURFACES = ("PAIRED_TABLE", "MCNEMAR_EXACT")
RECOVERY_SURFACE = "RULE_FUSION_RECOVERY"
RUNTIME_SURFACE = "RULE_RUNTIME_CENSUS"
NONVALUE_STATUSES = {
    "NOT_DETECTED", "NOT_EVALUABLE", "NOT_APPLICABLE",
    "INVALID_AUTHORITY", "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE",
}
SCIENTIFIC_HASHES = {
    "scientific_preregistration": "cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61",
    "method_bundle": "dab320da47489e5093862b7c4675523c3e6b710faceb753e7f39c8e56f002fe2",
    "metric": "1222d0c7431376dbfa77451875f811123f41af881ae1472b30cd4a2e0f1f0776",
    "etapr": "5381ceb1f19f25354a8feb36488dfaa85d3f2945770dc352f2bf8c18fd86cae4",
    "statistical": "cf90fee47e9294873e09aa516df8163328ee924d756c66b18a811c4ea2f9b463",
    "fusion": "587868f42fbdaedbd802541763e0390c09d2f04e4ba5944c45ad7e6e6593cbcc",
}


def canonical_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MetricSurfaceError("NONCANONICAL_OR_NONFINITE_VALUE") from exc
    return text.encode("ascii")


def digest(value: Any) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def self_hashed(body: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(body)
    value["self_hash"] = digest(value)
    return value


def validate_self_hashed(value: Mapping[str, Any], schema: str | None = None) -> None:
    if type(value) is not dict or (schema is not None and value.get("schema") != schema):
        raise MetricSurfaceError("SCHEMA_MISMATCH")
    if value.get("self_hash") != digest({k: v for k, v in value.items() if k != "self_hash"}):
        raise MetricSurfaceError("SELF_HASH_MISMATCH")


def _is_rule_method(method_id: str) -> bool:
    return method_id in {
        "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2",
        "ISOLATION_FOREST_PLUS_T2", "V2A_RULE_ONLY_REFERENCE", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY",
    }


def expected_surface_rows_v1() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for panel in FROZEN_PANEL_ORDER:
        for method in FROZEN_METHOD_IDS_BY_PANEL_V1[panel]:
            for kind in METHOD_SURFACES:
                rows.append({"surface_id": f"{panel}|METHOD|{method}|{kind}", "panel_id": panel,
                             "scope": "METHOD", "subject_id": method, "metric_surface": kind})
            if _is_rule_method(method):
                rows.append({"surface_id": f"{panel}|METHOD|{method}|{RUNTIME_SURFACE}", "panel_id": panel,
                             "scope": "METHOD", "subject_id": method, "metric_surface": RUNTIME_SURFACE})
        for contrast, pair in FROZEN_CONTRASTS.items():
            for kind in CONTRAST_SURFACES:
                rows.append({"surface_id": f"{panel}|CONTRAST|{contrast}|{kind}", "panel_id": panel,
                             "scope": "CONTRAST", "subject_id": contrast, "metric_surface": kind,
                             "method_a": pair[0], "method_b": pair[1]})
        rows.append({"surface_id": f"{panel}|PANEL|RECOVERY|{RECOVERY_SURFACE}", "panel_id": panel,
                     "scope": "PANEL", "subject_id": "RECOVERY", "metric_surface": RECOVERY_SURFACE})
    return sorted(rows, key=lambda row: row["surface_id"])


def build_metric_surface_contract_v1(*, source_commit: str) -> dict[str, Any]:
    rows = expected_surface_rows_v1()
    return self_hashed({
        "schema": "metric_surface_contract_v1", "executable_version": "DG05_EXECUTABLE_V3",
        "scientific_authorities": SCIENTIFIC_HASHES, "source_commit": source_commit,
        "status_types": ["PASS", "ZERO", *sorted(NONVALUE_STATUSES)],
        "nonvalue_payload_rule": "PAYLOAD_MUST_BE_NULL_EXCEPT_TYPED_CHILD_RECORDS",
        "surfaces": rows, "required_surface_count": len(rows), "cross_version_primary_pooling": False,
    })


def build_expected_result_surface_v1(contract: Mapping[str, Any]) -> dict[str, Any]:
    validate_self_hashed(contract, "metric_surface_contract_v1")
    return self_hashed({"schema": "expected_result_surface_builder_v1", "contract_hash": contract["self_hash"],
                        "surface_ids": [row["surface_id"] for row in contract["surfaces"]],
                        "surface_count": len(contract["surfaces"]), "exact_set_required": True})


def build_metric_primitives_v1(*, panel_id: str, dataset_version: str,
                               scenarios: Sequence[Mapping[str, Any]], methods: Mapping[str, Mapping[str, Any]],
                               authority_hashes: Mapping[str, str]) -> dict[str, Any]:
    if panel_id not in FROZEN_PANEL_ORDER or set(methods) != set(FROZEN_METHOD_IDS_BY_PANEL_V1[panel_id]):
        raise MetricSurfaceError("FROZEN_PANEL_METHOD_CENSUS_MISMATCH")
    if set(authority_hashes) != {"executable", "prediction_manifest", "scenario", "denominator", "normal_burden"}:
        raise MetricSurfaceError("PRIMITIVE_AUTHORITY_CENSUS_MISMATCH")
    if any(type(v) is not str or len(v) != 64 for v in authority_hashes.values()):
        raise MetricSurfaceError("SHA256_AUTHORITY_REQUIRED")
    ids = [str(row.get("scenario_id", "")) for row in scenarios]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        raise MetricSurfaceError("DUPLICATE_OR_EMPTY_SCENARIO_ID")
    return self_hashed({"schema": "metric_surface_primitives_v1", "panel_id": panel_id,
                        "dataset_version": dataset_version, "scenarios": [dict(v) for v in scenarios],
                        "methods": {k: dict(v) for k, v in sorted(methods.items())},
                        "authority_hashes": dict(authority_hashes), "label_or_attack_resource_paths": False})


def _surface(surface_id: str, status: str, payload: Any, bindings: Mapping[str, str]) -> dict[str, Any]:
    if status in NONVALUE_STATUSES and payload is not None:
        raise MetricSurfaceError("NONVALUE_STATUS_WITH_NUMERIC_PAYLOAD")
    if status not in {"PASS", "ZERO", *NONVALUE_STATUSES}:
        raise MetricSurfaceError("UNKNOWN_TYPED_STATUS")
    return {"surface_id": surface_id, "status": status, "payload": payload, "authority_bindings": dict(bindings)}


def _scenario_hits(scenarios: Sequence[Mapping[str, Any]], alarms: Mapping[str, Sequence[int]]) -> list[dict[str, Any]]:
    out = []
    for row in sorted((v for v in scenarios if v["eligibility"] == "P1_ELIGIBLE"), key=lambda v: v["scenario_id"]):
        if row["file_id"] not in alarms:
            raise MetricSurfaceError("SCENARIO_FILE_PREDICTION_MISSING")
        values = tuple(alarms[row["file_id"]])
        if tuple(sorted(set(values))) != values:
            raise MetricSurfaceError("ALARMS_MUST_BE_SORTED_UNIQUE")
        inside = [v for v in values if row["start"] <= v <= row["end"]]
        out.append({"scenario_id": row["scenario_id"], "file_id": row["file_id"],
                    "scenario_authority_hash": row["scenario_authority_hash"],
                    "eligibility_authority_hash": row["eligibility_authority_hash"],
                    "hit": bool(inside), "delay": None if not inside else min(inside) - row["start"]})
    return out


def _wilson(hits: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    p = hits / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - half), min(1.0, centre + half)]


def _delay_summary(hits: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    detected = sorted(int(row["delay"]) for row in hits if row["delay"] is not None)
    individual = [{"scenario_id": row["scenario_id"], "status": "NOT_DETECTED", "value": None}
                  if row["delay"] is None else {"scenario_id": row["scenario_id"], "status": "PASS", "value": row["delay"]}
                  for row in hits]
    if not detected:
        return {"detected": 0, "not_detected": len(hits), "median": None, "iqr": None, "individual": individual}
    def q(fraction: float) -> float:
        pos = (len(detected) - 1) * fraction
        lo, hi = int(pos), min(int(pos) + 1, len(detected) - 1)
        return detected[lo] * (1 - (pos - lo)) + detected[hi] * (pos - lo)
    return {"detected": len(detected), "not_detected": len(hits) - len(detected),
            "median": median(detected), "iqr": q(.75) - q(.25), "individual": individual}


def _normal_burden(value: Mapping[str, Any]) -> tuple[str, dict[str, Any] | None]:
    components = value.get("components")
    if type(components) is not list or not components:
        return "INVALID_AUTHORITY", None
    seconds = episodes = exposure = 0
    abstain = opportunities = evaluation = 0
    for row in components:
        if any(type(row.get(k)) is not int or row[k] < 0 for k in
               ("false_seconds", "false_episodes", "exposure_seconds", "abstain", "opportunities", "evaluated")):
            return "INVALID_AUTHORITY", None
        if row["exposure_seconds"] == 0 or row["evaluated"] > row["opportunities"]:
            return "INVALID_AUTHORITY", None
        seconds += row["false_seconds"]; episodes += row["false_episodes"]; exposure += row["exposure_seconds"]
        abstain += row["abstain"]; opportunities += row["opportunities"]; evaluation += row["evaluated"]
    hours = exposure / 3600
    payload = {"authority_class": value["authority_class"], "components": components,
               "false_seconds": seconds, "false_episodes": episodes, "exposure_seconds": exposure,
               "false_seconds_per_hour": seconds / hours, "false_episodes_per_hour": episodes / hours,
               "abstain_rate": None if opportunities == 0 else abstain / opportunities,
               "opportunity_coverage": value.get("opportunity_coverage"),
               "evaluation_coverage": None if opportunities == 0 else evaluation / opportunities}
    return ("ZERO" if seconds == 0 and episodes == 0 else "PASS"), payload


def _ranges(values: Sequence[int]) -> tuple[tuple[int, int], ...]:
    if not values:
        return ()
    ordered = tuple(sorted(set(values)))
    output: list[tuple[int, int]] = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value != previous + 1:
            output.append((start, previous)); start = value
        previous = value
    output.append((start, previous))
    return tuple(output)


def _etapr(wrapper: OfficialEtaprV1, scenarios: Sequence[Mapping[str, Any]], method: Mapping[str, Any]) -> dict[str, Any]:
    references: dict[str, list[tuple[int, int]]] = {file_id: [] for file_id in method["row_counts"]}
    for row in scenarios:
        if row["eligibility"] == "P1_ELIGIBLE":
            references[row["file_id"]].append((row["start"], row["end"]))
    files = [EtaprFileExchangeV1(file_id, int(method["row_counts"][file_id]), tuple(sorted(references[file_id])),
                                 _ranges(method["alarms_by_file"][file_id]))
             for file_id in sorted(method["row_counts"])]
    return score_namespaced_union_v2(wrapper, files)


def _runtime_census(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = {key: 0 for key in ("opportunities", "pass", "fail", "abstain", "system_errors")}
    rules: set[str] = set(); sources: set[str] = set(); episodes = 0
    for trace in traces:
        if any(type(trace.get(k)) is not int or trace[k] < 0 for k in total):
            raise MetricSurfaceError("INVALID_RUNTIME_TRACE_COUNT")
        if trace["opportunities"] != trace["pass"] + trace["fail"] + trace["abstain"] + trace["system_errors"]:
            raise MetricSurfaceError("RUNTIME_OUTCOME_CENSUS_MISMATCH")
        for key in total:
            total[key] += trace[key]
        rules.update(trace.get("rule_ids", ())); sources.update(trace.get("physical_source_ids", ()))
        episodes += int(trace.get("rule_alarm_episodes", 0))
    return {**total, "participating_rules": sorted(rules), "participating_source_identities": sorted(sources),
            "rule_alarm_episodes": episodes}


def _mcnemar(a_only: int, b_only: int) -> tuple[str, dict[str, Any] | None]:
    n = a_only + b_only
    if n == 0:
        return "NOT_APPLICABLE", None
    tail = sum(comb(n, k) for k in range(min(a_only, b_only) + 1)) / (2 ** n)
    return "PASS", {"p_value": min(1.0, 2 * tail), "discordant": n,
                     "implementation": "EXACT_TWO_SIDED_BINOMIAL"}


def build_complete_metric_surface_v1(*, primitives: Mapping[str, Any], contract: Mapping[str, Any],
                                     executable_manifest_hash: str, wrapper: OfficialEtaprV1,
                                     source_commit: str) -> dict[str, Any]:
    validate_self_hashed(primitives, "metric_surface_primitives_v1")
    validate_self_hashed(contract, "metric_surface_contract_v1")
    panel = primitives["panel_id"]
    if primitives["authority_hashes"]["executable"] != executable_manifest_hash:
        raise MetricSurfaceError("EXECUTABLE_AUTHORITY_MISMATCH")
    bindings = {**primitives["authority_hashes"], **SCIENTIFIC_HASHES, "contract": contract["self_hash"]}
    surfaces: list[dict[str, Any]] = []
    method_hits: dict[str, list[dict[str, Any]]] = {}
    method_burden: dict[str, dict[str, Any] | None] = {}
    for method_id in FROZEN_METHOD_IDS_BY_PANEL_V1[panel]:
        method = primitives["methods"][method_id]
        prefix = f"{panel}|METHOD|{method_id}|"
        if method.get("status") == "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE":
            for kind in METHOD_SURFACES + ((RUNTIME_SURFACE,) if _is_rule_method(method_id) else ()):
                surfaces.append(_surface(prefix + kind, "NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE", None, bindings))
            method_hits[method_id] = []; method_burden[method_id] = None
            continue
        hits = _scenario_hits(primitives["scenarios"], method["alarms_by_file"])
        method_hits[method_id] = hits
        n, k = len(hits), sum(row["hit"] for row in hits)
        surfaces.append(_surface(prefix + "SCENARIO_HIT_MISS", "NOT_EVALUABLE" if n == 0 else "PASS",
                                 None if n == 0 else hits, bindings))
        recall_status = "NOT_EVALUABLE" if n == 0 else ("ZERO" if k == 0 else "PASS")
        recall_payload = None if n == 0 else {"hits": k, "eligible": n, "recall": k / n,
                                               "denominator_authority_hash": primitives["authority_hashes"]["denominator"]}
        surfaces.append(_surface(prefix + "SCENARIO_RECALL", recall_status, recall_payload, bindings))
        surfaces.append(_surface(prefix + "WILSON95", "NOT_EVALUABLE" if n == 0 else "PASS",
                                 None if n == 0 else {"hits": k, "eligible": n, "interval": _wilson(k, n)}, bindings))
        delay = _delay_summary(hits)
        surfaces.append(_surface(prefix + "DETECTION_DELAY", "NOT_EVALUABLE" if n == 0 else "PASS",
                                 None if n == 0 else delay["individual"], bindings))
        surfaces.append(_surface(prefix + "DELAY_SUMMARY", "NOT_EVALUABLE" if n == 0 else "PASS",
                                 None if n == 0 else {k: v for k, v in delay.items() if k != "individual"}, bindings))
        burden_status, burden = _normal_burden(method["normal_burden"])
        method_burden[method_id] = burden
        surfaces.append(_surface(prefix + "NORMAL_BURDEN", burden_status, burden, bindings))
        eta = _etapr(wrapper, primitives["scenarios"], method)
        per_status = "NOT_APPLICABLE" if all(v["status"] == "NOT_APPLICABLE" for v in eta["per_file"]) else "PASS"
        surfaces.append(_surface(prefix + "ETAPR_PER_FILE", per_status,
                                 None if per_status == "NOT_APPLICABLE" else eta["per_file"], bindings))
        union_status = "NOT_APPLICABLE" if eta["status"] == "NOT_APPLICABLE" else ("ZERO" if eta["F1"] == 0 else "PASS")
        surfaces.append(_surface(prefix + "ETAPR_VERSION_UNION", union_status,
                                 None if union_status == "NOT_APPLICABLE" else eta, bindings))
        if _is_rule_method(method_id):
            census = _runtime_census(method["runtime_traces"])
            surfaces.append(_surface(prefix + RUNTIME_SURFACE, "ZERO" if census["opportunities"] == 0 else "PASS", census, bindings))

    for contrast_id, (method_a, method_b) in FROZEN_CONTRASTS.items():
        prefix = f"{panel}|CONTRAST|{contrast_id}|"
        if not method_hits[method_a] or not method_hits[method_b]:
            for kind in CONTRAST_SURFACES:
                surfaces.append(_surface(prefix + kind, "NOT_EVALUABLE", None, bindings))
            continue
        left = {row["scenario_id"]: row for row in method_hits[method_a]}
        right = {row["scenario_id"]: row for row in method_hits[method_b]}
        if set(left) != set(right) or any((left[k]["file_id"], left[k]["scenario_authority_hash"], left[k]["eligibility_authority_hash"]) !=
                                          (right[k]["file_id"], right[k]["scenario_authority_hash"], right[k]["eligibility_authority_hash"]) for k in left):
            raise MetricSurfaceError("PAIRED_AUTHORITY_OR_IDENTITY_MISMATCH")
        table = {"both_hit": sum(left[k]["hit"] and right[k]["hit"] for k in left),
                 "a_only": sum(left[k]["hit"] and not right[k]["hit"] for k in left),
                 "b_only": sum(not left[k]["hit"] and right[k]["hit"] for k in left),
                 "neither": sum(not left[k]["hit"] and not right[k]["hit"] for k in left),
                 "eligible": len(left), "hit_count_difference": sum(v["hit"] for v in left.values()) - sum(v["hit"] for v in right.values()),
                 "method_a": method_a, "method_b": method_b}
        surfaces.append(_surface(prefix + "PAIRED_TABLE", "PASS", table, bindings))
        status, value = _mcnemar(table["a_only"], table["b_only"])
        surfaces.append(_surface(prefix + "MCNEMAR_EXACT", status, value, bindings))

    required = ("M0_PCA_SPE", "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2")
    recovery_id = f"{panel}|PANEL|RECOVERY|{RECOVERY_SURFACE}"
    if any(not method_hits[name] for name in required):
        surfaces.append(_surface(recovery_id, "NOT_EVALUABLE", None, bindings))
    elif any(method_burden[name] is None for name in ("M0_PCA_SPE", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2")):
        surfaces.append(_surface(recovery_id, "INVALID_AUTHORITY", None, bindings))
    else:
        maps = {name: {v["scenario_id"]: v["hit"] for v in method_hits[name]} for name in required}
        misses = sorted(k for k, hit in maps["M0_PCA_SPE"].items() if not hit)
        payload = {"pca_miss_scenario_ids": misses,
                   "t0_rule_response_ids": [k for k in misses if maps["M1_T0_RULE_ONLY"][k]],
                   "t2_rule_response_ids": [k for k in misses if maps["M2_T2_RULE_ONLY"][k]],
                   "pca_t0_actual_recovery_ids": [k for k in misses if maps["M3_PCA_PLUS_T0"][k]],
                   "pca_t2_actual_recovery_ids": [k for k in misses if maps["M4_PCA_PLUS_T2"][k]],
                   "incremental_recall_t0": (sum(maps["M3_PCA_PLUS_T0"].values()) - sum(maps["M0_PCA_SPE"].values())) / len(maps["M0_PCA_SPE"]),
                   "incremental_recall_t2": (sum(maps["M4_PCA_PLUS_T2"].values()) - sum(maps["M0_PCA_SPE"].values())) / len(maps["M0_PCA_SPE"]),
                   "incremental_false_seconds_per_hour_t0": method_burden["M3_PCA_PLUS_T0"]["false_seconds_per_hour"] - method_burden["M0_PCA_SPE"]["false_seconds_per_hour"],
                   "incremental_false_seconds_per_hour_t2": method_burden["M4_PCA_PLUS_T2"]["false_seconds_per_hour"] - method_burden["M0_PCA_SPE"]["false_seconds_per_hour"]}
        surfaces.append(_surface(recovery_id, "ZERO" if not misses else "PASS", payload, bindings))

    actual = {row["surface_id"] for row in surfaces}
    expected = {row["surface_id"] for row in contract["surfaces"] if row["panel_id"] == panel}
    if actual != expected or len(actual) != len(surfaces):
        raise MetricSurfaceError("BLOCKED_METRIC_SURFACE_INCOMPLETE")
    return self_hashed({"schema": "complete_panel_metric_surface_v1", "executable_version": "DG05_EXECUTABLE_V3",
                        "panel_id": panel, "primitive_authority_hash": primitives["self_hash"],
                        "contract_hash": contract["self_hash"], "executable_manifest_hash": executable_manifest_hash,
                        "scientific_authorities": SCIENTIFIC_HASHES, "surfaces": sorted(surfaces, key=lambda v: v["surface_id"]),
                        "surface_count": len(surfaces), "source_commit": source_commit, "cross_version_pooled_result": False})


def result_surface_completeness_oracle_v1(*, contract: Mapping[str, Any], result_documents: Sequence[Mapping[str, Any]],
                                          verifier_supported_surface_ids: Sequence[str]) -> dict[str, Any]:
    validate_self_hashed(contract, "metric_surface_contract_v1")
    for result in result_documents:
        validate_self_hashed(result, "complete_panel_metric_surface_v1")
    expected = {row["surface_id"] for row in contract["surfaces"]}
    built_rows = [row for result in result_documents for row in result["surfaces"]]
    built = {row["surface_id"] for row in built_rows}
    verified = set(verifier_supported_surface_ids)
    if len(built_rows) != len(built) or expected != built or expected != verified:
        raise MetricSurfaceError("BLOCKED_METRIC_SURFACE_INCOMPLETE")
    for row in built_rows:
        if row["status"] in NONVALUE_STATUSES and row["payload"] is not None:
            raise MetricSurfaceError("STATUS_PAYLOAD_CONFLICT")
        if set(row) != {"surface_id", "status", "payload", "authority_bindings"} or not row["authority_bindings"]:
            raise MetricSurfaceError("UNTYPED_OR_UNBOUND_SURFACE")
    return self_hashed({"schema": "result_surface_completeness_oracle_v1", "contract_hash": contract["self_hash"],
                        "expected_count": len(expected), "builder_count": len(built), "verifier_count": len(verified),
                        "exact_set_equality": True, "status": "PASS"})


def persist_canonical_v1(path: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    validate_self_hashed(value)
    payload = canonical_bytes(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise MetricSurfaceError("APPEND_ONLY_CONFLICT")
    path.write_bytes(payload)
    replay = json.loads(path.read_text(encoding="ascii"))
    validate_self_hashed(replay)
    if path.read_bytes() != payload:
        raise MetricSurfaceError("CANONICAL_BYTE_REPLAY_MISMATCH")
    return self_hashed({"schema": "metric_surface_artifact_receipt_v1", "artifact_byte_hash": sha256(payload).hexdigest(),
                        "document_self_hash": value["self_hash"], "byte_count": len(payload)})


__all__ = ["MetricSurfaceError", "FROZEN_PANEL_ORDER", "FROZEN_CONTRASTS", "METHOD_SURFACES",
           "CONTRAST_SURFACES", "RUNTIME_SURFACE", "RECOVERY_SURFACE", "SCIENTIFIC_HASHES",
           "canonical_bytes", "digest", "self_hashed", "validate_self_hashed", "expected_surface_rows_v1",
           "build_metric_surface_contract_v1", "build_expected_result_surface_v1", "build_metric_primitives_v1",
           "build_complete_metric_surface_v1", "result_surface_completeness_oracle_v1", "persist_canonical_v1"]
