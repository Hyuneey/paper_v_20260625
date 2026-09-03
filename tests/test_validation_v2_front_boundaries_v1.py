from __future__ import annotations
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace

from test_validation_v2_evaluation_custody_v1 import MultiMethodEvaluationCustodyTests,artifact,H_B,METHODS
from paperworks.validation_v2.evaluation_custody_v1 import (persist_dense_prediction_before_label_v1,PredictionFreezeReferenceV1,EvaluationCustodyError,
    destroy_evaluation_label_capability_v1,consume_evaluation_label_access_v1)
from paperworks.validation_v2.front_label_adapter_v1 import parse_labels_v1
from test_validation_v2_formal_v4_authority_v1 import V2Fixture,h
from test_validation_v2_front_pipeline_v1 import synthetic_windows
from paperworks.validation_v2.exp05_runner_v1 import authorize_exp05_execution_v1,execute_and_materialize_formal_v4_batch_v1
from paperworks.validation_v2.front_runtime_v1 import iter_evaluated_units_v1
from paperworks.validation_v2.front_runtime_v1 import iter_rule_windows_v1
from paperworks.validation_v2.exp02_bindings_v2a import extract_candidate_specific_events_v1
from paperworks.validation_v2.exp05_batch_custody_v2 import publish_full_unit_batch_v2,replay_full_unit_batch_v2


class CrossCensusTests(MultiMethodEvaluationCustodyTests):
    def test_foreign_file_identity_rejected_before_bundle(self):
        first=self.freeze_method(METHODS[0])
        value=artifact(METHODS[1])
        value=replace(value,records=tuple(replace(r,file_content_sha256="f"*64) for r in value.records))
        receipt=persist_dense_prediction_before_label_v1(value,artifact_root=self.root,prediction_relative_path="foreign.json",receipt_relative_path="foreign.receipt.json")
        second=PredictionFreezeReferenceV1(METHODS[1],"foreign.json","foreign.receipt.json",receipt)
        with self.assertRaisesRegex(EvaluationCustodyError,"COORDINATE_CENSUS"):
            self.freeze_bundle((first,second))
        self.assertFalse((self.root/"bundle/evaluation.json").exists())

    def test_destroyed_capability_cannot_read(self):
        refs=self.freeze_methods();receipt=self.freeze_bundle(refs);capability=self.authorize(refs,receipt)
        destroy_evaluation_label_capability_v1(capability)
        reads=[]
        with self.assertRaises(EvaluationCustodyError):consume_evaluation_label_access_v1(capability,lambda:reads.append(1))
        self.assertEqual(reads,[])


class ExactLabelTests(unittest.TestCase):
    def test_identity_alignment_and_strict_tokens(self):
        timestamps=("2000-01-01 00:00:00","2000-01-01 00:00:01")
        for token in ("1","1.0","true"," 1"):
            raw=f"timestamp,label\n{timestamps[0]},0\n{timestamps[1]},{token}\n".encode()
            kwargs=dict(expected_hash=sha256(raw).hexdigest(),expected_size=len(raw),timestamps=timestamps)
            if token=="1":self.assertEqual(parse_labels_v1(raw,**kwargs),(0,1))
            else:
                with self.assertRaises(ValueError):parse_labels_v1(raw,**kwargs)
        with self.assertRaises(ValueError):parse_labels_v1(raw,expected_hash="f"*64,expected_size=len(raw),timestamps=timestamps)


class FullTraceCustodyTests(unittest.TestCase):
    def test_same_call_units_equal_reference_and_mutation_rejected(self):
        fx=V2Fixture()
        try:
            auth=authorize_exp05_execution_v1(execution_scope="SYNTHETIC_CONFORMANCE",preregistration_hash=h("exp05"),source_commit=fx.commit,bundle=fx.bundle)
            windows=synthetic_windows(fx,"SYNTHETIC",3)
            reference=execute_and_materialize_formal_v4_batch_v1(fx.bundle,authorization=auth,execution_context=fx.context,repository_root=fx.root,windows=windows)
            receipts=[]
            units=tuple(u for _,_,u in iter_evaluated_units_v1(bundle=fx.bundle,context=fx.context,root=fx.root,authorization=auth,windows=windows,finalization_receipts=receipts))
            self.assertEqual([u.to_dict() for u in units],[u.to_dict() for u in reference.units])
            self.assertEqual(receipts[0].evaluated_window_count,len(windows))
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/"units.jsonl";rp=Path(directory)/"receipt.json"
                receipt=publish_full_unit_batch_v2(units=units,artifact_path=path,receipt_path=rp)
                self.assertEqual(receipt["acceptance"],"PROVISIONAL_UNTIL_FULL_CENSUS_FINALIZATION")
                path.write_bytes(path.read_bytes()+b" ")
                with self.assertRaises(ValueError):replay_full_unit_batch_v2(artifact_path=path,receipt_path=rp,expected_receipt=receipt)
        finally:fx.close()


