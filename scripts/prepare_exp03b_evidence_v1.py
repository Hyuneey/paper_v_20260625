"""One split per process. Normal evidence only; no provider or final Rule inputs."""
from dataclasses import asdict
from hashlib import sha256
import argparse
import json
from pathlib import Path
import statistics
import subprocess
from paperworks.validation_v2.exp03b_contract_v1 import require,digest,t0,proposal_document,HORIZONS
from paperworks.validation_v2.exp03b_custody_v1 import publish,seal,replay,load_normal,load_checkpoint
from paperworks.validation_v2.exp03b_evidence_v1 import build_split_evidence
from paperworks.validation_v2.exp03b_firewall_v1 import SplitPurePredictiveEvidenceV1,project,render
from paperworks.validation_v2.exp01_scientific_v1 import SOURCE_VARIABLES,TARGET_VARIABLES
from paperworks.v6.task039e3_r2r_d0_detector_design_v1 import P1_FEATURE_ORDER

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/"research_control_center/validation_v2/exp03b"
PRIVATE=ROOT/"artifacts/validation_v2/exp03b/private"
BINDING=PUBLIC/"EXP03B_SCIENTIFIC_BINDINGS_V1.json"
DEPENDENCIES=("src/paperworks/validation_v2/numeric_policy_v1.py","src/paperworks/validation_v2/exp02_bindings_v2a.py","src/paperworks/validation_v2/runtime_v1.py","src/paperworks/v6/continuous_step_protocol_v1.py","src/paperworks/validation_v2/exp01c_backend_v1.py","src/paperworks/validation_v2/gdn_corr_v1.py","src/paperworks/validation_v2/gdn_corr_contract_v1.py","src/paperworks/candidates/statistical_candidate_discovery_v1.py","src/paperworks/validation_v2/hai_feature_adapter_v1.py")


