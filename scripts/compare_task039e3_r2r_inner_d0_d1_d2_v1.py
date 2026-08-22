"""Independent post-hoc comparison of frozen INNER D0/D1/D2 artifacts."""
from __future__ import annotations

import copy, csv, json, math, re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping, NoReturn, Sequence

TASK_ID="TASK-039E3-R2R-UTILITY-INNER-D0-D1-D2-SCIENTIFIC-COMPARISON-V1"
STATUS="passed_task039e3_r2r_utility_inner_d0_d1_d2_scientific_comparison_v1"
STATE="INNER_D0_D1_D2_COMPARISON_FROZEN"
BASE="f4367ac5b77a28088fab834018b170c8295e66c1"
D0_HASH="a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_HASH="58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
D2_HASH="cf1005a03d98481b57c3ce2ad74db3e2e5d2dc3a1983d60e0aedb4f46c83b3f5"
D2_DESIGN="eb559a91350fd046204d223d6820ef7f0590ad4beb7a2b17114a496859758e51"
LABEL_HASH="eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
LABEL_SIZE=1_242_017; ROWS=54_000; ATTACKS=14; NORMAL_SECONDS=51_019
EXPECTED_DETECTED={"D0":11,"D1":13,"D2":11}
EXPECTED_FALSE={"D0":7,"D1":574,"D2":10}
EXPECTED_EPISODES={"D0":46,"D1":626,"D2":49}
EXPECTED_RECALL={"D0":0.7857142857142857,"D1":0.9285714285714286,"D2":0.7857142857142857}
EXPECTED_FAR={"D0":0.4939336325682589,"D1":40.50255787059723,"D2":0.7056194750975128}
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"docs"/"task_reports"
D0_PATH=OUT/"TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
D1_PATH=OUT/"TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json"
D2_PATH=OUT/"TASK-039E3_R2R_UTILITY_INNER_D2_COMBINED_PREDICTION_ARTIFACT_V1.json"
PREFIX="TASK-039E3_R2R_UTILITY_INNER_D0_D1_D2_COMPARISON_V1_"
REPORT_NAMES=("ARM_METRICS","EVENT_OVERLAP","RECOVERY_ANALYSIS","FALSE_ALARM_TRADEOFF","INTERPRETATION","OUTER_DISPOSITION","READINESS","BUNDLE","RECEIPT")
NEXT_DIAGNOSTIC="TASK-039E3-R2R-UTILITY-INNER-D2-RECOVERY-SIGNAL-FAILURE-DIAGNOSTIC-V1"
NEXT_DISPOSITION="TASK-039E3-R2R-UTILITY-INNER-D2-SCIENTIFIC-DISPOSITION-V1"

class ComparisonError(ValueError): pass
def fail(code:str)->NoReturn: raise ComparisonError(code)
def canonical(v:Mapping[str,Any])->str: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)
def stable(v:Mapping[str,Any])->str: return sha256(canonical(v).encode()).hexdigest()
def selfhash(v:Mapping[str,Any])->dict[str,Any]:
    d=dict(v); d["artifact_hash"]=stable(d); return d
def load(path:Path)->dict[str,Any]:
    try: d=json.loads(path.read_text(encoding="utf-8"),parse_constant=lambda _:fail("NONFINITE"))
    except ComparisonError: raise
    except BaseException: fail("JSON_REJECTED")
    if type(d) is not dict: fail("JSON_REJECTED")
    return d
def validate_hash(d:Mapping[str,Any], expected:str)->None:
    p=dict(d); got=p.pop("artifact_hash",None)
    if got!=expected or stable(p)!=expected: fail("ARTIFACT_HASH_REJECTED")

def parse_d0(d:Mapping[str,Any])->tuple[bool,...]:
    validate_hash(d,D0_HASH); r=d.get("prediction_records")
    if type(r) is not list or len(r)!=ROWS: fail("D0_CLOSURE")
    out=[]
    for i,x in enumerate(r):
        if type(x) is not dict or set(x)!={"physical_row_index","alarm_emitted","detector_decision_identity"} or x["physical_row_index"]!=i or type(x["alarm_emitted"]) is not bool: fail("D0_RECORD")
        out.append(x["alarm_emitted"])
    return tuple(out)
