"""Synthetic-only semantic reduction, SCI02B ordering and revised budget regressions."""
from dataclasses import asdict,replace,fields
from pathlib import Path
from tempfile import TemporaryDirectory
from fractions import Fraction
import json,unittest,inspect,ast
import sys
from unittest.mock import patch
from hashlib import sha256
from paperworks.validation_v2.exp03b_semantic_v2 import *
from paperworks.validation_v2.exp03b_hidden_v2 import Train2SemanticEvidenceV2,Train2HiddenVerifierAuthorityV2,verify,feedback,retrieval
from paperworks.validation_v2.exp03b_firewall_v1 import SplitPurePredictiveEvidenceV1
from paperworks.validation_v2.exp03b_firewall_v2 import project,render,assert_clean
from paperworks.validation_v2.exp03b_prompt_v2 import request_body,output_schema,validate_repair
from paperworks.validation_v2.exp03b_execution_v2 import admit,replay_arm
from paperworks.validation_v2.exp03b_metrics_v2 import majority,strict_metrics,portfolio_repeat
from paperworks.validation_v2.exp03b_binder_v2 import (authorize_binding,bind_guard_rule,require_provider_open,fixed_roles,validate_roles,FIXED_ALIAS,PostInductionCapabilityV2)
from paperworks.validation_v2.exp03b_numeric_v1 import GRID,roles_from_summary,pooled_roles
from paperworks.validation_v2.exp03b_custody_v1 import publish,seal
from paperworks.validation_v2.exp03b_provider_gate_v2 import ProviderCallGate,validate_call_inventory


def fixture(count=2):
    source,target='P1_A','P1_B';cid='EXP03B-CAND-'+digest({'source':source,'target':target})[:20];rows=[]
    selected=[SemanticTupleV1('step_up','increase',5),SemanticTupleV1('step_down','decrease',10)][:count]
    for s in SOURCES:
        for t in TARGETS:
            for h in HORIZONS:
                x=SemanticTupleV1(s,t,h);good=x in selected
                rows.append(StructuralTupleEvidenceV1(x,8 if good else 0,.8 if good else 0,.1 if good else 0,3. if good else 0,'EV-'+digest(asdict(x))[:24]))
    e=Train1SemanticEvidenceV2(cid,source,target,'a'*64,tuple(rows))
    h=Train2SemanticEvidenceV2(cid,source,target,'b'*64,tuple(rows))
    auth=Train2HiddenVerifierAuthorityV2(h,frozenset(r.evidence_slice_id for r in rows))
    predictive=SplitPurePredictiveEvidenceV1('train1',cid,'c'*64,.5,tuple((h,.4,.3,None) for h in HORIZONS))
    return e,auth,render(project(e,predictive))


def chain(root,accepted):
    cid=accepted.candidate_id;cohort=seal({'count':1,'pairs':[{'candidate_id':cid}]});hashes=[]
    for arm in ('T1','T1-B','T2'):
        for repeat in (1,2,3):
            row=seal({'candidate_id':cid,'arm':arm,'repeat':repeat});publish(root/f'outputs/{cid}.{arm}.R{repeat}.json',row);hashes.append(row['self_hash'])
    bundle=seal({'count':9,'terminal_hashes':hashes});publish(root/'ALL_ARM_OUTPUTS_FROZEN.json',bundle)
    publish(root/'PROVIDER_PHASE_CLOSED.json',seal({'output_bundle_hash':bundle['self_hash'],'execution_freeze_hash':'f'*64,'provider_calls_allowed':False}))
    records=[{'candidate_id':cid,'arm':a,'repeat':r,'admission_hash':accepted.receipt['self_hash']} for a in ('T0','T1','T1-B','T2') for r in ((1,) if a=='T0' else (1,2,3))]
    admission=seal({'output_bundle_hash':bundle['self_hash'],'execution_freeze_hash':'f'*64,'records':records});publish(root/'evaluation/TRAIN2_ADMISSIONS_FROZEN.json',admission)
    reference=seal({'pairs':[{'candidate_id':cid,'relations':[asdict(x) for x in accepted.proposal.semantic_set()]}]})
    publish(root/'evaluation/TRAIN3_EVALUATION_FROZEN.json',seal({'output_bundle_hash':bundle['self_hash'],'admissions_hash':admission['self_hash'],'reference_hash':reference['self_hash']}))
    return cohort,reference


