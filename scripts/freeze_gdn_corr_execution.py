#!/usr/bin/env python3
"""Freeze the corrected-analysis orchestration before executing it."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

from paperworks.v6.common import stable_hash_v1


def main() -> None:
    root = Path.cwd().resolve(strict=True)
    contract_path = root / "research_control_center/validation_v2/gdn_corr_001/contracts/EXP01B_R1_CORRECTION_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    files = (
        "src/paperworks/validation_v2/gdn_corr_v1.py",
        "src/paperworks/validation_v2/gdn_corr_r1_runner_v1.py",
        "scripts/run_exp01b_r1_corrected.py",
    )
    previous = root / "research_control_center/validation_v2/gdn_corr_001/contracts/EXP01B_R1_EXECUTION_BINDING_R2.json"
    previous_document = json.loads(previous.read_text(encoding="utf-8"))
    body = {
        "schema": "paperworks.validation_v2.exp01b_r1_execution_binding_v1",
        "schema_version": "1.0.0", "experiment_id": "EXP-01B-R1",
        "source_commit": source_commit, "contract_hash": contract["contract_hash"],
        "implementation_hashes": {name: sha256((root / name).read_bytes()).hexdigest() for name in files},
        "supersedes_binding_hash": previous_document["binding_hash"],
        "repair_scope": "AUDIT_FROZEN_V1_GDN_UNIQUE_PAIR_SET_THROUGH_TRUE_FORMAL_V4_PATH",
        "status": "FROZEN_BEFORE_CORRECTED_RESULT_ACCESS", "retraining": False,
        "test1_allowed": False, "labels_allowed": False, "test2_allowed": False, "heldout_allowed": False,
    }
    document = {**body, "binding_hash": stable_hash_v1(body)}
    target = root / "research_control_center/validation_v2/gdn_corr_001/contracts/EXP01B_R1_EXECUTION_BINDING_R3.json"
    payload = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    print(json.dumps({"status": "PASS", "binding_hash": document["binding_hash"], "source_commit": source_commit}, sort_keys=True))


if __name__ == "__main__":
    main()
