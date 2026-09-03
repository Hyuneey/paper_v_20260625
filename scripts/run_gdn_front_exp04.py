"""Frozen V2 five-method runner. No evaluation I/O before exact Commit B gate."""
from __future__ import annotations
import argparse
from datetime import datetime
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.parse

from paperworks.validation_v2.front_authority_v1 import load_v2a_runtime_v1
from paperworks.validation_v2.front_execution_v1 import fit_detectors_v1,freeze_predictions_v1,evaluate_frozen_predictions_v1,write_json_v1
from paperworks.validation_v2.front_runtime_v1 import iter_rule_windows_v1
from paperworks.validation_v2.front_label_adapter_v1 import consume_exact_labels_v1
from paperworks.validation_v2.gdn_sidecar_v1 import seal,replay
from paperworks.validation_v2.private_vault_v1 import file_identity_v1,validate_private_path_v1
from paperworks.validation_v2.isolation_forest_v1 import build_detector_environment_receipt_v1,NormalMatrixInputV1
from paperworks.validation_v2.protocol_v1 import build_validation_protocol_v1,ProtocolExecutionGuardV1,ProtocolOperationV1,build_policy_freeze_receipt_v1
from paperworks.validation_v2.metric_contract_v1 import build_common_metric_contract_v1,PredictionCoordinateV1
from paperworks.validation_v2.hai_feature_adapter_v1 import resolve_hai_feature_root_capability_v1,load_authorized_hai_feature_frame_v1,HAIFeatureAccessLedgerV1
from paperworks.validation_v2.exp04_protocol_v1 import EXP04_METHOD_IDS
from paperworks.validation_v2.exp05_runner_v1 import authorize_exp05_execution_v1
from paperworks.validation_v2.evaluation_custody_v1 import authorize_evaluation_label_access_v1,verify_evaluation_inputs_unchanged_v1,destroy_evaluation_label_capability_v1
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER

V2=Path("research_control_center/validation_v2")
PUBLIC=V2/"gdn_front_exp04_001"
LOCAL=Path("artifacts/validation_v2/gdn_front_exp04_001/private/LOCAL_CONTEXT.json")
FREEZE=PUBLIC/"contracts/EXP04_EXECUTION_FREEZE_V1.json"
EXPERIMENT="V2-GDN-FRONT-EXP04-001"


def read(path):return json.loads(path.read_text(encoding="utf-8"))
def git(*args):return subprocess.check_output(["git",*args],text=True,stderr=subprocess.DEVNULL).strip()
def emit(stage,**values):print(json.dumps({"stage":stage,**values}),flush=True)