class SemanticReductionTests(unittest.TestCase):
    def test_output_zero_one_two(self):
        for n in range(3):
            e,a,_=fixture(n);p=t0(e);self.assertEqual(len(p.rules),n);self.assertEqual(parse_proposal(proposal_document(p)),p);self.assertEqual(verify(p,a).status,'ACCEPTED')
    def test_no_numeric_fields_or_mixed_objects(self):
        e,a,p=fixture();self.assertFalse(any('option' in f.name for f in fields(e)));self.assertFalse(any('option' in f.name for f in fields(a.evidence)))
        self.assertEqual(len(p['structural_rows']),20);self.assertNotIn('option_rows',p);self.assertNotIn('option_columns',p)
        self.assertNotIn('numeric',json.dumps(output_schema()))
    def test_numeric_injection_rejected(self):
        e,a,p=fixture();raw=proposal_document(t0(e))
        raw['rules'][0]['numeric_policy_option_id']='NUM-033'
        with self.assertRaises(ValueError):parse_proposal(raw)
        for key,value in [('option_rows',[]),('option_columns',[]),('selected_policy','x')]:
            with self.assertRaises(ValueError):request_body({**p,key:value})
        for value in ['NUM-033','RELATION_SPECIFIC_NORMAL_ONLY_V1:n7-q0.90-s2-f0.05']:
            with self.assertRaises(ValueError):assert_clean({'x':value})
    def test_hidden_object_taint(self):
        e,a,p=fixture();pred=SplitPurePredictiveEvidenceV1('train2',e.candidate_id,'c'*64,.2,tuple((h,.1,.2,None) for h in HORIZONS))
        with self.assertRaises(ValueError):project(e,pred)
        with self.assertRaises(ValueError):t0(a.evidence)
        with self.assertRaises(ValueError):render(a)
    def test_split_thresholds_preserved(self):
        e,a,p=fixture(1);rows=tuple(replace(r,effect=1.5) if r.support else r for r in e.rows)
        one=replace(e,rows=rows);two=replace(a,evidence=replace(a.evidence,rows=rows))
        self.assertEqual(t0(one).decision,'NO_RULE');self.assertEqual(verify(t0(e),two).status,'ACCEPTED')
    def test_repairable_directions_and_horizon(self):
        e,a,_=fixture(1);p=t0(e);r=p.rules[0]
        for semantic in (SemanticTupleV1('step_down','increase',5),SemanticTupleV1('step_up','decrease',5),SemanticTupleV1('step_up','increase',60)):
            wrong=SemanticProposalV2('RULE_SET',(replace(r,semantic=semantic),));v=verify(wrong,a);self.assertEqual(v.status,'NEEDS_REPAIR')
            f=feedback(wrong,v,1);q=retrieval(a,wrong,v);repair={'previous_proposal':proposal_document(wrong),'feedback':f,'retrieval':q};validate_repair(repair)
            self.assertFalse(any('NUMERIC' in code for _,code in v.issues))
            self.assertNotIn('preferred',json.dumps(q))
    def test_incomplete_and_no_rule_recovery(self):
        e,a,_=fixture();p=t0(e);one=SemanticProposalV2('RULE_SET',p.rules[:1])
        self.assertIn((-1,'RULE_SET_INCOMPLETE'),verify(one,a).issues)
        self.assertIn((-1,'NO_RULE_NOT_JUSTIFIED'),verify(SemanticProposalV2('NO_RULE',()),a).issues)
    def test_rule_to_no_rule_correction(self):
        e,_,_=fixture(1);_,a,_=fixture(0)
        self.assertEqual(verify(t0(e),a).status,'NEEDS_REPAIR');self.assertEqual(verify(SemanticProposalV2('NO_RULE',()),a).status,'ACCEPTED')
    def test_horizon_preference_no_new_margin(self):
        e,a,_=fixture(1);p=t0(e);rows=tuple(replace(r,support=8,consistency=.8,opposite_consistency=.1,effect=3) if r.semantic==SemanticTupleV1('step_up','increase',1) else r for r in a.evidence.rows)
        result=verify(p,replace(a,evidence=replace(a.evidence,rows=rows)));self.assertIn((0,'HORIZON_UNSTABLE'),result.issues)
    def test_t1_and_t1b_no_feedback(self):
        e,a,_=fixture(1);wrong={'decision':'NO_RULE','rules':[]};p=proposal_document(t0(e))
        for arm,responses in [('T1',(wrong,)),('T1-B',(wrong,p,wrong))]:
            result=replay_arm(candidate_id=e.candidate_id,arm=arm,repeat=1,mock_responses=responses,verify_callback=lambda x,ids:verify(x,a,retrieval_ids=ids),retrieve_callback=lambda *args:self.fail('NO_FEEDBACK'))
            self.assertFalse(result.feedback_records)
    def test_t2_second_third_and_early_stop(self):
        e,a,_=fixture(1);wrong={'decision':'NO_RULE','rules':[]};p=proposal_document(t0(e))
        for responses,n in [((p,wrong,wrong),1),((wrong,p),2),((wrong,wrong,p),3)]:
            r=replay_arm(candidate_id=e.candidate_id,arm='T2',repeat=1,mock_responses=responses,verify_callback=lambda x,ids:verify(x,a,retrieval_ids=ids),retrieve_callback=lambda x,v:retrieval(a,x,v));self.assertEqual(len(r.raw),n);self.assertIsNotNone(r.admitted)
        with self.assertRaises(ValueError):replay_arm(candidate_id=e.candidate_id,arm='T2',repeat=1,mock_responses=(p,)*4,verify_callback=lambda *args:None)
    def test_majority_failures_unchanged(self):
        e,_,_=fixture();p=t0(e);n=SemanticProposalV2('NO_RULE',());one=SemanticProposalV2('RULE_SET',p.rules[:1])
        self.assertEqual(majority((p,p,None)),('MAJORITY',p.semantic_set()))
        self.assertEqual(majority((p,one,n))[0],'NO_MAJORITY');self.assertEqual(majority((None,)*3)[0],'NO_VALID_OUTPUT')
        self.assertEqual(majority((p,one,n),decision_only=True),('MAJORITY','RULE_SET'))
    def test_strict_no_decision_penalty(self):
        e,_,_=fixture(1);truth=t0(e).semantic_set();m=strict_metrics({'a':truth,'b':()},{'a':None,'b':None})
        self.assertEqual((m['FN'],m['FP'],m['TN'],m['TP']),(1,1,0,0));self.assertEqual(m['N'],2)
        self.assertEqual(strict_metrics({'a':()},{'a':()})['semantic_exact_match_count'],1)
    def test_repeat_one(self):
        portfolio_repeat(1)
        for r in (2,3):
            with self.assertRaises(ValueError):portfolio_repeat(r)
    def test_finite_and_tuple_closure(self):
        _,_,p=fixture()
        for mutated in [{**p,'stat_association':float('nan')},{**p,'structural_rows':p['structural_rows'][:-1]},{**p,'split':'train2'}]:
            with self.assertRaises(ValueError):request_body(mutated)
    def test_numeric_formula_equivalence(self):
        self.assertEqual(tuple(map(float,GRID[int(FIXED_ALIAS[-3:])])),(7.,.9,2.,.05))
        for noise in (0.,.3,2.):
            s=(noise,(1.,2.,3.),(2.,3.,4.),(3.,4.,5.));t=(.4,None,None,None)
            for direction in SOURCES:
                roles=fixed_roles(s,t,direction);self.assertEqual(roles,roles_from_summary(s,t,direction,FIXED_ALIAS))
                validate_roles(roles)
                for bad in [{**roles,'target_noise_scale':0},{**roles,'source_step_threshold':float('inf')},{**roles,'extra':1},{k:v for k,v in roles.items() if k!='target_noise_scale'}]:
                    with self.assertRaises(ValueError):validate_roles(bad)
    def test_binding_only_after_three_freezes(self):
        e,a,_=fixture(1);p=t0(e);accepted=admit(p,a,implementation_hash='a'*64,config_hash='b'*64)
        with TemporaryDirectory() as td:
            root=Path(td);c,reference=chain(root,accepted)
            path=root/'evaluation/TRAIN3_EVALUATION_FROZEN.json';raw=path.read_bytes();path.unlink()
            with self.assertRaises(FileNotFoundError):authorize_binding(root,c,'f'*64,reference)
            path.write_bytes(raw);cap=authorize_binding(root,c,'f'*64,reference)
            s=(.2,(1.,2.,3.),(2.,3.,4.),(3.,4.,5.));t=(.4,None,None,None)
            maps={(p.rules[0].semantic.source_direction,alias):roles_from_summary(s,t,p.rules[0].semantic.source_direction,alias) for alias in (FIXED_ALIAS,'NUM-000')}
            before=encoded(proposal_document(p));kwargs=dict(pair=(e.source,e.target),reference={e.candidate_id:p.semantic_set()},reference_hash=reference['self_hash'],train1=maps,train2=maps)
            b=bind_guard_rule(cap,accepted,0,**kwargs);self.assertEqual(b,bind_guard_rule(cap,accepted,0,**kwargs));self.assertEqual(before,encoded(proposal_document(p)))
            with self.assertRaises(ValueError):require_provider_open(root)
            with self.assertRaises(ValueError):bind_guard_rule(None,accepted,0,**kwargs)
            with self.assertRaises(ValueError):bind_guard_rule(cap,accepted,0,**{**kwargs,'train1':{}})
            path.write_bytes(raw+b' ')
            with self.assertRaises(ValueError):cap.replay()
    def test_binder_factory_and_post_phase_barrier(self):
        with self.assertRaises(ValueError):PostInductionCapabilityV2(None,None,(),(),None)
        with TemporaryDirectory() as td:
            p=Path(td);require_provider_open(p)
            for name in ('ALL_ARM_OUTPUTS_FROZEN.json','PROVIDER_PHASE_CLOSED.json','evaluation/NUMERIC_BINDING_STARTED.json','evaluation/FINAL_LOCAL_RESULTS.json'):
                target=p/name;target.parent.mkdir(exist_ok=True);target.write_text('{}')
                with self.assertRaises(ValueError):require_provider_open(p)
                target.unlink()
    def test_provider_modules_no_hidden_import(self):
        import paperworks.validation_v2.exp03b_firewall_v2 as f
        import paperworks.validation_v2.exp03b_prompt_v2 as p
        for module in (f,p):
            names=[n.module or '' for n in ast.walk(ast.parse(inspect.getsource(module))) if isinstance(n,ast.ImportFrom)]
            self.assertFalse(any(any(x in n for x in ('hidden','binder','evaluation','numeric','selected_policy')) for n in names))


