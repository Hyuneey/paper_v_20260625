"""Prospectively frozen, version-separated multi-panel metric arithmetic."""
from __future__ import annotations
from dataclasses import dataclass
from math import comb, sqrt
from statistics import median
from typing import Iterable, Mapping, Sequence


class MultiPanelMetricError(ValueError): pass


@dataclass(frozen=True, order=True)
class EligibleScenarioIntervalV1:
    """One official, independently P1-eligible, closed scenario interval."""

    dataset_version: str
    file_id: str
    scenario_id: str
    start: int
    end: int
    scenario_authority_hash: str
    eligibility_authority_hash: str

    def validate(self) -> None:
        if any(not isinstance(value,str) or not value for value in (self.dataset_version,self.file_id,self.scenario_id)):
            raise MultiPanelMetricError("invalid official scenario identity")
        if type(self.start) is not int or type(self.end) is not int or not 0 <= self.start <= self.end:
            raise MultiPanelMetricError("invalid official scenario interval")
        for value in (self.scenario_authority_hash,self.eligibility_authority_hash):
            if len(value)!=64 or any(ch not in '0123456789abcdef' for ch in value):
                raise MultiPanelMetricError("invalid scenario or eligibility authority hash")

    @property
    def identity(self) -> tuple[str,str,str]:
        return self.dataset_version,self.file_id,self.scenario_id


@dataclass(frozen=True, order=True)
class ScenarioHitV1:
    dataset_version: str
    file_id: str
    scenario_id: str
    hit: bool
    scenario_authority_hash: str
    eligibility_authority_hash: str

    def validate(self) -> None:
        if any(not isinstance(value,str) or not value for value in (self.dataset_version,self.file_id,self.scenario_id)):
            raise MultiPanelMetricError("invalid scenario hit identity")
        if type(self.hit) is not bool:
            raise MultiPanelMetricError("strict Boolean scenario hit required")
        for value in (self.scenario_authority_hash,self.eligibility_authority_hash):
            if len(value)!=64 or any(ch not in '0123456789abcdef' for ch in value):
                raise MultiPanelMetricError("invalid scenario or eligibility authority hash")

    @property
    def identity(self) -> tuple[str,str,str]:
        return self.dataset_version,self.file_id,self.scenario_id


def scenario_recall_v1(hits: Sequence[bool]) -> Mapping[str, object]:
    if not hits: return {"status":"NOT_EVALUABLE","hits":0,"eligible":0,"recall":None}
    if any(type(value) is not bool for value in hits): raise MultiPanelMetricError("strict Boolean hits required")
    count=sum(hits)
    return {"status":"PASS","hits":count,"eligible":len(hits),"recall":count/len(hits)}


def official_scenario_hits_v1(
    scenarios: Sequence[EligibleScenarioIntervalV1],
    alarm_rows_by_file: Mapping[tuple[str,str],Sequence[int]],
) -> tuple[ScenarioHitV1,...]:
    """Bind alarms to official scenarios by same-version, same-file overlap."""
    if not scenarios:
        return ()
    for scenario in scenarios:
        if type(scenario) is not EligibleScenarioIntervalV1:
            raise MultiPanelMetricError("official eligible scenario authority required")
        scenario.validate()
    identities=[item.identity for item in scenarios]
    if len(set(identities)) != len(identities):
        raise MultiPanelMetricError("duplicate official scenario identity")
    versions={item.dataset_version for item in scenarios}
    if len(versions) != 1:
        raise MultiPanelMetricError("cross-version scenario pooling prohibited")
    required_files={(item.dataset_version,item.file_id) for item in scenarios}
    if set(alarm_rows_by_file) != required_files:
        raise MultiPanelMetricError("scenario alarm file authority mismatch")
    normalized:dict[tuple[str,str],tuple[int,...]]={}
    for key,rows in alarm_rows_by_file.items():
        if not isinstance(key,tuple) or len(key)!=2 or any(not isinstance(v,str) or not v for v in key):
            raise MultiPanelMetricError("invalid version-bound file identity")
        values=tuple(rows)
        if any(type(value) is not int or value < 0 for value in values) or tuple(sorted(set(values))) != values:
            raise MultiPanelMetricError("alarm rows must be unique sorted nonnegative integers")
        normalized[key]=values
    return tuple(
        ScenarioHitV1(item.dataset_version,item.file_id,item.scenario_id,
            any(item.start <= row <= item.end for row in normalized[(item.dataset_version,item.file_id)]),
            item.scenario_authority_hash,item.eligibility_authority_hash)
        for item in sorted(scenarios,key=lambda value:value.identity)
    )


