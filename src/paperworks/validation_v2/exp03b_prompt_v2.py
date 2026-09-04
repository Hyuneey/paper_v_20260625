"""Semantic request serializer. No hidden/numeric authority, credentials or network."""
import math
import re
from .exp03b_semantic_v2 import SOURCES,TARGETS,HORIZONS,SemanticTupleV1,StructuralTupleEvidenceV1,parse_proposal,require,encoded,digest,validate_rows
from .exp03b_firewall_v2 import assert_clean,STRUCTURAL_COLUMNS,GDN_COLUMNS

MODEL='gpt-5.4-mini-2026-03-17'
ENDPOINT='https://api.openai.com/v1/responses'
OUTPUT_CAP=2048
PROPOSAL_BYTE_CAP=768
FEEDBACK_BYTE_CAP=2048
ISSUE_CODES=('LOW_SOURCE_SUPPORT','LOW_TARGET_CONSISTENCY','LOW_EFFECT','OPPOSITE_DIRECTION_COMPETES','HORIZON_UNSUPPORTED','HORIZON_UNSTABLE','RULE_NOT_JUSTIFIED','RULE_SET_INCOMPLETE','NO_RULE_NOT_JUSTIFIED','EVIDENCE_REFERENCE_INVALID','DUPLICATE_SOURCE_DIRECTION')
SYSTEM_PROMPT='''Infer a semantic relational Rule set for the fixed source-target pair from the supplied normal evidence only. Return only the JSON schema. RULE_SET contains at most one Rule per source direction and at most two Rules total; otherwise explicitly return NO_RULE. Source and target are bound externally. Do not invent variables, thresholds, code, or causal claims.
Assess all 20 source-direction, target-direction and horizon tuples. Initial train1 criteria: isolated complete support >=5, consistency >=0.60, robust effect >=2.0, and consistency strictly greater than opposite consistency at the same source direction/horizon. Rank passing tuples per source direction by greater consistency, greater effect, greater support, then smaller horizon. Cite applicable evidence_slice_ids. STAT and GDN are normal predictive evidence, not causal truth or hard acceptance authority. GDN attention is shared encoder evidence, not horizon-specific attention. Null edge effect means graph-ineligible/unavailable, not zero.
The hidden second-normal-file verifier uses support>=5, consistency>=0.60, effect>=1.0, strict opposite competition, exact preferred tuple and horizon stability, and completeness over supported source directions. It does not choose an executable calibration here. On bounded feedback, revise the same pair from issue codes and the single authorized aggregate evidence slice containing all alternatives. Do not request unlisted data or tools. Stop immediately on ACCEPTED; no fourth generation.'''


def output_schema():
    fields={'source_direction':{'type':'string','enum':list(SOURCES)},'target_direction':{'type':'string','enum':list(TARGETS)},'horizon_seconds':{'type':'integer','enum':list(HORIZONS)},'evidence_slice_ids':{'type':'array','items':{'type':'string','pattern':'^EV-[0-9a-f]{24}$'},'minItems':1,'maxItems':4}}
    return {'type':'object','additionalProperties':False,'properties':{'decision':{'type':'string','enum':['RULE_SET','NO_RULE']},'rules':{'type':'array','maxItems':2,'items':{'type':'object','additionalProperties':False,'properties':fields,'required':list(fields)}}},'required':['decision','rules']}


def validate_projection(e):
    require(type(e) is dict and set(e)=={'candidate_id','source','target','split','structural_columns','structural_rows','stat_association','gdn_columns','gdn_rows'},'CLOSED_PROVIDER_SCHEMA')
    require(e['split']=='train1','INITIAL_PROMPT_SPLIT')
    require(all(type(e[k]) is str and re.fullmatch(r'P1_[A-Z0-9]+',e[k]) for k in ('source','target')),'FEATURE_FORMAT')
    require(e['candidate_id']=='EXP03B-CAND-'+digest({'source':e['source'],'target':e['target']})[:20],'PAIR_IDENTITY')
    require(e['structural_columns']==STRUCTURAL_COLUMNS and e['gdn_columns']==GDN_COLUMNS,'EVIDENCE_COLUMNS')
    require(type(e['structural_rows']) in (list,tuple) and all(type(r) in (list,tuple) and len(r)==8 for r in e['structural_rows']),'STRUCTURAL_ROW')
    validate_rows(tuple(StructuralTupleEvidenceV1(SemanticTupleV1(*r[:3]),*r[3:]) for r in e['structural_rows']))
    require(type(e['stat_association']) in (int,float) and math.isfinite(e['stat_association']),'STAT_NONFINITE')
    require(type(e['gdn_rows']) in (list,tuple) and len(e['gdn_rows'])==5 and all(len(r)==4 for r in e['gdn_rows']) and tuple(r[0] for r in e['gdn_rows'])==HORIZONS,'GDN_ROWS')
    require(all(x is None or type(x) in (int,float) and math.isfinite(x) for r in e['gdn_rows'] for x in r[1:]),'GDN_NONFINITE')
    assert_clean(e)


