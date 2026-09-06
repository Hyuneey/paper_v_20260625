"""The single V11R1 release-bound preaccess/real entrypoint."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"src")]
from paperworks.validation_v2.dg05_production_chain_v11 import PREACCESS_MODE, REAL_MODE, canonical_bytes
from paperworks.validation_v2.dg05_production_chain_v11r1 import initialize
from paperworks.validation_v2.dg05_v11r1_resource_loader import verify_plan


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=(PREACCESS_MODE,REAL_MODE)); p.add_argument("--manifest",type=Path,required=True); p.add_argument("--expected-hash",required=True); p.add_argument("--user-approved-release-hash"); p.add_argument("--physical-custody-receipt",type=Path,required=True); p.add_argument("--resource-plan",type=Path); p.add_argument("--preflight-only",action="store_true"); p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(); state=initialize(manifest_path=a.manifest,expected_hash=a.expected_hash,repository_root=ROOT,mode=a.mode,user_approved_release_hash=a.user_approved_release_hash)
    if a.mode==REAL_MODE:
        if a.resource_plan is None: raise RuntimeError("V11R1_PROTECTED_RESOURCE_PLAN_REQUIRED")
        preflight=verify_plan(plan_path=a.resource_plan,custody_receipt_path=a.physical_custody_receipt)
        if not a.preflight_only: raise RuntimeError("V11R1_REAL_SCHEDULE_REQUIRES_FROZEN_RESOURCE_ORCHESTRATOR")
    else:
        preflight={"status":"SYNTHETIC_PREACCESS_RESOURCE_MIRROR_ONLY","feature_rows_opened":0}
    if a.output.exists(): raise RuntimeError("V11R1_OUTPUT_NAMESPACE_REUSE_REJECTED")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(canonical_bytes({"schema":"dg05_v11r1_entrypoint_receipt_v1","status":"PASS","state_hash":state["self_hash"],"mode":a.mode,"resource_preflight":preflight,"heldout_predictions":0,"heldout_metrics":0})+b"\n")
    print(json.dumps({"status":"PASS","mode":a.mode,"heldout_predictions":0,"heldout_metrics":0},sort_keys=True))
if __name__=="__main__": main()