def official_scenario_recall_v1(
    scenarios: Sequence[EligibleScenarioIntervalV1],
    alarm_rows_by_file: Mapping[tuple[str,str],Sequence[int]],
) -> Mapping[str,object]:
    rows=official_scenario_hits_v1(scenarios,alarm_rows_by_file)
    result=dict(scenario_recall_v1(tuple(item.hit for item in rows)))
    result["scenario_hits"]=[{"dataset_version":item.dataset_version,"file_id":item.file_id,
        "scenario_id":item.scenario_id,"hit":item.hit,"scenario_authority_hash":item.scenario_authority_hash,
        "eligibility_authority_hash":item.eligibility_authority_hash} for item in rows]
    result["alignment"]="SAME_DATASET_VERSION_AND_PHYSICAL_FILE_CLOSED_INTERVAL_OVERLAP"
    return result


def wilson95_v1(hits: int, total: int) -> tuple[float,float] | None:
    if type(hits) is not int or type(total) is not int or not 0 <= hits <= total: raise MultiPanelMetricError("invalid Wilson counts")
    if total==0:return None
    z=1.959963984540054; p=hits/total; d=1+z*z/total
    c=(p+z*z/(2*total))/d; h=z*sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return max(0.0,c-h),min(1.0,c+h)


def detection_delay_v1(start: int, alarm_times: Sequence[int], end: int) -> int | None:
    if type(start) is not int or type(end) is not int or not 0<=start<=end: raise MultiPanelMetricError("invalid scenario interval")
    if any(type(value) is not int or value < 0 for value in alarm_times): raise MultiPanelMetricError("invalid alarm timestamp")
    inside=[value for value in alarm_times if start<=value<=end]
    return None if not inside else min(inside)-start


def summarize_delays_v1(delays: Sequence[int | None]) -> Mapping[str,object]:
    if any(value is not None and (type(value) is not int or value < 0) for value in delays):
        raise MultiPanelMetricError("invalid detection delay")
    detected=sorted(value for value in delays if value is not None)
    if not detected:return {"detected":0,"not_detected":len(delays),"median":None,"iqr":None,"individual":list(delays)}
    def quantile(frac: float) -> float:
        position=(len(detected)-1)*frac; lo=int(position); hi=min(lo+1,len(detected)-1); w=position-lo
        return detected[lo]*(1-w)+detected[hi]*w
    return {"detected":len(detected),"not_detected":len(delays)-len(detected),"median":median(detected),
            "iqr":quantile(.75)-quantile(.25),"individual":["NOT_DETECTED" if x is None else x for x in delays]}


def false_burden_v1(alarms_by_file: Mapping[str,Sequence[bool]], exposure_seconds_by_file: Mapping[str,int]) -> Mapping[str,object]:
    if set(alarms_by_file)!=set(exposure_seconds_by_file) or not alarms_by_file: raise MultiPanelMetricError("file authority mismatch")
    seconds=episodes=exposure=0
    components=[]
    for file_id in sorted(alarms_by_file):
        stream=tuple(alarms_by_file[file_id]); exp=exposure_seconds_by_file[file_id]
        if type(exp) is not int or exp<=0 or len(stream)!=exp: raise MultiPanelMetricError("INVALID_AUTHORITY")
        if any(type(v) is not bool for v in stream): raise MultiPanelMetricError("strict Boolean alarms required")
        fs=sum(stream); fe=sum(value and (index==0 or not stream[index-1]) for index,value in enumerate(stream))
        seconds+=fs;episodes+=fe;exposure+=exp;components.append({"file_id":file_id,"exposure_seconds":exp,"false_seconds":fs,"false_episodes":fe})
    hours=exposure/3600
    return {"status":"PASS","false_seconds_per_hour":seconds/hours,"false_episodes_per_hour":episodes/hours,
            "false_seconds":seconds,"false_episodes":episodes,"exposure_seconds":exposure,"components":components}


