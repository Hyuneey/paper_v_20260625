"""Pre-provider SCI01 closure: exact preferred supported tuple per source.

The pre-I/O evidence implementation stays immutable; this admission adapter
corrects omission of the already-approved preferred target/tuple comparison.
"""
from .exp03b_verifier_v1 import verify as original_verify,VerifierResultV1
from .exp03b_contract_v1 import SOURCES,preferred_option

def verify(proposal,authority,*,retrieval_ids=frozenset()):
    result=original_verify(proposal,authority,retrieval_ids=retrieval_ids)
    if proposal.decision=='NO_RULE':return result
    preferred={}
    for source in SOURCES:
        rows=[r for r in authority.evidence.rows if r.structural.semantic.source_direction==source and r.structural.passes('train2') and preferred_option(r.options) is not None]
        if rows:preferred[source]=min(rows,key=lambda r:r.structural.rank()).structural.semantic
    issues=list(result.issues)
    for i,rule in enumerate(proposal.rules):
        expected=preferred.get(rule.semantic.source_direction)
        if expected is not None and rule.semantic!=expected and (i,'RULE_NOT_JUSTIFIED') not in issues:issues.append((i,'RULE_NOT_JUSTIFIED'))
    invalid={i for i,_ in issues if i>=0}
    return VerifierResultV1('NEEDS_REPAIR' if issues else 'ACCEPTED',tuple(issues),sum(i not in invalid for i in range(len(proposal.rules))))
