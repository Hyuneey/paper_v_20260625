"""DEC-031 compatible DG-05 metric surface.

This prospective module preserves the preregistered surface identifiers while
replacing the historical row-coordinate/single-interval bridge.  Inputs are
already-frozen, method-blind scenario and denominator authorities plus
prediction/runtime and independently replayed normal-source evidence.
"""
from __future__ import annotations

from decimal import Decimal
from math import comb, sqrt
from statistics import median
from typing import Any, Mapping, Sequence

from .dg05_dec031_v1 import interval_local_detection_v1
from .dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1
from .dg05_metric_surface_v1 import (
    CONTRAST_SURFACES,
    FROZEN_CONTRASTS,
    FROZEN_PANEL_ORDER,
    METHOD_SURFACES,
    NONVALUE_STATUSES,
    RECOVERY_SURFACE,
    RUNTIME_SURFACE,
    SCIENTIFIC_HASHES,
    _is_rule_method,
    _ranges,
    canonical_bytes,
    digest,
    expected_surface_rows_v1,
    persist_canonical_v1,
    self_hashed,
    validate_self_hashed,
)
from .etapr_exchange_v1 import EtaprFileExchangeV1, OfficialEtaprV1
from .multipanel_etapr_v2 import score_namespaced_union_v2


class MetricSurfaceV2Error(ValueError):
    """Fail-closed DEC-031 metric-surface violation."""


def build_metric_surface_contract_v2(*, source_commit: str, dec031_binding_hash: str,
                                     normal_source_registry_hash: str) -> dict[str, Any]:
    for value in (dec031_binding_hash, normal_source_registry_hash):
        if type(value) is not str or len(value) != 64:
            raise MetricSurfaceV2Error("EXACT_DEC031_AND_NORMAL_SOURCE_AUTHORITIES_REQUIRED")
    rows = expected_surface_rows_v1()
    return self_hashed({
        "schema": "metric_surface_contract_v2",
        "executable_version": "DG05_EXECUTABLE_V4",
        "scientific_authorities": SCIENTIFIC_HASHES,
        "dec031_binding_hash": dec031_binding_hash,
        "normal_source_registry_hash": normal_source_registry_hash,
        "scenario_interval_semantics": "ONE_SCENARIO_ANY_OF_1_TO_N_CLOSED_PHYSICAL_INTERVALS",
        "detection_delay_semantics": "HIT_INTERVAL_LOCAL_DELAY",
        "time_coordinate": "PHYSICAL_TIMESTAMP",
        "duplicate_timestamp_policy": "FAIL_FILE_ON_DUPLICATE_TIMESTAMP",
        "non_unit_gap_policy": "FAIL_FILE_ON_NON_UNIT_GAP",
        "runtime_identity_census": "FOUR_WAY_RUNTIME_IDENTITY_CENSUS",
        "source_commit": source_commit,
        "status_types": ["PASS", "ZERO", *sorted(NONVALUE_STATUSES)],
        "surfaces": rows,
        "required_surface_count": len(rows),
        "cross_version_primary_pooling": False,
    })


