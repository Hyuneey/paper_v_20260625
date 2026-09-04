"""Synthetic-only external adapter equivalence and phase isolation."""
import ast
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import inspect
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from paperworks.validation_v2 import xver_confirmation_v1 as xc
from paperworks.validation_v2.exp01_relation_confirmation_v2 import fit_and_confirm_arbitrary_union_v2
from paperworks.validation_v2.xver_structural_v1 import build_structural
from paperworks.validation_v2.exp03b_evidence_v1 import build_split_evidence
from paperworks.validation_v2.exp03b_semantic_v2 import t0, Train1SemanticEvidenceV2, proposal_document
from paperworks.validation_v2.exp03b_hidden_v2 import Train2SemanticEvidenceV2, Train2HiddenVerifierAuthorityV2, verify
from paperworks.validation_v2.exp03b_execution_v2 import admit
from paperworks.validation_v2.exp03b_contract_v1 import SemanticTupleV1, StructuralTupleEvidenceV1, digest
from paperworks.validation_v2.xver_numeric_closure_v1 import authorize_t0_binding, ExternalT0ClosureV1
from paperworks.validation_v2.exp03b_custody_v1 import seal, publish
from paperworks.v6.relation_profiling_protocol_v1 import FROZEN_SOURCES, FROZEN_TARGETS
from paperworks.profiling.task039d1_execution_optimization_v1 import classify_all_source_isolation_indexed_v1, _event


