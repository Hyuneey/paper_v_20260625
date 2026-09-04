"""Split-local unconfirmed tuple numeric formulas and exact Formal V4 census."""
from bisect import bisect_left
from itertools import product
import math
from .exp03b_contract_v1 import OptionMetricsV1, ALIASES, require, digest
from .numeric_policy_v1 import (
    RELATION_THRESHOLD_NOISE_MULTIPLIERS,RELATION_AMPLITUDE_QUANTILES,
    RELATION_STABILITY_NOISE_MULTIPLIERS,RELATION_STABILITY_THRESHOLD_FRACTIONS,
    COMMON_THRESHOLD_NOISE_MULTIPLIER,COMMON_STABILITY_NOISE_MULTIPLIER,
    COMMON_STABILITY_THRESHOLD_FRACTION,FROZEN_WINDOW_VALUES,
)
from .exp02_bindings_v2a import extract_candidate_specific_events_v1, empirical_linear_quantiles_v1
from .runtime_v1 import FormalV4PreparedParametersV1, evaluate_formal_v4_semantics_v1

GRID=(None,)+tuple(product(RELATION_THRESHOLD_NOISE_MULTIPLIERS,RELATION_AMPLITUDE_QUANTILES,RELATION_STABILITY_NOISE_MULTIPLIERS,RELATION_STABILITY_THRESHOLD_FRACTIONS))


def derive_roles(source, target, source_direction: str, alias: str) -> dict[str,float]:
    import numpy as np
    require(alias in ALIASES and source_direction in ("step_up","step_down"),"NUMERIC_IDENTITY")
    require(np.asarray(source).ndim==np.asarray(target).ndim==1 and len(source)==len(target),"SPLIT_SERIES_SHAPE")
    return roles_from_summary(summarize_column(source),summarize_column(target),source_direction,alias)


def summarize_column(values):
    import numpy as np
    a=np.asarray(values,dtype=np.float64)
    require(a.ndim==1 and len(a)>1 and np.isfinite(a).all(),"SPLIT_SERIES_SHAPE")
    dx=np.diff(a)
    groups=(np.abs(dx)[np.abs(dx)>0],dx[dx>0],-dx[dx<0])
    return (float(np.median(np.abs(dx))),)+tuple(empirical_linear_quantiles_v1(v) if len(v) else None for v in groups)


def roles_from_summary(source_summary,target_summary,source_direction,alias):
    require(alias in ALIASES and source_direction in ("step_up","step_down"),"NUMERIC_IDENTITY")
    noise=source_summary[0];target_noise=target_summary[0]
    point=GRID[ALIASES.index(alias)]
    if point is None:
        quantiles=source_summary[1];n,q,s,f=COMMON_THRESHOLD_NOISE_MULTIPLIER,".75",COMMON_STABILITY_NOISE_MULTIPLIER,COMMON_STABILITY_THRESHOLD_FRACTION
    else:
        quantiles=source_summary[2 if source_direction=="step_up" else 3];n,q,s,f=point
    require(quantiles is not None and target_noise>0,"UNMATERIALIZABLE_NORMAL_OPTION")
    threshold=max(float(n)*noise,quantiles[(.5,.75,.9).index(float(q))])
    tolerance=max(float(s)*noise,float(f)*threshold)
    roles={"source_step_threshold":threshold,"source_stability_tolerance":tolerance,"target_noise_scale":target_noise,**{k:float(v) for k,v in FROZEN_WINDOW_VALUES}}
    require(all(math.isfinite(v) for v in roles.values()),"NONFINITE_NUMERIC_AUTHORITY")
    return roles


def parameters(roles: dict[str,float]) -> FormalV4PreparedParametersV1:
    return FormalV4PreparedParametersV1(source_pre_count=5,source_post_count=5,target_baseline_count=5,target_response_count=3,minimum_source_stability_fraction=roles["minimum_source_stability_fraction"],source_step_threshold=roles["source_step_threshold"],source_stability_tolerance=roles["source_stability_tolerance"],target_noise_scale=roles["target_noise_scale"],source_refractory_seconds=roles["source_refractory_seconds"],cross_source_isolation_radius_seconds=roles["cross_source_isolation_radius_seconds"])


def nearest(row:int, ordered:tuple[int,...]):
    at=bisect_left(ordered,row);choices=[]
    if at<len(ordered):choices.append(abs(row-ordered[at]))
    if at:choices.append(abs(row-ordered[at-1]))
    return float(min(choices)) if choices else None


def census(*,source,target,semantic,roles,events,other_rows,alias,slice_id):
    """Return private fail coordinates separately from safe aggregate metrics."""
    p=parameters(roles);same=tuple(e.event_index for e in events);passed=failed=abstained=0;fail_rows=set()
    for event in events:
        if event.direction!=semantic.source_direction:continue
        row=event.event_index;at=bisect_left(same,row);end=row+semantic.horizon_seconds+3
        result=evaluate_formal_v4_semantics_v1(source_direction=semantic.source_direction,target_direction=semantic.target_direction,parameters=p,source_pre_values=tuple(map(float,source[row-5:row])),source_post_values=tuple(map(float,source[row:row+5])),target_baseline_values=tuple(map(float,target[row-5:row])),target_response_values=tuple(map(float,target[row+semantic.horizon_seconds:min(end,len(target))])),seconds_since_previous_source_trigger=None if at==0 else float(row-same[at-1]),seconds_to_nearest_other_source_trigger=nearest(row,other_rows),future_window_complete=end<=len(target))
        if result.outcome=="PASS":passed+=1
        elif result.outcome=="FAIL":failed+=1;fail_rows.add(end-1)
        elif result.outcome=="ABSTAIN":abstained+=1
        else:raise ValueError("UNEXPECTED_FORMAL_V4_OUTCOME")
    episodes=sum(row-1 not in fail_rows for row in fail_rows)
    return OptionMetricsV1(alias,True,passed+failed+abstained,passed,failed,abstained,0,len(fail_rows),episodes,len(source),slice_id),tuple(sorted(fail_rows))


def pooled_roles(train1:dict,train2:dict,*,train2_status:str) -> dict:
    require(train2_status=="ACCEPTED" and set(train1)==set(train2),"POOLING_BEFORE_ACCEPTANCE")
    return {k:max(train1[k],train2[k]) for k in train1}
