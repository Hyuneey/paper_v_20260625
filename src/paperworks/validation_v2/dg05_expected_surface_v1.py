"""Deterministic pre-access expected DG-05 V3 result-surface builder."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from .dg05_execution_closure_v1 import FROZEN_METHOD_IDS_BY_PANEL_V1

PANELS = tuple(FROZEN_METHOD_IDS_BY_PANEL_V1)
METHOD_KINDS = ("SCENARIO_HIT_MISS", "SCENARIO_RECALL", "WILSON95", "DETECTION_DELAY", "DELAY_SUMMARY",
                "NORMAL_BURDEN", "ETAPR_PER_FILE", "ETAPR_VERSION_UNION")
RULE_METHODS = {"M1_T0_RULE_ONLY", "M2_T2_RULE_ONLY", "M3_PCA_PLUS_T0", "M4_PCA_PLUS_T2",
                "ISOLATION_FOREST_PLUS_T2", "V2A_RULE_ONLY_REFERENCE", "HISTORICAL_PCA_PLUS_V2A_CONTINUITY"}
CONTRASTS = ("C1", "C2", "C3", "C4")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def build_expected_result_surface_authority_v1(*, metric_surface_contract_hash: str) -> dict[str, Any]:
    ids = []
    for panel in PANELS:
        for method in FROZEN_METHOD_IDS_BY_PANEL_V1[panel]:
            ids.extend(f"{panel}|METHOD|{method}|{kind}" for kind in METHOD_KINDS)
            if method in RULE_METHODS:
                ids.append(f"{panel}|METHOD|{method}|RULE_RUNTIME_CENSUS")
        for contrast in CONTRASTS:
            ids.extend((f"{panel}|CONTRAST|{contrast}|PAIRED_TABLE", f"{panel}|CONTRAST|{contrast}|MCNEMAR_EXACT"))
        ids.append(f"{panel}|PANEL|RECOVERY|RULE_FUSION_RECOVERY")
    body = {"schema": "expected_result_surface_authority_v1", "metric_surface_contract_hash": metric_surface_contract_hash,
            "surface_ids": sorted(ids), "surface_count": len(ids), "derivation": "FROZEN_PANEL_METHOD_AND_CONTRAST_CENSUS",
            "cross_version_pooling": False}
    return {**body, "self_hash": sha256(_canonical(body)).hexdigest()}


__all__ = ["build_expected_result_surface_authority_v1"]
