"""Provider-side semantic types only. No hidden authority, numeric policy or I/O."""
from dataclasses import asdict, dataclass
import re
from .exp03b_contract_v1 import (SemanticTupleV1, StructuralTupleEvidenceV1,
    SOURCES, TARGETS, HORIZONS, require, digest, encoded)


def validate_rows(rows):
    require(type(rows) is tuple and len(rows)==20 and all(type(r) is StructuralTupleEvidenceV1 for r in rows), 'SEMANTIC_ROWS_TYPE')
    require({r.semantic for r in rows}=={SemanticTupleV1(s,t,h) for s in SOURCES for t in TARGETS for h in HORIZONS}, 'SEMANTIC_UNIVERSE')
    require(len({r.evidence_slice_id for r in rows})==20 and all(re.fullmatch(r'EV-[0-9a-f]{24}',r.evidence_slice_id) for r in rows), 'EVIDENCE_IDENTITIES')


@dataclass(frozen=True)
class Train1SemanticEvidenceV2:
    candidate_id: str
    source: str
    target: str
    input_hash: str
    rows: tuple[StructuralTupleEvidenceV1,...]
    split: str='train1'
    def __post_init__(self):
        require(self.split=='train1','TRAIN1_SPLIT_TAINT'); validate_rows(self.rows)
        require(self.candidate_id=='EXP03B-CAND-'+digest({'source':self.source,'target':self.target})[:20], 'PAIR_IDENTITY')


@dataclass(frozen=True)
class SemanticRuleV2:
    semantic: SemanticTupleV1
    evidence_slice_ids: tuple[str,...]
    def __post_init__(self):
        require(type(self.semantic) is SemanticTupleV1, 'RULE_SEMANTIC_TYPE')
        require(type(self.evidence_slice_ids) is tuple and 1<=len(self.evidence_slice_ids)<=4 and all(type(x) is str and re.fullmatch(r'EV-[0-9a-f]{24}',x) for x in self.evidence_slice_ids), 'EVIDENCE_REFERENCE_INVALID')


@dataclass(frozen=True)
class SemanticProposalV2:
    decision: str
    rules: tuple[SemanticRuleV2,...]
    def __post_init__(self):
        require(self.decision in ('RULE_SET','NO_RULE') and type(self.rules) is tuple, 'PROPOSAL_SCHEMA')
        require((self.decision=='NO_RULE' and not self.rules) or (self.decision=='RULE_SET' and 1<=len(self.rules)<=2), 'RULE_SET_OVERCOMPLEX')
        require(all(type(r) is SemanticRuleV2 for r in self.rules), 'RULE_TYPE')
    def semantic_set(self):return tuple(sorted(r.semantic for r in self.rules))


def parse_proposal(value):
    require(type(value) is dict and set(value)=={'decision','rules'} and type(value['rules']) is list, 'PARSE_FAILURE')
    result=[]
    for row in value['rules']:
        require(type(row) is dict and set(row)=={'source_direction','target_direction','horizon_seconds','evidence_slice_ids'} and type(row['evidence_slice_ids']) is list, 'PARSE_FAILURE')
        result.append(SemanticRuleV2(SemanticTupleV1(row['source_direction'],row['target_direction'],row['horizon_seconds']),tuple(row['evidence_slice_ids'])))
    return SemanticProposalV2(value['decision'],tuple(result))


def proposal_document(p):
    require(type(p) is SemanticProposalV2,'SEMANTIC_PROPOSAL_REQUIRED')
    return {'decision':p.decision,'rules':[{**asdict(r.semantic),'evidence_slice_ids':list(r.evidence_slice_ids)} for r in p.rules]}


def t0(evidence):
    require(type(evidence) is Train1SemanticEvidenceV2,'T0_HIDDEN_AUTHORITY_PROHIBITED')
    result=[]
    for direction in SOURCES:
        choices=[r for r in evidence.rows if r.semantic.source_direction==direction and r.passes('train1')]
        if choices:
            row=min(choices,key=lambda r:r.rank())
            result.append(SemanticRuleV2(row.semantic,(row.evidence_slice_id,)))
    return SemanticProposalV2('RULE_SET' if result else 'NO_RULE',tuple(result))
