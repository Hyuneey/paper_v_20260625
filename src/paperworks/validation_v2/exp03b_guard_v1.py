"""One-way hidden train4 guard and file-local portfolio aggregation."""
from dataclasses import dataclass
from fractions import Fraction
from .exp03b_contract_v1 import OptionMetricsV1, require


@dataclass(frozen=True)
class Train4HiddenGuardAuthorityV1:
    split_hash: str
    file_id: str
    exposure: int
    def __post_init__(self): require(type(self.exposure) is int and self.exposure>0,"EXPOSURE_INVALID")


def guard(candidate: OptionMetricsV1, common: OptionMetricsV1) -> str:
    require(type(candidate) is OptionMetricsV1 and type(common) is OptionMetricsV1 and common.alias=="NUM-000","GUARD_TYPES")
    require(candidate.exposure==common.exposure,"GUARD_EXPOSURE_MISMATCH")
    if candidate.system_errors or common.system_errors: return "TRAIN4_SYSTEM_ERROR"
    if candidate.formed<5 or common.formed<5 or candidate.exposure<=0 or not candidate.materializable or not common.materializable: return "TRAIN4_GUARD_UNDEROBSERVED"
    if candidate.retention<common.retention or candidate.opportunity_coverage<common.opportunity_coverage or candidate.evaluation_coverage<common.evaluation_coverage: return "TRAIN4_COVERAGE_REGRESSION"
    if candidate.burden()>common.burden(): return "TRAIN4_NORMAL_BURDEN_REGRESSION"
    return "RETAINED"


def retention_state(statuses: tuple[str,...]) -> str:
    require(1<=len(statuses)<=2,"GUARD_RULE_COUNT")
    n=statuses.count("RETAINED")
    return "FULLY_RETAINED_RULE_SET" if n==len(statuses) else "PARTIALLY_RETAINED_RULE_SET" if n else "NO_RULE_AFTER_GUARD"


def portfolio_census(rules: tuple[tuple[str,tuple[int,...],int,int,int],...], exposure_by_file: dict[str,int]) -> dict:
    require(bool(exposure_by_file) and all(type(n) is int and n>0 for n in exposure_by_file.values()),"PORTFOLIO_EXPOSURE")
    union=set(); passed=failed=abstained=0
    for file_id,seconds,p,f,a in rules:
        require(file_id in exposure_by_file and all(type(x) is int and 0<=x<exposure_by_file[file_id] for x in seconds),"ROW_OUTSIDE_FILE")
        require(all(type(x) is int and x>=0 for x in (p,f,a)) and len(set(seconds))<=f,"OPPORTUNITY_COUNTS")
        require((f==0)==(len(set(seconds))==0),"FAIL_COORDINATES_MISSING")
        union.update((file_id,x) for x in seconds); passed+=p;failed+=f;abstained+=a
    episodes=sum((file_id,row-1) not in union for file_id,row in union)
    exposure=sum(exposure_by_file.values()); opportunities=passed+failed+abstained
    return {"false_seconds":len(union),"false_episodes":episodes,"exposure":exposure,"PASS":passed,"FAIL":failed,"ABSTAIN":abstained,"burden":(Fraction(3600*len(union),exposure),Fraction(3600*episodes,exposure),Fraction(abstained,opportunities) if opportunities else None),"abstain_defined":opportunities>0}
