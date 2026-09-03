"""Read-only EXP01C evidence projection; never an executable authority.

The historical pair criterion is replayed unchanged. Horizon annotations are
stricter: the same directional reference must be positive in two combined
seeds. Predictive MSE does not establish the expected target response sign.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Mapping, Sequence

from paperworks.v6.common import stable_hash_v1

VIEWS = ("TRAIN1_TRAIN2_COMBINED", "TRAIN1_ONLY", "TRAIN2_ONLY")
SEEDS = (11, 23, 37)
EPSILON = 1e-12


def seal(body: Mapping[str, Any]) -> dict[str, Any]:
    return {**body, "self_hash": stable_hash_v1(body)}


def replay(document: Mapping[str, Any], field: str = "self_hash") -> None:
    if document.get(field) != stable_hash_v1({k: v for k, v in document.items() if k != field}):
        raise ValueError("EVIDENCE_SELF_HASH_MISMATCH")


def project_gdn_evidence_v1(*, reference: Mapping[str, Any], portfolio: Mapping[str, Any],
                            evidence: Sequence[Mapping[str, Any]], expected_stable_count: int,
                            bindings: Mapping[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project hash-verified private evidence into public identities and counts."""
    relations = reference["confirmed_directional_relations"]
    by_id = {row["relation_id"]: row for row in relations}
    if len(by_id) != len(relations):
        raise ValueError("REFERENCE_DUPLICATE")
    runs: dict[tuple[str, int], dict[str, float]] = {}
    for item in evidence:
        replay(item, "evidence_hash")
        key = (item["view"], item["seed"])
        if key in runs or not item["checkpoint_unchanged"] or not item["attention_invariance_passed"]:
            raise ValueError("EVIDENCE_RUN_INVALID")
        values = {r["relation_id"]: float(r["value"]) for r in item["event_edge_mask"]}
        if len(values) != len(item["event_edge_mask"]) or set(values) - set(by_id) or any(not math.isfinite(v) for v in values.values()):
            raise ValueError("EVENT_EVIDENCE_INVALID")
        runs[key] = values
    if set(runs) != {(v, s) for v in VIEWS for s in SEEDS}:
        raise ValueError("EXACT_NINE_EVIDENCE_RUNS_REQUIRED")
    pair_ids: dict[tuple[str, str], list[str]] = {}
    for rid, relation in by_id.items():
        pair_ids.setdefault((relation["source"], relation["target"]), []).append(rid)
    stable = []
    descriptors = portfolio["descriptors"]
    for pair, ids in sorted(pair_ids.items()):
        view_counts = {}
        for view in VIEWS:
            count = 0
            for seed in SEEDS:
                values = [runs[(view, seed)][rid] for rid in ids if rid in runs[(view, seed)]]
                count += bool(values and statistics.median(values) > EPSILON)
            view_counts[view] = count
        if view_counts[VIEWS[0]] < 2:
            continue
        directional = []
        horizons = set()
        for rid in sorted(ids):
            relation = by_id[rid]
            counts = {}
            for view in VIEWS:
                values = [runs[(view, s)].get(rid) for s in SEEDS]
                counts[view] = {"positive": sum(v is not None and v > EPSILON for v in values),
                                "negative": sum(v is not None and v < -EPSILON for v in values),
                                "neutral": sum(v is not None and abs(v) <= EPSILON for v in values),
                                "not_evaluable": sum(v is None for v in values)}
            if counts[VIEWS[0]]["positive"] >= 2:
                horizons.add(relation["selected_horizon_seconds"])
            directional.append({**relation, "seed_sign_counts": counts})
        matches = [d for d in descriptors if (d["source"], d["target"]) == pair]
        exact = [d for d in matches if d["selected_horizon_seconds"] in horizons]
        category = ("PAIR_AND_HORIZON_CORROBORATION" if exact else
                    "PAIR_ONLY_CORROBORATION" if matches else "NO_FINAL_PORTFOLIO_OVERLAP")
        stable.append({"source": pair[0], "target": pair[1], "supported_horizons": sorted(horizons),
                       "stable_seed_count": view_counts[VIEWS[0]], "view_positive_seed_counts": view_counts,
                       "event_conditioned_sign": "STABLE_POSITIVE_POOLED_DIRECTIONAL_MEDIAN",
                       "directional_evidence": directional, "classification": category,
                       "v2a_rule_ids": [d["relation_id"] for d in matches],
                       "v2a_rules": [{k: d[k] for k in ("relation_id", "descriptor_hash", "source_direction", "target_direction", "selected_horizon_seconds")} for d in matches],
                       "exact_horizon_rule_ids": [d["relation_id"] for d in exact]})
    if len(stable) != expected_stable_count:
        raise ValueError("FROZEN_STABLE_PAIR_COUNT_MISMATCH")
    by_pair = {(r["source"], r["target"]): r for r in stable}
    rows = []
    for descriptor in descriptors:
        pair = (descriptor["source"], descriptor["target"])
        item = by_pair.get(pair)
        evaluable = any(rid in run for rid in pair_ids.get(pair, ()) for run in runs.values())
        status = ("CORROBORATED_PAIR_AND_HORIZON" if item and descriptor["selected_horizon_seconds"] in item["supported_horizons"] else
                  "CORROBORATED_PAIR_ONLY" if item else "NOT_CORROBORATED" if evaluable else "NOT_EVALUABLE")
        rows.append({"rule_id": descriptor["relation_id"], "descriptor_hash": descriptor["descriptor_hash"],
                     "source": descriptor["source"], "target": descriptor["target"],
                     "rule_horizon": descriptor["selected_horizon_seconds"], "learned_graph_status": status,
                     "gdn_experiment_id": "EXP-01C-GDN-HAI-V1", "gdn_evidence_type": "EVENT_CONDITIONED_EDGEMASK",
                     "gdn_supported_horizons": item["supported_horizons"] if item else [],
                     "stable_seed_count": item["stable_seed_count"] if item else 0,
                     "evidence_authority_hash": bindings["functional_receipt_hash"]})
    mapping = seal({"schema": "gdn_to_v2a_rule_evidence_map_v1", "bindings": dict(bindings),
                    "stable_pair_count": len(stable), "pairs": stable,
                    "pair_rule": "UNCHANGED_EXP01C_POOLED_MEDIAN_POSITIVE_IN_TWO_COMBINED_SEEDS",
                    "horizon_projection": "SAME_DIRECTIONAL_REFERENCE_POSITIVE_IN_TWO_COMBINED_SEEDS",
                    "target_response_sign_corroborated": False, "documentation_only": True})
    sidecar = seal({"schema": "gdn_learned_graph_evidence_sidecar_v1", "bindings": dict(bindings),
                   "mapping_hash": mapping["self_hash"], "rule_identity_convention": "rule_id=relation_id",
                   "affects_runtime": False, "affects_predictions": False,
                   "permitted_consumers": ["documentation", "dashboard", "professor_report", "explanation_annotation"],
                   "rows": rows})
    return mapping, sidecar


