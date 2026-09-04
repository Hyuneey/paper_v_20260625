"""Future local evaluation only after every arm output is durably frozen."""
from pathlib import Path
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
import json
from paperworks.validation_v2.exp03b_contract_v1 import require,digest,parse_proposal,SemanticTupleV1
from paperworks.validation_v2.exp03b_custody_v1 import replay,seal,publish,load_normal
from paperworks.validation_v2.exp03b_codec import structural
from paperworks.validation_v2.exp03b_verifier_v1 import Train2HiddenVerifierAuthorityV1,retrieval,select_t1b,VerifierResultV1
from paperworks.validation_v2.exp03b_admission_verifier import verify
from paperworks.validation_v2.exp03b_execution import admit
from paperworks.validation_v2.exp03b_evaluation import bind_guard_rule,run_guard_portfolio
from paperworks.validation_v2.exp03b_guard_v1 import Train4HiddenGuardAuthorityV1
from paperworks.validation_v2.exp03b_reporting import report,repair_pair_sets,paired_comparison
from paperworks.validation_v2.exp03b_metrics_v1 import disposition
from paperworks.validation_v2.exp03b_conversion import convert
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
    freeze=read(PUBLIC/'EXP03B_FINAL_PREPARATION_FREEZE_V2.json');replay(freeze)
    for name,h in freeze['implementation_hashes'].items():require(sha256((ROOT/name).read_bytes()).hexdigest()==h,'EVALUATOR_CODE_CHANGED')
    run=PRIVATE/'provider_execution_v1'
    bundle=read(run/'ALL_ARM_OUTPUTS_FROZEN.json');replay(bundle)
    require(bundle['train3_evaluation_allowed'] and not (run/'SINGLE_WRITER.lock').exists(),'PROVIDER_WRITER_STILL_ACTIVE')
    cohort=read(PUBLIC/'EXP03B_COHORT_AUTHORITY_V1.json');replay(cohort)
    expected_hashes=[]
    for pair in cohort['pairs']:
        for arm in ('T1','T1-B','T2'):
            for repeat in (1,2,3):
                row=read(run/'outputs'/f"{pair['candidate_id']}.{arm}.R{repeat}.json");replay(row)
                require((row['candidate_id'],row['arm'],row['repeat'])==(pair['candidate_id'],arm,repeat),'OUTPUT_SLOT_IDENTITY')
                expected_hashes.append(row['self_hash'])
    require(len(expected_hashes)==bundle['count']==9*cohort['count'] and expected_hashes==bundle['terminal_hashes'],'OUTPUT_CLOSURE_BEFORE_REFERENCE')
    for name,h in freeze['private_input_hashes'].items():require(sha256((PRIVATE/name).read_bytes()).hexdigest()==h,'PRIVATE_INPUT_CHANGED')
    hidden=read(PRIVATE/'train3/reference.json');replay(hidden)
    require(hidden['self_hash']==freeze['private_reference_hash'],'REFERENCE_FREEZE_CHANGED')
    reference={r['candidate_id']:tuple(SemanticTupleV1(**x) for x in r['relations']) for r in hidden['pairs']}
    require(set(reference)=={p['candidate_id'] for p in cohort['pairs']},'REFERENCE_COHORT')
    outputs={a:{} for a in ('T0','T1','T1-B','T2')};terminals={a:{} for a in outputs};rows=[];repairs=[];hashes=[]
    for pair in cohort['pairs']:
        cid=pair['candidate_id'];pack=read(PRIVATE/'train1/provider'/f'{cid}.json')
        ids=frozenset([r[7] for r in pack['structural_rows']]+[r[11] for r in pack['option_rows']])
        auth=Train2HiddenVerifierAuthorityV1(structural(read(PRIVATE/'train2/structural'/f'{cid}.json'),'train2'),ids)
        for arm in outputs:
            observations=[];states=[]
            for repeat in ((1,) if arm=='T0' else (1,2,3)):
                retrieval_ids=frozenset()
                if arm=='T0':
                    raw=[parse_proposal(read(PRIVATE/'train1/t0'/f'{cid}.json'))];selected=0;row=None
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
                p=raw[selected];accepted=None
                if p is not None and verify(p,auth,retrieval_ids=retrieval_ids).status=='ACCEPTED':
                    accepted=admit(p,auth,implementation_hash=freeze['implementation_bundle_hash'],config_hash=freeze['provider_config_hash'],retrieval_ids=retrieval_ids)
                if row:require((accepted.receipt if accepted else None)==row['admission_receipt'],'ADMISSION_REPLAY_CHANGED')
                state=row['terminal'] if row else ('ACCEPTED_RULE_SET' if accepted and p.rules else 'INTENTIONAL_NO_RULE' if accepted else 'VERIFIER_REJECTION')
                observations.append(accepted);states.append(state);rows.append((arm,repeat,pair,accepted))
                if arm=='T2':repairs.append({'candidate_id':cid,'initial':raw[0],'final':accepted,'initial_status':row['verifier_results'][0]['status'],'feedback_actions':len(row['feedback'])})
            outputs[arm][cid]=tuple(observations*3 if arm=='T0' else observations)
            terminals[arm][cid]=tuple(states*3 if arm=='T0' else states)
    require(len(hashes)==3*3*cohort['count'] and sorted(hashes)==sorted(bundle['terminal_hashes']),'ALL_OUTPUT_CLOSURE')
    reports={a:report(reference,outputs[a],terminals[a]) for a in outputs}
    publish(run/'evaluation/TRAIN3_EVALUATION_FROZEN.json',seal(rational({'reports':reports,'reference_hash':hidden['self_hash'],'output_bundle_hash':bundle['self_hash'],'T0_repeat_policy':'DETERMINISTIC_SINGLE_RUN_REFERENCE'})))
    # Only after the persisted train3 evaluation. No provider call is possible here.
    matrix,receipt,access=load_normal(ROOT,'train4',freeze['audit_base_commit'])
    expected=read(PRIVATE/'train4/input_receipt.json')
    require(digest(receipt)==digest(expected['receipt']),'TRAIN4_CUSTODY_CHANGED')
    authority=Train4HiddenGuardAuthorityV1(digest(receipt),'HAI_TRAIN4',len(matrix))
    rolemaps={}
    for split in ('train1','train2'):
        doc=read(PRIVATE/split/'numeric_roles.json');require(doc['split']==split,'ROLE_SPLIT')
        rolemaps[split]=doc['roles']
    guard_results={};conversion={}
    for arm in outputs:
        for repeat in ((1,) if arm=='T0' else (1,2,3)):
            rules=[];proposed=0
            for a,r,pair,accepted in rows:
                if a!=arm or r!=repeat or accepted is None:continue
                proposed+=len(accepted.proposal.rules)
                maps={s:{(x['source_direction'],x['alias']):x['roles'] for x in rolemaps[s] if tuple(x['pair'])==(pair['source'],pair['target'])} for s in rolemaps}
                for i,rule in enumerate(accepted.proposal.rules):
                    if rule.semantic in reference[pair['candidate_id']]:rules.append(bind_guard_rule(accepted,i,pair=(pair['source'],pair['target']),reference=reference,reference_hash=hidden['self_hash'],train1=maps['train1'],train2=maps['train2']))
            descriptors=convert(ROOT,run/'evaluation/conversion'/f'{arm}.R{repeat}',tuple(rules))
            states,census=run_guard_portfolio(authority=authority,matrix=matrix,feature_order=tuple(P1_FEATURE_ORDER),rules=tuple(rules))
            guard_results[f'{arm}.R{repeat}']={'states':states,'census':census,'formal_conversion_count':len(descriptors),'admitted_rule_count':proposed,'deployment_authorized':False}
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
