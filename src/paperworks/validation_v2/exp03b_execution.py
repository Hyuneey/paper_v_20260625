"""Final prospective terminal-cause adapter; no provider transport in preparation."""
from dataclasses import replace, asdict
from .exp03b_arms_v1 import run_arm
from .exp03b_contract_v1 import require,digest,proposal_document,ProposalV1
from .exp03b_verifier_v1 import Train2HiddenVerifierAuthorityV1
from .exp03b_admission_verifier import verify

_ISSUER=object()


class VerifiedAdmission:
    __slots__=("candidate_id","proposal","receipt")
    def __init__(self, token, candidate_id, proposal, receipt):
        require(token is _ISSUER,"ADMISSION_FACTORY_REQUIRED")
        self.candidate_id=candidate_id;self.proposal=proposal;self.receipt=receipt
    def replay(self):
        body={k:v for k,v in self.receipt.items() if k!="self_hash"}
        require(self.receipt["self_hash"]==digest(body) and body["proposal_hash"]==digest(proposal_document(self.proposal)) and body["candidate_id"]==self.candidate_id and body["verifier_status"]=="ACCEPTED","ADMISSION_REPLAY_FAILED")


def admit(proposal:ProposalV1, authority:Train2HiddenVerifierAuthorityV1, *,implementation_hash:str,config_hash:str,retrieval_ids=frozenset()):
    require(all(len(h)==64 and set(h)<=set("0123456789abcdef") for h in (implementation_hash,config_hash)),"ADMISSION_EXECUTION_BINDING")
    result=verify(proposal,authority,retrieval_ids=retrieval_ids)
    require(result.status=="ACCEPTED","ADMISSION_VERIFIER_REJECTION")
    body={"candidate_id":authority.evidence.candidate_id,"proposal_hash":digest(proposal_document(proposal)),"hidden_authority_hash":digest(asdict(authority.evidence)),"verifier_result_hash":digest(asdict(result)),"verifier_status":result.status,"implementation_hash":implementation_hash,"config_hash":config_hash,"retrieval_ids_hash":digest(sorted(retrieval_ids))}
    return VerifiedAdmission(_ISSUER,authority.evidence.candidate_id,proposal,{**body,"self_hash":digest(body)})


def replay_arm(**kwargs):
    retrieval_failed=False
    original=kwargs.get("retrieve_callback")
    if original:
        def retrieve(p,v):
            nonlocal retrieval_failed
            try:return original(p,v)
            except (ValueError,RuntimeError):
                retrieval_failed=True
                raise
        kwargs["retrieve_callback"]=retrieve
    result=run_arm(**kwargs)
    if retrieval_failed:return replace(result,admitted=None,terminal="RETRIEVAL_FAILURE")
    if result.raw and result.raw[-1] is not None and result.verifier_results[-1].status=="REJECTED" and result.terminal=="EMPTY_RESPONSE":
        return replace(result,terminal="VERIFIER_REJECTION")
    return result