def validate_repair(r):
    require(type(r) is dict and set(r)=={'previous_proposal','feedback','retrieval'},'REPAIR_ENVELOPE')
    parse_proposal(r['previous_proposal']);require(len(encoded(r['previous_proposal']))<=PROPOSAL_BYTE_CAP,'REPAIR_PROPOSAL_BYTE_CAP')
    f=r['feedback'];require(type(f) is dict and set(f)=={'proposal_hash','issues','remaining_call_budget','evidence_retrieval_authorization'},'CLOSED_FEEDBACK_SCHEMA')
    require(f['proposal_hash']==digest(r['previous_proposal']) and type(f['remaining_call_budget']) is int and f['remaining_call_budget'] in (1,2),'FEEDBACK_PROPOSAL_BINDING')
    require(f['evidence_retrieval_authorization']=='ONE_STRUCTURAL_SLICE_ALL_ALTERNATIVES_CANONICAL','RETRIEVAL_AUTHORIZATION')
    require(type(f['issues']) is list and 1<=len(f['issues'])<=17 and all(type(i) is dict and set(i)=={'failing_rule_index','issue_code'} and type(i['failing_rule_index']) is int and i['failing_rule_index'] in (-1,0,1) and i['issue_code'] in ISSUE_CODES for i in f['issues']),'FEEDBACK_ISSUE_SCHEMA')
    require(len(encoded(f))<=FEEDBACK_BYTE_CAP,'FEEDBACK_BYTE_CAP')
    q=r['retrieval']
    if q is not None:
        require(type(q) is dict and set(q)=={'split','dimension','alternatives','retrieval_hash'} and q['split']=='train2' and q['dimension']=='temporal_structure','CLOSED_RETRIEVAL_SCHEMA')
        require(q['retrieval_hash']==digest({k:v for k,v in q.items() if k!='retrieval_hash'}),'RETRIEVAL_HASH')
        require(type(q['alternatives']) is list and all(type(v) is dict and set(v)=={'semantic','support','consistency','opposite_consistency','effect','evidence_slice_id'} and set(v['semantic'])=={'source_direction','target_direction','horizon_seconds'} for v in q['alternatives']),'RETRIEVAL_FIELDS')
        rows=tuple(StructuralTupleEvidenceV1(SemanticTupleV1(**v['semantic']),**{k:x for k,x in v.items() if k!='semantic'}) for v in q['alternatives'])
        validate_rows(rows);require(tuple(r.semantic for r in rows)==tuple(sorted(r.semantic for r in rows)),'RETRIEVAL_ORDER')
    assert_clean(r)


def request_body(evidence, *, repair=None):
    validate_projection(evidence); content={'evidence':evidence}
    if repair is not None:validate_repair(repair);content['repair']=repair
    return {'model':MODEL,'instructions':SYSTEM_PROMPT,'input':encoded(content).decode(),'reasoning':{'effort':'none'},'temperature':.7,'top_p':1.,'max_output_tokens':OUTPUT_CAP,'store':False,'service_tier':'default','tools':[],'stream':False,'text':{'format':{'type':'json_schema','name':'exp03b_semantic_rule_set_v2','strict':True,'schema':output_schema()}}}


def execution_config():
    return {'model':MODEL,'endpoint':ENDPOINT,'reasoning':{'effort':'none'},'temperature':.7,'top_p':1.,'output_cap':OUTPUT_CAP,'timeout_seconds':60,'automatic_retries':0,'scientific_concurrency':1,'store':False,'service_tier':'default','tools':[],'seed':None,'repair_history':'LATEST_PROPOSAL_ONE_FEEDBACK_ONE_STRUCTURAL_SLICE_STATELESS','T2_maximum_generations':3,'T2_early_stop':'IMMEDIATE_ACCEPTED_OR_NONREPAIRABLE_REJECTION','probe':'FIRST_SCHEDULED_CALL_COUNTS_TOWARD_BUDGET_NO_SEPARATE_SCIENTIFIC_CALL','post_induction_provider_calls':'PROHIBITED'}
