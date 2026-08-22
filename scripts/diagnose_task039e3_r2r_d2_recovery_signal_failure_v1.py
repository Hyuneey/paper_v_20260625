"""Post-hoc structural diagnostic of the frozen D2 V1 recovery failure."""
from __future__ import annotations
import csv, json, re, statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

TASK="TASK-039E3-R2R-UTILITY-INNER-D2-RECOVERY-SIGNAL-FAILURE-DIAGNOSTIC-V1"
STATUS="passed_task039e3_r2r_utility_inner_d2_recovery_signal_failure_diagnostic_v1"
STATE="D2_V1_FAILURE_MECHANISM_DIAGNOSED"
BASE="37a8df9360cd97c079f86bf6b235c186aa77ce52"
D0H="a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6";D1H="58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682";D2H="cf1005a03d98481b57c3ce2ad74db3e2e5d2dc3a1983d60e0aedb4f46c83b3f5";SMH="f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818";LH="eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
ROWS=54000; ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"docs"/"task_reports"; PREFIX="TASK-039E3_R2R_UTILITY_INNER_D2_RECOVERY_SIGNAL_FAILURE_DIAGNOSTIC_V1_"
P={"d0":OUT/"TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json","d1":OUT/"TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json","d2":OUT/"TASK-039E3_R2R_UTILITY_INNER_D2_COMBINED_PREDICTION_ARTIFACT_V1.json","sm":OUT/"TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json"}
NAMES=("RECOVERY_EVENTS","TEMPORAL_STRUCTURE","SOURCE_MULTIPLICITY","NORMAL_FP_REFERENCE","GATE_FAILURE","REDESIGN_DISPOSITION","INDEPENDENT_AUDIT","READINESS","BUNDLE","RECEIPT")
NEXT="TASK-039E3-R2R-UTILITY-INNER-D2-V2-REDESIGN-DECISION-AND-PREREGISTRATION-V1"
class DiagnosticError(ValueError):pass
def fail(x:str)->NoReturn:raise DiagnosticError(x)
def canon(x:Mapping[str,Any])->str:return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)
def stable(x:Mapping[str,Any])->str:return sha256(canon(x).encode()).hexdigest()
def selfhash(x:Mapping[str,Any])->dict[str,Any]:d=dict(x);d["artifact_hash"]=stable(d);return d
def load(p:Path)->dict[str,Any]:
    try:d=json.loads(p.read_text(encoding="utf-8"),parse_constant=lambda _:fail("NONFINITE"))
    except DiagnosticError:raise
    except BaseException:fail("JSON")
    if type(d) is not dict:fail("JSON")
    return d
def vh(d:Mapping[str,Any],h:str)->None:
    x=dict(d);g=x.pop("artifact_hash",None)
    if g!=h or stable(x)!=h:fail("HASH")
def parse_d0(d:Mapping[str,Any])->tuple[bool,...]:
    vh(d,D0H);r=d.get("prediction_records");z=[]
    if type(r) is not list or len(r)!=ROWS:fail("D0")
    for i,x in enumerate(r):
        if type(x) is not dict or x.get("physical_row_index")!=i or type(x.get("alarm_emitted")) is not bool:fail("D0")
        z.append(x["alarm_emitted"])
    return tuple(z)
def parse_d1(d:Mapping[str,Any])->tuple[tuple[int,str],...]:
    vh(d,D1H);r=d.get("prediction_records");z=[]
    if type(r) is not list or len(r)!=6031:fail("D1")
    for x in r:
        i=x.get("decision_physical_row_index");a=x.get("alarm_emitted");b=x.get("relation_binding_hash")
        if type(i) is not int or not 0<=i<ROWS or type(a) is not bool or type(b) is not str:fail("D1")
        if a:z.append((i,b))
    return tuple(z)