def annotate_explanation_v1(base: Mapping[str, Any], *, row: Mapping[str, Any],
                            descriptor: Mapping[str, Any], sidecar: Mapping[str, Any],
                            expected_sidecar_hash: str) -> dict[str, Any]:
    """Return a separate envelope; the base runtime outcome is never edited."""
    replay(sidecar)
    if sidecar["self_hash"] != expected_sidecar_hash or sidecar.get("affects_runtime") is not False or sidecar.get("affects_predictions") is not False:
        raise ValueError("ANNOTATION_SIDECAR_AUTHORITY_MISMATCH")
    if sum(item == row for item in sidecar["rows"]) != 1:
        raise ValueError("ANNOTATION_NOT_IN_FROZEN_SIDECAR")
    replay(base, "artifact_hash")
    if (base.get("portfolio_authority_hash") != sidecar["bindings"].get("portfolio_hash")
        or any(base.get(k) != descriptor[k] for k in ("descriptor_hash", "source", "target", "source_direction", "target_direction", "selected_horizon_seconds"))):
        raise ValueError("ANNOTATION_BASE_EXPLANATION_MISMATCH")
    expected = {"rule_id": descriptor["relation_id"], "descriptor_hash": descriptor["descriptor_hash"],
                "source": descriptor["source"], "target": descriptor["target"],
                "rule_horizon": descriptor["selected_horizon_seconds"]}
    if any(row.get(k) != v for k, v in expected.items()):
        raise ValueError("ANNOTATION_DESCRIPTOR_MISMATCH")
    clauses = {
        "CORROBORATED_PAIR_AND_HORIZON": "같은 source–target 의존성과 응답 지평은 HAI-adapted GDN 기능 분석에서도 보조 근거를 얻었습니다.",
        "CORROBORATED_PAIR_ONLY": "source–target 의존성은 HAI-adapted GDN 기능 분석에서도 보조 근거를 얻었으나, 정확한 응답 지평의 일치는 확인되지 않았습니다.",
        "NOT_CORROBORATED": None, "NOT_EVALUABLE": None,
    }
    if row.get("learned_graph_status") not in clauses:
        raise ValueError("ANNOTATION_STATUS_INVALID")
    return seal({"schema": "gdn_annotated_explanation_envelope_v1", "base_explanation": dict(base),
                 "base_hash": stable_hash_v1(base), "sidecar_hash": expected_sidecar_hash,
                 "rule_id": row["rule_id"], "optional_gdn_clause": clauses[row["learned_graph_status"]],
                 "affects_outcome": False})