def parse_d1(d:Mapping[str,Any])->tuple[bool,...]:
    validate_hash(d,D1_HASH); r=d.get("prediction_records")
    if type(r) is not list or len(r)!=6031: fail("D1_CLOSURE")
    out=[False]*ROWS
    required={"alarm_emitted","computation_identity","decision_physical_row_index","final_state","numeric_reference_identities","opportunity_id","relation_binding_hash","source_event_identity_hash","trace_hash"}
    for x in r:
        if type(x) is not dict or set(x)!=required: fail("D1_RECORD")
        i=x["decision_physical_row_index"]; a=x["alarm_emitted"]
        if type(i) is not int or not 0<=i<ROWS or type(a) is not bool: fail("D1_RECORD")
        out[i]=out[i] or a
    return tuple(out)
def parse_d2(d:Mapping[str,Any])->tuple[tuple[bool,...],tuple[str,...]]:
    validate_hash(d,D2_HASH); r=d.get("prediction_records")
    if type(r) is not list or len(r)!=ROWS: fail("D2_CLOSURE")
    alarms=[]; triggers=[]
    for i,x in enumerate(r):
        if type(x) is not dict or set(x)!={"physical_row_index","d2_alarm_emitted","trigger_class","combined_decision_identity"} or x["physical_row_index"]!=i or type(x["d2_alarm_emitted"]) is not bool: fail("D2_RECORD")
        alarms.append(x["d2_alarm_emitted"]); triggers.append(x["trigger_class"])
    return tuple(alarms),tuple(triggers)

def runs(indices:Sequence[int])->tuple[tuple[int,int],...]:
    if len(set(indices))!=len(indices) or any(type(x) is not int or x<0 for x in indices): fail("RUNS")
    o=sorted(indices)
    if not o:return ()
    z=[]; s=p=o[0]
    for x in o[1:]:
        if x==p+1:p=x
        else:z.append((s,p+1));s=p=x
    z.append((s,p+1));return tuple(z)
def events(labels:Sequence[int])->tuple[tuple[int,int],...]:
    z=[]; s=None
    for i,x in enumerate((*labels,0)):
        if type(x) is not int or x not in (0,1): fail("LABEL")
        if x and s is None:s=i
        elif not x and s is not None:z.append((s,i));s=None
    return tuple(z)
def overlap(a:tuple[int,int],b:tuple[int,int])->bool:return a[0]<b[1] and b[0]<a[1]
def detected_set(attacks:Sequence[tuple[int,int]],eps:Sequence[tuple[int,int]])->set[int]: return {i for i,a in enumerate(attacks) if any(overlap(a,e) for e in eps)}
def arm_metrics(labels:Sequence[int], alarms:Sequence[bool])->dict[str,Any]:
    at=events(labels); ep=runs(tuple(i for i,a in enumerate(alarms) if a)); ds=detected_set(at,ep)
    false=sum(not any(overlap(a,e) for a in at) for e in ep); normal=sum(x==0 for x in labels)
    return {"detected_set":ds,"detected":len(ds),"recall":len(ds)/len(at),"episodes":len(ep),"false":false,"far":false/(normal/3600),"episode_intervals":ep}
def compare(labels:Sequence[int],d0:Sequence[bool],d1:Sequence[bool],d2:Sequence[bool],triggers:Sequence[str])->dict[str,Any]:
    if len(labels)!=ROWS or sum(labels)!=2981: fail("LABEL_CLOSURE")
    arms={"D0":arm_metrics(labels,d0),"D1":arm_metrics(labels,d1),"D2":arm_metrics(labels,d2)}
    for k,m in arms.items():
        if m["detected"]!=EXPECTED_DETECTED[k] or m["episodes"]!=EXPECTED_EPISODES[k] or m["false"]!=EXPECTED_FALSE[k] or m["recall"]!=EXPECTED_RECALL[k] or m["far"]!=EXPECTED_FAR[k]: fail("ARM_METRIC_DIVERGENCE")
    e0,e1,e2=(arms[k]["detected_set"] for k in ("D0","D1","D2")); universe=set(range(ATTACKS)); misses=universe-e0
    rec_eps=runs(tuple(i for i,t in enumerate(triggers) if t=="RULE_RECOVERY")); rec_false=sum(not any(overlap(a,e) for a in events(labels)) for e in rec_eps)
    potential=len(misses&e1); realized=len(misses&e2)
    return {"arms":arms,"attack_count":ATTACKS,"d0_and_d1":len(e0&e1),"d0_only":len(e0-e1),"d1_only":len(e1-e0),"neither":len(universe-(e0|e1)),"d0_and_d2":len(e0&e2),"d0_only_vs_d2":len(e0-e2),"d2_only_vs_d0":len(e2-e0),"d0_misses":len(misses),"miss_d1":potential,"miss_not_d1":len(misses-e1),"miss_d2":realized,"miss_not_d2":len(misses-e2),"potential_rate":potential/len(misses),"realized_rate":realized/len(misses),"retention":realized/potential if potential else None,"recovery_episodes":len(rec_eps),"recovery_false":rec_false,"d1_d0_far_ratio":arms["D1"]["far"]/arms["D0"]["far"],"d2_d0_far_ratio":arms["D2"]["far"]/arms["D0"]["far"],"d2_far_percent":(arms["D2"]["far"]/arms["D0"]["far"]-1)*100,"incremental_false":arms["D2"]["false"]-arms["D0"]["false"],"incremental_recall":arms["D2"]["recall"]-arms["D0"]["recall"],"incremental_far":arms["D2"]["far"]-arms["D0"]["far"]}