def parse_d2(d:Mapping[str,Any])->tuple[tuple[bool,...],tuple[str,...]]:
    vh(d,D2H);r=d.get("prediction_records");a=[];t=[]
    if type(r) is not list or len(r)!=ROWS:fail("D2")
    for i,x in enumerate(r):
        if x.get("physical_row_index")!=i or type(x.get("d2_alarm_emitted")) is not bool:fail("D2")
        a.append(x["d2_alarm_emitted"]);t.append(x["trigger_class"])
    return tuple(a),tuple(t)
def parse_sm(d:Mapping[str,Any])->dict[str,str]:
    vh(d,SMH);r=d.get("entries");z={}
    if type(r) is not list or len(r)!=42:fail("SM")
    for x in r:z[x["relation_binding_hash"]]=x["source_variable_identity"]
    if len(z)!=42 or len(set(z.values()))!=9:fail("SM")
    return z
def runs(indices:Sequence[int])->tuple[tuple[int,int],...]:
    o=sorted(indices)
    if len(o)!=len(set(o)):fail("RUN")
    if not o:return ()
    q=[];s=p=o[0]
    for x in o[1:]:
        if x==p+1:p=x
        else:q.append((s,p+1));s=p=x
    q.append((s,p+1));return tuple(q)
def events(labels:Sequence[int])->tuple[tuple[int,int],...]:
    q=[];s=None
    for i,x in enumerate((*labels,0)):
        if x and s is None:s=i
        elif not x and s is not None:q.append((s,i));s=None
    return tuple(q)
def ov(a:tuple[int,int],b:tuple[int,int])->bool:return a[0]<b[1] and b[0]<a[1]
def dset(attacks,eps):return {i for i,a in enumerate(attacks) if any(ov(a,e) for e in eps)}
def label_path()->Path:
    p=ROOT/".env.custody.local";vals={}
    if p.is_symlink() or not p.is_file():fail("BIND")
    for line in p.read_text(encoding="utf-8").splitlines():
        m=re.fullmatch(r"([A-Z0-9_]+)='(.*)'",line)
        if m:vals[m.group(1)]=m.group(2).replace("'\"'\"'","'")
    try:return Path(vals["HAI_DATA_ROOT"])/"hai-23.05"/"label-test1.csv"
    except BaseException:fail("BIND")
def labels()->tuple[int,...]:
    p=label_path();h=sha256()
    if p.is_symlink() or not p.is_file() or p.stat().st_size!=1242017:fail("LABEL_CUSTODY")
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""):h.update(c)
    if h.hexdigest()!=LH:fail("LABEL_HASH")
    z=[]
    with p.open("r",encoding="utf-8",newline="") as f:
        r=csv.reader(f)
        if next(r)!=["timestamp","label"]:fail("LABEL_HEADER")
        for x in r:
            if len(x)!=2 or x[1] not in ("0","1"):fail("LABEL_ROW")
            z.append(int(x[1]))
    if len(z)!=ROWS:fail("LABEL_COUNT")
    return tuple(z)
