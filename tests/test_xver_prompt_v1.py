import copy
import json
import unittest
from dataclasses import asdict
import test_xver_semantic_execution_v1 as fixtures
from paperworks.validation_v2.xver_gdn_roles_v1 import GlobalSeedEvidenceV1
from paperworks.validation_v2.xver_gdn_provider_v1 import project_global_only
from paperworks.validation_v2.xver_prompt_v1 import request_body
from paperworks.validation_v2.exp03b_prompt_v2 import request_body as original
from paperworks.validation_v2.exp03b_contract_v1 import digest
from paperworks.validation_v2.exp03b_semantic_v2 import t0, proposal_document
from paperworks.validation_v2.exp03b_evidence_v1 import slice_id


class ExternalPromptTests(unittest.TestCase):
    def fixture(self):
        e=fixtures.ExternalSemanticTests().passing()
        seeds=tuple(GlobalSeedEvidenceV1('22.04','train1',s,e.source,e.target,tuple((h,.2,.3,-.1) for h in (1,5,10,30,60))) for s in (11,23,37))
        pack=project_global_only(version='22.04',train1=e,global_seeds=seeds,stat_association=.5,checkpoint_receipt_hash='a'*64)
        q={'split':'train2','dimension':'temporal_structure','alternatives':[{**asdict(r),'evidence_slice_id':slice_id('train2',(e.source,e.target),r.semantic,'structure')} for r in e.rows],'stat_association':.4,'gdn_rows':[(h,.1,.2,None) for h in (1,5,10,30,60)]}
        q={**q,'retrieval_hash':digest(q)}
        p=proposal_document(t0(e));f={'proposal_hash':digest(p),'issues':[{'failing_rule_index':0,'issue_code':'HORIZON_UNSTABLE'}],'remaining_call_budget':2,'evidence_retrieval_authorization':'ONE_STRUCTURAL_SLICE_ALL_ALTERNATIVES_CANONICAL'}
        return pack,{'previous_proposal':p,'feedback':f,'retrieval':q}

    def test_initial_identical_frozen_request(self):
        p,_=self.fixture();self.assertEqual(request_body(p),original(p))

    def test_extended_retrieval_roundtrip(self):
        p,r=self.fixture();body=request_body(p,repair=r)
        decoded=json.loads(body['input']);self.assertEqual(len(decoded['repair']['retrieval']['gdn_rows']),5)
        self.assertEqual(body['instructions'],original(p)['instructions'])

    def test_hidden_auxiliary_numeric_fields_rejected(self):
        for key in ('event_rows','numeric_policy','train3','T0_outcome','best_tuple','META_rank','candidate_arm'):
            p,r=self.fixture();q=r['retrieval'];q[key]=[];q['retrieval_hash']=digest({k:v for k,v in q.items() if k!='retrieval_hash'})
            with self.assertRaises(ValueError):request_body(p,repair=r)
            p,r=self.fixture();p[key]=[]
            with self.assertRaises(ValueError):request_body(p)

    def test_ten_row_event_not_cast_as_global(self):
        p,r=self.fixture();q=r['retrieval'];q['gdn_rows']*=2;q['retrieval_hash']=digest({k:v for k,v in q.items() if k!='retrieval_hash'})
        with self.assertRaises(ValueError):request_body(p,repair=r)

    def test_split_and_hash_taint(self):
        p,r=self.fixture();r['retrieval']['split']='train4'
        with self.assertRaises(ValueError):request_body(p,repair=r)

    def test_other_pair_retrieval_rejected(self):
        p,r=self.fixture();q=r['retrieval'];q['alternatives'][0]['evidence_slice_id']='EV-'+'0'*24
        q['retrieval_hash']=digest({k:v for k,v in q.items() if k!='retrieval_hash'})
        with self.assertRaises(ValueError):request_body(p,repair=r)
        p,r=self.fixture();r['retrieval']['retrieval_hash']='0'*64
        with self.assertRaises(ValueError):request_body(p,repair=r)


if __name__=='__main__':unittest.main()
