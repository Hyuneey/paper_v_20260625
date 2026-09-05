"""Freeze the approved XVER T2 transport source and user decision, offline."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from xver_execution_common import ROOT, PUB, document, committed, head, publish, seal, require, digest, sha256_file, version_authorities
from paperworks.validation_v2.xver_provider_execution_v1 import COMBINED_LIMITS, EXPECTED_BUDGET_HASHES, VERSIONS


PUBLIC = PUB / "provider_execution_v1"
BASELINE = "be3ff48bd2abfafc81544357af0daff69a6721a2"
IMPLEMENTATION = (
    "scripts/execute_xver_t2_provider_v1.py",
    "scripts/finalize_xver_t2_provider_v1.py",
    "src/paperworks/validation_v2/xver_provider_execution_v1.py",
    "src/paperworks/validation_v2/xver_t2_closure_v1.py",
    "src/paperworks/validation_v2/xver_prompt_v1.py",
    "src/paperworks/validation_v2/exp03b_prompt_v2.py",
    "src/paperworks/validation_v2/exp03b_hidden_v2.py",
    "src/paperworks/validation_v2/exp03b_execution_v2.py",
    "src/paperworks/validation_v2/exp03b_conversion.py",
    "src/paperworks/validation_v2/exp03b_evaluation.py",
    "tests/test_xver_provider_execution_v1.py",
)


def main() -> None:
    source_commit = head()
    require(subprocess.run(["git", "merge-base", "--is-ancestor", BASELINE, source_commit], cwd=ROOT).returncode == 0, "SOURCE_BASELINE_ANCESTRY")
    require(not subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True).strip(), "TRACKED_WORKTREE_NOT_CLEAN")
    hashes = {}
    for relative in IMPLEMENTATION:
        committed(ROOT / relative)
        hashes[relative] = sha256_file(ROOT / relative)
    budgets = {v: document(PUB / f"HAI{v[:2]}_T2_PROVIDER_BUDGET_V1.json") for v in VERSIONS}
    profiles = {v: document(PUB / f"HAI{v[:2]}_T2_TOKEN_PROFILE_V1.json") for v in VERSIONS}
    require({v: budgets[v]["self_hash"] for v in VERSIONS} == EXPECTED_BUDGET_HASHES, "BUDGET_AUTHORITY_MISMATCH")
    require(all(profiles[v]["self_hash"] == budgets[v]["profile_hash"] for v in VERSIONS), "TOKEN_PROFILE_CHANGED")
    serializer = document(PUB / "XVER_PROVIDER_SERIALIZER_FREEZE_V1.json")
    qa = document(PUB / "INDEPENDENT_EXECUTION_QA_V1.json")
    semantic = document(PUB / "SEMANTIC_EXECUTION_AUTHORITY_V1.json")
    gdn = document(PUB / "GDN_EXECUTION_AUTHORITY_V2.json")
    candidates = {v: version_authorities(v)[1] for v in VERSIONS}
    freeze = seal({
        "schema": "xver_t2_provider_execution_freeze_v1",
        "status": "APPROVED_PRETRANSPORT_SOURCE_FROZEN",
        "task": "XVER-T2-PROVIDER-EXEC-001",
        "integration_baseline": BASELINE,
        "execution_source_commit": source_commit,
        "implementation_hashes": hashes,
        "implementation_bundle_hash": digest(hashes),
        "budget_hashes": {v: budgets[v]["self_hash"] for v in VERSIONS},
        "profile_hashes": {v: profiles[v]["self_hash"] for v in VERSIONS},
        "serializer_hash": serializer["self_hash"],
        "prompt_hash": serializer["system_prompt_hash"],
        "schema_hash": serializer["schema_hash"],
        "config_hash": serializer["configuration_hash"],
        "preexecution_QA_hash": qa["self_hash"],
        "semantic_execution_hash": semantic["self_hash"],
        "GDN_execution_hash": gdn["self_hash"],
        "candidate_hashes": {v: candidates[v]["self_hash"] for v in VERSIONS},
        "evidence_hashes": {v: budgets[v]["evidence_hash"] for v in VERSIONS},
        "first_call_receipt_probe": "FIRST_SCHEDULED_HAI22_CALL",
        "retry": 0,
        "fallback": False,
        "concurrency": 1,
        "event_evidence_transmission": False,
        "attack_access": False,
    })
    publish(PUBLIC / "XVER_T2_PROVIDER_EXECUTION_FREEZE_V2.json", freeze)
    approval = seal({
        "schema": "xver_t2_provider_user_approval_receipt_v1",
        "task": "XVER-T2-PROVIDER-EXEC-001",
        "gate": "DG-XVER-PROVIDER",
        "status": "APPROVED",
        "decision_date": "2026-09-05",
        "timezone": "Asia/Seoul",
        "integration_baseline": BASELINE,
        "execution_freeze_hash": freeze["self_hash"],
        "model": "gpt-5.4-mini-2026-03-17",
        "endpoint": "Responses API",
        "budget_hashes": {v: budgets[v]["self_hash"] for v in VERSIONS},
        "combined_limits": COMBINED_LIMITS,
        "retry": 0,
        "concurrency": 1,
        "provider_tools": False,
        "fallback": False,
        "event_evidence": False,
        "attack_access": False,
        "scope": "NORMAL_ONLY_T2_SEMANTIC_RULE_INDUCTION",
    })
    publish(PUBLIC / "XVER_T2_PROVIDER_APPROVAL_RECEIPT_V2.json", approval)
    print(json.dumps({"status": "APPROVAL_AND_EXECUTION_SOURCE_FROZEN", "freeze_hash": freeze["self_hash"], "approval_hash": approval["self_hash"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "BLOCKED_PROVIDER_AUTHORITY_REPLAY", "error_type": type(error).__name__, "code": str(error)}))
        raise SystemExit(2)
