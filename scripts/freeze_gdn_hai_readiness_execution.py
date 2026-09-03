#!/usr/bin/env python3
from hashlib import sha256
import json, os, subprocess
from pathlib import Path
from paperworks.v6.common import stable_hash_v1

root = Path.cwd().resolve(strict=True)
prereg = json.loads((root / "research_control_center/validation_v2/gdn_corr_001/exp01c_gdn_hai/preregistration/EXP01C_PREREGISTRATION.json").read_text(encoding="utf-8"))
files = ("src/paperworks/validation_v2/gdn_corr_v1.py", "scripts/run_gdn_hai_readiness_audit.py")
body = {
    "schema": "paperworks.validation_v2.gdn_hai_readiness_execution_binding_v1",
    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
    "preregistration_hash": prereg["preregistration_hash"],
    "implementation_hashes": {name: sha256((root / name).read_bytes()).hexdigest() for name in files},
    "status": "FROZEN_BEFORE_NORMAL_DATA_IO", "allowed_splits": ["train1", "train2"],
    "test1_allowed": False, "labels_allowed": False, "test2_allowed": False, "heldout_allowed": False,
}
document = {**body, "binding_hash": stable_hash_v1(body)}; target = root / "research_control_center/validation_v2/gdn_corr_001/contracts/HAI_READINESS_EXECUTION_BINDING.json"
payload = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
target.parent.mkdir(parents=True, exist_ok=True); descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
try:
    with os.fdopen(descriptor, "wb", closefd=False) as stream: stream.write(payload); stream.flush(); os.fsync(stream.fileno())
finally: os.close(descriptor)
print(json.dumps({"status": "PASS", "binding_hash": document["binding_hash"]}, sort_keys=True))
