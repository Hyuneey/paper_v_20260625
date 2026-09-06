"""Synchronize public-safe RCC records for the unapproved DG05 V10 release."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RCC = ROOT / "research_control_center"
REG = RCC / "registry"
V10 = RCC / "validation_v2/dg05_v10_release"
BRANCH = "validation-v2-dg05-v4-route-upstream-lineage-closure-001"
IMPLEMENTATION_COMMIT = "5f3a4218382dfbb8e1b74bfb35a3b5aaea51c9cd"
CANDIDATE_COMMIT = "18ca8c6487a7f16da0067c0a825c44463be73710"
FINAL_COMMIT = "035e02c90b2a5a160dd83781f98e78c4d5877514"
V4_FINAL_COMMIT = "06ed9fbc20c6c4bd71cf734f7db254661c9a030d"
MANIFEST = "a916c18afb628326c28037e678fc809779b888535aafe2d9fc0a54b8107a91fd"
CLOSURE = "367dfb20df55d000396a248d22c26868c20143b8cfa9f52b6d39c2083c3f4776"
QA = "39e294f9096c36203cb5db231b34bbd3ad9cf7c51905ccd318e79b14d95b62e0"
REHEARSAL = "2e941ad447e19ba43ce78e3f595da14cfb8ec20735d8ed7409d3a45bb7bce6e9"
PARITY = "ac9f3a93654e0e320ebc0d4add364ae6f1df5bf67bd373205a5bae1c8c80d06e"
ROOT_REPLAY = "eba06ceb9c2ab9a7b5dfa97781533680bd6d7a42d142d614ee45c6f019201c30"
INDEX = "33c1869955e1f1a9937c3665b5dcccad3de01e9b1f8e8e887821735238ce81f0"


def read_csv(name: str) -> tuple[list[str], list[dict[str, str]]]:
    with (REG / name).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or ()), list(reader)


def write_csv(name: str, fields: list[str], rows: list[dict[str, str]]) -> None:
    with (REG / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def append_unique(rows: list[dict[str, str]], key: str, value: dict[str, str]) -> None:
    if any(row[key] == value[key] for row in rows):
        raise RuntimeError(f"DUPLICATE_RECORD:{key}:{value[key]}")
    rows.append(value)


def sync_decisions() -> None:
    fields, rows = read_csv("decisions.csv")
    dec32 = next(row for row in rows if row["decision_id"] == "DEC-032")
    dec32.update({
        "status": "SUPERSEDED",
        "decision": "USER_DECISION_NOT_GRANTED_V4_SUPERSEDED_BEFORE_APPROVAL",
        "consequence": "V4 remains historical and unapproved;it cannot authorize V10 or real access.",
        "current_relevance": "HISTORICAL_UNAPPROVED_V4_RELEASE",
        "source_commit": V4_FINAL_COMMIT,
        "superseded_by": "DEC-033",
        "user_approved": "false",
    })
    append_unique(rows, "decision_id", {
        "decision_id": "DEC-033", "date": "2026-09-06", "date_precision": "DAY",
        "title": "DG05_EXECUTABLE_V10_EXACT_RELEASE_REAPPROVAL", "status": "OPEN",
        "context": "G1 production-kernel parity and G2 raw-root-to-result replay are closed under exact V10 bytes;real access remains prohibited.",
        "alternatives_considered": "Approve exact V10 release;decline;request another bounded preaccess closure",
        "decision": "USER_DECISION_REQUIRED",
        "reason": "V10 changes release-bound implementation and verifier bytes and cannot inherit any earlier DG05 approval.",
        "consequence": "No attack/test/label/scenario access occurs until exact V10 manifest and closure are explicitly approved.",
        "current_relevance": "SOLE_OPEN_DG05_REAPPROVAL_DECISION",
        "source": "LOCAL_PREACCESS_CLOSURE",
        "source_ref": "research_control_center/validation_v2/dg05_v10_release/DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V10.md",
        "source_commit": FINAL_COMMIT, "affected_components": "RESULT_INTEGRITY;REPRODUCIBILITY;PROJECT_WIDE",
        "supersedes": "DEC-032", "superseded_by": "NONE", "user_approved": "false", "confidence": "HIGH",
    })
    write_csv("decisions.csv", fields, rows)


def sync_artifacts() -> None:
    fields, rows = read_csv("artifacts.csv")
    final_v4 = {
        "ART-DG05-V4-INDEPENDENT-QA", "ART-DG05-V4-EXEC-CLOSURE",
        "ART-DG05-V4-CLOSURE-REPORT", "ART-DG05-V4-ACCESS-BRIEF",
        "ART-DG05-V4-RELEASE-INDEX",
    }
    for row in rows:
        if row["artifact_id"].startswith("ART-DG05-V4-"):
            row["current"] = "false"
            row["superseded"] = "true"
            if row["artifact_id"] in final_v4:
                row["source_commit"] = V4_FINAL_COMMIT
    files = [
        ("EXEC-MANIFEST", "DG05_EXECUTABLE_AUTHORITY_MANIFEST_V10.json", "Exact V10 executable manifest", CANDIDATE_COMMIT),
        ("REHEARSAL", "SYNTHETIC_DG05_PRODUCTION_ROUTE_REHEARSAL_V10.json", "Connected frozen-kernel preaccess rehearsal", CANDIDATE_COMMIT),
        ("KERNEL-PARITY", "PRODUCTION_KERNEL_PARITY_V1.json", "Seventy-two-cell production-kernel invocation census", CANDIDATE_COMMIT),
        ("ROOT-REPLAY", "ROOT_TO_RESULT_REPLAY_V1.json", "Per-root upstream-to-result independent replay receipt", CANDIDATE_COMMIT),
        ("TRANSITIVE", "TRANSITIVE_IMPLEMENTATION_AUTHORITY_V1.json", "Repository-owned static Python transitive implementation closure", CANDIDATE_COMMIT),
        ("METRIC-CONTRACT", "METRIC_SURFACE_CONTRACT_V2.json", "V10-bound complete metric-surface contract", CANDIDATE_COMMIT),
        ("EXPECTED-SURFACE", "EXPECTED_RESULT_SURFACE_V3.json", "Expected 228-surface authority", CANDIDATE_COMMIT),
        ("COVERAGE-JSON", "RESULT_SURFACE_COVERAGE_MATRIX_V3.json", "Root and independent-result coverage for 228 surfaces", CANDIDATE_COMMIT),
        ("COVERAGE-CSV", "RESULT_SURFACE_COVERAGE_MATRIX_V3.csv", "Public-safe per-surface coverage matrix", CANDIDATE_COMMIT),
        ("MUTATIONS", "MUTATION_EVIDENCE_V3.json", "Twenty-five invalid rejection and three valid edge-case evidence", CANDIDATE_COMMIT),
        ("METHOD-SMOKE", "FROZEN_METHOD_SMOKE_V10.json", "Frozen-method no-refit smoke authority", CANDIDATE_COMMIT),
        ("INDEPENDENT-QA", "INDEPENDENT_QA_AUTHORITY_V10.json", "Independent exact-root preaccess V10 QA", FINAL_COMMIT),
        ("EXEC-CLOSURE", "DG05_EXECUTABLE_CLOSURE_AUTHORITY_V10.json", "V10 production-route and root-lineage closure authority", FINAL_COMMIT),
        ("CLOSURE-REPORT", "DG05_EXECUTABLE_CLOSURE_REPORT_V10.md", "Public-safe V10 preaccess closure report", FINAL_COMMIT),
        ("ACCESS-BRIEF", "DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V10.md", "Exact V10 DG05 user reapproval brief", FINAL_COMMIT),
        ("RELEASE-INDEX", "PUBLIC_PRIVATE_DG05_RELEASE_INDEX_V10.json", "Public-safe byte and private-custody index", FINAL_COMMIT),
    ]
    for suffix, filename, role, commit in files:
        append_unique(rows, "artifact_id", {
            "artifact_id": f"ART-DG05-V10-{suffix}", "name": filename, "role": role,
            "source_ref": BRANCH, "source_commit": commit, "producer": "RESULT_INTEGRITY",
            "consumer": "RCC", "public_private": "PUBLIC_SAFE", "frozen": "true",
            "audited": "true", "current": "true", "superseded": "false",
            "safe_path": f"research_control_center/validation_v2/dg05_v10_release/{filename}",
        })
    write_csv("artifacts.csv", fields, rows)


def sync_experiments_claims_risks_timeline() -> None:
    fields, rows = read_csv("experiments.csv")
    append_unique(rows, "experiment_id", {
        "experiment_id": "EXP-DG05-V10-CLOSURE", "name": "DG05 Executable V10 preaccess release qualification",
        "research_question": "Can the exact connected route execute frozen production kernels and independently replay immutable raw roots through all result surfaces?",
        "comparison": "Historical V4 gap counterexamples versus remediated V10 connected route",
        "dataset_scope": "Synthetic fixtures and existing frozen normal-source bundles only;no real attack labels or scenarios",
        "status": "IMPLEMENTED_NOT_EXECUTED",
        "current_evidence": "G1 and G2 reproduced;72/72 production-kernel cells;228/228 root-covered surfaces;25 invalid mutations rejected;independent QA PASS",
        "result_scope": "PREACCESS_ENGINEERING_QUALIFICATION_ONLY_NO_ATTACK_RESULT",
        "primary_metrics": "Kernel invocation identity;per-root replay;surface coverage;mutation rejection;fresh-process custody",
        "limitations": "Not held-out execution;static closure covers repository-owned Python imports;no scientific result",
        "next_action": "Explicit DEC-033 exact V10 user reapproval before any real access",
        "claim_impact": "Supports implementation readiness only;scientific claims and results unchanged.",
        "scientific_source_ref": BRANCH, "scientific_source_commit": FINAL_COMMIT,
        "linked_component_ids": "RESULT_INTEGRITY;REPRODUCIBILITY",
        "artifact_refs": "ART-DG05-V10-EXEC-MANIFEST;ART-DG05-V10-KERNEL-PARITY;ART-DG05-V10-ROOT-REPLAY;ART-DG05-V10-INDEPENDENT-QA;ART-DG05-V10-EXEC-CLOSURE",
    })
    write_csv("experiments.csv", fields, rows)

    fields, rows = read_csv("claims.csv")
    append_unique(rows, "claim_id", {
        "claim_id": "CLAIM-DG05-V10-EXECUTABLE-CLOSURE",
        "claim_text": "The exact DG05 V10 preaccess route invokes frozen production kernels and independently replays immutable roots through the complete synthetic result surface.",
        "claim_type": "IMPLEMENTATION", "status": "SUPPORTED_IMPLEMENTATION",
        "supporting_evidence": "artifact:ART-DG05-V10-KERNEL-PARITY;artifact:ART-DG05-V10-ROOT-REPLAY;artifact:ART-DG05-V10-INDEPENDENT-QA;artifact:ART-DG05-V10-EXEC-CLOSURE",
        "contradicting_evidence": "NONE",
        "allowed_wording": "The exact V10 preaccess route passed frozen-kernel and raw-root lineage qualification on synthetic and frozen normal-only authorities;real access remains unapproved.",
        "forbidden_wording": "Held-out utility generalization production superiority or T2 superiority over T0 is established.",
        "validation_needed": "Explicit DEC-033 exact-release reapproval then separately controlled DG05 execution.",
        "scientific_source_ref": BRANCH, "scientific_source_commit": FINAL_COMMIT,
        "linked_experiment_ids": "EXP-DG05-V10-CLOSURE",
    })
    write_csv("claims.csv", fields, rows)

    fields, rows = read_csv("risks.csv")
    closures = {
        "RISK-DG05-TIME-BINDING": ("CLOSED", "DEC-031 exact interval/timeline/runtime bindings are implemented and independently replayed."),
        "RISK-DG05-NORMAL-SOURCE-LINEAGE": ("CLOSED", "Frozen registry contains 30 components and 23 bundles with independent source-byte burden replay."),
        "RISK-DG05-PRODUCTION-ROUTE": ("CLOSED", "V10 connects projection through frozen kernels custody and root-to-result verification on the preaccess route."),
        "RISK-DG05-V4-EXACT-APPROVAL": ("CLOSED", "V4 is historical and unapproved;DEC-032 is superseded and cannot authorize V10."),
    }
    for row in rows:
        if row["risk_id"] in closures:
            row["status"], row["mitigation"] = closures[row["risk_id"]]
    append_unique(rows, "risk_id", {
        "risk_id": "RISK-DG05-V10-EXACT-APPROVAL", "category": "CUSTODY",
        "description": "The exact V10 executable bytes differ from all historical or suspended DG05 approvals and cannot inherit them.",
        "severity": "HIGH", "likelihood": "LOW", "affected_component": "RESULT_INTEGRITY",
        "evidence": "artifact:ART-DG05-V10-EXEC-CLOSURE",
        "mitigation": "Require explicit DEC-033 approval of the exact V10 manifest and closure before any real attack/test or label/scenario access.",
        "owner": "RESEARCH_OWNER", "status": "MITIGATING", "scientific_source_ref": BRANCH,
        "scientific_source_commit": FINAL_COMMIT,
    })
    write_csv("risks.csv", fields, rows)

    fields, rows = read_csv("timeline.csv")
    v4 = next(row for row in rows if row["event_id"] == "EVENT-DG05-V4-RELEASE-FREEZE-001")
    v4.update({"status": "HISTORICAL", "source_commit": V4_FINAL_COMMIT,
               "notes": "Historical unapproved V4 candidate;G1 and G2 required prospective remediation;DEC-032 superseded before approval"})
    append_unique(rows, "event_id", {
        "event_id": "EVENT-DG05-V5-V9-QUALIFICATION-001", "date": "2026-09-06", "date_precision": "DAY",
        "event_type": "AUDIT_MILESTONE", "title": "DG05 V5 through V9 failed release qualification preserved",
        "summary": "Successive fail-closed candidates exposed transitive implementation and custodian replay gaps;none was approved or used for real access.",
        "source": "LOCAL_READ_ONLY_AUDIT",
        "source_ref": "research_control_center/validation_v2/dg05_v9_release/RELEASE_QUALIFICATION_DISPOSITION_V1.json",
        "source_commit": "0e9fda03969f3b0deca8ed7426fa0d833cd8c059", "affected_components": "RESULT_INTEGRITY;REPRODUCIBILITY;PROJECT_WIDE",
        "decision_refs": "DEC-031;DEC-032", "status": "HISTORICAL", "superseded_by": "EVENT-DG05-V10-RELEASE-FREEZE-001",
        "notes": "Failed release candidates are evidence of fail-closed qualification and not execution approvals",
    })
    append_unique(rows, "event_id", {
        "event_id": "EVENT-DG05-V10-RELEASE-FREEZE-001", "date": "2026-09-06", "date_precision": "DAY",
        "event_type": "GOVERNANCE_MILESTONE", "title": "DG05 Executable V10 exact preaccess release qualified",
        "summary": "G1 and G2 closed;72 production-kernel cells;228 root-covered surfaces;fresh-process custody;25 invalid mutations rejected;real access0.",
        "source": "LOCAL_VERIFIED_IMPLEMENTATION",
        "source_ref": "research_control_center/validation_v2/dg05_v10_release/DG05_EXECUTABLE_CLOSURE_REPORT_V10.md",
        "source_commit": FINAL_COMMIT, "affected_components": "RESULT_INTEGRITY;REPRODUCIBILITY;PROJECT_WIDE",
        "decision_refs": "DEC-031;DEC-033", "status": "ACTIVE_CONTEXT", "superseded_by": "NONE",
        "notes": "DEC-033 exact V10 user reapproval required;no held-out or scientific result",
    })
    write_csv("timeline.csv", fields, rows)


def sync_state() -> None:
    current_path = REG / "current_state.yaml"
    state = load_json(current_path)
    statement = (
        "DG05 Executable V10 closes G1 production-kernel route parity and G2 immutable raw-root-to-result replay under DEC-031. "
        "The connected preaccess route executed 72/72 frozen-kernel cells and independently root-covered 228/228 result surfaces; "
        "real DG05 remains NO_GO until DEC-033 explicitly approves the exact V10 manifest and closure. No real attack/test/label/"
        "scenario/provider/credential resource was accessed. Professor package NOT_SUBMITTED; backup SINGLE_COPY_LOCAL_ONLY."
    )
    state["last_updated"] = "2026-09-06"
    state["current_phase_statement"] = statement
    state["top_priorities"][0] = "DEC-033 exact DG05 Executable V10 release reapproval"
    state["highest_priority_work"][0] = "DEC-033 exact DG05 Executable V10 release reapproval"
    state["user_todo_items"][4].update({
        "task": "DEC-033에서 정확한 DG05 Executable V10 manifest와 closure의 실제 접근 재승인 여부를 결정한다.",
        "why": "V10은 G1/G2를 닫는 새 실행·검증 바이트이므로 과거 승인이나 DEC-032를 상속할 수 없다.",
        "linked": "research_control_center/validation_v2/dg05_v10_release/DG05_MULTI_PANEL_ATTACK_ACCESS_BRIEF_V10.md",
    })
    state["top_user_todo"][0] = "DEC-033: exact DG05 Executable V10 release reapproval decision"
    state["recommended_next_management_task"] = "DG-05 REAPPROVAL — DG05_EXECUTABLE_V10 EXACT RELEASE"
    state["last_completed_task"] = "DG05-V4-PREACCESS-ROUTE-UPSTREAM-LINEAGE-CLOSURE-001 — COMPLETE_QA_PASS_READY_FOR_USER_REAPPROVAL"
    state["exact_next_task"] = "DG-05 REAPPROVAL — DG05_EXECUTABLE_V10 EXACT RELEASE"
    state["dg05_production_chain_closure"]["open_decision"] = "DEC-033"
    state["dg05_executable_v4_closure"]["historical_disposition"] = "UNAPPROVED_SUPERSEDED_BEFORE_USER_APPROVAL"
    state["dg05_executable_v4_closure"]["open_decision"] = "NONE_HISTORICAL"
    state["dg05_executable_v10_closure"] = {
        "task_id": "DG05-V4-PREACCESS-ROUTE-UPSTREAM-LINEAGE-CLOSURE-001",
        "status": "READY_FOR_USER_REAPPROVAL", "decision_binding": "DEC-031",
        "open_decision": "DEC-033", "release_manifest_hash": MANIFEST,
        "closure_authority_hash": CLOSURE, "independent_qa_hash": QA,
        "rehearsal_hash": REHEARSAL, "production_kernel_parity_hash": PARITY,
        "root_to_result_replay_hash": ROOT_REPLAY, "public_private_index_hash": INDEX,
        "implementation_commit": IMPLEMENTATION_COMMIT, "candidate_package_commit": CANDIDATE_COMMIT,
        "final_artifact_commit": FINAL_COMMIT, "production_kernel_cells": 72,
        "synthetic_fallback_cells": 0, "verified_result_surfaces": 228,
        "root_covered_result_surfaces": 228, "normal_source_components": 30,
        "normal_method_version_bundles": 23, "invalid_mutations_rejected": 25,
        "valid_semantic_edge_cases_accepted": 3, "held_out_accesses": 0,
        "label_scenario_accesses": 0, "provider_calls": 0, "credential_reads": 0,
        "professor_package": "NOT_SUBMITTED", "backup_status": "SINGLE_COPY_LOCAL_ONLY",
        "exact_next": "DG-05 REAPPROVAL — DG05_EXECUTABLE_V10 EXACT RELEASE",
    }
    write_json(current_path, state)

    program_path = RCC / "validation_v2/PROGRAM_STATE.json"
    program = load_json(program_path)
    program["current_stage"] = "DG05_EXECUTABLE_V10_PREACCESS_RELEASE"
    program["program_status"] = "READY_FOR_USER_REAPPROVAL_NO_GO_REAL_ACCESS"
    program["decision_gates"]["DG-05"] = "EXECUTABLE_V10_READY_EXACT_USER_REAPPROVAL_REQUIRED"
    program["exact_next_task"] = "DG-05 REAPPROVAL — DG05_EXECUTABLE_V10 EXACT RELEASE"
    program["dg05_executable_v4_closure"]["historical_disposition"] = "UNAPPROVED_SUPERSEDED_BEFORE_USER_APPROVAL"
    program["dg05_executable_v4_closure"]["open_decision"] = "NONE_HISTORICAL"
    program["dg05_executable_v10_closure"] = state["dg05_executable_v10_closure"]
    write_json(program_path, program)


def sync_panel_and_task_indexes() -> None:
    source = RCC / "validation_v2/evaluation_expansion/PANEL_REGISTRY_V6.csv"
    target = source.with_name("PANEL_REGISTRY_V7.csv")
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle); fields = list(reader.fieldnames or ()); rows = list(reader)
    for row in rows:
        if row["panel_id"] != "HAI23_TEST1_DEVELOPMENT_V1":
            row["metric_authority"] = "DG05_EXECUTABLE_V10_METRIC_SURFACE"
            row["custody_authority"] = "DG05_EXECUTABLE_V10_GLOBAL_FREEZE_CONTRACT"
            row["result_status"] = "DG05_V10_READY_USER_REAPPROVAL_REQUIRED"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)

    source = RCC / "validation_v2/evaluation_expansion/IMPLEMENTATION_TASK_INDEX_V6.csv"
    target = source.with_name("IMPLEMENTATION_TASK_INDEX_V7.csv")
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle); fields = list(reader.fieldnames or ()); rows = list(reader)
    rows.append({
        "task_id": "DG05-V4-PREACCESS-ROUTE-UPSTREAM-LINEAGE-CLOSURE-001", "status": "COMPLETE_QA_PASS",
        "prerequisite": "DEC-031 and historical unapproved V4 gap evidence",
        "allowed_data": "Synthetic fixtures and existing frozen normal-only sources read-only",
        "prohibited_data": "Real attack test label scenario provider and credentials",
        "expected_artifacts": "V10 frozen-kernel route parity and immutable raw-root replay release",
        "user_gate": "NONE_FOR_PREACCESS_CLOSURE", "parallelization": "Read-only audits and sole writer",
        "scientific_stop_condition": "Any protected access scientific-authority or coherent-rehash failure",
    })
    rows.append({
        "task_id": "MULTIPANEL-DG05-V10-EXEC-001", "status": "USER_DECISION_REQUIRED",
        "prerequisite": "Exact V10 manifest closure and DEC-033",
        "allowed_data": "Conditional feature-first attack execution only after exact approval",
        "prohibited_data": "Any access before approval;labels before freeze;post-result tuning",
        "expected_artifacts": "Version-specific held-out results", "user_gate": "DEC-033",
        "parallelization": "One prediction writer and isolated custodian",
        "scientific_stop_condition": "Any custody integrity privacy or authority failure",
    })
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    sync_decisions()
    sync_artifacts()
    sync_experiments_claims_risks_timeline()
    sync_state()
    sync_panel_and_task_indexes()
    print("DG05_V10_RECORD_SYNC_PASS")


if __name__ == "__main__":
    main()
