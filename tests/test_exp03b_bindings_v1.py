"""Synthetic only. No scientific payload/provider access."""
import unittest
from dataclasses import replace
from fractions import Fraction
from paperworks.validation_v2.exp03b_contract_v1 import *
from paperworks.validation_v2.exp03b_verifier_v1 import *
from paperworks.validation_v2.exp03b_guard_v1 import *
from paperworks.validation_v2.exp03b_metrics_v1 import *
from paperworks.validation_v2.exp03b_firewall_v1 import *
from paperworks.validation_v2.exp03b_arms_v1 import run_arm
from paperworks.validation_v2.exp03b_numeric_v1 import derive_roles, pooled_roles, census


def metric(alias="NUM-000", **changes):
    values=dict(alias=alias,materializable=True,formed=5,passed=5,failed=0,abstained=0,system_errors=0,false_seconds=0,false_episodes=0,exposure=100,evidence_slice_id="EV-option")
    return OptionMetricsV1(**(values|changes))


def table(split="train1", two=False, effect=2., support=5):
    rows=[]
    for sd in SOURCES:
        for td in TARGETS:
            for h in HORIZONS:
                good=h==5 and td=="increase" and (sd=="step_up" or two)
                sem=SemanticTupleV1(sd,td,h)
                s=StructuralTupleEvidenceV1(sem,support if good else 0,.6 if good else 0.,0.,effect if good else 0.,"EV-"+digest(asdict(sem))[:20])
                options=tuple(metric(a,evidence_slice_id="EV-"+digest([asdict(sem),a])[:20]) for a in ALIASES)
                rows.append(TupleEvidenceV1(s,options))
    kind=Train1ProviderStructuralEvidenceV1 if split=="train1" else Train2HiddenStructuralVerifierEvidenceV1
    return kind("CAND-A","S","T","a"*64,tuple(rows))


def authority(two=False, **kw):
    e=table("train2",two,**kw)
    ids=frozenset([r.structural.evidence_slice_id for r in e.rows]+[o.evidence_slice_id for r in e.rows for o in r.options])
    return Train2HiddenVerifierAuthorityV1(e,ids)