class TriggerAssemblyTests(unittest.TestCase):
    def test_relation_local_refractory_other_source_union_and_eof(self):
        import numpy as np
        source=np.repeat([0.,2.,0.,4.,0.,4.,0.,4.],10)
        other=np.repeat([0.,0.,3.,0.,3.,0.,3.,0.],10)
        matrix=np.column_stack((source,np.ones(80),other))
        descriptors=tuple(SimpleNamespace(relation_id=rid,source=s,target="T",source_direction=direction,selected_horizon_seconds=horizon)
            for rid,s,direction,horizon in (("R1","S","step_up",1),("R2","S","step_down",10),("R3","U","step_up",5)))
        roles={"source_pre_window_seconds":5.,"source_post_window_seconds":5.,"target_baseline_window_seconds":5.,
            "target_response_window_seconds":5.,"minimum_source_stability_fraction":.8,"source_stability_tolerance":0.,
            "target_noise_scale":1.,"source_refractory_seconds":10.,"cross_source_isolation_radius_seconds":1.}
        numeric=tuple((d.relation_id,tuple((k,"ref",v) for k,v in {**roles,"source_step_threshold":3. if d.relation_id=="R2" else 1.}.items())) for d in descriptors)
        binding=SimpleNamespace(content_sha256=h("binding"))
        context=SimpleNamespace(feature_contract_binding=binding,file_contract_binding=binding,sampling_contract_binding=binding)
        bundle=SimpleNamespace(authority=SimpleNamespace(descriptors=descriptors,numeric_authority_binding=binding))
        events={d.relation_id:extract_candidate_specific_events_v1(matrix[:,0 if d.source=="S" else 2],threshold=3. if d.relation_id=="R2" else 1.,tolerance=0.) for d in descriptors}
        with mock.patch("paperworks.validation_v2.front_runtime_v1.load_formal_v4_numeric_value_map_v1",return_value=numeric):
            windows=tuple(iter_rule_windows_v1(bundle=bundle,context=context,root=Path("."),matrix=matrix,feature_order=("S","T","U"),file_id="SYNTHETIC"))
        expected_count=sum(e.direction==d.source_direction for d in descriptors for e in events[d.relation_id])
        self.assertEqual(len(windows),expected_count)
        for window in windows:
            d=next(d for d in descriptors if d.relation_id==window.relation_id)
            local=[e.event_index for e in events[d.relation_id]]
            pos=local.index(window.event_index)
            self.assertEqual(window.seconds_since_previous_source_trigger,None if pos==0 else float(local[pos]-local[pos-1]))
            others={e.event_index for candidate in descriptors if candidate.source!=d.source for e in events[candidate.relation_id]}
            self.assertEqual(window.seconds_to_nearest_other_source_trigger,min(abs(i-window.event_index) for i in others) if others else None)
            self.assertEqual(window.future_window_complete,window.target_response_start_index+5<=len(matrix))

    def test_mutation_before_finalization_never_accepts_census(self):
        fx=V2Fixture()
        try:
            auth=authorize_exp05_execution_v1(execution_scope="SYNTHETIC_CONFORMANCE",preregistration_hash=h("exp05"),source_commit=fx.commit,bundle=fx.bundle)
            receipts=[]
            iterator=iter_evaluated_units_v1(bundle=fx.bundle,context=fx.context,root=fx.root,authorization=auth,windows=synthetic_windows(fx,"SYNTHETIC",1),finalization_receipts=receipts)
            next(iterator)
            path=fx.root/"authority/numeric.json"
            path.write_bytes(path.read_bytes()+b" ")
            with self.assertRaises(ValueError):tuple(iterator)
            self.assertEqual(receipts,[])
        finally:fx.close()
