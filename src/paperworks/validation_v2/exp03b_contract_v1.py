"""Prospective EXP03B types and user-approved SCI-01..04; no I/O."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from fractions import Fraction
from hashlib import sha256
import json
import math

SOURCES = ("step_up", "step_down")
TARGETS = ("increase", "decrease")
HORIZONS = (1, 5, 10, 30, 60)
ALIASES = tuple(f"NUM-{i:03d}" for i in range(37))


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: object) -> str:
    return sha256(encoded(value)).hexdigest()


@dataclass(frozen=True, order=True)
class SemanticTupleV1:
    source_direction: str
    target_direction: str
    horizon_seconds: int

    def __post_init__(self):
        require(self.source_direction in SOURCES and self.target_direction in TARGETS, "DIRECTION_INVALID")
        require(type(self.horizon_seconds) is int and self.horizon_seconds in HORIZONS, "HORIZON_INVALID")


@dataclass(frozen=True)
class StructuralTupleEvidenceV1:
    semantic: SemanticTupleV1
    support: int
    consistency: float
    opposite_consistency: float
    effect: float
    evidence_slice_id: str

    def __post_init__(self):
        require(type(self.semantic) is SemanticTupleV1, "SEMANTIC_TYPE")
        require(type(self.support) is int and self.support >= 0, "SUPPORT_INVALID")
        require(all(type(x) in (int,float) and math.isfinite(x) for x in (self.consistency,self.opposite_consistency,self.effect)), "NONFINITE_EVIDENCE")
        require(0 <= self.consistency <= 1 and 0 <= self.opposite_consistency <= 1 and self.effect >= 0, "EVIDENCE_RANGE")

    def passes(self, split: str) -> bool:
        require(split in ("train1", "train2"), "STRUCTURAL_SPLIT")
        return self.support >= 5 and self.consistency >= .60 and self.effect >= (2.0 if split == "train1" else 1.0) and self.consistency > self.opposite_consistency

    def rank(self):
        return (-self.consistency, -self.effect, -self.support, self.semantic.horizon_seconds)


@dataclass(frozen=True)
class OptionMetricsV1:
    alias: str
    materializable: bool
    formed: int
    passed: int
    failed: int
    abstained: int
    system_errors: int
    false_seconds: int
    false_episodes: int
    exposure: int
    evidence_slice_id: str

    def __post_init__(self):
        require(self.alias in ALIASES and type(self.materializable) is bool, "OPTION_ALIAS_OR_TYPE")
        counts=(self.formed,self.passed,self.failed,self.abstained,self.system_errors,self.false_seconds,self.false_episodes,self.exposure)
        require(all(type(v) is int and v>=0 for v in counts), "CENSUS_INVALID")
        require(self.formed==self.passed+self.failed+self.abstained+self.system_errors, "OPPORTUNITY_ACCOUNTING")
        require(self.false_seconds<=self.failed and self.false_episodes<=self.false_seconds and self.false_seconds<=self.exposure, "FALSE_CENSUS")
        require((self.failed==0)==(self.false_seconds==0) and (self.false_seconds==0)==(self.false_episodes==0), "FAIL_COORDINATE_CENSUS")

    @property
    def retention(self): return int(self.materializable)
    @property
    def opportunity_coverage(self): return int(self.materializable and self.formed>0)
    @property
    def evaluation_coverage(self):
        n=self.passed+self.failed+self.abstained
        return Fraction(self.passed+self.failed,n) if n else Fraction(0)
    @property
    def abstain_rate(self):
        n=self.passed+self.failed+self.abstained
        return Fraction(self.abstained,n) if n else Fraction(0)
    @property
    def complexity(self): return int(self.alias!="NUM-000")

    def burden(self, complexity=True):
        require(self.exposure>0,"EXPOSURE_INVALID")
        key=(Fraction(self.false_seconds*3600,self.exposure),Fraction(self.false_episodes*3600,self.exposure),self.abstain_rate)
        return key+(self.complexity,) if complexity else key

    def eligible(self, common):
        require(type(common) is OptionMetricsV1 and common.alias=="NUM-000" and self.exposure==common.exposure,"COMMON_COMPARATOR")
        return self.materializable and self.system_errors==0 and self.formed>=5 and self.exposure>0 and self.retention>=common.retention and self.opportunity_coverage>=common.opportunity_coverage and self.evaluation_coverage>=common.evaluation_coverage


def preferred_option(options: tuple[OptionMetricsV1,...]) -> OptionMetricsV1 | None:
    require(type(options) is tuple and len(options)==37 and tuple(x.alias for x in options)==ALIASES,"EXACT_37_OPTIONS")
    eligible=[x for x in options if x.eligible(options[0])]
    # Common is complexity0; frozen alias order resolves residual same-family ties.
    return min(eligible,key=lambda x:(x.burden(),x.alias)) if eligible else None


@dataclass(frozen=True)
class TupleEvidenceV1:
    structural: StructuralTupleEvidenceV1
    options: tuple[OptionMetricsV1,...]

    def __post_init__(self):
        require(type(self.structural) is StructuralTupleEvidenceV1,"STRUCTURAL_TYPE")
        require(type(self.options) is tuple and tuple(x.alias for x in self.options)==ALIASES,"OPTION_TABLE")


def validate_rows(rows):
    require(type(rows) is tuple and len(rows)==20 and all(type(r) is TupleEvidenceV1 for r in rows),"TUPLE_TABLE_TYPE")
    require({r.structural.semantic for r in rows}=={SemanticTupleV1(s,t,h) for s in SOURCES for t in TARGETS for h in HORIZONS},"EXACT_TUPLE_UNIVERSE")


@dataclass(frozen=True)
class Train1ProviderStructuralEvidenceV1:
    candidate_id: str
    source: str
    target: str
    input_hash: str
    rows: tuple[TupleEvidenceV1,...]
    split: str = "train1"
    def __post_init__(self):
        require(self.split=="train1","TRAIN1_SPLIT_TAINT"); validate_rows(self.rows)


@dataclass(frozen=True)
class Train2HiddenStructuralVerifierEvidenceV1:
    candidate_id: str
    source: str
    target: str
    input_hash: str
    rows: tuple[TupleEvidenceV1,...]
    split: str = "train2"
    def __post_init__(self):
        require(self.split=="train2","TRAIN2_SPLIT_TAINT"); validate_rows(self.rows)


@dataclass(frozen=True)
class ProposedRuleV1:
    semantic: SemanticTupleV1
    numeric_policy_option_id: str
    evidence_slice_ids: tuple[str,...]
    def __post_init__(self):
        require(type(self.semantic) is SemanticTupleV1,"RULE_SEMANTIC_TYPE")
        require(self.numeric_policy_option_id in ALIASES,"NUMERIC_OPTION_UNSUPPORTED")
        require(type(self.evidence_slice_ids) is tuple and 0<len(self.evidence_slice_ids)<=4 and all(type(x) is str and x.startswith("EV-") for x in self.evidence_slice_ids),"EVIDENCE_REFERENCE_INVALID")


@dataclass(frozen=True)
class ProposalV1:
    decision: str
    rules: tuple[ProposedRuleV1,...]
    def __post_init__(self):
        require(self.decision in ("RULE_SET","NO_RULE") and type(self.rules) is tuple,"PROPOSAL_SCHEMA")
        require((self.decision=="NO_RULE" and len(self.rules)==0) or (self.decision=="RULE_SET" and 1<=len(self.rules)<=2),"RULE_SET_OVERCOMPLEX")
        require(all(type(r) is ProposedRuleV1 for r in self.rules),"RULE_TYPE")

    def semantic_set(self): return tuple(sorted(r.semantic for r in self.rules))
    def execution_set(self): return tuple(sorted((r.semantic,r.numeric_policy_option_id) for r in self.rules))


def parse_proposal(value: dict) -> ProposalV1:
    require(type(value) is dict and set(value)=={"decision","rules"} and type(value["rules"]) is list,"PARSE_FAILURE")
    rules=[]
    for row in value["rules"]:
        require(type(row) is dict and set(row)=={"source_direction","target_direction","horizon_seconds","numeric_policy_option_id","evidence_slice_ids"},"PARSE_FAILURE")
        require(type(row["evidence_slice_ids"]) is list,"PARSE_FAILURE")
        rules.append(ProposedRuleV1(SemanticTupleV1(row["source_direction"],row["target_direction"],row["horizon_seconds"]),row["numeric_policy_option_id"],tuple(row["evidence_slice_ids"])))
    return ProposalV1(value["decision"],tuple(rules))


def proposal_document(p: ProposalV1) -> dict:
    return {"decision":p.decision,"rules":[{**asdict(r.semantic),"numeric_policy_option_id":r.numeric_policy_option_id,"evidence_slice_ids":list(r.evidence_slice_ids)} for r in p.rules]}


def t0(evidence: Train1ProviderStructuralEvidenceV1) -> ProposalV1:
    require(type(evidence) is Train1ProviderStructuralEvidenceV1,"T0_HIDDEN_AUTHORITY_PROHIBITED")
    result=[]
    for source_direction in SOURCES:
        rows=[r for r in evidence.rows if r.structural.semantic.source_direction==source_direction and r.structural.passes("train1")]
        # Structural choice first, then same-tuple eligible option; do not search hidden data.
        if rows:
            chosen=min(rows,key=lambda r:r.structural.rank())
            option=preferred_option(chosen.options)
            if option:
                result.append(ProposedRuleV1(chosen.structural.semantic,option.alias,(chosen.structural.evidence_slice_id,option.evidence_slice_id)))
    return ProposalV1("RULE_SET" if result else "NO_RULE",tuple(result))