class BindingTests(unittest.TestCase):
    def test_train1_not_pooled(self): self.assertEqual(t0(table()).decision,"RULE_SET")
    def test_train1_effect(self): self.assertEqual(t0(table(effect=1.9)).decision,"NO_RULE")
    def test_train2_effect(self): self.assertEqual(verify(t0(table()),authority(effect=1.)).status,"ACCEPTED")
    def test_support(self): self.assertEqual(t0(table(support=4)).decision,"NO_RULE")
    def test_hidden_type(self):
        with self.assertRaises(ValueError):t0(table("train2"))
    def test_two_rules(self): self.assertEqual(len(t0(table(two=True)).rules),2)
    def test_completeness(self): self.assertIn((-1,"RULE_SET_INCOMPLETE"),verify(t0(table()),authority(two=True)).issues)
    def test_no_rule_unjustified(self): self.assertEqual(verify(ProposalV1("NO_RULE",()),authority()).status,"NEEDS_REPAIR")
    def test_no_rule_justified(self): self.assertEqual(verify(ProposalV1("NO_RULE",()),authority(support=0)).status,"ACCEPTED")
    def test_horizon(self):
        p=t0(table());p=replace(p,rules=(replace(p.rules[0],semantic=SemanticTupleV1("step_up","increase",10)),))
        self.assertIn((0,"HORIZON_UNSTABLE"),verify(p,authority()).issues)
    def test_duplicate(self):
        p=t0(table());p=replace(p,rules=(p.rules[0],p.rules[0]))
        self.assertIn((1,"DUPLICATE_SOURCE_DIRECTION"),verify(p,authority()).issues)
    def test_aliases(self): self.assertEqual(len(set(ALIASES)),37)
    def test_common_tie(self): self.assertEqual(preferred_option(tuple(metric(a) for a in ALIASES)).alias,"NUM-000")
    def test_option_order(self):
        opts=tuple(metric(a,passed=4,failed=1,false_seconds=1,false_episodes=1) if a=="NUM-000" else metric(a) for a in ALIASES)
        self.assertEqual(preferred_option(opts).alias,"NUM-001")
    def test_coverage(self):self.assertFalse(metric("NUM-001",passed=4,abstained=1).eligible(metric()))
    def test_numeric_unstable(self):
        p=t0(table());p=replace(p,rules=(replace(p.rules[0],numeric_policy_option_id="NUM-001"),))
        self.assertIn((0,"NUMERIC_OPTION_UNSTABLE"),verify(p,authority()).issues)
    def test_pool_gate(self):
        with self.assertRaises(ValueError):pooled_roles({"x":1},{"x":2},train2_status="NEEDS_REPAIR")
        self.assertEqual(pooled_roles({"x":1},{"x":2},train2_status="ACCEPTED"),{"x":2})
    def test_guard_underobserved(self):self.assertEqual(guard(metric(formed=4,passed=4),metric()),"TRAIN4_GUARD_UNDEROBSERVED")
    def test_guard_common(self):self.assertEqual(guard(metric(),metric()),"RETAINED")
    def test_guard_partial(self):self.assertEqual(retention_state(("RETAINED","TRAIN4_GUARD_UNDEROBSERVED")),"PARTIALLY_RETAINED_RULE_SET")
    def test_guard_burden(self):self.assertEqual(guard(metric("NUM-001"),metric()),"TRAIN4_NORMAL_BURDEN_REGRESSION")
    def test_union(self):
        x=portfolio_census((("F",(1,2),0,2,0),("F",(2,3),0,2,0)),{"F":10})
        self.assertEqual((x["false_seconds"],x["false_episodes"],x["FAIL"],x["exposure"]),(3,1,4,10))
    def test_file_local(self): self.assertEqual(portfolio_census((("A",(1,),0,1,0),("B",(2,),0,1,0)),{"A":10,"B":10})["false_episodes"],2)
    def test_missing_coordinates(self):
        with self.assertRaises(ValueError):metric(passed=0,failed=5)
        with self.assertRaises(ValueError):portfolio_census((("F",(),0,5,0),),{"F":10})
    def test_majority_two_failure(self):
        p=t0(table());self.assertEqual(majority((p,None,p)),("MAJORITY",p.semantic_set()))
    def test_no_valid(self):self.assertEqual(majority((None,None,None))[0],"NO_VALID_OUTPUT")
    def test_no_majority(self): self.assertEqual(majority((t0(table()),t0(table(two=True)),ProposalV1("NO_RULE",())))[0],"NO_MAJORITY")
    def test_decision_majority(self): self.assertEqual(majority((t0(table()),t0(table(two=True)),None),decision_only=True),("MAJORITY","RULE_SET"))
    def test_failure_penalty(self):
        m=strict_metrics({"A":t0(table()).semantic_set(),"B":()},{"A":None,"B":None})
        self.assertEqual((m["FN"],m["FP"],m["TN"],m["F1"]),(1,1,0,0));self.assertTrue(m["no_predicted_positives"])
    def test_both_empty(self):
        m=strict_metrics({"A":()},{"A":()});self.assertEqual(m["semantic_exact_match_count"],1);self.assertEqual(m["directional_TP"],0)
    def test_empty_cohort(self):
        with self.assertRaises(ValueError):strict_metrics({}, {})
    def test_repeat_lock(self):
        with self.assertRaises(ValueError):portfolio_repeat(2)
    def test_format_not_repair(self):
        p=t0(table());self.assertFalse(exact_repair(p,p,p.semantic_set(),initial_status="NEEDS_REPAIR",feedback_actions=1))
    def test_firewall(self):
        e=table();g=SplitPurePredictiveEvidenceV1("train1",e.candidate_id,"a"*64,.1,tuple((h,.2,.1,None) for h in HORIZONS))
        render(project(e,g))
        with self.assertRaises(ValueError):project(table("train2"),g)
        with self.assertRaises(ValueError):project(e,replace(g,split="train2"))
        with self.assertRaises(ValueError):replace(g,split="train4")
    def test_denied(self):
        for key in DENIED:
            with self.subTest(key=key),self.assertRaises(ValueError):assert_clean({key:1})
        with self.assertRaises(ValueError):assert_clean({"x":"secret-answer"},forbidden_identities=("secret-answer",))
    def test_response_pair_mutation(self):
        value=proposal_document(t0(table()))|{"source":"OTHER"}
        with self.assertRaises(ValueError):parse_proposal(value)
    def test_t2_early_stop(self):
        p=proposal_document(t0(table()));a=authority()
        r=run_arm(candidate_id="CAND-A",arm="T2",repeat=1,mock_responses=(p,p,p),verify_callback=lambda p,ids:verify(p,a,retrieval_ids=ids))
        self.assertEqual(len(r.raw),1);self.assertIsNotNone(r.admitted)
    def test_second_repair(self):
        p=proposal_document(t0(table()));a=authority()
        r=run_arm(candidate_id="CAND-A",arm="T2",repeat=1,mock_responses=({"decision":"NO_RULE","rules":[]},p),verify_callback=lambda p,ids:verify(p,a,retrieval_ids=ids),retrieve_callback=lambda p,v:retrieval(a,p,v))
        self.assertEqual(len(r.raw),2);self.assertEqual(len(r.feedback_records),1);self.assertIsNotNone(r.admitted)
    def test_budget_exhausted(self):
        p={"decision":"NO_RULE","rules":[]};a=authority()
        r=run_arm(candidate_id="CAND-A",arm="T2",repeat=1,mock_responses=(p,p,p),verify_callback=lambda p,ids:verify(p,a))
        self.assertEqual(r.terminal,"NEEDS_REPAIR_BUDGET_EXHAUSTED");self.assertIsNone(r.admitted)
    def test_fourth_rejected(self):
        with self.assertRaises(ValueError):run_arm(candidate_id="A",arm="T2",repeat=1,mock_responses=(None,)*4,verify_callback=None)
    def test_failure_not_negative(self):
        r=run_arm(candidate_id="A",arm="T2",repeat=1,mock_responses=(None,),verify_callback=None)
        self.assertEqual(r.terminal,"PROVIDER_ERROR");self.assertIsNone(r.admitted)
    def test_numeric_file_local(self):
        import numpy as np
        a=np.arange(100,dtype=float);b=np.arange(100,dtype=float)*2
        x=derive_roles(a,b,"step_up","NUM-000");self.assertEqual(x["source_step_threshold"],5.);self.assertEqual(x["target_noise_scale"],2.)
    def test_all_options(self):
        import numpy as np
        a=np.tile(np.arange(10,dtype=float),10)
        for alias in ALIASES:self.assertTrue(derive_roles(a,a,"step_up",alias))
    def test_exact_quantile_reuse(self):
        from paperworks.validation_v2.exp03b_numeric_v1 import summarize_column
        self.assertEqual(summarize_column([0,51.182211287863204,146.2285858740871])[1][1],84.08033376163371)
    def test_single_split_producer(self):
        import numpy as np
        from paperworks.validation_v2.exp03b_evidence_v1 import build_split_evidence
        from paperworks.validation_v2.exp01_scientific_v1 import SOURCE_VARIABLES,TARGET_VARIABLES
        from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER
        x=np.arange(100,dtype=float)[:,None]*np.ones((1,37))
        kwargs=dict(matrix=x,feature_order=tuple(P1_FEATURE_ORDER),pairs=((SOURCE_VARIABLES[0],TARGET_VARIABLES[0]),),all_sources=SOURCE_VARIABLES,input_hash="a"*64)
        e,_=build_split_evidence(split="train1",**kwargs)
        self.assertEqual(len(e[0].rows),20);self.assertEqual(len(e[0].rows[0].options),37)
        with self.assertRaises(ValueError):build_split_evidence(split="train4",**kwargs)
        with self.assertRaises(ValueError):build_split_evidence(split="train1",**(kwargs|{"all_sources":SOURCE_VARIABLES[:-1]}))


if __name__=="__main__":unittest.main()
