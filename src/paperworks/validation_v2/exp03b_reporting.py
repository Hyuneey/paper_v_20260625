"""Pure strict reporting over admitted outputs; no feature or provider dependencies."""
from collections import Counter
from fractions import Fraction
from .exp03b_contract_v1 import require
from .exp03b_execution import VerifiedAdmission
from .exp03b_evaluation import evaluate_admitted,admitted_exact_repair


def ratio(n,d):return {"numerator":n,"denominator":d,"value":Fraction(n,d) if d else None,"defined":bool(d)}


def report(reference:dict,outputs:dict,terminals:dict):
    require(set(reference)==set(outputs)==set(terminals),"REPORT_COHORT_BINDING")
    evaluation=evaluate_admitted(reference,outputs)
    source=target=horizon=denominator=0;execution_stable=numeric_stable=valid_pairs=0
    failure=Counter()
    for pair,truth in reference.items():
        pred=evaluation["semantic_outputs"][pair]
        for r in truth:
            denominator+=1
            same=[p for p in pred or () if p.source_direction==r.source_direction]
            source+=int(bool(same))
            target+=int(any(p.target_direction==r.target_direction for p in same))
            horizon+=int(any(p.horizon_seconds==r.horizon_seconds for p in same))
        admitted=[x for x in outputs[pair] if x is not None]
        if admitted:
            valid_pairs+=1
            execution_stable+=int(max(Counter(x.proposal.execution_set() for x in admitted).values())>=2)
            numeric_stable+=int(max(Counter(tuple(sorted((r.semantic.source_direction,r.numeric_policy_option_id) for r in x.proposal.rules)) for x in admitted).values())>=2)
        require(len(terminals[pair])==3,"TERMINAL_REPEATS")
        for state in terminals[pair]:
            if state not in ("ACCEPTED_RULE_SET","INTENTIONAL_NO_RULE"):failure[state]+=1
    return {**evaluation,"structure_reference_rule_denominator":denominator,"source_direction_accuracy":ratio(source,denominator),"target_direction_accuracy":ratio(target,denominator),"exact_horizon_accuracy":ratio(horizon,denominator),"execution_set_majority_stability":ratio(execution_stable,len(reference)),"numeric_option_majority_stability":ratio(numeric_stable,len(reference)),"failure_taxonomy":dict(sorted(failure.items())),"stable_unit":"PAIR_NOT_REPEAT_IID"}


def repair_pair_sets(records:tuple,reference:dict):
    feedback=set();verifier=set();semantic=set();decision=set()
    for row in records:
        pair=row["candidate_id"];initial=row["initial"];final=row["final"]
        require(pair in reference and (final is None or type(final) is VerifiedAdmission and final.candidate_id==pair),"REPAIR_PAIR_BINDING")
        if row["feedback_actions"]>0:feedback.add(pair)
        if row["initial_status"]=="NEEDS_REPAIR" and final is not None:
            final.replay();verifier.add(pair)
        if admitted_exact_repair(pair,initial,final,reference[pair],initial_status=row["initial_status"],feedback_actions=row["feedback_actions"]):semantic.add(pair)
        if initial is not None and final is not None and bool(initial.rules)!=bool(reference[pair]) and bool(final.proposal.rules)==bool(reference[pair]):decision.add(pair)
    return {"feedback_pairs":tuple(sorted(feedback)),"verifier_repair_pairs":tuple(sorted(verifier)),"train3_confirmed_exact_repair_pairs":tuple(sorted(semantic)),"pair_decision_repair_pairs":tuple(sorted(decision))}


def paired_comparison(reference:dict,left:dict,right:dict):
    require(set(reference)==set(left)==set(right),"PAIRED_COHORT_ALIGNMENT")
    rows=[]
    for pair in sorted(reference):
        a=left[pair];b=right[pair];truth=tuple(sorted(reference[pair]))
        rows.append({"candidate_id":pair,"left_exact":a is not None and tuple(sorted(a))==truth,"right_exact":b is not None and tuple(sorted(b))==truth})
    return rows
