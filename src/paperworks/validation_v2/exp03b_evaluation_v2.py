"""Hidden evaluation consumers, physically separate from provider rendering."""
from dataclasses import dataclass
from fractions import Fraction
from .exp03b_semantic_v2 import require,SemanticTupleV1,SemanticProposalV2 as ProposalV1
from .exp03b_execution_v2 import VerifiedAdmission
from .exp03b_metrics_v1 import strict_metrics,exact_repair
from .exp03b_metrics_v2 import majority
from .exp03b_guard_v1 import guard,portfolio_census,Train4HiddenGuardAuthorityV1
from .exp03b_numeric_v1 import census
from .exp02_bindings_v2a import extract_candidate_specific_events_v1


def admitted_majority(candidate_id:str, outputs:tuple, *,decision_only=False):
    require(len(outputs)==3 and all(o is None or type(o) is VerifiedAdmission and o.candidate_id==candidate_id for o in outputs),"ADMITTED_PAIR_BINDING")
    for o in outputs:
        if o:o.replay()
    return majority(tuple(o.proposal if o else None for o in outputs),decision_only=decision_only)


def evaluate_admitted(reference:dict, outputs:dict) -> dict:
    require(set(reference)==set(outputs),"COHORT_BINDING")
    decisions={};semantic={};valid_reference={};valid_outputs={}
    for pair,observations in outputs.items():
        status,s=admitted_majority(pair,observations)
        decisions[pair]=admitted_majority(pair,observations,decision_only=True)
        semantic[pair]=s if status=="MAJORITY" else None
        if status=="MAJORITY":valid_reference[pair]=reference[pair];valid_outputs[pair]=s
    strict=strict_metrics(reference,semantic)
    conditional=strict_metrics(valid_reference,valid_outputs) if valid_reference else None
    return {"strict":strict,"conditional":conditional,"conditional_denominator":len(valid_reference),"top_level_majority":decisions,"semantic_outputs":semantic}


def admitted_exact_repair(candidate_id,initial,final,truth,*,initial_status,feedback_actions):
    require(final is None or type(final) is VerifiedAdmission and final.candidate_id==candidate_id,"REPAIR_ADMISSION_PAIR")
    if final:final.replay()
    return exact_repair(initial,final.proposal if final else None,truth,initial_status=initial_status,feedback_actions=feedback_actions)



