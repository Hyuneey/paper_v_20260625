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

from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes, load_self_hashed
from paperworks.validation_v2.dg05_production_chain_v11r1 import build_manifest


def _paths() -> dict[str, Path]:
    p = ROOT / "src/paperworks/validation_v2"
    return {
        "successor_gate": p / "dg05_production_chain_v11r1.py",
        "unified_runner": ROOT / "scripts/run_dg05_v11r1.py",
        "resource_loader": p / "dg05_v11r1_resource_loader.py",
        "resource_materializer": p / "dg05_v11r1_resource_materializer.py",
        "container_materializer": p / "dg05_v11r1_container_materializer.py",
        "resource_orchestrator": p / "dg05_real_resource_orchestrator_v11r1.py",
        "production_executor": p / "dg05_v11r1_production_executor.py",
        "shared_route_core": p / "dg05_v11r1_route_core.py",
        "terminal_chain": p / "dg05_v11r1_terminal_chain.py",
        "v5_compatibility": p / "dg05_v11r1_v5_compatibility.py",
        "source_file_crosswalk": p / "dg05_v11r1_source_file_crosswalk.py",
        "postfreeze_metric_binding": p / "dg05_v11r1_postfreeze_metric_binding.py",
        "v11_bridge": p / "dg05_schedule_release_provenance_bridge_v11.py",
        "metric_primitives": p / "dg05_metric_surface_execution_v2.py",
        "metric_surface": p / "dg05_metric_surface_v2.py",
        "metric_oracle": p / "dg05_metric_surface_oracle_v2.py",
        "v11_route": p / "dg05_production_route_v11.py",
        "v11_custodian": p / "dg05_label_custodian_v3.py",
        "scenario_adapter": p / "dg05_hai_scenario_adapter_v1.py",
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
    ap.add_argument("--scenario-authority", required=True, type=Path)
    ap.add_argument("--p1-authority", required=True, type=Path)
    args = ap.parse_args()
    if args.output.exists():
        raise RuntimeError("V11R1_E2E_OUTPUT_APPEND_ONLY_CONFLICT")
    args.output.mkdir(parents=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = build_manifest(repository_root=ROOT, source_commit=head, implementation_paths=_paths())
    manifest_path = args.output / "V11R1_EXECUTION_BINDING_MANIFEST.json"
    manifest_path.write_bytes(canonical_bytes(manifest) + b"\n")
    command=[sys.executable,str(ROOT/"scripts/run_dg05_v11r1.py"),"--mode","PREACCESS_SYNTHETIC_QUALIFICATION",
        "--manifest",str(manifest_path),"--expected-hash",manifest["self_hash"],"--scenario-authority",str(args.scenario_authority),
        "--p1-authority",str(args.p1_authority),"--legacy-v10-release",str(args.legacy_release),
        "--predecessor-v4-manifest",str(args.predecessor_v4_manifest),"--predecessor-v4-closure",str(args.predecessor_v4_closure),
        "--historical-v1-manifest",str(args.historical_v1_manifest),"--metric-contract",str(args.metric_contract),
        "--normal-registry",str(args.normal_registry),"--private-normal-manifest",str(args.private_normal_manifest),
        "--expected-private-normal-hash",args.expected_private_normal_hash,"--output-root",str(args.output/"unified-cli-route")]
    completed=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,check=False)
    if completed.returncode != 0:
        raise RuntimeError("V11R1_UNIFIED_CLI_E2E_FAILED:"+completed.stderr[-1000:])
    receipt_path=args.output/"unified-cli-route"/"V11R1_SHARED_ROUTE_RECEIPT.json"
    receipt=load_self_hashed(receipt_path,"dg05_v11r1_shared_route_receipt_v1")
    if not (args.output/"unified-cli-route"/"DG06_INPUT_HANDOFF.json").is_file(): raise RuntimeError("V11R1_UNIFIED_CLI_E2E_ARTIFACT_MISSING")
    print(json.dumps({"status":"PASS","manifest":manifest["self_hash"],"receipt":receipt["self_hash"],"cli_stdout":completed.stdout.strip(),
                      "heldout_predictions":0,"heldout_metrics":0},sort_keys=True))


if __name__ == "__main__":
    main()
