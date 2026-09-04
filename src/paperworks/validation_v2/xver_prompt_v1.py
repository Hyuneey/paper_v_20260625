"""External T2 uses frozen prompt and semantic schema, extended GLOBAL retrieval.

Input is an already-projected train2 aggregate, never a hidden answer object.
No event, numeric, evaluation, provider transport or filesystem dependency.
"""
import math
from .exp03b_prompt_v2 import request_body as initial_request, validate_repair, validate_projection, execution_config as base_config
from .exp03b_contract_v1 import require, digest, encoded, HORIZONS
from .exp03b_firewall_v2 import assert_clean


def validate_global_retrieval(q):
    require(type(q) is dict and set(q)=={'split','dimension','alternatives','stat_association','gdn_rows','retrieval_hash'}, 'CLOSED_EXTERNAL_RETRIEVAL')
    require(q['split']=='train2' and q['dimension']=='temporal_structure', 'EXTERNAL_RETRIEVAL_SPLIT')
    require(q['retrieval_hash']==digest({k:v for k,v in q.items() if k!='retrieval_hash'}), 'EXTERNAL_RETRIEVAL_HASH')
    require(type(q['stat_association']) in (int,float) and math.isfinite(q['stat_association']), 'STAT_NONFINITE')
    rows=q['gdn_rows']
    require(type(rows) in (tuple,list) and len(rows)==5 and all(type(r) in (tuple,list) and len(r)==4 for r in rows) and tuple(r[0] for r in rows)==HORIZONS, 'GLOBAL_ONLY_RETRIEVAL')
    require(all(type(x) in (int,float) and math.isfinite(x) for r in rows for x in r[1:3]) and all(r[3] is None or type(r[3]) in (int,float) and math.isfinite(r[3]) for r in rows), 'GLOBAL_FINITE')
    assert_clean(q)
    structural={k:q[k] for k in ('split','dimension','alternatives')}
    return {**structural,'retrieval_hash':digest(structural)}


def request_body(evidence, *, repair=None):
    body=initial_request(evidence)
    if repair is None:return body
    require(type(repair) is dict and set(repair)=={'previous_proposal','feedback','retrieval'}, 'REPAIR_ENVELOPE')
    q=repair['retrieval']
    structural=validate_global_retrieval(q) if q is not None else None
    # Validate unchanged proposal/feedback and all twenty structural alternatives.
    validate_repair({'previous_proposal':repair['previous_proposal'],'feedback':repair['feedback'],'retrieval':structural})
    assert_clean(repair)
    body['input']=encoded({'evidence':evidence,'repair':repair}).decode()
    return body


def execution_config():
    config=base_config()
    return {**config,'repair_history':'LATEST_PROPOSAL_ONE_FEEDBACK_ONE_SPLIT_PURE_STRUCTURAL_STAT_GLOBAL_SLICE_STATELESS','external_repetitions':1,'external_arms':['T2'],'event_evidence_allowed':False}