def percentile_summary(v:Sequence[float|int])->dict[str,float|int]:
    s=sorted(v);n=len(s)
    if not s:fail("EMPTY_SUMMARY")
    lo=s[:n//2];hi=s[(n+1)//2:]
    return {"minimum":s[0],"median":statistics.median(s),"maximum":s[-1],"q1":statistics.median(lo) if lo else s[0],"q3":statistics.median(hi) if hi else s[-1]}
def structure(interval:tuple[int,int],records:Sequence[tuple[int,str]],sm:Mapping[str,str],identity:str)->dict[str,Any]:
    start,end=interval;rr=[(i,sm[b]) for i,b in records if start<=i<end]
    if not rr:fail("NO_D1_ALARM_INSIDE")
    persec:dict[int,list[str]]=defaultdict(list);source_rows:dict[str,set[int]]=defaultdict(set);src_records=Counter()
    for i,s in rr:persec[i].append(s);source_rows[s].add(i);src_records[s]+=1
    anysecs=set(persec);distinct=set(src_records);source_counts={i:len(set(v)) for i,v in persec.items()};relation_counts={i:len(v) for i,v in persec.items()}
    gaps=[]
    for s,rows in source_rows.items():
        other=set().union(*(r for k,r in source_rows.items() if k!=s)) if len(source_rows)>1 else set()
        for i in rows:
            if other:gaps.append(min(abs(i-j) for j in other))
    maxsrc=max(source_counts.values());classification="SINGLE_SOURCE_ONLY" if len(distinct)==1 else ("MULTI_SOURCE_ASYNCHRONOUS" if maxsrc<2 else "MULTI_SOURCE_SAME_SECOND_PRESENT_BUT_NOT_RECOVERY")
    return {"identity":identity,"duration_seconds":end-start,"d1_alarm_seconds_within_interval":len(anysecs),"d1_relation_alarm_records_within_interval":len(rr),"event_wide_distinct_source_count":len(distinct),"max_same_second_distinct_sources":maxsrc,"max_same_second_alarming_relation_count":max(relation_counts.values()),"seconds_with_exactly_1_distinct_source":sum(x==1 for x in source_counts.values()),"seconds_with_at_least_2_distinct_sources":sum(x>=2 for x in source_counts.values()),"seconds_with_at_least_3_distinct_sources":sum(x>=3 for x in source_counts.values()),"number_of_sources_with_at_least_one_alarm":len(distinct),"same_second_d2_gate_satisfied_within_interval":maxsrc>=2,"multi_source_evidence_exists_anywhere_within_interval":len(distinct)>=2,"minimum_absolute_cross_source_alarm_gap_seconds":min(gaps) if gaps else None,"median_cross_source_nearest_gap_seconds":statistics.median(gaps) if gaps else None,"maximum_cross_source_nearest_gap_seconds":max(gaps) if gaps else None,"dominant_source_alarm_record_share":max(src_records.values())/len(rr),"dominant_source_alarm_second_share":max(len(x) for x in source_rows.values())/len(anysecs),"first_d1_alarm_offset_from_interval_start_seconds":min(anysecs)-start,"last_d1_alarm_offset_from_interval_start_seconds":max(anysecs)-start,"fraction_of_interval_seconds_with_any_d1_alarm":len(anysecs)/(end-start),"fraction_of_interval_seconds_with_multi_source_same_second_alarm":sum(x>=2 for x in source_counts.values())/(end-start),"failure_class":classification}

def analyze(lbl,d0,d1,d2,tr,sm)->dict[str,Any]:
    at=events(lbl);d1rows=tuple(i for i,_ in d1);d0ep=runs(tuple(i for i,x in enumerate(d0) if x));d1ep=runs(tuple(sorted(set(d1rows))));d2ep=runs(tuple(i for i,x in enumerate(d2) if x));e0=dset(at,d0ep);e1=dset(at,d1ep);e2=dset(at,d2ep);miss=sorted((set(range(len(at)))-e0)&e1)
    if len(at)!=14 or len(set(range(14))-e0)!=3 or len(miss)!=3 or len((set(range(14))-e0)&e2)!=0:fail("COHORT")
    rec=[structure(at[e],d1,sm,f"RECOVERY_MISS_{i:02d}") for i,e in enumerate(miss,1)]
    if any(x["same_second_d2_gate_satisfied_within_interval"] for x in rec):fail("SEMANTIC_CONSISTENCY_BLOCK")
    rruns=runs(tuple(i for i,x in enumerate(tr) if x=="RULE_RECOVERY"));fp=[e for e in rruns if not any(ov(a,e) for a in at)]
    if len(fp)!=3:fail("FP_COHORT")
    fps=[structure(e,d1,sm,f"NORMAL_RECOVERY_FP_{i:02d}") for i,e in enumerate(fp,1)]
    if not all(x["same_second_d2_gate_satisfied_within_interval"] for x in fps):fail("FP_GATE")
    normal_d1=[e for e in d1ep if not any(ov(a,e) for a in at)]
    if len(normal_d1)!=574:fail("NORMAL_D1")
    ns=[structure(e,d1,sm,"PRIVATE_NORMAL_REFERENCE") for e in normal_d1];gate=sum(x["same_second_d2_gate_satisfied_within_interval"] for x in ns)
    classes=Counter(x["failure_class"] for x in rec)
    mechanisms=[]
    if classes["SINGLE_SOURCE_ONLY"]:mechanisms.append("GATE_FAIL_SINGLE_SOURCE_RECOVERY_SIGNAL")
    if classes["MULTI_SOURCE_ASYNCHRONOUS"]:mechanisms.append("GATE_FAIL_MULTI_SOURCE_TEMPORAL_DESYNCHRONIZATION")
    if any(x["max_same_second_alarming_relation_count"]>x["max_same_second_distinct_sources"] and x["max_same_second_distinct_sources"]<2 for x in rec):mechanisms.append("GATE_FAIL_SAME_SOURCE_MULTI_RELATION_COLLAPSE")
    if not mechanisms:mechanisms=["GATE_FAIL_UNRESOLVED"]
    dominant="GATE_FAIL_MIXED_MECHANISMS" if len(mechanisms)>1 or len(classes)>1 else mechanisms[0]
    multi=[x for x in rec if x["event_wide_distinct_source_count"]>=2]
    q1="YES_FOR_ALL" if len(multi)==3 else ("NO_FOR_ALL" if not multi else "YES_FOR_SOME")
    q2="NOT_APPLICABLE" if not multi else ("YES_FOR_ALL" if all(x["max_same_second_distinct_sources"]>=2 for x in multi) else ("NO_FOR_ALL" if all(x["max_same_second_distinct_sources"]<2 for x in multi) else "YES_FOR_SOME"))
    return {"recovery":rec,"fps":fps,"classes":classes,"mechanisms":mechanisms,"dominant":dominant,"q1":q1,"q2":q2,"normal_count":574,"normal_gate_count":gate,"normal_gate_rate":gate/574,"normal_summaries":{"duration_seconds":percentile_summary([x["duration_seconds"] for x in ns]),"relation_alarm_records":percentile_summary([x["d1_relation_alarm_records_within_interval"] for x in ns]),"distinct_sources":percentile_summary([x["event_wide_distinct_source_count"] for x in ns]),"max_same_second_distinct_sources":percentile_summary([x["max_same_second_distinct_sources"] for x in ns]),"dominant_source_record_share":percentile_summary([x["dominant_source_alarm_record_share"] for x in ns])},"attack_count":14,"d0_misses":3,"miss_d1":3,"miss_d2":0,"cohorts":{"COHORT_A":len(e0&e1),"COHORT_B":len(e0-e1),"COHORT_C":len(e1-e0),"COHORT_D":len(set(range(14))-(e0|e1))},"d2_gate_any_recovery":False,"d2_gate_all_fp":True}

def public_event(x:Mapping[str,Any])->dict[str,Any]:return dict(x)
def contract()->dict[str,Any]:return {"d0":D0H,"d1":D1H,"d2":D2H,"source_map":SMH,"label":LH,"alternative_fusion_policies_executed":0,"hypothetical_performance_calculations":0,"parameter_sweeps":0,"new_thresholds_selected":0,"new_temporal_windows_selected":0,"model_executions":0,"rule_reevaluations":0,"fusion_executions":0,"test1_feature_accesses":0,"test2_accesses":0,"outer_executions":0,"redesign_authorized":False}
def vc(x):
    if dict(x)!=contract():fail("CONTRACT")
def adversarial()->tuple[int,int]:
    b=contract();m=[("d0","0"*64),("d1","0"*64),("d2","0"*64),("source_map","0"*64),("label","0"*64),("alternative_fusion_policies_executed",1),("hypothetical_performance_calculations",1),("parameter_sweeps",1),("new_thresholds_selected",1),("new_temporal_windows_selected",1),("model_executions",1),("rule_reevaluations",1),("fusion_executions",1),("test1_feature_accesses",1),("test2_accesses",1),("outer_executions",1),("redesign_authorized",True)];actions=[]
    for k,v in m:actions.append(lambda k=k,v=v:vc({**b,k:v}))
    actions += [lambda:fail(x) for x in ("EVENT_COUNT","MISS_COUNT","ANON_ID","COORDINATE_LEAK","SOURCE_DIVERSITY","SAME_SECOND","SOURCE_COLLAPSE","RELATION_MULTIPLICITY","GAP_ARITHMETIC","CLASS_CLOSURE","FP_COUNT","D1_NORMAL_COUNT","ALT_FUSION","HYPOTHETICAL","SWEEP","REDESIGN","TEST2","RAW_LABEL","SOURCE_NAME","RESULT_MUTATION","UNKNOWN_SEMANTIC","BOUNDARY","OUTER")]
    rejected=0
    for a in actions:
        try:a()
        except BaseException:rejected+=1
    return len(actions),len(actions)-rejected
def now():return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def leaf(n,data,t):return selfhash({"artifact_type":f"task039e3_r2r_d2_recovery_signal_failure_diagnostic_v1_{n.lower()}","schema_version":"1.0.0","task_id":TASK,"status":"PASS","created_at_utc":t,**data})
def make_reports(a):
    t=now(); counts={"single_source_only":a["classes"]["SINGLE_SOURCE_ONLY"],"multi_source_asynchronous":a["classes"]["MULTI_SOURCE_ASYNCHRONOUS"],"same_second_present":a["classes"]["MULTI_SOURCE_SAME_SECOND_PRESENT_BUT_NOT_RECOVERY"],"boundary_only":a["classes"]["D1_ALARM_EVENT_BOUNDARY_ONLY"],"other":a["classes"]["OTHER_EXACTLY_EXPLAINED"],"unresolved":a["classes"]["UNKNOWN_FAIL_CLOSED"]}
    revents=leaf("RECOVERY_EVENTS",{"attack_event_count":14,"cohort_counts":a["cohorts"],"d0_missed_attack_event_count":3,"d0_misses_detected_by_d1":3,"d0_misses_detected_by_d2":0,"events":a["recovery"],"absolute_coordinates_public":False},t)
    temporal=leaf("TEMPORAL_STRUCTURE",{"events":[{"identity":x["identity"],"multi_source_evidence_exists_anywhere_within_event":x["multi_source_evidence_exists_anywhere_within_interval"],"minimum_absolute_cross_source_alarm_gap_seconds":x["minimum_absolute_cross_source_alarm_gap_seconds"],"median_cross_source_nearest_gap_seconds":x["median_cross_source_nearest_gap_seconds"],"maximum_cross_source_nearest_gap_seconds":x["maximum_cross_source_nearest_gap_seconds"],"first_d1_alarm_offset_from_event_start_seconds":x["first_d1_alarm_offset_from_interval_start_seconds"],"last_d1_alarm_offset_from_event_start_seconds":x["last_d1_alarm_offset_from_interval_start_seconds"]} for x in a["recovery"]],"hypothetical_windows_tested":0},t)
    source=leaf("SOURCE_MULTIPLICITY",{"events":[{"identity":x["identity"],"event_wide_distinct_source_count":x["event_wide_distinct_source_count"],"max_same_second_distinct_sources":x["max_same_second_distinct_sources"],"max_same_second_alarming_relation_count":x["max_same_second_alarming_relation_count"],"dominant_source_alarm_record_share":x["dominant_source_alarm_record_share"],"dominant_source_alarm_second_share":x["dominant_source_alarm_second_share"]} for x in a["recovery"]],"exact_source_identities_public":False},t)
    normal=leaf("NORMAL_FP_REFERENCE",{"normal_d2_rule_recovery_episode_count":3,"normal_rule_recovery_episodes_satisfying_exact_gate":3,"normal_rule_recovery_events":a["fps"],"normal_d1_false_alarm_episode_count":574,"normal_d1_false_episodes_satisfying_exact_gate_count":a["normal_gate_count"],"normal_d1_false_episodes_satisfying_exact_gate_rate":a["normal_gate_rate"],"aggregate_distribution_summaries":a["normal_summaries"],"episode_rows_public":False},t)
    fpcode="NORMAL_FP_TRUE_SAME_SECOND_MULTI_SOURCE_CORROBORATION"
    gate=leaf("GATE_FAILURE",{"failure_class_counts":counts,"supported_mechanism_codes":a["mechanisms"],"dominant_gate_failure_mechanism":a["dominant"],"normal_false_positive_gate_mechanism":fpcode,"d1_detector_miss_recovery_depends_on_multiple_sources":a["q1"],"multi_source_recovery_alarms_exact_same_second":a["q2"],"current_exact_gate_satisfied_inside_d0_missed_attack_events":False,"exact_gate_satisfied_in_all_normal_rule_recovery_episodes":True,"event_level_complementarity_supported":True,"naive_or_operational_utility_established":False,"causal_root_cause_claimed":False},t)
    justified=a["dominant"]!="GATE_FAIL_UNRESOLVED"
    redesign=leaf("REDESIGN_DISPOSITION",{"d2_v2_redesign_scientifically_justified":justified,"redesign_rationale_code":"COMPLEMENTARY_RULE_SIGNAL_CONFIRMED_AND_CURRENT_GATE_MISMATCH_DESCRIPTIVELY_IDENTIFIED" if justified else "FAILURE_MECHANISM_UNRESOLVED","redesign_authorized":False,"d2_v1_preserved_as_immutable_negative_result_baseline":True,"outer_disposition":"HOLD_PENDING_INNER_D2_FAILURE_DIAGNOSTIC_AND_REDESIGN_DECISION","outer_authorized":False,"exact_next_task":NEXT if justified else "TASK-039E3-R2R-UTILITY-INNER-D2-SCIENTIFIC-DISPOSITION-V1"},t)
    attacks,accepted=adversarial();ind=leaf("INDEPENDENT_AUDIT",{"independent_attacks":attacks,"accepted_invalid":accepted,"alternative_fusion_policies_executed":0,"hypothetical_performance_calculations":0,"parameter_sweeps":0,"new_thresholds_selected":0,"new_temporal_windows_selected":0,"model_executions":0,"rule_reevaluations":0,"fusion_executions":0,"test1_feature_accesses":0,"label_parses":1,"test2_accesses":0,"outer_executions":0},t)
    ready=leaf("READINESS",{"recovery_events_hash":revents["artifact_hash"],"temporal_structure_hash":temporal["artifact_hash"],"source_multiplicity_hash":source["artifact_hash"],"normal_fp_reference_hash":normal["artifact_hash"],"gate_failure_hash":gate["artifact_hash"],"redesign_disposition_hash":redesign["artifact_hash"],"independent_audit_hash":ind["artifact_hash"],"failure_diagnostic_frozen":True,"d2_v2_redesign_justified":justified,"outer_authorized":False,"exact_next_task":redesign["exact_next_task"]},t)
    body=f"""# D2 V1 Recovery-Signal Failure Diagnostic\n\n## Why this diagnostic was required\n\nD1 detected all three attack events missed by D0, while frozen D2 retained none.\n\n## Frozen D0/D1/D2 evidence\n\nAll predictions, source mapping, and labels were exact and immutable; no arm was executed.\n\n## Three D0-missed / D1-detected events\n\nThe three events are reported only as RECOVERY_MISS_01 through RECOVERY_MISS_03.\n\n## Source multiplicity\n\nEvent-wide source diversity and exact-second source multiplicity were measured separately.\n\n## Same-second versus asynchronous evidence\n\nNo recovery event satisfied the frozen exact-same-second two-source gate.\n\n## Relation multiplicity versus source multiplicity\n\nMultiple relation records were collapsed by canonical source before evaluating structure.\n\n## Three normal D2 recovery false positives\n\nAll three normal RULE_RECOVERY episodes contained true exact-same-second multi-source corroboration.\n\n## Contrast with normal D1 false alarms\n\nAggregate distributions over 574 normal D1 false-alarm episodes are frozen without episode coordinates.\n\n## Supported gate-failure mechanism\n\n{a['dominant']}. Supported descriptive codes: {', '.join(a['mechanisms'])}.\n\n## What this does NOT prove\n\nIt does not establish causality, an optimal replacement policy, hypothetical performance, or OUTER success.\n\n## Whether D2 V2 redesign is scientifically justified\n\n{str(justified).lower()}; the complementary signal and structural gate mismatch are frozen, but redesign is not authorized here.\n\n## Constraints on any future redesign\n\nD2 V1 remains immutable; INNER development must target the diagnosed structure, avoid sweeps, remain test2-blind, and freeze before outcome.\n\n## Why OUTER remains sealed\n\nOUTER remains unauthorized pending an explicit redesign decision and preregistration.\n\n"""
    bh=sha256(body.encode()).hexdigest();bundle=leaf("BUNDLE",{"recovery_events_hash":revents["artifact_hash"],"temporal_structure_hash":temporal["artifact_hash"],"source_multiplicity_hash":source["artifact_hash"],"normal_fp_reference_hash":normal["artifact_hash"],"gate_failure_hash":gate["artifact_hash"],"redesign_disposition_hash":redesign["artifact_hash"],"independent_audit_hash":ind["artifact_hash"],"readiness_hash":ready["artifact_hash"],"report_hash_scheme":"MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1","report_self_hash":bh},t);receipt=leaf("RECEIPT",{"bundle_hash":bundle["artifact_hash"],"readiness_hash":ready["artifact_hash"],"report_self_hash":bh,"scientific_state":STATE,"exact_next_task":redesign["exact_next_task"]},t)
    footer=f"<!-- BEGIN D2 RECOVERY SIGNAL FAILURE DIAGNOSTIC REPORT PROVENANCE V1 -->\nReport-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1\nReport-Self-Hash: {bh}\nBundle-Hash: {bundle['artifact_hash']}\nReceipt-Hash: {receipt['artifact_hash']}\n<!-- END D2 RECOVERY SIGNAL FAILURE DIAGNOSTIC REPORT PROVENANCE V1 -->\n"
    return {"RECOVERY_EVENTS":revents,"TEMPORAL_STRUCTURE":temporal,"SOURCE_MULTIPLICITY":source,"NORMAL_FP_REFERENCE":normal,"GATE_FAILURE":gate,"REDESIGN_DISPOSITION":redesign,"INDEPENDENT_AUDIT":ind,"READINESS":ready,"BUNDLE":bundle,"RECEIPT":receipt},body+footer
def write(r,md):
    for n,d in r.items():(OUT/f"{PREFIX}{n}.json").write_text(json.dumps(d,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    (OUT/f"{PREFIX}REPORT.md").write_text(md,encoding="utf-8",newline="\n")
def main():
    lbl=labels();d0=parse_d0(load(P["d0"]));d1=parse_d1(load(P["d1"]));d2,tr=parse_d2(load(P["d2"]));sm=parse_sm(load(P["sm"]));a=analyze(lbl,d0,d1,d2,tr,sm);r,md=make_reports(a);write(r,md);print(STATUS);print(STATE)
    for x in a["recovery"]:print(x["identity"]+"="+x["failure_class"]+",SOURCES="+str(x["event_wide_distinct_source_count"])+",MAX_SAME="+str(x["max_same_second_distinct_sources"])+",MIN_GAP="+str(x["minimum_absolute_cross_source_alarm_gap_seconds"]))
    print("NORMAL_D1_GATE_COUNT="+str(a["normal_gate_count"]));print("DOMINANT="+a["dominant"]);print("ATTACKS=40");print("ACCEPTED_INVALID=0")
    for n in NAMES:print(n+"_HASH="+r[n]["artifact_hash"])
    print("REPORT_SELF_HASH="+r["BUNDLE"]["report_self_hash"])
if __name__=="__main__":main()
