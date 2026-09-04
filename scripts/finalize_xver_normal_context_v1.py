"""Publish scoped context completion and a truthful, non-executed evidence gate."""
from pathlib import Path
from hashlib import sha256
import json
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay
from paperworks.validation_v2.exp03b_contract_v1 import require

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'research_control_center/validation_v2/xver_normal'


def main():
    versions={}
    for v in ('22','21'):
        mapping=json.loads((PUB/f'HAI{v}_GDN_CONTEXT_MAPPING_V1.json').read_text());replay(mapping)
        receipt=json.loads((PUB/f'HAI{v}_GDN_CONTEXT_PROJECTION_RECEIPT_V1.json').read_text());replay(receipt)
        require(len(receipt['records'])==2,'CONTEXT_PROJECTIONS_REQUIRED')
        versions['HAI'+v]={'mapped_GDN_nodes':mapping['context_count'],
            'context_status':mapping['context_status'],'context_mapping_hash':mapping['self_hash'],
            'context_projection_hash':receipt['self_hash'],'context_projection_files':2,
            'context_finite_type':'FINITE_FLOAT64','sample_interval_seconds':1,
            'absent_nodes':[r['canonical_identity'] for r in mapping['rows'] if r['status']=='ABSENT'],
            'scientific_GDN_runs':0,'T0_executed':False,'T0_portfolio_hash':None,
            'T2_evidence_ready':False,
            'profiled_tokens':None,'hard_token_ceiling':None,'cost_ceiling':None}
        parent=json.loads((ROOT/f'research_control_center/validation_v2/dg04_xver_prep/HAI{v}_META_STAT_CANDIDATE_AUTHORITY_V2.json').read_text());replay(parent)
        # Derive N from exact identities, not an expected summary number.
        pairs=parent.get('candidates',parent.get('pairs',parent.get('candidate_union')))
        require(type(pairs) is list,'CANDIDATE_IDENTITY_LIST')
        versions['HAI'+v]['candidate_count']=len(pairs)
        versions['HAI'+v]['maximum_calls_structural_only']=3*len(pairs)
    status=seal({'schema':'xver_normal_preparation_status_v1','task':'HAI-XVER-NORMAL-PREP-001',
        'parent_commit':'3a410f5b6aa32ce7aa7547ddc445cf50c1aa347b',
        'status':'BLOCKED_GDN_METHOD_CHANGE_REQUIRED','context_preparation':'PASS',
        'stage_a_changed':False,'versions':versions,'scientific_GDN_runs':0,
        'training_stop_reason':'REQUIRED_EVENT_CONDITIONED_EVIDENCE_CONTRACT_NOT_UNIQUELY_BOUND_BEFORE_RUN_1',
        'decision_brief':'GDN_EVENT_EVIDENCE_BINDING_DECISION_V1.md',
        'DG_XVER_PROVIDER':'NOT_READY_USER_DECISION_REQUIRED_AFTER_EVIDENCE_FREEZE',
        'DG05':'NOT_APPROVED','professor_package':'NOT_SUBMITTED','backup':'SINGLE_COPY_LOCAL_ONLY',
        'provider_calls':0,'credential_reads':0,'test1_accesses':0,'test2_accesses':0,
        'external_attack_accesses':0,'attack_label_accesses':0,'excluded_values_parsed':False,
        'real_scenario_accesses':0,'eligibility_materialized':False,'private_exposures':0,
        '37_option_reselection':0,'best_seed_selection':False,'HAI23_weights_transferred':False})
    publish(PUB/'XVER_NORMAL_PREPARATION_STATUS_V1.json',status)
    print(json.dumps({'status':status['status'],'contexts':versions,'hash':status['self_hash']}))


if __name__=='__main__':main()
