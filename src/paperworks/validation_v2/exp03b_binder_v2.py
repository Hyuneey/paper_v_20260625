"""SCI02B: deterministic calibration AFTER durable semantic evaluation. Private only."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import math
from .exp03b_contract_v1 import require,digest,ALIASES
from .exp03b_custody_v1 import replay,seal,publish
from .exp03b_numeric_v1 import GRID,pooled_roles,roles_from_summary
from .numeric_policy_v1 import FROZEN_WINDOW_VALUES
from .formal_v4_authority_v1 import V4_NUMERIC_ROLES
from .exp03b_execution_v2 import VerifiedAdmission
from .exp03b_evaluation import GuardRuleInput,run_guard_portfolio

POLICY='RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05'
FIXED_ALIAS=ALIASES[next(i for i,p in enumerate(GRID) if p is not None and tuple(map(float,p))==(7.,.90,2.,.05))]
_ISSUER=object()


def read_sealed(path):
    value=json.loads(path.read_text());replay(value);return value


def require_provider_open(run):
    require(not any((run/p).exists() for p in ('ALL_ARM_OUTPUTS_FROZEN.json','PROVIDER_PHASE_CLOSED.json','evaluation/TRAIN2_ADMISSIONS_FROZEN.json','evaluation/TRAIN3_EVALUATION_FROZEN.json','evaluation/NUMERIC_BINDING_STARTED.json','evaluation/FINAL_LOCAL_RESULTS.json')), 'PROVIDER_PHASE_PERMANENTLY_CLOSED')


class PostInductionCapabilityV2:
    __slots__=('run','files','admission_hashes','reference_hash','reference_members')
    def __init__(self,token,run,files,admission_hashes,reference_hash,reference_members=()):
        require(token is _ISSUER,'POST_INDUCTION_FACTORY_REQUIRED')
        self.run=run;self.files=tuple(files);self.admission_hashes=frozenset(admission_hashes);self.reference_hash=reference_hash;self.reference_members=frozenset(reference_members)
    def replay(self):
        require(not (self.run/'SINGLE_WRITER.lock').exists(),'PROVIDER_WRITER_ACTIVE')
        require(all(sha256(p.read_bytes()).hexdigest()==h for p,h in self.files),'POST_INDUCTION_BYTES_CHANGED')


def authorize_binding(run:Path,cohort:dict,freeze_hash:str,reference_document:dict):
    replay(cohort);require(cohort['count']>0 and cohort['count']==len(cohort['pairs']),'BLOCKED_EMPTY_COHORT')
    files=[]
    def read(name):
        p=run/name;v=read_sealed(p);files.append((p,sha256(p.read_bytes()).hexdigest()));return v
    closed=read('PROVIDER_PHASE_CLOSED.json');bundle=read('ALL_ARM_OUTPUTS_FROZEN.json')
    require(closed['output_bundle_hash']==bundle['self_hash'] and closed['execution_freeze_hash']==freeze_hash and closed['provider_calls_allowed'] is False,'CLOSED_PHASE_BINDING')
    outputs=[]
    for pair in cohort['pairs']:
        for arm in ('T1','T1-B','T2'):
            for repeat in (1,2,3):
                row=read(f"outputs/{pair['candidate_id']}.{arm}.R{repeat}.json")
                require((row['candidate_id'],row['arm'],row['repeat'])==(pair['candidate_id'],arm,repeat),'OUTPUT_SLOT_IDENTITY');outputs.append(row['self_hash'])
    require(bundle['count']==9*cohort['count'] and outputs==bundle['terminal_hashes'],'OUTPUT_CLOSURE')
    admissions=read('evaluation/TRAIN2_ADMISSIONS_FROZEN.json');evaluation=read('evaluation/TRAIN3_EVALUATION_FROZEN.json')
    require(admissions['output_bundle_hash']==bundle['self_hash'] and admissions['execution_freeze_hash']==freeze_hash,'ADMISSIONS_BINDING')
    require(evaluation['output_bundle_hash']==bundle['self_hash'] and evaluation['admissions_hash']==admissions['self_hash'],'TRAIN3_EVALUATION_BINDING')
    require(len(admissions['records'])==10*cohort['count'],'ADMISSION_SLOT_CLOSURE')
    expected={(p['candidate_id'],a,r) for p in cohort['pairs'] for a in ('T0','T1','T1-B','T2') for r in ((1,) if a=='T0' else (1,2,3))}
    require({(x['candidate_id'],x['arm'],x['repeat']) for x in admissions['records']}==expected,'ADMISSION_SLOT_IDENTITIES')
    hashes=[x['admission_hash'] for x in admissions['records'] if x['admission_hash'] is not None]
    replay(reference_document);require(reference_document['self_hash']==evaluation['reference_hash'],'REFERENCE_CONTENT_BINDING')
    require({r['candidate_id'] for r in reference_document['pairs']}=={p['candidate_id'] for p in cohort['pairs']},'REFERENCE_COHORT_BINDING')
    members=((p['candidate_id'],r['source_direction'],r['target_direction'],r['horizon_seconds']) for p in reference_document['pairs'] for r in p['relations'])
    cap=PostInductionCapabilityV2(_ISSUER,run,files,hashes,evaluation['reference_hash'],members);cap.replay()
    publish(run/'evaluation/NUMERIC_BINDING_STARTED.json',seal({'policy':POLICY,'output_bundle_hash':bundle['self_hash'],'admissions_hash':admissions['self_hash'],'train3_evaluation_hash':evaluation['self_hash'],'provider_calls_allowed':False}))
    return cap


def validate_roles(roles):
    require(type(roles) is dict and set(roles)==set(V4_NUMERIC_ROLES),'NUMERIC_ROLE_CLOSURE')
    require(all(type(v) in (int,float) and math.isfinite(v) for v in roles.values()),'NONFINITE_NUMERIC_AUTHORITY')
    require(all(roles[k]>0 for k in ('source_step_threshold','source_stability_tolerance','target_noise_scale')),'NUMERIC_SCALE_INVALID')
    require(all(roles[k]==float(v) for k,v in FROZEN_WINDOW_VALUES),'FROZEN_WINDOW_MISMATCH')


def fixed_roles(source_summary,target_summary,direction):
    result=roles_from_summary(source_summary,target_summary,direction,FIXED_ALIAS);validate_roles(result);return result


def load_numeric_cache(cap,private,hashes):
    require(type(cap) is PostInductionCapabilityV2,'POST_INDUCTION_REQUIRED');cap.replay()
    result={}
    for split in ('train1','train2'):
        relative=split+'/numeric_roles.json';path=private/relative
        raw=path.read_bytes();require(sha256(raw).hexdigest()==hashes[relative],'NUMERIC_CACHE_IDENTITY')
        doc=json.loads(raw);require(doc['split']==split,'NUMERIC_SPLIT')
        result[split]=doc['roles']
    return result


def bind_guard_rule(cap,admission,rule_index,*,pair,reference,reference_hash,train1,train2):
    require(type(cap) is PostInductionCapabilityV2,'POST_INDUCTION_REQUIRED');cap.replay()
    require(type(admission) is VerifiedAdmission,'GUARD_ADMISSION_REQUIRED');admission.replay()
    require(admission.receipt['self_hash'] in cap.admission_hashes and reference_hash==cap.reference_hash,'FROZEN_ADMISSION_REFERENCE_REQUIRED')
    require(admission.candidate_id=='EXP03B-CAND-'+digest({'source':pair[0],'target':pair[1]})[:20],'GUARD_PAIR_BINDING')
    rule=admission.proposal.rules[rule_index]
    require(rule.semantic in reference[admission.candidate_id] and (admission.candidate_id,rule.semantic.source_direction,rule.semantic.target_direction,rule.semantic.horizon_seconds) in cap.reference_members,'TRAIN3_CONFIRMATION_REQUIRED')
    selected=(rule.semantic.source_direction,FIXED_ALIAS);common=(rule.semantic.source_direction,'NUM-000')
    for table in (train1,train2):
        for key in (selected,common):require(key in table,'INCOMPLETE_NUMERIC_AUTHORITY');validate_roles(table[key])
    roles=pooled_roles(train1[selected],train2[selected],train2_status='ACCEPTED');baseline=pooled_roles(train1[common],train2[common],train2_status='ACCEPTED')
    numhash=lambda table:digest([{'key':k,'values':table[k]} for k in sorted((selected,common))])
    return GuardRuleInput(admission.candidate_id,*pair,rule.semantic,FIXED_ALIAS,tuple(sorted(roles.items())),tuple(sorted(baseline.items())),admission.receipt['self_hash'],reference_hash,numhash(train1),numhash(train2))
