"""Future local evaluation only after every arm output is durably frozen."""
from pathlib import Path
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
import json
from paperworks.validation_v2.exp03b_semantic_v2 import require,digest,parse_proposal,SemanticTupleV1
from paperworks.validation_v2.exp03b_custody_v1 import replay,seal,publish,load_normal
from paperworks.validation_v2.exp03b_codec_v2 import structural
from paperworks.validation_v2.exp03b_hidden_v2 import Train2HiddenVerifierAuthorityV2 as Train2HiddenVerifierAuthorityV1,retrieval,feedback,select_t1b,VerifierResultV1
from paperworks.validation_v2.exp03b_hidden_v2 import verify
from paperworks.validation_v2.exp03b_execution_v2 import admit
from paperworks.validation_v2.exp03b_binder_v2 import bind_guard_rule,run_guard_portfolio,authorize_binding,load_numeric_cache
from paperworks.validation_v2.exp03b_guard_v1 import Train4HiddenGuardAuthorityV1
from paperworks.validation_v2.exp03b_reporting_v2 import report,repair_pair_sets,paired_comparison
from paperworks.validation_v2.exp03b_metrics_v1 import disposition
from paperworks.validation_v2.exp03b_conversion import convert
from paperworks.validation_v2.exp03b_provider_gate_v2 import ProviderCallGate,validate_call_inventory
from paperworks.validation_v2.exp03b_prompt_v2 import request_body
from paperworks.validation_v2.exp03b_semantic_v2 import proposal_document
from execute_exp03b_provider_v2 import response_proposal,ParsedResponseFailure
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'research_control_center/validation_v2/exp03b'
PRIVATE=ROOT/'artifacts/validation_v2/exp03b/private'

