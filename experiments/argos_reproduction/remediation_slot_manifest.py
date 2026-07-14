"""Bind TASK-035AR slots to immutable TASK-035A anchors and prompt bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from experiments.argos_reproduction.anomaly_anchor_selection import chunk_hash
from experiments.argos_reproduction.expanded_kpi_cohort import read_json, sha256_file, sha256_json, write_json
from experiments.argos_reproduction.task035a_failure_taxonomy import verify_report_hash


class RemediationManifestError(RuntimeError): pass


def remediation_request_hash(complete_prompt_hash: str) -> str:
    return sha256_json({
        "complete_prompt_hash": complete_prompt_hash,
        "provider": "openai_responses",
        "model": "gpt-5.6-luna",
        "max_output_tokens": 6000,
        "temperature_parameter_sent": False,
        "provider_seed_sent": False,
        "reasoning_parameter_added": False,
    })


def build_remediation_slots(original_anchors: list[dict[str, Any]], original_slots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_anchor: dict[str, list[dict[str, Any]]] = {}
    for slot in original_slots: by_anchor.setdefault(slot["anchor_id"], []).append(slot)
    result: list[dict[str, Any]] = []
    for anchor in original_anchors:
        siblings = sorted(by_anchor.get(anchor["anchor_id"], []), key=lambda item: item["replicate_id"])
        if len(siblings) != 2 or {item["replicate_id"] for item in siblings} != {1, 2} or len({item["complete_request_hash"] for item in siblings}) != 1:
            raise RemediationManifestError("TASK035AR_ORIGINAL_SIBLING_BINDING_INVALID")
        for replicate_id in (3, 4):
            result.append({
                "slot_id": f"SLOT-R{len(result)+1:03d}", "remediation_slot_id": f"SLOT-R{len(result)+1:03d}",
                "parent_anchor_id": anchor["anchor_id"], "anchor_id": anchor["anchor_id"], "kpi_id": anchor["kpi_id"], "replicate_id": replicate_id,
                "task035a_system_prompt_hash": siblings[0]["system_prompt_hash"], "task035a_user_prompt_hash": siblings[0]["user_prompt_hash"],
                "task035a_chunk_hash": siblings[0]["chunk_hash"], "task035a_complete_prompt_hash": siblings[0]["complete_request_hash"],
                "new_request_hash": remediation_request_hash(siblings[0]["complete_request_hash"]),
                "complete_request_hash": siblings[0]["complete_request_hash"],
                "max_output_tokens": 6000, "prompt_bytes_unchanged": True,
            })
    return result


def prepare_manifest(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path); old = config["task035a"]
    anchor_manifest = verify_report_hash(ROOT / old["anchor_report"]); request_manifest = verify_report_hash(ROOT / old["request_report"])
    if len(anchor_manifest["anchors"]) != 50 or request_manifest["registered_slot_count"] != 100:
        raise RemediationManifestError("TASK035AR_ORIGINAL_COHORT_SIZE_INVALID")
    slots = build_remediation_slots(anchor_manifest["anchors"], request_manifest["slots"])
    if len(slots) != 100 or {item["replicate_id"] for item in slots} != {3, 4}:
        raise RemediationManifestError("TASK035AR_REMEDIATION_SLOT_SIZE_INVALID")
    old_private = ROOT / old["private_root"]; new_private = ROOT / config["private_root"]
    old_slot_by_anchor = {item["anchor_id"]: item for item in request_manifest["slots"] if item["replicate_id"] == 1}
    original_hashes: dict[str, str] = {}
    for anchor in anchor_manifest["anchors"]:
        old_anchor = old_private / "anchors" / anchor["kpi_id"] / f"{anchor['anchor_id']}.npz"
        with np.load(old_anchor, allow_pickle=False) as data:
            actual_chunk_hash = chunk_hash(data["values"], data["labels"], data["indices"])
        if actual_chunk_hash != anchor["chunk_sha256"]:
            raise RemediationManifestError("TASK035AR_ANCHOR_HASH_MISMATCH")
        target_anchor = new_private / "anchors" / anchor["kpi_id"] / old_anchor.name; target_anchor.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(old_anchor, target_anchor)
        if sha256_file(old_anchor) != sha256_file(target_anchor): raise RemediationManifestError("TASK035AR_ANCHOR_COPY_MISMATCH")
        original_hashes[f"anchor:{anchor['anchor_id']}"] = sha256_file(old_anchor)
        source_request = old_private / "requests" / old_slot_by_anchor[anchor["anchor_id"]]["slot_id"] / "complete_request.json"
        source_bytes = source_request.read_bytes(); source_hash = sha256_json(read_json(source_request))
        if source_hash != old_slot_by_anchor[anchor["anchor_id"]]["complete_request_hash"]: raise RemediationManifestError("TASK035AR_ORIGINAL_REQUEST_HASH_MISMATCH")
        original_hashes[f"request:{anchor['anchor_id']}"] = hashlib.sha256(source_bytes).hexdigest()
        for slot in [item for item in slots if item["anchor_id"] == anchor["anchor_id"]]:
            target = new_private / "requests" / slot["slot_id"] / "complete_request.json"; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(source_bytes)
            if sha256_json(read_json(target)) != slot["task035a_complete_prompt_hash"] or target.read_bytes() != source_bytes:
                raise RemediationManifestError("TASK035AR_PROMPT_BYTES_CHANGED")
            if remediation_request_hash(slot["task035a_complete_prompt_hash"]) != slot["new_request_hash"]:
                raise RemediationManifestError("TASK035AR_REQUEST_ENVELOPE_HASH_MISMATCH")
    report = {
        "schema_version": "1.0", "task_id": "TASK-035AR", "artifact_type": "remediation_request_manifest",
        "status": "prepared", "slot_order": [item["slot_id"] for item in slots], "registered_slot_count": len(slots), "replicate_ids": [3, 4],
        "provider": config["provider"]["provider"], "model": config["provider"]["model"], "max_output_tokens": 6000,
        "prompt_change": False, "anchor_change": False, "chunk_change": False, "reasoning_parameter_added": False,
        "slots": slots, "task035a_lineage_hash": sha256_json(original_hashes), "raw_prompts_tracked": False,
    }
    report["report_hash"] = sha256_json(report); write_json(ROOT / config["reports"]["requests"], report); return report


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--config",default="configs/argos_reproduction/task035ar_output_budget_remediation.json"); args=parser.parse_args(); report=prepare_manifest((ROOT/args.config).resolve()); print(json.dumps({"registered_slot_count":report["registered_slot_count"],"status":report["status"]})); return 0


if __name__ == "__main__": raise SystemExit(main())
