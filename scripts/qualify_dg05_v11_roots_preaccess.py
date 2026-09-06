"""Run only V11 root/custodian fresh-process prequalification.

This intentionally produces a non-executable technical prequalification.  It
does not invoke the V5 schedule, so it cannot be mistaken for a full release
candidate or for a held-out execution.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from paperworks.validation_v2.dg05_production_chain_v11 import (
    build_v11_candidate_manifest, canonical_bytes, digest, load_self_hashed, self_hashed,
)
from paperworks.validation_v2.dg05_v11_root_verifier_v1 import verify_v11_roots

OUT = ROOT / "research_control_center/validation_v2/dg05_v11_prequalification"


def write(name: str, value: dict) -> None:
    path = OUT / name
    if path.exists():
        raise RuntimeError("APPEND_ONLY_PREQUALIFICATION_CONFLICT")
    path.write_bytes(canonical_bytes(value) + b"\n")


def implementation_paths() -> dict[str, Path]:
    return {
        "scenario_adapter": ROOT / "src/paperworks/validation_v2/dg05_hai_scenario_adapter_v1.py",
        "custodian": ROOT / "src/paperworks/validation_v2/dg05_label_custodian_v3.py",
        "production_route": ROOT / "src/paperworks/validation_v2/dg05_production_route_v11.py",
        "frozen_v5_kernel": ROOT / "src/paperworks/validation_v2/dg05_production_route_v5.py",
        "fresh_process_launcher": ROOT / "scripts/run_dg05_v11_preaccess_launcher.py",
        "root_verifier": ROOT / "src/paperworks/validation_v2/dg05_v11_root_verifier_v1.py",
        "release_gate": ROOT / "src/paperworks/validation_v2/dg05_production_chain_v11.py",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-authority", required=True, type=Path)
    parser.add_argument("--p1-authority", required=True, type=Path)
    args = parser.parse_args()
    if OUT.exists():
        raise RuntimeError("APPEND_ONLY_PREQUALIFICATION_DIRECTORY_CONFLICT")
    scenario = load_self_hashed(args.scenario_authority, "hai_official_source_triangulated_scenario_authority_private_v1")
    p1 = load_self_hashed(args.p1_authority, "hai_p1_direct_target_denominator_authority_v2")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    roots = {
        "physical_custody": "46b1319363731aeb050133b92aee0f5d37db0879cb6066ceaee70191cdd3fbaa",
        "normal_registry": "35b34e0a33d99334bf7bbf9a31289221db052429c6710a216c53165711b84220",
        "scenario_authority": scenario["self_hash"], "unified_p1": p1["self_hash"],
        "dec031": "e9706eb50391021ada69fe269be3f22bb50f591239daaedfaa6194a04275de62",
        "dec034": "67a724b3b433d2b21904d587a1ce357090021dc654f212e667e0dd7a79c45ccd",
        "dec035": "fcea5ca9055bfecb54656ab75b5e0899fc032f75ba94ae67dea8117f2b080038",
        "dec036": "7f584ecce817ac873984a7f86d7d8e7c7bab0132472bd092e3b2c2f411a6544b",
        "dec037": "3e0310ebfbece3d1dcc3305f39a727feca5c482b4f9a5c01e2b8af1da6e37bd7",
        "scientific_preregistration": "cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61",
    }
    qualifications = {key: digest({"v11_prequalification_contract": key}) for key in
                      ("root_replay", "kernel_parity", "fresh_process", "independent_qa", "privacy", "adversarial", "rehearsal")}
    manifest = build_v11_candidate_manifest(repository_root=ROOT, source_commit=head,
                                            authority_hashes=roots, implementation_paths=implementation_paths(),
                                            qualification_hashes=qualifications,
                                            status="TECHNICAL_PREQUALIFICATION_ONLY")
    OUT.mkdir(parents=True)
    manifest_path = OUT / "DG05_V11_TECHNICAL_PREQUALIFICATION_MANIFEST_V1.json"
    write(manifest_path.name, manifest)
    root = verify_v11_roots(repository_root=ROOT, manifest_path=manifest_path, scenario_path=args.scenario_authority,
                            p1_path=args.p1_authority, expected_hash=manifest["self_hash"])
    write("ROOT_TO_KERNEL_PREQUALIFICATION_REPLAY_V1.json", root)
    completed = subprocess.run([sys.executable, str(ROOT / "scripts/run_dg05_v11_preaccess_launcher.py"),
                                 "--manifest", str(manifest_path), "--scenario", str(args.scenario_authority), "--p1", str(args.p1_authority),
                                 "--expected-hash", manifest["self_hash"]], check=True, capture_output=True, text=True)
    launcher = json.loads(completed.stdout)
    if not launcher.get("pid_distinct") or launcher.get("heldout_prediction_cells") != 0:
        raise RuntimeError("FRESH_PROCESS_PREQUALIFICATION_FAILED")
    receipt = self_hashed({"schema": "dg05_v11_preaccess_technical_qualification_receipt_v1",
                           "status": "MAXIMUM_SAFE_PROGRESS_COMPLETE_BLOCKED",
                           "manifest_hash": manifest["self_hash"], "root_replay_hash": root["self_hash"],
                           "fresh_process": {k: launcher[k] for k in ("pid_distinct", "mode", "root_replay_hash", "route_initialization_hash")},
                           "scenario_records": 146, "p1_decisions": 146, "p1_unresolved": 0,
                           "production_kernel_resolved": True, "production_kernel_cells": 0,
                           "synthetic_fallback_cells": 0, "heldout_prediction_cells": 0, "heldout_metric_cells": 0,
                           "narrowest_blocker": "V11_SCHEDULE_RELEASE_PROVENANCE_BRIDGE_MISSING",
                           "reason": "The frozen V5 schedule rejects a V11 manifest and no V11-bound schedule wrapper yet carries V11 release provenance into its result container.",
                           "candidate_created": False, "user_approval_required": False,
                           "source_commit": head})
    write("DG05_V11_TECHNICAL_QUALIFICATION_RECEIPT_V1.json", receipt)
    print(json.dumps({"manifest": manifest["self_hash"], "root": root["self_hash"], "receipt": receipt["self_hash"]}, sort_keys=True))


if __name__ == "__main__":
    main()
