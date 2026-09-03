from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from test_validation_v2_formal_v4_authority_v1 import V2Fixture, h
from paperworks.validation_v2.exp04_protocol_v1 import exp04_opportunity_id_v1, EXP04_METHOD_IDS
from paperworks.validation_v2.exp05_runner_v1 import authorize_exp05_execution_v1
from paperworks.validation_v2.runtime_v1 import FormalV4ObservationWindowV1
from paperworks.validation_v2.isolation_forest_v1 import build_detector_environment_receipt_v1,NormalMatrixInputV1,_AUTHORIZED_FILES
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER
from paperworks.validation_v2.front_execution_v1 import fit_detectors_v1,freeze_predictions_v1,evaluate_frozen_predictions_v1
from paperworks.validation_v2.gdn_sidecar_v1 import seal
from paperworks.validation_v2.protocol_v1 import (build_validation_protocol_v1,ProtocolExecutionGuardV1,
    ProtocolOperationV1,build_policy_freeze_receipt_v1,ValidationProtocolError)
from paperworks.validation_v2.metric_contract_v1 import build_common_metric_contract_v1,PredictionCoordinateV1
from paperworks.validation_v2.evaluation_custody_v1 import (authorize_evaluation_label_access_v1,consume_evaluation_label_access_v1,
    verify_evaluation_inputs_unchanged_v1,destroy_evaluation_label_capability_v1,EvaluationCustodyError)


def synthetic_inputs(n=2048):
    import numpy as np
    rng=np.random.default_rng(314159)
    result=[]
    for role,count in (("NORMAL_FIT_PRIMARY",256),("NORMAL_FIT_SECONDARY",256),("NORMAL_CONFIRMATION_CALIBRATION",256),("NORMAL_POLICY_SELECTION_SANITY",n)):
        file_id,digest=_AUTHORIZED_FILES[role]
        result.append(NormalMatrixInputV1(file_id,digest,role,tuple(P1_FEATURE_ORDER),rng.normal(size=(count,37))))
    return tuple(result)


def synthetic_windows(fx,file_id,per_relation=10):
    windows=[]
    for descriptor in fx.descriptors:
        for i in range(per_relation):
            event=10+i*11
            decision=event+descriptor.selected_horizon_seconds+1
            up=descriptor.source_direction=="step_up"
            windows.append(FormalV4ObservationWindowV1(
                opportunity_id=exp04_opportunity_id_v1(file_id=file_id,row_index=decision,rule_id=descriptor.relation_id),
                relation_id=descriptor.relation_id,feature_contract_hash=fx.feature_binding.content_sha256,
                file_contract_hash=fx.file_binding.content_sha256,sampling_contract_hash=fx.sampling_binding.content_sha256,
                event_index=event,target_response_start_index=event+descriptor.selected_horizon_seconds,
                source_pre_values=(0.,0.) if up else (2.,2.),source_post_values=(2.,2.) if up else (0.,0.),
                target_baseline_values=(10.,10.),target_response_values=(11.,11.) if up and i%3==0 else (9.,9.) if not up and i%3==0 else (10.,10.),
                seconds_since_previous_source_trigger=None,seconds_to_nearest_other_source_trigger=None,future_window_complete=i%3!=2))
    return tuple(windows)


