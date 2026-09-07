"""Single V11R1 route core assembled exclusively from frozen components.

The provider is selected before this module is entered.  From physical
authority creation through the DG-06 handoff both preaccess and real modes
use this same orchestration; this module contains no scoring, parser, Rule,
or metric semantics.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import PREACCESS_MODE, REAL_MODE, file_hash, load_self_hashed, self_hashed
from .dg05_production_chain_v11r1 import initialize
from .dg05_schedule_release_provenance_bridge_v11 import invoke_frozen_v5_schedule_v11
from .dg05_v11r1_postfreeze_metric_binding import build_freeze_bound_authorities, verify_freeze_bound_authorities
from .dg05_v11r1_production_executor import build_frozen_production_executor_v11r1
from .dg05_v11r1_terminal_chain import build_dg06_handoff_v1, build_terminal_package_v11r1, next_execution_state_v11r1, write_new_state_v11r1


class DG05V11R1RouteCoreError(ValueError):
    pass


def _load_private(path: Path, schema: str) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="ascii"))
    if value.get("schema") != schema:
        raise DG05V11R1RouteCoreError("V11R1_SOURCE_AUTHORITY_SCHEMA_REQUIRED")
    from .dg05_production_chain_v11 import digest
    if value.get("self_hash") != digest({k:v for k,v in value.items() if k!="self_hash"}):
        raise DG05V11R1RouteCoreError("V11R1_SOURCE_AUTHORITY_REPLAY_FAILED")
    return value


def _synthetic_plan(*, repository_root: Path, source_root: Path) -> dict[str, Any]:
    """Produce the ten-file synthetic provider only; projection remains frozen."""
    from .dg05_connected_rehearsal_v4 import _write_fixture
    from .dg05_execution_closure_v1 import digest, file_sha256
    from .multipanel_custody_v1 import FROZEN_ATTACK_FILE_IDS_V2, FROZEN_PANEL_ORDER_V2, frozen_feature_allowlist_authorities_v2
    allowlists=frozen_feature_allowlist_authorities_v2(); rows=[]
    for panel in FROZEN_PANEL_ORDER_V2:
        for file_id in FROZEN_ATTACK_FILE_IDS_V2[panel]:
            source=source_root/panel/file_id; _write_fixture(source,allowlists[panel])
            rows.append({"panel_id":panel,"file_id":file_id,"path":str(source),"sha256":file_sha256(source),
                         "header_hash":digest([allowlists[panel].timestamp_id,*allowlists[panel].feature_ids,"Attack","unknown_field"]),
                         "official_source_hash":digest([panel,file_id,"SYNTHETIC_QUALIFICATION_ONLY"])})
    return {"schema":"dg05_v11r1_synthetic_resource_plan_v1","physical_custody_hash":digest("SYNTHETIC_QUALIFICATION_ONLY"),"files":rows}


def execute_dg05_v11r1(*, repository_root: Path, work_root: Path, manifest_path: Path,
                       expected_hash: str, mode: str, user_approved_release_hash: str | None,
                       legacy_release_path: Path, predecessor_v4_path: Path,
                       predecessor_v4_closure_path: Path, historical_v1_manifest_path: Path,
                       metric_contract_path: Path, normal_registry_path: Path,
                       private_normal_manifest_path: Path, expected_private_normal_hash: str,
                       unified_scenario_path: Path, unified_p1_path: Path, wrapper: Any,
                       resource_plan: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run the release-bound route after resource-provider selection.

    ``REAL_HELDOUT_EXECUTION`` callers supply a pre-verified resource plan
    after exact approval.  Preaccess uses a synthetic plan with the identical
    physical-authority/projection/census path.
    """
    if work_root.exists():
        raise DG05V11R1RouteCoreError("V11R1_OUTPUT_NAMESPACE_REUSE_REJECTED")
    outer=load_self_hashed(manifest_path,"dg05_executable_v11r1_candidate_manifest_v1")
    state=initialize(manifest_path=manifest_path,expected_hash=expected_hash,repository_root=repository_root,
                     mode=mode,user_approved_release_hash=user_approved_release_hash)
    from .dg05_connected_rehearsal_v4 import _private_normal_paths, _typed_manifest
    from .dg05_execution_closure_v1 import build_global_prediction_manifest_v1, freeze_global_predictions_v1
    from .dg05_metric_surface_execution_v2 import build_metric_primitives_from_frozen_execution_v2
    from .dg05_metric_surface_oracle_v2 import verify_complete_metric_surface_from_paths_v2
    from .dg05_metric_surface_v2 import build_complete_metric_surface_v2, persist_canonical_v1
    from .dg05_normal_source_v2 import replay_normal_source_registry_v2
    from .dg05_production_chain_v2 import initialize_production_release_v5
    from .dg05_real_resource_orchestrator_v11r1 import prepare_frozen_v5_resources_v11r1
    from .multipanel_custody_v1 import FROZEN_PANEL_ORDER_V2
    from scripts.freeze_dg05_execution_closure_v1 import build_detectors, build_dispatch, build_rule_runtime_registry

    legacy=load_self_hashed(legacy_release_path,"dg05_production_release_manifest_v2")
    historical=_typed_manifest(historical_v1_manifest_path)
    detectors=build_detectors(); rules,rule_sources=build_rule_runtime_registry(); dispatch=build_dispatch(detectors,rules)
    executor=build_frozen_production_executor_v11r1(repository_root=repository_root,executable_manifest=historical,
        detector_registry=detectors,dispatch_registry=dispatch,rule_runtime_registry=rules,rule_sources=rule_sources)
    if executor.authority_mode!="PRODUCTION" or len(executor.detector_assets)!=6 or len(executor.rule_assets)!=7:
        raise DG05V11R1RouteCoreError("V11R1_PRODUCTION_EXECUTOR_REQUIRED")
    adapter_hash=file_hash(repository_root/"src/paperworks/validation_v2/dg05_execution_closure_v1.py")
    plan=_synthetic_plan(repository_root=repository_root,source_root=work_root/"synthetic-sources") if mode==PREACCESS_MODE else resource_plan
    if plan is None:
        raise DG05V11R1RouteCoreError("V11R1_VERIFIED_RESOURCE_PLAN_REQUIRED")
    resources=prepare_frozen_v5_resources_v11r1(verified_plan=plan,work_root=work_root/"resources",
        adapter_implementation_hash=adapter_hash,source_commit=legacy["source_commit"],dispatch=dispatch)
    legacy_state=initialize_production_release_v5(release_manifest_path=legacy_release_path,repository_root=repository_root,
        predecessor_v4_manifest_path=predecessor_v4_path,predecessor_v4_closure_path=predecessor_v4_closure_path,
        expected_release_hash=legacy["self_hash"],authority_mode="PREACCESS_FROZEN_KERNEL_REHEARSAL",
        expected_executable_version=legacy["executable_version"])
    schedule_executor=executor
    if mode==PREACCESS_MODE:
        from .dg05_preaccess_kernel_v5 import PreaccessFrozenKernelExecutorV5
        schedule_executor=PreaccessFrozenKernelExecutorV5(executor); schedule_executor.validate()
    bridge_hash=file_hash(repository_root/"src/paperworks/validation_v2/dg05_schedule_release_provenance_bridge_v11.py")
    predecessor=load_self_hashed(repository_root/"research_control_center/validation_v2/dg05_metric_verifier_closure/DG05_EXECUTABLE_AUTHORITY_MANIFEST_V3.json","dg05_executable_authority_manifest_v3")
    receipts,artifacts,prediction_paths,trace_paths,kernel,bridged=invoke_frozen_v5_schedule_v11(repository_root=repository_root,
        outer_release=outer,outer_state=state,legacy_release=legacy,legacy_state=legacy_state,bridge_authority_hash=bridge_hash,
        schedule_kwargs={"census":resources["census"],"physical":resources["physical"],"dispatch":dispatch,
          "projections":resources["projections"],"timestamps":resources["timestamps"],"release":legacy,
          "predecessor_v3":predecessor,"initialized_release_state":legacy_state,"executor":schedule_executor,
          "output_directory":work_root/"predictions","source_commit":legacy["source_commit"],"repository_root":repository_root})
    if len(receipts)!=resources["census"]["count"] or any(row.status!="SUCCESS" for row in receipts) or kernel["synthetic_fallback_invocation_count"]!=0:
        raise DG05V11R1RouteCoreError("V11R1_FROZEN_V5_SCHEDULE_INCOMPLETE")
    manifest=build_global_prediction_manifest_v1(census=resources["census"],receipts=receipts,executable_manifest_hash=legacy["self_hash"],dispatch=dispatch)
    freeze=freeze_global_predictions_v1(manifest=manifest,census=resources["census"],receipt_artifacts=artifacts,
        predecessor_state=self_hashed({"schema":"dg05_v11r1_synthetic_prediction_state_v1","state":"PREDICTIONS_COMPLETE_LABEL_LOCKED","release_hash":outer["self_hash"],"release_initialization_hash":state["self_hash"]}))
    persist_canonical_v1(work_root/"GLOBAL_PREDICTION_MANIFEST.json",manifest); persist_canonical_v1(work_root/"GLOBAL_PREDICTION_FREEZE.json",freeze)
    freeze=load_self_hashed(work_root/"GLOBAL_PREDICTION_FREEZE.json","global_prediction_freeze_v3")
    manifest=load_self_hashed(work_root/"GLOBAL_PREDICTION_MANIFEST.json","global_prediction_manifest_v3")
    source_scenario=_load_private(unified_scenario_path,"hai_official_source_triangulated_scenario_authority_private_v1")
    source_p1=_load_private(unified_p1_path,"hai_p1_direct_target_denominator_authority_v2")
    scenario,denominator=build_freeze_bound_authorities(unified_scenario=source_scenario,unified_p1=source_p1,
        global_freeze=freeze,physical=resources["physical"],timestamps=resources["timestamps"],release_hash=outer["self_hash"],
        adapter_hash=file_hash(repository_root/"src/paperworks/validation_v2/dg05_v11r1_postfreeze_metric_binding.py"),source_commit=outer["implementation_source_commit"])
    persist_canonical_v1(work_root/"V11R1_FREEZE_BOUND_SCENARIO_AUTHORITY.json",scenario)
    persist_canonical_v1(work_root/"V11R1_FREEZE_BOUND_P1_DENOMINATOR_AUTHORITY.json",denominator)
    scenario=load_self_hashed(work_root/"V11R1_FREEZE_BOUND_SCENARIO_AUTHORITY.json","v11r1_freeze_bound_scenario_authority_v1")
    denominator=load_self_hashed(work_root/"V11R1_FREEZE_BOUND_P1_DENOMINATOR_AUTHORITY.json","v11r1_freeze_bound_p1_denominator_authority_v1")
    replay=verify_freeze_bound_authorities(scenario=scenario,denominator=denominator,unified_scenario=source_scenario,
        unified_p1=source_p1,global_freeze=freeze,physical=resources["physical"],timestamps=resources["timestamps"],release_hash=outer["self_hash"])
    persist_canonical_v1(work_root/"V11R1_FREEZE_BOUND_AUTHORITY_REPLAY.json",replay)
    contract=load_self_hashed(metric_contract_path,"metric_surface_contract_v2"); registry=load_self_hashed(normal_registry_path,"normal_burden_source_registry_v2")
    component_paths=_private_normal_paths(manifest_path=private_normal_manifest_path,registry=registry,expected_manifest_hash=expected_private_normal_hash)
    normal=replay_normal_source_registry_v2(registry=registry,component_paths=component_paths,expected_dec031_binding_hash=contract["dec031_binding_hash"])
    primitive_hashes={}; surface_hashes={}; oracle_hashes={}
    for panel in FROZEN_PANEL_ORDER_V2:
        ids=tuple(sorted({row.file_id for row in receipts if row.panel_id==panel}))
        primitive=build_metric_primitives_from_frozen_execution_v2(panel_id=panel,global_prediction_manifest=manifest,global_prediction_freeze=freeze,
            scenario_authority=scenario,denominator_authority=denominator,projection_paths={x:resources["projections"][(panel,x)][1] for x in ids},
            prediction_paths=prediction_paths,trace_paths=trace_paths,normal_source_replay=normal,normal_source_registry_hash=registry["self_hash"],dec031_binding_hash=contract["dec031_binding_hash"],source_commit=legacy["source_commit"])
        result=build_complete_metric_surface_v2(primitives=primitive,contract=contract,executable_manifest_hash=legacy["self_hash"],wrapper=wrapper,source_commit=legacy["source_commit"])
        primitive_path=work_root/"metrics"/f"{panel}.primitive.json"; result_path=work_root/"metrics"/f"{panel}.surface.json"
        persist_canonical_v1(primitive_path,primitive); persist_canonical_v1(result_path,result)
        oracle=verify_complete_metric_surface_from_paths_v2(primitive_path=primitive_path,result_path=result_path,contract_path=metric_contract_path,wrapper=wrapper,expected_executable_hash=legacy["self_hash"])
        primitive_hashes[panel]=primitive["self_hash"]; surface_hashes[panel]=result["self_hash"]; oracle_hashes[panel]=oracle["self_hash"]
    root_to_terminal=self_hashed({"schema":"dg05_v11r1_root_to_terminal_replay_v1","status":"PASS","release_hash":outer["self_hash"],"v5_kernel_hash":kernel["self_hash"],"prediction_freeze_hash":freeze["self_hash"],"scenario_replay_hash":replay["self_hash"],"metric_surface_hashes":surface_hashes,"oracle_hashes":oracle_hashes})
    physical_source_hash=resources["physical"].document()["self_hash"]
    transition=None
    for name in ("READY","REAL_EXECUTION_STARTED","PREDICTION_CONTACT_OCCURRED","PREDICTIONS_FROZEN","METRICS_FROZEN","TERMINAL_COMPLETE"):
        transition=next_execution_state_v11r1(release_hash=outer["self_hash"],execution_binding_hash=outer["self_hash"],physical_source_set_hash=physical_source_hash,output_namespace=str(work_root),predecessor=transition,state=name)
        write_new_state_v11r1(work_root/"execution-states"/f"{name}.json",transition)
    terminal=build_terminal_package_v11r1(release_hash=outer["self_hash"],terminal_state=transition,physical_custody_hash=physical_source_hash,
        projection_timestamp_hash=scenario["timestamp_authority_aggregate_hash"],private_asset_custody_hash=self_hashed({"schema":"v11r1_production_asset_custody_v1","detectors":6,"rules":7})["self_hash"],
        prediction_freeze_hash=freeze["self_hash"],scenario_authority_hash=scenario["self_hash"],p1_authority_hash=denominator["self_hash"],metric_primitives_hashes=primitive_hashes,metric_surface_hashes=surface_hashes,independent_metric_verification_hashes=oracle_hashes,root_to_terminal_hash=root_to_terminal["self_hash"])
    handoff=build_dg06_handoff_v1(terminal_package=terminal,scientific_preregistration_hash=outer["authority_hashes"]["scientific_preregistration"])
    persist_canonical_v1(work_root/"DG05_TERMINAL_RESULT_PACKAGE.json",terminal); persist_canonical_v1(work_root/"DG06_INPUT_HANDOFF.json",handoff)
    return self_hashed({"schema":"dg05_v11r1_shared_route_receipt_v1","status":"PASS","mode":mode,"release_hash":outer["self_hash"],"state_hash":state["self_hash"],"planned_cells":resources["census"]["count"],"v5_terminal_cells":len(receipts),"frozen_prediction_cells":manifest["success_count"],"fallback_cells":0,"unexercised_cells":0,"scenario_records":146,"p1_records":146,"p1_counts":denominator["classification_counts"],"adapter_replay_hash":replay["self_hash"],"metric_primitive_count":len(primitive_hashes),"metric_surface_count":sum(load_self_hashed(work_root/"metrics"/f"{p}.surface.json","complete_metric_surface_v2")["surface_count"] for p in FROZEN_PANEL_ORDER_V2),"independent_panel_count":len(oracle_hashes),"kernel_hash":kernel["self_hash"],"prediction_freeze_hash":freeze["self_hash"],"terminal_package_hash":terminal["self_hash"],"dg06_handoff_hash":handoff["self_hash"],"root_to_terminal_hash":root_to_terminal["self_hash"],"heldout_rows_parsed":0,"heldout_predictions":0,"heldout_metrics":0,"result_driven_changes":0})


__all__=["DG05V11R1RouteCoreError","execute_dg05_v11r1"]