def build_metric_primitives_v2(*, panel_id: str, dataset_version: str,
                               scenarios: Sequence[Mapping[str, Any]],
                               methods: Mapping[str, Mapping[str, Any]],
                               authority_hashes: Mapping[str, str]) -> dict[str, Any]:
    if panel_id not in FROZEN_PANEL_ORDER or set(methods) != set(FROZEN_METHOD_IDS_BY_PANEL_V1[panel_id]):
        raise MetricSurfaceV2Error("FROZEN_PANEL_METHOD_CENSUS_MISMATCH")
    required = {"executable", "prediction_manifest", "scenario", "denominator", "normal_burden", "dec031"}
    if set(authority_hashes) != required or any(type(value) is not str or len(value) != 64 for value in authority_hashes.values()):
        raise MetricSurfaceV2Error("PRIMITIVE_AUTHORITY_CENSUS_MISMATCH")
    ids = [str(row.get("scenario_id", "")) for row in scenarios]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise MetricSurfaceV2Error("DUPLICATE_OR_EMPTY_SCENARIO_ID")
    for row in scenarios:
        intervals = row.get("closed_intervals")
        if type(intervals) is not list or not intervals or any(type(value) is not list or len(value) != 2 for value in intervals):
            raise MetricSurfaceV2Error("PLURAL_CLOSED_INTERVAL_AUTHORITY_REQUIRED")
    return self_hashed({
        "schema": "metric_surface_primitives_v2",
        "panel_id": panel_id,
        "dataset_version": dataset_version,
        "scenarios": [dict(row) for row in scenarios],
        "methods": {key: dict(value) for key, value in sorted(methods.items())},
        "authority_hashes": dict(authority_hashes),
        "label_or_attack_resource_paths": False,
        "caller_supplied_normal_burden": False,
    })


def _surface(surface_id: str, status: str, payload: Any, bindings: Mapping[str, str]) -> dict[str, Any]:
    if status in NONVALUE_STATUSES and payload is not None:
        raise MetricSurfaceV2Error("NONVALUE_STATUS_WITH_PAYLOAD")
    if status not in {"PASS", "ZERO", *NONVALUE_STATUSES}:
        raise MetricSurfaceV2Error("UNKNOWN_TYPED_STATUS")
    return {"surface_id": surface_id, "status": status, "payload": payload,
            "authority_bindings": dict(bindings)}


