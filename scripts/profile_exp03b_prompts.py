"""Offline exact local serialization/token profile; no network/API/credential code."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import sys
from decimal import Decimal,ROUND_CEILING
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/".venv/exp03b-tokenizer"))
from paperworks.validation_v2.exp03b_contract_v1 import encoded,digest,require
from paperworks.validation_v2.exp03b_custody_v1 import seal,publish,replay
from paperworks.validation_v2.exp03b_prompt import request_body,execution_config,output_schema,SYSTEM_PROMPT,OUTPUT_CAP
PUBLIC=ROOT/"research_control_center/validation_v2/exp03b"
PRIVATE=ROOT/"artifacts/validation_v2/exp03b/private"


def profile(split):
    import tiktoken
    encoder=tiktoken.get_encoding("o200k_base")
    cohort=json.loads((PUBLIC/"EXP03B_COHORT_AUTHORITY_V1.json").read_text());replay(cohort)
    rows=[]
    for pair in cohort["pairs"]:
        identifier=pair["candidate_id"]
        if split=="train1":
            evidence=json.loads((PRIVATE/split/"provider"/(identifier+".json")).read_text())
            body=request_body(evidence);payload=encoded(body)
            publish(PRIVATE/split/"requests"/(identifier+".json"),body)
            rows.append({"candidate_id":identifier,"serialized_request_bytes":len(payload),"local_request_tokens":len(encoder.encode(payload.decode())),"request_hash":sha256(payload).hexdigest()})
        else:
            # No train1 payload is loaded in this process. Only allowed retrieval alternatives are profiled.
            e=json.loads((PRIVATE/split/"structural"/(identifier+".json")).read_text())
            tables=[{"split":"train2","dimension":"temporal_structure","alternatives":[r["structural"] for r in e["rows"]]}]
            tables.extend({"split":"train2","dimension":"numeric_option","alternatives":r["options"]} for r in e["rows"])
            sizes=[(len(encoded(t)),len(encoder.encode(encoded(t).decode()))) for t in tables]
            rows.append({"candidate_id":identifier,"maximum_retrieval_bytes":max(n for n,_ in sizes)+128,"maximum_retrieval_local_tokens":max(n for _,n in sizes)+128,"table_count":len(tables)})
    receipt=seal({"schema":"exp03b_offline_token_profile_v1","split":split,"tokenizer":"tiktoken==0.12.0","encoding":"o200k_base","profiles":rows,"provider_calls":0,"credential_reads":0,"capability_probes":0,"account_metering":"NOT_PROBED_LOCAL_SERIALIZATION_COUNTS_ONLY"})
    publish(PUBLIC/f"EXP03B_{split.upper()}_PROMPT_SIZE_PROFILE_V1.json",receipt)
    print(json.dumps({"status":"PASS","split":split,"profile_count":len(rows)}))


def finalize():
    a=json.loads((PUBLIC/"EXP03B_TRAIN1_PROMPT_SIZE_PROFILE_V1.json").read_text());b=json.loads((PUBLIC/"EXP03B_TRAIN2_PROMPT_SIZE_PROFILE_V1.json").read_text())
    replay(a);replay(b);one={r["candidate_id"]:r for r in a["profiles"]};two={r["candidate_id"]:r for r in b["profiles"]};require(set(one)==set(two) and bool(one),"PROFILE_COHORT")
    # UTF-8 byte ceilings conservatively dominate BPE text tokens. Explicit repair
    # limits and a separately reserved provider framing allowance are hard gates.
    repair_proposal_byte_cap=16384;feedback_byte_cap=8192;framing_allowance=4096
    caps={p:one[p]["serialized_request_bytes"]+two[p]["maximum_retrieval_bytes"]+repair_proposal_byte_cap+feedback_byte_cap+framing_allowance for p in one}
    calls=len(one)*3*7;input_cap=max(caps.values());output_cap=OUTPUT_CAP
    require(input_cap+output_cap<=400000,"PROMPT_CONTEXT_CAP")
    maximum_input=calls*input_cap;maximum_output=calls*output_cap
    cost=((Decimal(maximum_input)*Decimal("0.75")+Decimal(maximum_output)*Decimal("4.50"))/Decimal(1000000)).quantize(Decimal(".01"),rounding=ROUND_CEILING)
    config=execution_config()
    body={"schema":"exp03b_provider_budget_v1","status":"USER_DECISION_REQUIRED","model":config["model"],"N":len(one),"R":3,"T1_calls":len(one)*3,"T1B_calls":len(one)*9,"T2_calls":len(one)*9,"maximum_calls":calls,"input_tokens_per_call_cap":input_cap,"output_tokens_per_call_cap":output_cap,"maximum_input_tokens":maximum_input,"maximum_output_tokens":maximum_output,"maximum_total_tokens":maximum_input+maximum_output,"standard_api_cost_ceiling_usd":str(cost),"price_per_million":{"input":"0.75","output":"4.50"},"price_source":"https://developers.openai.com/api/docs/models/gpt-5.4-mini","cap_method":"UTF8_BYTE_BOUND_PLUS_EXPLICIT_REPAIR_AND_FRAMING_RESERVES","local_token_counts_not_server_metering":True,"repair_proposal_byte_cap":repair_proposal_byte_cap,"feedback_byte_cap":feedback_byte_cap,"framing_allowance":framing_allowance,"minimum_scheduled_calls_if_all_T2_accept_first":len(one)*3*5,"maximum_scheduled_calls":calls,"profile_hashes":[a["self_hash"],b["self_hash"]],"config":config,"config_hash":digest(config),"prompt_hash":digest(SYSTEM_PROMPT),"schema_hash":digest(output_schema()),"provider_calls":0,"credential_reads":0,"capability_probes":0,"prior_DG03_approval_inherited":False}
    publish(PUBLIC/"EXP03B_PROVIDER_BUDGET_V1.json",seal(body))
    publish(PUBLIC/"EXP03B_OUTPUT_SCHEMA_V1.json",output_schema())
    publish(PUBLIC/"EXP03B_PROMPT_FREEZE_V1.json",seal({"system_prompt":SYSTEM_PROMPT,"config":config,"output_schema":output_schema(),"implementation_hash":sha256((ROOT/"src/paperworks/validation_v2/exp03b_prompt.py").read_bytes()).hexdigest(),"request_profiles_hash":a["self_hash"]}))
    print(json.dumps({"status":"USER_DECISION_REQUIRED","calls":calls,"input_cap":maximum_input,"output_cap":maximum_output,"cost_usd":str(cost)}))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("phase",choices=("train1","train2","finalize"));args=p.parse_args()
    try:finalize() if args.phase=="finalize" else profile(args.phase)
    except Exception as e:
        print(json.dumps({"status":"PROFILE_FAIL_CLOSED","error_type":type(e).__name__}));raise SystemExit(2)
