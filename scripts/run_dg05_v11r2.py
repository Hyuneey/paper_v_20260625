"""Single V11R2 runner with closure, preflight, and durable one-shot guards."""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"), str(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_dependencies")]

from paperworks.validation_v2.dg05_production_chain_v11 import PREACCESS_MODE, REAL_MODE, canonical_bytes, file_hash, load_self_hashed
from paperworks.validation_v2.dg05_production_chain_v11r2 import initialize
from paperworks.validation_v2.dg05_v11r1_resource_loader import verify_plan
from paperworks.validation_v2.dg05_v11r1_resource_materializer import build_materialization_contract_v11r1, materialize_runtime_plan_v11r1
from paperworks.validation_v2.dg05_v11r1_route_core import _load_private, execute_dg05_v11r1
from paperworks.validation_v2.dg05_v11r1_source_file_crosswalk import derive_source_file_identity_crosswalk_v11r1
from paperworks.validation_v2.dg05_v11r2_execution_ledger import append_contact_guard_v11r2, append_terminal_state_v11r2, start_real_execution_v11r2
from paperworks.validation_v2.dg05_v11r2_runtime_approval_guard import build_real_preflight_receipt_v11r2, verify_real_preflight_receipt_v11r2, verify_runtime_approval_v11r2
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1

PREFLIGHT = "REAL_PREFLIGHT_ONLY"


def _args() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=(PREACCESS_MODE, REAL_MODE, PREFLIGHT))
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--expected-hash", required=True)
    p.add_argument("--final-closure", type=Path); p.add_argument("--user-approved-release-hash"); p.add_argument("--user-approved-final-closure-hash"); p.add_argument("--user-approved-execution-binding-hash")
    p.add_argument("--preflight-receipt", type=Path); p.add_argument("--execution-ledger-root", type=Path)
    p.add_argument("--physical-custody-receipt", type=Path); p.add_argument("--resource-plan", type=Path); p.add_argument("--resource-root", type=Path, action="append", default=[])
    p.add_argument("--scenario-authority", type=Path, required=True); p.add_argument("--p1-authority", type=Path, required=True)
    p.add_argument("--legacy-v10-release", type=Path, required=True); p.add_argument("--predecessor-v4-manifest", type=Path, required=True); p.add_argument("--predecessor-v4-closure", type=Path, required=True); p.add_argument("--historical-v1-manifest", type=Path, required=True); p.add_argument("--metric-contract", type=Path, required=True); p.add_argument("--normal-registry", type=Path, required=True); p.add_argument("--private-normal-manifest", type=Path, required=True); p.add_argument("--expected-private-normal-hash", required=True); p.add_argument("--output-root", type=Path, required=True)
    return p.parse_args()


def _require_real_inputs(a: argparse.Namespace) -> None:
    if any(value is None for value in (a.final_closure, a.user_approved_release_hash, a.user_approved_final_closure_hash, a.user_approved_execution_binding_hash)):
        raise RuntimeError("V11R2_RUNTIME_APPROVAL_CLOSURE_INPUTS_REQUIRED")
    if a.physical_custody_receipt is None or (a.resource_plan is None and not a.resource_root):
        raise RuntimeError("V11R2_RUNTIME_RESOURCE_INPUTS_REQUIRED")


def _plan(a: argparse.Namespace, manifest: dict[str, object]) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    if a.resource_plan:
        plan=load_self_hashed(a.resource_plan, "dg05_v11r1_protected_resource_plan_v1")
        contract={"self_hash": manifest.get("resource_materialization_contract_hash", "UNBOUND_PRIVATE_PLAN")}
    else:
        contract=build_materialization_contract_v11r1(custody_receipt_path=a.physical_custody_receipt, implementation_hash=file_hash(ROOT / "src/paperworks/validation_v2/dg05_v11r1_resource_materializer.py"), source_commit=str(manifest["implementation_source_commit"]))
        plan,_=materialize_runtime_plan_v11r1(contract=contract, authorized_roots=a.resource_root)
    return plan, contract, verify_plan(plan_document=plan, custody_receipt_path=a.physical_custody_receipt)


class _RealLifecycle:
    def __init__(self, *, ledger_root: Path, approval: dict[str, object], preflight: dict[str, object], output_root: Path, physical_custody_hash: str):
        self.ledger_root=ledger_root; self.approval=approval; self.preflight=preflight; self.output_root=output_root; self.physical=physical_custody_hash
        self.current=start_real_execution_v11r2(ledger_root=ledger_root, release_hash=str(approval["release_hash"]), final_closure_hash=str(approval["final_closure_hash"]), execution_binding_hash=str(approval["execution_binding_hash"]), preflight_receipt_hash=str(preflight["self_hash"]), physical_custody_hash=physical_custody_hash, output_namespace=str(output_root))
    def commit_contact_guard(self): self.current=append_contact_guard_v11r2(ledger_root=self.ledger_root,start_state=self.current)
    def mark_predictions_frozen(self): self.current=append_terminal_state_v11r2(ledger_root=self.ledger_root,predecessor=self.current,state_name="PREDICTIONS_FROZEN")
    def mark_metrics_frozen(self): self.current=append_terminal_state_v11r2(ledger_root=self.ledger_root,predecessor=self.current,state_name="METRICS_FROZEN")
    def mark_terminal_complete(self): self.current=append_terminal_state_v11r2(ledger_root=self.ledger_root,predecessor=self.current,state_name="TERMINAL_COMPLETE"); return self.current
    def fail(self):
        try: self.current=append_terminal_state_v11r2(ledger_root=self.ledger_root,predecessor=self.current,state_name="TERMINAL_FAILED_AFTER_SCIENTIFIC_CONTACT" if self.current["state"] != "REAL_EXECUTION_STARTED" else "PRECONTACT_ABORTED")
        except Exception: pass


