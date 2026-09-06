"""Clean-process V11 release-root rehearsal entrypoint; it never loads held-out rows."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path[:0] = [str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"), str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies")]
from paperworks.validation_v2.dg05_production_chain_v11 import PREACCESS_MODE
from paperworks.validation_v2.dg05_v11_root_verifier_v1 import verify_v11_roots
from paperworks.validation_v2.dg05_production_chain_v11 import load_self_hashed
from paperworks.validation_v2.dg05_production_route_v11 import initialize_prediction_schedule_v11
from paperworks.validation_v2.dg05_v11_bridged_rehearsal_v1 import run_v11_bridged_rehearsal
from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes, self_hashed
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--scenario", required=True, type=Path)
    parser.add_argument("--p1", required=True, type=Path)
    parser.add_argument("--expected-hash", required=True)
    parser.add_argument("--legacy-v10-release", type=Path)
    parser.add_argument("--predecessor-v4-manifest", type=Path)
    parser.add_argument("--predecessor-v4-closure", type=Path)
    parser.add_argument("--historical-v1-manifest", type=Path)
    parser.add_argument("--metric-contract", type=Path)
    parser.add_argument("--normal-registry", type=Path)
    parser.add_argument("--private-normal-manifest", type=Path)
    parser.add_argument("--expected-private-normal-hash")
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--work-root", type=Path)
    args = parser.parse_args()
    receipt = verify_v11_roots(repository_root=ROOT, manifest_path=args.manifest,
                               scenario_path=args.scenario, p1_path=args.p1,
                               expected_hash=args.expected_hash)
    scenario = load_self_hashed(args.scenario, "hai_official_source_triangulated_scenario_authority_private_v1")
    p1 = load_self_hashed(args.p1, "hai_p1_direct_target_denominator_authority_v2")
    route = initialize_prediction_schedule_v11(
        unified_scenario=scenario, unified_p1=p1,
        state={"state": "GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED"}, repository_root=ROOT)
    required=(args.legacy_v10_release,args.predecessor_v4_manifest,args.predecessor_v4_closure,args.historical_v1_manifest,args.metric_contract,args.normal_registry,args.private_normal_manifest,args.expected_private_normal_hash,args.output_directory,args.work_root)
    if any(v is None for v in required):
        raise RuntimeError("FRESH_PROCESS_V11_BRIDGE_INPUT_REQUIRED")
    args.output_directory.mkdir(parents=True, exist_ok=False)
    legacy=json.loads(args.legacy_v10_release.read_text(encoding="ascii"))
    etapr=OfficialEtaprV1(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677")
    bridge,schedule,result=run_v11_bridged_rehearsal(repository_root=ROOT,work_root=args.work_root,outer_manifest_path=args.manifest,expected_outer_hash=args.expected_hash,legacy_release_path=args.legacy_v10_release,predecessor_v4_path=args.predecessor_v4_manifest,predecessor_v4_closure_path=args.predecessor_v4_closure,historical_v1_manifest_path=args.historical_v1_manifest,metric_contract_path=args.metric_contract,normal_registry_path=args.normal_registry,private_normal_manifest_path=args.private_normal_manifest,expected_private_manifest_hash=args.expected_private_normal_hash,wrapper=etapr,source_commit=legacy["source_commit"])
    for name,value in (("V11_BRIDGED_REHEARSAL_RECEIPT.json",bridge),("V11_SCHEDULE_ENVELOPE.json",schedule),("V11_STRUCTURAL_RESULT_CONTAINER.json",result)):
        (args.output_directory/name).write_bytes(canonical_bytes(value)+b"\n")
    safe = self_hashed({"schema": "dg05_v11_fresh_process_launcher_receipt_v2", "status": "PASS",
            "parent_pid": os.getppid(), "custodian_pid": os.getpid(),
            "pid_distinct": os.getppid() != os.getpid(), "python": sys.version.split()[0],
            "mode": PREACCESS_MODE, "root_replay_hash": receipt["self_hash"],
            "route_initialization_hash": __import__("hashlib").sha256(
                json.dumps(route, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest(),
            "resolved_kernel": route["resolved_kernel"], "custodian_prediction_capability": False,
            "heldout_prediction_cells": 0, "metric_cells": 0,
            "inherited_authority_objects": False,"bridge_authority_hash":bridge["bridge_authority_hash"],"planned_cells":bridge["planned_cells"],"actual_v5_cells":bridge["actual_v5_schedule_cells"],"v11_envelope_cells":bridge["v11_bridged_cells"],"schedule_envelope_hash":schedule["self_hash"],"result_container_hash":result["self_hash"]})
    (args.output_directory/"V11_FRESH_PROCESS_QUALIFICATION_RECEIPT.json").write_bytes(canonical_bytes(safe)+b"\n")
    print(json.dumps(safe, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
