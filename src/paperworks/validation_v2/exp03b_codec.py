"""Closed authority decoding. Callers keep train1 and train2 files separate."""
from .exp03b_contract_v1 import (SemanticTupleV1,StructuralTupleEvidenceV1,OptionMetricsV1,TupleEvidenceV1,Train1ProviderStructuralEvidenceV1,Train2HiddenStructuralVerifierEvidenceV1,require)


def structural(document:dict,split:str):
    require(split in ("train1","train2") and document.get("split")==split,"DECODE_SPLIT")
    require(set(document)=={"candidate_id","source","target","input_hash","rows","split"},"DECODE_CLOSED_SCHEMA")
    rows=[]
    for row in document["rows"]:
        require(set(row)=={"structural","options"},"DECODE_ROW_SCHEMA")
        s=dict(row["structural"]);s["semantic"]=SemanticTupleV1(**s["semantic"])
        rows.append(TupleEvidenceV1(StructuralTupleEvidenceV1(**s),tuple(OptionMetricsV1(**o) for o in row["options"])))
    kind=Train1ProviderStructuralEvidenceV1 if split=="train1" else Train2HiddenStructuralVerifierEvidenceV1
    return kind(document["candidate_id"],document["source"],document["target"],document["input_hash"],tuple(rows))