def synthetic_pipeline(root,*,rows=2048,relations=2,per_relation=3,tamper_memory=False):
    environment=build_detector_environment_receipt_v1()
    fx=V2Fixture(relation_count=relations)
    source_commit="b"*40 # Deliberately distinct from frozen portfolio production.
    try:
        inputs=synthetic_inputs(rows)
        protocol=build_validation_protocol_v1(source_commit="c"*40)
        metric=build_common_metric_contract_v1(protocol)
        guard=ProtocolExecutionGuardV1(protocol)
        policy=build_policy_freeze_receipt_v1(protocol=protocol,candidate_set_hash=h("cohort"),selection_objective="SYNTHETIC",
            tie_break_rule="SYNTHETIC",selected_config_hash=h("config"),authority_hash=fx.bundle.authority.authority_hash,
            method_policy_hashes=(h("policy"),),metric_contract_hash=metric.contract_hash)
        guard.freeze_policies(policy)
        guard.authorize(split_id="test1",operation=ProtocolOperationV1.DEVELOPMENT_PREDICTION)
        models=fit_detectors_v1(train1=inputs[0],train2=inputs[1],train3=inputs[2],environment=environment,
            source_commit=source_commit,pca_preregistration_hash=h("pca"),if_preregistration_hash=h("if"),custody_root=root)
        auth=authorize_exp05_execution_v1(execution_scope="SYNTHETIC_CONFORMANCE",preregistration_hash=h("exp05"),source_commit=fx.commit,bundle=fx.bundle)
        sidecar=seal({"bindings":{"portfolio_hash":fx.bundle.authority.authority_hash},"affects_runtime":False,"affects_predictions":False,
            "rows":[{"rule_id":d.relation_id,"descriptor_hash":d.descriptor_hash,"source":d.source,"target":d.target,
                "rule_horizon":d.selected_horizon_seconds,"learned_graph_status":"CORROBORATED_PAIR_AND_HORIZON"} for d in fx.descriptors]})
        result=freeze_predictions_v1(models=models,evaluation_input=inputs[3],expected_role="NORMAL_POLICY_SELECTION_SANITY",
            bundle=fx.bundle,context=fx.context,repository_root=fx.root,custody_root=root,
            windows=synthetic_windows(fx,inputs[3].file_id,per_relation),exp05_authorization=auth,
            source_commit=source_commit,evaluation_policy_hash=h("policy"),metric_contract_hash=metric.contract_hash,
            experiment_id="SYNTHETIC-FRONT-PREFLIGHT",dataset_id="SYNTHETIC-DATASET",sidecar=sidecar)
        capability=authorize_evaluation_label_access_v1(artifact_root=root,exact_method_ids=EXP04_METHOD_IDS,
            prediction_references=result["references"],evaluation_policy_hash=h("policy"),metric_contract_hash=metric.contract_hash,
            source_commit=source_commit,bundle_relative_path="evaluation/bundle.json",bundle_receipt_relative_path="evaluation/bundle.freeze.json",
            expected_bundle_receipt=result["bundle_receipt"])
        guard.record_development_prediction_frozen()
        correct=dict(exact_method_ids=EXP04_METHOD_IDS,evaluation_policy_hash=h("policy"),metric_contract_hash=metric.contract_hash,execution_source_commit=source_commit)
        for key,value in (("evaluation_policy_hash",h("wrong")),("metric_contract_hash",h("wrong")),("execution_source_commit","d"*40)):
            try:guard.authorize_multi_method_label_metrics_v1(capability,**{**correct,key:value})
            except (ValidationProtocolError,EvaluationCustodyError):pass
            else:raise AssertionError("WRONG_MULTI_METHOD_BINDING_ACCEPTED")
        guard.authorize_multi_method_label_metrics_v1(capability,**correct)
        selftest=[]
        consume_evaluation_label_access_v1(capability,lambda:selftest.append("SYNTHETIC_ONLY"))
        guard.record_development_labels_accessed();guard.complete()
        verify_evaluation_inputs_unchanged_v1(capability)
        destroy_evaluation_label_capability_v1(capability)
        if selftest!=["SYNTHETIC_ONLY"]:raise AssertionError("callback census")
        coordinates=tuple(PredictionCoordinateV1(inputs[3].file_id,inputs[3].file_content_sha256,i,1000+i) for i in range(rows))
        if tamper_memory=="native":
            result["native"]=result["native"][1:]
        elif tamper_memory:
            key=EXP04_METHOD_IDS[0];values=result["masks"][key]
            result["masks"][key]=(not values[0],*values[1:])
        result["metrics"]=evaluate_frozen_predictions_v1(predictions=result,coordinates=coordinates,
            label_values=tuple(int(30<=i<45) for i in range(rows)),label_authority_hash=h("synthetic-labels"),
            protocol=protocol,contract=metric,context=fx.context,dataset_id="SYNTHETIC-DATASET",custody_root=root)
        return result
    finally:
        fx.close()


class FrontPipelineTests(unittest.TestCase):
    def test_full_synthetic_five_method_pipeline(self):
        try:build_detector_environment_receipt_v1()
        except ValueError:self.skipTest("exact frozen detector environment required")
        with tempfile.TemporaryDirectory() as directory:
            result=synthetic_pipeline(Path(directory))
            self.assertEqual(tuple(sorted(result["masks"])),EXP04_METHOD_IDS)
            self.assertEqual(result["trace_receipt"]["unit_count"],6)
            self.assertEqual(result["trace_receipt"]["native_outcomes"],{"PASS":2,"FAIL":2,"ABSTAIN":2})
            self.assertTrue(all(len(v)==2048 for v in result["masks"].values()))

    def test_metrics_reject_memory_divergence_from_frozen_bytes(self):
        try:build_detector_environment_receipt_v1()
        except ValueError:self.skipTest("exact frozen detector environment required")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,"IN_MEMORY_PREDICTION"):
                synthetic_pipeline(Path(directory),tamper_memory=True)

    def test_metrics_reject_native_census_deletion(self):
        try:build_detector_environment_receipt_v1()
        except ValueError:self.skipTest("exact frozen detector environment required")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,"NATIVE_CENSUS_DIFFERS"):
                synthetic_pipeline(Path(directory),tamper_memory="native")


if __name__=="__main__":unittest.main()
