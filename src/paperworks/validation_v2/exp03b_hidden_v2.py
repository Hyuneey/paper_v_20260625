"""Physically separate train2 semantic admission. No numeric selection."""
from dataclasses import dataclass, asdict
from .exp03b_contract_v1 import StructuralTupleEvidenceV1, SOURCES, require, digest
from .exp03b_semantic_v2 import SemanticProposalV2, validate_rows, proposal_document
from .exp03b_verifier_v1 import VerifierResultV1, select_t1b


@dataclass(frozen=True)
class Train2SemanticEvidenceV2:
    candidate_id: str
    source: str
    target: str
    input_hash: str
    rows: tuple[StructuralTupleEvidenceV1,...]
    split: str='train2'
    def __post_init__(self):
        require(self.split=='train2','TRAIN2_SPLIT_TAINT');validate_rows(self.rows)
        require(self.candidate_id=='EXP03B-CAND-'+digest({'source':self.source,'target':self.target})[:20], 'PAIR_IDENTITY')


@dataclass(frozen=True)
class Train2HiddenVerifierAuthorityV2:
    evidence: Train2SemanticEvidenceV2
    provider_evidence_ids: frozenset[str]
    def __post_init__(self):
        require(type(self.evidence) is Train2SemanticEvidenceV2 and type(self.provider_evidence_ids) is frozenset,'HIDDEN_AUTHORITY_TYPE')


def verify(proposal, authority, *, retrieval_ids=frozenset()):
    require(type(proposal) is SemanticProposalV2 and type(authority) is Train2HiddenVerifierAuthorityV2,'VERIFIER_TYPE')
    rows=authority.evidence.rows; supported={}
    for source in SOURCES:
        choices=[r for r in rows if r.semantic.source_direction==source and r.passes('train2')]
        if choices:supported[source]=min(choices,key=lambda r:r.rank())
    if proposal.decision=='NO_RULE':
        return VerifierResultV1('NEEDS_REPAIR',((-1,'NO_RULE_NOT_JUSTIFIED'),),0) if supported else VerifierResultV1('ACCEPTED',(),0)
    issues=[];seen=set();accepted=0
    for index,rule in enumerate(proposal.rules):
        before=len(issues);semantic=rule.semantic
        if semantic.source_direction in seen:issues.append((index,'DUPLICATE_SOURCE_DIRECTION'))
        seen.add(semantic.source_direction)
        if not set(rule.evidence_slice_ids)<=authority.provider_evidence_ids|retrieval_ids:issues.append((index,'EVIDENCE_REFERENCE_INVALID'))
        s=next(r for r in rows if r.semantic==semantic)
        for failed,code in ((s.support<5,'LOW_SOURCE_SUPPORT'),(s.consistency<.60,'LOW_TARGET_CONSISTENCY'),(s.effect<1.,'LOW_EFFECT'),(s.consistency<=s.opposite_consistency,'OPPOSITE_DIRECTION_COMPETES')):
            if failed:issues.append((index,code))
        alternatives=[r for r in rows if r.semantic.source_direction==semantic.source_direction and r.semantic.target_direction==semantic.target_direction and r.passes('train2')]
        if not alternatives:issues.append((index,'HORIZON_UNSUPPORTED'))
        elif min(alternatives,key=lambda r:r.rank()).semantic.horizon_seconds!=semantic.horizon_seconds:issues.append((index,'HORIZON_UNSTABLE'))
        if semantic.source_direction not in supported or supported[semantic.source_direction].semantic!=semantic:issues.append((index,'RULE_NOT_JUSTIFIED'))
        if len(issues)==before:accepted+=1
    if set(supported)-seen:issues.append((-1,'RULE_SET_INCOMPLETE'))
    return VerifierResultV1('NEEDS_REPAIR' if issues else 'ACCEPTED',tuple(issues),accepted)


ISSUE_CODES=('LOW_SOURCE_SUPPORT','LOW_TARGET_CONSISTENCY','LOW_EFFECT','OPPOSITE_DIRECTION_COMPETES','HORIZON_UNSUPPORTED','HORIZON_UNSTABLE','RULE_NOT_JUSTIFIED','RULE_SET_INCOMPLETE','NO_RULE_NOT_JUSTIFIED','EVIDENCE_REFERENCE_INVALID','DUPLICATE_SOURCE_DIRECTION')


def feedback(proposal,result,calls_used):
    require(result.status=='NEEDS_REPAIR' and calls_used in (1,2),'FEEDBACK_GATE')
    return {'proposal_hash':digest(proposal_document(proposal)), 'issues':[{'failing_rule_index':i,'issue_code':c} for i,c in result.issues], 'remaining_call_budget':3-calls_used, 'evidence_retrieval_authorization':'ONE_STRUCTURAL_SLICE_ALL_ALTERNATIVES_CANONICAL'}


def retrieval(authority,proposal,result):
    require(type(authority) is Train2HiddenVerifierAuthorityV2 and type(proposal) is SemanticProposalV2 and result.status=='NEEDS_REPAIR' and all(c in ISSUE_CODES for _,c in result.issues),'RETRIEVAL_GATE')
    body={'split':'train2','dimension':'temporal_structure','alternatives':[asdict(r) for r in sorted(authority.evidence.rows,key=lambda r:r.semantic)]}
    return {**body,'retrieval_hash':digest(body)}