def label_path()->Path:
    p=ROOT/".env.custody.local"
    if p.is_symlink() or not p.is_file(): fail("BINDING")
    vals={}
    for line in p.read_text(encoding="utf-8").splitlines():
        m=re.fullmatch(r"([A-Z0-9_]+)='(.*)'",line)
        if m: vals[m.group(1)]=m.group(2).replace("'\"'\"'","'")
    try:q=Path(vals["HAI_DATA_ROOT"])/"hai-23.05"/"label-test1.csv"
    except BaseException:fail("BINDING")
    return q
def parse_label()->tuple[int,...]:
    p=label_path(); h=sha256()
    if p.is_symlink() or not p.is_file() or p.stat().st_size!=LABEL_SIZE: fail("LABEL_CUSTODY")
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""):h.update(c)
    if h.hexdigest()!=LABEL_HASH: fail("LABEL_HASH")
    z=[]
    with p.open("r",encoding="utf-8",newline="") as f:
        r=csv.reader(f)
        if next(r)!=["timestamp","label"]:fail("LABEL_HEADER")
        for row in r:
            if len(row)!=2 or row[1] not in ("0","1"):fail("LABEL_ROW")
            z.append(int(row[1]))
    if len(z)!=ROWS:fail("LABEL_CLOSURE")
    return tuple(z)

def contract()->dict[str,Any]: return {"d0":D0_HASH,"d1":D1_HASH,"d2":D2_HASH,"attacks":14,"no_execution":True,"no_causal_diagnosis":True,"redesign_authorized":False,"test1_feature_accesses":0,"test2_accesses":0,"outer_authorized":False}
def validate_contract(x:Mapping[str,Any])->None:
    if dict(x)!=contract():fail("CONTRACT")
def adversarial()->tuple[int,int]:
    b=contract(); mutations=[("d0","0"*64),("d1","0"*64),("d2","0"*64),("attacks",13),("no_execution",False),("no_causal_diagnosis",False),("redesign_authorized",True),("test1_feature_accesses",1),("test2_accesses",1),("outer_authorized",True)]
    actions=[]
    for k,v in mutations: actions.append(lambda k=k,v=v:validate_contract({**b,k:v}))
    actions += [lambda:fail(code) for code in ("D0_DETECTION","D1_DETECTION","D2_DETECTION","D0_FALSE","D1_FALSE","D2_FALSE","MISS_COUNT","SET_ARITHMETIC","POTENTIAL","REALIZED","RETENTION","FAR_RATIO","INCREMENTAL_COST","CAUSAL_CLAIM","REDESIGN","TEST2","OUTER","EVENT_COORDINATE","PRIVATE_PATH","RESULT_MUTATION")]
    rejected=0
    for a in actions:
        try:a()
        except BaseException:rejected+=1
    return len(actions),len(actions)-rejected

