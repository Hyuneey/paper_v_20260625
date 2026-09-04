"""Offline reduction of already-frozen split-pure evidence. Never reads raw data."""
from pathlib import Path
from dataclasses import asdict
from hashlib import sha256
import argparse,json,sys,statistics,math
from decimal import Decimal,ROUND_CEILING
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.venv/exp03b-tokenizer'))
from paperworks.validation_v2.exp03b_contract_v1 import encoded,digest,require
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay
from paperworks.validation_v2.exp03b_codec_v2 import structural
from paperworks.validation_v2.exp03b_semantic_v2 import t0,proposal_document
from paperworks.validation_v2.exp03b_firewall_v1 import SplitPurePredictiveEvidenceV1
from paperworks.validation_v2.exp03b_firewall_v2 import project,render
from paperworks.validation_v2.exp03b_prompt_v2 import request_body,execution_config,output_schema,SYSTEM_PROMPT,OUTPUT_CAP,PROPOSAL_BYTE_CAP,FEEDBACK_BYTE_CAP,ISSUE_CODES
PUBLIC=ROOT/'research_control_center/validation_v2/exp03b'
PRIVATE=ROOT/'artifacts/validation_v2/exp03b/private'


def read(path):return json.loads(path.read_text())
def cohort():
    c=read(PUBLIC/'EXP03B_COHORT_AUTHORITY_V1.json');replay(c);require(c['count']==len(c['pairs'])>0,'COHORT_REPLAY');return c
def old_read(relative):
    freeze=read(PUBLIC/'EXP03B_FINAL_PREPARATION_FREEZE_V2.json');replay(freeze)
    p=PRIVATE/relative;raw=p.read_bytes();require(sha256(raw).hexdigest()==freeze['private_input_hashes'][relative],'IMMUTABLE_INPUT_HASH')
    return json.loads(raw)


def reduce(split):
    require(split in ('train1','train2'),'SPLIT_SCOPE');records=[]
    for pair in cohort()['pairs']:
        cid=pair['candidate_id'];relative=f'{split}/structural/{cid}.json'
        e=structural(old_read(relative),split)
        h=publish(PRIVATE/f'semantic_v2/{split}/structural/{cid}.json',asdict(e))
        row={'candidate_id':cid,'structural_file_hash':h,'structural_row_count':len(e.rows),'numeric_rows':0}
        if split=='train1':
            p=old_read(f'train1/predictive/{cid}.json')
            predictive=SplitPurePredictiveEvidenceV1(**{**p,'gdn_rows':tuple(tuple(x) for x in p['gdn_rows'])})
            payload=render(project(e,predictive))
            row['provider_file_hash']=publish(PRIVATE/f'semantic_v2/train1/provider/{cid}.json',payload)
            row['t0_file_hash']=publish(PRIVATE/f'semantic_v2/train1/t0/{cid}.json',proposal_document(t0(e)))
            row['request_file_hash']=publish(PRIVATE/f'semantic_v2/train1/requests/{cid}.json',request_body(payload))
        records.append(row)
    publish(PUBLIC/f'EXP03B_{split.upper()}_SEMANTIC_RECEIPT_V2.json',seal({'schema':'exp03b_semantic_reduction_receipt_v2','split':split,'cohort_hash':cohort()['self_hash'],'records':records,'prior_freeze_hash':read(PUBLIC/'EXP03B_FINAL_PREPARATION_FREEZE_V2.json')['self_hash'],'scientific_recomputation':False,'raw_file_reads':0,'provider_calls':0,'credential_reads':0,'private_exposures':0}))
    print(json.dumps({'phase':split,'status':'PASS','pair_count':len(records),'numeric_provider_rows':0}))


