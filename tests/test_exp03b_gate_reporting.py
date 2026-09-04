import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
from fractions import Fraction
from unittest.mock import patch
from test_exp03b_bindings_v1 import table,authority
from paperworks.validation_v2.exp03b_contract_v1 import digest,t0,SemanticTupleV1
from paperworks.validation_v2.exp03b_execution import admit
from paperworks.validation_v2.exp03b_reporting import report
from paperworks.validation_v2.exp03b_provider_gate import ProviderCallGate

class GateReportingTests(unittest.TestCase):
    def gate(self):
        b={'self_hash':'a'*64,'model':'gpt-5.4-mini-2026-03-17','maximum_calls':3,'input_tokens_per_call_cap':100,'output_tokens_per_call_cap':20,'maximum_input_tokens':300,'maximum_output_tokens':60,'standard_api_cost_ceiling_usd':'1'}
        return ProviderCallGate(b,{'gate':'DG-03B','status':'APPROVED','budget_hash':'a'*64,'execution_freeze_hash':'b'*64},'b'*64)
    def request(self):return {'model':'gpt-5.4-mini-2026-03-17','max_output_tokens':20}
    def finish(self,g):return g.reconcile(input_tokens=10,output_tokens=5,response_hash='c'*64,model=g.budget['model'],latency=.1)
    def test_wrong_gate_rejected(self):
        with self.assertRaises(ValueError):ProviderCallGate({}, {'gate':'DG-03','status':'APPROVED'},'b'*64)
    def test_one_inflight(self):
        g=self.gate();g.reserve(slot='1',request=self.request(),input_upper_bound=50)
        with self.assertRaises(ValueError):g.reserve(slot='2',request=self.request(),input_upper_bound=50)
    def test_receipt_first(self):
        g=self.gate();g.reserve(slot='1',request=self.request(),input_upper_bound=50);r=self.finish(g)
        with self.assertRaises(ValueError):g.reserve(slot='2',request=self.request(),input_upper_bound=50)
        g.accept_one_call_receipt(digest(r),persisted_and_replayed=True,privacy_pass=True,schema_pass=True)
        g.reserve(slot='2',request=self.request(),input_upper_bound=50)
    def test_fourth_call_rejected(self):
        g=self.gate()
        for i in range(3):
            g.reserve(slot=str(i),request=self.request(),input_upper_bound=50);r=self.finish(g)
            if i==0:g.accept_one_call_receipt(digest(r),persisted_and_replayed=True,privacy_pass=True,schema_pass=True)
        with self.assertRaises(ValueError):g.reserve(slot='4',request=self.request(),input_upper_bound=50)
    def test_snapshot_not_alias(self):
        g=self.gate();r=self.request();r['model']='gpt-5.4-mini'
        with self.assertRaises(ValueError):g.reserve(slot='1',request=r,input_upper_bound=50)
    def test_false_probe_rejected(self):
        g=self.gate();g.reserve(slot='1',request=self.request(),input_upper_bound=50);r=self.finish(g)
        with self.assertRaises(ValueError):g.accept_one_call_receipt(digest(r),persisted_and_replayed=False,privacy_pass=True,schema_pass=True)
    def test_usage_cap(self):
        g=self.gate();g.reserve(slot='1',request=self.request(),input_upper_bound=50)
        with self.assertRaises(ValueError):g.reconcile(input_tokens=101,output_tokens=1,response_hash='c'*64,model=g.budget['model'],latency=0.)
    def test_horizon_separate_from_target(self):
        x=admit(t0(table()),authority(),implementation_hash='a'*64,config_hash='b'*64)
        actual=x.proposal.rules[0].semantic
        truth=SemanticTupleV1(actual.source_direction,'decrease' if actual.target_direction=='increase' else 'increase',actual.horizon_seconds)
        out=report({'CAND-A':(truth,)},{'CAND-A':(x,x,x)},{'CAND-A':('ACCEPTED_RULE_SET',)*3})
        self.assertEqual(out['exact_horizon_accuracy']['value'],Fraction(1))
        self.assertEqual(out['target_direction_accuracy']['value'],Fraction(0))
    def test_actual_formal_descriptor_conversion(self):
        from paperworks.validation_v2.exp03b_numeric_v1 import roles_from_summary
        from paperworks.validation_v2.exp03b_conversion import convert
        roles=roles_from_summary((1.,(1.,2.,3.),(1.,2.,3.),(1.,2.,3.)),(1.,(1.,2.,3.),None,None),'step_up','NUM-000')
        r=SimpleNamespace(candidate_id='SYNTH',source='S',target='T',semantic=SemanticTupleV1('step_up','increase',5),alias='NUM-000',train2_acceptance_hash='a'*64,train3_reference_hash='b'*64,candidate_roles=tuple(roles.items()))
        with tempfile.TemporaryDirectory() as d:
            result=convert(Path(d),Path(d)/'private',(r,))
            self.assertEqual(len(result),1)
            self.assertTrue((Path(d)/'private/CONVERSION_RECEIPT.json').exists())
    def test_exact_preferred_target_tuple_required(self):
        from paperworks.validation_v2.exp03b_admission_verifier import verify
        auth=authority();rows=[]
        alternative=SemanticTupleV1('step_up','decrease',10)
        for row in auth.evidence.rows:
            s=row.structural
            if s.semantic==alternative:s=replace(s,support=5,consistency=.6,effect=2.)
            elif s.semantic==SemanticTupleV1('step_up','increase',5):s=replace(s,consistency=.9,effect=3.)
            rows.append(replace(row,structural=s))
        auth=replace(auth,evidence=replace(auth.evidence,rows=tuple(rows)))
        p=t0(table());p=replace(p,rules=(replace(p.rules[0],semantic=alternative),))
        self.assertEqual(verify(p,auth).status,'NEEDS_REPAIR')
        self.assertIn((0,'RULE_NOT_JUSTIFIED'),verify(p,auth).issues)

if __name__=='__main__':unittest.main()