def read(path):return json.loads(path.read_text())
def rational(value):
    if isinstance(value,Fraction):return {'numerator':value.numerator,'denominator':value.denominator}
    if isinstance(value,SemanticTupleV1):return asdict(value)
    if isinstance(value,dict):return {str(k):rational(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [rational(v) for v in value]
    return value

def main():
    freeze=read(PUBLIC/'EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json');replay(freeze)
    for name,h in freeze['implementation_hashes'].items():require(sha256((ROOT/name).read_bytes()).hexdigest()==h,'EVALUATOR_CODE_CHANGED')
    run=PRIVATE/'provider_execution_v2'
    bundle=read(run/'ALL_ARM_OUTPUTS_FROZEN.json');replay(bundle)
    require(bundle['train3_evaluation_allowed'] and not (run/'SINGLE_WRITER.lock').exists(),'PROVIDER_WRITER_STILL_ACTIVE')
    cohort=read(PUBLIC/'EXP03B_COHORT_AUTHORITY_V1.json');replay(cohort)
    budget=read(PUBLIC/'EXP03B_PROVIDER_BUDGET_V2.json');replay(budget)
    require(validate_call_inventory(run,budget['maximum_calls'])==bundle['calls'],'FROZEN_CALL_COUNT')
    approval=read(run/'USER_APPROVAL_RECEIPT.json');replay(approval)
    gate=ProviderCallGate(budget,approval,freeze['self_hash']);call_rows={}
    for index in range(1,bundle['calls']+1):
        req=read(run/'calls'/f'{index:04d}.request.json');replay(req)
        res=read(run/'calls'/f'{index:04d}.response.json');replay(res)
        receipt=read(run/'calls'/f'{index:04d}.receipt.json');replay(receipt)
        require(res['request_hash']==digest(req['request'])==req['reservation']['request_hash'],'CALL_RESPONSE_BINDING')
        reservation=gate.reserve(slot=req['slot'],request=req['request'],input_upper_bound=req['input_upper_bound'])
        require(asdict(reservation)==req['reservation'],'CALL_RESERVATION_REPLAY')
        actual=gate.reconcile(input_tokens=res['usage']['input_tokens'],output_tokens=res['usage']['output_tokens'],response_hash=digest(res['response']),model=res['response']['model'],latency=res['latency_seconds'])
        require(seal(actual)==receipt,'CALL_RECEIPT_REPLAY')
        if index==1:
            probe=read(run/'ONE_CALL_CAPABILITY_RECEIPT.json');replay(probe)
            require(probe['status']=='PASS' and probe['call_receipt_hash']==digest(actual) and probe['budget_hash']==budget['self_hash'],'PROBE_REPLAY')
            response_proposal(res['response']);gate.accept_one_call_receipt(digest(actual),persisted_and_replayed=True,privacy_pass=True,schema_pass=True)
        call_rows[req['slot']]=(req,res)
    expected_hashes=[]
    for pair in cohort['pairs']:
        for arm in ('T1','T1-B','T2'):
            for repeat in (1,2,3):
                row=read(run/'outputs'/f"{pair['candidate_id']}.{arm}.R{repeat}.json");replay(row)
                require((row['candidate_id'],row['arm'],row['repeat'])==(pair['candidate_id'],arm,repeat),'OUTPUT_SLOT_IDENTITY')
                expected_hashes.append(row['self_hash'])
    require(len(expected_hashes)==bundle['count']==9*cohort['count'] and expected_hashes==bundle['terminal_hashes'],'OUTPUT_CLOSURE_BEFORE_REFERENCE')
    publish(run/'PROVIDER_PHASE_CLOSED.json',seal({'output_bundle_hash':bundle['self_hash'],'execution_freeze_hash':freeze['self_hash'],'provider_calls_allowed':False}))
    for name,h in freeze['provider_input_hashes'].items():require(sha256((PRIVATE/name).read_bytes()).hexdigest()==h,'PRIVATE_INPUT_CHANGED')
    outputs={a:{} for a in ('T0','T1','T1-B','T2')};terminals={a:{} for a in outputs};rows=[];repairs=[];hashes=[]
    for pair in cohort['pairs']:
        cid=pair['candidate_id'];pack=read(PRIVATE/'semantic_v2/train1/provider'/f'{cid}.json')
        ids=frozenset(r[7] for r in pack['structural_rows'])
        auth=Train2HiddenVerifierAuthorityV1(structural(read(PRIVATE/'semantic_v2/train2/structural'/f'{cid}.json'),'train2'),ids)
        for arm in outputs:
            observations=[];states=[]
            for repeat in ((1,) if arm=='T0' else (1,2,3)):
                retrieval_ids=frozenset()
                if arm=='T0':
                    raw=[parse_proposal(read(PRIVATE/'semantic_v2/train1/t0'/f'{cid}.json'))];selected=0;row=None
                else:
                    row=read(run/'outputs'/f'{cid}.{arm}.R{repeat}.json');replay(row);hashes.append(row['self_hash'])
                    raw=[parse_proposal(x) if x is not None else None for x in row['raw']];selected=row['selected_draw']-1
                    require(len(raw)==(1 if arm=='T1' else 3 if arm=='T1-B' else len(raw)) and 1<=len(raw)<=3,'ARM_CALL_CARDINALITY')
                    if arm=='T1-B':
                        choices=[(p,verify(p,auth) if p else VerifierResultV1('REJECTED',((-1,'PARSE_FAILURE'),),0)) for p in raw]
                        require(selected==select_t1b(choices),'T1B_SELECTION_REPLAY')
                    else:require(selected==len(raw)-1,'FINAL_DRAW_IDENTITY')
                    if arm=='T2':
                        for p in raw[:selected]:
                            require(p is not None,'REPAIR_AFTER_PARSE_FAILURE')
                            v=verify(p,auth,retrieval_ids=retrieval_ids);q=retrieval(auth,p,v)
                            require(v.status=='NEEDS_REPAIR','EARLY_STOP_REPLAY')
                            retrieval_ids|=frozenset(x['evidence_slice_id'] for x in q['alternatives'])
                    replay_ids=frozenset();replay_feedback=[];replay_results=[];repair=None
                    for draw,proposal in enumerate(raw,1):
                        slot=f'{cid}.{arm}.R{repeat}.C{draw}';req,res=call_rows.pop(slot)
                        require(req['request']==request_body(pack,repair=repair),'OUTPUT_PROMPT_LEDGER_BINDING')
                        try:from_call=response_proposal(res['response'])
                        except ParsedResponseFailure:from_call=None
                        require(from_call==proposal,'RAW_OUTPUT_RESPONSE_BINDING')
                        vv=verify(proposal,auth,retrieval_ids=replay_ids) if proposal else VerifierResultV1('REJECTED',((-1,'PARSE_FAILURE'),),0)
                        replay_results.append(asdict(vv))
                        if arm=='T2' and vv.status=='NEEDS_REPAIR' and draw<3:
                            ff=feedback(proposal,vv,draw);qq=retrieval(auth,proposal,vv);replay_feedback.append(ff)
                            replay_ids|=frozenset(x['evidence_slice_id'] for x in qq['alternatives'])
                            repair={'previous_proposal':proposal_document(proposal),'feedback':ff,'retrieval':qq}
                    require(digest(replay_results)==digest(row['verifier_results']) and replay_feedback==row['feedback'],'VERIFIER_FEEDBACK_REPLAY')
                p=raw[selected];accepted=None
                if p is not None and verify(p,auth,retrieval_ids=retrieval_ids).status=='ACCEPTED':
                    accepted=admit(p,auth,implementation_hash=freeze['implementation_bundle_hash'],config_hash=freeze['provider_config_hash'],retrieval_ids=retrieval_ids)
                if row:require((accepted.receipt if accepted else None)==row['admission_receipt'],'ADMISSION_REPLAY_CHANGED')
                if row:
                    final_status=replay_results[selected]['status']
                    if arm=='T2' and final_status=='NEEDS_REPAIR':require(len(raw)==3,'T2_TRUNCATED_REPAIR_BUDGET')
                    expected_terminal='ACCEPTED_RULE_SET' if accepted and p.rules else 'INTENTIONAL_NO_RULE' if accepted else 'NEEDS_REPAIR_BUDGET_EXHAUSTED' if arm=='T2' and final_status=='NEEDS_REPAIR' else 'VERIFIER_REJECTION'
                    if not accepted and p is None:expected_terminal='ALL_DRAWS_FAILED' if arm=='T1-B' and all(x is None for x in raw) else 'PARSE_FAILURE'
                    require(row['terminal']==expected_terminal,'TERMINAL_TAXONOMY_REPLAY')
                state=row['terminal'] if row else ('ACCEPTED_RULE_SET' if accepted and p.rules else 'INTENTIONAL_NO_RULE' if accepted else 'VERIFIER_REJECTION')
                observations.append(accepted);states.append(state);rows.append((arm,repeat,pair,accepted))
                if arm=='T2':repairs.append({'candidate_id':cid,'initial':raw[0],'final':accepted,'initial_status':row['verifier_results'][0]['status'],'feedback_actions':len(row['feedback'])})
            outputs[arm][cid]=tuple(observations*3 if arm=='T0' else observations)
            terminals[arm][cid]=tuple(states*3 if arm=='T0' else states)
    require(len(hashes)==3*3*cohort['count'] and sorted(hashes)==sorted(bundle['terminal_hashes']) and not call_rows,'ALL_OUTPUT_CLOSURE')
    admissions=seal({'output_bundle_hash':bundle['self_hash'],'execution_freeze_hash':freeze['self_hash'],'records':[{'candidate_id':pair['candidate_id'],'arm':a,'repeat':r,'admission_hash':accepted.receipt['self_hash'] if accepted else None} for a,r,pair,accepted in rows]})
    publish(run/'evaluation/TRAIN2_ADMISSIONS_FROZEN.json',admissions)
    require(sha256((PRIVATE/'train3/reference.json').read_bytes()).hexdigest()==freeze['private_input_hashes']['train3/reference.json'],'TRAIN3_FROZEN_REFERENCE_HASH')
    hidden=read(PRIVATE/'train3/reference.json');replay(hidden)
    require(hidden['self_hash']==freeze['private_reference_hash'],'REFERENCE_FREEZE_CHANGED')
    reference={r['candidate_id']:tuple(SemanticTupleV1(**x) for x in r['relations']) for r in hidden['pairs']}
    require(set(reference)=={p['candidate_id'] for p in cohort['pairs']},'REFERENCE_COHORT')
    reports={a:report(reference,outputs[a],terminals[a]) for a in outputs}
    publish(run/'evaluation/TRAIN3_EVALUATION_FROZEN.json',seal(rational({'reports':reports,'reference_hash':hidden['self_hash'],'output_bundle_hash':bundle['self_hash'],'admissions_hash':admissions['self_hash'],'T0_repeat_policy':'DETERMINISTIC_SINGLE_RUN_REFERENCE'})))
    # Permanent close precedes hidden evaluation; binder follows all three durable freezes.
    cap=authorize_binding(run,cohort,freeze['self_hash'],hidden)
    rolemaps=load_numeric_cache(cap,PRIVATE,freeze['private_input_hashes'])
    require(sha256((PRIVATE/'train4/input_receipt.json').read_bytes()).hexdigest()==freeze['private_input_hashes']['train4/input_receipt.json'],'TRAIN4_FROZEN_CUSTODY_HASH')
    matrix,receipt,access=load_normal(ROOT,'train4',freeze['normal_custody_source_commit'])
    expected=read(PRIVATE/'train4/input_receipt.json')
    require(digest(receipt)==digest(expected['receipt']),'TRAIN4_CUSTODY_CHANGED')
    authority=Train4HiddenGuardAuthorityV1(digest(receipt),'HAI_TRAIN4',len(matrix))
    guard_results={};conversion={}
    for arm in outputs:
        for repeat in ((1,) if arm=='T0' else (1,2,3)):
            rules=[];proposed=0;binding_failures=[]
            for a,r,pair,accepted in rows:
                if a!=arm or r!=repeat or accepted is None:continue
                proposed+=len(accepted.proposal.rules)
                maps={s:{(x['source_direction'],x['alias']):x['roles'] for x in rolemaps[s] if tuple(x['pair'])==(pair['source'],pair['target'])} for s in rolemaps}
                for i,rule in enumerate(accepted.proposal.rules):
                    if rule.semantic in reference[pair['candidate_id']]:
                        try:rules.append(bind_guard_rule(cap,accepted,i,pair=(pair['source'],pair['target']),reference=reference,reference_hash=hidden['self_hash'],train1=maps['train1'],train2=maps['train2']))
                        except (ValueError,KeyError) as error:
                            if isinstance(error,ValueError) and str(error) not in ('INCOMPLETE_NUMERIC_AUTHORITY','NUMERIC_ROLE_CLOSURE','NONFINITE_NUMERIC_AUTHORITY','NUMERIC_SCALE_INVALID','FROZEN_WINDOW_MISMATCH'):
                                raise
                            binding_failures.append({'candidate_id':pair['candidate_id'],'rule_index':i,'status':'NUMERIC_BINDING_FAIL_CLOSED','reason':str(error) if isinstance(error,ValueError) else 'INCOMPLETE_NUMERIC_AUTHORITY'})
            descriptors=convert(ROOT,run/'evaluation/conversion'/f'{arm}.R{repeat}',tuple(rules))
            states,census=run_guard_portfolio(authority=authority,matrix=matrix,feature_order=tuple(P1_FEATURE_ORDER),rules=tuple(rules))
            guard_results[f'{arm}.R{repeat}']={'states':states,'census':census,'numeric_binding_count':len(rules),'numeric_binding_failures':binding_failures,'formal_conversion_count':len(descriptors),'admitted_rule_count':proposed,'deployment_authorized':False}
            conversion[f'{arm}.R{repeat}']=Fraction(len(descriptors),proposed) if proposed else Fraction(0)
    repair=repair_pair_sets(tuple(repairs),reference)
    a=guard_results['T2.R1']['census']['burden'];b=guard_results['T1-B.R1']['census']['burden']
    # Undefined burden cannot be used as evidence of advantage.
    if any(x is None for x in a+b):
        result='AGENTIC_MECHANISM_SUPPORTED_BUT_ADVANTAGE_LIMITED' if len(repair['train3_confirmed_exact_repair_pairs'])>=2 else 'AGENTIC_NOT_SUPPORTED'
        limitation='UNDEFINED_BURDEN_PRIMARY_ADVANTAGE_INELIGIBLE'
    else:
        result=disposition(feedback_pairs=len(repair['feedback_pairs']),repair_pairs=len(repair['train3_confirmed_exact_repair_pairs']),t2=reports['T2']['strict'],t1b=reports['T1-B']['strict'],t2_burden=a,t1b_burden=b,t2_conversion=conversion['T2.R1'],t1b_conversion=conversion['T1-B.R1']);limitation=None
    require(reports['T2']['strict']['disposition_reference_valid'],'BLOCKED_DEGENERATE_REFERENCE_COHORT')
    resultdoc=seal(rational({'guard':guard_results,'repairs':repair,'disposition':result,'limitation':limitation,'paired':paired_comparison(reference,reports['T2']['semantic_outputs'],reports['T1-B']['semantic_outputs']),'next_gate':'DG-04','production_portfolio_created':False,'train4_access_receipt':access}))
    publish(run/'evaluation/FINAL_LOCAL_RESULTS.json',resultdoc)
    print(json.dumps({'status':'LOCAL_EVALUATION_FROZEN','next_gate':'DG-04'}))

if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'status':'FAIL_CLOSED','error_type':type(e).__name__}));raise SystemExit(2)
