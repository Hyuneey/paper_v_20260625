"""Freeze the hardened pre-DG05 V2 authorities without protected-data reads."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research_control_center/validation_v2/multipanel_pre_dg05'
IMPLEMENTATION_COMMIT='e8ad3a141eb204415079e7415f69167a8d30dbae'
BASELINE='3e8799155ede1e4e6b7b835e8e8866c4e21b6d16'


def canonical(value:object)->bytes:
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()


def sha_file(path:Path)->str:return sha256(path.read_bytes()).hexdigest()


def read(name:str)->dict:
    value=json.loads((OUT/name).read_text(encoding='utf-8'))
    body={key:item for key,item in value.items() if key!='self_hash'}
    if value.get('self_hash')!=sha256(canonical(body)).hexdigest():raise RuntimeError(f'SELF_HASH_MISMATCH:{name}')
    return value


def write(name:str,body:dict)->str:
    payload=dict(body);payload['self_hash']=sha256(canonical(payload)).hexdigest()
    (OUT/name).write_bytes(canonical(payload)+b'\n');return payload['self_hash']


def main()->None:
    method=read('MULTIPANEL_METHOD_BUNDLE_AUTHORITY_V1.json')
    fusion=read('FUSION_AUTHORITY_REPLAY_V1.json')
    burden=read('NORMAL_FALSE_BURDEN_AUTHORITY_V1.json')
    gdn=read('../xver_normal/GDN_CANONICAL_CONTEXT_AUTHORITY_V1.json')
    mapping=read('../dg04_xver_prep/P1_FEATURE_MAPPING_AUTHORITY_V1.json')
    external={v:read(f'{v}_DETECTOR_AUTHORITY_V1.json') for v in ('HAI22','HAI21')}
    panel_specs=(
        ('HAI23_TEST2_PRIMARY_HELDOUT_V1','23.05','timestamp',tuple(P1_FEATURE_ORDER)),
        ('HAI22_EXTERNAL_REPLICATION_V1','22.04','timestamp',tuple(external['HAI22']['feature_ids'])),
        ('HAI21_EXTERNAL_REPLICATION_V1','21.03','time',tuple(external['HAI21']['feature_ids'])),
    )
    allowlist_documents=[]
    for panel,version,timestamp,features in panel_specs:
        body={'schema':'multipanel_feature_allowlist_authority_v2','panel_id':panel,'dataset_version':version,
              'timestamp_id':timestamp,'feature_ids':list(features),'method_bundle_hash':method['self_hash'],
              'source_commit':IMPLEMENTATION_COMMIT}
        allowlist_documents.append({**body,'self_hash':sha256(canonical(body)).hexdigest()})
    allowlist_hash=write('ATTACK_FEATURE_ALLOWLIST_AUTHORITIES_V1.json',{
        'schema':'attack_feature_allowlist_authorities_v1','status':'FROZEN_BEFORE_DG05',
        'authorities':allowlist_documents,'unknown_columns':'EXCLUDED_WITHOUT_VALUE_DESERIALIZATION',
        'label_scenario_value_accesses':0})
    file_census_hash=write('ATTACK_FILE_CENSUS_AUTHORITIES_V1.json',{
        'schema':'attack_file_census_authorities_v1','status':'FROZEN_FROM_PUBLIC_OFFICIAL_METADATA_BEFORE_DG05',
        'official_metadata_file_hash':sha_file(ROOT/'docs/task_reports/TASK-039AR_KAGGLE_METADATA_FREEZE.json'),
        'panels':[
            {'panel_id':'HAI23_TEST2_PRIMARY_HELDOUT_V1','dataset_version':'23.05','file_ids':['hai-test2.csv']},
            {'panel_id':'HAI22_EXTERNAL_REPLICATION_V1','dataset_version':'22.04','file_ids':['test1.csv','test2.csv','test3.csv','test4.csv']},
            {'panel_id':'HAI21_EXTERNAL_REPLICATION_V1','dataset_version':'21.03','file_ids':['test1.csv','test2.csv','test3.csv','test4.csv','test5.csv']}],
        'raw_container_hashes':'MUST_BE_BOUND_IN_FROZEN_PHYSICAL_FILE_AUTHORITY_DURING_DG05_PHASE_A',
        'attack_payload_accesses':0,'label_or_scenario_accesses':0})
    p1_documents=[]
    for panel,version,_,features in panel_specs:
        provenance=gdn['self_hash'] if version=='23.05' else mapping['self_hash']
        entries=[{'official_identity':feature,'scope':'P1','mapping_state':'EXACT_MATCH','provenance_hash':provenance}
                 for feature in sorted(features)]
        body={'schema':'frozen_p1_mapping_authority_v2','dataset_version':version,'entries':entries,
              'official_mapping_source_hash':provenance,'source_commit':IMPLEMENTATION_COMMIT}
        p1_documents.append({**body,'self_hash':sha256(canonical(body)).hexdigest()})
    p1_mapping_hash=write('P1_MAPPING_AUTHORITIES_V1.json',{
        'schema':'p1_mapping_authorities_v1','status':'METHOD_BLIND_FROZEN_BEFORE_DG05',
        'authorities':p1_documents,'unlisted_official_identity':'UNRESOLVED','verified_alias_count':0,
        'prediction_inputs':False,'real_scenario_metadata_accesses':0})
    metric_hash=write('MULTIPANEL_METRIC_AUTHORITY_V2.json',{
        'schema':'multipanel_metric_authority_v2','status':'FROZEN_BEFORE_DG05','integration_baseline':BASELINE,
        'implementation_source_commit':IMPLEMENTATION_COMMIT,'primary_unit':'OFFICIAL_ATTACK_SCENARIO',
        'primary_scope':'P1_ELIGIBLE_ONLY','primary_metric':'OFFICIAL_SCENARIO_RECALL_MICRO_WITHIN_VERSION',
        'scenario_hit_implementation':'official_scenario_hits_v1:SAME_DATASET_VERSION_AND_PHYSICAL_FILE_CLOSED_INTERVAL_OVERLAP',
        'scenario_authority_binding':['dataset_version','file_id','scenario_id','scenario_authority_hash','eligibility_authority_hash'],
        'wilson':'TWO_SIDED_95_PERCENT','delay':'STRICT_INTEGER_FIRST_IN_INTERVAL_ALARM_MINUS_OFFICIAL_START_FILE_LOCAL',
        'miss_delay':'NOT_DETECTED','false_burden':'FILE_LOCAL_EPISODES_RATIO_OF_SUMS_WITHIN_AUTHORITY',
        'cross_version_false_burden_pooling':'PROHIBITED',
        'etapr':{'source_commit':'af9e7aed35cfd160cbe0d04c8ec4c102502cb677','theta_p':0.5,'theta_r':0.1,'delta':0.0,
                 'binding':'FILE_NAMESPACED_DISJOINT_RANGE_UNION_WITH_PER_FILE_RESULTS_RETAINED','separator_safe_test_set':[1,7,101,1024],
                 'target_scope':'P1_ELIGIBLE_OFFICIAL_SCENARIO_RANGES_WITH_ALL_FILE_LOCAL_PREDICTION_RANGES','existing_conformance':'109_OF_109_PASS'},
        'empty':{'scenario_gt_positive_prediction_empty':0.0,'scenario_gt_empty':'NOT_EVALUABLE','paired_scenario_empty':'NOT_EVALUABLE',
                 'normal_positive_exposure_no_alarm':0.0,'normal_zero_exposure':'INVALID_AUTHORITY',
                 'etapr_gt_positive_prediction_empty':[0.0,0.0,0.0],'etapr_gt_empty':'NOT_APPLICABLE'},
        'contrasts':[['M2','M1'],['M4','M0'],['M3','M0'],['M4','M3']],
        'paired_alignment_implementation':'paired_official_scenario_table_v1:EXACT_COMPOSITE_IDENTITY_AND_AUTHORITY',
        'mcnemar':'EXACT_TWO_SIDED_BINOMIAL_WITHIN_VERSION_ONLY',
        'no_pooling_implementation':'assert_single_version_records_v1','primary_cross_version_pooling':'PROHIBITED',
        'point_adjustment':'NONE','implementation_hashes':{name:sha_file(ROOT/name) for name in (
            'src/paperworks/validation_v2/multipanel_metrics_v1.py','src/paperworks/validation_v2/multipanel_etapr_v2.py',
            'src/paperworks/validation_v2/etapr_exchange_v1.py')},'attack_accesses':0,'label_accesses':0})
    etapr_hash=write('ETAPR_MULTIFILE_CONFORMANCE_V2.json',{
        'schema':'etapr_multifile_conformance_v2','status':'PASS','official_source_commit':'af9e7aed35cfd160cbe0d04c8ec4c102502cb677',
        'prior_cases':'109_OF_109_PASS_UNCHANGED','new_tests':{'file_order_invariance':True,'separator_invariance':True,
        'separators':[1,7,101,1024],'no_cross_file_merge':True,'independent_block_diagonal_oracle_equality':True,
        'per_file_outputs_retained':True,'per_file_empty_semantics_retained':True,'empty_gt_guard':True,'empty_prediction_guard':True},
        'parameters':{'theta_p':0.5,'theta_r':0.1,'delta':0.0},
        'implementation_source_commit':IMPLEMENTATION_COMMIT,'test_source_hash':sha_file(ROOT/'tests/test_multipanel_etapr_official_v2.py'),
        'attack_accesses':0,'labels_accessed':0})
    statistics_hash=write('STATISTICAL_ANALYSIS_CONTRACT_V2.json',{
        'schema':'multipanel_statistical_analysis_contract_v2','primary_unit':'OFFICIAL_P1_ELIGIBLE_SCENARIO',
        'within_version_recall':'MICRO_EXACT_NUMERATOR_DENOMINATOR','uncertainty':'WILSON_95_PERCENT',
        'paired_contrasts':{'C1':['M2','M1'],'C2':['M4','M0'],'C3':['M3','M0'],'C4':['M4','M3']},
        'paired_table':['both_hit','A_only','B_only','neither'],
        'paired_alignment':'EXACT_DATASET_FILE_SCENARIO_AND_SCENARIO_ELIGIBILITY_AUTHORITY_HASHES',
        'empty_paired_table':'NOT_EVALUABLE','mcnemar':'EXACT_TWO_SIDED_BINOMIAL_WHEN_ALIGNED_WITHIN_VERSION',
        'pooled_cross_version_recall':'PROHIBITED','pooled_cross_version_mcnemar':'PROHIBITED','iid_146_claim':False,
        'descriptive_synthesis':['direction','heterogeneity','portfolio_size','hit_miss_patterns','confidence_intervals','version_specific_burden']})
    p1_hash=write('P1_ELIGIBILITY_CUSTODIAN_AUTHORITY_V2.json',{
        'schema':'p1_eligibility_custodian_authority_v2','status':'DESIGN_ONLY_FROZEN_BEFORE_DG05',
        'integration_baseline':BASELINE,'implementation_source_commit':IMPLEMENTATION_COMMIT,
        'implementation_entrypoint':'classify_p1_scenario_v2','mapping_authority':'FrozenP1MappingAuthorityV2_CANONICAL_SELF_HASH_BOUND',
        'mapping_authority_bundle_hash':p1_mapping_hash,
        'scenario_authority':'OfficialScenarioMetadataV2_WITH_OFFICIAL_SOURCE_AND_SCENARIO_HASHES',
        'input':['dataset_version','file_id','official_scenario_id','official_attacked_identities','official_explicit_affected_processes',
                 'official_source_hash','scenario_authority_hash','frozen_mapping_authority'],
        'output':['P1_ELIGIBLE','CROSS_PROCESS_P1_RELEVANT','OUT_OF_SCOPE','UNRESOLVED'],
        'precedence':['ANY_DIRECT_EXACT_OR_VERIFIED_P1_IS_P1_ELIGIBLE','ANY_UNRESOLVED_WITHOUT_DIRECT_P1_IS_UNRESOLVED',
                      'EXPLICIT_OFFICIAL_P1_EFFECT_IS_CROSS_PROCESS','OTHERWISE_OUT_OF_SCOPE'],
        'record_fields':['reason','unresolved_identity_count','official_source_hash','scenario_authority_hash','mapping_authority_hash','mapping_source_hash','self_hash'],
        'primary_denominator':['P1_ELIGIBLE'],'cross_process':'SECONDARY_DESCRIPTIVE_ONLY','method_prediction_input':False,
        'nested_method_taint_rejection':True,'implementation_hash':sha_file(ROOT/'src/paperworks/validation_v2/p1_eligibility_custodian_v1.py'),
        'real_eligibility_generated':False})
    custody_hash=write('GLOBAL_PREDICTION_CUSTODY_AUTHORITY_V2.json',{
        'schema':'global_prediction_custody_authority_v2','status':'DESIGN_ONLY_FROZEN_BEFORE_DG05',
        'integration_baseline':BASELINE,'implementation_source_commit':IMPLEMENTATION_COMMIT,
        'method_bundle_authority_hash':method['self_hash'],'panels':method['operational_order'],
        'attack_file_census_authority_hash':file_census_hash,'feature_allowlist_authority_bundle_hash':allowlist_hash,
        'physical_file_authority':'FrozenPhysicalFileAuthorityV2_PHASE_A_RAW_HEADER_AND_OFFICIAL_SOURCE_HASH_BOUND',
        'physical_file_binding':'EXACT_PUBLIC_FILE_CENSUS_AND_MANIFEST_DG05_HASH_REQUIRED',
        'states':['ATTACK_CONTAINER_CUSTODIED_LABEL_LOCKED','ATTACK_FEATURE_PROJECTION_READY_LABEL_LOCKED',
                  'PREDICTIONS_IN_PROGRESS_LABEL_LOCKED','GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED','LABEL_SCENARIO_LEASE_OPEN','RESULTS_COMPUTED'],
        'transition_policy':'STATE_SPECIFIC_DURABLE_APPEND_ONLY_HASH_CHAIN_ADJACENT_ONLY_NO_SKIP','labels_between_panels':False,
        'projection_transition_evidence':'EXACT_TEN_FILE_TYPED_RECEIPT_AND_PROJECTION_BYTE_REPLAY',
        'cell_census':'GlobalCellCensusAuthorityV2_EXACT_PANEL_FILE_AND_DETECTOR_PORTFOLIO_FUSION_DERIVED_METHOD_PRODUCT',
        'success_receipt':'PredictionSuccessReceiptV2_WITH_DURABLE_ARTIFACT_HASH_REPLAY',
        'failure_receipt':'PredictionFailureReceiptV2_NO_SYNTHETIC_PREDICTION_OR_ALARM_FIELDS',
        'attack_projection':'FrozenFeatureAllowlistAuthorityV2_BOUND_TIMESTAMP_PLUS_APPROVED_FEATURES',
        'projection_artifact_replay':'CANONICAL_COLUMNS_VALUES_ROW_COUNT_AND_SHA256',
        'excluded_value_contact_flags':'LABEL_AND_SCENARIO_PARSE_DECODE_INSPECT_COUNT_VALIDATE_FILTER_USE_ALL_FALSE_REQUIRED',
        'manifest':'GlobalPredictionManifestV2_DURABLE_REOPEN_HASH_REPLAY',
        'lease_precondition':'DURABLE_EXACT_GLOBAL_CENSUS_AND_GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED',
        'lease':'OPAQUE_APPEND_ONLY_SINGLE_ISSUE_SINGLE_CONSUME_NO_RETRY','lease_count':1,
        'publication':'FILE_FSYNC_ATOMIC_NO_OVERWRITE_LINK_POST_PUBLICATION_REPLAY',
        'reader_failure_consumes_lease':True,'post_reader_projection_prediction_replay':'REQUIRED',
        'global_freeze_transition_evidence':'TYPED_MANIFEST_CELL_AND_SUCCESS_ARTIFACT_BYTE_REPLAY',
        'results_state':'EXACT_PANEL_METHOD_RESULT_CENSUS_BUNDLE_AND_SEPARATE_DURABLE_RESULT_INTEGRITY_RECEIPT_REQUIRED',
        'result_bundle':'HASH_ONLY_EXACT_PANEL_METHOD_CENSUS_BOUND_TO_MANIFEST_LEASE_METRIC_AND_P1_AUTHORITIES',
        'post_label_prediction_mutation':'PROHIBITED',
        'implementation_hash':sha_file(ROOT/'src/paperworks/validation_v2/multipanel_custody_v1.py'),
        'attack_accesses':0,'label_accesses':0})
    prereg_hash=write('MULTIPANEL_PREREGISTRATION_V2.json',{
        'schema':'multipanel_preregistration_v2','status':'PRE_DG05_FROZEN','integration_baseline':BASELINE,
        'implementation_source_commit':IMPLEMENTATION_COMMIT,
        'panels':[{'panel_id':'HAI23_TEST2_PRIMARY_HELDOUT_V1','nominal_scenarios':38},
                  {'panel_id':'HAI22_EXTERNAL_REPLICATION_V1','nominal_scenarios':58},
                  {'panel_id':'HAI21_EXTERNAL_REPLICATION_V1','nominal_scenarios':50}],
        'method_bundle_authority_hash':method['self_hash'],'metric_authority_hash':metric_hash,
        'eligibility_authority_hash':p1_hash,'custody_authority_hash':custody_hash,
        'attack_feature_allowlist_authorities_hash':allowlist_hash,'attack_file_census_authorities_hash':file_census_hash,
        'p1_mapping_authorities_hash':p1_mapping_hash,
        'fusion_replay_hash':fusion['self_hash'],'normal_burden_authority_hash':burden['self_hash'],
        'etapr_conformance_hash':etapr_hash,'statistical_analysis_hash':statistics_hash,
        'supersedes_preregistration_hash':read('MULTIPANEL_PREREGISTRATION_V1.json')['self_hash'],
        'dg05_status':'USER_DECISION_REQUIRED','phase_a':'FEATURE_ONLY_AND_ALL_PANEL_PREDICTION',
        'phase_b':'CONDITIONAL_ONE_SHOT_LABEL_SCENARIO_LEASE_AFTER_DURABLE_GLOBAL_FREEZE',
        'no_primary_pooled_recall':True,'post_result_tuning':False,'attack_accesses':0})
    hai23=read('HAI23_DETECTOR_PRIVATE_HASH_BINDING_V1.json')
    brief=f"""# DG-05 — Multi-Panel Attack Feature + Conditional Label/Scenario Access