def historical_transport(root):
    path=root/"scripts/local/materialize_hai_inner_payload_v1.py"
    spec=importlib.util.spec_from_file_location("front_frozen_hai_transport",path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    module._load_fallback_authority(root) # Tracked metadata only, no payload calls.
    return module


def source_hashes(root):
    paths=git("ls-files","src","configs","schemas","scripts/local/materialize_hai_inner_payload_v1.py",
              "scripts/run_gdn_front_exp04.py").splitlines()
    return {path:sha256((root/path).read_bytes()).hexdigest() for path in paths}


def protected_inputs(root):
    paths=git("ls-files",str(V2/"core_v2a/authorities"),str(V2/"core_v2a/contracts"),
        str(V2/"preregistration"),str(V2/"gdn_rule_evidence"),str(V2/"STAGE2_COMMIT_A_MANIFEST.json"),
        str(V2/"reports/V2_PROTOCOL_001_EVIDENCE.json"),
        "docs/task_reports/TASK-039AR_KAGGLE_METADATA_FREEZE.json",
        "docs/task_reports/TASK-039AR_BYTE_EQUIVALENCE_REPORT.json").splitlines()
    return {path:sha256((root/path).read_bytes()).hexdigest() for path in paths}


def assert_frozen_inputs(root,document,freeze_bytes_hash):
    if (source_hashes(root)!=document["source_hashes"] or protected_inputs(root)!=document["protected_inputs"]
        or sha256((root/FREEZE).read_bytes()).hexdigest()!=freeze_bytes_hash):
        raise ValueError("FROZEN_EXECUTION_INPUT_MUTATION")


def protocols(root):
    evidence=read(root/V2/"reports/V2_PROTOCOL_001_EVIDENCE.json")
    # Current protocol receipt contains its original scientific source identity.
    def find(document,key):
        if isinstance(document,dict):
            if key in document:return document[key]
            for value in document.values():
                result=find(value,key)
                if result is not None:return result
        return None
    protocol=build_validation_protocol_v1(source_commit=find(evidence,"protocol_source_commit"))
    if protocol.protocol_hash!=find(evidence,"protocol_hash"):raise ValueError("FROZEN_PROTOCOL_IDENTITY_MISMATCH")
    return protocol,build_common_metric_contract_v1(protocol)


def freeze(root):
    if git("status","--porcelain"):raise ValueError("COMMIT_A_CLEAN_REQUIRED")
    bundle,context=load_v2a_runtime_v1(root)
    protocol,metric=protocols(root)
    environment=build_detector_environment_receipt_v1()
    sidecar=read(root/V2/"gdn_rule_evidence/GDN_LEARNED_GRAPH_EVIDENCE_SIDECAR_V1.json");replay(sidecar)
    transport=historical_transport(root)
    prereg={name:read(root/V2/f"preregistration/{name}_PREREGISTRATION_V2.json") for name in ("EXP04","EXP05","D0_PCA_SPE","STRONGER_DETECTOR")}
    for doc in prereg.values():replay(doc,"preregistration_hash")
    stage2=read(root/V2/"STAGE2_COMMIT_A_MANIFEST.json");replay(stage2,"manifest_hash")
    manifest=seal({"schema":"front_exp04_execution_freeze_v1","task_id":EXPERIMENT,"code_commit_a":git("rev-parse","HEAD"),
        "execution_commit_policy":"EXACT_COMMIT_A_PARENT_FREEZE_FILE_ONLY_COMMIT_B","source_hashes":source_hashes(root),
        "protected_inputs":protected_inputs(root),
        "protocol_hash":protocol.protocol_hash,"protocol_source_commit":protocol.source_commit,"metric_contract_hash":metric.contract_hash,
        "portfolio_hash":bundle.authority.authority_hash,"runtime_authorization_hash":bundle.receipt.authorization_hash,
        "sidecar_hash":sidecar["self_hash"],"environment":environment.to_document(),"preregistrations":prereg,
        "stage2_commit_a_manifest_hash":stage2["manifest_hash"],
        "selected_numeric_authority_file_sha256":sha256((root/V2/"core_v2a/authorities/EXP02_SELECTED_POLICY_AUTHORITY_V2A.json").read_bytes()).hexdigest(),
        "method_ids":list(EXP04_METHOD_IDS),"dataset":"HAI_23.05","evaluation_role":"DEVELOPMENT_ONLY",
        "feature_spec":transport.FEATURE_SPEC.__dict__,"label_spec":transport.LABEL_SPEC.__dict__,
        "normal_roles":{"train1":"DETECTOR_FIT","train2":"DETECTOR_FIT","train3":"THRESHOLD_CALIBRATION"},
        "tail_policy":"PRESERVE_FULL_ABSTAIN_TRACE_NO_NONEXISTENT_DENSE_ROW",
        "source_event_policy":"EXACT_EXP02_CANDIDATE_SPECIFIC_BOTH_DIRECTION_OTHER_SOURCE_UNION",
        "no_post_feature_source_revision":True,"label_gate":"ALL_FIVE_EXACT_COORDINATE_DURABLE_FREEZE_ONE_SHOT_CAPABILITY",
        "label_semantic_parse_count":1,"provider_allowed":False,"test2_allowed":False,"heldout_allowed":False})
    write_json_v1(root/FREEZE,manifest)
    emit("EXECUTION_CONTRACT_WRITTEN_COMMIT_B_REQUIRED",contract_hash=manifest["self_hash"])


def execute(root):
    freeze_doc=read(root/FREEZE);replay(freeze_doc)
    freeze_bytes_hash=sha256((root/FREEZE).read_bytes()).hexdigest()
    head=git("rev-parse","HEAD")
    branch=git("branch","--show-current")
    if (git("status","--porcelain") or git("rev-parse","HEAD^")!=freeze_doc["code_commit_a"]
        or git("diff","--name-only","HEAD^","HEAD").splitlines()!=[FREEZE.as_posix()]):
        raise ValueError("EXACT_CLEAN_COMMIT_B_REQUIRED")
    if git("rev-parse","origin/"+branch)!=head:raise ValueError("COMMIT_B_ORIGIN_PARITY_REQUIRED")
    assert_frozen_inputs(root,freeze_doc,freeze_bytes_hash)
    local=read(root/LOCAL)
    repository=Path(git("rev-parse","--git-common-dir")).resolve().parent
    approved_vault=repository.parent/"paper_v_20260625_private_vault"
    if Path(local["private_vault"])!=approved_vault:raise ValueError("PRIVATE_VAULT_ROOT_NOT_APPROVED")
    custody=validate_private_path_v1(approved_vault/"gdn-front-exp04-001/scientific-run",allowed_root=approved_vault)
    if custody.exists():raise ValueError("SCIENTIFIC_NAMESPACE_ALREADY_EXISTS_NO_RERUN")
    custody.mkdir(parents=True)
    write_json_v1(custody/"V2_SCIENTIFIC_RUN_MANIFEST.json",seal({"execution_commit":head,"freeze_contract_hash":freeze_doc["self_hash"],
        "environment":build_detector_environment_receipt_v1().to_document(),"scope":"DEVELOPMENT_ONLY","state":"PRE_FEATURE"}))
    if build_detector_environment_receipt_v1().to_document()!=freeze_doc["environment"]:raise ValueError("ENVIRONMENT_MISMATCH")
    bundle,context=load_v2a_runtime_v1(root)
    protocol,metric=protocols(root)
    if (bundle.authority.authority_hash!=freeze_doc["portfolio_hash"] or metric.contract_hash!=freeze_doc["metric_contract_hash"]
        or bundle.receipt.authorization_hash!=freeze_doc["runtime_authorization_hash"]):raise ValueError("EXECUTION_AUTHORITY_MISMATCH")
    sidecar=read(root/V2/"gdn_rule_evidence/GDN_LEARNED_GRAPH_EVIDENCE_SIDECAR_V1.json");replay(sidecar)
    if sidecar["self_hash"]!=freeze_doc["sidecar_hash"]:raise ValueError("SIDECAR_CHANGED")
    guard=ProtocolExecutionGuardV1(protocol)
    ledger=HAIFeatureAccessLedgerV1(experiment_id=EXPERIMENT)
    os.environ["HAI_DATA_ROOT"]=local["normal_materialization_root"]
    capability=resolve_hai_feature_root_capability_v1(root)
    normal=[];normal_receipts=[]
    for split,operation in (("train1",ProtocolOperationV1.DETECTOR_FIT),("train2",ProtocolOperationV1.DETECTOR_FIT),("train3",ProtocolOperationV1.THRESHOLD_CALIBRATION)):
        emit("NORMAL_FEATURE_READ",split=split)
        frame=load_authorized_hai_feature_frame_v1(capability=capability,split_id=split,operation=operation,protocol_guard=guard,ledger=ledger)
        receipt=frame.receipt.to_dict();normal_receipts.append(receipt)
        normal.append(NormalMatrixInputV1("hai-"+split+".csv",receipt["file_sha256"],receipt["split_role"],tuple(P1_FEATURE_ORDER),frame.numeric_matrix()))
    write_json_v1(custody/"normal-input-receipts.json",seal({"receipts":normal_receipts}))
    emit("NORMAL_DETECTOR_FIT")
    models=fit_detectors_v1(train1=normal[0],train2=normal[1],train3=normal[2],environment=build_detector_environment_receipt_v1(),
        source_commit=head,pca_preregistration_hash=freeze_doc["preregistrations"]["D0_PCA_SPE"]["preregistration_hash"],
        if_preregistration_hash=freeze_doc["preregistrations"]["STRONGER_DETECTOR"]["preregistration_hash"],custody_root=custody)
    del normal,frame,capability
    selected=read(root/V2/"core_v2a/authorities/EXP02_SELECTED_POLICY_AUTHORITY_V2A.json")
    policy=build_policy_freeze_receipt_v1(protocol=protocol,candidate_set_hash=selected["cohort_hash"],
        selection_objective="FROZEN_EXP02_NORMAL_ONLY_ZERO_COVERAGE_LOSS",tie_break_rule="FROZEN_EXP02_LEXICOGRAPHIC_COMMON_TOTAL_TIE",
        selected_config_hash=selected["selected_candidate_hash"],authority_hash=bundle.authority.authority_hash,
        method_policy_hashes=(freeze_doc["self_hash"],freeze_doc["preregistrations"]["EXP04"]["fusion_policy_hash"]),metric_contract_hash=metric.contract_hash)
    guard.freeze_policies(policy)
    write_json_v1(custody/"POLICY_FREEZE_RECEIPT.json",policy.to_dict())
    transport=historical_transport(root)
    data_root=transport._private_cache_root(root)
    transport.require_cache_outside_repository(data_root,root)
    validate_private_path_v1(data_root,allowed_root=data_root)
    data_root.mkdir(parents=True,exist_ok=True)
    def payload_path(spec):
        if spec not in (transport.FEATURE_SPEC,transport.LABEL_SPEC):raise ValueError("UNAUTHORIZED_PAYLOAD")
        return validate_private_path_v1(data_root/spec.relative_path,allowed_root=data_root)
    def acquire(spec):
        path=payload_path(spec)
        if not path.is_file():
            for suffix in (".download",".part"):
                auxiliary=validate_private_path_v1(path.with_suffix(path.suffix+suffix),allowed_root=data_root)
                if auxiliary.exists():raise ValueError("STALE_ACQUISITION_TEMPORARY_REJECTED")
            metadata,hosts=transport._load_fallback_authority(root)
            template=metadata["selective_download_endpoint_template"]
            url=template.format(owner=transport.KAGGLE_OWNER,slug=transport.KAGGLE_SLUG,
                file_name=urllib.parse.quote(spec.relative_path,safe=""),version=transport.KAGGLE_VERSION)
            transport._download_selective_payload(url=url,staging_root=data_root,spec=spec,allowed_hosts=hosts)
        return path
    # Marker is durable BEFORE any feature stat/hash/download; failed access is not silently retried.
    assert_frozen_inputs(root,freeze_doc,freeze_bytes_hash)
    write_json_v1(custody/"TEST1_FEATURE_ACCESS_STARTED.json",seal({"execution_commit":head,"freeze_hash":freeze_doc["self_hash"],"code_revision_after_this_point":"PROHIBITED"}))
    feature_path=acquire(transport.FEATURE_SPEC)
    os.environ["HAI_DATA_ROOT"]=str(data_root)
    feature_cap=resolve_hai_feature_root_capability_v1(root)
    frame=load_authorized_hai_feature_frame_v1(capability=feature_cap,split_id="test1",operation=ProtocolOperationV1.DEVELOPMENT_PREDICTION,protocol_guard=guard,ledger=ledger)
    observed=frame.receipt.to_dict();timestamps=frame.file_local_timestamps();matrix=frame.numeric_matrix()
    evaluation_input=NormalMatrixInputV1("hai-test1.csv",observed["file_sha256"],"DEVELOPMENT_ONLY",tuple(P1_FEATURE_ORDER),matrix)
    write_json_v1(custody/"TEST1_FEATURE_RECEIPT.json",observed)
    exp05=authorize_exp05_execution_v1(execution_scope="SCIENTIFIC_V2",preregistration_hash=freeze_doc["preregistrations"]["EXP05"]["preregistration_hash"],
        source_commit=bundle.authority.source_commit,bundle=bundle,stage2_commit_a_receipt_hash=freeze_doc["stage2_commit_a_manifest_hash"],
        normal_selection_commit_b_receipt_hash=freeze_doc["selected_numeric_authority_file_sha256"],test1_features_authorized=True)
    emit("FIVE_METHOD_LABEL_BLIND_PREDICTION")
    predictions=freeze_predictions_v1(models=models,evaluation_input=evaluation_input,expected_role="DEVELOPMENT_ONLY",bundle=bundle,context=context,
        repository_root=root,custody_root=custody,windows=iter_rule_windows_v1(bundle=bundle,context=context,root=root,matrix=matrix,feature_order=P1_FEATURE_ORDER,file_id="hai-test1.csv"),
        exp05_authorization=exp05,source_commit=head,evaluation_policy_hash=freeze_doc["self_hash"],metric_contract_hash=metric.contract_hash,
        experiment_id=EXPERIMENT,dataset_id="HAI_23.05_P1_DEVELOPMENT",sidecar=sidecar)
    # Release all generator/model/feature objects before label capability issuance.
    del models,evaluation_input,matrix,frame,feature_cap
    guard.record_development_prediction_frozen()
    assert_frozen_inputs(root,freeze_doc,freeze_bytes_hash)
    label_cap=authorize_evaluation_label_access_v1(artifact_root=custody,exact_method_ids=EXP04_METHOD_IDS,prediction_references=predictions["references"],
        evaluation_policy_hash=freeze_doc["self_hash"],metric_contract_hash=metric.contract_hash,source_commit=head,
        bundle_relative_path="evaluation/bundle.json",bundle_receipt_relative_path="evaluation/bundle.freeze.json",expected_bundle_receipt=predictions["bundle_receipt"])
    guard.authorize_multi_method_label_metrics_v1(label_cap,exact_method_ids=EXP04_METHOD_IDS,evaluation_policy_hash=freeze_doc["self_hash"],
        metric_contract_hash=metric.contract_hash,execution_source_commit=head)
    write_json_v1(custody/"TEST1_LABEL_ACCESS_AUTHORIZATION_V2.json",seal({"bundle_receipt_hash":predictions["bundle_receipt"].self_hash,
        "exact_methods":list(EXP04_METHOD_IDS),"prediction_generators_closed":True,"source_commit":head,"metric_contract_hash":metric.contract_hash,
        "label_identity":transport.LABEL_SPEC.sha256,"scope":"DEVELOPMENT_ONLY"}))
    emit("ALL_FIVE_FROZEN_LABEL_CAPABILITY_AUTHORIZED")
    values=consume_exact_labels_v1(label_cap,reader=lambda:acquire(transport.LABEL_SPEC).read_bytes(),expected_hash=transport.LABEL_SPEC.sha256,
        expected_size=transport.LABEL_SPEC.size_bytes,timestamps=timestamps,exact_method_ids=EXP04_METHOD_IDS,evaluation_policy_hash=freeze_doc["self_hash"],
        metric_contract_hash=metric.contract_hash,source_commit=head)
    guard.record_development_labels_accessed();ledger.mark_labels_accessed()
    coordinates=tuple(PredictionCoordinateV1("hai-test1.csv",observed["file_sha256"],i,int((datetime.fromisoformat(t)-datetime(1970,1,1)).total_seconds())) for i,t in enumerate(timestamps))
    results=evaluate_frozen_predictions_v1(predictions=predictions,coordinates=coordinates,label_values=values,label_authority_hash=transport.LABEL_SPEC.sha256,
        protocol=protocol,contract=metric,context=context,dataset_id="HAI_23.05_P1_DEVELOPMENT",custody_root=custody)
    verified=verify_evaluation_inputs_unchanged_v1(label_cap);destroy_evaluation_label_capability_v1(label_cap);guard.complete()
    assert_frozen_inputs(root,freeze_doc,freeze_bytes_hash)
    load_v2a_runtime_v1(root)
    write_json_v1(custody/"EXP04_RESULTS_PUBLIC_SAFE.json",results)
    write_json_v1(custody/"POST_LABEL_INTEGRITY_RECEIPT.json",seal({"verified_bound_hashes":list(verified),"source_unchanged":True,
        "capability_destroyed":True,"data_access":ledger.public_document(),"provider_calls":0,"gdn_training":0,"result_driven_redesign":False}))
    write_json_v1(root/PUBLIC/"results/EXP04_RESULTS_V1.json",results)
    full=predictions["trace_receipt"]
    public_trace={k:v for k,v in full.items() if k not in ("self_hash","full_unit_batch_receipts")}
    public_trace["private_full_census_hash"]=full["self_hash"]
    public_trace["full_unit_batch_hashes"]=[r["self_hash"] for r in full["full_unit_batch_receipts"]]
    write_json_v1(root/PUBLIC/"results/EXP05_FULL_CENSUS_V1.json",seal(public_trace))
    emit("DEVELOPMENT_EXECUTION_COMPLETE_INDEPENDENT_QA_REQUIRED",methods=len(results["rows"]),traces=predictions["trace_receipt"]["unit_count"])


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("mode",choices=("freeze","execute"));args=parser.parse_args()
    try:
        (freeze if args.mode=="freeze" else execute)(Path.cwd())
    except Exception as error:
        # Never expose a private path/value through a traceback.
        code=str(error)
        if not code or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789" for c in code):code=type(error).__name__
        emit("FAIL_CLOSED",error_code=code)
        raise SystemExit(1)
