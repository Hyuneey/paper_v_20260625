"""Prospective request serialization only. No transport or credential access."""
from .exp03b_contract_v1 import ALIASES, HORIZONS, SOURCES, TARGETS, require, encoded, digest
import re
from .exp03b_firewall_v1 import assert_clean

MODEL="gpt-5.4-mini-2026-03-17"
ENDPOINT="https://api.openai.com/v1/responses"
OUTPUT_CAP=2048
SYSTEM_PROMPT="""Infer a bounded relational Rule set for the fixed source-target pair from the supplied normal evidence only. Return only the JSON schema. RULE_SET contains at most one rule per source direction and at most two rules total; otherwise explicitly return NO_RULE. Source and target are bound externally. Do not invent variables, numeric thresholds, code, or causal claims.
Assess every provided source-direction, target-direction, horizon tuple. The proposal evidence criteria are isolated complete support >=5, consistency >=0.60, robust effect >=2.0, and consistency strictly greater than the opposite direction at that horizon. Rank supported tuples per source direction by greater consistency, greater effect, greater support, then smaller horizon. Numeric aliases are opaque options, not raw thresholds. Require materializable authority, zero system errors, at least5 formed opportunities, and no retention/opportunity/evaluation coverage loss versus NUM-000 for that same tuple. Prefer lower false-firing seconds/hour, episodes/hour, abstain rate, family complexity (NUM-000 first), then canonical alias order. Evidence columns expose all alternatives without a best marker. Cite applicable evidence_slice_ids for each proposed rule. STAT and GDN provide normal predictive evidence, never causal truth or hard acceptance authority. GDN attention is shared encoder evidence, not horizon-specific attention; null functional effect means graph-ineligible/unavailable, not zero. Do not infer absent evidence as support.
The hidden second-normal-file verifier uses support>=5, consistency>=0.60, effect>=1.0, strict opposite-direction competition, exact preferred horizon stability, same-file numeric preference and supported-source-direction completeness. This differs from the initial evidence effect>=2.0 proposal gate. When bounded feedback is supplied, use only its issue codes and authorized aggregate alternatives to revise the same pair. No unlisted data retrieval, provider tool calls, or fourth generation is permitted."""