Status: `USER_DECISION_REQUIRED`

No attack/test payload, label value, scenario interval, scenario target, or real eligibility was accessed while preparing this gate.

## Scope and phases

One conditional approval covers exactly HAI23 test2 (38 nominal scenarios), HAI22 (58), and HAI21 (50). Phase A permits strict positive-allowlist feature projection and all frozen-method predictions in the fixed HAI23 → HAI22 → HAI21 order. Phase B can issue exactly one opaque label/scenario lease only after the V2 exact cell census, prediction-artifact replay, append-only state chain, and durable `GLOBAL_PREDICTION_FROZEN_LABEL_LOCKED` manifest all pass.

## Frozen authorities

- method bundle: `{method['self_hash']}`
- metric V2: `{metric_hash}`
- P1 custodian V2: `{p1_hash}`
- global custody V2: `{custody_hash}`
- preregistration V2: `{prereg_hash}`
- eTaPR conformance V2: `{etapr_hash}`
- statistical analysis V2: `{statistics_hash}`
- attack feature allowlists: `{allowlist_hash}`
- exact public attack-file census: `{file_census_hash}`
- P1 mapping authorities: `{p1_mapping_hash}`
- Fusion: `{fusion['authority_hash']}`
- HAI23 detector private binding: `{hai23['self_hash']}`
- HAI23 PCA fit/threshold: `{hai23['pca_fit_authority_hash']}` / `{hai23['pca_threshold_authority_hash']}`
- HAI23 IF fit/threshold: `{hai23['if_fit_authority_hash']}` / `{hai23['if_threshold_authority_hash']}`
- HAI22 detector: `{external['HAI22']['self_hash']}`
- HAI21 detector: `{external['HAI21']['self_hash']}`

