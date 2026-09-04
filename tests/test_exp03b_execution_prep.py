"""Closed prompt and bound admission regression tests; synthetic only."""
import unittest
from dataclasses import asdict
from test_exp03b_bindings_v1 import table,authority
from paperworks.validation_v2.exp03b_contract_v1 import t0,proposal_document,ProposalV1
from paperworks.validation_v2.exp03b_verifier_v1 import VerifierResultV1,verify
from paperworks.validation_v2.exp03b_execution import replay_arm,admit,VerifiedAdmission
from paperworks.validation_v2.exp03b_evaluation import admitted_majority
from paperworks.validation_v2.exp03b_prompt import request_body,validate_repair


class ExecutionPrepTests(unittest.TestCase):
    def test_arbitrary_initial_hidden_object(self):
        with self.assertRaises(ValueError):request_body({"split":"train1","train2_hidden":{"correct_horizon":60}})
    def test_feedback_answer(self):
        with self.assertRaises(ValueError):validate_repair({"previous_proposal":proposal_document(t0(table())),"feedback":{"correct_direction":"increase"},"retrieval":{"best_option":"NUM-001"}})
    def test_rejected_terminal(self):
        r=replay_arm(candidate_id="A",arm="T1",repeat=1,mock_responses=(proposal_document(t0(table())),),verify_callback=lambda p,i:VerifierResultV1("REJECTED",((0,"PRIVACY"),),0))
        self.assertEqual(r.terminal,"VERIFIER_REJECTION")
    def test_retrieval_terminal(self):
        def broken(p,v):raise ValueError("RETRIEVAL_FAILURE")
        r=replay_arm(candidate_id="A",arm="T2",repeat=1,mock_responses=({"decision":"NO_RULE","rules":[]},),verify_callback=lambda p,i:verify(p,authority()),retrieve_callback=broken)
        self.assertEqual(r.terminal,"RETRIEVAL_FAILURE")
    def test_admission_actual_authority(self):
        x=admit(t0(table()),authority(),implementation_hash="a"*64,config_hash="b"*64)
        x.replay();self.assertIn("hidden_authority_hash",x.receipt)
        self.assertEqual(admitted_majority("CAND-A",(x,x,None))[0],"MAJORITY")
    def test_admission_reject(self):
        with self.assertRaises(ValueError):admit(ProposalV1("NO_RULE",()),authority(),implementation_hash="a"*64,config_hash="b"*64)
    def test_admission_no_constructor(self):
        with self.assertRaises(ValueError):VerifiedAdmission(None,"A",t0(table()),{})
    def test_receipt_mutation(self):
        x=admit(t0(table()),authority(),implementation_hash="a"*64,config_hash="b"*64)
        x.receipt["verifier_status"]="REJECTED"
        with self.assertRaises(ValueError):x.replay()
    def test_pair_binding(self):
        x=admit(t0(table()),authority(),implementation_hash="a"*64,config_hash="b"*64)
        with self.assertRaises(ValueError):admitted_majority("OTHER",(x,x,None))


if __name__=="__main__":unittest.main()
