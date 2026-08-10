"""Generate the deterministic TASK-039C0 protocol freeze artifacts.

The generator reads tracked public lineage only. It never opens HAI data or
BR2 private scientific ledgers.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from paperworks.v6.candidate_discovery_protocol_v1 import (  # noqa: E402
    AUTHORITATIVE_MAIN_COMMIT,
    BR1_PROTOCOL_BUNDLE_HASH,
    CANDIDATE_LEARNING_VIEW_ID,
    CANONICAL_RULE_VIEW_ID,
    NORMAL_CANDIDATE_FIT_SPLIT_ID,
    NORMAL_GUARD_SPLIT_ID,
    NORMAL_RELATION_CALIBRATION_SPLIT_ID,
    PROCESS_FREEZE_HASH,
    build_default_candidate_discovery_bundle_v1,
    default_candidate_discovery_config_content_v1,
)
from paperworks.v6.common import canonical_json_v1, stable_hash_v1  # noqa: E402


BR2_CONFIG = "configs/v6/task039br2_hai_continuous_step_feasibility.json"
BR2_PROCESS_FREEZE = "docs/task_reports/TASK-039BR2_PROCESS_FREEZE.json"
BR2_CANDIDATE_VIEW = "docs/task_reports/TASK-039BR2_CANDIDATE_LEARNING_VIEW_V2.json"
BR2_CANONICAL_VIEW = "docs/task_reports/TASK-039BR2_CANONICAL_RULE_VIEW_V2.json"
BR2_SPLITS = "docs/task_reports/TASK-039BR2_SPLIT_MANIFESTS_V2.json"
BR1_BUNDLE = "docs/task_reports/TASK-039BR1_PROTOCOL_BUNDLE.json"


def _load_json(relative_path: str) -> dict[str, Any]:
    path = REPOSITORY_ROOT / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_self_hash(
    payload: Mapping[str, Any], field_name: str, expected: str
) -> None:
    observed = payload.get(field_name)
    if observed != expected:
        raise ValueError(f"{field_name} identity mismatch")
    content = deepcopy(dict(payload))
    content.pop(field_name, None)
    if stable_hash_v1(content) != expected:
        raise ValueError(f"{field_name} self-hash mismatch")


def _verify_lineage() -> dict[str, Any]:
    br2_config = _load_json(BR2_CONFIG)
    _verify_self_hash(br2_config, "config_hash", str(br2_config["config_hash"]))
    process_freeze = _load_json(BR2_PROCESS_FREEZE)
    _verify_self_hash(process_freeze, "artifact_hash", PROCESS_FREEZE_HASH)
    if process_freeze.get("selected_process_id") != "P1":
        raise ValueError("BR2 selected process is not P1")
    candidate_view = _load_json(BR2_CANDIDATE_VIEW)
    _verify_self_hash(candidate_view, "artifact_hash", CANDIDATE_LEARNING_VIEW_ID)
    canonical_view = _load_json(BR2_CANONICAL_VIEW)
    _verify_self_hash(canonical_view, "artifact_hash", CANONICAL_RULE_VIEW_ID)
    br1_bundle = _load_json(BR1_BUNDLE)
    _verify_self_hash(br1_bundle, "artifact_hash", BR1_PROTOCOL_BUNDLE_HASH)

    splits = _load_json(BR2_SPLITS)
    split_records = {item["role"]: item for item in splits.get("records", [])}
    expected_splits = {
        "normal_candidate_fit": NORMAL_CANDIDATE_FIT_SPLIT_ID,
        "normal_relation_calibration": NORMAL_RELATION_CALIBRATION_SPLIT_ID,
        "normal_guard": NORMAL_GUARD_SPLIT_ID,
    }
    for role, expected_hash in expected_splits.items():
        record = split_records.get(role)
        if record is None:
            raise ValueError(f"missing BR2 split: {role}")
        _verify_self_hash(record, "artifact_hash", expected_hash)

    eligibility = br2_config.get("frozen_eligibility", {}).get("P1", {})
    sources = eligibility.get("sources")
    targets = eligibility.get("targets")
    if not isinstance(sources, list) or not isinstance(targets, list):
        raise ValueError("frozen public P1 identities are unavailable")
    if len(sources) != 12 or len(targets) != 12:
        raise ValueError("frozen public P1 identity count changed")
    return {"sources": sources, "targets": targets}


def _write_json(relative_path: str, payload: Mapping[str, Any]) -> None:
    path = REPOSITORY_ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _inferred_schema(value: Any, *, property_name: str = "") -> dict[str, Any]:
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if value is None:
        return {"type": "null"}
    if isinstance(value, str):
        result: dict[str, Any] = {"type": "string"}
        if property_name == "schema_version":
            result["const"] = value
        elif property_name == "artifact_type":
            result["const"] = value
        elif property_name.endswith(("_hash", "_id")) and len(value) == 64:
            result["pattern"] = "^[0-9a-f]{64}$"
        return result
    if isinstance(value, list):
        item_schema: dict[str, Any] = {}
        if value:
            candidates = [
                json.dumps(_inferred_schema(item), sort_keys=True) for item in value
            ]
            if len(set(candidates)) == 1:
                item_schema = json.loads(candidates[0])
            elif all(isinstance(item, str) for item in value):
                item_schema = {"type": "string"}
        return {"type": "array", "items": item_schema}
    if isinstance(value, Mapping):
        properties = {
            key: _inferred_schema(item, property_name=key)
            for key, item in sorted(value.items())
        }
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": list(properties),
        }
    raise TypeError(f"unsupported schema exemplar: {type(value).__name__}")


def _write_artifact_schema(artifact: Mapping[str, Any]) -> None:
    artifact_type = str(artifact["artifact_type"])
    schema = _inferred_schema(artifact)
    schema.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": (
                "https://paperworks.local/schemas/v6/"
                f"{artifact_type}_schema.json"
            ),
            "title": artifact_type,
        }
    )
    _write_json(f"schemas/v6/{artifact_type}_schema.json", schema)


def generate() -> dict[str, str]:
    identities = _verify_lineage()
    config = default_candidate_discovery_config_content_v1(
        source_entries=identities["sources"], target_entries=identities["targets"]
    )
    config["config_hash"] = stable_hash_v1(config)
    bundle = build_default_candidate_discovery_bundle_v1(config=config)

    schema_artifacts = (
        bundle.universe_policy,
        bundle.budget_policy,
        bundle.metadata_policy,
        bundle.statistical_policy,
        bundle.gdn_policy,
        bundle.arm_result_contract,
        bundle.integration_policy,
        bundle.data_access_policy,
        bundle.parallel_branch_plan,
        bundle,
    )
    for artifact in schema_artifacts:
        _write_artifact_schema(artifact.to_dict())

    _write_json("configs/v6/task039c0_candidate_discovery_protocol.json", config)
    _write_json(
        "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json", bundle.to_dict()
    )
    _write_json(
        "docs/task_reports/TASK-039C0_PARALLEL_BRANCH_PLAN.json",
        bundle.parallel_branch_plan.to_dict(),
    )
    _write_json(
        "docs/task_reports/TASK-039C0_DATA_ACCESS_POLICY.json",
        bundle.data_access_policy.to_dict(),
    )
    return {
        "authoritative_main_commit": AUTHORITATIVE_MAIN_COMMIT,
        "config_hash": config["config_hash"],
        "protocol_bundle_hash": bundle.artifact_hash,
        "source_identity_list_hash": bundle.universe_policy.source_identity_list_hash,
        "target_identity_list_hash": bundle.universe_policy.target_identity_list_hash,
        "eligible_pair_universe_hash": bundle.universe_policy.eligible_pair_universe_hash,
        "metadata_policy_hash": bundle.metadata_policy.artifact_hash,
        "statistical_policy_hash": bundle.statistical_policy.artifact_hash,
        "gdn_policy_hash": bundle.gdn_policy.artifact_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = generate()
    if args.check:
        for relative in (
            "configs/v6/task039c0_candidate_discovery_protocol.json",
            "docs/task_reports/TASK-039C0_PROTOCOL_BUNDLE.json",
            "docs/task_reports/TASK-039C0_PARALLEL_BRANCH_PLAN.json",
            "docs/task_reports/TASK-039C0_DATA_ACCESS_POLICY.json",
        ):
            json.loads((REPOSITORY_ROOT / relative).read_text(encoding="utf-8"))
    print(canonical_json_v1(generated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
