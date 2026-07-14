"""Construct and freeze all TASK-035A provider requests before network use."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

REPO_ROOT_BOOTSTRAP = Path(__file__).resolve().parents[2]
if str(REPO_ROOT_BOOTSTRAP) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_BOOTSTRAP))

from experiments.argos_reproduction.expanded_kpi_cohort import REPO_ROOT, read_json, sha256_json, stable_json_bytes, write_json
from experiments.argos_reproduction.prompt_capture import build_system_prompt, serialize_chunk_like_argos


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_request(values: np.ndarray, labels: np.ndarray, indices: np.ndarray, chunk_size: int) -> tuple[dict[str, Any], dict[str, str]]:
    rows = [{"value": float(v), "label": int(l), "index": int(i)} for v, l, i in zip(values, labels, indices)]
    prompt = build_system_prompt(chunk_size)
    system = prompt["system_prompt"]
    user = "##### DATA 0\n" + serialize_chunk_like_argos(rows) + "\n"
    request = {"messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    return request, {
        "system_prompt_template_hash": prompt["template_hash"],
        "system_prompt_hash": prompt["system_prompt_hash"], "user_prompt_hash": sha256_text(user),
        "complete_request_hash": sha256_json(request),
    }


def prepare_requests(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    anchors = read_json(REPO_ROOT / config["reports"]["anchors"])
    private_root = REPO_ROOT / config["private_root"]
    slots: list[dict[str, Any]] = []
    for anchor in anchors["anchors"]:
        private = private_root / "anchors" / anchor["kpi_id"] / f"{anchor['anchor_id']}.npz"
        with np.load(private, allow_pickle=False) as data:
            request, hashes = build_request(data["values"], data["labels"], data["indices"], int(config["design"]["chunk_size"]))
        sibling_hash: str | None = None
        for replicate in range(1, int(config["design"]["replicates_per_anchor"]) + 1):
            slot_id = f"SLOT-{len(slots)+1:03d}"
            request_path = private_root / "requests" / slot_id / "complete_request.json"
            write_json(request_path, request)
            actual = sha256_json(read_json(request_path))
            if actual != hashes["complete_request_hash"]:
                raise RuntimeError("TASK035A_REQUEST_HASH_MISMATCH")
            if sibling_hash is None:
                sibling_hash = actual
            slots.append({
                "slot_id": slot_id, "kpi_id": anchor["kpi_id"], "anchor_id": anchor["anchor_id"],
                "replicate_id": replicate, **hashes, "chunk_hash": anchor["chunk_sha256"],
                "request_body_identical_to_sibling_replicate": actual == sibling_hash,
                "previous_rule_history_present": False,
            })
    expected = int(config["design"]["total_slots"])
    if len(slots) != expected or any(not slot["request_body_identical_to_sibling_replicate"] for slot in slots):
        raise RuntimeError("TASK035A_REQUEST_COHORT_INVALID")
    manifest = {
        "schema_version": "1.0", "task_id": "TASK-035A", "artifact_type": "request_manifest",
        "status": "prepared", "slot_order": [slot["slot_id"] for slot in slots], "slots": slots,
        "registered_slot_count": len(slots), "provider": config["provider"]["provider"],
        "model": config["provider"]["model"], "temperature_parameter_sent": False,
        "provider_seed_sent": False, "previous_rule_history_present": False,
        "raw_prompts_tracked": False,
    }
    manifest["report_hash"] = sha256_json(manifest)
    write_json(REPO_ROOT / config["reports"]["requests"], manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/argos_reproduction/task035a_expanded_rule_cohort.json")
    args = parser.parse_args()
    result = prepare_requests((REPO_ROOT / args.config).resolve())
    print(json.dumps({"status": result["status"], "registered_slot_count": result["registered_slot_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