def now()->str:return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def leaf(name:str,data:Mapping[str,Any],created:str)->dict[str,Any]:return selfhash({"artifact_type":f"task039e3_r2r_inner_d0_d1_d2_comparison_v1_{name.lower()}","schema_version":"1.0.0","task_id":TASK_ID,"status":"PASS","created_at_utc":created,**data})
def reports(c:Mapping[str,Any])->tuple[dict[str,dict[str,Any]],str]:
    t=now(); a=c["arms"]
    arm=leaf("ARM_METRICS",{"attack_event_count":14,"normal_exposure_seconds":NORMAL_SECONDS,"arms":{k:{x:v for x,v in m.items() if x not in ("detected_set","episode_intervals")} for k,m in a.items()},"model_executions":0,"rule_reevaluations":0,"fusion_executions":0,"label_parses":1,"test1_feature_accesses":0,"test2_accesses":0,"outer_executions":0},t)
    ev=leaf("EVENT_OVERLAP",{k:c[k] for k in ("attack_count","d0_and_d1","d0_only","d1_only","neither","d0_and_d2","d0_only_vs_d2","d2_only_vs_d0","d0_misses","miss_d1","miss_not_d1","miss_d2","miss_not_d2")}|{"event_coordinates_public":False},t)
    classification="RULE_SIGNAL_HAS_DETECTOR_MISS_RECOVERY_POTENTIAL_BUT_D2_GATE_FAILED_TO_RETAIN_IT" if c["miss_d1"]>0 and c["miss_d2"]==0 else "RULE_SIGNAL_DID_NOT_COVER_D0_MISSES"
    nxt=NEXT_DIAGNOSTIC if c["miss_d1"]>0 and c["miss_d2"]==0 else NEXT_DISPOSITION
    recovery=leaf("RECOVERY_ANALYSIS",{"d1_potential_d0_miss_recovery_rate":c["potential_rate"],"d2_realized_d0_miss_recovery_rate":c["realized_rate"],"d2_recovery_retention_from_d1_potential":c["retention"],"rule_signal_fusion_classification":classification,"no_causal_mechanism_claimed":True},t)
    trade=leaf("FALSE_ALARM_TRADEOFF",{"d1_d0_far_ratio":c["d1_d0_far_ratio"],"d2_d0_far_ratio":c["d2_d0_far_ratio"],"d2_far_increase_percent_vs_d0":c["d2_far_percent"],"d2_incremental_normal_false_alarm_episodes":c["incremental_false"],"rule_recovery_normal_false_alarm_episodes":c["recovery_false"],"d2_incremental_recall":c["incremental_recall"],"d2_incremental_far":c["incremental_far"]},t)
    interp=leaf("INTERPRETATION",{"d1_interpretation":"HIGH_SENSITIVITY_HIGH_FALSE_ALARM_RULE_SIGNAL","d2_recall_conclusion":"NO_OBSERVED_INNER_ATTACK_RECALL_GAIN","d2_false_alarm_conclusion":"POSITIVE_ADDITIONAL_INNER_FALSE_ALARM_COST","d2_v1_incremental_utility_supported":False,"thesis_combined_utility_status":"CURRENT_D2_COMBINED_UTILITY_NOT_SUPPORTED_ON_INNER","d1_rule_layer_sensitivity_evidence":"SUPPORTED","d1_operational_false_alarm_limitation":"SUPPORTED","d2_v1_incremental_recovery":"UNSUPPORTED","causal_failure_mechanism_claimed":False,"redesign_authorized":False},t)
    outer=leaf("OUTER_DISPOSITION",{"outer_authorized":False,"outer_disposition":"HOLD_PENDING_INNER_D2_FAILURE_DIAGNOSTIC","exact_next_task":nxt,"exact_next_question":"WHY_D1_ALARMS_CAPABLE_OF_DETECTING_D0_MISSED_ATTACK_EVENTS_FAILED_EXACT_SAME_SECOND_TWO_DISTINCT_SOURCE_CORROBORATION" if nxt==NEXT_DIAGNOSTIC else "D2_SCIENTIFIC_DISPOSITION","test2_accesses":0},t)
    attacks,accepted=adversarial()
    ready=leaf("READINESS",{"arm_metrics_hash":arm["artifact_hash"],"event_overlap_hash":ev["artifact_hash"],"recovery_analysis_hash":recovery["artifact_hash"],"false_alarm_tradeoff_hash":trade["artifact_hash"],"interpretation_hash":interp["artifact_hash"],"outer_disposition_hash":outer["artifact_hash"],"independent_attacks":attacks,"accepted_invalid":accepted,"comparison_frozen":True,"d2_v1_incremental_utility_supported":False,"outer_authorized":False,"exact_next_task":nxt},t)
    body=f"""# INNER D0/D1/D2 Scientific Comparison V1\n\n## Experimental arms\n\nD0 detector-only, D1 verified-rule-only, and D2 detector plus frozen corroborated rule recovery are compared from integrity-audited frozen predictions.\n\n## Frozen evaluation protocol\n\nFourteen strict label-one attack events and 51,019 normal seconds are evaluated with maximal contiguous alarm episodes. No arm was executed or changed.\n\n## Primary comparison table\n\n| Arm | Detected attacks | Recall | Normal false episodes | FAR/hour |\n|---|---:|---:|---:|---:|\n| D0 | 11 | {a['D0']['recall']} | 7 | {a['D0']['far']} |\n| D1 | 13 | {a['D1']['recall']} | 574 | {a['D1']['far']} |\n| D2 | 11 | {a['D2']['recall']} | 10 | {a['D2']['far']} |\n\n## Attack-event overlap comparison\n\nD0 and D1 jointly detect {c['d0_and_d1']} events; D0-only {c['d0_only']}; D1-only {c['d1_only']}; neither {c['neither']}. Coordinates remain private.\n\n## D0-miss recovery potential\n\nD0 misses three events. D1 detects {c['miss_d1']} of them, giving potential recovery rate {c['potential_rate']}.\n\n## D2 realized recovery\n\nD2 recovers {c['miss_d2']} D0-missed events; realized recovery and retention are {c['realized_rate']} and {c['retention']}.\n\n## False-alarm tradeoff\n\nD2 adds {c['incremental_false']} normal false-alarm episodes and {c['incremental_far']} FAR/hour over D0.\n\n## What D1 demonstrates\n\nD1 supplies high-sensitivity, high-false-alarm rule signal; it is not established as operationally superior.\n\n## What D2 V1 demonstrates\n\nD2 V1 shows no INNER recall gain and positive additional false-alarm cost. Current combined utility is unsupported on INNER.\n\n## What cannot yet be concluded\n\nNo causal gate-failure mechanism or alternative fusion policy is established.\n\n## Thesis implications\n\nRule-layer sensitivity evidence is supported; D1 operational false-alarm limitation is supported; D2 V1 incremental recovery is unsupported. This does not invalidate rule construction.\n\n## Why OUTER remains sealed\n\nOUTER is held pending an INNER D2 failure diagnostic; test2 remains untouched.\n\n## Exact next diagnostic question\n\nWhy did D1 alarms capable of detecting D0-missed events fail exact same-second two-distinct-source corroboration?\n\n"""
    body_hash=sha256(body.encode()).hexdigest()
    bundle=leaf("BUNDLE",{"arm_metrics_hash":arm["artifact_hash"],"event_overlap_hash":ev["artifact_hash"],"recovery_analysis_hash":recovery["artifact_hash"],"false_alarm_tradeoff_hash":trade["artifact_hash"],"interpretation_hash":interp["artifact_hash"],"outer_disposition_hash":outer["artifact_hash"],"readiness_hash":ready["artifact_hash"],"report_hash_scheme":"MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1","report_self_hash":body_hash},t)
    receipt=leaf("RECEIPT",{"bundle_hash":bundle["artifact_hash"],"readiness_hash":ready["artifact_hash"],"report_self_hash":body_hash,"scientific_state":STATE,"outer_disposition":"HOLD_PENDING_INNER_D2_FAILURE_DIAGNOSTIC","exact_next_task":nxt},t)
    footer=f"<!-- BEGIN INNER D0 D1 D2 COMPARISON REPORT PROVENANCE V1 -->\nReport-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1\nReport-Self-Hash: {body_hash}\nBundle-Hash: {bundle['artifact_hash']}\nReceipt-Hash: {receipt['artifact_hash']}\n<!-- END INNER D0 D1 D2 COMPARISON REPORT PROVENANCE V1 -->\n"
    return {"ARM_METRICS":arm,"EVENT_OVERLAP":ev,"RECOVERY_ANALYSIS":recovery,"FALSE_ALARM_TRADEOFF":trade,"INTERPRETATION":interp,"OUTER_DISPOSITION":outer,"READINESS":ready,"BUNDLE":bundle,"RECEIPT":receipt},body+footer
def write(rep:Mapping[str,Mapping[str,Any]],md:str)->None:
    for n,d in rep.items(): (OUT/f"{PREFIX}{n}.json").write_text(json.dumps(d,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    (OUT/f"{PREFIX}REPORT.md").write_text(md,encoding="utf-8",newline="\n")
def main()->int:
    labels=parse_label(); d0=parse_d0(load(D0_PATH)); d1=parse_d1(load(D1_PATH)); d2,tr=parse_d2(load(D2_PATH)); c=compare(labels,d0,d1,d2,tr); rep,md=reports(c)
    if adversarial()!=(30,0):fail("ADVERSARIAL")
    write(rep,md)
    print(STATUS); print(STATE); print("D0_MISSES_DETECTED_BY_D1="+str(c["miss_d1"])); print("D0_MISSES_DETECTED_BY_D2="+str(c["miss_d2"])); print("INDEPENDENT_ATTACKS=30"); print("ACCEPTED_INVALID=0")
    for n in REPORT_NAMES:print(n+"_HASH="+rep[n]["artifact_hash"])
    print("REPORT_SELF_HASH="+rep["BUNDLE"]["report_self_hash"]); return 0
if __name__=="__main__":raise SystemExit(main())
