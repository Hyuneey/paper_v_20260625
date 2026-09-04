"""Offline exact-payload profiling. No credential, API or capability probe."""
import argparse
from decimal import Decimal, ROUND_CEILING
import json
import math
import statistics
import sys
import os
import tempfile
from hashlib import sha1
from pathlib import Path
from unittest.mock import patch
from xver_execution_common import ROOT, PUB, private_root, document, committed, head, publish, seal, require, digest, sha256_file
from run_xver_semantic_execution_v1 import replay_authority, run_directory
from paperworks.validation_v2.exp03b_contract_v1 import encoded
from paperworks.validation_v2.exp03b_prompt_v2 import SYSTEM_PROMPT, OUTPUT_CAP, PROPOSAL_BYTE_CAP, FEEDBACK_BYTE_CAP, ISSUE_CODES, output_schema
from paperworks.validation_v2.xver_prompt_v1 import request_body, execution_config, validate_global_retrieval


def offline_encoder():
    sys.path.insert(0,str(ROOT/'.venv/exp03b-tokenizer'))
    import tiktoken
    require(tiktoken.__version__=='0.12.0','FROZEN_TOKENIZER_VERSION')
    url='https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken'
    expected='446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d'
    cache=Path(os.environ.get('TIKTOKEN_CACHE_DIR',os.environ.get('DATA_GYM_CACHE_DIR',str(Path(tempfile.gettempdir())/'data-gym-cache'))))/sha1(url.encode()).hexdigest()
    require(cache.is_file() and sha256_file(cache)==expected,'OFFLINE_TOKENIZER_CACHE_REQUIRED')
    raw=cache.read_bytes()
    def only_cached(blobpath,expected_hash=None):
        require(blobpath==url and expected_hash==expected,'TOKENIZER_NETWORK_FORBIDDEN')
        return raw
    with patch('tiktoken.load.read_file_cached',side_effect=only_cached):encoder=tiktoken.get_encoding('o200k_base')
    return tiktoken,encoder,expected