def paired_scenario_table_v1(a: Sequence[bool], b: Sequence[bool]) -> Mapping[str,object]:
    if len(a)!=len(b) or any(type(v) is not bool for v in (*a,*b)): raise MultiPanelMetricError("paired scenario alignment mismatch")
    if not a:return {"status":"NOT_EVALUABLE","both_hit":0,"a_only":0,"b_only":0,"neither":0,"hit_difference":0}
    return {"status":"PASS","both_hit":sum(x and y for x,y in zip(a,b)),"a_only":sum(x and not y for x,y in zip(a,b)),
            "b_only":sum(not x and y for x,y in zip(a,b)),"neither":sum(not x and not y for x,y in zip(a,b)),
            "hit_difference":sum(a)-sum(b)}


def paired_official_scenario_table_v1(a: Sequence[ScenarioHitV1],b: Sequence[ScenarioHitV1]) -> Mapping[str,object]:
    """Create a paired table only after exact composite-authority alignment."""
    for row in (*a,*b):
        if type(row) is not ScenarioHitV1: raise MultiPanelMetricError("scenario hit authority required")
        row.validate()
    left={row.identity:(row.hit,row.scenario_authority_hash,row.eligibility_authority_hash) for row in a}
    right={row.identity:(row.hit,row.scenario_authority_hash,row.eligibility_authority_hash) for row in b}
    if len(left)!=len(a) or len(right)!=len(b) or set(left)!=set(right):
        raise MultiPanelMetricError("paired official scenario identity mismatch")
    if any(left[key][1:]!=right[key][1:] for key in left):
        raise MultiPanelMetricError("paired scenario authority mismatch")
    if len({identity[0] for identity in left})>1:
        raise MultiPanelMetricError("cross-version paired table prohibited")
    ordered=sorted(left)
    result=dict(paired_scenario_table_v1(tuple(left[key][0] for key in ordered),tuple(right[key][0] for key in ordered)))
    result["aligned_scenario_count"]=len(ordered)
    return result


def assert_single_version_records_v1(records:Sequence[EligibleScenarioIntervalV1|ScenarioHitV1])->str:
    if not records:raise MultiPanelMetricError("empty version denominator")
    for row in records:row.validate()
    versions={row.dataset_version for row in records}
    if len(versions)!=1:raise MultiPanelMetricError("cross-version primary pooling prohibited")
    return next(iter(versions))


def mcnemar_exact_v1(a_only: int,b_only: int) -> Mapping[str,object]:
    if type(a_only) is not int or type(b_only) is not int or min(a_only,b_only)<0: raise MultiPanelMetricError("invalid discordance")
    n=a_only+b_only
    if n==0:return {"status":"NOT_APPLICABLE_NO_DISCORDANCE","p_value":None,"discordant":0}
    tail=sum(comb(n,k) for k in range(0,min(a_only,b_only)+1))/(2**n)
    return {"status":"PASS","p_value":min(1.0,2*tail),"discordant":n,"implementation":"EXACT_TWO_SIDED_BINOMIAL"}


PRIMARY_CONTRASTS=(('M2','M1'),('M4','M0'),('M3','M0'),('M4','M3'))

__all__=["EligibleScenarioIntervalV1","ScenarioHitV1","scenario_recall_v1","official_scenario_hits_v1",
         "official_scenario_recall_v1","wilson95_v1","detection_delay_v1","summarize_delays_v1",
         "false_burden_v1","paired_scenario_table_v1","paired_official_scenario_table_v1",
         "assert_single_version_records_v1","mcnemar_exact_v1","PRIMARY_CONTRASTS","MultiPanelMetricError"]
