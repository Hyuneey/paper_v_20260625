from __future__ import annotations

import json
from pathlib import Path

from paperworks.v6.common import stable_hash_v1
from paperworks.v6.task039e0_rule_construction_protocol_v1 import (
    ConfirmedRelationIdentityCohortV1,
    ConfirmedRelationIdentityV1,
)


ROOT = Path(__file__).resolve().parents[1]


def hashed(content: dict) -> dict:
    return {**content, "artifact_hash": stable_hash_v1(content)}


def synthetic_real_inputs():
    public = json.loads(
        (ROOT / "docs/task_reports/TASK-039E0_CONFIRMED_RELATION_COHORT.json").read_text(encoding="utf-8")
    )
    source_by_name: dict[str, dict] = {}
    target_by_name: dict[str, dict] = {}
    d1_records: list[dict] = []
    d2_records: list[dict] = []
    relations: list[ConfirmedRelationIdentityV1] = []
    for index, original in enumerate(public["relations"]):
        source = original["source"]
        target = original["target"]
        if source not in source_by_name:
            source_by_name[source] = hashed({
                "source": source,
                "source_step_threshold": 1.0 + len(source_by_name),
                "source_stability_tolerance": 0.2 + len(source_by_name) / 100,
                "parameter_status": "supported",
            })
        if target not in target_by_name:
            target_by_name[target] = hashed({
                "target": target,
                "target_noise_scale": 0.5 + len(target_by_name) / 100,
            })
        source_record = source_by_name[source]
        target_record = target_by_name[target]
        d1 = hashed({
            "source": source,
            "target": target,
            "source_step_direction": original["source_step_direction"],
            "selected_target_direction": original["target_response_direction"],
            "selected_horizon_seconds": original["selected_delay_horizon_seconds"],
            "source_parameter_ref": source_record["artifact_hash"],
            "target_parameter_ref": target_record["artifact_hash"],
            "fit_result": "fit_supported",
            "lower_ranked_fallback_used": False,
        })
        d2 = hashed({
            "source": source,
            "target": target,
            "source_step_direction": original["source_step_direction"],
            "target_response_direction": original["target_response_direction"],
            "selected_horizon_seconds": original["selected_delay_horizon_seconds"],
            "source_parameter_record_hash": source_record["artifact_hash"],
            "target_parameter_record_hash": target_record["artifact_hash"],
            "d1_directional_record_hash": d1["artifact_hash"],
            "confirmation_status": "calibration_confirmed",
        })
        d1_records.append(d1)
        d2_records.append(d2)
        relations.append(ConfirmedRelationIdentityV1(
            source=source,
            source_step_direction=original["source_step_direction"],
            target=target,
            target_response_direction=original["target_response_direction"],
            selected_delay_horizon_seconds=original["selected_delay_horizon_seconds"],
            d1_directional_record_hash=d1["artifact_hash"],
            d2_confirmation_record_hash=d2["artifact_hash"],
        ))
    cohort = ConfirmedRelationIdentityCohortV1(tuple(relations))
    return (
        cohort,
        {"records": list(source_by_name.values())},
        {"records": list(target_by_name.values())},
        {"records": d1_records},
        {"records": d2_records},
    )
