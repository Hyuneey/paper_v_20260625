"""Closed semantic train1 projection; no hidden-authority or numeric/I/O imports."""
from dataclasses import dataclass
from .exp03b_semantic_v2 import Train1SemanticEvidenceV2, require, encoded, digest
from .exp03b_firewall_v1 import SplitPurePredictiveEvidenceV1, assert_clean as old_clean

DENIED=('numeric','option_','num-','relation_specific_normal_only','common_fixed_normalized','n7-q0.90-s2-f0.05','best_option')


def assert_clean(document, *, forbidden_identities=()):
    old_clean(document,forbidden_identities=forbidden_identities)
    text=encoded(document).decode().lower()
    require(not any(x in text for x in DENIED),'NUMERIC_PROVIDER_TAINT')


@dataclass(frozen=True)
class ProviderTrain1EvidencePackV2:
    candidate_id:str
    source:str
    target:str
    structural_rows:tuple
    stat_association:float
    gdn_rows:tuple
    evidence_hash:str


def project(train1,predictive):
    require(type(train1) is Train1SemanticEvidenceV2 and type(predictive) is SplitPurePredictiveEvidenceV1,'PROVIDER_TYPE_FIREWALL')
    require(predictive.split=='train1' and predictive.candidate_id==train1.candidate_id,'PROVIDER_SPLIT_FIREWALL')
    rows=tuple((r.semantic.source_direction,r.semantic.target_direction,r.semantic.horizon_seconds,r.support,r.consistency,r.opposite_consistency,r.effect,r.evidence_slice_id) for r in train1.rows)
    body={'candidate_id':train1.candidate_id,'source':train1.source,'target':train1.target,'structural_rows':rows,'stat_association':predictive.stat_association,'gdn_rows':predictive.gdn_rows}
    assert_clean(body)
    return ProviderTrain1EvidencePackV2(**body,evidence_hash=digest(body))


STRUCTURAL_COLUMNS=['source_direction','target_direction','horizon_seconds','support','consistency','opposite_consistency','effect','evidence_slice_id']
GDN_COLUMNS=['horizon','embedding','shared_encoder_attention','edge_relative_delta']


def render(pack):
    require(type(pack) is ProviderTrain1EvidencePackV2,'PROMPT_HIDDEN_OBJECT_REJECTED')
    body={'candidate_id':pack.candidate_id,'source':pack.source,'target':pack.target,'split':'train1','structural_columns':STRUCTURAL_COLUMNS,'structural_rows':pack.structural_rows,'stat_association':pack.stat_association,'gdn_columns':GDN_COLUMNS,'gdn_rows':pack.gdn_rows}
    assert_clean(body)
    return body
