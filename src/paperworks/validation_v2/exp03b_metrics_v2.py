"""SCI04 semantic majority, unchanged no-vote/failure behavior."""
from collections import Counter
from .exp03b_semantic_v2 import SemanticProposalV2, require
from .exp03b_metrics_v1 import strict_metrics, exact_repair, portfolio_repeat, disposition


def majority(outputs, *, decision_only=False):
    require(len(outputs)==3,'THREE_REPEATS_REQUIRED')
    valid=[x for x in outputs if x is not None]
    require(all(type(x) is SemanticProposalV2 for x in valid),'ADMITTED_OUTPUT_TYPE')
    if not valid:return 'NO_VALID_OUTPUT',None
    keys=[x.decision if decision_only else x.semantic_set() for x in valid]
    for key,count in Counter(keys).items():
        if count>=2:return 'MAJORITY',key
    return 'NO_MAJORITY',None
