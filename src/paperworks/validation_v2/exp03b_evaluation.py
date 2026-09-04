"""Hidden evaluation consumers, physically separate from provider rendering."""
from dataclasses import dataclass
from fractions import Fraction
from .exp03b_contract_v1 import require,SemanticTupleV1,ProposalV1
from .exp03b_execution import VerifiedAdmission
from .exp03b_metrics_v1 import majority,strict_metrics,exact_repair
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


@dataclass(frozen=True)
class GuardRuleInput:
    candidate_id:str
    source:str
    target:str
    semantic:SemanticTupleV1
    alias:str
    candidate_roles:tuple[tuple[str,float],...]
    common_roles:tuple[tuple[str,float],...]
    train2_acceptance_hash:str
    train3_reference_hash:str
    train1_numeric_hash:str
    train2_numeric_hash:str
    def __post_init__(self):
        require(type(self.semantic) is SemanticTupleV1,"GUARD_SEMANTIC")
        require(all(type(h) is str and len(h)==64 for h in (self.train2_acceptance_hash,self.train3_reference_hash,self.train1_numeric_hash,self.train2_numeric_hash)),"GUARD_PREDECESSOR_BINDING")
        require(set(dict(self.candidate_roles))==set(dict(self.common_roles)),"GUARD_ROLE_CLOSURE")


def bind_guard_rule(admission:VerifiedAdmission,rule_index:int,*,pair:tuple,reference:dict,reference_hash:str,train1:dict,train2:dict):
    """Numeric maps contain only this pair's split-local (direction,alias) roles."""
    from .exp03b_numeric_v1 import pooled_roles
    from .exp03b_contract_v1 import digest
    require(type(admission) is VerifiedAdmission,"GUARD_ADMISSION_REQUIRED");admission.replay()
    require(admission.candidate_id=="EXP03B-CAND-"+digest({"source":pair[0],"target":pair[1]})[:20],"GUARD_PAIR_BINDING")
    rule=admission.proposal.rules[rule_index]
    require(rule.semantic in reference[admission.candidate_id],"TRAIN3_CONFIRMATION_REQUIRED")
    selected=(rule.semantic.source_direction,rule.numeric_policy_option_id);common=(rule.semantic.source_direction,"NUM-000")
    roles=pooled_roles(train1[selected],train2[selected],train2_status="ACCEPTED")
    baseline=pooled_roles(train1[common],train2[common],train2_status="ACCEPTED")
    numhash=lambda table:digest([{ "key":k,"values":v} for k,v in sorted(table.items())])
    return GuardRuleInput(admission.candidate_id,*pair,rule.semantic,rule.numeric_policy_option_id,tuple(sorted(roles.items())),tuple(sorted(baseline.items())),admission.receipt["self_hash"],reference_hash,numhash(train1),numhash(train2))


def run_guard_portfolio(*,authority:Train4HiddenGuardAuthorityV1,matrix,feature_order:tuple,rules:tuple[GuardRuleInput,...]):
    """Two counterfactual numeric worlds on the same train3-confirmed semantic set.

    Each world's source activity is its relation-local both-direction event union;
    isolation and all outcomes are delegated to Formal V4. No downstream repair.
    """
    require(type(authority) is Train4HiddenGuardAuthorityV1 and len(matrix)==authority.exposure,"TRAIN4_AUTHORITY_BINDING")
    require(all(type(r) is GuardRuleInput for r in rules),"GUARD_RULE_BINDING")
    require(len({(r.candidate_id,r.semantic) for r in rules})==len(rules),"GUARD_DUPLICATE_RULE")
    positions={s:i for i,s in enumerate(feature_order)};worlds={}
    for world in ("candidate","common"):
        events={};activity={};roles={}
        for i,r in enumerate(rules):
            values=dict(r.candidate_roles if world=="candidate" else r.common_roles);roles[i]=values
            e=extract_candidate_specific_events_v1(matrix[:,positions[r.source]],threshold=values["source_step_threshold"],tolerance=values["source_stability_tolerance"])
            events[i]=e;activity.setdefault(r.source,set()).update(x.event_index for x in e)
        records=[]
        for i,r in enumerate(rules):
            other=tuple(sorted({n for source,ns in activity.items() if source!=r.source for n in ns}))
            records.append(census(source=matrix[:,positions[r.source]],target=matrix[:,positions[r.target]],semantic=r.semantic,roles=roles[i],events=events[i],other_rows=other,alias=r.alias if world=="candidate" else "NUM-000",slice_id="EV-HIDDEN-GUARD"))
        worlds[world]=records
    states=[];retained=[]
    for i,r in enumerate(rules):
        c,seconds=worlds["candidate"][i];b,_=worlds["common"][i]
        status=guard(c,b);states.append((r.candidate_id,r.semantic,status))
        if status=="RETAINED":retained.append((authority.file_id,seconds,c.passed,c.failed,c.abstained))
    return states,portfolio_census(tuple(retained),{authority.file_id:authority.exposure})