class RevisedGateTests(unittest.TestCase):
    def budget(self):
        e,a,p=fixture();b=seal({'model':'gpt-5.4-mini-2026-03-17','candidate_ids':[e.candidate_id],'maximum_calls':7,'phase_input_caps':{'initial':10000,'repair':20000},'maximum_input_tokens':90000,'maximum_output_tokens':14336,'output_tokens_per_call_cap':2048,'standard_api_cost_ceiling_usd':'1.00','framing_allowance':512})
        approval={'gate':'DG-03B_REVISED','status':'APPROVED','budget_hash':b['self_hash'],'execution_freeze_hash':'f'*64}
        return e,p,b,approval
    def test_old_approval_rejected(self):
        e,p,b,a=self.budget()
        with self.assertRaises(ValueError):ProviderCallGate(b,{**a,'gate':'DG-03B'},'f'*64)
    def test_receipt_first_and_cumulative_cap(self):
        e,p,b,a=self.budget();g=ProviderCallGate(b,a,'f'*64);body=request_body(p)
        g.reserve(slot=f'{e.candidate_id}.T1.R1.C1',request=body,input_upper_bound=5000)
        with self.assertRaises(ValueError):g.reserve(slot=f'{e.candidate_id}.T1.R2.C1',request=body,input_upper_bound=5000)
        r=g.reconcile(input_tokens=100,output_tokens=100,response_hash='a'*64,model=b['model'],latency=1)
        with self.assertRaises(ValueError):g.reserve(slot=f'{e.candidate_id}.T1.R2.C1',request=body,input_upper_bound=5000)
        g.accept_one_call_receipt(digest(r),persisted_and_replayed=True,privacy_pass=True,schema_pass=True)
        g.budget={**b,'maximum_input_tokens':10000}
        with self.assertRaises(ValueError):g.reserve(slot=f'{e.candidate_id}.T1.R2.C1',request=body,input_upper_bound=5000)
    def test_fourth_call_and_config_rejected(self):
        e,p,b,a=self.budget();g=ProviderCallGate(b,a,'f'*64)
        for slot in (f'{e.candidate_id}.T2.R1.C4',f'{e.candidate_id}.T1.R1.C2'):
            with self.assertRaises(ValueError):g.reserve(slot=slot,request=request_body(p),input_upper_bound=5000)
        with self.assertRaises(ValueError):g.reserve(slot=f'{e.candidate_id}.T1.R1.C1',request={**request_body(p),'model':'gpt-5.4-mini'},input_upper_bound=5000)
    def test_understated_bound_rejected(self):
        e,p,b,a=self.budget();g=ProviderCallGate(b,a,'f'*64)
        with self.assertRaises(ValueError):g.reserve(slot=f'{e.candidate_id}.T1.R1.C1',request=request_body(p),input_upper_bound=1)
    def test_ledger_gap_orphan_rejected(self):
        with TemporaryDirectory() as td:
            root=Path(td);calls=root/'calls';calls.mkdir();self.assertEqual(validate_call_inventory(root,609),0)
            for kind in ('request','response','receipt'):(calls/f'0001.{kind}.json').write_text('{}')
            self.assertEqual(validate_call_inventory(root,609),1)
            for kind in ('request','response','receipt'):(calls/f'0003.{kind}.json').write_text('{}')
            with self.assertRaises(ValueError):validate_call_inventory(root,609)
            for kind in ('request','response','receipt'):(calls/f'0002.{kind}.json').write_text('{}')
            self.assertEqual(validate_call_inventory(root,609),3)
            (calls/'0002.request.json').unlink()
            with self.assertRaises(ValueError):validate_call_inventory(root,609)