class ExternalSemanticTests(unittest.TestCase):
    def passing(self, directions=('step_up','step_down')):
        source,target=FROZEN_SOURCES[0],FROZEN_TARGETS[0]
        cid='EXP03B-CAND-'+digest({'source':source,'target':target})[:20]
        rows=[]
        for sd in ('step_up','step_down'):
            for td in ('increase','decrease'):
                for h in (1,5,10,30,60):
                    semantic=SemanticTupleV1(sd,td,h)
                    good=sd in directions and td=='increase'
                    rows.append(StructuralTupleEvidenceV1(semantic,10,0.9 if good else 0.,0. if good else 0.9,3.,'EV-'+digest(asdict(semantic))[:24]))
        return Train1SemanticEvidenceV2(cid,source,target,'a'*64,tuple(sorted(rows,key=lambda r:r.semantic)))

    def test_t0_passing_field_access(self):
        for directions in (('step_up',),('step_up','step_down')):
            e=self.passing(directions);seen=set();original=StructuralTupleEvidenceV1.__getattribute__
            def access(obj,name):
                if not name.startswith('__'):seen.add(name)
                return original(obj,name)
            with patch.object(StructuralTupleEvidenceV1,'__getattribute__',access):p=t0(e)
            self.assertEqual(len(p.rules),len(directions))
            self.assertTrue({'semantic','support','consistency','opposite_consistency','effect','rank','passes','evidence_slice_id'}<=seen)
            self.assertTrue(all(r.semantic.horizon_seconds==1 for r in p.rules))
            unrelated={'STAT':999,'GDN':-999,'event':'TAINT'};before=proposal_document(p)
            unrelated.update(STAT=-999,GDN=999)
            self.assertEqual(before,proposal_document(t0(e)))

    def closure_documents(self, mutation=None):
        e=self.passing();p=t0(e);y=Train2SemanticEvidenceV2(e.candidate_id,e.source,e.target,'b'*64,e.rows)
        authority=Train2HiddenVerifierAuthorityV2(y,frozenset(r.evidence_slice_id for r in e.rows))
        ar=admit(p,authority,implementation_hash='c'*64,config_hash='d'*64)
        base={'version':'22.04','provider_calls':0,'execution_hash':'d'*64}
        o={'candidate_id':e.candidate_id,'proposal':proposal_document(p),'proposal_hash':digest(proposal_document(p))}
        a={'candidate_id':e.candidate_id,'status':'ACCEPTED','verifier':asdict(verify(p,authority)),'admission_hash':ar.receipt['self_hash'],'admission_receipt':ar.receipt}
        r={'candidate_id':e.candidate_id,'relations':[asdict(s) for s in p.semantic_set()]}
        ev={'candidate_id':e.candidate_id,'admitted':True,'semantic_exact':True}
        if mutation:mutation(o,a,r,ev,base)
        out=seal({**base,'records':[o]});adm=seal({**base,'records':[a],'outputs_hash':out['self_hash']})
        ref=seal({**base,'records':[r]});evaluation=seal({**base,'records':[ev],'outputs_hash':out['self_hash'],'admissions_hash':adm['self_hash'],'reference_hash':ref['self_hash']})
        return e.candidate_id,dict(zip(('T0_OUTPUTS_FROZEN.json','TRAIN2_ADMISSIONS_FROZEN.json','NORMAL_REFERENCE_FROZEN.json','SEMANTIC_EVALUATION_FROZEN.json'),(out,adm,ref,evaluation)))

    def test_successful_numeric_closure_and_mutations(self):
        mutations=(None,lambda o,a,r,e,b:o.update(proposal_hash='0'*64),lambda o,a,r,e,b:a.update(admission_hash='0'*64),lambda o,a,r,e,b:a.update(status='NEEDS_REPAIR'),lambda o,a,r,e,b:e.update(semantic_exact=False),lambda o,a,r,e,b:b.update(execution_hash='0'*64),lambda o,a,r,e,b:a['admission_receipt'].update(proposal_hash='0'*64))
        for mutation in mutations:
            cid,docs=self.closure_documents(mutation)
            with tempfile.TemporaryDirectory() as d:
                for name,doc in docs.items():publish(Path(d)/name,doc)
                if mutation:
                    with self.assertRaises(ValueError):authorize_t0_binding(Path(d),version='22.04',candidate_ids=(cid,),execution_hash='d'*64)
                else:
                    cap=authorize_t0_binding(Path(d),version='22.04',candidate_ids=(cid,),execution_hash='d'*64);cap.replay()
    def test_confirmation_AST_only_schema_interface_changes(self):
        old = inspect.getsource(fit_and_confirm_arbitrary_union_v2)
        new = inspect.getsource(xc.fit_and_confirm_mapped_union_v1)
        new = new.replace('fit_and_confirm_mapped_union_v1','fit_and_confirm_arbitrary_union_v2').replace('    mapped_sources: tuple[str, ...],\n','').replace('    mapped_targets: tuple[str, ...],\n','').replace('mapped_sources','FROZEN_SOURCES').replace('mapped_targets','FROZEN_TARGETS').replace('classify_mapped_isolation','classify_all_source_isolation_indexed_v1')
        self.assertEqual(ast.dump(ast.parse(old)), ast.dump(ast.parse(new)))

    def test_isolation_full_and_subset_oracle(self):
        data={s:tuple(_event(i) for i in (10+7*j,50+3*j,100)) for j,s in enumerate(FROZEN_SOURCES)}
        self.assertEqual(xc.classify_mapped_isolation(data),classify_all_source_isolation_indexed_v1(data))
        data.pop(FROZEN_SOURCES[-1])
        actual=xc.classify_mapped_isolation(data)
        for s, rows in actual.items():
            for e, isolated in rows:
                self.assertEqual(isolated, not any(abs(e.event_index-o.event_index)<=2 for other,events in data.items() if other!=s for o in events))

    def test_structural_reference_equivalence(self):
        order=FROZEN_SOURCES+FROZEN_TARGETS
        a=np.random.default_rng(391).normal(size=(180,len(order))).cumsum(axis=0)
        pairs=((FROZEN_SOURCES[0],FROZEN_TARGETS[0]),)
        for split in ('train1','train2'):
            old,_=build_split_evidence(split=split,matrix=a,feature_order=order,pairs=pairs,all_sources=FROZEN_SOURCES,input_hash='a'*64)
            new=build_structural(split=split,matrix=a,feature_order=order,pairs=pairs,all_sources=FROZEN_SOURCES,all_targets=FROZEN_TARGETS,input_hash='a'*64)
            self.assertEqual(tuple(r.structural for r in old[0].rows),new[0].rows)
            self.assertEqual(old[0].candidate_id,new[0].candidate_id)

    def test_t0_field_access(self):
        order=FROZEN_SOURCES+FROZEN_TARGETS
        a=np.random.default_rng(11).normal(size=(180,len(order))).cumsum(axis=0)
        e=build_structural(split='train1',matrix=a,feature_order=order,pairs=((order[0],FROZEN_TARGETS[0]),),all_sources=FROZEN_SOURCES,all_targets=FROZEN_TARGETS,input_hash='a'*64)[0]
        observed=set(); original=Train1SemanticEvidenceV2.__getattribute__
        def access(obj,name):
            if not name.startswith('__'):observed.add(name)
            return original(obj,name)
        with patch.object(Train1SemanticEvidenceV2,'__getattribute__',access):t0(e)
        self.assertEqual(observed,{'rows'})
        self.assertNotIn('GDN',inspect.getsource(t0));self.assertNotIn('STAT',inspect.getsource(t0))

    def test_t0_rejects_hidden_and_auxiliary(self):
        with self.assertRaises(ValueError):t0(object())

    def test_numeric_requires_complete_durable_closure(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):authorize_t0_binding(Path(d),version='22.04',candidate_ids=('a',),execution_hash='a'*64)
        with self.assertRaises(ValueError):ExternalT0ClosureV1(None,(),'a'*64,(),())

    def test_numeric_no_provider_schedule_impersonation(self):
        from paperworks.validation_v2 import xver_numeric_closure_v1 as m
        text=inspect.getsource(m)
        self.assertNotIn('ALL_ARM_OUTPUTS',text)
        self.assertNotIn('train4',text)
        self.assertNotIn('T1-B',text)

    def test_numeric_formula_equivalence_and_formal_conversion(self):
        from paperworks.validation_v2.xver_numeric_closure_v1 import bind_t0_rule
        from paperworks.validation_v2.exp03b_numeric_v1 import summarize_column, pooled_roles, roles_from_summary
        from paperworks.validation_v2.exp03b_binder_v2 import FIXED_ALIAS
        from paperworks.validation_v2.exp03b_conversion import convert
        e=self.passing();p=t0(e)
        y=Train2SemanticEvidenceV2(e.candidate_id,e.source,e.target,'b'*64,e.rows)
        ar=admit(p,Train2HiddenVerifierAuthorityV2(y,frozenset(r.evidence_slice_id for r in e.rows)),implementation_hash='c'*64,config_hash='d'*64)
        cid,docs=self.closure_documents()
        values=np.sin(np.arange(200)*.31)+np.arange(200)*.001
        summaries=[(summarize_column(values*k),summarize_column(values*k*.4)) for k in (1.,2.)]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name,doc in docs.items():publish(root/name,doc)
            cap=authorize_t0_binding(root,version='22.04',candidate_ids=(cid,),execution_hash='d'*64)
            r=bind_t0_rule(cap,ar,0,pair=(e.source,e.target),train1_summary=summaries[0],train2_summary=summaries[1])
            expected=pooled_roles(*(roles_from_summary(s,t,r.semantic.source_direction,FIXED_ALIAS) for s,t in summaries),train2_status='ACCEPTED')
            self.assertEqual(dict(r.candidate_roles),expected)
            self.assertEqual(r,bind_t0_rule(cap,ar,0,pair=(e.source,e.target),train1_summary=summaries[0],train2_summary=summaries[1]))
            descriptors=convert(root,root/'formal',(r,));self.assertEqual(len(descriptors),1)
            with self.assertRaises(ValueError):bind_t0_rule(cap,ar,0,pair=(e.source,e.target),train1_summary=(summaries[0][0],(0.,None,None,None)),train2_summary=summaries[1])


if __name__=='__main__':unittest.main()
