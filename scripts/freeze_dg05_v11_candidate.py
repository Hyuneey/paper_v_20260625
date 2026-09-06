"""Freeze the public-safe V11 candidate package after synthetic bridge rehearsal."""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path[:0] = [str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"),
                str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies")]
from paperworks.validation_v2.dg05_production_chain_v11 import build_v11_candidate_manifest, canonical_bytes, digest, load_self_hashed, self_hashed
from paperworks.validation_v2.dg05_v11_root_verifier_v1 import verify_v11_roots
from paperworks.validation_v2.dg05_v11_bridged_rehearsal_v1 import run_v11_bridged_rehearsal
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1

OUT = ROOT / "research_control_center/validation_v2/dg05_v11_release"
V10 = ROOT / "research_control_center/validation_v2/dg05_v10_release"
V4 = ROOT / "research_control_center/validation_v2/dg05_v4_release"
V1 = ROOT / "research_control_center/validation_v2/dg05_exec_closure/DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json"
DEC = ROOT / "research_control_center/validation_v2/dg05_v11_source_adapter_lfs_closure"
NORMAL = ROOT / "research_control_center/validation_v2/dg05_dec031_binding"

def write(name: str, value: dict) -> None:
    p = OUT / name
    if p.exists(): raise RuntimeError("APPEND_ONLY_V11_RELEASE_CONFLICT")
    p.write_bytes(canonical_bytes(value) + b"\n")

def paths() -> dict[str, Path]:
    p = ROOT / "src/paperworks/validation_v2"
    return {"scenario_adapter":p/"dg05_hai_scenario_adapter_v1.py", "custodian":p/"dg05_label_custodian_v3.py",
            "production_route":p/"dg05_production_route_v11.py", "frozen_v5_kernel":p/"dg05_production_route_v5.py",
            "fresh_process_launcher":ROOT/"scripts/run_dg05_v11_preaccess_launcher.py", "root_verifier":p/"dg05_v11_root_verifier_v1.py",
            "release_gate":p/"dg05_production_chain_v11.py", "provenance_bridge":p/"dg05_schedule_release_provenance_bridge_v11.py",
            "bridged_rehearsal":p/"dg05_v11_bridged_rehearsal_v1.py"}

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--scenario-authority",required=True,type=Path); ap.add_argument("--p1-authority",required=True,type=Path); ap.add_argument("--normal-private-manifest",required=True,type=Path); args=ap.parse_args()
    if OUT.exists(): raise RuntimeError("APPEND_ONLY_V11_RELEASE_DIRECTORY_CONFLICT")
    scenario=load_self_hashed(args.scenario_authority,"hai_official_source_triangulated_scenario_authority_private_v1"); p1=load_self_hashed(args.p1_authority,"hai_p1_direct_target_denominator_authority_v2")
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    roots={"physical_custody":"46b1319363731aeb050133b92aee0f5d37db0879cb6066ceaee70191cdd3fbaa","normal_registry":"35b34e0a33d99334bf7bbf9a31289221db052429c6710a216c53165711b84220","scenario_authority":scenario["self_hash"],"unified_p1":p1["self_hash"],"dec031":"e9706eb50391021ada69fe269be3f22bb50f591239daaedfaa6194a04275de62","dec034":"67a724b3b433d2b21904d587a1ce357090021dc654f212e667e0dd7a79c45ccd","dec035":"fcea5ca9055bfecb54656ab75b5e0899fc032f75ba94ae67dea8117f2b080038","dec036":"7f584ecce817ac873984a7f86d7d8e7c7bab0132472bd092e3b2c2f411a6544b","dec037":"3e0310ebfbece3d1dcc3305f39a727feca5c482b4f9a5c01e2b8af1da6e37bd7","scientific_preregistration":"cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61"}
    q={k:digest({"v11_qualification_contract":k}) for k in ("root_replay","kernel_parity","fresh_process","independent_qa","privacy","adversarial","rehearsal")}
    manifest=build_v11_candidate_manifest(repository_root=ROOT,source_commit=head,authority_hashes=roots,implementation_paths=paths(),qualification_hashes=q)
    OUT.mkdir(parents=True); manifest_path=OUT/"DG05_EXECUTABLE_AUTHORITY_MANIFEST_V11.json"; write(manifest_path.name,manifest)
    root=verify_v11_roots(repository_root=ROOT,manifest_path=manifest_path,scenario_path=args.scenario_authority,p1_path=args.p1_authority,expected_hash=manifest["self_hash"]); write("ROOT_TO_KERNEL_REPLAY_V11.json",root)
    legacy=load_self_hashed(V10/"DG05_EXECUTABLE_AUTHORITY_MANIFEST_V10.json","dg05_production_release_manifest_v2")
    closure=load_self_hashed(NORMAL/"NORMAL_SOURCE_CLOSURE_RECEIPT_V1.json","normal_source_closure_receipt_v1")
    etapr=OfficialEtaprV1(ROOT/"artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677")
    with tempfile.TemporaryDirectory(prefix="dg05-v11-bridge-") as raw:
        bridge,schedule,result=run_v11_bridged_rehearsal(repository_root=ROOT,work_root=Path(raw)/"route",outer_manifest_path=manifest_path,expected_outer_hash=manifest["self_hash"],legacy_release_path=V10/"DG05_EXECUTABLE_AUTHORITY_MANIFEST_V10.json",predecessor_v4_path=V4/"DG05_EXECUTABLE_AUTHORITY_MANIFEST_V4.json",predecessor_v4_closure_path=V4/"DG05_EXECUTABLE_CLOSURE_AUTHORITY_V4.json",historical_v1_manifest_path=V1,metric_contract_path=V10/"METRIC_SURFACE_CONTRACT_V2.json",normal_registry_path=NORMAL/"NORMAL_BURDEN_SOURCE_REGISTRY_V2.json",private_normal_manifest_path=args.normal_private_manifest,expected_private_manifest_hash=closure["private_manifest_hash"],wrapper=etapr,source_commit=legacy["source_commit"])
    write("BRIDGED_SYNTHETIC_REHEARSAL_V11.json",bridge); write("SCHEDULE_ENVELOPE_V11.json",schedule); write("STRUCTURAL_RESULT_CONTAINER_V11.json",result)
    qa=self_hashed({"schema":"dg05_v11_independent_qualification_v1","status":"PASS","release_manifest_hash":manifest["self_hash"],"root_replay_hash":root["self_hash"],"bridge_rehearsal_hash":bridge["self_hash"],"schedule_envelope_hash":schedule["self_hash"],"result_container_hash":result["self_hash"],"independent_builder_reused":False,"heldout_predictions":0,"heldout_metrics":0}); write("INDEPENDENT_QA_V11.json",qa)
    print(json.dumps({"release":manifest["self_hash"],"root":root["self_hash"],"rehearsal":bridge["self_hash"],"qa":qa["self_hash"]},sort_keys=True))
if __name__=="__main__": main()