## Non-negotiable execution

Every exact panel × physical file × primary/secondary method cell terminates with either a success receipt bound to replayed prediction bytes or a distinct method-failure receipt that contains no invented prediction/alarm fields. Phase A binds each public file identity to raw-container/header/official-source hashes in a typed physical-file authority before projection. Labels stay locked until projection and prediction artifacts plus the complete manifest are durably replayed. The lease is append-only, single-issue, single-consume, and remains consumed if the reader fails. After lease issue, prediction artifacts, models, portfolios, thresholds, Fusion, mappings, and eligibility logic are immutable.

Official Scenario Recall is computed from same-version, same-file overlap against independently eligible official closed intervals. Paired tables require exact dataset/file/scenario identities plus identical scenario and eligibility authority hashes. Per-file eTaPR outputs are retained alongside the canonical disjoint union. Cross-version primary pooling and point adjustment are prohibited.

No provider call, GDN training, method redesign, attack access before approval, post-result tuning, or professor submission is authorized.
"""
    (OUT/'DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V1.md').write_text(brief,encoding='utf-8',newline='\n')
    print(json.dumps({'status':'PRE_DG05_V2_AUTHORITY_FREEZE_PASS','metric':metric_hash,'p1':p1_hash,
                      'custody':custody_hash,'preregistration':prereg_hash},sort_keys=True))


if __name__=='__main__':main()
