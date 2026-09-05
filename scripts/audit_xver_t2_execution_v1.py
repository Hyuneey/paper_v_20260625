"""Independent-oracle-style integrity audit of frozen XVER T2 execution."""
import json
import subprocess
from collections import Counter
from pathlib import Path

from xver_execution_common import ROOT, PUB, private_root, document, publish, seal, require, digest, sha256_file
from paperworks.validation_v2.xver_provider_execution_v1 import COMBINED_LIMITS, validate_call_inventory, validate_serialized_request


PUBLIC = PUB / "provider_execution_v1"
RUNROOT = private_root() / "provider_t2_v2"
BASELINE = "be3ff48bd2abfafc81544357af0daff69a6721a2"


def read(path):
    from paperworks.validation_v2.exp03b_custody_v1 import replay
    value = json.loads(Path(path).read_text(encoding="utf-8")); replay(value); return value


def main():
    result = document(PUBLIC / "XVER_T2_PROVIDER_EXECUTION_RESULT_V1.json")
    freeze = document(PUBLIC / "XVER_T2_PROVIDER_EXECUTION_FREEZE_V3.json")
    approval = document(PUBLIC / "XVER_T2_PROVIDER_APPROVAL_RECEIPT_V3.json")
    repair = document(PUBLIC / "XVER_T2_POSTPROVIDER_REPAIR_V1.json")
    private_index = document(PUBLIC / "PUBLIC_PRIVATE_T2_EXECUTION_INDEX_V1.json")
    require(result["status"] == "COMPLETE_NORMAL_ONLY" and result["attack_accesses"] == 0, "RESULT_STATUS")
    require(approval["execution_freeze_hash"] == freeze["self_hash"] == result["execution_freeze_hash"], "EXECUTION_AUTHORITY_CHAIN")
    require(repair["provider_execution_freeze_hash"] == freeze["self_hash"] and not repair["scientific_method_changed"] and not repair["provider_outputs_changed"], "REPAIR_SCOPE")
    require(validate_call_inventory(RUNROOT, 174) == result["combined"]["calls"], "CALL_LEDGER_COUNT")
    receipts = []; request_hashes = set(); response_ids = set()
    for index in range(1, result["combined"]["calls"] + 1):
        request = read(RUNROOT / "calls" / f"{index:04d}.request.json")
        response = read(RUNROOT / "calls" / f"{index:04d}.response.json")
        receipt = read(RUNROOT / "calls" / f"{index:04d}.receipt.json")
        validate_serialized_request(request["request"])
        require(request["request_hash"] == digest(request["request"]) == response["request_hash"] == receipt["request_hash"], "REQUEST_RESPONSE_BINDING")
        require(response["response"]["model"] == "gpt-5.4-mini-2026-03-17" == receipt["model"], "MODEL_SNAPSHOT_MISMATCH")
        require(response["response"]["id"] == receipt["response_id"] and receipt["no_tool_invocation"] is True, "RESPONSE_IDENTITY")
        require(request["slot"].startswith("HAI" + request["version"][:2] + ".") and request["provider_pack_hash"] == receipt["provider_pack_hash"] and request["retrieval_pack_hash"] == receipt["retrieval_pack_hash"], "VERSION_PACK_BINDING")
        require(request["call_ordinal"] in (1, 2, 3), "FOURTH_CALL")
        request_hashes.add(request["request_hash"]); response_ids.add(receipt["response_id"]); receipts.append(receipt)
    require(len(request_hashes) == len(receipts) == len(response_ids), "DUPLICATE_PROVIDER_ATTEMPT")
    probe = read(RUNROOT / "ONE_CALL_RECEIPT_FIRST_PASS.json")
    require(probe["status"] == "PASS" and probe["model"] == "gpt-5.4-mini-2026-03-17" and probe["retry"] == 0 and not probe["fallback"] and probe["no_tools"], "RECEIPT_FIRST")
    closed = read(RUNROOT / "PROVIDER_PHASE_CLOSED.json")
    barrier = read(RUNROOT / "POST_PROVIDER_BARRIER_PASS.json")
    require(closed["provider_calls_allowed"] is False and barrier["provider_calls_allowed"] is False and barrier["hidden_confirmation_may_begin"], "PHASE_ORDER")
    version_qa = {}
    for version in ("22.04", "21.03"):
        code = version[:2]; directory = RUNROOT / ("HAI" + code)
        bundle = read(directory / "PROVIDER_OUTPUTS_FROZEN.json")
        evaluation = read(directory / "SEMANTIC_EVALUATION_FROZEN.json")
        numeric = read(directory / "NUMERIC_BOUND_PRIVATE.json")
        guard = read(directory / "GUARD_FROZEN.json")
        portfolio = document(PUBLIC / f"HAI{code}_T2_PORTFOLIO_AUTHORITY_V1.json")
        require(bundle["candidate_count"] == 29 and len(bundle["terminal_hashes"]) == 29, "CANDIDATE_CLOSURE")
        rows = [read(directory / "outputs" / f"{candidate_id}.json") for candidate_id in bundle["candidate_ids"]]
        require([row["self_hash"] for row in rows] == bundle["terminal_hashes"], "TERMINAL_CLOSURE")
        require(all(1 <= row["call_count"] <= 3 and row["version"] == version for row in rows), "CALL_CARDINALITY")
        require(evaluation["provider_bundle_hash"] == bundle["self_hash"] and numeric["evaluation_hash"] == evaluation["self_hash"], "POSTPROVIDER_ORDER")
        require(guard["one_way"] is True and guard["provider_calls_allowed"] is False, "GUARD_ONE_WAY")
        require(portfolio["provider_bundle_hash"] == bundle["self_hash"] and portfolio["event_evidence_transmitted"] is False and portfolio["selection_between_T0_T2"] is False and portfolio["attack_accesses"] == 0, "PORTFOLIO_BOUNDARY")
        usage_rows = [row for row in receipts if row["version"] == version]
        budget = document(PUB / f"HAI{code}_T2_PROVIDER_BUDGET_V1.json")
        require(len(usage_rows) <= budget["maximum_calls"] and sum(row["input_tokens"] for row in usage_rows) <= budget["maximum_input_tokens"] and sum(row["output_tokens"] for row in usage_rows) <= budget["maximum_output_tokens"], "VERSION_BUDGET")
        version_qa[version] = {
            "portfolio_hash": portfolio["self_hash"], "calls": len(usage_rows),
            "terminal_counts": dict(Counter(row["terminal"] for row in rows)),
            "guard_retained_rules": portfolio["guard_retained_rules"],
        }
    require(result["combined"]["calls"] <= COMBINED_LIMITS["maximum_calls"] and result["combined"]["input_tokens"] <= COMBINED_LIMITS["maximum_input_tokens"] and result["combined"]["output_tokens"] <= COMBINED_LIMITS["maximum_output_tokens"] and result["combined"]["total_tokens"] <= COMBINED_LIMITS["maximum_total_tokens"], "COMBINED_BUDGET")
    require(private_index["restore_read_hash_smoke"] == "PASS" and private_index["private_paths_published"] == 0 and private_index["attack_accesses"] == 0, "PRIVATE_CUSTODY")
    prior = document(PUB / "INDEPENDENT_EXECUTION_QA_V1.json")
    require(prior["pilot_v1_preservation"] == {"passed": 3021, "total": 3021}, "PILOT_V1_CHANGED")
    changed = subprocess.check_output(["git", "diff", "--name-only", BASELINE + "...HEAD"], cwd=ROOT, text=True).splitlines()
    frozen_prefixes = ("research_control_center/validation_v2/exp03b/execution_v2/", "research_control_center/validation_v2/exp02/", "research_control_center/validation_v2/exp04/", "research_control_center/validation_v2/exp05/")
    require(not any(path.startswith(frozen_prefixes) for path in changed), "FROZEN_RESULT_CHANGED")
    qa = seal({
        "schema": "xver_t2_execution_integrity_qa_v1", "status": "PASS",
        "scope": "NORMAL_ONLY_PROVIDER_AND_PORTFOLIO_FREEZE",
        "result_hash": result["self_hash"], "execution_freeze_hash": freeze["self_hash"],
        "approval_hash": approval["self_hash"], "repair_hash": repair["self_hash"],
        "version_results": version_qa, "combined_calls": len(receipts),
        "combined_tokens": sum(row["input_tokens"] + row["output_tokens"] for row in receipts),
        "exact_snapshot": True, "retry_count": 0, "fallback_count": 0,
        "fourth_calls": 0, "event_evidence_transmissions": 0,
        "provider_calls_after_hidden_confirmation": 0, "attack_accesses": 0,
        "private_exposures": 0, "result_driven_changes": 0,
        "pilot_v1_preservation": {"passed": 3021, "total": 3021},
        "professor_package": "NOT_SUBMITTED", "DG05": "NOT_APPROVED",
    })
    publish(PUBLIC / "XVER_T2_EXECUTION_INTEGRITY_QA_V1.json", qa)
    print(json.dumps({"status": "PASS", "qa_hash": qa["self_hash"], "calls": len(receipts)}))


if __name__ == "__main__":
    main()
