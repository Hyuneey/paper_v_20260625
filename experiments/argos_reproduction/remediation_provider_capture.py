"""Receipt-first, no-retry provider capture for TASK-035AR slots."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any
import urllib.error

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from experiments.argos_reproduction.expanded_kpi_cohort import read_json, sha256_json, write_json
from experiments.argos_reproduction.multi_provider_capture import call_once, is_global_block
from experiments.argos_reproduction.remediation_slot_manifest import remediation_request_hash


class RemediationProviderError(RuntimeError): pass


def approval_blockers(config: dict[str,Any], approval: dict[str,Any], allow: bool) -> list[str]:
    blockers=[]
    checks={"approved":True,"provider":config["provider"]["provider"],"model":config["provider"]["model"],"maximum_requests":100,"maximum_requests_per_new_slot":1,"maximum_input_tokens_per_call":20000,"maximum_output_tokens_per_call":6000,"maximum_total_declared_input_tokens":2000000,"maximum_total_declared_output_tokens":600000,"automatic_retry":False,"manual_retry":False,"temperature_parameter_sent":False,"provider_seed_sent":False,"reasoning_parameter_added":False}
    for key,expected in checks.items():
        if approval.get(key)!=expected: blockers.append(f"{key}_invalid")
    if not allow: blockers.append("cli_allow_flag_missing")
    if not approval.get("approved_by") or not approval.get("approval_date"): blockers.append("approval_identity_missing")
    credential=approval.get("credential_env_var")
    if not credential or not os.environ.get(credential): blockers.append("credential_missing")
    return blockers


def capture_remediation(config_path: Path, *, allow_real_provider_call: bool) -> dict[str,Any]:
    config=read_json(config_path); approval=read_json(ROOT/config["provider"]["approval_path"]); blockers=approval_blockers(config,approval,allow_real_provider_call)
    if blockers: raise RemediationProviderError("TASK035AR_PROVIDER_PREFLIGHT_BLOCKED:"+",".join(blockers))
    manifest=read_json(ROOT/config["reports"]["requests"])
    if manifest["registered_slot_count"]!=100: raise RemediationProviderError("TASK035AR_SLOT_COUNT_INVALID")
    private=ROOT/config["private_root"]; outcomes=[]; global_block=False
    for index,slot in enumerate(manifest["slots"]):
        base={key:slot[key] for key in ("slot_id","kpi_id","anchor_id","replicate_id")}
        if global_block:
            outcomes.append({**base,"capture_status":"not_attempted_global_block"}); continue
        request_path=private/"requests"/slot["slot_id"]/"complete_request.json"; request=read_json(request_path)
        if sha256_json(request)!=slot["task035a_complete_prompt_hash"]:
            raise RemediationProviderError("TASK035AR_PROMPT_HASH_MISMATCH")
        if remediation_request_hash(slot["task035a_complete_prompt_hash"])!=slot["new_request_hash"]:
            raise RemediationProviderError("TASK035AR_REQUEST_HASH_MISMATCH")
        receipt=request_path.parent/"receipt.json"; response_dir=private/"responses"/slot["slot_id"]
        if receipt.exists(): raise RemediationProviderError("TASK035AR_SLOT_ALREADY_CONSUMED")
        write_json(receipt,{"remediation_slot_id":slot["slot_id"],"parent_anchor_id":slot["anchor_id"],"kpi_id":slot["kpi_id"],"replicate_id":slot["replicate_id"],"request_sha256":slot["new_request_hash"],"provider":approval["provider"],"model":approval["model"],"max_output_tokens":6000,"call_budget_consumed":True,"started_at":datetime.now(timezone.utc).isoformat()})
        response_dir.mkdir(parents=True,exist_ok=True)
        try:
            result=call_once(request,approval,int(config["provider"]["timeout_seconds"])); error=result["provider_error"] is not None or result["http_status_code"]>=400
            write_json(response_dir/("provider_error.json" if error else "raw_response.json"),result["raw_json"])
            if error: status="provider_error"; global_block=is_global_block(result)
            elif not result["raw_text"]: status="response_without_rule"
            else: status="provider_response_captured"
            if result["raw_text"]: (response_dir/"raw_response.md").write_bytes(result["raw_text"].encode("utf-8"))
            outcomes.append({**base,"capture_status":status,"http_status_code":result["http_status_code"],"response_sha256":hashlib.sha256(result["raw_text"].encode()).hexdigest() if result["raw_text"] else None,"provider_reported_model":result["model_reported"],"usage":result["usage"],"global_block":global_block})
        except (OSError,TimeoutError,urllib.error.URLError) as error:
            write_json(response_dir/"transport_error.json",{"error_type":type(error).__name__}); outcomes.append({**base,"capture_status":"transport_error"})
        if index+1<len(manifest["slots"]) and not global_block: time.sleep(float(config["provider"]["inter_call_delay_seconds"]))
    usages=[item.get("usage",{}) for item in outcomes]
    report={"schema_version":"1.0","task_id":"TASK-035AR","artifact_type":"remediation_provider_report","slots_registered":100,"requests_sent":sum(x["capture_status"]!="not_attempted_global_block" for x in outcomes),"non_empty_responses":sum(x["capture_status"]=="provider_response_captured" for x in outcomes),"empty_visible_responses":sum(x["capture_status"]=="response_without_rule" for x in outcomes),"provider_errors":sum(x["capture_status"]=="provider_error" for x in outcomes),"transport_errors":sum(x["capture_status"]=="transport_error" for x in outcomes),"unattempted_after_global_block":sum(x["capture_status"]=="not_attempted_global_block" for x in outcomes),"input_tokens_total":sum(int(u.get("input_tokens",0) or 0) for u in usages),"output_tokens_total":sum(int(u.get("output_tokens",0) or 0) for u in usages),"reasoning_tokens_total":sum(int((u.get("output_tokens_details") or {}).get("reasoning_tokens",0) or 0) for u in usages),"slots":outcomes,"automatic_retries":0,"repair_review_calls":0,"max_output_tokens":6000,"raw_responses_tracked":False}
    report["report_hash"]=sha256_json(report); write_json(ROOT/config["reports"]["provider"],report); return report


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--config",default="configs/argos_reproduction/task035ar_output_budget_remediation.json"); parser.add_argument("--allow-real-provider-call",action="store_true"); args=parser.parse_args(); report=capture_remediation((ROOT/args.config).resolve(),allow_real_provider_call=args.allow_real_provider_call); print(json.dumps({k:report[k] for k in ("requests_sent","non_empty_responses","provider_errors","transport_errors")})); return 0


if __name__=="__main__": raise SystemExit(main())
