"""Single release-bound V11R1 entrypoint for preaccess, preflight, and real modes."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"src"),
    str(ROOT/"artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677"),
    str(ROOT/"artifacts/validation_v2/dg04_xver_prep/metric_dependencies")]

from paperworks.validation_v2.dg05_production_chain_v11 import PREACCESS_MODE, REAL_MODE, canonical_bytes, load_self_hashed
from paperworks.validation_v2.dg05_production_chain_v11r1 import initialize
from paperworks.validation_v2.dg05_v11r1_resource_loader import verify_plan
from paperworks.validation_v2.dg05_v11r1_resource_materializer import (
    build_materialization_contract_v11r1, materialize_runtime_plan_v11r1,
)
from paperworks.validation_v2.dg05_v11r1_container_materializer import inspect_container_framing_v11r1
from paperworks.validation_v2.dg05_v11r1_route_core import execute_dg05_v11r1
from paperworks.validation_v2.etapr_exchange_v1 import OfficialEtaprV1

REAL_PREFLIGHT_ONLY="REAL_PREFLIGHT_ONLY"


def _arguments() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=(PREACCESS_MODE,REAL_MODE,REAL_PREFLIGHT_ONLY))
    p.add_argument("--manifest",type=Path,required=True); p.add_argument("--expected-hash",required=True)
    p.add_argument("--user-approved-release-hash"); p.add_argument("--physical-custody-receipt",type=Path)
    p.add_argument("--resource-plan",type=Path); p.add_argument("--resource-root",type=Path,action="append",default=[])
    p.add_argument("--scenario-authority",type=Path,required=True)
    p.add_argument("--p1-authority",type=Path,required=True); p.add_argument("--legacy-v10-release",type=Path,required=True)
    p.add_argument("--predecessor-v4-manifest",type=Path,required=True); p.add_argument("--predecessor-v4-closure",type=Path,required=True)
    p.add_argument("--historical-v1-manifest",type=Path,required=True); p.add_argument("--metric-contract",type=Path,required=True)
    p.add_argument("--normal-registry",type=Path,required=True); p.add_argument("--private-normal-manifest",type=Path,required=True)
    p.add_argument("--expected-private-normal-hash",required=True); p.add_argument("--output-root",type=Path,required=True)
    return p.parse_args()


def main() -> None:
    a=_arguments()
    def materialized_plan(state: dict[str, object]) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        if a.physical_custody_receipt is None:
            raise RuntimeError("V11R1_PHYSICAL_CUSTODY_RECEIPT_REQUIRED")
        if a.resource_plan is not None:
            plan=load_self_hashed(a.resource_plan,"dg05_v11r1_protected_resource_plan_v1")
            materialization={"schema":"dg05_v11r1_resource_materialization_legacy_plan_receipt_v1","status":"LEGACY_PRIVATE_PLAN_REPLAY"}
        else:
            if not a.resource_root:
                raise RuntimeError("V11R1_AUTHORIZED_RESOURCE_ROOT_REQUIRED")
            materializer=ROOT/"src/paperworks/validation_v2/dg05_v11r1_resource_materializer.py"
            contract=build_materialization_contract_v11r1(custody_receipt_path=a.physical_custody_receipt,
                implementation_hash=__import__("paperworks.validation_v2.dg05_production_chain_v11",fromlist=["file_hash"]).file_hash(materializer),
                source_commit=str(state.get("implementation_source_commit", "RELEASE_BOUND")))
            plan,materialization=materialize_runtime_plan_v11r1(contract=contract,authorized_roots=a.resource_root)
        preflight=verify_plan(plan_document=plan,custody_receipt_path=a.physical_custody_receipt)
        return plan,materialization,preflight
    if a.mode==REAL_PREFLIGHT_ONLY:
        state=initialize(manifest_path=a.manifest,expected_hash=a.expected_hash,repository_root=ROOT,mode=REAL_MODE,
                         user_approved_release_hash=a.user_approved_release_hash)
        plan,materialization,preflight=materialized_plan(state)
        framing=inspect_container_framing_v11r1(plan=plan)
        # Complete every authority replay that is possible without opening a
        # protected CSV row.  Projection and the schedule remain unreachable
        # in this mode.
        from paperworks.validation_v2.dg05_v11r1_route_core import _load_private
        from paperworks.validation_v2.dg05_v11r1_source_file_crosswalk import derive_source_file_identity_crosswalk_v11r1
        from paperworks.validation_v2.dg05_v11r1_production_executor import build_frozen_production_executor_v11r1
        from paperworks.validation_v2.dg05_connected_rehearsal_v4 import _private_normal_paths, _typed_manifest
        from paperworks.validation_v2.dg05_normal_source_v2 import replay_normal_source_registry_v2
        from scripts.freeze_dg05_execution_closure_v1 import build_detectors, build_dispatch, build_rule_runtime_registry
        outer=load_self_hashed(a.manifest,"dg05_executable_v11r1_candidate_manifest_v1")
        scenario=_load_private(a.scenario_authority,"hai_official_source_triangulated_scenario_authority_private_v1")
        p1=_load_private(a.p1_authority,"hai_p1_direct_target_denominator_authority_v2")
        if scenario["self_hash"]!=outer["scenario_authority_hash"] or p1["self_hash"]!=outer["p1_authority_hash"]:
            raise RuntimeError("V11R1_SCENARIO_P1_ROOT_REPLAY_FAILED")
        if len(scenario.get("canonical_records",()))!=146 or len(p1.get("decisions",()))!=146:
            raise RuntimeError("V11R1_SCENARIO_P1_CENSUS_FAILED")
        if any(row.get("eligibility_status")=="UNRESOLVED" for row in p1["decisions"]):
            raise RuntimeError("V11R1_P1_UNRESOLVED_REJECTED")
        crosswalk=derive_source_file_identity_crosswalk_v11r1(unified_scenario=scenario,
            physical_custody_hash=outer["physical_custody_hash"],
            implementation_hash=__import__("paperworks.validation_v2.dg05_production_chain_v11",fromlist=["file_hash"]).file_hash(ROOT/"src/paperworks/validation_v2/dg05_v11r1_source_file_crosswalk.py"),
            source_commit=outer["implementation_source_commit"])
        if crosswalk["entry_count"]!=10:
            raise RuntimeError("V11R1_SOURCE_FILE_CROSSWALK_CENSUS_FAILED")
        historical=_typed_manifest(a.historical_v1_manifest); detectors=build_detectors()
        rules,rule_sources=build_rule_runtime_registry(); dispatch=build_dispatch(detectors,rules)
        executor=build_frozen_production_executor_v11r1(repository_root=ROOT,executable_manifest=historical,
            detector_registry=detectors,dispatch_registry=dispatch,rule_runtime_registry=rules,rule_sources=rule_sources)
        if executor.authority_mode!="PRODUCTION" or len(executor.detector_assets)!=6 or len(executor.rule_assets)!=7:
            raise RuntimeError("V11R1_PRODUCTION_ASSET_PREFLIGHT_FAILED")
        contract=load_self_hashed(a.metric_contract,"metric_surface_contract_v2")
        registry=load_self_hashed(a.normal_registry,"normal_burden_source_registry_v2")
        components=_private_normal_paths(manifest_path=a.private_normal_manifest,registry=registry,
            expected_manifest_hash=a.expected_private_normal_hash)
        replay_normal_source_registry_v2(registry=registry,component_paths=components,
            expected_dec031_binding_hash=contract["dec031_binding_hash"])
        if a.output_root.exists(): raise RuntimeError("V11R1_OUTPUT_NAMESPACE_REUSE_REJECTED")
        a.output_root.parent.mkdir(parents=True,exist_ok=True)
        receipt={"schema":"dg05_v11r1_real_preflight_receipt_v1","status":"REAL_PREFLIGHT_PASS_NO_FEATURE_ACCESS",
                 "release_hash":state["release_hash"],"state_hash":state["self_hash"],"resource_preflight_hash":preflight["self_hash"],
                 "resource_materialization_hash":materialization.get("self_hash"),"container_framing_hash":framing["self_hash"],
                 "production_assets":{"detectors":6,"rules":7},"scenario_records":146,"p1_decisions":146,
                 "p1_unresolved":0,"crosswalk_entries":10,
                 "heldout_rows_parsed":0,"heldout_predictions":0,"heldout_metrics":0}
        a.output_root.write_bytes(canonical_bytes(receipt)+b"\n")
        print(json.dumps({"status":receipt["status"],"heldout_rows_parsed":0},sort_keys=True)); return
    plan=None
    if a.mode==REAL_MODE:
        pre_state=initialize(manifest_path=a.manifest,expected_hash=a.expected_hash,repository_root=ROOT,mode=REAL_MODE,
                             user_approved_release_hash=a.user_approved_release_hash)
        plan,_,_=materialized_plan(pre_state)
    wrapper=OfficialEtaprV1(ROOT/"artifacts/validation_v2/dg04_xver_prep/metric_source/af9e7aed35cfd160cbe0d04c8ec4c102502cb677")
    receipt=execute_dg05_v11r1(repository_root=ROOT,work_root=a.output_root,manifest_path=a.manifest,expected_hash=a.expected_hash,
        mode=a.mode,user_approved_release_hash=a.user_approved_release_hash,legacy_release_path=a.legacy_v10_release,
        predecessor_v4_path=a.predecessor_v4_manifest,predecessor_v4_closure_path=a.predecessor_v4_closure,
        historical_v1_manifest_path=a.historical_v1_manifest,metric_contract_path=a.metric_contract,normal_registry_path=a.normal_registry,
        private_normal_manifest_path=a.private_normal_manifest,expected_private_normal_hash=a.expected_private_normal_hash,
        unified_scenario_path=a.scenario_authority,unified_p1_path=a.p1_authority,wrapper=wrapper,resource_plan=plan)
    (a.output_root/"V11R1_SHARED_ROUTE_RECEIPT.json").write_bytes(canonical_bytes(receipt)+b"\n")
    print(json.dumps({"status":receipt["status"],"planned_cells":receipt["planned_cells"],"heldout_predictions":0,"heldout_metrics":0},sort_keys=True))


if __name__=="__main__": main()
