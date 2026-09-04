"""Single-split normal evidence producer. No file/provider/hidden-answer I/O."""
from dataclasses import asdict
import statistics
from .exp03b_contract_v1 import (SemanticTupleV1,StructuralTupleEvidenceV1,TupleEvidenceV1,Train1ProviderStructuralEvidenceV1,Train2HiddenStructuralVerifierEvidenceV1,OptionMetricsV1,SOURCES,TARGETS,HORIZONS,ALIASES,require,digest)
from .exp03b_numeric_v1 import derive_roles,census,nearest,summarize_column,roles_from_summary
from .exp01_scientific_v1 import SOURCE_VARIABLES,TARGET_VARIABLES
from .exp02_bindings_v2a import extract_candidate_specific_events_v1
from paperworks.v6.continuous_step_protocol_v1 import derive_source_screening_parameters_v1,robust_one_step_scale_v1


def slice_id(split,pair,semantic,kind):
    return "EV-"+digest({"experiment":"EXP03B","split":split,"pair":pair,"tuple":asdict(semantic),"kind":kind})[:24]


def build_split_evidence(*,split:str,matrix,feature_order:tuple[str,...],pairs:tuple[tuple[str,str],...],all_sources:tuple[str,...],input_hash:str,progress=None):
    import numpy as np
    require(split in ("train1","train2"),"PROVIDER_VERIFIER_SPLITS_ONLY")
    array=np.asarray(matrix,dtype=np.float64)
    require(array.ndim==2 and array.shape[1]==len(feature_order) and np.isfinite(array).all(),"SPLIT_MATRIX_INVALID")
    require(len(set(feature_order))==len(feature_order) and len(set(pairs))==len(pairs),"DUPLICATE_IDENTITY")
    columns={name:array[:,i] for i,name in enumerate(feature_order)}
    require(len(all_sources)==len(SOURCE_VARIABLES) and set(all_sources)==set(SOURCE_VARIABLES) and set(all_sources)<=set(columns),"ISOLATION_SOURCE_UNIVERSE")
    require(all(s in SOURCE_VARIABLES and t in TARGET_VARIABLES for s,t in pairs),"PAIR_ROLE_UNIVERSE")
    structural_events={}
    for source in all_sources:
        p=derive_source_screening_parameters_v1(tuple(map(float,columns[source])))
        structural_events[source]=() if p.source_step_threshold is None else extract_candidate_specific_events_v1(columns[source],threshold=p.source_step_threshold,tolerance=p.source_stability_tolerance)
    target_scales={target:robust_one_step_scale_v1(tuple(map(float,columns[target]))) for target in {t for _,t in pairs}}
    structural={};option_rows={};private_roles={}
    for pair in pairs:
        source,target=pair
        others=tuple(sorted({e.event_index for s,events in structural_events.items() if s!=source for e in events}))
        for sd in SOURCES:
            events=[e for e in structural_events[source] if e.direction==sd and (nearest(e.event_index,others) is None or nearest(e.event_index,others)>2)]
            for h in HORIZONS:
                responses=[float(statistics.median(columns[target][e.event_index+h:e.event_index+h+3]))-float(statistics.median(columns[target][e.event_index-5:e.event_index])) for e in events if e.event_index>=5 and e.event_index+h+3<=len(array)]
                count=len(responses);scale=target_scales[target]
                up=sum(x>scale for x in responses)/count if count else 0.;down=sum(x<-scale for x in responses)/count if count else 0.;effect=abs(float(statistics.median(responses)))/scale if count else 0.
                for td in TARGETS:
                    semantic=SemanticTupleV1(sd,td,h);key=(pair,semantic)
                    structural[key]=StructuralTupleEvidenceV1(semantic,count,up if td=="increase" else down,down if td=="increase" else up,effect,slice_id(split,pair,semantic,"structure"));option_rows[key]=[]
    event_cache={}
    summaries={name:summarize_column(column) for name,column in columns.items()}
    for alias in ALIASES:
        role_map={};event_map={};source_universe={}
        for pair in pairs:
            for sd in SOURCES:
                try:roles=roles_from_summary(summaries[pair[0]],summaries[pair[1]],sd,alias)
                except ValueError as error:
                    if str(error)!="UNMATERIALIZABLE_NORMAL_OPTION":raise
                    continue
                role_map[(pair,sd)]=roles
                key=(pair[0],roles["source_step_threshold"],roles["source_stability_tolerance"])
                if key not in event_cache:event_cache[key]=extract_candidate_specific_events_v1(columns[pair[0]],threshold=key[1],tolerance=key[2])
                event_map[(pair,sd)]=event_cache[key]
                source_universe.setdefault(pair[0],set()).update(e.event_index for e in event_cache[key])
        other_by_source={s:tuple(sorted({row for other,rows in source_universe.items() if other!=s for row in rows})) for s in source_universe}
        for pair,semantic in structural:
            ev_id=slice_id(split,pair,semantic,alias)
            roles=role_map.get((pair,semantic.source_direction))
            if roles is None:
                metric=OptionMetricsV1(alias,False,0,0,0,0,0,0,0,len(array),ev_id)
            else:
                metric,_=census(source=columns[pair[0]],target=columns[pair[1]],semantic=semantic,roles=roles,events=event_map[(pair,semantic.source_direction)],other_rows=other_by_source[pair[0]],alias=alias,slice_id=ev_id)
                private_roles[(pair,semantic.source_direction,alias)]=roles
            option_rows[(pair,semantic)].append(metric)
        if progress:progress(alias)
    kind=Train1ProviderStructuralEvidenceV1 if split=="train1" else Train2HiddenStructuralVerifierEvidenceV1
    bundles=[]
    for pair in pairs:
        rows=tuple(TupleEvidenceV1(structural[(pair,s)],tuple(option_rows[(pair,s)])) for s in sorted(s for p,s in structural if p==pair))
        bundles.append(kind("EXP03B-CAND-"+digest({"source":pair[0],"target":pair[1]})[:20],pair[0],pair[1],input_hash,rows))
    return tuple(bundles),private_roles