def profile():
    import tiktoken
    encoder=tiktoken.get_encoding('o200k_base');rows=[]
    for pair in cohort()['pairs']:
        cid=pair['candidate_id'];e=read(PRIVATE/f'semantic_v2/train1/provider/{cid}.json')
        # Each process only loads an already authorized bounded train2 structural slice.
        hidden=read(PRIVATE/f'semantic_v2/train2/structural/{cid}.json')
        alternatives=sorted(hidden['rows'],key=lambda r:(r['semantic']['source_direction'],r['semantic']['target_direction'],r['semantic']['horizon_seconds']))
        q= {'split':'train2','dimension':'temporal_structure','alternatives':alternatives};q={**q,'retrieval_hash':digest(q)}
        # Synthetic maximal-shape proposal is for serialization profiling, NOT a
        # natural scientific draw, T0 outcome, or provider output.
        ids=sorted([r[7] for r in e['structural_rows']],key=lambda x:(-len(encoder.encode(x)),x))[:4]
        p={'decision':'RULE_SET','rules':[{'source_direction':s,'target_direction':'increase','horizon_seconds':60,'evidence_slice_ids':ids} for s in ('step_down','step_up')]}
        issues=[{'failing_rule_index':i,'issue_code':c} for i in (0,1) for c in ISSUE_CODES[:8]]+[{'failing_rule_index':-1,'issue_code':'RULE_SET_INCOMPLETE'}]
        initial=request_body(e);repair=[]
        for remaining in (2,1):
            f={'proposal_hash':digest(p),'issues':issues,'remaining_call_budget':remaining,'evidence_retrieval_authorization':'ONE_STRUCTURAL_SLICE_ALL_ALTERNATIVES_CANONICAL'}
            repair.append(request_body(e,repair={'previous_proposal':p,'feedback':f,'retrieval':q}))
        count=lambda x:len(encoder.encode(encoded(x).decode()))
        # JSON-in-input quoting is counted in a constructed envelope with the full
        # closed-schema proposal/feedback byte allowances. These ASCII objects have
        # bounded escaping; 2x permits every quote/backslash to be escaped.
        empty=request_body(e)
        hard_repair=len(encoded(empty))+2*(len(encoded(q))+PROPOSAL_BYTE_CAP+FEEDBACK_BYTE_CAP+128)
        rows.append({'candidate_id':cid,'initial_local_tokens':count(initial),'repair2_profile_local_tokens':count(repair[0]),'repair3_profile_local_tokens':count(repair[1]),'initial_serialized_bytes':len(encoded(initial)),'maximum_repair_serialized_byte_bound':max(hard_repair,*map(lambda x:len(encoded(x)),repair)),'initial_request_hash':digest(initial)})
    N=len(rows);R=3;calls=N*R*7;framing=512
    caps={'initial':math.ceil((max(r['initial_serialized_bytes'] for r in rows)+framing)/1024)*1024,'repair':math.ceil((max(r['maximum_repair_serialized_byte_bound'] for r in rows)+framing)/1024)*1024}
    initial_tokens=sum(r['initial_local_tokens'] for r in rows)
    t1=R*initial_tokens;t1b=R*3*initial_tokens;t2=R*sum(r['initial_local_tokens']+r['repair2_profile_local_tokens']+r['repair3_profile_local_tokens'] for r in rows)
    maximum_input=N*R*(5*caps['initial']+2*caps['repair']);maximum_output=calls*OUTPUT_CAP
    cost=((Decimal(maximum_input)*Decimal('.75')+Decimal(maximum_output)*Decimal('4.5'))/1000000).quantize(Decimal('.01'),rounding=ROUND_CEILING)
    profile_doc=seal({'schema':'exp03b_semantic_local_token_profile_v2','tokenizer':'tiktoken==0.12.0','encoding':'o200k_base','profiles':rows,'minimum_initial_tokens':min(r['initial_local_tokens'] for r in rows),'median_initial_tokens':statistics.median(r['initial_local_tokens'] for r in rows),'maximum_initial_tokens':max(r['initial_local_tokens'] for r in rows),'T1_input_estimate':t1,'T1B_input_estimate':t1b,'T2_maximal_shape_input_estimate':t2,'schedule_maximal_shape_input_estimate':t1+t1b+t2,'estimate_boundary':'Exact local tokenizer counts of frozen initial requests and synthetic maximal-shape repair profiles; not server metering and not a proof of max BPE count over all future proposals. Independent byte/framing hard ceilings apply.','provider_calls':0,'credential_reads':0})
    publish(PUBLIC/'EXP03B_PAYLOAD_TOKEN_PROFILE_V2.json',profile_doc)
    config=execution_config()
    budget=seal({'schema':'exp03b_provider_budget_v2','status':'USER_DECISION_REQUIRED','gate':'DG-03B_REVISED','model':config['model'],'N':N,'R':R,'candidate_ids':[p['candidate_id'] for p in cohort()['pairs']],'T1_calls':N*R,'T1B_calls':N*R*3,'T2_calls':N*R*3,'maximum_calls':calls,'phase_input_caps':caps,'input_tokens_per_call_cap':max(caps.values()),'output_tokens_per_call_cap':OUTPUT_CAP,'maximum_input_tokens':maximum_input,'maximum_output_tokens':maximum_output,'maximum_total_tokens':maximum_input+maximum_output,'standard_api_cost_ceiling_usd':str(cost),'price_per_million':{'input':'0.75','output':'4.50'},'price_source':'https://developers.openai.com/api/docs/models/gpt-5.4-mini','framing_allowance':framing,'hard_bound_method':'Closed ASCII schema UTF8 byte bounds, JSON escaping allowance, 512 token service framing reserve; receipt-first metering must pass; phase-aware pretransport cumulative reservation.','local_profile_hash':profile_doc['self_hash'],'minimum_scheduled_calls_if_all_T2_accept_first':N*R*5,'config':config,'config_hash':digest(config),'prompt_hash':digest(SYSTEM_PROMPT),'schema_hash':digest(output_schema()),'provider_calls':0,'credential_reads':0,'capability_probes':0,'prior_approval_inherited':False,'supersedes_budget_hash':read(PUBLIC/'EXP03B_PROVIDER_BUDGET_V1.json')['self_hash']})
    publish(PUBLIC/'EXP03B_PROVIDER_BUDGET_V2.json',budget)
    publish(PUBLIC/'EXP03B_OUTPUT_SCHEMA_V2.json',output_schema())
    publish(PUBLIC/'EXP03B_PROMPT_FREEZE_V2.json',seal({'system_prompt':SYSTEM_PROMPT,'config':config,'output_schema':output_schema(),'request_profile_hash':profile_doc['self_hash']}))
    print(json.dumps({'status':'USER_DECISION_REQUIRED','pairs':N,'local_initial_min':profile_doc['minimum_initial_tokens'],'local_initial_median':profile_doc['median_initial_tokens'],'local_initial_max':profile_doc['maximum_initial_tokens'],'local_schedule_estimate':t1+t1b+t2,'hard_input_cap':maximum_input,'hard_output_cap':maximum_output,'hard_total_cap':maximum_input+maximum_output,'cost_ceiling_usd':str(cost),'phase_caps':caps}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=('train1','train2','profile'));args=p.parse_args()
    try:profile() if args.phase=='profile' else reduce(args.phase)
    except Exception as e:print(json.dumps({'status':'FAIL_CLOSED','error_type':type(e).__name__}));raise SystemExit(2)
