"""Versioned multi-file binding over the immutable pinned eTaPR adapter."""
from __future__ import annotations
from math import isfinite
from typing import Sequence
from .etapr_exchange_v1 import OfficialEtaprV1, EtaprFileExchangeV1, validate_file_batch_v1


TARGET_SCOPE='P1_ELIGIBLE_OFFICIAL_SCENARIO_RANGES_WITH_ALL_FILE_LOCAL_PREDICTION_RANGES'


def score_namespaced_union_v2(wrapper:OfficialEtaprV1,files:Sequence[EtaprFileExchangeV1],*,separator:int=1024)->dict:
    """Canonical disjoint union; primary eligibility never derives from eTaPR.

    Reference ranges are only official intervals of scenarios independently
    classified P1_ELIGIBLE.  All frozen prediction ranges in the corresponding
    physical files are retained, so false prediction ranges are not masked.
    """
    if type(wrapper) is not OfficialEtaprV1:raise ValueError('PINNED_OFFICIAL_WRAPPER_REQUIRED')
    validate_file_batch_v1(files)
    if type(separator) is not int or separator < 1:raise ValueError('UNSAFE_FILE_NAMESPACE_SEPARATOR')
    ordered=tuple(sorted(files,key=lambda item:item.file_id))
    prediction_count=sum(len(item.prediction_ranges) for item in ordered)
    if not any(item.reference_ranges for item in ordered):
        return {'status':'NOT_APPLICABLE','eTaP':None,'eTaR':None,'F1':None,'prediction_range_count':prediction_count,'target_scope':TARGET_SCOPE}
    if prediction_count==0:
        return {'status':'PASS_EMPTY_PREDICTION','eTaP':0.0,'eTaR':0.0,'F1':0.0,'prediction_range_count':0,'target_scope':TARGET_SCOPE}
    references=[];predictions=[];offset=0
    for namespace,item in enumerate(ordered):
        references.extend(wrapper._range_class(offset+a,offset+b,f'f{namespace}:r{i}') for i,(a,b) in enumerate(item.reference_ranges))
        predictions.extend(wrapper._range_class(offset+a,offset+b,f'f{namespace}:p{i}') for i,(a,b) in enumerate(item.prediction_ranges))
        offset+=item.row_count+separator
    engine=wrapper._engine_class(theta_p=.5,theta_r=.1,delta=0.0);engine.set(references,predictions)
    precision,recall=float(engine.eTaP()),float(engine.eTaR())
    if not all(isfinite(value) and 0<=value<=1 for value in (precision,recall)):raise ValueError('INVALID_ETAPR_RESULT')
    f1=0.0 if precision+recall==0 else 2*precision*recall/(precision+recall)
    return {'status':'PASS','eTaP':precision,'eTaR':recall,'F1':f1,'prediction_range_count':prediction_count,
            'file_count':len(ordered),'separator':separator,'file_order':'LEXICAL_FILE_ID','target_scope':TARGET_SCOPE}

__all__=['score_namespaced_union_v2','TARGET_SCOPE']