def _scenario_hits(scenarios: Sequence[Mapping[str, Any]], method: Mapping[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    alarms = method["alarm_timestamps_by_file"]
    for row in sorted((value for value in scenarios if value["eligibility"] == "P1_ELIGIBLE"),
                      key=lambda value: value["scenario_id"]):
        if row["file_id"] not in alarms:
            raise MetricSurfaceV2Error("SCENARIO_FILE_PREDICTION_MISSING")
        result = interval_local_detection_v1(
            alarm_timestamps=alarms[row["file_id"]], closed_intervals=row["closed_intervals"])
        out.append({
            "scenario_id": row["scenario_id"], "file_id": row["file_id"],
            "scenario_authority_hash": row["scenario_authority_hash"],
            "eligibility_authority_hash": row["eligibility_authority_hash"],
            "hit": result["scenario_outcome"] == "HIT",
            "earliest_hit_timestamp": result["earliest_hit_timestamp"],
            "containing_interval_index": result["containing_interval_index"],
            "containing_interval_start": result["containing_interval_start"],
            "interval_local_delay_seconds": result["interval_local_delay_seconds"],
            "detection_delay_status": result["detection_delay_status"],
            "delay_terminology": result["delay_terminology"],
        })
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


def _delay(hits: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    values = [Decimal(row["interval_local_delay_seconds"]) for row in hits if row["hit"]]
    ordered = sorted(values)
    individual = [{
        "scenario_id": row["scenario_id"],
        "status": "PASS" if row["hit"] else "NOT_DETECTED",
        "earliest_hit_timestamp": row["earliest_hit_timestamp"],
        "containing_interval_index": row["containing_interval_index"],
        "containing_interval_start": row["containing_interval_start"],
        "interval_local_delay_seconds": row["interval_local_delay_seconds"],
        "terminology": "INTERVAL_LOCAL_DETECTION_DELAY",
    } for row in hits]
    if not ordered:
        return individual, {"detected": 0, "not_detected": len(hits), "median_seconds": None, "iqr_seconds": None,
                            "terminology": "INTERVAL_LOCAL_DETECTION_DELAY"}
    def quantile(fraction: Decimal) -> Decimal:
        position = Decimal(len(ordered) - 1) * fraction
        low = int(position); high = min(low + 1, len(ordered) - 1)
        weight = position - low
        return ordered[low] * (1 - weight) + ordered[high] * weight
    return individual, {
        "detected": len(ordered), "not_detected": len(hits) - len(ordered),
        "median_seconds": format(median(ordered), ".6f"),
        "iqr_seconds": format(quantile(Decimal("0.75")) - quantile(Decimal("0.25")), ".6f"),
        "terminology": "INTERVAL_LOCAL_DETECTION_DELAY",
    }


def _normal_burden(method: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    required = {"authority_class", "components", "false_seconds", "false_episodes", "exposure_seconds",
                "false_seconds_per_hour", "false_episodes_per_hour"}
    if not required.issubset(method) or type(method["components"]) is not list or not method["components"]:
        raise MetricSurfaceV2Error("REPLAYED_NORMAL_SOURCE_METHOD_REQUIRED")
    exposure = sum(int(row["exposure_seconds"]) for row in method["components"])
    seconds = sum(int(row["false_seconds"]) for row in method["components"])
    episodes = sum(int(row["false_episodes"]) for row in method["components"])
    if (exposure, seconds, episodes) != (method["exposure_seconds"], method["false_seconds"], method["false_episodes"]):
        raise MetricSurfaceV2Error("NORMAL_SOURCE_REPLAY_ARITHMETIC_MISMATCH")
    expected_seconds = seconds * 3600 / exposure
    expected_episodes = episodes * 3600 / exposure
    if method["false_seconds_per_hour"] != expected_seconds or method["false_episodes_per_hour"] != expected_episodes:
        raise MetricSurfaceV2Error("NORMAL_SOURCE_RATE_REPLAY_MISMATCH")
    payload = dict(method)
    payload["source_bytes_reopened"] = True
    return ("ZERO" if seconds == 0 and episodes == 0 else "PASS"), payload


def _interval_row_ranges(scenarios: Sequence[Mapping[str, Any]], method: Mapping[str, Any]) -> dict[str, list[tuple[int, int]]]:
    from datetime import datetime
    output: dict[str, list[tuple[int, int]]] = {file_id: [] for file_id in method["timestamps_by_file"]}
    for scenario in scenarios:
        if scenario["eligibility"] != "P1_ELIGIBLE":
            continue
        file_id = scenario["file_id"]
        timestamps = [datetime.fromisoformat(value) for value in method["timestamps_by_file"][file_id]]
        for start_text, end_text in scenario["closed_intervals"]:
            start, end = datetime.fromisoformat(start_text), datetime.fromisoformat(end_text)
            indices = [index for index, value in enumerate(timestamps) if start <= value <= end]
            if indices:
                output[file_id].append((indices[0], indices[-1]))
    return output


def _etapr(wrapper: OfficialEtaprV1, scenarios: Sequence[Mapping[str, Any]], method: Mapping[str, Any]) -> dict[str, Any]:
    references = _interval_row_ranges(scenarios, method)
    files = [EtaprFileExchangeV1(file_id, len(method["timestamps_by_file"][file_id]),
                                 tuple(sorted(references[file_id])),
                                 _ranges(method["alarm_rows_by_file"][file_id]))
             for file_id in sorted(method["timestamps_by_file"])]
    return score_namespaced_union_v2(wrapper, files)


def _mcnemar(a_only: int, b_only: int) -> tuple[str, dict[str, Any] | None]:
    discordant = a_only + b_only
    if discordant == 0:
        return "NOT_APPLICABLE", None
    tail = sum(comb(discordant, index) for index in range(min(a_only, b_only) + 1)) / (2 ** discordant)
    return "PASS", {"p_value": min(1.0, 2 * tail), "discordant": discordant,
                    "implementation": "EXACT_TWO_SIDED_BINOMIAL"}


def build_complete_metric_surface_v2(*, primitives: Mapping[str, Any], contract: Mapping[str, Any],
                                     executable_manifest_hash: str, wrapper: OfficialEtaprV1,
                                     source_commit: str) -> dict[str, Any]:
    validate_self_hashed(primitives, "metric_surface_primitives_v2")
    validate_self_hashed(contract, "metric_surface_contract_v2")
    panel = primitives["panel_id"]
    if primitives["authority_hashes"]["executable"] != executable_manifest_hash:
        raise MetricSurfaceV2Error("EXECUTABLE_AUTHORITY_MISMATCH")
    if (
        primitives["authority_hashes"]["normal_burden"] != contract.get("normal_source_registry_hash")
        or primitives["authority_hashes"]["dec031"] != contract.get("dec031_binding_hash")
    ):
        raise MetricSurfaceV2Error("CONTRACT_UPSTREAM_SOURCE_BINDING_MISMATCH")
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
        hits = _scenario_hits(primitives["scenarios"], method)
        method_hits[method_id] = hits
        total, hit_count = len(hits), sum(row["hit"] for row in hits)
        surfaces.append(_surface(prefix + "SCENARIO_HIT_MISS", "NOT_EVALUABLE" if total == 0 else "PASS", None if total == 0 else hits, bindings))
        status = "NOT_EVALUABLE" if total == 0 else ("ZERO" if hit_count == 0 else "PASS")
        surfaces.append(_surface(prefix + "SCENARIO_RECALL", status, None if total == 0 else {"hits": hit_count, "eligible": total, "recall": hit_count / total, "denominator_authority_hash": primitives["authority_hashes"]["denominator"]}, bindings))
        surfaces.append(_surface(prefix + "WILSON95", "NOT_EVALUABLE" if total == 0 else "PASS", None if total == 0 else {"hits": hit_count, "eligible": total, "interval": _wilson(hit_count, total)}, bindings))
        individual, summary = _delay(hits)
        surfaces.append(_surface(prefix + "DETECTION_DELAY", "NOT_EVALUABLE" if total == 0 else "PASS", None if total == 0 else individual, bindings))
        surfaces.append(_surface(prefix + "DELAY_SUMMARY", "NOT_EVALUABLE" if total == 0 else "PASS", None if total == 0 else summary, bindings))
        burden_status, burden = _normal_burden(method["normal_burden"])
        method_burden[method_id] = burden
        surfaces.append(_surface(prefix + "NORMAL_BURDEN", burden_status, burden, bindings))
        eta = _etapr(wrapper, primitives["scenarios"], method)
        per_status = "NOT_APPLICABLE" if all(value["status"] == "NOT_APPLICABLE" for value in eta["per_file"]) else "PASS"
        surfaces.append(_surface(prefix + "ETAPR_PER_FILE", per_status, None if per_status == "NOT_APPLICABLE" else eta["per_file"], bindings))
        union_status = "NOT_APPLICABLE" if eta["status"] == "NOT_APPLICABLE" else ("ZERO" if eta["F1"] == 0 else "PASS")
        surfaces.append(_surface(prefix + "ETAPR_VERSION_UNION", union_status, None if union_status == "NOT_APPLICABLE" else eta, bindings))
        if _is_rule_method(method_id):
            census = method.get("runtime_census")
            if type(census) is not dict or census.get("unqualified_participating_rules_field") != "PROHIBITED":
                raise MetricSurfaceV2Error("FOUR_WAY_RUNTIME_CENSUS_REQUIRED")
            surfaces.append(_surface(prefix + RUNTIME_SURFACE, "ZERO" if census["opportunities"] == 0 else "PASS", census, bindings))
    for contrast_id, (method_a, method_b) in FROZEN_CONTRASTS.items():
        prefix = f"{panel}|CONTRAST|{contrast_id}|"
        if not method_hits[method_a] or not method_hits[method_b]:
            for kind in CONTRAST_SURFACES:
                surfaces.append(_surface(prefix + kind, "NOT_EVALUABLE", None, bindings))
            continue
        left = {row["scenario_id"]: row for row in method_hits[method_a]}; right = {row["scenario_id"]: row for row in method_hits[method_b]}
        if set(left) != set(right):
            raise MetricSurfaceV2Error("PAIRED_SCENARIO_CENSUS_MISMATCH")
        table = {"both_hit": sum(left[key]["hit"] and right[key]["hit"] for key in left),
                 "a_only": sum(left[key]["hit"] and not right[key]["hit"] for key in left),
                 "b_only": sum(not left[key]["hit"] and right[key]["hit"] for key in left),
                 "neither": sum(not left[key]["hit"] and not right[key]["hit"] for key in left),
                 "eligible": len(left), "hit_count_difference": sum(row["hit"] for row in left.values()) - sum(row["hit"] for row in right.values()),
                 "method_a": method_a, "method_b": method_b}
        surfaces.append(_surface(prefix + "PAIRED_TABLE", "PASS", table, bindings))
        mc_status, mc_value = _mcnemar(table["a_only"], table["b_only"])
        surfaces.append(_surface(prefix + "MCNEMAR_EXACT", mc_status, mc_value, bindings))
    required = ("M0_PCA_SPE", "M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2")
    recovery_id = f"{panel}|PANEL|RECOVERY|{RECOVERY_SURFACE}"
    if any(not method_hits[name] for name in required):
        surfaces.append(_surface(recovery_id, "NOT_EVALUABLE", None, bindings))
    else:
        maps = {name: {row["scenario_id"]: row["hit"] for row in method_hits[name]} for name in required}
        misses = sorted(key for key, hit in maps["M0_PCA_SPE"].items() if not hit)
        payload = {"pca_miss_scenario_ids": misses,
                   "t0_rule_response_ids": [key for key in misses if maps["M1_T0_RULE_ONLY"][key]],
                   "t2_rule_response_ids": [key for key in misses if maps["M2_T2_RULE_ONLY"][key]],
                   "pca_t0_actual_recovery_ids": [key for key in misses if maps["M3_PCA_PLUS_T0"][key]],
                   "pca_t2_actual_recovery_ids": [key for key in misses if maps["M4_PCA_PLUS_T2"][key]],
                   "incremental_recall_t0": (sum(maps["M3_PCA_PLUS_T0"].values()) - sum(maps["M0_PCA_SPE"].values())) / len(maps["M0_PCA_SPE"]),
                   "incremental_recall_t2": (sum(maps["M4_PCA_PLUS_T2"].values()) - sum(maps["M0_PCA_SPE"].values())) / len(maps["M0_PCA_SPE"]),
                   "incremental_false_seconds_per_hour_t0": method_burden["M3_PCA_PLUS_T0"]["false_seconds_per_hour"] - method_burden["M0_PCA_SPE"]["false_seconds_per_hour"],
                   "incremental_false_seconds_per_hour_t2": method_burden["M4_PCA_PLUS_T2"]["false_seconds_per_hour"] - method_burden["M0_PCA_SPE"]["false_seconds_per_hour"]}
        surfaces.append(_surface(recovery_id, "ZERO" if not misses else "PASS", payload, bindings))
    expected = {row["surface_id"] for row in contract["surfaces"] if row["panel_id"] == panel}
    actual = {row["surface_id"] for row in surfaces}
    if actual != expected or len(actual) != len(surfaces):
        raise MetricSurfaceV2Error("BLOCKED_METRIC_SURFACE_INCOMPLETE")
    return self_hashed({"schema": "complete_panel_metric_surface_v2", "executable_version": "DG05_EXECUTABLE_V4",
                        "panel_id": panel, "primitive_authority_hash": primitives["self_hash"],
                        "contract_hash": contract["self_hash"], "executable_manifest_hash": executable_manifest_hash,
                        "scientific_authorities": SCIENTIFIC_HASHES, "surfaces": sorted(surfaces, key=lambda row: row["surface_id"]),
                        "surface_count": len(surfaces), "source_commit": source_commit, "cross_version_pooled_result": False})


__all__ = ["MetricSurfaceV2Error", "build_metric_surface_contract_v2", "build_metric_primitives_v2",
           "build_complete_metric_surface_v2", "persist_canonical_v1", "canonical_bytes"]
