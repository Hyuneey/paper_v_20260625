"""Freeze the explicit user decision, not a fabricated scientific execution result."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
from paperworks.validation_v2.exp03b_custody_v1 import seal, publish, replay
from paperworks.validation_v2.exp03b_contract_v1 import require

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'research_control_center/validation_v2/xver_normal'
BASE='ade70214c9d70105e448276bfe643eae939fbaa1'


def main():
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE,'EXACT_APPROVAL_BASE')
    dependencies={}
    for name in ('GDN_CANONICAL_CONTEXT_AUTHORITY_V1.json','HAI22_GDN_CONTEXT_MAPPING_V1.json',
                 'HAI21_GDN_CONTEXT_MAPPING_V1.json','HAI22_GDN_CONTEXT_PROJECTION_RECEIPT_V1.json',
                 'HAI21_GDN_CONTEXT_PROJECTION_RECEIPT_V1.json','XVER_NORMAL_PREPARATION_STATUS_V1.json'):
        path=PUB/name;value=json.loads(path.read_text(encoding='utf-8'));replay(value)
        require(path.read_bytes()==subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT),'PARENT_AUTHORITY_CHANGED')
        dependencies[name]=value['self_hash']
    paths=['src/paperworks/validation_v2/xver_gdn_roles_v1.py',
           'src/paperworks/validation_v2/xver_gdn_provider_v1.py',
           'tests/test_xver_gdn_roles_v1.py',
           'scripts/freeze_xver_separated_gdn_roles_v1.py',
           'src/paperworks/validation_v2/exp03b_gdn_v1.py',
           'src/paperworks/validation_v2/exp03b_firewall_v2.py',
           'src/paperworks/validation_v2/exp03b_hidden_v2.py',
           'src/paperworks/validation_v2/exp03b_semantic_v2.py',
           'src/paperworks/validation_v2/exp01c_backend_v1.py',
           'src/paperworks/validation_v2/gdn_corr_contract_v1.py',
           'scripts/prepare_exp03b_evidence_v1.py']
    for path in paths[4:]:
        require((ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),'FROZEN_IMPLEMENTATION_CHANGED')
    binding=seal({'schema':'xver_separated_gdn_evidence_binding_v1',
        'status':'APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES','source_base_commit':BASE,
        'approval_source':'EXPLICIT_USER_SCIENTIFIC_BINDING_DECISION',
        'supersedes_question_only':'GDN_EVENT_EVIDENCE_BINDING_DECISION_V1.md',
        'historical_artifacts_preserved':True,'dependencies':dependencies,
        'implementation_hashes':{p:sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        'specification_hash':sha256((PUB/'GDN_SEPARATED_EVIDENCE_BINDING_V1.md').read_bytes()).hexdigest(),
        'provider_facing_GDN':'EXP03B_COMPATIBLE_SPLIT_PURE_GLOBAL',
        'provider_split':'train1','retrieval_split':'train2','global_rows_per_pair':5,
        'global_seed_aggregation':'EXP03B_MEDIAN_ALL_THREE_EMBEDDING_ATTENTION_AVAILABLE_GRAPH_SIGNED_EFFECT',
        'event_role':'AUXILIARY_CORROBORATION_ONLY',
        'event_authority':'SCI01_SPLIT_LOCAL_SOURCE_EVENTS',
        'event_window':'INTERSECTION_WITH_SEED_SPECIFIC_PURGED_VALIDATION',
        'event_rows_per_pair_per_seed':10,'event_stop_anchor':'START_PLUS_HISTORY_5',
        'event_output':'SEPARATE_PRIVATE_PER_SEED_SIDECAR_NO_NEW_POOLING_ESTIMATOR',
        'global_event_fusion_allowed':False,'event_provider_exposure_allowed':False,
        'event_retrieval_exposure_allowed':False,'event_verifier_use_allowed':False,
        'event_candidate_admission_allowed':False,'event_numeric_policy_selection_allowed':False,
        'train3_GDN_allowed':False,'train4_GDN_allowed':False,'best_seed_selection_allowed':False,
        'provider_calls_authorized':False,'credentials_authorized':False,'attack_access_authorized':False,
        'runtime_authorization':'REQUIRES_COMMITTED_VERSIONED_EXECUTION_ADAPTER_ENVIRONMENT_CUSTODY_PREFLIGHT',
        'scientific_runs_completed':0,'independent_QA':'PASS_SCOPED_ROLE_BINDING_AND_ADAPTER_QA',
        'synthetic_tests_passed':15,'scientific_execution_ready':False})
    publish(PUB/'GDN_SEPARATED_EVIDENCE_BINDING_V1.json',binding)
    print(json.dumps({'status':binding['status'],'binding_hash':binding['self_hash'],
                      'scientific_runs':0,'provider_calls':0}))


if __name__=='__main__':main()