def main() -> None:
    a=_args()
    if a.mode == PREACCESS_MODE:
        wrapper=OfficialEtaprV1(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677")
        receipt=execute_dg05_v11r1(repository_root=ROOT,work_root=a.output_root,manifest_path=a.manifest,expected_hash=a.expected_hash,mode=a.mode,user_approved_release_hash=None,legacy_release_path=a.legacy_v10_release,predecessor_v4_path=a.predecessor_v4_manifest,predecessor_v4_closure_path=a.predecessor_v4_closure,historical_v1_manifest_path=a.historical_v1_manifest,metric_contract_path=a.metric_contract,normal_registry_path=a.normal_registry,private_normal_manifest_path=a.private_normal_manifest,expected_private_normal_hash=a.expected_private_normal_hash,unified_scenario_path=a.scenario_authority,unified_p1_path=a.p1_authority,wrapper=wrapper,manifest_schema="dg05_executable_v11r2_candidate_manifest_v1",initialize_fn=initialize)
        (a.output_root / "V11R2_SHARED_ROUTE_RECEIPT.json").write_bytes(canonical_bytes(receipt)+b"\n"); print(json.dumps({"status":"PASS","heldout_rows_parsed":0},sort_keys=True)); return
    _require_real_inputs(a)
    manifest=load_self_hashed(a.manifest,"dg05_executable_v11r2_candidate_manifest_v1")
    approval=verify_runtime_approval_v11r2(manifest=manifest,final_closure_path=a.final_closure,approved_release_hash=a.user_approved_release_hash,approved_final_closure_hash=a.user_approved_final_closure_hash,approved_execution_binding_hash=a.user_approved_execution_binding_hash)
    plan,contract,resource_preflight=_plan(a,manifest)
    scenario=_load_private(a.scenario_authority,"hai_official_source_triangulated_scenario_authority_private_v1"); p1=_load_private(a.p1_authority,"hai_p1_direct_target_denominator_authority_v2")
    crosswalk=derive_source_file_identity_crosswalk_v11r1(unified_scenario=scenario,physical_custody_hash=manifest["physical_custody_hash"],implementation_hash=file_hash(ROOT/"src/paperworks/validation_v2/dg05_v11r1_source_file_crosswalk.py"),source_commit=manifest["implementation_source_commit"])
    source_set=resource_preflight["self_hash"]
    if a.mode == PREFLIGHT:
        if a.preflight_receipt is None or a.preflight_receipt.exists(): raise RuntimeError("V11R2_PREFLIGHT_RECEIPT_APPEND_ONLY_REQUIRED")
        receipt=build_real_preflight_receipt_v11r2(approval_replay=approval,resource_preflight=resource_preflight,materialization_contract_hash=str(contract["self_hash"]),crosswalk_hash=crosswalk["self_hash"],scenario_authority_hash=scenario["self_hash"],p1_authority_hash=p1["self_hash"],physical_source_set_hash=source_set)
        a.preflight_receipt.parent.mkdir(parents=True,exist_ok=True); a.preflight_receipt.write_bytes(canonical_bytes(receipt)+b"\n"); print(json.dumps({"status":receipt["status"],"heldout_rows_parsed":0},sort_keys=True)); return
    if a.preflight_receipt is None or a.execution_ledger_root is None: raise RuntimeError("V11R2_PREFLIGHT_RECEIPT_AND_LEDGER_REQUIRED")
    preflight=verify_real_preflight_receipt_v11r2(receipt_path=a.preflight_receipt,approval_replay=approval,physical_custody_hash=resource_preflight["physical_custody_hash"],materialization_contract_hash=str(contract["self_hash"]),crosswalk_hash=crosswalk["self_hash"],scenario_authority_hash=scenario["self_hash"],p1_authority_hash=p1["self_hash"])
    lifecycle=_RealLifecycle(ledger_root=a.execution_ledger_root,approval=approval,preflight=preflight,output_root=a.output_root,physical_custody_hash=resource_preflight["physical_custody_hash"])
    try:
        wrapper=OfficialEtaprV1(ROOT / "artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677")
        receipt=execute_dg05_v11r1(repository_root=ROOT,work_root=a.output_root,manifest_path=a.manifest,expected_hash=a.expected_hash,mode=REAL_MODE,user_approved_release_hash=a.user_approved_release_hash,legacy_release_path=a.legacy_v10_release,predecessor_v4_path=a.predecessor_v4_manifest,predecessor_v4_closure_path=a.predecessor_v4_closure,historical_v1_manifest_path=a.historical_v1_manifest,metric_contract_path=a.metric_contract,normal_registry_path=a.normal_registry,private_normal_manifest_path=a.private_normal_manifest,expected_private_normal_hash=a.expected_private_normal_hash,unified_scenario_path=a.scenario_authority,unified_p1_path=a.p1_authority,wrapper=wrapper,resource_plan=plan,manifest_schema="dg05_executable_v11r2_candidate_manifest_v1",initialize_fn=initialize,lifecycle=lifecycle)
    except Exception:
        lifecycle.fail(); raise
    (a.output_root / "V11R2_SHARED_ROUTE_RECEIPT.json").write_bytes(canonical_bytes(receipt)+b"\n"); print(json.dumps({"status":receipt["status"]},sort_keys=True))


if __name__ == "__main__": main()
