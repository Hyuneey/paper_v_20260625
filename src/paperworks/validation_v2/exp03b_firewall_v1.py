"""Closed train1 projection. This module has no hidden-authority or I/O imports."""
from dataclasses import dataclass
import math
import re
from .exp03b_contract_v1 import Train1ProviderStructuralEvidenceV1, require, encoded, digest

DENIED = ("test1", "test2", "heldout", "held-out", "train3", "train4", "selected_policy", "selected_horizon", "confirmed", "descriptor_hash", "rule_id", "relation_id", "meta_tier", "meta_rank", "manual_text", "detector", "fusion", "api_key", "credential", "private_roles")


@dataclass(frozen=True)
class SplitPurePredictiveEvidenceV1:
    split: str
    candidate_id: str
    authority_hash: str
    stat_association: float
    gdn_rows: tuple[tuple[int, float, float, float | None], ...]
    # horizon, embedding, shared-encoder attention, fixed-edge relative delta
    def __post_init__(self):
        require(self.split in ("train1", "train2"), "GDN_SPLIT_TAINT")
        require(len(self.authority_hash)==64, "GDN_CUSTODY_HASH")
        require(math.isfinite(self.stat_association), "STAT_NONFINITE")
        require(tuple(r[0] for r in self.gdn_rows)==(1,5,10,30,60), "GDN_HORIZONS")
        require(all(len(r)==4 and all(v is None or math.isfinite(v) for v in r[1:]) for r in self.gdn_rows), "GDN_NONFINITE")


@dataclass(frozen=True)
class ProviderTrain1EvidencePackV1:
    candidate_id: str
    source: str
    target: str
    structural_rows: tuple
    option_rows: tuple
    stat_association: float
    gdn_rows: tuple
    evidence_hash: str


def assert_clean(document: object, *, forbidden_identities: tuple[str,...]=()) -> None:
    text=encoded(document).decode().lower()
    require(not any(x in text for x in DENIED), "PROVIDER_FIELD_TAINT")
    require(not re.search(r"[a-z]:\\\\|/users/|/home/|sk-[a-z0-9]",text), "PROVIDER_PATH_OR_SECRET_TAINT")
    require(not any(x.lower() in text for x in forbidden_identities if x), "PROVIDER_ANSWER_IDENTITY_TAINT")


def project(train1: Train1ProviderStructuralEvidenceV1, predictive: SplitPurePredictiveEvidenceV1) -> ProviderTrain1EvidencePackV1:
    require(type(train1) is Train1ProviderStructuralEvidenceV1 and type(predictive) is SplitPurePredictiveEvidenceV1, "PROVIDER_TYPE_FIREWALL")
    require(predictive.split=="train1" and predictive.candidate_id==train1.candidate_id, "PROVIDER_SPLIT_FIREWALL")
    structure=[];options=[]
    for row in train1.rows:
        s=row.structural;t=s.semantic
        structure.append((t.source_direction,t.target_direction,t.horizon_seconds,s.support,s.consistency,s.opposite_consistency,s.effect,s.evidence_slice_id))
        for o in row.options:
            # All aliases including unavailable ones; no recommendation/eligibility flag.
            options.append((s.evidence_slice_id,o.alias,o.materializable,o.formed,o.passed,o.failed,o.abstained,o.system_errors,o.false_seconds,o.false_episodes,o.exposure,o.evidence_slice_id))
    body={"candidate_id":train1.candidate_id,"source":train1.source,"target":train1.target,"structural_rows":tuple(structure),"option_rows":tuple(options),"stat_association":predictive.stat_association,"gdn_rows":predictive.gdn_rows}
    assert_clean(body)
    return ProviderTrain1EvidencePackV1(**body,evidence_hash=digest(body))


def render(pack: ProviderTrain1EvidencePackV1) -> dict:
    require(type(pack) is ProviderTrain1EvidencePackV1, "PROMPT_HIDDEN_OBJECT_REJECTED")
    body={"candidate_id":pack.candidate_id,"source":pack.source,"target":pack.target,"split":"train1","structural_columns":["source_direction","target_direction","horizon_seconds","support","consistency","opposite_consistency","effect","evidence_slice_id"],"structural_rows":pack.structural_rows,"option_columns":["structural_slice","alias","materializable","formed","PASS","FAIL","ABSTAIN","system_errors","false_seconds","false_episodes","exposure","evidence_slice_id"],"option_rows":pack.option_rows,"stat_association":pack.stat_association,"gdn_columns":["horizon","embedding","shared_encoder_attention","edge_relative_delta"],"gdn_rows":pack.gdn_rows}
    assert_clean(body)
    return body
