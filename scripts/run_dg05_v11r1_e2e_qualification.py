"""Fresh-process V11R1 full synthetic E2E qualification entrypoint."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"),
                str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"),
                str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies")]

from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes
from paperworks.validation_v2.dg05_production_chain_v11r1 import build_manifest
from paperworks.validation_v2.dg05_v11r1_e2e_qualification import run_full_synthetic_e2e_v11r1
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1


def _paths() -> dict[str, Path]:
    p = ROOT / "src/paperworks/validation_v2"
    return {
        "successor_gate": p / "dg05_production_chain_v11r1.py",
        "unified_runner": ROOT / "scripts/run_dg05_v11r1.py",
        "resource_loader": p / "dg05_v11r1_resource_loader.py",
        "resource_orchestrator": p / "dg05_real_resource_orchestrator_v11r1.py",
        "production_executor": p / "dg05_v11r1_production_executor.py",
        "e2e_qualification": p / "dg05_v11r1_e2e_qualification.py",
        "terminal_chain": p / "dg05_v11r1_terminal_chain.py",
        "v5_compatibility": p / "dg05_v11r1_v5_compatibility.py",
        "postfreeze_metric_binding": p / "dg05_v11r1_postfreeze_metric_binding.py",
        "v11_bridge": p / "dg05_schedule_release_provenance_bridge_v11.py",
        "connected_rehearsal": p / "dg05_connected_rehearsal_v5.py",
        "v5_kernel": p / "dg05_production_route_v5.py",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--legacy-release", required=True, type=Path)
    ap.add_argument("--predecessor-v4-manifest", required=True, type=Path)
    ap.add_argument("--predecessor-v4-closure", required=True, type=Path)
    ap.add_argument("--historical-v1-manifest", required=True, type=Path)
    ap.add_argument("--metric-contract", required=True, type=Path)
    ap.add_argument("--normal-registry", required=True, type=Path)
    ap.add_argument("--private-normal-manifest", required=True, type=Path)
    ap.add_argument("--expected-private-normal-hash", required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise RuntimeError("V11R1_E2E_OUTPUT_APPEND_ONLY_CONFLICT")
    args.output.mkdir(parents=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = build_manifest(repository_root=ROOT, source_commit=head, implementation_paths=_paths())
    manifest_path = args.output / "V11R1_EXECUTION_BINDING_MANIFEST.json"
    manifest_path.write_bytes(canonical_bytes(manifest) + b"\n")
    wrapper = OfficialEtaprV1(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677")
    legacy = json.loads(args.legacy_release.read_text(encoding="ascii"))
    receipt = run_full_synthetic_e2e_v11r1(
        repository_root=ROOT, work_root=args.output / "synthetic-route",
        outer_manifest_path=manifest_path, expected_outer_hash=manifest["self_hash"],
        legacy_release_path=args.legacy_release,
        predecessor_v4_path=args.predecessor_v4_manifest,
        predecessor_v4_closure_path=args.predecessor_v4_closure,
        historical_v1_manifest_path=args.historical_v1_manifest,
        metric_contract_path=args.metric_contract, normal_registry_path=args.normal_registry,
        private_normal_manifest_path=args.private_normal_manifest,
        expected_private_normal_hash=args.expected_private_normal_hash,
        # The V5 schedule validates its frozen legacy source commit; the
        # outer V11R1 manifest independently binds the current implementation.
        wrapper=wrapper, source_commit=legacy["source_commit"],
    )
    (args.output / "V11R1_FULL_SYNTHETIC_E2E_RECEIPT.json").write_bytes(canonical_bytes(receipt) + b"\n")
    print(json.dumps({"status": receipt["status"], "manifest": manifest["self_hash"], "receipt": receipt["self_hash"],
                      "planned_cells": receipt["planned_cells"], "heldout_predictions": 0, "heldout_metrics": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
