#!/usr/bin/env python3
"""Freeze a public-safe hash manifest for V2 evaluation-expansion records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


FILES = (
    "CHANGE_SUMMARY_V1.md",
    "EVALUATION_MASTER_PLAN_V1.md",
    "PANEL_REGISTRY_V1.csv",
    "CROSS_VERSION_REPLICATION_POLICY_V1.md",
    "METRIC_POLICY_V1.md",
    "P1_ELIGIBILITY_POLICY_V1.md",
    "NO_POOLING_INTERPRETATION_V1.md",
    "DATASET_COMPATIBILITY_MATRIX_V1.csv",
    "NORMAL_SPLIT_ROLE_POLICY_V1.md",
    "EXP03_TO_FINAL_METHOD_LOCK_V1.md",
    "DECISION_GATE_PLAN_V1.md",
    "IMPLEMENTATION_TASK_INDEX_V1.csv",
    "ETAPR_DEPENDENCY_RECEIPT_V1.json",
    "OFFICIAL_HAI_PLANNING_IDENTITY_V1.json",
    "DG04_DECISION_BRIEF_TEMPLATE_V1.md",
    "DG05_COMBINED_EVALUATION_AUTHORIZATION_PACKAGE_V1.md",
)


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    directory = repository / "research_control_center/validation_v2/evaluation_expansion"
    records = []
    for name in FILES:
        path = directory / name
        records.append({"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    artifact = {
        "artifact_type": "validation_v2_evaluation_expansion_authority_v1",
        "schema_version": "1.0.0",
        "status": "PREPARATION_ONLY_FROZEN",
        "files": records,
        "official_hai_commit": "2a814cebc9a66b06c9e5cd545e2d72e65d383737",
        "official_etapr_commit": "af9e7aed35cfd160cbe0d04c8ec4c102502cb677",
        "attack_data_accesses": 0,
        "label_accesses": 0,
        "provider_calls": 0,
    }
    artifact["self_hash"] = canonical_hash(artifact)
    target = directory / "EVALUATION_EXPANSION_AUTHORITY_V1.json"
    target.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"EVALUATION_EXPANSION_FREEZE_PASS files={len(records)} self_hash={artifact['self_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