class SyntheticRunnerIntegrationTests(unittest.TestCase):
    def test_probe_resume_semantic_freeze_binder_guard(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
        import execute_exp03b_provider_v2 as runner
        import evaluate_exp03b_frozen_outputs_v2 as evaluator
        from paperworks.validation_v2.exp03b_codec_v2 import structural
        with TemporaryDirectory() as td:
            root=Path(td);pub=root/'public';private=root/'private';pub.mkdir();pairs=[];reference=[];provider_hashes={};roles={'train1':[],'train2':[]}
            for index,n in enumerate((1,0)):
                e,a,p=fixture(n)
                if index:
                    cid='EXP03B-CAND-'+digest({'source':'P1_C','target':'P1_D'})[:20]
                    e=replace(e,source='P1_C',target='P1_D',candidate_id=cid);a=replace(a,evidence=replace(a.evidence,source=e.source,target=e.target,candidate_id=cid));p={**p,'source':e.source,'target':e.target,'candidate_id':cid}
                cid=e.candidate_id;pairs.append({'candidate_id':cid,'source':e.source,'target':e.target});reference.append({'candidate_id':cid,'relations':[asdict(r) for r in t0(e).semantic_set()]})
                for relative,value in [(f'semantic_v2/train1/provider/{cid}.json',p),(f'semantic_v2/train1/t0/{cid}.json',proposal_document(t0(e))),(f'semantic_v2/train2/structural/{cid}.json',asdict(a.evidence))]:provider_hashes[relative]=publish(private/relative,value)
                for split in roles:
                    for direction in SOURCES:
                        for alias in (FIXED_ALIAS,'NUM-000'):
                            v=roles_from_summary((.2,(1.,2.,3.),(2.,3.,4.),(3.,4.,5.)),(.4,None,None,None),direction,alias)
                            roles[split].append({'pair':[e.source,e.target],'source_direction':direction,'alias':alias,'roles':v})
            cohort=seal({'count':2,'pairs':pairs});publish(pub/'EXP03B_COHORT_AUTHORITY_V1.json',cohort)
            hidden=seal({'pairs':reference});private_hashes=dict(provider_hashes)
            private_hashes['train3/reference.json']=publish(private/'train3/reference.json',hidden)
            train4_receipt={'synthetic':True};private_hashes['train4/input_receipt.json']=publish(private/'train4/input_receipt.json',{'receipt':train4_receipt})
            for split in roles:private_hashes[split+'/numeric_roles.json']=publish(private/split/'numeric_roles.json',{'split':split,'roles':roles[split]})
            budget=seal({'model':'gpt-5.4-mini-2026-03-17','candidate_ids':[p['candidate_id'] for p in pairs],'maximum_calls':42,'phase_input_caps':{'initial':7168,'repair':23552},'maximum_input_tokens':497664,'maximum_output_tokens':86016,'output_tokens_per_call_cap':2048,'standard_api_cost_ceiling_usd':'2.00','framing_allowance':512,'config_hash':'a'*64})
            publish(pub/'EXP03B_PROVIDER_BUDGET_V2.json',budget)
            freeze=seal({'status':'PREPARED_DG03B_REVISED_PENDING','implementation_hashes':{},'implementation_bundle_hash':'b'*64,'provider_config_hash':'a'*64,'provider_input_hashes':provider_hashes,'private_input_hashes':private_hashes,'private_reference_hash':hidden['self_hash'],'normal_custody_source_commit':'c'*40})
            publish(pub/'EXP03B_SEMANTIC_PREPARATION_FREEZE_V2.json',freeze)
            approval=private/'approval.json';publish(approval,seal({'gate':'DG-03B_REVISED','status':'APPROVED','budget_hash':budget['self_hash'],'execution_freeze_hash':freeze['self_hash']}))
            calls=[]
            def synthetic_transport(body):
                calls.append(body);e=json.loads(body['input'])['evidence'];doc={'candidate_id':e['candidate_id'],'source':e['source'],'target':e['target'],'input_hash':'d'*64,'split':'train1','rows':[{'semantic':dict(zip(('source_direction','target_direction','horizon_seconds'),r[:3])),'support':r[3],'consistency':r[4],'opposite_consistency':r[5],'effect':r[6],'evidence_slice_id':r[7]} for r in e['structural_rows']]}
                out=proposal_document(t0(structural(doc,'train1')))
                return {'model':budget['model'],'usage':{'input_tokens':1000,'output_tokens':100},'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(out)}]}]}
            with patch.multiple(runner,ROOT=root,PUBLIC=pub,PRIVATE=private),patch.object(runner,'transport',synthetic_transport):
                runner.main(approval,True);self.assertEqual(len(calls),1)
                runner.main(approval,True);self.assertEqual(len(calls),1)
                runner.main(approval,False);self.assertEqual(len(calls),30)
                with self.assertRaises(ValueError):runner.main(approval,False)
            def synthetic_guard(**kwargs):return [],{'burden':(Fraction(0),Fraction(0),Fraction(0))}
            with patch.multiple(evaluator,ROOT=root,PUBLIC=pub,PRIVATE=private),patch.object(evaluator,'load_normal',return_value=([0]*100,train4_receipt,{'synthetic':True})),patch.object(evaluator,'run_guard_portfolio',synthetic_guard):
                evaluator.main()
            run=private/'provider_execution_v2';self.assertTrue((run/'evaluation/TRAIN3_EVALUATION_FROZEN.json').exists());self.assertTrue((run/'evaluation/NUMERIC_BINDING_STARTED.json').exists());self.assertTrue((run/'evaluation/FINAL_LOCAL_RESULTS.json').exists())
            self.assertEqual(len(calls),30)


if __name__=='__main__':unittest.main()
