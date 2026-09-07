"""Publish V11R1 review artifacts after a completed synthetic qualification.

The path-bearing runtime materialization plan is deliberately neither an input
nor an output.  This builder binds portable source identity and public-safe
qualification evidence only.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes, load_self_hashed, self_hashed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase-a-manifest", type=Path, required=True)
    parser.add_argument("--qualification-receipt", type=Path, required=True)
    parser.add_argument("--materialization-contract", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    if args.output_directory.exists():
        raise RuntimeError("V11R1_FINAL_CANDIDATE_NAMESPACE_REUSE_REJECTED")
    phase_a = load_self_hashed(args.phase_a_manifest, "dg05_executable_v11r1_candidate_manifest_v1")
    qualification = load_self_hashed(args.qualification_receipt, "dg05_v11r1_shared_route_receipt_v1")
    contract = load_self_hashed(args.materialization_contract, "dg05_v11r1_protected_resource_materialization_contract_v1")
    if qualification["status"] != "PASS" or qualification["release_hash"] != phase_a["self_hash"]:
        raise RuntimeError("V11R1_PHASE_B_QUALIFICATION_BINDING_FAILED")
    final = self_hashed({
        **{key: value for key, value in phase_a.items() if key != "self_hash"},
        "execution_binding_hash": phase_a["self_hash"],
        "qualification_receipt_hash": qualification["self_hash"],
        "resource_materialization_contract_hash": contract["self_hash"],
        "approval_status": "NOT_APPROVED",
        "user_approved_release_hash": None,
    })
    args.output_directory.mkdir(parents=True)
    for name, document in (
        ("V11R1_EXECUTION_BINDING_MANIFEST.json", phase_a),
        ("V11R1_SHARED_ROUTE_QUALIFICATION_RECEIPT.json", qualification),
        ("DG05_V11R1_PROTECTED_RESOURCE_MATERIALIZATION_CONTRACT_V1.json", contract),
        ("DG05_EXECUTABLE_V11R1_FINAL_MANIFEST.json", final),
    ):
        (args.output_directory / name).write_bytes(canonical_bytes(document) + b"\n")
    print(final["self_hash"])


if __name__ == "__main__":
    main()