def output_schema():
    rule={"type":"object","additionalProperties":False,"properties":{
        "source_direction":{"type":"string","enum":list(SOURCES)},"target_direction":{"type":"string","enum":list(TARGETS)},
        "horizon_seconds":{"type":"integer","enum":list(HORIZONS)},"numeric_policy_option_id":{"type":"string","enum":list(ALIASES)},
        "evidence_slice_ids":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":4}},
        "required":["source_direction","target_direction","horizon_seconds","numeric_policy_option_id","evidence_slice_ids"]}
    return {"type":"object","additionalProperties":False,"properties":{"decision":{"type":"string","enum":["RULE_SET","NO_RULE"]},"rules":{"type":"array","items":rule,"maxItems":2}},"required":["decision","rules"]}


def request_body(evidence:dict, *,repair:dict|None=None) -> dict:
    validate_projection(evidence)
    assert_clean(evidence)
    require(evidence.get("split")=="train1","INITIAL_PROMPT_SPLIT")
    content={"evidence":evidence}
    if repair is not None:
        require(set(repair)=={"previous_proposal","feedback","retrieval"},"REPAIR_ENVELOPE")
        validate_repair(repair)
        # Repair evidence is a separately authorized bounded train2 slice, never a hidden object.
        assert_clean(repair)
        content["repair"]=repair
    return {"model":MODEL,"instructions":SYSTEM_PROMPT,"input":encoded(content).decode(),"reasoning":{"effort":"none"},"temperature":.7,"top_p":1.,"max_output_tokens":OUTPUT_CAP,"store":False,"service_tier":"default","tools":[],"stream":False,"text":{"format":{"type":"json_schema","name":"exp03b_rule_set_v1","strict":True,"schema":output_schema()}}}


def execution_config():
    return {"model":MODEL,"endpoint":ENDPOINT,"reasoning":{"effort":"none"},"temperature":.7,"top_p":1.,"output_cap":OUTPUT_CAP,"timeout_seconds":60,"automatic_retries":0,"scientific_concurrency":1,"store":False,"service_tier":"default","tools":[],"seed":None,"repair_history":"LATEST_PROPOSAL_ONE_FEEDBACK_ONE_SLICE_STATELESS","T2_maximum_generations":3,"T2_early_stop":"IMMEDIATE_ACCEPTED_OR_NONREPAIRABLE_REJECTION","probe":"FIRST_SCHEDULED_CALL_COUNTS_TOWARD_BUDGET_NO_SEPARATE_SCIENTIFIC_CALL"}


def validate_projection(e):
    keys={"candidate_id","source","target","split","structural_columns","structural_rows","option_columns","option_rows","stat_association","gdn_columns","gdn_rows"}
    require(type(e) is dict and set(e)==keys,"CLOSED_PROVIDER_SCHEMA")
    require(re.fullmatch(r"EXP03B-CAND-[0-9a-f]{20}",e["candidate_id"]) is not None,"CANDIDATE_FORMAT")
    require(all(re.fullmatch(r"P1_[A-Z0-9]+",e[k]) for k in ("source","target")),"FEATURE_FORMAT")
    require(e["structural_columns"]==["source_direction","target_direction","horizon_seconds","support","consistency","opposite_consistency","effect","evidence_slice_id"],"STRUCTURAL_COLUMNS")
    require(e["option_columns"]==["structural_slice","alias","materializable","formed","PASS","FAIL","ABSTAIN","system_errors","false_seconds","false_episodes","exposure","evidence_slice_id"],"OPTION_COLUMNS")
    require(e["gdn_columns"]==["horizon","embedding","shared_encoder_attention","edge_relative_delta"],"GDN_COLUMNS")
    require(len(e["structural_rows"])==20 and len(e["option_rows"])==740 and len(e["gdn_rows"])==5,"EVIDENCE_TABLE_CLOSURE")
    require({tuple(r[:3]) for r in e["structural_rows"]}=={(s,t,h) for s in SOURCES for t in TARGETS for h in HORIZONS},"TUPLE_CLOSURE")
    require(all(len(r)==8 and type(r[3]) is int and r[3]>=0 and all(type(x) in (int,float) for x in r[4:7]) and re.fullmatch(r"EV-[0-9a-f]{24}",r[7]) for r in e["structural_rows"]),"STRUCTURAL_ROW")
    ids={r[7] for r in e["structural_rows"]}
    require(all(len(r)==12 and r[0] in ids and r[1] in ALIASES and type(r[2]) is bool and all(type(x) is int and x>=0 for x in r[3:11]) and re.fullmatch(r"EV-[0-9a-f]{24}",r[11]) for r in e["option_rows"]),"OPTION_ROW")
    require(len({(r[0],r[1]) for r in e["option_rows"]})==740,"OPTION_TABLE_DUPLICATES")
    require(all(len(r)==4 and r[0] in HORIZONS and all(x is None or type(x) in (int,float) for x in r[1:]) for r in e["gdn_rows"]),"GDN_ROW")


def validate_repair(r):
    from .exp03b_contract_v1 import parse_proposal
    parse_proposal(r["previous_proposal"])
    require(len(encoded(r["previous_proposal"]))<=16384,"REPAIR_PROPOSAL_BYTE_CAP")
    f=r["feedback"]
    require(type(f) is dict and set(f)=={"proposal_hash","issues","remaining_call_budget","evidence_retrieval_authorization"},"CLOSED_FEEDBACK_SCHEMA")
    require(f["proposal_hash"]==digest(r["previous_proposal"]) and f["remaining_call_budget"] in (1,2),"FEEDBACK_PROPOSAL_BINDING")
    codes={"LOW_SOURCE_SUPPORT","LOW_TARGET_CONSISTENCY","LOW_EFFECT","OPPOSITE_DIRECTION_COMPETES","HORIZON_UNSUPPORTED","HORIZON_UNSTABLE","RULE_NOT_JUSTIFIED","RULE_SET_INCOMPLETE","NO_RULE_NOT_JUSTIFIED","NUMERIC_OPTION_UNSUPPORTED","NUMERIC_OPTION_UNSTABLE","EVIDENCE_REFERENCE_INVALID","DUPLICATE_SOURCE_DIRECTION"}
    require(all(type(i) is dict and set(i)=={"failing_rule_index","issue_code"} and i["failing_rule_index"] in (-1,0,1) and i["issue_code"] in codes for i in f["issues"]),"FEEDBACK_ISSUE_SCHEMA")
    require(len(encoded(f))<=8192,"FEEDBACK_BYTE_CAP")
    q=r["retrieval"]
    if q is None:return
    require(type(q) is dict and set(q)=={"split","dimension","alternatives","retrieval_hash"} and q["split"]=="train2","CLOSED_RETRIEVAL_SCHEMA")
    require(q["retrieval_hash"]==digest({k:v for k,v in q.items() if k!="retrieval_hash"}),"RETRIEVAL_HASH")
    if q["dimension"]=="numeric_option":
        expected={"alias","materializable","formed","passed","failed","abstained","system_errors","false_seconds","false_episodes","exposure","evidence_slice_id"}
        require(len(q["alternatives"])==37 and tuple(v["alias"] for v in q["alternatives"])==ALIASES and all(set(v)==expected for v in q["alternatives"]),"RETRIEVAL_OPTION_SCHEMA")
    else:
        require(q["dimension"]=="temporal_structure" and len(q["alternatives"])==20,"RETRIEVAL_STRUCTURE_SCHEMA")
        require(all(set(v)=={"semantic","support","consistency","opposite_consistency","effect","evidence_slice_id"} and set(v["semantic"])=={"source_direction","target_direction","horizon_seconds"} for v in q["alternatives"]),"RETRIEVAL_STRUCTURE_FIELDS")
