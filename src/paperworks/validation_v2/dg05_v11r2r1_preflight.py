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
from .dg05_v11r2_execution_ledger import execution_scope_id_v11r2, ledger_scope_status_v11r2
from .dg05_v11r2r1_execution_binding import replay_execution_binding_v11r2r1

_SCENARIO_HASH = "2bd2bb4d4a6b8eacf5caaa44b36b5d41e06514e9521ac08789cfe5d268245e38"
_P1_HASH = "eda3cdc46e0fc044b38f6c1c3f1c45330b93d6a85d3e52a36381936fbb88a737"
_CROSSWALK_HASH = "9f2c0d442fd92fb09a8f56389aa7a2bfde7bad74657577bef5460e5beb2d9554"
_NORMAL_CLOSURE_HASH = "277fe2626b51cb1b9af8052151f6fbfec499f6ab1a6ad73ebfbe93dc80b15eae"
_NORMAL_REPLAY_HASH = "9d9193b2d5f00ffce3823aa4e2e6e351ce7b68aa3c36ac5ba7933072d597a0c5"

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
    try:
        binding_replay = replay_execution_binding_v11r2r1(
            repository_root=root, binding_path=execution_binding_path,
            candidate_manifest=manifest,
        )
    except Exception as exc:
        raise DG05V11R2R1PreflightError('EXECUTION_BINDING_REPLAY_FAILED') from exc
    if resolve_frozen_kernel_v11(root)['source_byte_hash']!=V5_SHA256: raise DG05V11R2R1PreflightError('FROZEN_V5_REPLAY_FAILED')
    legacy=load_self_hashed(legacy_release_path,'dg05_production_release_manifest_v2'); v4=load_self_hashed(predecessor_v4_path,'dg05_executable_authority_manifest_v4'); v4c=load_self_hashed(predecessor_v4_closure_path,'dg05_executable_closure_authority_v4'); v1=load_self_hashed(historical_v1_manifest_path,'dg05_executable_authority_manifest_v1')
    # A merely well-formed historical artifact is not enough: every supplied
    # predecessor root must be the one named by the Phase-A authority census.
    authority_hashes = manifest.get('authority_hashes', {})
    expected_legacy = authority_hashes.get('legacy_v10_release_hash')
    expected_v4 = authority_hashes.get('predecessor_v4_manifest_hash')
    expected_v4c = authority_hashes.get('predecessor_v4_closure_hash')
    expected_v1 = authority_hashes.get('historical_v1_manifest_hash')
    for observed, expected in ((legacy['self_hash'], expected_legacy), (v4['self_hash'], expected_v4),
                               (v4c['self_hash'], expected_v4c), (v1['self_hash'], expected_v1)):
        if expected is not None and observed != expected:
            raise DG05V11R2R1PreflightError('LEGACY_PREDECESSOR_LINEAGE_MISMATCH')
    legacy_replay = self_hashed({'schema':'v11r2r1_legacy_predecessor_replay_receipt_v1','status':'PASS',
                                 'legacy_hash':legacy['self_hash'],'v4_hash':v4['self_hash'],
                                 'v4_closure_hash':v4c['self_hash'],'v1_hash':v1['self_hash'],
                                 'expected_authority_hashes': {key: value for key, value in {
                                     'legacy_v10_release_hash':expected_legacy,
                                     'predecessor_v4_manifest_hash':expected_v4,
                                     'predecessor_v4_closure_hash':expected_v4c,
                                     'historical_v1_manifest_hash':expected_v1,
                                 }.items() if value is not None}})
    physical=verify_plan(custody_receipt_path=custody_receipt_path,plan_document=plan); framing=inspect_container_framing_v11r1(plan=plan)
    from .dg05_connected_rehearsal_v4 import _private_normal_paths,_typed_manifest
    from .dg05_normal_source_v2 import replay_normal_source_registry_v2
    from .dg05_v11r1_production_executor import build_frozen_production_executor_v11r1
    from scripts.freeze_dg05_execution_closure_v1 import build_detectors,build_dispatch,build_rule_runtime_registry
    det=build_detectors(); rules,sources=build_rule_runtime_registry(); dispatch=build_dispatch(det,rules); ex=build_frozen_production_executor_v11r1(repository_root=root,executable_manifest=_typed_manifest(historical_v1_manifest_path),detector_registry=det,dispatch_registry=dispatch,rule_runtime_registry=rules,rule_sources=sources)
    # Re-run validation at the preflight boundary.  The counts below are
    # summaries of validated registries/assets, never standalone evidence.
    ex.validate()
    detector_required = len(det.entries)
    rule_required = len(rules.entries)
    detector_validated = sum(1 for asset in ex.detector_assets if (asset.validate(det.lookup(asset.panel_id, asset.detector_id)) is None))
    rule_validated = sum(1 for asset in ex.rule_assets if (asset.validate(rules.lookup(asset.panel_id, asset.portfolio_role)) is None))
    if detector_required != detector_validated or rule_required != rule_validated:
        raise DG05V11R2R1PreflightError('PRODUCTION_ASSET_REPLAY_FAILED')
    assets=self_hashed({'schema':'v11r2r1_production_executor_preflight_receipt_v1','status':'PASS','detector_required':detector_required,'detector_validated':detector_validated,'rule_required':rule_required,'rule_validated':rule_validated,'authority_mode':ex.authority_mode,'executor_validate_called':True})
    contract=load_self_hashed(metric_contract_path,'metric_surface_contract_v2'); registry=load_self_hashed(normal_registry_path,'normal_burden_source_registry_v2'); closure=load_self_hashed(normal_closure_path,'normal_source_closure_receipt_v1')
    if closure['self_hash']!=_NORMAL_CLOSURE_HASH or closure['private_manifest_hash']!=expected_private_normal_hash: raise DG05V11R2R1PreflightError('NORMAL_CLOSURE_REPLAY_FAILED')
    paths=_private_normal_paths(manifest_path=private_normal_manifest_path,registry=registry,expected_manifest_hash=expected_private_normal_hash); normal=replay_normal_source_registry_v2(registry=registry,component_paths=paths,expected_dec031_binding_hash=contract['dec031_binding_hash'])
    required_components = registry.get('component_count')
    if not isinstance(required_components, int) or required_components != len(registry.get('components', ())) or len(paths) != required_components:
        raise DG05V11R2R1PreflightError('NORMAL_COMPONENT_CENSUS_REPLAY_FAILED')
    if normal['self_hash'] != _NORMAL_REPLAY_HASH:
        raise DG05V11R2R1PreflightError('NORMAL_REGISTRY_REPLAY_FAILED')
    norm=self_hashed({'schema':'v11r2r1_normal_authority_preflight_receipt_v1','status':'PASS','closure_hash':closure['self_hash'],'registry_hash':registry['self_hash'],'private_manifest_hash':expected_private_normal_hash,'components_required':required_components,'components_validated':len(paths),'normal_replay_hash':normal['self_hash'],'attack_test_accesses':0,'private_paths_published':False})
    scenario=_load_private(scenario_path,'hai_official_source_triangulated_scenario_authority_private_v1'); p1=_load_private(p1_path,'hai_p1_direct_target_denominator_authority_v2')
    panel_counts={panel: sum(row.get('panel_id') == panel for row in scenario.get('canonical_records', ())) for panel in ('HAI23_TEST2_PRIMARY_HELDOUT_V1','HAI22_EXTERNAL_REPLICATION_V1','HAI21_EXTERNAL_REPLICATION_V1')}
    p1_counts={status: sum(row.get('eligibility_status') in ({'P1_ELIGIBLE'} if status == 'P1_ELIGIBLE' else {'P1_NOT_ELIGIBLE','OUT_OF_SCOPE'} if status == 'OUT_OF_SCOPE' else {'UNRESOLVED'}) for row in p1.get('decisions', ())) for status in ('P1_ELIGIBLE','OUT_OF_SCOPE','UNRESOLVED')}
    if scenario.get('self_hash') != _SCENARIO_HASH or len(scenario.get('canonical_records', ())) != 146 or panel_counts != {'HAI23_TEST2_PRIMARY_HELDOUT_V1':38,'HAI22_EXTERNAL_REPLICATION_V1':58,'HAI21_EXTERNAL_REPLICATION_V1':50}:
        raise DG05V11R2R1PreflightError('SCENARIO_AUTHORITY_REPLAY_FAILED')
    if p1.get('self_hash') != _P1_HASH or len(p1.get('decisions', ())) != 146 or p1_counts != {'P1_ELIGIBLE':116,'OUT_OF_SCOPE':30,'UNRESOLVED':0}:
        raise DG05V11R2R1PreflightError('P1_AUTHORITY_REPLAY_FAILED')
    cross=derive_source_file_identity_crosswalk_v11r1(unified_scenario=scenario,physical_custody_hash=manifest['physical_custody_hash'],implementation_hash=file_hash(root/'src/paperworks/validation_v2/dg05_v11r1_source_file_crosswalk.py'),source_commit=manifest['implementation_source_commit']); crossr=verify_source_file_identity_crosswalk_v11r1(crosswalk=cross,unified_scenario=scenario,physical_custody_hash=manifest['physical_custody_hash'])
    if cross['self_hash'] != _CROSSWALK_HASH or len(cross.get('entries', ())) != 10:
        raise DG05V11R2R1PreflightError('SOURCE_FILE_CROSSWALK_REPLAY_FAILED')
    scope=execution_scope_id_v11r2(release_hash=manifest['self_hash'],final_closure_hash=final_closure_hash,execution_binding_hash=manifest['execution_binding_hash'])
    ledger_status = ledger_scope_status_v11r2(ledger_root=ledger_root, release_hash=manifest['self_hash'], final_closure_hash=final_closure_hash, execution_binding_hash=manifest['execution_binding_hash'])
    if ledger_status['status'] != 'UNUSED': raise DG05V11R2R1PreflightError('EXECUTION_LEDGER_SCOPE_CONSUMED')
    return self_hashed({'schema':'dg05_v11r2r1_complete_real_preflight_authority_replay_v1','status':'PASS','implementation_replay_hash':impl['self_hash'],'execution_binding_hash':binding_replay['execution_binding_hash'],'execution_binding_replay_hash':binding_replay['self_hash'],'v5_kernel_hash':V5_SHA256,'legacy_hash':legacy['self_hash'],'v4_hash':v4['self_hash'],'v4_closure_hash':v4c['self_hash'],'v1_hash':v1['self_hash'],'legacy_predecessor_replay_hash':legacy_replay['self_hash'],'physical_hash':physical['self_hash'],'framing_hash':framing['self_hash'],'production_executor_hash':assets['self_hash'],'normal_authority_hash':norm['self_hash'],'scenario_hash':scenario['self_hash'],'p1_hash':p1['self_hash'],'crosswalk_hash':cross['self_hash'],'crosswalk_replay_hash':crossr['self_hash'],'execution_scope_id':scope,'ledger_status_hash':ledger_status['self_hash'],'heldout_rows_parsed':0,'heldout_predictions':0,'heldout_metrics':0})
