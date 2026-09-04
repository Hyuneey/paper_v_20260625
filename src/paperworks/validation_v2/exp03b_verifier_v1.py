"""Hidden train2 induction admission and bounded feedback; never an answer projection."""
from dataclasses import dataclass, asdict
from .exp03b_contract_v1 import (
    Train2HiddenStructuralVerifierEvidenceV1, ProposalV1, SOURCES,
    preferred_option, require, digest, proposal_document,
)


@dataclass(frozen=True)
class Train2HiddenVerifierAuthorityV1:
    evidence: Train2HiddenStructuralVerifierEvidenceV1
    provider_evidence_ids: frozenset[str]
    def __post_init__(self):
        require(type(self.evidence) is Train2HiddenStructuralVerifierEvidenceV1,"HIDDEN_AUTHORITY_TYPE")
        require(type(self.provider_evidence_ids) is frozenset,"REFERENCE_ALLOWLIST_TYPE")


@dataclass(frozen=True)
class VerifierResultV1:
    status: str
    issues: tuple[tuple[int,str],...]
    accepted_rule_count: int


def verify(proposal: ProposalV1, authority: Train2HiddenVerifierAuthorityV1, *, retrieval_ids=frozenset()) -> VerifierResultV1:
    require(type(proposal) is ProposalV1 and type(authority) is Train2HiddenVerifierAuthorityV1,"VERIFIER_TYPE")
    rows=authority.evidence.rows
    supported={}
    for source in SOURCES:
        choices=[r for r in rows if r.structural.semantic.source_direction==source and r.structural.passes("train2") and preferred_option(r.options) is not None]
        if choices:
            supported[source]=min(choices,key=lambda r:r.structural.rank())
    if proposal.decision=="NO_RULE":
        return VerifierResultV1("NEEDS_REPAIR",((-1,"NO_RULE_NOT_JUSTIFIED"),),0) if supported else VerifierResultV1("ACCEPTED",(),0)
    issues=[]; seen=set(); accepted=0
    for index,rule in enumerate(proposal.rules):
        before=len(issues); semantic=rule.semantic
        if semantic.source_direction in seen: issues.append((index,"DUPLICATE_SOURCE_DIRECTION"))
        seen.add(semantic.source_direction)
        if not set(rule.evidence_slice_ids)<=authority.provider_evidence_ids|retrieval_ids: issues.append((index,"EVIDENCE_REFERENCE_INVALID"))
        row=next(r for r in rows if r.structural.semantic==semantic)
        s=row.structural
        for failed,code in ((s.support<5,"LOW_SOURCE_SUPPORT"),(s.consistency<.60,"LOW_TARGET_CONSISTENCY"),(s.effect<1.,"LOW_EFFECT"),(s.consistency<=s.opposite_consistency,"OPPOSITE_DIRECTION_COMPETES")):
            if failed: issues.append((index,code))
        alternatives=[r for r in rows if r.structural.semantic.source_direction==semantic.source_direction and r.structural.semantic.target_direction==semantic.target_direction and r.structural.passes("train2")]
        if not alternatives: issues.append((index,"HORIZON_UNSUPPORTED"))
        elif min(alternatives,key=lambda r:r.structural.rank()).structural.semantic.horizon_seconds!=semantic.horizon_seconds: issues.append((index,"HORIZON_UNSTABLE"))
        if semantic.source_direction not in supported: issues.append((index,"RULE_NOT_JUSTIFIED"))
        option=preferred_option(row.options)
        if option is None: issues.append((index,"NUMERIC_OPTION_UNSUPPORTED"))
        elif option.alias!=rule.numeric_policy_option_id: issues.append((index,"NUMERIC_OPTION_UNSTABLE"))
        if len(issues)==before: accepted+=1
    if set(supported)-seen: issues.append((-1,"RULE_SET_INCOMPLETE"))
    return VerifierResultV1("NEEDS_REPAIR" if issues else "ACCEPTED",tuple(issues),accepted)


def feedback(proposal: ProposalV1, result: VerifierResultV1, calls_used: int) -> dict:
    require(result.status=="NEEDS_REPAIR" and calls_used in (1,2),"FEEDBACK_GATE")
    return {"proposal_hash":digest(proposal_document(proposal)),"issues":[{"failing_rule_index":i,"issue_code":c} for i,c in result.issues],"remaining_call_budget":3-calls_used,"evidence_retrieval_authorization":"ONE_FAILED_DIMENSION_ALL_ALTERNATIVES_CANONICAL"}


def retrieval(authority: Train2HiddenVerifierAuthorityV1, proposal: ProposalV1, result: VerifierResultV1) -> dict:
    require(type(authority) is Train2HiddenVerifierAuthorityV1 and result.status=="NEEDS_REPAIR","RETRIEVAL_GATE")
    numeric=any(code.startswith("NUMERIC_OPTION") for _,code in result.issues)
    if numeric:
        index=next(i for i,c in result.issues if c.startswith("NUMERIC_OPTION"))
        row=next(r for r in authority.evidence.rows if r.structural.semantic==proposal.rules[index].semantic)
        alternatives=[asdict(option) for option in row.options]
        dimension="numeric_option"
    else:
        alternatives=[asdict(r.structural) for r in sorted(authority.evidence.rows,key=lambda r:r.structural.semantic)]
        dimension="temporal_structure"
    body={"split":"train2","dimension":dimension,"alternatives":alternatives}
    return {**body,"retrieval_hash":digest(body)}


def select_t1b(draws):
    require(len(draws)==3,"T1B_THREE_DRAWS")
    rank={"ACCEPTED":0,"NEEDS_REPAIR":1,"REJECTED":2}
    return min(range(3),key=lambda i:(rank[draws[i][1].status],-draws[i][1].accepted_rule_count,len(draws[i][1].issues),i))