def hashes():
    paths=list((ROOT/"src/paperworks/validation_v2").glob("exp03b_*_v1.py"))+[Path(__file__).resolve()]+[ROOT/p for p in DEPENDENCIES]
    return {p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def cohort():
    doc=json.loads((ROOT/"research_control_center/validation_v2/core_v2a/authorities/VALIDATION_V2_META_STAT_CANDIDATE_UNION_AUTHORITY_V1.json").read_text())
    require(doc["authority_hash"]==digest({k:v for k,v in doc.items() if k!="authority_hash"}),"CANDIDATE_HASH")
    pairs=tuple(sorted((r["source"],r["target"]) for r in doc["candidates"]))
    require(pairs and len(set(pairs))==len(pairs),"COHORT_INVALID")
    return pairs,doc["authority_hash"]


def freeze():
    pairs,union=cohort();head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    specs={
        "SCI-01":{"windows":[5,5,5,3],"stability":.8,"refractory":10,"isolation":2,"horizons":HORIZONS,"minimum_amplitudes":20,"train1":[5,.6,2.],"train2":[5,.6,1.],"competition":"STRICTLY_GREATER","horizon_preference":"CONSISTENCY_EFFECT_SUPPORT_SMALLER_HORIZON","completeness":"ALL_SUPPORTED_SOURCE_DIRECTIONS_WITH_ADMISSIBLE_OPTION"},
        "SCI-02":{"options":37,"aliases":"NUM-000..NUM-036","common":"NUM-000","minimum_opportunities":5,"zero_coverage_loss":True,"order":["FALSE_SECONDS","FALSE_EPISODES","ABSTAIN","COMPLEXITY","COMMON","ALIAS_ORDER_RESIDUAL_TIE"],"fit_variability":False,"pooling":"MAX_ONLY_AFTER_TRAIN2_ACCEPTED"},
        "SCI-03":{"order":"AFTER_TRAIN3_ONLY_NO_FEEDBACK","candidate_and_common_minimum_opportunities":5,"coverage_loss":0,"burden":"LEX_SECONDS_EPISODES_ABSTAIN_COMPLEXITY_LE_COMMON","portfolio":"UNION_FILE_ROW_FAIL_THEN_EPISODES_EXPOSURE_ONCE"},
        "SCI-04":{"T0_runs":1,"stochastic_repeats":3,"portfolio_repeat":1,"majority":"EXACT_SEMANTIC_SET_TWO_VALID_VOTES","failure":"NO_VOTE_NO_DECISION_STRICT_FN_OR_FP","empty_cohort":"BLOCKED","degenerate_reference":"BLOCKED_FOR_DISPOSITION"},
        "GDN":{"checkpoints":"EXP01C_TRAIN1_ONLY_TRAIN2_ONLY","seeds":[11,23,37],"evaluation":"EXACT_PRECOMMITTED_PURGED_VALIDATION_INDICES","attention":"SHARED_ENCODER_NOT_HEAD_SPECIFIC","mask":"FIXED_SINGLE_EDGE_REMOVE_NO_REFILL","aggregation":"MEDIAN_ACROSS_THREE_SEEDS_AVAILABLE_GRAPH_EFFECTS_ONLY","retraining":False},
        "STAT":{"formula":"EXISTING_FILE_LOCAL_LAGGED_FIRST_DIFFERENCE_PEARSON","evidence":"MAX_ABSOLUTE_CORRELATION_OVER_FROZEN_HORIZONS","no_rank":True,"no_pool":True},
        "privacy":{"provider":False,"credentials":False,"tests":False,"attack_data":False,"normal_splits":["train1","train2","train4"],"train3":"REFERENCE_REPLAY_ONLY"}}
    document=seal({"schema":"exp03b_scientific_bindings_v1","source_commit":head,"implementation_hashes":hashes(),"specification":specs,"configuration_hash":digest(specs),"candidate_authority_hash":union,"candidate_count":len(pairs),"data_io_authorized":True,"provider_authorized":False,"test1_allowed":False,"test2_allowed":False,"labels_allowed":False})
    publish(BINDING,document)
    public_cohort=seal({"schema":"exp03b_pair_only_cohort_v1","upstream_union_hash":union,"pairs":[{"candidate_id":"EXP03B-CAND-"+digest({"source":s,"target":t})[:20],"source":s,"target":t} for s,t in pairs],"count":len(pairs),"contains_arm_or_confirmation":False})
    publish(PUBLIC/"EXP03B_COHORT_AUTHORITY_V1.json",public_cohort)
    print(json.dumps({"phase":"FREEZE","status":"PASS","N":len(pairs),"binding_hash":document["self_hash"]}))


def prepare(split):
    binding=json.loads(BINDING.read_text());replay(binding)
    require(binding["implementation_hashes"]==hashes(),"BINDING_IMPLEMENTATION_CHANGED")
    pairs,union=cohort();require(union==binding["candidate_authority_hash"],"CANDIDATE_CHANGED")
    require(subprocess.run(["git","check-ignore","--quiet",str(PRIVATE.relative_to(ROOT))],cwd=ROOT).returncode==0,"PRIVATE_NOT_IGNORED")
    matrix,receipt,access=load_normal(ROOT,split,binding["source_commit"])
    publish(PRIVATE/split/"input_receipt.json",seal({"receipt":receipt,"access":access,"binding_hash":binding["self_hash"]}))
    print(json.dumps({"phase":"NORMAL_INPUT","split":split,"status":"PASS"}),flush=True)
    if split=="train4":
        publish(PUBLIC/"EXP03B_TRAIN4_PREPARATION_RECEIPT_V1.json",seal({"split":"train4","input_receipt_hash":digest(receipt),"status":"IDENTITY_READY_GUARD_NOT_YET_EXECUTED","provider_feedback_allowed":False,"binding_hash":binding["self_hash"]}))
        return
    evidence,roles=build_split_evidence(split=split,matrix=matrix,feature_order=tuple(P1_FEATURE_ORDER),pairs=pairs,all_sources=SOURCE_VARIABLES,input_hash=digest(receipt),progress=lambda alias:print(json.dumps({"phase":"NUMERIC_CENSUS","split":split,"completed_alias":alias,"total":37}),flush=True))
    for e in evidence:publish(PRIVATE/split/"structural"/(e.candidate_id+".json"),asdict(e))
    publish(PRIVATE/split/"numeric_roles.json",{"split":split,"roles":[{"pair":p,"source_direction":sd,"alias":a,"roles":v} for (p,sd,a),v in sorted(roles.items())]})
    del roles
    from paperworks.validation_v2.exp03b_gdn_v1 import infer
    gdn=[];checkpoint_receipts=[]
    for seed in (11,23,37):
        checkpoint,cr=load_checkpoint(ROOT,split,seed)
        result=infer(split=split,checkpoint=checkpoint,matrix=matrix,feature_order=tuple(P1_FEATURE_ORDER),pairs=pairs,progress=lambda n,total:print(json.dumps({"phase":"GDN_FIXED_INFERENCE","split":split,"seed":seed,"completed_windows":n,"total_windows":total}),flush=True))
        publish(PRIVATE/split/f"gdn_seed_{seed}.json",seal(result));gdn.append(result);checkpoint_receipts.append(cr)
        del checkpoint
    import numpy as np
    from paperworks.candidates.statistical_candidate_discovery_v1 import vectorized_file_lagged_correlations_v1
    positions={name:i for i,name in enumerate(P1_FEATURE_ORDER)}
    stat=vectorized_file_lagged_correlations_v1(source_values=matrix[:,[positions[s] for s in SOURCE_VARIABLES]],target_values=matrix[:,[positions[t] for t in TARGET_VARIABLES]])
    records=[]
    for e in evidence:
        i=SOURCE_VARIABLES.index(e.source);j=TARGET_VARIABLES.index(e.target)
        vals=[abs(float(v[i,j])) for v in stat.values() if np.isfinite(v[i,j])]
        require(bool(vals),"STAT_SPLIT_EVIDENCE_UNAVAILABLE")
        rows=[]
        for h in HORIZONS:
            matching=[next(r for r in run["rows"] if r["source"]==e.source and r["target"]==e.target and r["horizon"]==h) for run in gdn]
            effects=[r["edge_delta"] for r in matching if r["edge_delta"] is not None]
            rows.append((h,statistics.median(r["embedding"] for r in matching),statistics.median(r["attention"] for r in matching),statistics.median(effects) if effects else None))
        predictive=SplitPurePredictiveEvidenceV1(split,e.candidate_id,digest(checkpoint_receipts),max(vals),tuple(rows))
        publish(PRIVATE/split/"predictive"/(e.candidate_id+".json"),asdict(predictive))
        if split=="train1":
            pack=project(e,predictive)
            content_hash=publish(PRIVATE/split/"provider"/(e.candidate_id+".json"),render(pack))
            publish(PRIVATE/split/"t0"/(e.candidate_id+".json"),proposal_document(t0(e)))
        else:content_hash=digest(asdict(e))
        records.append({"candidate_id":e.candidate_id,"content_hash":content_hash})
    public=seal({"schema":"exp03b_split_pure_evidence_receipt_v1","split":split,"binding_hash":binding["self_hash"],"candidate_count":len(records),"records":records,"checkpoint_receipts":checkpoint_receipts,"input_receipt_hash":digest(receipt),"provider_calls":0,"test1_accesses":0,"test2_accesses":0,"label_accesses":0,"private_exposures":0})
    publish(PUBLIC/f"EXP03B_{split.upper()}_EVIDENCE_RECEIPT_V1.json",public)
    print(json.dumps({"phase":"SPLIT_COMPLETE","split":split,"N":len(records),"status":"PASS"}),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("phase",choices=("freeze","train1","train2","train4"));args=parser.parse_args()
    try:freeze() if args.phase=="freeze" else prepare(args.phase)
    except Exception as error:
        print(json.dumps({"status":"FAIL_CLOSED","phase":args.phase,"error_type":type(error).__name__,"code":str(error) if type(error) is ValueError and str(error).replace("_","").isalnum() else "REDACTED_ERROR"}),flush=True)
        raise SystemExit(2)
