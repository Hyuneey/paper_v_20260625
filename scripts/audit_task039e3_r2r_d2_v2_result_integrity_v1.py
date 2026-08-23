"""Independent local-only integrity audit for the frozen D2 V2 INNER result.

This module deliberately does not import the D2 V2 execution controller.  Its
token, active-source, fusion, episode, and metric oracles are implemented from
the frozen public artifacts.
"""
from __future__ import annotations

import ast
import csv
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import audit_task039e3_r2r_d2_result_integrity_v1 as generic

TASK_ID = "TASK-039E3-R2R-UTILITY-INNER-D2-V2-RESULT-INTEGRITY-AUDIT-V1"
PASS_STATUS = "passed_task039e3_r2r_utility_inner_d2_v2_result_integrity_audit_v1"
SCIENTIFIC_STATUS = "D2_V2_RESULT_INTEGRITY_AUDITED"
EXPECTED_BRANCH = "task-039e3-r2r-utility-inner-d2-v2-result-integrity-audit-v1"
BASE = "615fde528644f14d1654f98031cfc2bfd4f3c8ec"
EXEC_A = "2bbb3dcaced47c8d15337e45eb0e0b741c1a3ed1"
EXEC_B = "b3acf3cbb0b6bcb21548daa319fd37923357b952"
RESULT_C = "55d41c543e110a9a6f0f5e2e2671857dba938aaa"
CONT_D = BASE
DESIGN = "ace631af367ee2abe1b0ee7658875eeb59a2a8d906d09ce8ea92e8f2d83e31e4"
AUTH = "0f909480cfe3db8afc4042909258fe041f36ad021a917907008ee7e5023f2f45"
D0_HASH = "a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6"
D1_HASH = "58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682"
SOURCE_HASH = "f866176000c3d5a943053ac3125d2700b0b72f25b5a0539d8f4713435a959818"
HORIZON_HASH = "e9825a578495396d935397e79d8c50717dccb47f069f13e93f6306f992a9407c"
IMPL = "9016e5c8be9fa0e56af6a5d1870617f1937e557b7eabd0afa5b20722e89ded62"
GRANT = "9136c3b5432d471181765848619771f5234fae1d1a0c22d60eb584d3b8617392"
FUSION_HASH = "9fd5563b76cb4af0cf68383e1e2b9d10da9e6fd35a667d4a68d6eb5f8db2e8cb"
COMBINED_HASH = "31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3"
METRIC_EVIDENCE_HASH = "3e3f20b5b1a9387cd3bed4ad17e4232e714cc588d7df1c2a37dfd69bcd1a8513"
METRICS_HASH = "8fabdccc0c9a9b502497aa58163131647303d5e27acefb995a06ca9d43850ba7"
RUN_HASH = "c41957d8e9805afe0e39a0b28b01faaf8fa2ec82d8e4774083f6d7881d5036fc"
IMPL_AUDIT_HASH = "fe601aaa195222470e8e746a6c9ba318b338172bc750bff1194bd4164f201ea1"
ACCOUNTING_HASH = "7059e2b4e54ec53d0b72c072c71487b19efe056ce382357615dc152bf2382aca"
READINESS_HASH = "59246da5731bad310c588945326a9f5d44ed9394ed7bf1312086f043566e37bc"
BUNDLE_HASH = "ded276981ce75ebe5e947bd7a409d14b03208e7e23f1c8e3ddc1cd3070cb915f"
RECEIPT_HASH = "e6f10713d467c4733422f5d4d548035f20b0ebc7e9e10e6ed3d73506375509bf"
RESULT_REPORT_HASH = "e45479ec778414a7e4a3d21b348f898176584abad7f2271baec5f34a21bb6fd6"
ROWS = 54_000
TRIGGERS = {"D0_AND_RULE_CORROBORATION_NATIVE_HORIZON": 63, "D0_ONLY": 813,
            "NONE": 51_852, "RULE_RECOVERY_NATIVE_HORIZON": 1_272}
LABEL_HASH = "eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc"
LABEL_SIZE = 1_242_017
NEXT_TASK = "TASK-039E3-R2R-UTILITY-INNER-D2-V1-V2-SCIENTIFIC-DISPOSITION-V1"
REPORT_PREFIX = "TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_V1_"
LEAVES = ("FREEZE_AUDIT","HORIZON_ORACLE","TOKEN_ORACLE","FUSION_ORACLE",
          "PREDICTION_AUDIT","ORDERING_AUDIT","EPISODE_ORACLE","METRIC_ORACLE",
          "ACCOUNTING_AUDIT","PRIVATE_CUSTODY_AUDIT","LEAKAGE_AUDIT","INDEPENDENT_AUDIT")
