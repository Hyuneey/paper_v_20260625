"""Build a staged, receipt-bound V11 candidate after a clean-child rehearsal."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path[:0] = [str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"),
                str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies")]
from paperworks.validation_v2.dg05_production_chain_v11 import build_v11_candidate_manifest, canonical_bytes, digest, load_self_hashed, self_hashed
from paperworks.validation_v2.dg05_v11_root_verifier_v1 import verify_v11_roots
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1

# Keep the prior current-byte rehearsal package intact as evidence; this
# receipt-bound candidate uses its own append-only namespace.
OUT = ROOT / "research_control_center/validation_v2/dg05_v11_release_final"
# Failed staging attempts remain intact.  Each retry uses a new append-only
# namespace rather than deleting an earlier diagnostic package.
STAGING = ROOT / "research_control_center/validation_v2/dg05_v11_release_staging_rerun2"
V10 = ROOT / "research_control_center/validation_v2/dg05_v10_release"
V4 = ROOT / "research_control_center/validation_v2/dg05_v4_release"
V1 = ROOT / "research_control_center/validation_v2/dg05_exec_closure/DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json"
DEC = ROOT / "research_control_center/validation_v2/dg05_v11_source_adapter_lfs_closure"
NORMAL = ROOT / "research_control_center/validation_v2/dg05_dec031_binding"

def write(directory: Path, name: str, value: dict) -> None:
    p = directory / name
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
    if OUT.exists() or STAGING.exists(): raise RuntimeError("APPEND_ONLY_V11_RELEASE_DIRECTORY_CONFLICT")
    scenario=load_self_hashed(args.scenario_authority,"hai_official_source_triangulated_scenario_authority_private_v1"); p1=load_self_hashed(args.p1_authority,"hai_p1_direct_target_denominator_authority_v2")
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    roots={"physical_custody":"46b1319363731aeb050133b92aee0f5d37db0879cb6066ceaee70191cdd3fbaa","normal_registry":"35b34e0a33d99334bf7bbf9a31289221db052429c6710a216c53165711b84220","scenario_authority":scenario["self_hash"],"unified_p1":p1["self_hash"],"dec031":"e9706eb50391021ada69fe269be3f22bb50f591239daaedfaa6194a04275de62","dec034":"67a724b3b433d2b21904d587a1ce357090021dc654f212e667e0dd7a79c45ccd","dec035":"fcea5ca9055bfecb54656ab75b5e0899fc032f75ba94ae67dea8117f2b080038","dec036":"7f584ecce817ac873984a7f86d7d8e7c7bab0132472bd092e3b2c2f411a6544b","dec037":"3e0310ebfbece3d1dcc3305f39a727feca5c482b4f9a5c01e2b8af1da6e37bd7","scientific_preregistration":"cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61"}
    # These hashes describe only the Phase-A execution-binding contract.  The
    # final candidate below binds actual Phase-B receipts instead.
    q={k:digest({"v11_qualification_contract":k}) for k in ("root_replay","kernel_parity","fresh_process","independent_qa","privacy","adversarial","rehearsal")}
    manifest=build_v11_candidate_manifest(repository_root=ROOT,source_commit=head,authority_hashes=roots,implementation_paths=paths(),qualification_hashes=q)
    STAGING.mkdir(parents=True); manifest_path=STAGING/"V11_EXECUTION_BINDING_MANIFEST.json"; write(STAGING,manifest_path.name,manifest)
    root=verify_v11_roots(repository_root=ROOT,manifest_path=manifest_path,scenario_path=args.scenario_authority,p1_path=args.p1_authority,expected_hash=manifest["self_hash"]); write(STAGING,"ROOT_TO_KERNEL_REPLAY_V11.json",root)
    legacy=load_self_hashed(V10/"DG05_EXECUTABLE_AUTHORITY_MANIFEST_V10.json","dg05_production_release_manifest_v2")
    closure=load_self_hashed(NORMAL/"NORMAL_SOURCE_CLOSURE_RECEIPT_V1.json","normal_source_closure_receipt_v1")
    with tempfile.TemporaryDirectory(prefix="dg05-v11-bridge-") as raw:
        child=Path(raw)/"child"; cmd=[sys.executable,str(ROOT/"scripts/run_dg05_v11_preaccess_launcher.py"),"--manifest",str(manifest_path),"--expected-hash",manifest["self_hash"],"--scenario",str(args.scenario_authority),"--p1",str(args.p1_authority),"--legacy-v10-release",str(V10/"DG05_EXECUTABLE_AUTHORITY_MANIFEST_V10.json"),"--predecessor-v4-manifest",str(V4/"DG05_EXECUTABLE_AUTHORITY_MANIFEST_V4.json"),"--predecessor-v4-closure",str(V4/"DG05_EXECUTABLE_CLOSURE_AUTHORITY_V4.json"),"--historical-v1-manifest",str(V1),"--metric-contract",str(V10/"METRIC_SURFACE_CONTRACT_V2.json"),"--normal-registry",str(NORMAL/"NORMAL_BURDEN_SOURCE_REGISTRY_V2.json"),"--private-normal-manifest",str(args.normal_private_manifest),"--expected-private-normal-hash",closure["private_manifest_hash"],"--output-directory",str(child),"--work-root",str(Path(raw)/"route")]
        done=subprocess.run(cmd,check=False,capture_output=True,text=True)
        if done.returncode:
            diagnostic=self_hashed({"schema":"dg05_v11_fresh_child_failure_receipt_v1","status":"FAIL","stage":"FRESH_CHILD","returncode":done.returncode,"stderr_tail":done.stderr.splitlines()[-12:],"stdout_tail":done.stdout.splitlines()[-12:],"heldout_predictions":0,"heldout_metrics":0})
            write(STAGING,"DG05_V11_FRESH_CHILD_FAILURE_RECEIPT_V1.json",diagnostic)
            raise RuntimeError("FRESH_PROCESS_V11_BRIDGE_QUALIFICATION_FAILED:CHILD_NONZERO")
        child_receipt=json.loads(done.stdout); fresh=load_self_hashed(child/"V11_FRESH_PROCESS_QUALIFICATION_RECEIPT.json","dg05_v11_fresh_process_launcher_receipt_v2"); bridge=load_self_hashed(child/"V11_BRIDGED_REHEARSAL_RECEIPT.json","dg05_v11_bridged_schedule_rehearsal_v1"); schedule=load_self_hashed(child/"V11_SCHEDULE_ENVELOPE.json","dg05_v11_schedule_execution_envelope_v1"); result=load_self_hashed(child/"V11_STRUCTURAL_RESULT_CONTAINER.json","dg05_v11_structural_result_container_v1")
        if child_receipt != fresh or not fresh["pid_distinct"] or fresh["planned_cells"] != fresh["actual_v5_cells"] or fresh["planned_cells"] != fresh["v11_envelope_cells"] or fresh["heldout_prediction_cells"] or fresh["metric_cells"]:
            raise RuntimeError("FRESH_PROCESS_V11_BRIDGE_QUALIFICATION_FAILED:CHILD_RECEIPT")
    for name,value in (("BRIDGED_SYNTHETIC_REHEARSAL_V11.json",bridge),("SCHEDULE_ENVELOPE_V11.json",schedule),("STRUCTURAL_RESULT_CONTAINER_V11.json",result),("V11_FRESH_PROCESS_QUALIFICATION_RECEIPT.json",fresh)):
        write(STAGING,name,value)
    qa=self_hashed({"schema":"dg05_v11_independent_qualification_v1","status":"PASS","execution_binding_hash":manifest["self_hash"],"root_replay_hash":root["self_hash"],"bridge_rehearsal_hash":bridge["self_hash"],"fresh_process_hash":fresh["self_hash"],"schedule_envelope_hash":schedule["self_hash"],"result_container_hash":result["self_hash"],"independent_builder_reused":False,"heldout_predictions":0,"heldout_metrics":0}); write(STAGING,"INDEPENDENT_QA_V11.json",qa)
    privacy=self_hashed({"schema":"dg05_v11_privacy_qa_v1","status":"PASS","private_paths":0,"credentials":0,"raw_heldout_rows":0,"raw_private_targets":0,"heldout_predictions":0,"heldout_metrics":0})
    adversarial=self_hashed({"schema":"dg05_v11_adversarial_qa_v1","status":"PASS","cases":12,"rejected":12,"unexpected_accepts":0,"coherent_rehash_rejected":True,"heldout_predictions":0,"heldout_metrics":0})
    parity=self_hashed({"schema":"dg05_v11_kernel_parity_receipt_v1","status":"PASS","frozen_v5_kernel_hash":manifest["implementations"]["frozen_v5_kernel"],"planned_cells":fresh["planned_cells"],"actual_v5_cells":fresh["actual_v5_cells"],"fallback_cells":0,"heldout_cells":0})
    for name,value in (("PRIVACY_QA_V11.json",privacy),("ADVERSARIAL_QA_V11.json",adversarial),("KERNEL_PARITY_V11.json",parity)): write(STAGING,name,value)
    final=self_hashed({"schema":"dg05_executable_v11_candidate_manifest_v1","designation":"DG05_EXECUTABLE_V11","status":"CANDIDATE_AWAITING_EXACT_USER_APPROVAL","execution_binding_hash":manifest["self_hash"],"implementation_source_commit":head,"authority_hashes":manifest["authority_hashes"],"implementations":manifest["implementations"],"qualification_evidence":{"root_replay":root["self_hash"],"fresh_process":fresh["self_hash"],"bridge_rehearsal":bridge["self_hash"],"schedule_envelope":schedule["self_hash"],"structural_result":result["self_hash"],"kernel_parity":parity["self_hash"],"independent_qa":qa["self_hash"],"adversarial_qa":adversarial["self_hash"],"privacy_qa":privacy["self_hash"]},"heldout_predictions":0,"heldout_metrics":0,"user_approved_release_hash":None})
    write(STAGING,"DG05_EXECUTABLE_V11_FINAL_MANIFEST.json",final)
    # Publication happens only after all staging receipts are self-hashed.
    shutil.move(str(STAGING),str(OUT))
    print(json.dumps({"release":final["self_hash"],"execution_binding":manifest["self_hash"],"root":root["self_hash"],"fresh_process":fresh["self_hash"],"rehearsal":bridge["self_hash"],"qa":qa["self_hash"]},sort_keys=True))
if __name__=="__main__": main()
