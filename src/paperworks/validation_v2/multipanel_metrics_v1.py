"""Prospectively frozen, version-separated multi-panel metric arithmetic."""
from __future__ import annotations
from dataclasses import dataclass
from math import comb, sqrt
from statistics import median
from typing import Iterable, Mapping, Sequence


class MultiPanelMetricError(ValueError): pass


def scenario_recall_v1(hits: Sequence[bool]) -> Mapping[str, object]:
    if not hits: return {"status":"NOT_EVALUABLE","hits":0,"eligible":0,"recall":None}
    if any(type(value) is not bool for value in hits): raise MultiPanelMetricError("strict Boolean hits required")
    count=sum(hits)
    return {"status":"PASS","hits":count,"eligible":len(hits),"recall":count/len(hits)}


def wilson95_v1(hits: int, total: int) -> tuple[float,float] | None:
    if type(hits) is not int or type(total) is not int or not 0 <= hits <= total: raise MultiPanelMetricError("invalid Wilson counts")
    if total==0:return None
    z=1.959963984540054; p=hits/total; d=1+z*z/total
    c=(p+z*z/(2*total))/d; h=z*sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return max(0.0,c-h),min(1.0,c+h)


def detection_delay_v1(start: int, alarm_times: Sequence[int], end: int) -> int | None:
    if type(start) is not int or type(end) is not int or start>end: raise MultiPanelMetricError("invalid scenario interval")
    inside=[value for value in alarm_times if type(value) is int and start<=value<=end]
    return None if not inside else min(inside)-start


def summarize_delays_v1(delays: Sequence[int | None]) -> Mapping[str,object]:
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


def paired_scenario_table_v1(a: Sequence[bool], b: Sequence[bool]) -> Mapping[str,int]:
    if len(a)!=len(b) or any(type(v) is not bool for v in (*a,*b)): raise MultiPanelMetricError("paired scenario alignment mismatch")
    return {"both_hit":sum(x and y for x,y in zip(a,b)),"a_only":sum(x and not y for x,y in zip(a,b)),
            "b_only":sum(not x and y for x,y in zip(a,b)),"neither":sum(not x and not y for x,y in zip(a,b)),
            "hit_difference":sum(a)-sum(b)}


def mcnemar_exact_v1(a_only: int,b_only: int) -> Mapping[str,object]:
    if type(a_only) is not int or type(b_only) is not int or min(a_only,b_only)<0: raise MultiPanelMetricError("invalid discordance")
    n=a_only+b_only
    if n==0:return {"status":"NOT_APPLICABLE_NO_DISCORDANCE","p_value":None,"discordant":0}
    tail=sum(comb(n,k) for k in range(0,min(a_only,b_only)+1))/(2**n)
    return {"status":"PASS","p_value":min(1.0,2*tail),"discordant":n,"implementation":"EXACT_TWO_SIDED_BINOMIAL"}


PRIMARY_CONTRASTS=(('M2','M1'),('M4','M0'),('M3','M0'),('M4','M3'))

__all__=["scenario_recall_v1","wilson95_v1","detection_delay_v1","summarize_delays_v1",
         "false_burden_v1","paired_scenario_table_v1","mcnemar_exact_v1","PRIMARY_CONTRASTS","MultiPanelMetricError"]
