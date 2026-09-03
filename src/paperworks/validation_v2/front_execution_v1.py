"""Five-method frozen orchestration over caller-authorized inputs; no data I/O."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
import pickle
from pathlib import Path
from typing import Any

from .isolation_forest_v1 import (fit_isolation_forest_v1,calibrate_isolation_forest_threshold_v1,predict_isolation_forest_v1)
from .pca_spe_v2 import fit_pca_spe_v2,calibrate_pca_spe_threshold_v2,predict_pca_spe_v2
from .exp04_protocol_v1 import EXP04_METHOD_IDS,RuleOutcomeEvidenceV1,fuse_detector_with_rules_v1
from .prediction_custody_v1 import D1PredictionArtifactV2,D1PredictionRecordV2,persist_prediction_before_label_v1,replay_prediction_before_label_v1
from .evaluation_custody_v1 import (DenseBooleanPredictionArtifactV1,DenseBooleanPredictionRecordV1,
    PredictionFreezeReferenceV1,persist_dense_prediction_before_label_v1,freeze_multi_method_evaluation_bundle_v1,replay_dense_prediction_before_label_v1)
from .exp05_batch_custody_v2 import publish_full_unit_batch_v2
from .front_runtime_v1 import iter_evaluated_units_v1
from .private_vault_v1 import publish_private_bytes_v1
from .gdn_sidecar_v1 import seal, replay, annotate_explanation_v1

PCA="V2_D0_PCA_SPE_NORMAL_ONLY_V1"
IF="V2_ISOLATION_FOREST_FIXED_NORMAL_ONLY_V1"
RULE="V2_VERIFIED_RELATIONAL_RULE_ONLY_V1"
PCA_FUSION="V2_D2_PCA_RULE_CONFIRM2_SAME_SECOND_V1"
IF_FUSION="V2_D2_IF_RULE_CONFIRM2_SAME_SECOND_V1"


@dataclass(frozen=True)
class NativeCoordinateV1:
    event_index:int
    target_response_start_index:int


def native_census_document_v1(native):
    return seal({"schema":"native_census_v1","rows":[{"event":w.event_index,"response_start":w.target_response_start_index,
        "decision":decision,"trace":trace.to_dict()} for w,trace,decision in native]})


def write_json_v1(path: Path, document: dict) -> None:
    publish_private_bytes_v1(path,(json.dumps(document,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)+"\n").encode())


def fit_detectors_v1(*,train1,train2,train3,environment,source_commit:str,pca_preregistration_hash:str,if_preregistration_hash:str,custody_root:Path):
    pca=fit_pca_spe_v2(train1,train2,source_commit=source_commit,preregistration_hash=pca_preregistration_hash,environment=environment)
    forest=fit_isolation_forest_v1(train1,train2,source_commit=source_commit,preregistration_hash=if_preregistration_hash,environment=environment)
    pca_threshold=calibrate_pca_spe_threshold_v2(pca,train3,expected_fit_receipt_hash=pca.fit_receipt.receipt_hash)
    if_threshold=calibrate_isolation_forest_threshold_v1(forest,train3,expected_fit_receipt_hash=forest.fit_receipt.self_hash)
    models=(pca,forest,pca_threshold,if_threshold)
    payload=pickle.dumps(models,protocol=5)
    publish_private_bytes_v1(custody_root/"models/fitted.private.pkl",payload)
    reopened=(custody_root/"models/fitted.private.pkl").read_bytes()
    if reopened!=payload:
        raise ValueError("MODEL_REPLAY_FAILED")
    # Only our just-published, hash-verified private pickle is deserialized.
    restored=pickle.loads(reopened)
    if (restored[0].fit_receipt!=pca.fit_receipt or restored[1].fit_receipt!=forest.fit_receipt
        or restored[2]!=pca_threshold or restored[3]!=if_threshold):
        raise ValueError("MODEL_AUTHORITY_REPLAY_FAILED")
    import numpy as np
    # sklearn pickle byte layout is not invariant across deserialize/serialize.
    # Preserve the original live authority; independently replay tree state and
    # normal calibration scores from the exact persisted model bytes.
    if forest.estimator.get_params()!=restored[1].estimator.get_params():
        raise ValueError("RESTORED_FOREST_PARAMETER_MISMATCH")
    for original_tree,restored_tree in zip(forest.estimator.estimators_,restored[1].estimator.estimators_,strict=True):
        left=original_tree.tree_.__getstate__();right=restored_tree.tree_.__getstate__()
        for key in left:
            if not np.array_equal(left[key],right[key]):raise ValueError("RESTORED_TREE_STATE_MISMATCH")
    if not np.array_equal(forest.estimator.score_samples(train3.values),restored[1].estimator.score_samples(train3.values)):
        raise ValueError("RESTORED_FOREST_SCORE_MISMATCH")
    write_json_v1(custody_root/"models/authority.private.json",seal({"pca_fit_hash":pca.fit_receipt.receipt_hash,
        "if_fit_hash":forest.fit_receipt.self_hash,"pca_threshold_hash":pca_threshold.receipt_hash,
        "if_threshold_hash":if_threshold.self_hash,"model_bytes_sha256":sha256(payload).hexdigest(),
        "source_commit":source_commit,"environment_hash":environment.self_hash,
        "restoration":"EXACT_BYTES_RECEIPTS_TREES_AND_NORMAL_CALIBRATION_SCORES",
        "execution_model":"ORIGINAL_HASH_BOUND_LIVE_STATE"}))
    return models


def freeze_predictions_v1(*, models, evaluation_input, expected_role:str, bundle, context, repository_root:Path,
    custody_root:Path, windows, exp05_authorization, source_commit:str, evaluation_policy_hash:str,
    metric_contract_hash:str, experiment_id:str, dataset_id:str, sidecar:dict|None=None) -> dict[str,Any]:
    """All prediction generators terminate before returning a durable bundle."""
    pca,forest,pca_threshold,if_threshold=models
    file_id=evaluation_input.file_id
    file_hash=evaluation_input.file_content_sha256
    n=len(evaluation_input.values)
    masks={}
    for method,model,threshold,predict,fit_hash,threshold_hash in (
        (PCA,pca,pca_threshold,predict_pca_spe_v2,pca.fit_receipt.receipt_hash,pca_threshold.receipt_hash),
        (IF,forest,if_threshold,predict_isolation_forest_v1,forest.fit_receipt.self_hash,if_threshold.self_hash)):
        scores,alarms,binding=predict(model,threshold,evaluation_input,expected_role=expected_role,
            expected_fit_receipt_hash=fit_hash,expected_threshold_receipt_hash=threshold_hash)
        masks[method]=tuple(bool(v) for v in alarms)
        publish_private_bytes_v1(custody_root/f"models/{method}.scores.private.bin",scores.tobytes(order="C"))
    references={}
    def freeze(method,mask,authority_hash):
        artifact=DenseBooleanPredictionArtifactV1(artifact_id=method+"-PREDICTION",method_id=method,config_id=method+"-CONFIG",
            experiment_id=experiment_id,dataset_id=dataset_id,split_role="DEVELOPMENT_TEST1",authority_hash=authority_hash,
            evaluation_policy_hash=evaluation_policy_hash,metric_contract_hash=metric_contract_hash,
            file_contract_hash=context.file_contract_binding.content_sha256,source_commit=source_commit,
            records=tuple(DenseBooleanPredictionRecordV1(file_id,file_hash,i,value) for i,value in enumerate(mask)))
        relative=f"predictions/{method}.json"; receipt_relative=f"predictions/{method}.freeze.json"
        receipt=persist_dense_prediction_before_label_v1(artifact,artifact_root=custody_root,prediction_relative_path=relative,receipt_relative_path=receipt_relative)
        references[method]=PredictionFreezeReferenceV1(method,relative,receipt_relative,receipt)
        return artifact
    freeze(PCA,masks[PCA],pca_threshold.receipt_hash)
    freeze(IF,masks[IF],if_threshold.self_hash)
    counts=Counter(); evidence=[]; native=[]; fail_groups=defaultdict(list)
    full_units=[]; batch_receipts=[]; annotations=[]; annotation_batches=[]; finalization=[]
    opportunity_ids=set(); tail_count=0; fidelity_count=0; annotated_count=0
    side_rows={r["rule_id"]:r for r in sidecar["rows"]} if sidecar else {}
    descriptors={d.relation_id:d for d in bundle.authority.descriptors}
    def flush():
        index=len(batch_receipts)
        batch_receipts.append(publish_full_unit_batch_v2(units=tuple(full_units),
            artifact_path=custody_root/f"traces/batch-{index:05d}.jsonl",receipt_path=custody_root/f"traces/batch-{index:05d}.receipt.json"))
        if annotations:
            doc=seal({"annotations":annotations,"unit_batch_hash":batch_receipts[-1]["self_hash"]})
            write_json_v1(custody_root/f"traces/batch-{index:05d}.annotations.json",doc)
            annotation_batches.append(doc["self_hash"])
        full_units.clear(); annotations.clear()
    for window,trace,unit in iter_evaluated_units_v1(bundle=bundle,context=context,root=repository_root,authorization=exp05_authorization,
                                                   windows=windows,finalization_receipts=finalization):
        if trace.opportunity_id in opportunity_ids:
            raise ValueError("DUPLICATE_OPPORTUNITY_ID")
        opportunity_ids.add(trace.opportunity_id)
        counts[trace.final_outcome]+=1
        descriptor=descriptors[trace.relation_id]
        # Opportunity identity is frozen at logical response-end, even past EOF.
        decision=int(trace.opportunity_id.split("|")[2])
        native.append((NativeCoordinateV1(window.event_index,window.target_response_start_index),trace,decision))
        if decision>=n:
            if trace.final_outcome!="ABSTAIN" or trace.alarm_emitted:
                raise ValueError("OUT_OF_CENSUS_NON_ABSTAIN")
            tail_count+=1
        else:
            row=RuleOutcomeEvidenceV1(file_id=file_id,feature_file_sha256=file_hash,row_index=decision,rule_id=trace.relation_id,
                source_id=descriptor.source,outcome=trace.final_outcome,descriptor_hash=descriptor.descriptor_hash,
                trace_hash=trace.trace_hash,portfolio_authority_hash=bundle.authority.authority_hash,
                runtime_authorization_hash=bundle.receipt.authorization_hash,runtime_trace=trace)
            evidence.append(row)
            if trace.final_outcome=="FAIL":fail_groups[decision].append(row)
        # Validator already ran on the exact full unit in the same call path.
        fidelity_count+=1
        full_units.append(unit)
        if sidecar:
            annotation=annotate_explanation_v1(unit.explanation.to_dict(),row=side_rows[descriptor.relation_id],
                descriptor=descriptor.to_dict(),sidecar=sidecar,expected_sidecar_hash=sidecar["self_hash"])
            annotated_count+=annotation["optional_gdn_clause"] is not None
            annotations.append(annotation)
        if len(full_units)==256:flush()
    if full_units:flush()
    if sum(r["unit_count"] for r in batch_receipts)!=len(opportunity_ids):
        raise ValueError("EXP05_FULL_CENSUS_MISMATCH")
    if len(finalization)!=1 or finalization[0].evaluated_window_count!=len(opportunity_ids):
        raise ValueError("EXP05_FINAL_AUTHORITY_REPLAY_CENSUS_MISMATCH")
    native_document=native_census_document_v1(native)
    write_json_v1(custody_root/"traces/native-census.private.json",native_document)
    d1_records=tuple(D1PredictionRecordV2(file_id,file_hash,i,bool(fail_groups[i]),
        tuple(sorted(r.rule_id for r in fail_groups[i])),tuple(sorted(r.trace_hash for r in fail_groups[i]))) for i in range(n))
    d1=D1PredictionArtifactV2(method_id=RULE,config_id=RULE+"-CONFIG",experiment_id=experiment_id,dataset_id=dataset_id,
        split_role="DEVELOPMENT_TEST1",authority_hash=bundle.authority.authority_hash,runtime_authorization_hash=bundle.receipt.authorization_hash,
        execution_context_hash=context.context_hash,source_commit=source_commit,portfolio_hash=bundle.authority.authority_hash,
        file_contract_hash=context.file_contract_binding.content_sha256,records=d1_records)
    d1_receipt=persist_prediction_before_label_v1(d1,artifact_root=custody_root,prediction_relative_path="predictions/d1.native.json",
        receipt_relative_path="predictions/d1.native.freeze.json")
    masks[RULE]=tuple(r.alarm for r in d1_records)
    freeze(RULE,masks[RULE],bundle.authority.authority_hash)
    for base,method in ((PCA,PCA_FUSION),(IF,IF_FUSION)):
        decisions=fuse_detector_with_rules_v1(base_custody_root=custody_root,base_prediction_reference=references[base],
            expected_evaluation_policy_hash=evaluation_policy_hash,expected_metric_contract_hash=metric_contract_hash,
            d1_custody_root=custody_root,d1_receipt_relative_path="predictions/d1.native.freeze.json",d1_freeze_receipt=d1_receipt,
            rule_outcomes=tuple(evidence),authorized_runtime=bundle,execution_context=context,repository_root=repository_root,
            execution_source_commit=source_commit)
        masks[method]=tuple(d.final_alarm for d in decisions)
        if any(base_alarm and not final for base_alarm,final in zip(masks[base],masks[method],strict=True)):
            raise ValueError("FUSION_BASE_PRESERVATION_FAILED")
        freeze(method,masks[method],evaluation_policy_hash)
    references_tuple=tuple(references[m] for m in EXP04_METHOD_IDS)
    frozen=freeze_multi_method_evaluation_bundle_v1(artifact_root=custody_root,bundle_id=experiment_id+"-FIVE-METHOD-BUNDLE",
        exact_method_ids=EXP04_METHOD_IDS,prediction_references=references_tuple,evaluation_policy_hash=evaluation_policy_hash,
        metric_contract_hash=metric_contract_hash,source_commit=source_commit,bundle_relative_path="evaluation/bundle.json",
        bundle_receipt_relative_path="evaluation/bundle.freeze.json")
    trace_receipt=seal({"schema":"exp05_full_census_receipt_v2","acceptance":"ACCEPTED_AFTER_FINAL_AUTHORITY_REPLAY",
        "native_census_hash":native_document["self_hash"],
        "unit_count":len(opportunity_ids),"native_outcomes":dict(counts),
        "tail_abstain_without_physical_decision":tail_count,"fidelity_unit_count":fidelity_count,"annotated_unit_count":annotated_count,
        "full_unit_batch_receipts":batch_receipts,"annotation_batch_hashes":annotation_batches,
        "opportunity_census_hash":sha256(json.dumps(sorted(opportunity_ids),separators=(",",":")).encode()).hexdigest(),
        "runtime_finalization_receipts":[r.to_dict() for r in finalization],"human_usefulness":"UNVALIDATED",
        "runner_source_commit":source_commit,"authority_source_commit":bundle.authority.source_commit})
    write_json_v1(custody_root/"traces/full-census.receipt.json",trace_receipt)
    return dict(masks=masks,references=references_tuple,bundle_receipt=frozen,d1=d1,d1_receipt=d1_receipt,
                native=native,trace_receipt=trace_receipt)


def evaluate_frozen_predictions_v1(*, predictions:dict, coordinates:tuple, label_values:tuple,
    label_authority_hash:str, protocol, contract, context, dataset_id:str, custody_root:Path) -> dict:
    """Common metric interface only; called after external custody grants labels."""
    from .metric_contract_v1 import (build_file_second_series_authority_v1,build_label_timeline_v1,LabelPointV1,
        adapt_boolean_alarm_timeline_v1,BooleanAlarmInputV1,adapt_d1_alarm_timeline_v1,D1OutcomeInputV1,
        evaluate_common_timeline_v1,compare_common_results_v1)
    series=build_file_second_series_authority_v1(dataset_id=dataset_id,sampling_contract_hash=context.sampling_contract_binding.content_sha256,coordinates=coordinates)
    labels=build_label_timeline_v1(dataset_id=dataset_id,label_authority_sha256=label_authority_hash,file_series=series,
        points=tuple(LabelPointV1(c,y) for c,y in zip(coordinates,label_values,strict=True)))
    results={}
    native_document=json.loads((custody_root/"traces/native-census.private.json").read_bytes())
    trace_receipt=json.loads((custody_root/"traces/full-census.receipt.json").read_bytes())
    replay(native_document);replay(trace_receipt)
    if (trace_receipt!=predictions["trace_receipt"] or native_document["self_hash"]!=trace_receipt["native_census_hash"]
        or native_census_document_v1(predictions["native"])!=native_document):
        raise ValueError("NATIVE_CENSUS_DIFFERS_FROM_FROZEN_FULL_TRACE")
    by_method={r.method_id:r for r in predictions["references"]}
    frozen_masks={}
    for method,ref in by_method.items():
        artifact=replay_dense_prediction_before_label_v1(artifact_root=custody_root,reference=ref,
            expected_policy_hash=ref.receipt.evaluation_policy_hash,expected_metric_contract_hash=contract.contract_hash,
            expected_source_commit=ref.receipt.source_commit)
        if tuple((r.file_id,r.file_content_sha256,r.row_index) for r in artifact.records)!=tuple(
            (c.file_id,c.feature_file_sha256,c.row_index) for c in coordinates):
            raise ValueError("METRIC_COORDINATES_DIFFER_FROM_FROZEN_PREDICTIONS")
        frozen_masks[method]=tuple(r.alarm for r in artifact.records)
        if frozen_masks[method]!=predictions["masks"][method]:
            raise ValueError("IN_MEMORY_PREDICTION_DIFFERS_FROM_FROZEN_BYTES")
    d1=predictions["d1"]
    replayed_d1=replay_prediction_before_label_v1(artifact_root=custody_root,
        prediction_relative_path="predictions/d1.native.json",receipt_relative_path="predictions/d1.native.freeze.json",
        expected_receipt=predictions["d1_receipt"],expected_authority_hash=d1.authority_hash,
        expected_runtime_authorization_hash=d1.runtime_authorization_hash,expected_execution_context_hash=d1.execution_context_hash,
        expected_source_commit=d1.source_commit,expected_portfolio_hash=d1.portfolio_hash,expected_file_contract_hash=d1.file_contract_hash)
    if replayed_d1!=d1 or tuple(r.alarm for r in replayed_d1.records)!=frozen_masks[RULE]:
        raise ValueError("NATIVE_AND_DENSE_RULE_PREDICTION_MISMATCH")
    native=[]
    for window,trace,decision in predictions["native"]:
        if decision>=len(coordinates):continue
        c=coordinates[decision]
        native.append(D1OutcomeInputV1(file_id=c.file_id,feature_file_sha256=c.feature_file_sha256,
            event_row_index=window.event_index,target_response_start_index=window.target_response_start_index,
            response_window_seconds=decision-window.target_response_start_index+1,
            selected_horizon_seconds=window.target_response_start_index-window.event_index,decision_row_index=decision,
            decision_timestamp_second=c.timestamp_second,trace=trace))
    for method in EXP04_METHOD_IDS:
        ref=by_method[method]
        if method==RULE:
            timeline=adapt_d1_alarm_timeline_v1(prediction_artifact=replayed_d1,freeze_receipt=predictions["d1_receipt"],
                contract=contract,protocol=protocol,file_series=series,outcomes=tuple(native))
        else:
            receipt_hash=sha256((custody_root/ref.receipt_relative_path).read_bytes()).hexdigest()
            timeline=adapt_boolean_alarm_timeline_v1(method_id=method,config_id=method+"-CONFIG",
                source_prediction_sha256=ref.receipt.prediction_bytes_sha256,prediction_freeze_receipt_sha256=receipt_hash,
                contract=contract,protocol=protocol,file_series=series,
                records=tuple(BooleanAlarmInputV1(c,a) for c,a in zip(coordinates,frozen_masks[method],strict=True)))
        result=evaluate_common_timeline_v1(contract=contract,protocol=protocol,file_series=series,prediction=timeline,labels=labels)
        results[method]=result
        write_json_v1(custody_root/f"metrics/{method}.private.json",result.to_dict())
    comparisons=[]
    for base,candidate in ((PCA,RULE),(IF,RULE),(PCA,PCA_FUSION),(IF,IF_FUSION)):
        comparison=compare_common_results_v1(contract=contract,protocol=protocol,baseline=results[base],candidate=results[candidate])
        comparisons.append(comparison.to_dict())
    public_rows=[]
    for method,result in results.items():
        public_rows.append({"method_id":method,"recall":result.recall.to_dict(),"far_per_hour":result.far_per_hour.to_dict(),
            "normal_false_episodes":result.normal_false_episodes,"normal_exposure_seconds":result.normal_exposure_seconds,
            "alarm_seconds":result.alarm_seconds,"alarm_episode_count":len(result.alarm_episodes),
            "native_state_counts":dict(result.native_state_counts),"result_hash":result.self_hash})
    return seal({"schema":"exp04_development_results_v1","status":"DEVELOPMENT_ONLY","rows":public_rows,"comparisons":comparisons,
        "label_authority_hash":label_authority_hash,"label_timeline_hash":labels.self_hash,"metric_contract_hash":contract.contract_hash,
        "prediction_bundle_receipt_hash":predictions["bundle_receipt"].self_hash,
        "event_unit_interpretation":"CONTIGUOUS_ATTACK_EVENT_UNITS_INDEPENDENCE_NOT_ESTABLISHED",
        "heldout_generalization":"UNCONFIRMED","post_result_tuning":False})
