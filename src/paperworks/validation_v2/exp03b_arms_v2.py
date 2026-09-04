"""Transport-free bounded state machine. No provider, credentials or file I/O."""
from dataclasses import dataclass
from .exp03b_semantic_v2 import SemanticProposalV2 as ProposalV1, parse_proposal, proposal_document, digest, require
from .exp03b_hidden_v2 import VerifierResultV1, feedback, select_t1b

FAILURES=("PROVIDER_ERROR","EMPTY_RESPONSE","PARSE_FAILURE","VERIFIER_REJECTION","NEEDS_REPAIR_BUDGET_EXHAUSTED","RETRIEVAL_FAILURE","SYSTEM_ERROR","ALL_DRAWS_FAILED","NO_MAJORITY","NO_VALID_OUTPUT")


@dataclass(frozen=True)
class AdmittedOutputV1:
    candidate_id: str
    proposal: ProposalV1
    verifier_hash: str
    status: str = "ACCEPTED"
    def __post_init__(self):
        require(self.status=="ACCEPTED" and type(self.proposal) is ProposalV1 and len(self.verifier_hash)==64,"ADMISSION_REQUIRED")


@dataclass(frozen=True)
class ArmResultV1:
    candidate_id: str
    arm: str
    repeat: int
    raw: tuple[ProposalV1|None,...]
    verifier_results: tuple[VerifierResultV1,...]
    admitted: AdmittedOutputV1|None
    terminal: str
    feedback_records: tuple[dict,...]
    retrieval_records: tuple[dict,...]


def run_arm(*, candidate_id: str, arm: str, repeat: int, mock_responses: tuple, verify_callback, retrieve_callback=None) -> ArmResultV1:
    """Synthetic/local response replay only; callable provider transports are rejected.

    Future execution must acquire/persist each response through separately authorized
    receipt-first custody, then use the same step contract. This function cannot call a network.
    """
    require(arm in ("T1","T1-B","T2") and repeat in (1,2,3),"ARM_IDENTITY")
    require(type(mock_responses) is tuple and len(mock_responses)<= (1 if arm=="T1" else 3),"FOURTH_CALL_PROHIBITED")
    raw=[];results=[];feedbacks=[];retrievals=[];terminal="EMPTY_RESPONSE";allowed=frozenset()
    limit=1 if arm=="T1" else 3
    for i,response in enumerate(mock_responses[:limit]):
        p=None
        if response is None:
            terminal="PROVIDER_ERROR";v=VerifierResultV1("REJECTED",((-1,terminal),),0)
        else:
            try:p=parse_proposal(response)
            except (ValueError,TypeError,KeyError):
                terminal="PARSE_FAILURE";v=VerifierResultV1("REJECTED",((-1,terminal),),0)
            else:v=verify_callback(p,allowed)
        raw.append(p);results.append(v)
        if arm=="T2":
            if v.status=="ACCEPTED":break
            if v.status=="REJECTED":break
            if i==2:terminal="NEEDS_REPAIR_BUDGET_EXHAUSTED";break
            f=feedback(p,v,i+1);feedbacks.append(f)
            if retrieve_callback:
                try:r=retrieve_callback(p,v)
                except (ValueError,RuntimeError):terminal="RETRIEVAL_FAILURE";break
                retrievals.append(r)
                def ids(x):
                    if isinstance(x,dict):
                        for k,z in x.items():
                            if k=="evidence_slice_id":yield z
                            else:yield from ids(z)
                    elif isinstance(x,(tuple,list)):
                        for z in x:yield from ids(z)
                allowed=allowed|frozenset(ids(r))
        elif arm=="T1":break
    chosen=None
    if arm=="T1-B":
        require(len(raw)==3,"T1B_THREE_DRAWS")
        chosen=select_t1b(tuple(zip(raw,results)))
        terminal="ALL_DRAWS_FAILED"
    elif raw:chosen=len(raw)-1
    admitted=None
    if chosen is not None and results[chosen].status=="ACCEPTED":
        p=raw[chosen];admitted=AdmittedOutputV1(candidate_id,p,digest({"proposal":proposal_document(p),"status":"ACCEPTED","candidate_id":candidate_id}))
        terminal="INTENTIONAL_NO_RULE" if p.decision=="NO_RULE" else "ACCEPTED_RULE_SET"
    elif chosen is not None and results[chosen].status=="NEEDS_REPAIR":terminal="NEEDS_REPAIR_BUDGET_EXHAUSTED" if arm=="T2" else "VERIFIER_REJECTION"
    return ArmResultV1(candidate_id,arm,repeat,tuple(raw),tuple(results),admitted,terminal,tuple(feedbacks),tuple(retrievals))