def freeze_version(version):
    tiktoken,encoder,rank_hash=offline_encoder()
    authority,context,candidate,roles,pairs=replay_authority(version)
    serializer=document(PUB/'XVER_PROVIDER_SERIALIZER_FREEZE_V1.json');committed(PUB/'XVER_PROVIDER_SERIALIZER_FREEZE_V1.json')
    for path,h in serializer['implementation_hashes'].items():require(sha256_file(ROOT/path)==h,'FROZEN_SERIALIZER_CHANGED')
    require(serializer['configuration']==execution_config(),'FROZEN_PROVIDER_SETTINGS_CHANGED')
    for p in ('scripts/freeze_xver_provider_v1.py','src/paperworks/validation_v2/xver_prompt_v1.py','src/paperworks/validation_v2/exp03b_prompt_v2.py','research_control_center/validation_v2/xver_normal/PROVIDER_PRICE_AUTHORITY_V1.md'):committed(ROOT/p)
    directory=run_directory(version);evidence=document(directory/'EVIDENCE_FROZEN.json')
    portfolio=document(PUB/f'HAI{version[:2]}_T0_PORTFOLIO_AUTHORITY_V1.json')
    require(portfolio['evidence_hash']==evidence['self_hash'],'PORTFOLIO_EVIDENCE_CLOSURE')
    require(evidence['execution_hash']==portfolio['execution_hash']==authority['self_hash'] and evidence['version']==portfolio['version']==version and evidence['candidate_hash']==portfolio['candidate_hash']==candidate['self_hash'],'PROVIDER_EXECUTION_COHORT_BINDING')
    ids={'EXP03B-CAND-'+digest({'source':s,'target':t})[:20] for s,t in pairs}
    require(evidence['N']==portfolio['candidate_N']==len(ids) and len(evidence['records'])==2*len(ids) and {(r['candidate_id'],r['split']) for r in evidence['records']}=={(cid,s) for cid in ids for s in ('train1','train2')},'PROVIDER_SLOT_CLOSURE')
    require(tiktoken.__version__=='0.12.0','FROZEN_TOKENIZER_VERSION')
    rows=[]
    count=lambda x:len(encoder.encode(encoded(x).decode()))
    for source,target in pairs:
        cid='EXP03B-CAND-'+digest({'source':source,'target':target})[:20]
        ep=directory/'provider'/f'{cid}.json';qp=directory/'retrieval'/f'{cid}.json'
        expected={r['split']:r for r in evidence['records'] if r['candidate_id']==cid}
        require(sha256_file(ep)==expected['train1']['pack_hash'] and sha256_file(qp)==expected['train2']['pack_hash'],'FROZEN_PROVIDER_PACK_BYTES')
        e=json.loads(ep.read_text());q=json.loads(qp.read_text());validate_global_retrieval(q)
        initial=request_body(e);publish(directory/'requests'/f'{cid}.initial.json',initial)
        # Serialization-only maximal shape, not T0/output/reference or natural error injection.
        ids=sorted((r[7] for r in e['structural_rows']),key=lambda x:(-len(encoder.encode(x)),x))[:4]
        proposal={'decision':'RULE_SET','rules':[{'source_direction':s,'target_direction':'increase','horizon_seconds':60,'evidence_slice_ids':ids} for s in ('step_down','step_up')]}
        issues=[{'failing_rule_index':i,'issue_code':c} for i in (0,1) for c in ISSUE_CODES[:8]]+[{'failing_rule_index':-1,'issue_code':'RULE_SET_INCOMPLETE'}]
        repairs=[]
        for remaining in (2,1):
            feedback={'proposal_hash':digest(proposal),'issues':issues,'remaining_call_budget':remaining,'evidence_retrieval_authorization':'ONE_STRUCTURAL_SLICE_ALL_ALTERNATIVES_CANONICAL'}
            repairs.append(request_body(e,repair={'previous_proposal':proposal,'feedback':feedback,'retrieval':q}))
        byte_bound=len(encoded(initial))+2*(len(encoded(q))+PROPOSAL_BYTE_CAP+FEEDBACK_BYTE_CAP+128)
        rows.append({'candidate_id':cid,'initial_tokens':count(initial),'initial_bytes':len(encoded(initial)),'repair2_profile_tokens':count(repairs[0]),'repair3_profile_tokens':count(repairs[1]),'maximum_repair_byte_bound':max(byte_bound,*map(lambda r:len(encoded(r)),repairs)),'request_hash':digest(initial),'provider_pack_hash':sha256_file(ep),'retrieval_pack_hash':sha256_file(qp)})
    require(len(rows)==candidate['candidate_count'],'TOKEN_COHORT_COUNT')
    profile=seal({'schema':'xver_T2_local_token_profile_v1','version':version,'tokenizer_version':tiktoken.__version__,'encoding':'o200k_base','BPE_rank_hash':rank_hash,'N':len(rows),'minimum_initial_input_tokens':min(r['initial_tokens'] for r in rows),'median_initial_input_tokens':statistics.median(r['initial_tokens'] for r in rows),'maximum_initial_input_tokens':max(r['initial_tokens'] for r in rows),'initial_total_input_tokens':sum(r['initial_tokens'] for r in rows),'maximum_repair_profile_input_tokens':max(max(r['repair2_profile_tokens'],r['repair3_profile_tokens']) for r in rows),'maximum_shape_schedule_profile_input_tokens':sum(r['initial_tokens']+r['repair2_profile_tokens']+r['repair3_profile_tokens'] for r in rows),'profiles':rows,'boundary':'LOCAL_TOKENIZER_ESTIMATE_NOT_SERVER_METERING_NOT_MAX_BPE_PROOF','provider_calls':0})
    publish(PUB/f'HAI{version[:2]}_T2_TOKEN_PROFILE_V1.json',profile)
    framing=512
    caps={'initial':math.ceil((max(r['initial_bytes'] for r in rows)+framing)/1024)*1024,'repair':math.ceil((max(r['maximum_repair_byte_bound'] for r in rows)+framing)/1024)*1024}
    n=len(rows);calls=3*n;incap=n*(caps['initial']+2*caps['repair']);outcap=calls*OUTPUT_CAP
    cost=((Decimal(incap)*Decimal('.75')+Decimal(outcap)*Decimal('4.50'))/1000000).quantize(Decimal('.01'),rounding=ROUND_CEILING)
    config=execution_config()
    budget=seal({'schema':'xver_T2_provider_budget_v1','version':version,'status':'USER_DECISION_REQUIRED','gate':'DG-XVER-PROVIDER','N':n,'repetitions':1,'arms':['T2'],'maximum_calls':calls,'calls_if_all_accept_first':n,'hard_phase_input_caps':caps,'maximum_input_tokens':incap,'output_cap_per_call':OUTPUT_CAP,'maximum_output_tokens':outcap,'maximum_total_tokens':incap+outcap,'prospective_standard_price_ceiling_usd':str(cost),'cost_status':'VERIFIED_OFFICIAL_PUBLISHED_PRICE_NOT_ACTUAL_BILL','price_input_per_million':'0.75','price_output_per_million':'4.50','price_authority_hash':sha256_file(PUB/'PROVIDER_PRICE_AUTHORITY_V1.md'),'price_source':'https://developers.openai.com/api/docs/models/gpt-5.4-mini','framing_allowance':framing,'hard_bound_method':'CLOSED_ASCII_UTF8_BYTES_JSON_ESCAPING_PLUS_FRAMING_RESERVE_RECEIPT_FIRST_METERING_REQUIRED','profile_hash':profile['self_hash'],'evidence_hash':evidence['self_hash'],'config':config,'config_hash':digest(config),'prompt_hash':digest(SYSTEM_PROMPT),'output_schema_hash':digest(output_schema()),'source_commit':head(),'source_hashes':{p:sha256_file(ROOT/p) for p in ('scripts/freeze_xver_provider_v1.py','src/paperworks/validation_v2/xver_prompt_v1.py','src/paperworks/validation_v2/exp03b_prompt_v2.py')},'provider_calls':0,'credential_reads':0,'capability_probes':0,'prior_approval_inherited':False})
    publish(PUB/f'HAI{version[:2]}_T2_PROVIDER_BUDGET_V1.json',budget)
    publish(directory/'PROVIDER_PREPARATION_FROZEN.json',seal({'version':version,'budget_hash':budget['self_hash'],'profile_hash':profile['self_hash'],'evidence_hash':evidence['self_hash'],'provider_calls_authorized':False}))
    print(json.dumps({'phase':'PROVIDER_FROZEN_USER_DECISION_REQUIRED','version':version,'maximum_calls':calls,'hard_total_tokens':incap+outcap,'prospective_cost_ceiling_usd':str(cost)}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--version',choices=('22.04','21.03'),required=True);args=p.parse_args()
    try:freeze_version(args.version)
    except Exception as error:
        print(json.dumps({'status':'BLOCKED_PROVIDER_PROJECTION','error_type':type(error).__name__,'code':str(error) if type(error) is ValueError and str(error).replace('_','').isalnum() else 'REDACTED'}),flush=True);raise SystemExit(2)
