"""Freeze V11R2 review artifacts from an already completed synthetic route."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes, load_self_hashed, self_hashed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase-a", type=Path, required=True)
    ap.add_argument("--qualification", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists(): raise RuntimeError("V11R2_FINAL_NAMESPACE_REUSE_REJECTED")
    phase = load_self_hashed(args.phase_a, "dg05_executable_v11r2_candidate_manifest_v1")
    qualification = load_self_hashed(args.qualification, "dg05_v11r1_shared_route_receipt_v1")
    if qualification.get("status") != "PASS" or qualification.get("release_hash") != phase["self_hash"]:
        raise RuntimeError("V11R2_PHASE_B_QUALIFICATION_BINDING_FAILED")
    final = self_hashed({**{k:v for k,v in phase.items() if k != "self_hash"},
                         "execution_binding_hash": phase["self_hash"],
                         "qualification_receipt_hash": qualification["self_hash"],
                         "approval_status": "NOT_APPROVED", "user_approved_release_hash": None})
    args.output.mkdir(parents=True)
    for name, document in (("V11R2_EXECUTION_BINDING_MANIFEST.json", phase),
                           ("V11R2_SHARED_ROUTE_QUALIFICATION_RECEIPT.json", qualification),
                           ("DG05_EXECUTABLE_V11R2_FINAL_MANIFEST.json", final)):
        (args.output / name).write_bytes(canonical_bytes(document) + b"\n")
    print(final["self_hash"])


if __name__ == "__main__": main()
