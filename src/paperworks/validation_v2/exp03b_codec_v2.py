"""Offline, split-explicit migration of immutable normal evidence; no resampling."""
from .exp03b_semantic_v2 import Train1SemanticEvidenceV2, SemanticTupleV1, StructuralTupleEvidenceV1, require


def structural(document,split):
    require(document['split']==split and split in ('train1','train2'),'SPLIT_IDENTITY')
    rows=[]
    for r in document['rows']:
        # V1's file is already split-pure; discard its separate option census.
        s=r['structural'] if 'structural' in r else r
        rows.append(StructuralTupleEvidenceV1(SemanticTupleV1(**s['semantic']),**{k:v for k,v in s.items() if k!='semantic'}))
    cls=Train1SemanticEvidenceV2
    if split=='train2':
        from .exp03b_hidden_v2 import Train2SemanticEvidenceV2
        cls=Train2SemanticEvidenceV2
    return cls(document['candidate_id'],document['source'],document['target'],document['input_hash'],tuple(rows),split)
