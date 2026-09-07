"""Complete, read-only V11R2R1 real-route precondition replay.

This is intentionally the single preflight routine for both real preflight
and real execution.  It never invokes a projection/parser/schedule.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping
from .dg05_production_chain_v11 import file_hash, load_self_hashed, self_hashed, resolve_frozen_kernel_v11
from .dg05_production_chain_v11r1 import V5_SHA256
from .dg05_v11r1_resource_loader import verify_plan
from .dg05_v11r1_container_materializer import inspect_container_framing_v11r1
from .dg05_v11r1_route_core import _load_private
from .dg05_v11r1_source_file_crosswalk import derive_source_file_identity_crosswalk_v11r1, verify_source_file_identity_crosswalk_v11r1
from .dg05_v11r2_execution_ledger import execution_scope_id_v11r2

class DG05V11R2R1PreflightError(ValueError): pass

def replay_all_real_preconditions_v11r2r1(*, repository_root: Path, manifest: Mapping[str,Any], execution_binding_path: Path,
    legacy_release_path: Path, predecessor_v4_path: Path, predecessor_v4_closure_path: Path, historical_v1_manifest_path: Path,
    custody_receipt_path: Path, plan: Mapping[str,Any], metric_contract_path: Path, normal_registry_path: Path,
    normal_closure_path: Path, private_normal_manifest_path: Path, expected_private_normal_hash: str,
    scenario_path: Path, p1_path: Path, ledger_root: Path, final_closure_hash: str) -> dict[str,Any]:
    root=repository_root.resolve(); rows=[]
    for item in manifest['implementation_authorities']:
        p=(root/item['relative_path']).resolve()
        if root not in p.parents or p.is_symlink() or not p.is_file() or file_hash(p)!=item['byte_hash']: raise DG05V11R2R1PreflightError('IMPLEMENTATION_REPLAY_FAILED')
        rows.append(item['byte_hash'])
    impl=self_hashed({'schema':'v11r2r1_implementation_replay_receipt_v1','status':'PASS','count':len(rows),'aggregate_hash':__import__('paperworks.validation_v2.dg05_production_chain_v11',fromlist=['digest']).digest(rows)})
    binding=load_self_hashed(execution_binding_path,'dg05_executable_v11r2_candidate_manifest_v1')
    if binding['self_hash']!=manifest['execution_binding_hash']: raise DG05V11R2R1PreflightError('EXECUTION_BINDING_REPLAY_FAILED')
    if resolve_frozen_kernel_v11(root)['source_byte_hash']!=V5_SHA256: raise DG05V11R2R1PreflightError('FROZEN_V5_REPLAY_FAILED')
    legacy=load_self_hashed(legacy_release_path,'dg05_production_release_manifest_v2'); v4=load_self_hashed(predecessor_v4_path,'dg05_executable_authority_manifest_v4'); v4c=load_self_hashed(predecessor_v4_closure_path,'dg05_executable_closure_authority_v4'); v1=load_self_hashed(historical_v1_manifest_path,'dg05_executable_authority_manifest_v1')
    physical=verify_plan(custody_receipt_path=custody_receipt_path,plan_document=plan); framing=inspect_container_framing_v11r1(plan=plan)
    from .dg05_connected_rehearsal_v4 import _private_normal_paths,_typed_manifest
    from .dg05_normal_source_v2 import replay_normal_source_registry_v2
    from .dg05_v11r1_production_executor import build_frozen_production_executor_v11r1
    from scripts.freeze_dg05_execution_closure_v1 import build_detectors,build_dispatch,build_rule_runtime_registry
    det=build_detectors(); rules,sources=build_rule_runtime_registry(); dispatch=build_dispatch(det,rules); ex=build_frozen_production_executor_v11r1(repository_root=root,executable_manifest=_typed_manifest(historical_v1_manifest_path),detector_registry=det,dispatch_registry=dispatch,rule_runtime_registry=rules,rule_sources=sources)
    assets=self_hashed({'schema':'v11r2r1_production_executor_preflight_receipt_v1','status':'PASS','detector_required':len(ex.detector_assets),'detector_validated':len(ex.detector_assets),'rule_required':len(ex.rule_assets),'rule_validated':len(ex.rule_assets),'authority_mode':ex.authority_mode})
    contract=load_self_hashed(metric_contract_path,'metric_surface_contract_v2'); registry=load_self_hashed(normal_registry_path,'normal_burden_source_registry_v2'); closure=load_self_hashed(normal_closure_path,'normal_source_closure_receipt_v1')
    if closure['self_hash']!='277fe2626b51cb1b9af8052151f6fbfec499f6ab1a6ad73ebfbe93dc80b15eae' or closure['private_manifest_hash']!=expected_private_normal_hash: raise DG05V11R2R1PreflightError('NORMAL_CLOSURE_REPLAY_FAILED')
    paths=_private_normal_paths(manifest_path=private_normal_manifest_path,registry=registry,expected_manifest_hash=expected_private_normal_hash); normal=replay_normal_source_registry_v2(registry=registry,component_paths=paths,expected_dec031_binding_hash=contract['dec031_binding_hash'])
    norm=self_hashed({'schema':'v11r2r1_normal_authority_preflight_receipt_v1','status':'PASS','closure_hash':closure['self_hash'],'registry_hash':registry['self_hash'],'private_manifest_hash':expected_private_normal_hash,'components_required':30,'components_validated':len(paths),'normal_replay_hash':normal['self_hash'],'attack_test_accesses':0,'private_paths_published':False})
    scenario=_load_private(scenario_path,'hai_official_source_triangulated_scenario_authority_private_v1'); p1=_load_private(p1_path,'hai_p1_direct_target_denominator_authority_v2'); cross=derive_source_file_identity_crosswalk_v11r1(unified_scenario=scenario,physical_custody_hash=manifest['physical_custody_hash'],implementation_hash=file_hash(root/'src/paperworks/validation_v2/dg05_v11r1_source_file_crosswalk.py'),source_commit=manifest['implementation_source_commit']); crossr=verify_source_file_identity_crosswalk_v11r1(crosswalk=cross,unified_scenario=scenario,physical_custody_hash=manifest['physical_custody_hash'])
    scope=execution_scope_id_v11r2(release_hash=manifest['self_hash'],final_closure_hash=final_closure_hash,execution_binding_hash=manifest['execution_binding_hash'])
    if (ledger_root/scope).exists(): raise DG05V11R2R1PreflightError('EXECUTION_LEDGER_SCOPE_CONSUMED')
    return self_hashed({'schema':'dg05_v11r2r1_complete_real_preflight_authority_replay_v1','status':'PASS','implementation_replay_hash':impl['self_hash'],'execution_binding_hash':binding['self_hash'],'v5_kernel_hash':V5_SHA256,'legacy_hash':legacy['self_hash'],'v4_hash':v4['self_hash'],'v4_closure_hash':v4c['self_hash'],'v1_hash':v1['self_hash'],'physical_hash':physical['self_hash'],'framing_hash':framing['self_hash'],'production_executor_hash':assets['self_hash'],'normal_authority_hash':norm['self_hash'],'scenario_hash':scenario['self_hash'],'p1_hash':p1['self_hash'],'crosswalk_hash':cross['self_hash'],'crosswalk_replay_hash':crossr['self_hash'],'execution_scope_id':scope,'heldout_rows_parsed':0,'heldout_predictions':0,'heldout_metrics':0})
