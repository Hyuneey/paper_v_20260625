"""Publish a path-free hash binding for the frozen HAI23 detector authority.

This reads only the existing private custody manifest and the hash-only
``authority.private.json`` record created by EXP-04. It never deserializes
model bytes, scores, test data, labels, or attack metadata.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_control_center/validation_v2/multipanel_pre_dg05"
INDEX = ROOT / "research_control_center/validation_v2/local_custody/PUBLIC_PRIVATE_ARTIFACT_INDEX_FINAL_V2.json"
AUTHORITY_ARTIFACT_ID = "FRONT_RESULT_000012"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    common = Path(
        subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, text=True).strip()
    ).resolve()
    vault = common.parent.parent / "paper_v_20260625_private_vault"
    snapshot = vault / "gdn-front-exp04-001" / "snapshots" / f"{index['private_manifest_hash']}.json"
    snapshot_doc = json.loads(snapshot.read_text(encoding="utf-8"))
    record = next(item for item in snapshot_doc["records"] if item["artifact_id"] == AUTHORITY_ARTIFACT_ID)
    authority_path = Path(record["private_source"])
    if file_hash(authority_path) != record["content_hash"]:
        raise ValueError("HAI23_PRIVATE_AUTHORITY_HASH_MISMATCH")
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    expected_keys = {
        "pca_fit_hash", "if_fit_hash", "pca_threshold_hash", "if_threshold_hash",
        "model_bytes_sha256", "source_commit", "environment_hash", "restoration", "execution_model",
    }
    if not expected_keys.issubset(authority):
        raise ValueError("HAI23_PRIVATE_AUTHORITY_FIELDS_MISSING")
    for key in expected_keys - {"restoration", "execution_model"}:
        value = authority[key]
        expected_length = 40 if key == "source_commit" else 64
        if not isinstance(value, str) or len(value) != expected_length:
            raise ValueError(f"HAI23_PRIVATE_AUTHORITY_INVALID_{key.upper()}")
    model_record = next(item for item in snapshot_doc["records"] if item["artifact_id"] == "FRONT_RESULT_000013")
    if authority["model_bytes_sha256"] != model_record["content_hash"]:
        raise ValueError("HAI23_PRIVATE_MODEL_BYTES_NOT_BOUND")
    body = {
        "schema": "hai23_detector_private_hash_binding_v1",
        "status": "EXACT_PRIVATE_HASH_REPLAY_PASS",
        "source_commit": authority["source_commit"],
        "environment_hash": authority["environment_hash"],
        "private_manifest_hash": index["private_manifest_hash"],
        "private_authority_artifact_id": AUTHORITY_ARTIFACT_ID,
        "private_authority_content_hash": record["content_hash"],
        "private_model_artifact_id": "FRONT_RESULT_000013",
        "private_model_bytes_hash": authority["model_bytes_sha256"],
        "pca_fit_authority_hash": authority["pca_fit_hash"],
        "pca_threshold_authority_hash": authority["pca_threshold_hash"],
        "if_fit_authority_hash": authority["if_fit_hash"],
        "if_threshold_authority_hash": authority["if_threshold_hash"],
        "restoration": authority["restoration"],
        "execution_model": authority["execution_model"],
        "private_paths_published": False,
        "private_numeric_values_published": False,
        "model_bytes_deserialized": False,
        "score_bytes_read": False,
        "test_or_attack_payload_accesses": 0,
        "label_or_scenario_accesses": 0,
    }
    body["self_hash"] = sha256(canonical(body)).hexdigest()
    (OUT / "HAI23_DETECTOR_PRIVATE_HASH_BINDING_V1.json").write_bytes(canonical(body) + b"\n")
    print(json.dumps({"status": body["status"], "self_hash": body["self_hash"]}))


if __name__ == "__main__":
    main()