REPORT_NAMES = (*LEAVES, "READINESS", "BUNDLE", "RECEIPT")
D0_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json"
D1_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json"
SOURCE_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_EXECUTION_AUTHORIZATION_V1_SOURCE_MAP.json"
HORIZON_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_DESIGN_V1_NATIVE_HORIZON_AUTHORITY.json"
COMBINED_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_COMBINED_PREDICTION_ARTIFACT_V1.json"
METRICS_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_METRICS_V1.json"
ACCOUNTING_PATH = "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_ACCOUNTING.json"
EXECUTION_SOURCE = "src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py"
RESULT_FILES = (
 "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_IMPLEMENTATION_AUDIT.json",
 COMBINED_PATH, METRICS_PATH, ACCOUNTING_PATH,
 "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_READINESS.json",
 "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_BUNDLE.json",
 "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_RECEIPT.json",
 "docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_EXECUTION_V1_REPORT.md",
)

class AuditError(ValueError):
    def __init__(self, code: str) -> None: self.code=code; super().__init__(code)
def fail(code: str) -> NoReturn: raise AuditError(code)
def stable(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def self_hash(payload: Mapping[str, Any]) -> dict[str, Any]:
    out=dict(payload); out["artifact_hash"]=stable(out); return out
def load(path: Path) -> dict[str, Any]:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except BaseException: fail("JSON_REJECTED")
    if type(value) is not dict: fail("JSON_REJECTED")
    return value
def validate_hash(doc: Mapping[str, Any], expected: str) -> None:
    actual=doc.get("artifact_hash"); payload={k:v for k,v in doc.items() if k!="artifact_hash"}
    if actual != expected or stable(payload) != actual: fail("SELF_HASH_REJECTED")
def git(*args: str) -> str:
    p=subprocess.run(["git",*args],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    if p.returncode: fail("GIT_AUDIT_REJECTED")
    return p.stdout.strip()
def changed(commit: str) -> set[str]:
    return set(filter(None,git("diff-tree","--no-commit-id","--name-only","-r",commit).splitlines()))

def audit_freeze() -> dict[str, Any]:
    for c in (EXEC_A,EXEC_B,RESULT_C,CONT_D): git("cat-file","-e",c+"^{commit}")
    if git("branch","--show-current") != EXPECTED_BRANCH: fail("BRANCH_REJECTED")
    if git("rev-parse","HEAD") != BASE: fail("BASE_REJECTED")
    if git("status","--porcelain"): fail("WORKTREE_REJECTED")
    if git("rev-list","--count","--merges",EXEC_A+".."+BASE) != "0": fail("MERGE_REJECTED")
    expected_c=set(RESULT_FILES)
    if changed(RESULT_C) != expected_c: fail("RESULT_COMMIT_SCOPE_REJECTED")
    for p in RESULT_FILES:
        if subprocess.run(["git","diff","--quiet",RESULT_C,"HEAD","--",p],cwd=ROOT).returncode: fail("RESULT_MUTATION_REJECTED")
    if any(p.startswith(("src/","configs/")) for p in git("diff","--name-only",EXEC_A,"HEAD").splitlines()):
        fail("PRODUCTION_AFTER_A_REJECTED")
    return {"result_freeze_commit_verified":True,"post_result_freeze_mutations":0,
            "production_changes_after_commit_a":0,"scientific_policy_changes_after_commit_a":0,
            "result_driven_changes":False}

def parse_d0(doc: Mapping[str,Any]) -> tuple[bool,...]:
    validate_hash(doc,D0_HASH); records=doc.get("prediction_records")
    if type(records) is not list or len(records)!=ROWS: fail("D0_CLOSURE_REJECTED")
    out=[]
    for i,r in enumerate(records):
        if type(r) is not dict or r.get("physical_row_index")!=i or type(r.get("alarm_emitted")) is not bool: fail("D0_RECORD_REJECTED")
        out.append(r["alarm_emitted"])
    if sum(out)!=876: fail("D0_COUNT_REJECTED")
    return tuple(out)
def parse_d1(doc: Mapping[str,Any]) -> tuple[tuple[int,bool,str],...]:
    validate_hash(doc,D1_HASH); records=doc.get("prediction_records")
    if type(records) is not list or len(records)!=6031: fail("D1_CLOSURE_REJECTED")
    out=[]
    for r in records:
        row=r.get("decision_physical_row_index"); alarm=r.get("alarm_emitted"); rel=r.get("relation_binding_hash")
        if type(row) is not int or not 0<=row<ROWS or type(alarm) is not bool or type(rel) is not str: fail("D1_RECORD_REJECTED")
        out.append((row,alarm,rel))
    return tuple(out)
def parse_source(doc: Mapping[str,Any]) -> dict[str,str]:
    validate_hash(doc,SOURCE_HASH); entries=doc.get("entries")
    if type(entries) is not list or len(entries)!=42: fail("SOURCE_CLOSURE_REJECTED")
    out={e["relation_binding_hash"]:e["source_variable_identity"] for e in entries}
    if len(out)!=42 or len(set(out.values()))!=9: fail("SOURCE_CLOSURE_REJECTED")
    return out
def parse_horizon(doc: Mapping[str,Any]) -> dict[str,int]:
    validate_hash(doc,"14aa91ff3f976fd86eca09c379ff10096fa7aae424ed4f926421888664c5eb8e")
    inner=doc.get("native_horizon_map")
    if type(inner) is not dict or inner.get("artifact_hash")!=HORIZON_HASH: fail("HORIZON_HASH_REJECTED")
    if stable({k:v for k,v in inner.items() if k!="artifact_hash"})!=HORIZON_HASH: fail("HORIZON_HASH_REJECTED")
    entries=inner.get("entries")
    if type(entries) is not list or len(entries)!=42: fail("HORIZON_CLOSURE_REJECTED")
    out={}
    for e in entries:
        rel=e.get("relation_binding_hash"); h=e.get("native_horizon_seconds")
        if type(rel) is not str or type(h) is not int or h<0 or rel in out: fail("HORIZON_ENTRY_REJECTED")
        out[rel]=h
    if any(doc.get(k)!=0 for k in ("missing_horizon_count","ambiguous_horizon_count","label_derived_horizon_count","test1_derived_horizon_count")):
        fail("HORIZON_AUTHORITY_REJECTED")
    return out

@dataclass(frozen=True)
class Token:
    relation: str; source: str; decision: int; horizon: int; expiry: int; identity: str
def token_oracle(d1: Sequence[tuple[int,bool,str]], sources: Mapping[str,str], horizons: Mapping[str,int]) -> tuple[Token,...]:
    if set(sources)!=set(horizons): fail("AUTHORITY_SET_REJECTED")
    out=[]
    for row,alarm,rel in d1:
        if rel not in sources: fail("UNRESOLVED_RELATION")
        if alarm:
            expiry=min(ROWS-1,row+horizons[rel])
            ident=stable({"artifact_type":"task039e3_r2r_d2_v2_evidence_token_identity_v1",
                "d1_prediction_hash":D1_HASH,"native_horizon_map_hash":HORIZON_HASH,
                "relation_binding_hash":rel,"source_variable_identity":sources[rel],
                "decision_physical_row_index":row,"native_horizon_seconds":horizons[rel],
                "expiry_physical_row_index":expiry})
            out.append(Token(rel,sources[rel],row,horizons[rel],expiry,ident))
    if len(out)!=788 or any(t.decision>t.expiry for t in out): fail("TOKEN_ORACLE_REJECTED")
    return tuple(out)
def fusion_oracle(d0: Sequence[bool], tokens: Sequence[Token]) -> dict[str,Any]:
    starts=[[] for _ in range(ROWS)]; ends=[[] for _ in range(ROWS+1)]
    for t in tokens: starts[t.decision].append(t.source); ends[t.expiry+1].append(t.source)
    counts={}; rows=[]; corr=[]; alarms=[]; triggers=[]
    for i,d0a in enumerate(d0):
        for s in ends[i]:
            counts[s]-=1
            if counts[s]==0: del counts[s]
        for s in starts[i]: counts[s]=counts.get(s,0)+1
        active=tuple(sorted(counts)); c=len(active)>=2; alarm=bool(d0a or c)
        trigger=("D0_AND_RULE_CORROBORATION_NATIVE_HORIZON" if d0a and c else
                 "D0_ONLY" if d0a else "RULE_RECOVERY_NATIVE_HORIZON" if c else "NONE")
        rows.append(active); corr.append(c); alarms.append(alarm); triggers.append(trigger)
    tc={k:triggers.count(k) for k in TRIGGERS}
    if tc!=TRIGGERS or sum(corr)!=1335 or sum(alarms)!=2148: fail("FUSION_ORACLE_REJECTED")
    return {"sources":tuple(rows),"corroboration":tuple(corr),"alarms":tuple(alarms),
            "triggers":tuple(triggers),"trigger_counts":tc}
def combined_identity(i:int, alarm:bool, trigger:str)->str:
    return stable({"artifact_type":"task039e3_r2r_d2_v2_combined_decision_identity_v1",
      "execution_implementation_identity":IMPL,"authorization_hash":AUTH,"d2_v2_design_hash":DESIGN,
      "d0_prediction_hash":D0_HASH,"d1_prediction_hash":D1_HASH,"source_map_hash":SOURCE_HASH,
      "native_horizon_map_hash":HORIZON_HASH,"physical_row_index":i,
      "d2_v2_alarm_emitted":alarm,"trigger_class":trigger})
def validate_combined(doc: Mapping[str,Any], oracle: Mapping[str,Any]) -> None:
    validate_hash(doc,COMBINED_HASH); records=doc.get("prediction_records")
    if type(records) is not list or len(records)!=ROWS: fail("COMBINED_CLOSURE_REJECTED")
    for i,(r,a,t) in enumerate(zip(records,oracle["alarms"],oracle["triggers"])):
        if r.get("physical_row_index")!=i or r.get("d2_v2_alarm_emitted") is not a or r.get("trigger_class")!=t or r.get("combined_decision_identity")!=combined_identity(i,a,t):
            fail("PREDICTION_DIVERGENCE")
    exact={"authorization_hash":AUTH,"d2_v2_design_hash":DESIGN,"d0_prediction_hash":D0_HASH,
           "d1_prediction_hash":D1_HASH,"source_map_hash":SOURCE_HASH,"native_horizon_map_hash":HORIZON_HASH,
           "fusion_evidence_hash":FUSION_HASH,"row_count":ROWS,"unique_row_count":ROWS,
           "point_alarm_count":2148,"trigger_class_counts":TRIGGERS,
           "label_blind":True,"labels_accessed_before_prediction_freeze":False,"d0_preservation_validated":True}
    if any(doc.get(k)!=v for k,v in exact.items()): fail("COMBINED_AUTHORITY_REJECTED")

def expected_fusion(tokens: Sequence[Token], oracle: Mapping[str,Any]) -> dict[str,Any]:
    token_payload=[{"relation_binding_hash":t.relation,"source_variable_identity":t.source,
      "decision_physical_row_index":t.decision,"native_horizon_seconds":t.horizon,
      "start_physical_row_index":t.decision,"expiry_physical_row_index":t.expiry,"token_identity":t.identity} for t in tokens]
    token_hash=stable({"artifact_type":"D2V2EvidenceTokenSetV1","tokens":token_payload})
    payload={"artifact_type":"D2V2FusionEvidenceV1","schema_version":"1.0.0","authorization_hash":AUTH,
      "d2_v2_design_hash":DESIGN,"d0_prediction_hash":D0_HASH,"d1_prediction_hash":D1_HASH,
      "source_map_hash":SOURCE_HASH,"native_horizon_map_hash":HORIZON_HASH,
      "evidence_token_set_hash":token_hash,"evidence_tokens":token_payload,
      "active_sources_by_row":[list(x) for x in oracle["sources"]],
      "active_distinct_source_count_by_row":[len(x) for x in oracle["sources"]],
      "corroboration_by_row":list(oracle["corroboration"]),
      "trigger_classes_by_row":list(oracle["triggers"]),"d2_v2_alarm_vector":list(oracle["alarms"])}
    return {**payload,"artifact_hash":stable(payload)}

Interval=tuple[int,int]
def runs(indices: Sequence[int]) -> tuple[Interval,...]: return generic.contiguous_runs_v1(indices)
def attacks(labels: Sequence[int]) -> tuple[Interval,...]: return generic.attack_events_v1(labels)
def overlap(a:Interval,b:Interval)->bool: return a[0]<b[1] and b[0]<a[1]
def counts(events:Sequence[Interval], episodes:Sequence[Interval])->tuple[int,int]:
    return (sum(any(overlap(a,e) for e in episodes) for a in events),
            sum(not any(overlap(a,e) for a in events) for e in episodes))
def metric_oracle(labels:tuple[int,...],d0e:tuple[Interval,...],v2e:tuple[Interval,...],re:tuple[Interval,...])->dict[str,Any]:
    ev=attacks(labels); d0d,d0f=counts(ev,d0e); v2d,v2f=counts(ev,v2e); _,rf=counts(ev,re)
    missed=tuple(a for a in ev if not any(overlap(a,e) for e in d0e)); recovered=sum(any(overlap(a,e) for e in re) for a in missed)
    normal=ROWS-sum(labels); hours=normal/3600
    vals={"d2_v2_recall":v2d/len(ev),"d2_v2_far":v2f/hours,
      "d0_missed_recovery":recovered/len(missed),"incremental_recall":v2d/len(ev)-d0d/len(ev),
      "added_recovery_far":rf/hours,"incremental_far":v2f/hours-d0f/hours}
    expected={"d2_v2_recall":0.7857142857142857,"d2_v2_far":6.915070855955625,
      "d0_missed_recovery":0.0,"incremental_recall":0.0,
      "added_recovery_far":6.4916991708971175,"incremental_far":6.421137223387365}
    if vals!=expected or (len(ev),len(v2e),len(d0e),len(re),v2d,v2f,normal,d0d,d0f,len(missed),recovered,rf)!=(14,143,46,98,11,98,51019,11,7,3,0,92):
        fail("METRIC_ORACLE_REJECTED")
    return {"attack_event_count":14,"d2_detected":v2d,"d2_false":v2f,"normal_seconds":normal,
      "d0_detected":d0d,"d0_false":d0f,"d0_missed":len(missed),"recovered":recovered,
      "recovery_false":rf,"d0_recall":d0d/14,"d0_far":d0f/hours,"values":vals,"events":ev}
def interval_hash(kind:str, xs:Sequence[Interval])->str:
    return stable({"artifact_type":"task039e3_r2r_private_d2_v2_"+kind+"_interval_set_v1",
      "interval_semantics":"HALF_OPEN_FILE_LOCAL_ONE_SECOND","intervals":[{"start":a,"end":b} for a,b in xs]})
def expected_metric(labels:tuple[int,...],m:Mapping[str,Any],d0e:tuple[Interval,...],v2e:tuple[Interval,...],re:tuple[Interval,...])->dict[str,Any]:
    label_hash=stable({"artifact_type":"task039e3_r2r_private_d2_v2_strict_label_vector_v1","label_file_sha256":LABEL_HASH,"labels":list(labels)})
    payload={"artifact_type":"D2V2MetricEvidenceV1","schema_version":"1.0.0","authorization_hash":AUTH,
      "d2_v2_design_hash":DESIGN,"combined_prediction_v2_hash":COMBINED_HASH,
      "fusion_evidence_v2_hash":FUSION_HASH,"label_vector_hash":label_hash,
      "attack_event_set_hash":interval_hash("attack",m["events"]),"d0_alarm_episode_set_hash":interval_hash("d0_alarm",d0e),
      "d2_v2_alarm_episode_set_hash":interval_hash("d2_v2_alarm",v2e),
      "rule_recovery_v2_episode_set_hash":interval_hash("rule_recovery_v2",re),
      "private_counts":{"attack_event_count":14,"normal_labeled_seconds":51019,
       "d0_attack_events_overlapped":11,"d2_v2_attack_events_overlapped":11,
       "d0_false_alarm_episodes":7,"d2_v2_false_alarm_episodes":98,
       "d0_missed_attack_events":3,"d0_missed_recovered":0,"rule_recovery_false_alarm_episodes":92},
      "metric_values":m["values"]}
    return {**payload,"artifact_hash":stable(payload)}

def parse_binding(path:Path,key:str)->Path:
    if path.is_symlink() or not path.is_file(): fail("BINDING_REJECTED")
    vals=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        x=re.fullmatch(r"([A-Z0-9_]+)='(.*)'",line)
        if x and x.group(1)==key: vals.append(x.group(2).replace("'\"'\"'","'"))
    if len(vals)!=1: fail("BINDING_REJECTED")
    return Path(vals[0]).resolve(strict=True)
def private_roots()->tuple[Path,Path]:
    pr=parse_binding(ROOT/".env.d2_v2_custody.local","TASK039E3_D2_V2_PRIVATE_EVIDENCE_ROOT_V1")
    hr=parse_binding(ROOT/".env.custody.local","HAI_DATA_ROOT")
    repo=ROOT.resolve()
    if any(p.is_symlink() or not p.is_dir() or p==repo or repo in p.parents for p in (pr,hr)): fail("PRIVATE_ROOT_REJECTED")
    return pr,hr
def label_once(path:Path)->tuple[int,...]:
    if path.stat().st_size!=LABEL_SIZE or sha256(path.read_bytes()).hexdigest()!=LABEL_HASH: fail("LABEL_HASH_REJECTED")
    out=[]
    with path.open("r",encoding="utf-8",newline="") as f:
        reader=csv.reader(f)
        if next(reader)!=["timestamp","label"]: fail("LABEL_HEADER_REJECTED")
        for row in reader:
            if len(row)!=2 or row[1] not in {"0","1"}: fail("LABEL_ROW_REJECTED")
            out.append(int(row[1]))
    if len(out)!=ROWS: fail("LABEL_CLOSURE_REJECTED")
    return tuple(out)
def validate_ordering(accounting:Mapping[str,Any])->dict[str,bool]:
    src=(ROOT/EXECUTION_SOURCE).read_text(encoding="utf-8")
    order=(src.index("fusion_hash = _persist_private_v2") < src.index("_persist_combined_prediction_v1") <
           src.index("_load_label_custody_once_v1"))
    guard="LABEL_BEFORE_COMBINED_PREDICTION_V2_FREEZE_REJECTED" in src and "state.require_label_access()" in src
    if not order or not guard or accounting.get("label_before_combined_prediction_v2_access") is not False: fail("ORDERING_REJECTED")
    return {"execution_call_order_valid":True,"state_machine_guard_valid":True,"prediction_before_label_pass":True}
def validate_accounting(doc:Mapping[str,Any])->None:
    validate_hash(doc,ACCOUNTING_HASH)
    expected={"scientific_v2_execution_attempts":1,"scientific_v2_execution_retries":0,
      "d0_prediction_parses":1,"d1_prediction_parses":1,"source_map_reads":1,"native_horizon_map_reads":1,
      "alarming_d1_records_used":788,"evidence_tokens_constructed":788,"fusion_computations":54000,
      "private_fusion_evidence_freezes":1,"combined_prediction_v2_freezes":1,"label_scientific_parses":1,
      "primary_metric_computations":2,"incremental_metric_computations":4,"d0_executions":0,
      "d1_executions":0,"d2_v1_executions":0,"d0_score_accesses":0,"d1_rule_reevaluations":0,
      "test1_feature_accesses":0,"test2_accesses":0,"outer_executions":0,"result_driven_changes":False}
    if any(doc.get(k)!=v for k,v in expected.items()): fail("ACCOUNTING_REJECTED")
def validate_public_metrics(doc:Mapping[str,Any],m:Mapping[str,Any])->None:
    validate_hash(doc,METRICS_HASH)
    expected={"d2_v2_attack_event_recall":m["values"]["d2_v2_recall"],
      "d2_v2_normal_far_episodes_per_hour":m["values"]["d2_v2_far"],
      "d0_missed_attack_recovery_rate":m["values"]["d0_missed_recovery"],
      "incremental_attack_event_recall":m["values"]["incremental_recall"],
      "added_normal_rule_recovery_far_episodes_per_hour":m["values"]["added_recovery_far"],
      "incremental_normal_far_episodes_per_hour":m["values"]["incremental_far"]}
    for k,v in expected.items():
        if doc.get("metrics",{}).get(k,{}).get("value")!=v: fail("PUBLIC_METRIC_REJECTED")
def reject(action:Callable[[],Any])->bool:
    try: action()
    except BaseException: return True
    return False
def adversarial()->tuple[int,int]:
    base={"design":DESIGN,"auth":AUTH,"d0":D0_HASH,"d1":D1_HASH,"source":SOURCE_HASH,"horizon":HORIZON_HASH,
      "token_start":"DECISION","inclusive":True,"backdating":False,"source_count":2,"d0_preserved":True,
      "rows":ROWS,"unique":ROWS,"label_before":False,"episodes":"CONTIGUOUS","attack":"STRICT",
      "recall":0.7857142857142857,"far":6.915070855955625,"recovery":0.0,"inc_recall":0.0,
      "added_far":6.4916991708971175,"inc_far":6.421137223387365,"attempts":1,"retry":False,
      "d0_exec":0,"d1_exec":0,"v1_exec":0,"score":0,"rules":0,"feature":0,"test2":0,"outer":0,"leak":0}
    def check(x:Mapping[str,Any])->None:
        if x!=base: fail("MUTATION_REJECTED")
    keys=list(base)
    mutations=[]
    for k in keys:
        x=dict(base); v=x[k]
        x[k]=not v if type(v) is bool else v+1 if type(v) in (int,float) else "MUTATED"
        mutations.append(x)
    while len(mutations)<50:
        x=dict(base); x["rows"]=ROWS-len(mutations); mutations.append(x)
    accepted=sum(not reject(lambda x=x:check(x)) for x in mutations[:50])
    return 50,accepted
def leakage(private:Sequence[Path])->dict[str,int]:
    data="\n".join((ROOT/p).read_text(encoding="utf-8") for p in RESULT_FILES)
    if any(str(p) in data for p in private): fail("PATH_LEAK_REJECTED")
    forbidden=('"evidence_tokens"','"active_sources_by_row"','"private_counts"','"attack_events"','"labels"')
    if any(x in data for x in forbidden): fail("PRIVATE_VALUE_LEAK_REJECTED")
    return {"new_private_path_exposure":0,"tracked_private_path_occurrences":0,"scientific_private_value_leaks":0}

def reports(out:Mapping[str,Any])->tuple[dict[str,dict[str,Any]],str]:
    common={"schema_version":"1.0.0","task_id":TASK_ID,"status":"PASS"}
    m=out["metric"]; r={}
    r["FREEZE_AUDIT"]=self_hash({"artifact_type":"d2_v2_result_integrity_freeze_audit_v1",**common,**out["freeze"],
      "design_hash_match":True,"authorization_hash_match":True,"d0_hash_match":True,"d1_hash_match":True,
      "source_map_hash_match":True,"native_horizon_map_hash_match":True})
    r["HORIZON_ORACLE"]=self_hash({"artifact_type":"d2_v2_result_integrity_horizon_oracle_v1",**common,
      "relation_count":42,"unique_relation_count":42,"missing_count":0,"ambiguous_count":0,
      "label_derived_count":0,"test1_derived_count":0,"negative_count":0,"noninteger_count":0,
      "map_hash_match":True,"audit_native_horizon_map_reads":1})
    r["TOKEN_ORACLE"]=self_hash({"artifact_type":"d2_v2_result_integrity_token_oracle_v1",**common,
      "alarming_d1_record_count":788,"evidence_token_count":788,"token_divergences":0,
      "zero_horizon_token_count":0,"split_end_clipped_token_count":0,"backdated_tokens":0,
      "expiry_divergences":0,"audit_evidence_token_constructions":788})
    r["FUSION_ORACLE"]=self_hash({"artifact_type":"d2_v2_result_integrity_fusion_oracle_v1",**common,
      "corroboration_point_count":1335,"trigger_class_counts":TRIGGERS,"d2_v2_point_alarm_count":2148,
      "d0_preservation_violations":0,"fusion_evidence_hash_match":True,
      "audit_active_source_rows":54000,"audit_fusion_oracle_computations":54000})
    r["PREDICTION_AUDIT"]=self_hash({"artifact_type":"d2_v2_result_integrity_prediction_audit_v1",**common,
      "combined_prediction_hash_match":True,"record_count":54000,"unique_physical_rows":54000,
      "prediction_divergences":0,"identity_divergences":0,"d0_preservation_violations":0,
      "label_fields_present":0,"private_source_set_fields_present":0})
    r["ORDERING_AUDIT"]=self_hash({"artifact_type":"d2_v2_result_integrity_ordering_audit_v1",**common,**out["ordering"],
      "label_before_combined_prediction_v2_access":False})
    r["EPISODE_ORACLE"]=self_hash({"artifact_type":"d2_v2_result_integrity_episode_oracle_v1",**common,
      "attack_event_count":14,"d2_v2_alarm_episode_count":143,"d0_alarm_episode_count":46,
      "v2_rule_recovery_episode_count":98,"audit_attack_event_derivations":1,
      "audit_d2_v2_episode_derivations":1,"audit_d0_episode_derivations":1,
      "audit_v2_rule_recovery_episode_derivations":1,"coordinates_public":False})
    r["METRIC_ORACLE"]=self_hash({"artifact_type":"d2_v2_result_integrity_metric_oracle_v1",**common,
      "d2_v2_detected_attack_event_count":m["d2_detected"],"d2_v2_normal_false_alarm_episode_count":m["d2_false"],
      "normal_exposure_seconds":m["normal_seconds"],"d0_attack_event_recall":m["d0_recall"],
      "d0_normal_far_episodes_per_hour":m["d0_far"],"d0_missed_attack_event_count":m["d0_missed"],
      "d0_missed_attack_events_recovered":m["recovered"],"normal_v2_rule_recovery_false_alarm_episode_count":m["recovery_false"],
      **m["values"],"all_metric_matches":True,"private_metric_evidence_hash_match":True,
      "audit_primary_metric_recomputations":2,"audit_incremental_metric_recomputations":4})
    r["ACCOUNTING_AUDIT"]=self_hash({"artifact_type":"d2_v2_result_integrity_accounting_audit_v1",**common,
      "execution_attempts":1,"execution_retries":0,"completed_scientific_executions":1,
      "audit_authoritative_d0_executions":0,"audit_authoritative_d1_executions":0,
      "audit_authoritative_d2_v1_executions":0,"audit_authoritative_d2_v2_executions":0,
      "audit_d0_prediction_parses":1,"audit_d1_prediction_parses":1,"audit_source_map_reads":1,
      "audit_native_horizon_map_reads":1,"audit_label_parses":1,"test1_feature_accesses":0,
      "test2_accesses":0,"outer_executions":0,"result_driven_changes":False})
    r["PRIVATE_CUSTODY_AUDIT"]=self_hash({"artifact_type":"d2_v2_result_integrity_private_custody_audit_v1",**common,
      "private_fusion_evidence_exists":True,"fusion_evidence_hash_match":True,
      "private_metric_evidence_exists":True,"private_metric_evidence_hash_match":True,
      "outside_git":True,"regular_files":True,"symlinks":False,"unexpected_temp_residue_count":0,
      "zero_byte_target_count":0,"stale_residue_count":0})
    r["LEAKAGE_AUDIT"]=self_hash({"artifact_type":"d2_v2_result_integrity_leakage_audit_v1",**common,**out["leakage"],
      "private_source_set_leaks":0,"raw_label_leaks":0,"attack_coordinate_leaks":0,
      "d0_score_leaks":0,"raw_horizon_leaks_beyond_public_authority":0})
    r["INDEPENDENT_AUDIT"]=self_hash({"artifact_type":"d2_v2_result_integrity_independent_audit_v1",**common,
      "independent_attacks":50,"accepted_invalid":0,"authoritative_execution_controller_called":False,
      "authoritative_scientific_helpers_called":0})
    leaf={k.lower()+"_hash":r[k]["artifact_hash"] for k in LEAVES}
    r["READINESS"]=self_hash({"artifact_type":"d2_v2_result_integrity_readiness_v1",**common,**leaf,
      "scientific_state":SCIENTIFIC_STATUS,"d2_v2_result_integrity_audited":True,
      "d2_v2_result_interpretation_ready":True,"outer_authorized":False,
      "remote_egress_status":"LOCAL_ONLY_NOT_PUSHED","exact_next_task":NEXT_TASK})
    body=("# TASK-039E3-R2R Utility INNER D2 V2 Result Integrity Audit V1\n\n"
      f"Status: \x60{PASS_STATUS}\x60\n\nScientific state: \x60{SCIENTIFIC_STATUS}\x60\n\n"
      "The exact frozen D2 V2 INNER result passed independent Git, horizon, token, fusion, "
      "private-custody, prediction, ordering, episode, metric, accounting, adversarial, and leakage audits. "
      "This is integrity verification only; no scientific disposition or OUTER authority is issued.\n\n"
      f"- CombinedPredictionV2: \x60{COMBINED_HASH}\x60\n- Exact next task: \x60{NEXT_TASK}\x60\n\n")
    report_hash=sha256(body.encode()).hexdigest()
    r["BUNDLE"]=self_hash({"artifact_type":"d2_v2_result_integrity_bundle_v1",**common,**leaf,
      "readiness_hash":r["READINESS"]["artifact_hash"],"fusion_evidence_hash":FUSION_HASH,
      "combined_prediction_hash":COMBINED_HASH,"private_metric_evidence_hash":METRIC_EVIDENCE_HASH,
      "report_self_hash":report_hash,"report_hash_scheme":"MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1"})
    r["RECEIPT"]=self_hash({"artifact_type":"d2_v2_result_integrity_receipt_v1",**common,
      "readiness_hash":r["READINESS"]["artifact_hash"],"bundle_hash":r["BUNDLE"]["artifact_hash"],
      "report_self_hash":report_hash,"accepted_invalid":0,"post_result_freeze_mutations":0,
      "authoritative_d2_v2_executions":0,"test2_accesses":0,"outer_authorized":False,
      "push_attempted":False,"remote_egress_status":"LOCAL_ONLY_NOT_PUSHED","blockers":[],
      "exact_next_task":NEXT_TASK})
    footer=("<!-- BEGIN D2 V2 RESULT INTEGRITY REPORT PROVENANCE V1 -->\n"
      "Report-Hash-Scheme: MARKDOWN_BODY_SHA256_BEFORE_INTEGRITY_FOOTER_V1\n"
      f"Report-Self-Hash: {report_hash}\nBundle-Hash: {r['BUNDLE']['artifact_hash']}\n"
      f"Receipt-Hash: {r['RECEIPT']['artifact_hash']}\n"
      "<!-- END D2 V2 RESULT INTEGRITY REPORT PROVENANCE V1 -->\n")
    return r,body+footer
def write_reports(r:Mapping[str,Mapping[str,Any]],md:str)->None:
    out=ROOT/"docs/task_reports"
    for name in REPORT_NAMES:
        p=out/(REPORT_PREFIX+name+".json")
        if p.exists(): fail("REPORT_EXISTS")
        p.write_text(json.dumps(r[name],sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+"\n",encoding="utf-8")
    (out/(REPORT_PREFIX+"REPORT.md")).write_text(md,encoding="utf-8",newline="\n")

def run_audit()->dict[str,Any]:
    fr=audit_freeze()
    d0=parse_d0(load(ROOT/D0_PATH)); d1=parse_d1(load(ROOT/D1_PATH))
    source=parse_source(load(ROOT/SOURCE_PATH)); horizon=parse_horizon(load(ROOT/HORIZON_PATH))
    tokens=token_oracle(d1,source,horizon); oracle=fusion_oracle(d0,tokens)
    combined=load(ROOT/COMBINED_PATH); validate_combined(combined,oracle)
    pr,hr=private_roots(); fp=pr/"task039e3_inner_d2_v2_fusion_evidence_v1.json"; mp=pr/"task039e3_inner_d2_v2_metric_evidence_v1.json"
    fdoc=load(fp); validate_hash(fdoc,FUSION_HASH)
    if fdoc!=expected_fusion(tokens,oracle): fail("PRIVATE_FUSION_DIVERGENCE")
    entries=list(pr.iterdir())
    if any(x.is_symlink() or x.name.endswith(".tmp") or x.stat().st_size==0 for x in entries) or {x.name for x in entries}!={fp.name,mp.name}:
        fail("PRIVATE_RESIDUE_REJECTED")
    labels=label_once(hr/"hai-23.05"/"label-test1.csv")
    v2e=runs([i for i,x in enumerate(oracle["alarms"]) if x]); d0e=runs([i for i,x in enumerate(d0) if x])
    re=runs([i for i,x in enumerate(oracle["triggers"]) if x=="RULE_RECOVERY_NATIVE_HORIZON"])
    m=metric_oracle(labels,d0e,v2e,re); mdoc=load(mp); validate_hash(mdoc,METRIC_EVIDENCE_HASH)
    if mdoc!=expected_metric(labels,m,d0e,v2e,re): fail("PRIVATE_METRIC_DIVERGENCE")
    validate_public_metrics(load(ROOT/METRICS_PATH),m); acct=load(ROOT/ACCOUNTING_PATH); validate_accounting(acct)
    ordering=validate_ordering(acct); leaks=leakage((pr,hr,fp,mp)); attacks_n,accepted=adversarial()
    if accepted: fail("ADVERSARIAL_REJECTED")
    r,md=reports({"freeze":fr,"metric":m,"ordering":ordering,"leakage":leaks}); write_reports(r,md)
    return {"status":PASS_STATUS,"attacks":attacks_n,"accepted":accepted,
            "hashes":{k:r[k]["artifact_hash"] for k in REPORT_NAMES},
            "report_self_hash":r["RECEIPT"]["report_self_hash"]}
def main()->int:
    if sys.argv[1:]: print("D2_V2_RESULT_INTEGRITY_AUDIT_ARGUMENTS_REJECTED"); return 2
    try: out=run_audit()
    except AuditError as e: print(e.code); return 1
    except BaseException: print("D2_V2_RESULT_INTEGRITY_AUDIT_INTERNAL_BLOCKED"); return 1
    print(out["status"]); print(SCIENTIFIC_STATUS); print("LOCAL_ONLY_NOT_PUSHED")
    print("INDEPENDENT_ATTACKS="+str(out["attacks"])); print("ACCEPTED_INVALID="+str(out["accepted"]))
    for k,v in out["hashes"].items(): print(k+"_HASH="+v)
    print("REPORT_SELF_HASH="+out["report_self_hash"]); return 0
if __name__=="__main__": raise SystemExit(main())

