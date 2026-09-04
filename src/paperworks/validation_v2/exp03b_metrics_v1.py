"""Strict full-cohort admitted-output metrics; repeats are not independent samples."""
from dataclasses import dataclass
from collections import Counter
from fractions import Fraction
from .exp03b_contract_v1 import ProposalV1, SemanticTupleV1, require


@dataclass(frozen=True)
class Train3HiddenReferenceAuthorityV1:
    cohort_hash: str
    pairs: tuple[tuple[str,tuple[SemanticTupleV1,...]],...]
    def __post_init__(self):
        require(bool(self.pairs),"BLOCKED_EMPTY_COHORT")
        require(len({p for p,_ in self.pairs})==len(self.pairs),"DUPLICATE_REFERENCE_PAIR")


def majority(outputs: tuple[ProposalV1|None,...], *, decision_only=False):
    require(len(outputs)==3,"THREE_REPEATS_REQUIRED")
    valid=[x for x in outputs if x is not None]
    require(all(type(x) is ProposalV1 for x in valid),"ADMITTED_OUTPUT_TYPE")
    if not valid:return "NO_VALID_OUTPUT",None
    keys=[x.decision if decision_only else x.semantic_set() for x in valid]
    for key,count in Counter(keys).items():
        if count>=2:return "MAJORITY",key
    return "NO_MAJORITY",None


def strict_metrics(reference: dict[str,tuple[SemanticTupleV1,...]], outputs: dict[str,tuple[SemanticTupleV1,...]|None]) -> dict:
    require(bool(reference),"BLOCKED_EMPTY_COHORT")
    require(set(reference)==set(outputs),"FIXED_COHORT_DENOMINATOR")
    tp=fp=fn=tn=exact=valid=dtp=dfp=dfn=positive_predictions=0
    for pair,truth in reference.items():
        pred=outputs[pair]; r=set(truth)
        require(len(r)==len(truth),"REFERENCE_TUPLE_DUPLICATE")
        if pred is None:
            if r:fn+=1
            else:fp+=1
            dfn+=len(r)
            continue
        valid+=1;p=set(pred)
        positive_predictions+=int(bool(p))
        require(len(p)==len(pred),"PREDICTED_TUPLE_DUPLICATE")
        if p and r:tp+=1
        elif p:fp+=1
        elif r:fn+=1
        else:tn+=1
        exact+=int(p==r);dtp+=len(p&r);dfp+=len(p-r);dfn+=len(r-p)
    ratio=lambda a,b:Fraction(a,b) if b else Fraction(0)
    return {"N":len(reference),"TP":tp,"FP":fp,"FN":fn,"TN":tn,"strict_accuracy":ratio(tp+tn,len(reference)),"precision":ratio(tp,tp+fp),"recall":ratio(tp,tp+fn),"F1":ratio(2*tp,2*tp+fp+fn),"valid_output_coverage":ratio(valid,len(reference)),"semantic_exact_match_count":exact,"directional_TP":dtp,"directional_FP":dfp,"directional_FN":dfn,"directional_precision":ratio(dtp,dtp+dfp),"directional_recall":ratio(dtp,dtp+dfn),"directional_F1":ratio(2*dtp,2*dtp+dfp+dfn),"disposition_reference_valid":any(reference.values()) and not all(reference.values()),"no_predicted_positives":positive_predictions==0 and any(reference.values())}


def exact_repair(initial: ProposalV1|None, final: ProposalV1|None, truth: tuple[SemanticTupleV1,...], *, initial_status: str, feedback_actions: int) -> bool:
    return initial_status=="NEEDS_REPAIR" and feedback_actions>0 and final is not None and final.semantic_set()==tuple(sorted(truth)) and (initial is None or initial.semantic_set()!=tuple(sorted(truth)))


def portfolio_repeat(repeat: int):
    require(type(repeat) is int and repeat==1,"ONLY_REPEAT_1_PORTFOLIO")


def disposition(*,feedback_pairs:int,repair_pairs:int,t2:dict,t1b:dict,t2_burden:tuple,t1b_burden:tuple,t2_conversion:Fraction,t1b_conversion:Fraction) -> str:
    require(t2["disposition_reference_valid"] and t1b["disposition_reference_valid"],"BLOCKED_DEGENERATE_REFERENCE_COHORT")
    require(len(t2_burden)==3 and len(t1b_burden)==3 and all(type(x) is Fraction for x in t2_burden+t1b_burden),"DEFINED_PORTFOLIO_BURDEN_REQUIRED")
    primary=(feedback_pairs>=3 and repair_pairs>=2 and t2["semantic_exact_match_count"]>=t1b["semantic_exact_match_count"]+2 and t2["F1"]>=t1b["F1"] and t2["directional_F1"]>t1b["directional_F1"] and t2_burden<=t1b_burden and t2_conversion>=t1b_conversion)
    return "AGENTIC_ADVANTAGE_SUPPORTED" if primary else "AGENTIC_MECHANISM_SUPPORTED_BUT_ADVANTAGE_LIMITED" if repair_pairs>=2 else "AGENTIC_NOT_SUPPORTED"
