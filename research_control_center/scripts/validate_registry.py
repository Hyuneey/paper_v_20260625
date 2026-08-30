#!/usr/bin/env python3
"""Fail-closed validator for the public-safe Research Control Center registry."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from build_dashboard import AUTHORITY_COMMIT, load_registry, registry_digest


AUTHORITY_REF = "origin/research-v6-thesis-checkpoint"
OVERLAY_COMMIT = "ebc5a57bfdb7d8266f96f2990338effb9d0a2743"
OVERLAY_REF = "origin/task-039e3-r2r-thesis-draft-scaffold-v1"
IMMUTABLE_TAG = "thesis-v1-post-push-audit"
ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]*$")
FORMULA_MARKERS = ("=", "+", "@")
BOOLEAN_FIELDS = {"true", "false"}
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
CLAIM_TYPES = {"IMPLEMENTATION", "SCIENTIFIC_CONTRIBUTION", "UTILITY", "GENERALIZATION", "HUMAN_EVALUATION"}
EVENT_TYPES = {
    "RESEARCH_PIVOT", "PROFESSOR_FEEDBACK", "METHOD_DECISION", "DATASET_DECISION",
    "IMPLEMENTATION_MILESTONE", "EXPERIMENT_MILESTONE", "RESULT_MILESTONE",
    "AUDIT_MILESTONE", "THESIS_MILESTONE", "GOVERNANCE_MILESTONE",
}
DATE_PRECISIONS = {"DAY", "MONTH", "RANGE", "APPROXIMATE"}
HISTORY_STATUSES = {"ACTIVE_CONTEXT", "HISTORICAL", "SUPERSEDED", "ABANDONED", "CONDITIONAL"}
DECISION_STATUSES = {"ACTIVE", "SUPERSEDED", "ABANDONED", "CONDITIONAL", "OPEN"}
CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}

EXPECTED_HEADERS = {
    "components": (
        "component_id", "name", "research_role", "status", "lifecycle_stage",
        "scientific_source_ref", "scientific_source_commit", "representative_path",
        "representative_symbol", "input_summary", "output_summary", "artifact_refs",
        "test_refs", "executed", "audited", "reproduced", "claim_ready", "risk_level",
        "next_action", "deep_review_part",
    ),
    "experiments": (
        "experiment_id", "name", "research_question", "comparison", "dataset_scope",
        "status", "current_evidence", "result_scope", "primary_metrics", "limitations",
        "next_action", "claim_impact", "scientific_source_ref", "scientific_source_commit",
        "linked_component_ids", "artifact_refs",
    ),
    "claims": (
        "claim_id", "claim_text", "claim_type", "status", "supporting_evidence",
        "contradicting_evidence", "allowed_wording", "forbidden_wording", "validation_needed",
        "scientific_source_ref", "scientific_source_commit", "linked_experiment_ids",
    ),
    "risks": (
        "risk_id", "category", "description", "severity", "likelihood", "affected_component",
        "evidence", "mitigation", "owner", "status", "scientific_source_ref",
        "scientific_source_commit",
    ),
    "artifacts": (
        "artifact_id", "name", "role", "source_ref", "source_commit", "producer", "consumer",
        "public_private", "frozen", "audited", "current", "superseded", "safe_path",
    ),
    "decisions": (
        "decision_id", "date", "date_precision", "title", "status", "context",
        "alternatives_considered", "decision", "reason", "consequence",
        "current_relevance", "source", "source_ref", "source_commit",
        "affected_components", "supersedes", "superseded_by", "user_approved", "confidence",
    ),
    "timeline": (
        "event_id", "date", "date_precision", "event_type", "title", "summary", "source",
        "source_ref", "source_commit", "affected_components", "decision_refs", "status",
        "superseded_by", "notes",
    ),
}

STATUS_ENUMS = {
    "components": {
        "IMPLEMENTED_EXECUTED_AUDITED", "IMPLEMENTED_EXECUTED", "IMPLEMENTED_NOT_EXECUTED",
        "RESEARCH_ONLY", "DESIGN_ONLY", "PARTIAL", "BLOCKED", "LEGACY_OR_SUPERSEDED", "UNKNOWN",
    },
    "experiments": {
        "NOT_STARTED", "DESIGN_ONLY", "IMPLEMENTED_NOT_EXECUTED", "EXECUTED_NOT_AUDITED",
        "EXECUTED_AUDITED_PILOT", "BLOCKED", "SUPERSEDED", "UNKNOWN",
    },
    "claims": {
        "SUPPORTED_IMPLEMENTATION", "PILOT_ONLY", "UNVALIDATED", "NOT_SUPPORTED",
        "CONDITIONAL", "SUPERSEDED",
    },
    "risks": {"OPEN", "MITIGATING", "ACCEPTED", "CLOSED"},
    "decisions": DECISION_STATUSES,
    "timeline": HISTORY_STATUSES,
}

LIFECYCLE_STAGES = {
    "DESIGN_COMPLETE", "CODE_IMPLEMENTED", "INTEGRATED", "EXECUTED", "AUDITED", "REPRODUCED", "CLAIM_READY",
}
REQUIRED_RCC_FILES = (
    "START_HERE.md", "SOURCE_AUTHORITY.md", "CURRENT_CONTEXT.md", "SESSION_HANDOFF.md",
    "MY_TODO.md", "DECISION_INBOX.md", "registry/README.md", "registry/current_state.yaml",
    "registry/components.csv", "registry/experiments.csv", "registry/claims.csv",
    "registry/risks.csv", "registry/artifacts.csv", "registry/decisions.csv", "registry/timeline.csv",
    "registry/history.yaml",
    "wiki/README.md", "history/README.md", "architecture/README.md",
    "dashboard/assets/rcc.css", "dashboard/assets/rcc.js",
    "scripts/build_dashboard.py", "scripts/validate_registry.py", "scripts/refresh_all.py",
    "scripts/open_dashboard.bat",
    "bootstrap/ARCH_006/ARCH_006_REPORT.md",
    "bootstrap/ARCH_006/ARCH_006_RUNTIME_AUDIT.md",
    "bootstrap/ARCH_006/ARCH_006_TRACE_AUDIT.md",
    "bootstrap/ARCH_006/ARCH_006_D1_FREEZE_AUDIT.md",
    "bootstrap/ARCH_006/ARCH_006_EXPLANATION_AUDIT.md",
    "bootstrap/ARCH_006/ARCH_006_R1_INPUT_BOUNDARY.md",
    "bootstrap/ARCH_006/ARCH_006_MISMATCHES.md",
    "bootstrap/ARCH_006/ARCH_006_QA_REPORT.md",
    "bootstrap/ARCH_006/ARCH_006_MULTI_AGENT_REVIEW.md",
    "bootstrap/ARCH_006/ARCH_006_EVIDENCE.json",
    "bootstrap/ARCH_006/agents/agent_a_runtime.json",
    "bootstrap/ARCH_006/agents/agent_b_trace.json",
    "bootstrap/ARCH_006/agents/agent_c_prediction_freeze.json",
    "bootstrap/ARCH_006/agents/agent_d_explanation.json",
    "bootstrap/ARCH_006/agents/agent_e_qa.json",
    "bootstrap/ARCH_007/ARCH_007_REPORT.md",
    "bootstrap/ARCH_007/ARCH_007_PCA_SPE_AUDIT.md",
    "bootstrap/ARCH_007/ARCH_007_CALIBRATION_AUDIT.md",
    "bootstrap/ARCH_007/ARCH_007_PREDICTION_LINEAGE_AUDIT.md",
    "bootstrap/ARCH_007/ARCH_007_BASELINE_SCOPE.md",
    "bootstrap/ARCH_007/ARCH_007_MISMATCHES.md",
    "bootstrap/ARCH_007/ARCH_007_QA_REPORT.md",
    "bootstrap/ARCH_007/ARCH_007_MULTI_AGENT_REVIEW.md",
    "bootstrap/ARCH_007/ARCH_007_EVIDENCE.json",
    "bootstrap/ARCH_007/agents/agent_a_pca.json",
    "bootstrap/ARCH_007/agents/agent_b_calibration.json",
    "bootstrap/ARCH_007/agents/agent_c_prediction_result.json",
    "bootstrap/ARCH_007/agents/agent_d_qa.json",
    "bootstrap/ARCH_008/ARCH_008_REPORT.md",
    "bootstrap/ARCH_008/ARCH_008_ATTACK_EVENT_AUDIT.md",
    "bootstrap/ARCH_008/ARCH_008_NORMAL_FALSE_ALARM_AUDIT.md",
    "bootstrap/ARCH_008/ARCH_008_D0_D1_OVERLAP_AUDIT.md",
    "bootstrap/ARCH_008/ARCH_008_RESULT_INTEGRITY_AUDIT.md",
    "bootstrap/ARCH_008/ARCH_008_COMPLEMENTARITY_BOUNDARY.md",
    "bootstrap/ARCH_008/ARCH_008_RULE_ONLY_UTILITY.md",
    "bootstrap/ARCH_008/ARCH_008_PROFESSOR_RULE_ONLY_NOTE.md",
    "bootstrap/ARCH_008/ARCH_008_MISMATCHES.md",
    "bootstrap/ARCH_008/ARCH_008_QA_REPORT.md",
    "bootstrap/ARCH_008/ARCH_008_MULTI_AGENT_REVIEW.md",
    "bootstrap/ARCH_008/ARCH_008_EVIDENCE.json",
    "bootstrap/ARCH_008/agents/agent_a_attack_events.json",
    "bootstrap/ARCH_008/agents/agent_b_false_alarms.json",
    "bootstrap/ARCH_008/agents/agent_c_overlap.json",
    "bootstrap/ARCH_008/agents/agent_d_integrity_claims.json",
    "bootstrap/ARCH_008/agents/agent_e_qa.json",
    "bootstrap/ARCH_009/ARCH_009_REPORT.md",
    "bootstrap/ARCH_009/ARCH_009_V1_POLICY_AUDIT.md",
    "bootstrap/ARCH_009/ARCH_009_V2_POLICY_AUDIT.md",
    "bootstrap/ARCH_009/ARCH_009_INPUT_FREEZE_AUDIT.md",
    "bootstrap/ARCH_009/ARCH_009_MISS_RECOVERY_AUDIT.md",
    "bootstrap/ARCH_009/ARCH_009_COMPLEMENTARITY_INTERPRETATION.md",
    "bootstrap/ARCH_009/ARCH_009_CLAIM_MATRIX.csv",
    "bootstrap/ARCH_009/ARCH_009_MISMATCHES.md",
    "bootstrap/ARCH_009/ARCH_009_QA_REPORT.md",
    "bootstrap/ARCH_009/ARCH_009_MULTI_AGENT_REVIEW.md",
    "bootstrap/ARCH_009/ARCH_009_EVIDENCE.json",
    "bootstrap/ARCH_009/agents/agent_a_v1.json",
    "bootstrap/ARCH_009/agents/agent_b_v2.json",
    "bootstrap/ARCH_009/agents/agent_c_authority_freeze.json",
    "bootstrap/ARCH_009/agents/agent_d_result_claims.json",
    "bootstrap/ARCH_009/agents/agent_e_qa.json",
    "bootstrap/ARCH_010/ARCH_010_REPORT.md",
    "bootstrap/ARCH_010/ARCH_010_ATTACK_EVENT_AUDIT.md",
    "bootstrap/ARCH_010/ARCH_010_EPISODE_FAR_AUDIT.md",
    "bootstrap/ARCH_010/ARCH_010_CROSS_METHOD_METRIC_AUDIT.md",
    "bootstrap/ARCH_010/ARCH_010_RESULT_INTEGRITY_AUDIT.md",
    "bootstrap/ARCH_010/ARCH_010_CLAIM_MATRIX.csv",
    "bootstrap/ARCH_010/ARCH_010_MISMATCHES.md",
    "bootstrap/ARCH_010/ARCH_010_QA_REPORT.md",
    "bootstrap/ARCH_010/ARCH_010_MULTI_AGENT_REVIEW.md",
    "bootstrap/ARCH_010/ARCH_010_EVIDENCE.json",
    "bootstrap/ARCH_010/agents/agent_a_attack_events.json",
    "bootstrap/ARCH_010/agents/agent_b_episode_far.json",
    "bootstrap/ARCH_010/agents/agent_c_metric_consistency.json",
    "bootstrap/ARCH_010/agents/agent_d_integrity.json",
    "bootstrap/ARCH_010/agents/agent_e_qa.json",
    "bootstrap/GAP_000/GAP_000_REPORT.md",
    "bootstrap/GAP_000/GAP_000_RAW_FINDINGS.csv",
    "bootstrap/GAP_000/GAP_000_ROOT_ISSUES.csv",
    "bootstrap/GAP_000/GAP_000_REMEDIATION_MATRIX.csv",
    "bootstrap/GAP_000/GAP_000_EXPERIMENT_GATES.csv",
    "bootstrap/GAP_000/GAP_000_CORE_VALIDATION_GATE.md",
    "bootstrap/GAP_000/GAP_000_EXP01_GATE.md",
    "bootstrap/GAP_000/GAP_000_EXP03_GATE.md",
    "bootstrap/GAP_000/GAP_000_EXP05_GATE.md",
    "bootstrap/GAP_000/GAP_000_CODE_FIX_QUEUE.md",
    "bootstrap/GAP_000/GAP_000_EXPERIMENT_REQUIREMENTS.md",
    "bootstrap/GAP_000/GAP_000_CLAIM_LIMITATIONS.md",
    "bootstrap/GAP_000/GAP_000_MINIMUM_THESIS_PATH.md",
    "bootstrap/GAP_000/GAP_000_USER_DECISIONS_REQUIRED.md",
    "bootstrap/GAP_000/GAP_000_QA_REPORT.md",
    "bootstrap/GAP_000/GAP_000_MULTI_AGENT_REVIEW.md",
    "bootstrap/GAP_000/GAP_000_EVIDENCE.json",
    "bootstrap/GAP_000/agents/agent_a_scientific_validity.json",
    "bootstrap/GAP_000/agents/agent_b_code_authority.json",
    "bootstrap/GAP_000/agents/agent_c_governance_reproducibility.json",
    "bootstrap/GAP_000/agents/agent_d_claim_scope.json",
    "bootstrap/GAP_000/agents/agent_e_qa.json",
    "bootstrap/ARCH_011/ARCH_011_REPORT.md",
    "bootstrap/ARCH_011/ARCH_011_OUTER_CUSTODY_AUDIT.md",
    "bootstrap/ARCH_011/ARCH_011_ENVIRONMENT_AUDIT.md",
    "bootstrap/ARCH_011/ARCH_011_PORTABILITY_AUDIT.md",
    "bootstrap/ARCH_011/ARCH_011_REPRODUCTION_LEVELS.md",
    "bootstrap/ARCH_011/ARCH_011_AUTHORITY_OPTIONS.csv",
    "bootstrap/ARCH_011/ARCH_011_FRESH_MACHINE_PROTOCOL.md",
    "bootstrap/ARCH_011/ARCH_011_VALIDATION_V2_VERSIONING.md",
    "bootstrap/ARCH_011/ARCH_011_RELEASE_SCOPE.md",
    "bootstrap/ARCH_011/ARCH_011_MISMATCHES.md",
    "bootstrap/ARCH_011/ARCH_011_QA_REPORT.md",
    "bootstrap/ARCH_011/ARCH_011_MULTI_AGENT_REVIEW.md",
    "bootstrap/ARCH_011/ARCH_011_EVIDENCE.json",
    "bootstrap/ARCH_011/agents/agent_a_environment.json",
    "bootstrap/ARCH_011/agents/agent_b_outer.json",
    "bootstrap/ARCH_011/agents/agent_c_portability.json",
    "bootstrap/ARCH_011/agents/agent_d_reproduction.json",
    "bootstrap/ARCH_011/agents/agent_e_qa.json",
)
GENERATED_FILES = (
    "dashboard/index.html", "generated/GPT_BRIEF.md", "generated/CURRENT_STATUS.md",
    "generated/CHANGE_SUMMARY.md", "generated/RCC_002_USER_SUMMARY.md",
    "generated/RCC_003_HISTORY_SUMMARY.md", "generated/ARCH_001_USER_SUMMARY.md",
    "generated/ARCH_002_USER_SUMMARY.md", "generated/ARCH_003_USER_SUMMARY.md",
    "generated/ARCH_004_USER_SUMMARY.md",
    "generated/ARCH_005_USER_SUMMARY.md",
    "generated/ARCH_006_USER_SUMMARY.md",
    "generated/ARCH_007_USER_SUMMARY.md",
    "generated/ARCH_008_USER_SUMMARY.md",
    "generated/ARCH_009_USER_SUMMARY.md",
    "generated/ARCH_010_USER_SUMMARY.md",
    "generated/GAP_000_USER_SUMMARY.md",
    "generated/ARCH_011_USER_SUMMARY.md",
    "history/PROJECT_TIMELINE.md",
    "history/PROFESSOR_FEEDBACK_LINEAGE.md", "history/SUPERSEDED_DIRECTIONS.md",
    "history/TERMINOLOGY_GUIDE.md", "history/HISTORY_CONFIRMATION_NEEDED.md",
    "CURRENT_CONTEXT.md", "MY_TODO.md", "DECISION_INBOX.md",
)
REQUIRED_RCC_DIRS = (
    "registry", "wiki", "history", "history/decisions", "history/checkpoints",
    "architecture", "dashboard", "dashboard/assets", "generated", "scripts",
    "bootstrap/RCC_000", "bootstrap/RCC_003", "bootstrap/RCC_003/agents",
    "architecture/01_data_and_splits", "bootstrap/ARCH_001", "bootstrap/ARCH_001/agents",
    "architecture/02_candidate_discovery", "bootstrap/ARCH_002", "bootstrap/ARCH_002/agents",
    "architecture/03_relation_and_numeric", "bootstrap/ARCH_003", "bootstrap/ARCH_003/agents",
    "architecture/04_rule_construction", "bootstrap/ARCH_004", "bootstrap/ARCH_004/agents",
    "architecture/05_verifier_common42", "bootstrap/ARCH_005", "bootstrap/ARCH_005/agents",
    "architecture/06_runtime_trace_explanation", "bootstrap/ARCH_006", "bootstrap/ARCH_006/agents",
    "architecture/07_d0_detector", "bootstrap/ARCH_007", "bootstrap/ARCH_007/agents",
    "architecture/08_d1_rule_only", "bootstrap/ARCH_008", "bootstrap/ARCH_008/agents",
    "architecture/09_d2_fusion", "bootstrap/ARCH_009", "bootstrap/ARCH_009/agents",
    "architecture/10_metrics_integrity", "bootstrap/ARCH_010", "bootstrap/ARCH_010/agents",
    "architecture/gap_000_pre_validation", "bootstrap/GAP_000", "bootstrap/GAP_000/agents",
    "architecture/11_outer_reproducibility", "bootstrap/ARCH_011", "bootstrap/ARCH_011/agents",
)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)


def _split_refs(value: str) -> list[str]:
    return [] if value == "NONE" else value.split(";")


def _read_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return tuple(next(csv.reader(handle)))


def _validate_headers_and_cells(rcc_root: Path, data: Mapping[str, Any], result: ValidationResult) -> None:
    for registry, headers in EXPECTED_HEADERS.items():
        path = rcc_root / "registry" / f"{registry}.csv"
        result.require(_read_header(path) == headers, f"{registry}.csv header does not match the frozen schema")
        for row_number, row in enumerate(data[registry], start=2):
            for column in headers:
                value = row.get(column)
                result.require(value is not None and value != "", f"{registry}.csv:{row_number} has an empty {column}")
                if value:
                    result.require(value == value.strip(), f"{registry}.csv:{row_number} {column} has surrounding whitespace")
                    result.require(not CONTROL_CHARS.search(value), f"{registry}.csv:{row_number} {column} has a control character")
                    result.require(not value.startswith(FORMULA_MARKERS), f"{registry}.csv:{row_number} {column} begins with a formula marker")


def _validate_unique_ids(data: Mapping[str, Any], result: ValidationResult) -> None:
    key_fields = {
        "components": "component_id", "experiments": "experiment_id", "claims": "claim_id",
        "risks": "risk_id", "artifacts": "artifact_id", "decisions": "decision_id", "timeline": "event_id",
    }
    for registry, key in key_fields.items():
        values = [row[key] for row in data[registry]]
        result.require(len(values) == len(set(values)), f"{registry}.{key} contains duplicates")
        for value in values:
            result.require(bool(ID_PATTERN.fullmatch(value)), f"{registry}.{key} has invalid ID {value!r}")


def _validate_authority(data: Mapping[str, Any], result: ValidationResult) -> None:
    state = data["state"]
    result.require(state.get("schema_version") == "rcc-current-state-v1", "current-state schema version mismatch")
    result.require(state.get("rcc_version") == "0.1.0", "RCC version must be 0.1.0")
    result.require(state.get("registry_version") == "0.1.0", "registry version must be 0.1.0")
    result.require(state.get("scientific_authority") == {"ref": AUTHORITY_REF, "commit": AUTHORITY_COMMIT}, "scientific authority does not match the approved pin")
    result.require(state.get("immutable_scientific_pin") == {"tag": IMMUTABLE_TAG, "commit": AUTHORITY_COMMIT}, "immutable scientific pin mismatch")
    result.require(
        state.get("documentation_overlay") == {"ref": OVERLAY_REF, "commit": OVERLAY_COMMIT, "role": "READ_ONLY_DOCUMENTATION_OVERLAY"},
        "documentation overlay mismatch",
    )
    checkout = state.get("non_authoritative_checkout", {})
    result.require(
        checkout == {
            "ref": "task-039c-gdn",
            "commit": "c0efdb6218385ec326be1a929371242314e63cb6",
            "authoritative": False,
        },
        "historical checkout identity or non-authoritative flag mismatch",
    )
    result.require(
        state.get("phase_progression") == ["ARCHITECTURE_COMPLETE", "EVALUATION_SCOPE_EXPANSION", "HYPOTHESIS_VALIDATION"],
        "phase progression mismatch",
    )
    result.require(state.get("current_phase") == "EVALUATION_SCOPE_EXPANSION", "current phase mismatch")
    result.require(len(state.get("highest_priority_work", [])) == 3, "highest_priority_work must contain exactly three entries")
    result.require(len(state.get("top_user_todo", [])) == 6, "top_user_todo must contain the six current V2 review entries")
    result.require(len(state.get("user_todo_items", [])) == 8, "ARCH-011 must leave eight user review questions")
    result.require(state.get("last_completed_task") == "V2-PROTOCOL-001 — Validation / Development / Final-Test Contract Freeze", "last completed task mismatch")
    result.require(state.get("exact_next_task") == "GAP-FIX-METRIC-001 — Metric Portability & Common Evaluation Contract", "exact next task mismatch")
    result.require(
        state.get("research_stage") == {
            "architecture_complete": True,
            "evaluation_scope_expansion": "current",
            "hypothesis_validation": "pending",
        },
        "research stage mismatch",
    )
    result.require(state.get("scientific_result_status") == "pilot_only", "scientific result must remain pilot_only")
    result.require(state.get("held_out_generalization") == "unconfirmed", "held-out generalization must remain unconfirmed")
    result.require(state.get("fresh_machine_reproducibility") == "incomplete", "fresh-machine reproducibility must remain incomplete")
    result.require(len(state.get("top_priorities", [])) == 3, "top_priorities must contain exactly three entries")
    result.require(state.get("recommended_next_management_task") == "GAP-FIX-METRIC-001 — Metric Portability & Common Evaluation Contract", "next management task mismatch")
    result.require(state.get("recommended_next_architecture_task") == "NONE — ARCH-000 through ARCH-011 complete", "next architecture task mismatch")
    readiness = state.get("pre_validation_readiness", {})
    result.require(readiness.get("status") == "REMEDIATION_IN_PROGRESS", "VALIDATION V2 remediation status mismatch")
    result.require(readiness.get("p0_global_fixes") == [], "remaining global P0 fix mismatch")
    result.require(readiness.get("raw_findings") == 120 and readiness.get("root_issues") == 19, "GAP-000 inventory counts mismatch")
    result.require(readiness.get("source_severity") == {"critical": 0, "high": 54, "medium": 55, "low": 11}, "GAP-000 source severity mismatch")
    result.require(readiness.get("disposition_counts") == {
        "P0_FIX_BEFORE_EXPANDED_VALIDATION": 2,
        "P1_FIX_BEFORE_SPECIFIC_EXPERIMENT": 3,
        "EXPERIMENT_DESIGN_REQUIREMENT": 6,
        "ENGINEERING_HARDENING": 3,
        "CLAIM_DOCUMENTATION_CORRECTION": 1,
        "ACCEPTABLE_THESIS_LIMITATION": 3,
        "FUTURE_WORK_ONLY": 1,
    }, "GAP-000 disposition counts mismatch")
    result.require(readiness.get("priority_counts") == {"P0": 4, "P1": 10, "P2": 3, "P3": 2}, "GAP-000 priority counts mismatch")
    result.require(readiness.get("arch011_position") == "BEFORE_REMEDIATION_READ_ONLY", "ARCH-011 position mismatch")
    result.require("INVALIDATED_ARTIFACTS=0" in readiness.get("past_pilot", ""), "GAP-000 pilot preservation mismatch")
    outer = state.get("outer_reproducibility", {})
    result.require(outer.get("audit_status") == "ARCH_011_PASS_READ_ONLY", "ARCH-011 audit status mismatch")
    result.require(outer.get("old_outer", {}).get("retryability") == "NOT_RETRYABLE_BY_PROTOCOL", "ARCH-011 retryability mismatch")
    result.require(outer.get("old_outer", {}).get("feature_byte_reads") == 0 and outer.get("old_outer", {}).get("label_accesses") == 0, "ARCH-011 content-access boundary mismatch")
    result.require(outer.get("reproduction_levels", {}).get("traceability") == "STRONG_SUPPORTED", "ARCH-011 traceability mismatch")
    result.require(outer.get("reproduction_levels", {}).get("fresh_machine_scientific") == "NOT_DEMONSTRATED_BLOCKED", "ARCH-011 fresh-machine status mismatch")
    relation = state.get("relation_numeric_authority", {})
    result.require(relation.get("candidate_pairs") == 47 and relation.get("confirmed_directions") == 42, "ARCH-003 relation lineage summary mismatch")
    result.require(relation.get("fit_supported_pair_contexts") == 25 and relation.get("fit_supported_directions") == 45, "ARCH-003 fit-stage summary mismatch")
    result.require("EXACT_VALUE_EQUIVALENT" in relation.get("authority_relationship", ""), "ARCH-003 shared-value equivalence is missing")
    construction = state.get("rule_construction_authority", {})
    result.require(construction.get("observed_feedback_actions") == 0, "ARCH-004 feedback action count mismatch")
    result.require("not detection performance" in construction.get("warning", ""), "ARCH-004 construction/utility boundary is missing")
    result.require("runtime authority" in construction.get("lifecycle", ""), "ARCH-004 lifecycle boundary is missing")
    verifier = state.get("verifier_common42_authority", {})
    result.require("20 ordered" in verifier.get("canonical_verifier", ""), "ARCH-005 verifier stage summary mismatch")
    result.require("PARTIALLY_OVERLAPPING" in verifier.get("task_canonical_relationship", ""), "ARCH-005 validity relationship mismatch")
    result.require("42 V4" in verifier.get("common42", ""), "ARCH-005 COMMON-42 definition mismatch")
    result.require(verifier.get("preferred_d1_term") == "COMMON-42 Verified Relational Rule-only", "ARCH-005 D1 terminology mismatch")
    result.require("committed one-attempt INNER execution grant" in verifier.get("d1_authority", ""), "ARCH-005 D1 authority summary mismatch")
    runtime = state.get("runtime_trace_explanation", {})
    result.require("V4 authority plane" in runtime.get("authority", ""), "ARCH-006 frozen D1 authority mismatch")
    result.require(runtime.get("llm_calls") == 0, "ARCH-006 frozen R0/D1 must remain LLM-free")
    result.require(runtime.get("freeze_classification") == "SAFE_BUT_WEAKER_THAN_D0_D2", "ARCH-006 freeze classification mismatch")
    result.require(runtime.get("durable_persistence") is False, "ARCH-006 must not overstate durable pre-label persistence")
    result.require("NON_EQUIVALENT" in runtime.get("canonical_trace_relationship", ""), "ARCH-006 trace relationship mismatch")
    result.require(runtime.get("human_usefulness") == "UNVALIDATED", "ARCH-006 explanation usefulness boundary mismatch")
    result.require("630 unique alarm" in runtime.get("prediction", ""), "ARCH-006 unique alarm summary mismatch")
    d0 = state.get("d0_detector", {})
    result.require(d0.get("detector_id") == "D0_PCA_SPE_V1" and d0.get("features") == 37, "ARCH-007 detector or feature contract mismatch")
    result.require(d0.get("fit_split") == "normal train1 + train2" and d0.get("calibration_split") == "normal train3", "ARCH-007 split authority mismatch")
    result.require(d0.get("variance_target") == 0.95 and d0.get("selected_components") == 10, "ARCH-007 PCA selection summary mismatch")
    result.require("score > threshold" in d0.get("comparator", ""), "ARCH-007 strict comparator mismatch")
    result.require(d0.get("labels_used_in_fit_or_calibration") is False, "ARCH-007 must remain normal-only")
    result.require(d0.get("prediction_freeze") == "DURABLY_PERSISTED_AND_REPLAYED_BEFORE_LABEL_ACCESS", "ARCH-007 freeze boundary mismatch")
    result.require(d0.get("point_alarms") == 876 and d0.get("alarm_episodes") == 46, "ARCH-007 point/episode counts mismatch")
    result.require(d0.get("attack_event_response") == "11/14" and d0.get("normal_false_alarm_episodes") == 7, "ARCH-007 frozen pilot semantics mismatch")
    result.require(d0.get("validation") == "PILOT_ONLY" and d0.get("fresh_machine_reproducibility") == "INCOMPLETE", "ARCH-007 scientific boundary mismatch")
    d1 = state.get("d1_evaluation", {})
    result.require(d1.get("preferred_name") == "COMMON-42 Verified Relational Rule-only", "ARCH-008 preferred D1 terminology mismatch")
    result.require(d1.get("opportunities") == 6031 and d1.get("anomalous_rule_records") == 788, "ARCH-008 opportunity or rule-record count mismatch")
    result.require(d1.get("unique_alarm_seconds") == 630 and d1.get("total_alarm_episodes") == 626, "ARCH-008 alarm second or episode count mismatch")
    result.require(d1.get("normal_false_episodes") == 574 and d1.get("normal_exposure_seconds") == 51019, "ARCH-008 normal false-alarm evidence mismatch")
    result.require(d1.get("attack_events_detected") == 13 and d1.get("pilot_events") == 14, "ARCH-008 attack-event evidence mismatch")
    result.require(d1.get("overlap") == {"both": 10, "d0_only": 1, "d1_only": 3, "neither": 0}, "ARCH-008 D0/D1 overlap mismatch")
    result.require(d1.get("durable_freeze") is False, "ARCH-008 must preserve the durable-freeze limitation")
    result.require(d1.get("llm_rule_only") == "NOT_DIRECTLY_TESTED" and d1.get("agentic_rule_only") == "MISLEADING_NOT_APPLICABLE", "ARCH-008 arm terminology boundary mismatch")
    result.require(d1.get("held_out_generalization") == "UNCONFIRMED", "ARCH-008 held-out status mismatch")
    d2 = state.get("d2_fusion", {})
    result.require(d2.get("event_unit_count") == 14 and "independence not established" in d2.get("event_unit_definition", ""), "ARCH-009 event-unit terminology mismatch")
    result.require(d2.get("raw_features_used") is False and d2.get("labels_used_in_fusion") is False, "ARCH-009 fusion boundary mismatch")
    result.require("VERIFIED_POINTWISE" in d2.get("d0_preservation", ""), "ARCH-009 D0 preservation missing")
    result.require(d2.get("v1", {}).get("threshold") == 2 and d2.get("v1", {}).get("attack_event_response") == "11/14", "ARCH-009 V1 policy/result mismatch")
    result.require(d2.get("v1", {}).get("normal_far_episodes_per_hour") == 0.7056194750975128 and d2.get("v1", {}).get("d0_miss_recovery") == "0/3", "ARCH-009 V1 FAR/recovery mismatch")
    result.require(d2.get("v2", {}).get("threshold") == 2 and d2.get("v2", {}).get("attack_event_response") == "11/14", "ARCH-009 V2 policy/result mismatch")
    result.require(d2.get("v2", {}).get("normal_far_episodes_per_hour") == 6.915070855955625 and d2.get("v2", {}).get("d0_miss_recovery") == "0/3", "ARCH-009 V2 FAR/recovery mismatch")
    result.require(d2.get("v1", {}).get("durable_pre_label_freeze") is True and d2.get("v2", {}).get("durable_pre_label_freeze") is True, "ARCH-009 durable freeze mismatch")
    result.require(d2.get("v2", {}).get("independent_confirmation") is False, "ARCH-009 V2 independence boundary mismatch")
    metrics = state.get("metric_integrity", {})
    result.require(metrics.get("event_unit_count") == 14 and metrics.get("event_independence") == "NOT_ESTABLISHED", "ARCH-010 event-unit boundary mismatch")
    result.require(metrics.get("normal_exposure_seconds") == 51019, "ARCH-010 normal exposure mismatch")
    result.require(metrics.get("comparability") == "SEMANTICALLY_EQUIVALENT" and metrics.get("fairness") == "FAIR_WITH_LIMITATIONS", "ARCH-010 comparability mismatch")
    result.require(metrics.get("overlap") == {"both": 10, "d0_only": 1, "d1_only": 3, "neither": 0}, "ARCH-010 overlap mismatch")
    result.require(metrics.get("inferential_statistics") == "NONE_FROZEN_OR_AUTHORITATIVE", "ARCH-010 inferential-statistics boundary mismatch")
    governance = state.get("data_governance", {})
    result.require(governance.get("dataset") == "HAI 23.05", "ARCH-001 dataset summary mismatch")
    result.require(governance.get("process") == "P1 Boiler", "ARCH-001 process summary mismatch")
    result.require(len(governance.get("splits", [])) == 6, "ARCH-001 split summary must cover train1-train4 and test1-test2")
    result.require("NO VERIFIED LEAKAGE FOUND" in governance.get("leakage_status", ""), "ARCH-001 leakage status is not conservative")
    result.require("pilot" in governance.get("test1_status", "").lower(), "test1 must remain pilot evidence")
    result.require("unavailable" in governance.get("test2_status", "").lower(), "test2 outcome must remain unavailable")
    semantics = state.get("status_semantics", {})
    result.require(
        set(semantics) == {
            "implementation_engineering_state", "audited_field", "result_integrity_audit",
            "claim_ready_field", "reproduced_field", "scientific_validation",
        },
        "status semantics contract is incomplete",
    )
    if semantics:
        result.require("source or evidence status" in semantics["audited_field"], "audited field semantics are ambiguous")
        result.require("not a performance-validation flag" in semantics["audited_field"], "audited field could imply performance validation")
        result.require("explicit result-specific integrity artifacts" in semantics["result_integrity_audit"], "result-integrity semantics are not artifact-specific")
        result.require("claims.csv" in semantics["claim_ready_field"], "claim_ready does not defer to claims.csv")
        result.require("narrow implementation or contract claim" in semantics["claim_ready_field"], "claim_ready is not narrowly scoped")
        result.require("independent reproduction" in semantics["reproduced_field"], "reproduction semantics are ambiguous")
        result.require("claims.csv" in semantics["scientific_validation"], "scientific validation is not claim-registry bound")
    summary = state.get("research_status_summary", {})
    result.require(
        set(summary) == {"engineering", "result_integrity", "scientific_validation", "reproducibility", "generalization", "claims"},
        "research status summary does not separate required dimensions",
    )
    result.require(
        state.get("safety_counters") == {
            "scientific_executions": 0,
            "test2_feature_accesses": 0,
            "test2_label_accesses": 0,
            "new_private_exposures": 0,
        },
        "RCC safety counters must remain zero",
    )
    try:
        timestamp = str(state["generated_at"])
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        result.require(timestamp.endswith("Z"), "generated_at must be UTC with a Z suffix")
    except (KeyError, ValueError):
        result.errors.append("generated_at is missing or not an ISO-8601 timestamp")

    for registry in ("experiments", "claims", "risks"):
        for row in data[registry]:
            result.require(row["scientific_source_ref"] == AUTHORITY_REF, f"{registry} row has a non-authoritative scientific source ref")
            result.require(row["scientific_source_commit"] == AUTHORITY_COMMIT, f"{registry} row has a non-authoritative scientific source commit")
    for row in data["components"]:
        expected = (OVERLAY_REF, OVERLAY_COMMIT) if row["component_id"] == "THESIS_DRAFT" else (AUTHORITY_REF, AUTHORITY_COMMIT)
        result.require(
            (row["scientific_source_ref"], row["scientific_source_commit"]) == expected,
            f"component {row['component_id']} has an invalid authority binding",
        )
    history = data.get("history", {})
    result.require(history.get("schema_version") == "rcc-history-v1", "history schema mismatch")
    result.require(history.get("scientific_authority") == {"ref": AUTHORITY_REF, "commit": AUTHORITY_COMMIT}, "history authority mismatch")
    result.require(
        history.get("documentation_overlay") == {"ref": OVERLAY_REF, "commit": OVERLAY_COMMIT, "role": "NARRATIVE_CONTEXT_ONLY"},
        "history overlay mismatch",
    )
    for registry in ("decisions", "timeline"):
        for row in data[registry]:
            if row["source"] in {"USER_CONTEXT", "USER_CONFIRMED_CONTEXT", "GAP_000_TRIAGE", "USER_APPROVED_VALIDATION_V2_POLICY"}:
                result.require(row["source_commit"] == "NONE", f"{registry} context-only row must not claim a Git commit")
            else:
                result.require(
                    row["source_commit"] in {AUTHORITY_COMMIT, OVERLAY_COMMIT, "e81baadcfd6cf6b9f23d307056455e024876c2ed"},
                    f"{registry} row has an unsupported source commit",
                )
    for row in data["artifacts"]:
        expected = (OVERLAY_REF, OVERLAY_COMMIT) if row["artifact_id"] == "ART-THESIS-DRAFT" else (AUTHORITY_REF, AUTHORITY_COMMIT)
        result.require((row["source_ref"], row["source_commit"]) == expected, f"artifact {row['artifact_id']} has an invalid authority binding")


def _validate_enums(data: Mapping[str, Any], result: ValidationResult) -> None:
    for registry, allowed in STATUS_ENUMS.items():
        for row in data[registry]:
            result.require(row["status"] in allowed, f"{registry} has invalid status {row['status']!r}")
    for row in data["components"]:
        result.require(row["lifecycle_stage"] in LIFECYCLE_STAGES, f"component has invalid lifecycle stage {row['lifecycle_stage']!r}")
        result.require(row["risk_level"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}, "component has invalid risk_level")
        for field_name in ("executed", "audited", "reproduced", "claim_ready"):
            result.require(row[field_name] in BOOLEAN_FIELDS, f"component {field_name} must be lowercase boolean")
        if row["audited"] == "true":
            result.require(
                row["executed"] == "true" or row["status"] == "PARTIAL",
                "audited component must also be executed unless the audit establishes a partial readiness state",
            )
        if row["reproduced"] == "true":
            result.require(row["audited"] == "true", "reproduced component must also be audited")
        if row["claim_ready"] == "true":
            result.require(row["audited"] == "true", "claim-ready component must also be audited")
    for row in data["claims"]:
        result.require(row["claim_type"] in CLAIM_TYPES, "claim has invalid claim_type")
    for row in data["risks"]:
        result.require(row["severity"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}, "risk has invalid severity")
        result.require(row["likelihood"] in {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}, "risk has invalid likelihood")
    for row in data["artifacts"]:
        result.require(row["public_private"] in {"PUBLIC_SAFE", "PRIVATE"}, "artifact has invalid public_private classification")
        for field_name in ("frozen", "audited", "current", "superseded"):
            result.require(row[field_name] in BOOLEAN_FIELDS, f"artifact {field_name} must be lowercase boolean")
        result.require(not (row["current"] == "true" and row["superseded"] == "true"), "artifact cannot be current and superseded")
    for row in data["decisions"]:
        result.require(row["user_approved"] in BOOLEAN_FIELDS, "decision user_approved must be lowercase boolean")
        result.require(row["date_precision"] in DATE_PRECISIONS, "decision has invalid date_precision")
        result.require(row["confidence"] in CONFIDENCE_LEVELS, "decision has invalid confidence")
    for row in data["timeline"]:
        result.require(row["event_type"] in EVENT_TYPES, "timeline has invalid event_type")
        result.require(row["date_precision"] in DATE_PRECISIONS, "timeline has invalid date_precision")


def _validate_dates(data: Mapping[str, Any], result: ValidationResult) -> None:
    for registry in ("decisions", "timeline"):
        for row in data[registry]:
            precision = row["date_precision"]
            value = row["date"]
            if precision == "DAY":
                pattern = r"\d{4}-\d{2}-\d{2}"
            elif precision == "MONTH":
                pattern = r"\d{4}-\d{2}"
            elif precision == "RANGE":
                pattern = r"\d{4}(?:-\d{2})?(?:-\d{2})? ~ \d{4}(?:-\d{2})?(?:-\d{2})?"
            else:
                pattern = r"(?:approximately )?\d{4}(?:-Q[1-4]|-\d{2})?"
            result.require(bool(re.fullmatch(pattern, value)), f"{registry} date does not match {precision} precision")


def _validate_references(data: Mapping[str, Any], result: ValidationResult) -> None:
    component_ids = {row["component_id"] for row in data["components"]}
    experiment_ids = {row["experiment_id"] for row in data["experiments"]}
    artifact_ids = {row["artifact_id"] for row in data["artifacts"]}
    decision_ids = {row["decision_id"] for row in data["decisions"]}
    event_ids = {row["event_id"] for row in data["timeline"]}
    component_targets = component_ids | {"PROJECT_WIDE"}
    artifact_actors = component_ids | {"PROJECT_GOVERNANCE", "EXTERNAL_GIT", "RCC"}

    for row in data["components"]:
        result.require(set(_split_refs(row["artifact_refs"])) <= artifact_ids, f"component {row['component_id']} has broken artifact_refs")
    for row in data["experiments"]:
        result.require(set(_split_refs(row["linked_component_ids"])) <= component_ids, f"experiment {row['experiment_id']} has broken linked_component_ids")
        result.require(set(_split_refs(row["artifact_refs"])) <= artifact_ids, f"experiment {row['experiment_id']} has broken artifact_refs")
    for row in data["claims"]:
        result.require(set(_split_refs(row["linked_experiment_ids"])) <= experiment_ids, f"claim {row['claim_id']} has broken linked_experiment_ids")
        for field_name in ("supporting_evidence", "contradicting_evidence"):
            for reference in _split_refs(row[field_name]):
                kind, separator, identifier = reference.partition(":")
                valid = separator == ":" and ((kind == "artifact" and identifier in artifact_ids) or (kind == "component" and identifier in component_ids) or (kind == "experiment" and identifier in experiment_ids))
                result.require(valid, f"claim {row['claim_id']} has broken {field_name}")
    for row in data["risks"]:
        result.require(row["affected_component"] in component_targets, f"risk {row['risk_id']} has broken affected_component")
        kind, separator, identifier = row["evidence"].partition(":")
        valid = separator == ":" and ((kind == "artifact" and identifier in artifact_ids) or (kind == "component" and identifier in component_ids))
        result.require(valid, f"risk {row['risk_id']} has broken evidence")
    for row in data["artifacts"]:
        result.require(row["producer"] in artifact_actors, f"artifact {row['artifact_id']} has broken producer")
        result.require(row["consumer"] in artifact_actors, f"artifact {row['artifact_id']} has broken consumer")
    for row in data["decisions"]:
        result.require(set(_split_refs(row["affected_components"])) <= component_targets, f"decision {row['decision_id']} has broken affected_components")
        result.require(set(_split_refs(row["supersedes"])) <= decision_ids, f"decision {row['decision_id']} has broken supersedes")
        result.require(set(_split_refs(row["superseded_by"])) <= decision_ids, f"decision {row['decision_id']} has broken superseded_by")
        result.require(row["decision_id"] not in _split_refs(row["supersedes"]), f"decision {row['decision_id']} cannot supersede itself")
        result.require(row["decision_id"] not in _split_refs(row["superseded_by"]), f"decision {row['decision_id']} cannot be superseded by itself")
    for row in data["timeline"]:
        result.require(set(_split_refs(row["affected_components"])) <= component_targets, f"timeline {row['event_id']} has broken affected_components")
        result.require(set(_split_refs(row["decision_refs"])) <= decision_ids, f"timeline {row['event_id']} has broken decision_refs")
        result.require(set(_split_refs(row["superseded_by"])) <= event_ids, f"timeline {row['event_id']} has broken superseded_by")
        result.require(row["event_id"] not in _split_refs(row["superseded_by"]), f"timeline {row['event_id']} cannot supersede itself")
    for row in data["decisions"]:
        for target in _split_refs(row["supersedes"]):
            target_row = next(item for item in data["decisions"] if item["decision_id"] == target)
            result.require(row["decision_id"] in _split_refs(target_row["superseded_by"]), f"decision supersedes relation is not reciprocal for {target}")
        for target in _split_refs(row["superseded_by"]):
            target_row = next(item for item in data["decisions"] if item["decision_id"] == target)
            result.require(row["decision_id"] in _split_refs(target_row["supersedes"]), f"decision superseded_by relation is not reciprocal for {row['decision_id']}")


def _validate_history(data: Mapping[str, Any], result: ValidationResult, repo_root: Path, check_git: bool) -> None:
    history = data["history"]
    result.require(15 <= len(data["timeline"]) <= 30, "timeline must contain 15 to 30 meaningful events")
    result.require(10 <= len(data["decisions"]) <= 25, "decision registry must contain 10 to 25 meaningful decisions")
    result.require(5 <= len(history.get("phases", [])) <= 12, "history must contain a concise major-phase sequence")
    result.require(1 <= len(history.get("confirmation_questions", [])) <= 10, "history confirmation queue must contain 1 to 10 high-value questions")
    dashboard_ids = history.get("dashboard_event_ids", [])
    result.require(8 <= len(dashboard_ids) <= 12, "dashboard history must select 8 to 12 milestones")
    result.require(len(dashboard_ids) == len(set(dashboard_ids)), "dashboard history contains duplicate event IDs")
    event_ids = {row["event_id"] for row in data["timeline"]}
    result.require(set(dashboard_ids) <= event_ids, "dashboard history references an unknown event")
    result.require("EVENT-013" in dashboard_ids, "dashboard history omits the August 4 professor-feedback milestone")
    result.require(
        history.get("safety_counters") == {
            "scientific_executions": 0,
            "test2_accesses": 0,
            "private_payload_accesses": 0,
            "production_changes": 0,
            "frozen_result_changes": 0,
            "new_private_exposures": 0,
        },
        "history safety counters must remain zero",
    )
    for item in history.get("phases", []):
        result.require(item["date_precision"] in DATE_PRECISIONS, "history phase has invalid date precision")
        result.require(item["status"] in HISTORY_STATUSES, "history phase has invalid status")
        result.require(item["confidence"] in CONFIDENCE_LEVELS, "history phase has invalid confidence")
        if item["source_class"].startswith("USER_CONTEXT"):
            result.require(item["confidence"] in {"LOW", "MEDIUM"}, "user-context phase has overstated confidence")
    questions = history.get("confirmation_questions", [])
    result.require(len({item["id"] for item in questions}) == len(questions), "history confirmation IDs are not unique")
    for item in questions:
        result.require(item["confidence"] in {"LOW", "MEDIUM"}, "history confirmation question has invalid confidence")
    professor = {item["date"]: item for item in history.get("professor_feedback_lineage", [])}
    result.require(professor.get("2026-08-18", {}).get("classification", "").endswith("NOT_PROFESSOR_FEEDBACK"), "August 18 is mislabeled as professor feedback")
    result.require(professor.get("2026-08-26", {}).get("classification", "").endswith("NOT_PROFESSOR_FEEDBACK"), "August 26 is mislabeled as professor feedback")
    august_four = professor.get("2026-08-04", {})
    result.require("CONTEXT" in august_four.get("classification", ""), "August 4 feedback context boundary is missing")
    result.require("reinforced" in august_four.get("interpretation", ""), "August 4 feedback is incorrectly presented as originating pairwise design")
    for row in data["timeline"]:
        if row["source"].startswith("USER_CONTEXT"):
            result.require("confidence" in row["notes"].lower(), f"timeline {row['event_id']} lacks user-context confidence")
        if check_git:
            for commit in re.findall(r"\b[0-9a-f]{40}\b", row["source_ref"]):
                completed = subprocess.run(["git", "-C", str(repo_root), "cat-file", "-e", commit], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                result.require(completed.returncode == 0, f"timeline {row['event_id']} cites an unresolved commit")
    for row in data["decisions"]:
        if row["source"].startswith("USER_CONTEXT"):
            result.require(row["user_approved"] == "false", f"decision {row['decision_id']} overstates user approval for unresolved user context")
    result.require(any(row["status"] == "SUPERSEDED" for row in data["decisions"]), "decision history lacks superseded decisions")
    result.require(any(row["status"] == "CONDITIONAL" for row in data["decisions"]), "decision history lacks conditional decisions")
    open_decisions = {row["decision_id"] for row in data["decisions"] if row["status"] == "OPEN"}
    result.require(open_decisions == set(), "decision registry contains an unexpected unresolved decision")
    decision_020 = next((row for row in data["decisions"] if row["decision_id"] == "DEC-020"), None)
    result.require(decision_020 is not None and decision_020["status"] == "ACTIVE" and decision_020["user_approved"] == "true", "Formal V4 decision is not recorded as active and user-approved")
    decision_021 = next((row for row in data["decisions"] if row["decision_id"] == "DEC-021"), None)
    result.require(decision_021 is not None and decision_021["status"] == "ACTIVE" and decision_021["user_approved"] == "true", "ARCH-011 user-approved conditional contribution policy is not recorded")
    risk_011 = next((row for row in data["risks"] if row["risk_id"] == "RISK-11"), None)
    result.require(risk_011 is not None and risk_011["status"] == "CLOSED", "VALIDATION V2 durable D1 custody risk is not prospectively closed")
    custody = data["state"].get("validation_v2_custody", {})
    result.require(custody.get("gap_fix_002") == "PASS", "GAP-FIX-002 custody status is not PASS")
    result.require(custody.get("pilot_v1_impact", "").startswith("NONE"), "GAP-FIX-002 must not rewrite PILOT V1")
    protocol = data["state"].get("validation_v2_protocol", {})
    result.require(protocol.get("v2_protocol_001") == "PASS", "V2-PROTOCOL-001 status is not PASS")
    result.require(protocol.get("protocol_source_commit") == "e014382feeea0ebb69280f11c099645b1ed192b6", "V2 protocol source commit mismatch")
    result.require(protocol.get("protocol_hash") == "2c3000a912caf2167bfe49929c55229e5159d52cc9ad09b7e48d79d9aecc562f", "V2 protocol hash mismatch")
    result.require("DEVELOPMENT_ONLY" in protocol.get("development_role", ""), "test1 is not frozen as development-only")
    result.require("no authorized operation" in protocol.get("heldout_role", ""), "held-out operation boundary is not fail-closed")
    result.require(protocol.get("pilot_v1_impact", "").startswith("NONE"), "V2-PROTOCOL-001 must not rewrite PILOT V1")


def _git_resolves_to(repo_root: Path, revision: str, expected: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--verify", revision],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return completed.returncode == 0 and completed.stdout.strip() == expected


def _validate_git_authorities(repo_root: Path, result: ValidationResult) -> None:
    result.require(
        _git_resolves_to(repo_root, f"refs/remotes/{AUTHORITY_REF}^{{commit}}", AUTHORITY_COMMIT),
        "local scientific authority ref does not resolve to the approved commit",
    )
    result.require(
        _git_resolves_to(repo_root, f"refs/tags/{IMMUTABLE_TAG}^{{}}", AUTHORITY_COMMIT),
        "local immutable scientific pin does not peel to the approved commit",
    )
    result.require(
        _git_resolves_to(repo_root, f"refs/remotes/{OVERLAY_REF}^{{commit}}", OVERLAY_COMMIT),
        "local documentation overlay ref does not resolve to the approved commit",
    )


def is_safe_relative_path(value: str) -> bool:
    if not value or value == "NONE" or "\\" in value or "\x00" in value:
        return False
    if re.match(r"^[A-Za-z]:", value) or value.startswith(("/", "~", "$", "%", "//")):
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _git_has_path(repo_root: Path, commit: str, path: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{commit}:{path}"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=False,
    )
    return completed.returncode == 0


def _validate_paths(data: Mapping[str, Any], result: ValidationResult, repo_root: Path, check_git: bool) -> None:
    candidates: list[tuple[str, str]] = []
    for row in data["components"]:
        candidates.append((f"component {row['component_id']} representative_path", row["representative_path"]))
        for value in _split_refs(row["test_refs"]):
            candidates.append((f"component {row['component_id']} test_refs", value))
    for row in data["artifacts"]:
        if row["public_private"] == "PUBLIC_SAFE":
            commit = OVERLAY_COMMIT if row["artifact_id"] == "ART-THESIS-DRAFT" else AUTHORITY_COMMIT
            candidates.append((f"artifact {row['artifact_id']} safe_path", row["safe_path"], commit))
        else:
            result.require(row["safe_path"] in {"LOCAL_DATA_CUSTODY", "PRIVATE_ARTIFACT_CUSTODY"}, f"private artifact {row['artifact_id']} lacks a symbolic safe identity")
    normalized: list[tuple[str, str, str]] = []
    for candidate in candidates:
        if len(candidate) == 2:
            label, value = candidate
            commit = OVERLAY_COMMIT if "THESIS_DRAFT" in label else AUTHORITY_COMMIT
            normalized.append((label, value, commit))
        else:
            normalized.append(candidate)
    for label, value, commit in normalized:
        safe = is_safe_relative_path(value)
        result.require(safe, f"{label} is not a safe relative path")
        if safe and check_git:
            tree_name = "documentation overlay" if commit == OVERLAY_COMMIT else "pinned scientific Git tree"
            result.require(_git_has_path(repo_root, commit, value), f"{label} is absent from the {tree_name}")


def privacy_exposures(rcc_root: Path) -> list[str]:
    """Return sanitized locations of private-locator patterns in new RCC files."""

    private_tokens = (
        "".join(("HAI", "_DATA_ROOT")),
        "".join(("TASK039E3", "_D0_PCA_SPE_MODEL_V1")),
        "".join(("TASK039E3", "_D0_PCA_SPE_THRESHOLD_V1")),
        "".join((".env", ".custody.local")),
        "".join(("hai-", "test2")),
        "".join(("label-", "test2")),
    )
    drive_path = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
    home_path = re.compile(r"/(?:home|Users)/[^/\s]+/")
    allowed_suffixes = {".md", ".csv", ".yaml", ".json", ".html", ".css", ".js", ".py", ".bat"}
    findings: list[str] = []
    for path in sorted(rcc_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        relative = path.relative_to(rcc_root)
        if relative.parts[:2] == ("bootstrap", "RCC_000"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if drive_path.search(text) or home_path.search(text) or any(token in text for token in private_tokens):
            findings.append(relative.as_posix())
    return findings


def _validate_privacy(rcc_root: Path, result: ValidationResult) -> None:
    findings = privacy_exposures(rcc_root)
    result.require(not findings, "new RCC files contain private-locator patterns: " + ", ".join(findings))


def _validate_outputs(rcc_root: Path, data: Mapping[str, Any], result: ValidationResult) -> None:
    digest = registry_digest(rcc_root)
    state = data["state"]
    marker = f"registry_version={state['registry_version']} registry_digest={digest} authority={AUTHORITY_COMMIT}"
    for relative in GENERATED_FILES:
        path = rcc_root / relative
        result.require(path.is_file(), f"generated output missing: {relative}")
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            result.require(marker in text, f"generated output is stale or unbound: {relative}")
            result.require(AUTHORITY_COMMIT in text, f"generated output omits scientific authority: {relative}")
    html_path = rcc_root / "dashboard" / "index.html"
    if html_path.is_file():
        dashboard = html_path.read_text(encoding="utf-8")
        result.require(not re.search(r'<(?:script|link)[^>]+(?:https?:)?//', dashboard), "dashboard contains an external network resource")
        result.require(AUTHORITY_COMMIT in dashboard, "dashboard omits scientific authority")
        result.require("전체 완료율은 만들지 않습니다." in dashboard, "dashboard omits the no-completion-percentage warning")
        result.require("구현 완료, 실행 완료, 결과 무결성 확인, 과학적 검증, 재현성, 일반화는 서로 다른 상태입니다." in dashboard, "dashboard does not separate status concepts")
        result.require("근거 점검 완료" in dashboard, "dashboard does not translate the component audited field")
        result.require("결과 무결성" in dashboard, "dashboard does not display result integrity separately")
        result.require("claims.csv" in dashboard, "dashboard does not identify the authoritative claim registry")
        result.require("Claim-ready" not in dashboard, "dashboard still headlines component claim-ready status")
        result.require(dashboard.count('class="primary-nav-item') == 5, "dashboard primary navigation must contain exactly five items")
        result.require(dashboard.count('id="map-svg-NODE_') == 14, "dashboard architecture map must contain fourteen top-level nodes")
        for heading in ("현재 연구 단계", "전체 연구 시스템 지도", "실험·결과", "준비도·위험", "이력·근거"):
            result.require(heading in dashboard, f"dashboard omits required section {heading}")
    required_semantic_outputs = {
        "generated/CURRENT_STATUS.md": ("Evidence-reviewed", "결과 무결성 확인", "claims.csv", "하나의 완료율이 아니며"),
        "generated/GPT_BRIEF.md": ("Evidence-reviewed", "Result-integrity audit", "claims.csv", "not a single completion percentage"),
        "generated/RCC_002_USER_SUMMARY.md": ("Evidence-reviewed", "Result-integrity audited", "claims.csv", "하나의 연구 완료율"),
        "generated/RCC_003_HISTORY_SUMMARY.md": ("우리 연구가 어떻게 여기까지 왔나", "pilot evidence", "홀드아웃 일반화"),
        "generated/ARCH_001_USER_SUMMARY.md": ("우리가 어떤 데이터를 쓰고 있는가", "test1", "test2", "NO VERIFIED LEAKAGE FOUND"),
        "generated/ARCH_002_USER_SUMMARY.md": ("관계 후보는 왜 세 방식으로 고르는가", "META", "STAT", "GDN", "47개"),
        "generated/ARCH_003_USER_SUMMARY.md": ("47개 후보는 어떻게 42개 실행 관계가 되는가", "train3", "Numeric authority", "causal relation"),
        "generated/ARCH_004_USER_SUMMARY.md": ("Rule은 어떻게 만들어지는가", "Evidence Pack", "39/42", "runtime authorization"),
        "generated/ARCH_005_USER_SUMMARY.md": ("COMMON-42", "20단계", "runtime authorization", "다음 task"),
        "generated/ARCH_006_USER_SUMMARY.md": ("Rule은 실제 시계열에서 어떻게 판단하는가", "630 unique alarm seconds", "RuntimeTraceV1", "다음 task"),
        "generated/ARCH_007_USER_SUMMARY.md": ("D0 PCA-SPE를 쉽게 이해하기", "q=.999", "11/14", "stronger detector", "다음 task"),
        "generated/ARCH_008_USER_SUMMARY.md": ("D1 검증된 관계 규칙 단독 평가", "788", "574", "13/14", "다음 task"),
        "generated/ARCH_009_USER_SUMMARY.md": ("D2에서 Detector와 Rule을 어떻게 합쳤는가", "same-second", "native horizon", "0/3", "GAP-FIX-METRIC-001"),
        "generated/ARCH_010_USER_SUMMARY.md": ("성능 숫자를 어떻게 읽어야 하는가", "51,019", "FAIR_WITH_LIMITATIONS", "integrity PASS", "GAP-FIX-METRIC-001"),
        "generated/GAP_000_USER_SUMMARY.md": ("본격 실험 전에 무엇을 고쳐야 하는가", "PILOT V1", "VALIDATION V2", "primary disposition", "Urgency priority", "Graph-Guided", "Agentic"),
        "generated/ARCH_011_USER_SUMMARY.md": ("OUTER와 재현성을 쉽게 이해하기", "NOT_RETRYABLE", "fresh-machine", "PILOT V1", "VALIDATION V2", "GAP-FIX-METRIC-001"),
        "history/PROJECT_TIMELINE.md": ("Research Evolution", "USER_CONTEXT", "What survived into the current method"),
        "history/PROFESSOR_FEEDBACK_LINEAGE.md": ("2026-08-18", "not professor feedback", "2026-08-26"),
        "history/SUPERSEDED_DIRECTIONS.md": ("Superseded and Conditional Directions", "Do not use as current claim"),
        "history/TERMINOLOGY_GUIDE.md": ("Historical Terminology Guide", "Current preferred meaning"),
        "history/HISTORY_CONFIRMATION_NEEDED.md": ("History Confirmation Needed", "HIST-Q002"),
    }
    for relative, phrases in required_semantic_outputs.items():
        path = rcc_root / relative
        if path.is_file():
            payload = path.read_text(encoding="utf-8")
            for phrase in phrases:
                result.require(phrase in payload, f"{relative} omits status-semantic phrase {phrase!r}")
    decision_files = sorted((rcc_root / "history" / "decisions").glob("DEC-*.md"))
    result.require(len(decision_files) == len(data["decisions"]), "generated decision-record count does not match decisions.csv")
    expected_prefixes = {row["decision_id"] for row in data["decisions"]}
    actual_prefixes = {"-".join(path.stem.split("-")[:2]) for path in decision_files}
    result.require(actual_prefixes == expected_prefixes, "generated decision records do not cover every decision ID")
    for path in decision_files:
        payload = path.read_text(encoding="utf-8")
        result.require(marker in payload, f"decision record is stale or unbound: {path.name}")


def _validate_architecture(rcc_root: Path, data: Mapping[str, Any], result: ValidationResult, repo_root: Path, check_git: bool) -> None:
    overview = rcc_root / "architecture" / "00_overview"
    required = {
        "ARCH_000_SOURCE_MAP.csv", "ARCH_000_ENTRYPOINT_MAP.csv", "ARCH_000_DATAFLOW.csv",
        "ARCH_000_ARTIFACT_LINEAGE.csv", "ARCH_000_RESULT_LINEAGE.md",
        "ARCH_000_CORE_GOVERNANCE_MAP.md", "ARCH_000_LEGACY_AND_GAPS.md",
        "ARCH_000_ARCHITECTURE.mmd", "ARCH_000_REPORT.md", "ARCH_000_MISMATCHES.md",
        "ARCH_000_COMPONENT_DETAIL.csv", "DEEP_REVIEW_INDEX.md",
    }
    if not overview.is_dir():
        return
    for name in required:
        result.require((overview / name).is_file(), f"ARCH-000 output missing: {name}")
    if result.errors:
        return
    def rows(name: str) -> list[dict[str, str]]:
        with (overview / name).open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    source = rows("ARCH_000_SOURCE_MAP.csv")
    edges = rows("ARCH_000_DATAFLOW.csv")
    artifacts = rows("ARCH_000_ARTIFACT_LINEAGE.csv")
    details = rows("ARCH_000_COMPONENT_DETAIL.csv")
    component_ids = {row["component_id"] for row in data["components"]}
    result.require(len(source) == 32 and {row["component_id"] for row in source} == component_ids, "ARCH-000 source map does not cover 32 RCC components")
    result.require(len(details) == 11, "ARCH-000 dashboard detail map does not cover 11 review domains")
    result.require(all(row["verified"] in {"TRUE", "UNKNOWN"} for row in edges), "ARCH-000 dataflow contains an invalid verification state")
    for row in edges:
        result.require(row["from_component"] in component_ids and row["to_component"] in component_ids, f"ARCH-000 edge {row['edge_id']} has an unknown component")
    result.require(len({row["edge_id"] for row in edges}) == len(edges), "ARCH-000 edge IDs are not unique")
    result.require(len({row["artifact_id"] for row in artifacts}) == len(artifacts), "ARCH-000 artifact IDs are not unique")
    for row in source:
        result.require(is_safe_relative_path(row["path"]), f"ARCH-000 source path for {row['component_id']} is unsafe")
        if check_git:
            result.require(_git_has_path(repo_root, row["source_commit"], row["path"]), f"ARCH-000 source path for {row['component_id']} is absent from its pinned tree")
    mermaid = (overview / "ARCH_000_ARCHITECTURE.mmd").read_text(encoding="utf-8")
    result.require(mermaid.startswith("flowchart "), "ARCH-000 Mermaid does not declare a flowchart")
    result.require("-." in mermaid, "ARCH-000 Mermaid omits dotted unverified/documented-only edges")
    result.require((rcc_root / "generated" / "ARCH_000_USER_SUMMARY.md").is_file(), "ARCH-000 user summary is missing")

    deep = rcc_root / "architecture" / "01_data_and_splits"
    required_deep = {
        "ARCH_001_REPORT.md", "ARCH_001_LABEL_ACCESS_TIMELINE.md",
        "ARCH_001_LEAKAGE_MATRIX.csv", "ARCH_001_INPUT_CONTRACTS.csv",
        "ARCH_001_FUNCTION_CATALOG.csv", "ARCH_001_SPLIT_FLOW.mmd",
        "ARCH_001_MISMATCHES.md",
    }
    for name in required_deep:
        result.require((deep / name).is_file(), f"ARCH-001 output missing: {name}")
    if not deep.is_dir() or any(not (deep / name).is_file() for name in required_deep):
        return
    with (deep / "ARCH_001_LEAKAGE_MATRIX.csv").open("r", encoding="utf-8", newline="") as handle:
        matrix = list(csv.DictReader(handle))
    allowed_cells = {"READ_ALLOWED", "READ_NOT_USED", "FORBIDDEN", "UNKNOWN", "NOT_APPLICABLE"}
    result.require(len(matrix) >= 20, "ARCH-001 leakage matrix is incomplete")
    result.require(len({row["stage"] for row in matrix}) == len(matrix), "ARCH-001 leakage stages are not unique")
    for row in matrix:
        result.require(all(value in allowed_cells for key, value in row.items() if key != "stage"), f"ARCH-001 leakage matrix has invalid enum at {row['stage']}")
    with (deep / "ARCH_001_INPUT_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        contracts = list(csv.DictReader(handle))
    with (deep / "ARCH_001_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        functions = list(csv.DictReader(handle))
    result.require(len(contracts) >= 15, "ARCH-001 input contract catalog is incomplete")
    result.require(len({row["contract_id"] for row in contracts}) == len(contracts), "ARCH-001 contract IDs are not unique")
    result.require(len(functions) >= 20, "ARCH-001 function catalog is incomplete")
    result.require(all(is_safe_relative_path(row["path"]) for row in functions), "ARCH-001 function catalog contains an unsafe source path")
    mermaid_deep = (deep / "ARCH_001_SPLIT_FLOW.mmd").read_text(encoding="utf-8")
    result.require(mermaid_deep.startswith("flowchart "), "ARCH-001 Mermaid does not declare a flowchart")
    result.require("0 feature bytes read" in mermaid_deep, "ARCH-001 Mermaid obscures the OUTER byte-read boundary")

    discovery = rcc_root / "architecture" / "02_candidate_discovery"
    required_discovery = {
        "ARCH_002_REPORT.md", "ARCH_002_GDN_PROFESSOR_ANSWER.md",
        "ARCH_002_ARM_COMPARISON.csv", "ARCH_002_CANDIDATE_PROVENANCE.csv",
        "ARCH_002_FUNCTION_CATALOG.csv", "ARCH_002_IO_CONTRACTS.csv",
        "ARCH_002_DISCOVERY_FLOW.mmd", "ARCH_002_MISMATCHES.md",
    }
    for name in required_discovery:
        result.require((discovery / name).is_file(), f"ARCH-002 output missing: {name}")
    if not discovery.is_dir() or any(not (discovery / name).is_file() for name in required_discovery):
        return
    with (discovery / "ARCH_002_CANDIDATE_PROVENANCE.csv").open("r", encoding="utf-8", newline="") as handle:
        candidates = list(csv.DictReader(handle))
    with (discovery / "ARCH_002_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        discovery_functions = list(csv.DictReader(handle))
    with (discovery / "ARCH_002_IO_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        discovery_contracts = list(csv.DictReader(handle))
    result.require(len(candidates) == 47, "ARCH-002 provenance does not contain 47 candidates")
    result.require(len({row["pair_id"] for row in candidates}) == 47, "ARCH-002 pair IDs are not unique")
    result.require(len({(row["source"], row["target"]) for row in candidates}) == 47, "ARCH-002 pair identities are not unique")
    result.require(sum(row["meta_selected"] == "true" for row in candidates) == 20, "ARCH-002 META provenance count mismatch")
    result.require(sum(row["stat_selected"] == "true" for row in candidates) == 20, "ARCH-002 STAT provenance count mismatch")
    result.require(sum(row["gdn_selected"] == "true" for row in candidates) == 20, "ARCH-002 GDN provenance count mismatch")
    result.require(all(row["safe_artifact_reference"] == "docs/task_reports/TASK-039C_CANDIDATE_PROFILING_COHORT.json" for row in candidates), "ARCH-002 provenance has an unexpected artifact reference")
    result.require(len(discovery_functions) >= 30, "ARCH-002 function catalog is incomplete")
    result.require(all(is_safe_relative_path(row["path"]) for row in discovery_functions), "ARCH-002 function catalog contains an unsafe source path")
    result.require(len(discovery_contracts) >= 7, "ARCH-002 IO contract catalog is incomplete")
    mermaid_discovery = (discovery / "ARCH_002_DISCOVERY_FLOW.mmd").read_text(encoding="utf-8")
    result.require(mermaid_discovery.startswith("flowchart "), "ARCH-002 Mermaid does not declare a flowchart")
    result.require("UNSCORED SET UNION" in mermaid_discovery and "Post-hoc XAI" in mermaid_discovery, "ARCH-002 Mermaid omits required discovery boundaries")

    relation = rcc_root / "architecture" / "03_relation_and_numeric"
    required_relation = {
        "ARCH_003_REPORT.md", "ARCH_003_RELATION_SCHEMA.md", "ARCH_003_METRIC_DEFINITIONS.md",
        "ARCH_003_RELATION_LINEAGE.csv", "ARCH_003_NUMERIC_AUTHORITY.csv",
        "ARCH_003_CONSTRUCTION_RUNTIME_AUTHORITY.md", "ARCH_003_FUNCTION_CATALOG.csv",
        "ARCH_003_IO_CONTRACTS.csv", "ARCH_003_RELATION_FLOW.mmd", "ARCH_003_MISMATCHES.md",
    }
    for name in required_relation:
        result.require((relation / name).is_file(), f"ARCH-003 output missing: {name}")
    if not relation.is_dir() or any(not (relation / name).is_file() for name in required_relation):
        return
    with (relation / "ARCH_003_RELATION_LINEAGE.csv").open("r", encoding="utf-8", newline="") as handle:
        relation_rows = list(csv.DictReader(handle))
    with (relation / "ARCH_003_NUMERIC_AUTHORITY.csv").open("r", encoding="utf-8", newline="") as handle:
        numeric_rows = list(csv.DictReader(handle))
    with (relation / "ARCH_003_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        relation_functions = list(csv.DictReader(handle))
    with (relation / "ARCH_003_IO_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        relation_contracts = list(csv.DictReader(handle))
    result.require(len(relation_rows) == 4, "ARCH-003 sanitized relation lineage is incomplete")
    result.require(sum(int(row["final_relation_count"]) for row in relation_rows) == 42, "ARCH-003 final relation count mismatch")
    result.require(len(numeric_rows) == 21, "ARCH-003 numeric role catalog must contain 11 construction and 10 runtime rows")
    result.require(sum(row["construction_or_runtime"] == "construction" for row in numeric_rows) == 11, "ARCH-003 construction role count mismatch")
    result.require(sum(row["construction_or_runtime"] == "runtime" for row in numeric_rows) == 10, "ARCH-003 runtime role count mismatch")
    result.require(len(relation_functions) >= 20, "ARCH-003 function catalog is incomplete")
    result.require(all(is_safe_relative_path(row["path"]) for row in relation_functions), "ARCH-003 function catalog contains an unsafe source path")
    result.require(len(relation_contracts) >= 9, "ARCH-003 IO contract catalog is incomplete")
    mermaid_relation = (relation / "ARCH_003_RELATION_FLOW.mmd").read_text(encoding="utf-8")
    result.require(mermaid_relation.startswith("flowchart "), "ARCH-003 Mermaid does not declare a flowchart")
    result.require("45 directions" in mermaid_relation and "42 directional relations" in mermaid_relation, "ARCH-003 Mermaid omits the fit/confirmation boundary")

    construction = rcc_root / "architecture" / "04_rule_construction"
    required_construction = {
        "ARCH_004_REPORT.md", "ARCH_004_EVIDENCE_PACK_SCHEMA.md", "ARCH_004_EVIDENCE_LINEAGE.csv",
        "ARCH_004_RULE_DSL.md", "ARCH_004_T2_FEEDBACK_LOOP.md", "ARCH_004_AGENTIC_CLAIM_BOUNDARY.md",
        "ARCH_004_ARM_OUTCOMES.csv", "ARCH_004_FUNCTION_CATALOG.csv", "ARCH_004_IO_CONTRACTS.csv",
        "ARCH_004_RULE_CONSTRUCTION_FLOW.mmd", "ARCH_004_MISMATCHES.md",
    }
    for name in required_construction:
        result.require((construction / name).is_file(), f"ARCH-004 output missing: {name}")
    if not construction.is_dir() or any(not (construction / name).is_file() for name in required_construction):
        return
    with (construction / "ARCH_004_ARM_OUTCOMES.csv").open("r", encoding="utf-8", newline="") as handle:
        arm_rows = list(csv.DictReader(handle))
    with (construction / "ARCH_004_EVIDENCE_LINEAGE.csv").open("r", encoding="utf-8", newline="") as handle:
        evidence_rows = list(csv.DictReader(handle))
    with (construction / "ARCH_004_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        construction_functions = list(csv.DictReader(handle))
    with (construction / "ARCH_004_IO_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        construction_contracts = list(csv.DictReader(handle))
    result.require([row["arm"] for row in arm_rows] == ["T0", "T1", "T1-B", "T2"], "ARCH-004 arm outcomes are incomplete")
    result.require([int(row["task_specific_admissible"]) for row in arm_rows] == [42, 42, 42, 39], "ARCH-004 accepted proposal counts differ")
    result.require(int(arm_rows[3]["feedback_actions"]) == 0 and int(arm_rows[3]["retrieval_actions"]) == 0, "ARCH-004 observed T2 feedback differs")
    result.require(len(evidence_rows) == 4 and all(row["verified"] == "true" for row in evidence_rows), "ARCH-004 evidence lineage is incomplete")
    result.require(len(construction_functions) >= 20, "ARCH-004 function catalog is incomplete")
    result.require(all(is_safe_relative_path(row["path"]) for row in construction_functions), "ARCH-004 function catalog contains an unsafe source path")
    result.require(len(construction_contracts) >= 10, "ARCH-004 IO contract catalog is incomplete")
    mermaid_construction = (construction / "ARCH_004_RULE_CONSTRUCTION_FLOW.mmd").read_text(encoding="utf-8")
    result.require(mermaid_construction.startswith("flowchart "), "ARCH-004 Mermaid does not declare a flowchart")
    result.require("revise 0 / retrieve 0" in mermaid_construction and "later authority" in mermaid_construction, "ARCH-004 Mermaid omits feedback or lifecycle boundary")

    verifier = rcc_root / "architecture" / "05_verifier_common42"
    required_verifier = {
        "ARCH_005_REPORT.md", "ARCH_005_RULE_LIFECYCLE.md", "ARCH_005_CANONICAL_RULE_SCHEMA.md",
        "ARCH_005_VERIFIER_STAGES.csv", "ARCH_005_VALIDITY_EQUIVALENCE.csv", "ARCH_005_COMMON42.md",
        "ARCH_005_ARM_PORTFOLIO_MAPPING.csv", "ARCH_005_PORTFOLIO_FREEZE.md",
        "ARCH_005_RUNTIME_AUTHORIZATION.md", "ARCH_005_HASH_CHAIN.csv", "ARCH_005_NO_RULE_TAXONOMY.md",
        "ARCH_005_PROFESSOR_TERMINOLOGY.md", "ARCH_005_FUNCTION_CATALOG.csv",
        "ARCH_005_IO_CONTRACTS.csv", "ARCH_005_VERIFIER_PORTFOLIO_FLOW.mmd", "ARCH_005_MISMATCHES.md",
        "ARCH_005_HIGH_RISK_DISPOSITION.md",
    }
    for name in required_verifier:
        result.require((verifier / name).is_file(), f"ARCH-005 output missing: {name}")
    if not verifier.is_dir() or any(not (verifier / name).is_file() for name in required_verifier):
        return
    with (verifier / "ARCH_005_VERIFIER_STAGES.csv").open("r", encoding="utf-8", newline="") as handle:
        stage_rows = list(csv.DictReader(handle))
    with (verifier / "ARCH_005_VALIDITY_EQUIVALENCE.csv").open("r", encoding="utf-8", newline="") as handle:
        validity_rows = list(csv.DictReader(handle))
    with (verifier / "ARCH_005_ARM_PORTFOLIO_MAPPING.csv").open("r", encoding="utf-8", newline="") as handle:
        mapping_rows = list(csv.DictReader(handle))
    with (verifier / "ARCH_005_HASH_CHAIN.csv").open("r", encoding="utf-8", newline="") as handle:
        hash_rows = list(csv.DictReader(handle))
    with (verifier / "ARCH_005_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        function_rows = list(csv.DictReader(handle))
    with (verifier / "ARCH_005_IO_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        contract_rows = list(csv.DictReader(handle))
    result.require(len(stage_rows) == 20 and [int(row["stage_order"]) for row in stage_rows] == list(range(1, 21)), "ARCH-005 verifier stage map must contain ordered stages 1-20")
    result.require(len(validity_rows) >= 14, "ARCH-005 validity equivalence matrix is incomplete")
    result.require([row["arm"] for row in mapping_rows] == ["T0", "T1", "T1-B", "T2"], "ARCH-005 arm mapping is incomplete")
    result.require(mapping_rows[3]["D1_used"] == "no", "ARCH-005 T2 must remain outside D1 authority")
    result.require(all(row["D1_used"] == "shared_projection_only" for row in mapping_rows[:3]), "ARCH-005 common arms must not imply direct artifact loading")
    result.require(len(hash_rows) >= 12, "ARCH-005 hash chain is incomplete")
    result.require(len(function_rows) >= 15 and all(is_safe_relative_path(row["path"]) for row in function_rows), "ARCH-005 function catalog is incomplete or unsafe")
    result.require(len(contract_rows) >= 10, "ARCH-005 IO contracts are incomplete")
    mermaid_verifier = (verifier / "ARCH_005_VERIFIER_PORTFOLIO_FLOW.mmd").read_text(encoding="utf-8")
    result.require(mermaid_verifier.startswith("flowchart "), "ARCH-005 Mermaid does not declare a flowchart")
    result.require("no tracked materialization bridge" in mermaid_verifier and "T2: 39 accepted + 3 no_rule" in mermaid_verifier, "ARCH-005 Mermaid omits the authority or T2 boundary")
    disposition = (verifier / "ARCH_005_HIGH_RISK_DISPOSITION.md").read_text(encoding="utf-8")
    for status in ("RESOLVED", "PARTIALLY_RESOLVED", "DEFER_TO_ARCH_006", "REQUIRES_CODE_FIX"):
        result.require(status in disposition, f"ARCH-005 carryover disposition omits {status}")

    runtime = rcc_root / "architecture" / "06_runtime_trace_explanation"
    required_runtime = {
        "ARCH_006_REPORT.md", "ARCH_006_RUNTIME_STATE_MACHINE.md", "ARCH_006_OUTCOME_TAXONOMY.md",
        "ARCH_006_D1_PREDICTION_SCHEMA.md", "ARCH_006_D1_FREEZE_BOUNDARY.md",
        "ARCH_006_TRACE_SCHEMA.csv", "ARCH_006_TRACE_HASH_CHAIN.md",
        "ARCH_006_EXPLANATION_RENDERER.md", "ARCH_006_R1_INPUT_BOUNDARY.md",
        "ARCH_006_FUNCTION_CATALOG.csv", "ARCH_006_IO_CONTRACTS.csv",
        "ARCH_006_RUNTIME_FLOW.mmd", "ARCH_006_CARRYOVER_DISPOSITION.md", "ARCH_006_MISMATCHES.md",
    }
    for name in required_runtime:
        result.require((runtime / name).is_file(), f"ARCH-006 output missing: {name}")
    if not runtime.is_dir() or any(not (runtime / name).is_file() for name in required_runtime):
        return
    with (runtime / "ARCH_006_TRACE_SCHEMA.csv").open("r", encoding="utf-8", newline="") as handle:
        trace_rows = list(csv.DictReader(handle))
    with (runtime / "ARCH_006_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        runtime_functions = list(csv.DictReader(handle))
    with (runtime / "ARCH_006_IO_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        runtime_contracts = list(csv.DictReader(handle))
    result.require(len(trace_rows) >= 14, "ARCH-006 trace schema comparison is incomplete")
    result.require(any(row["semantic_equivalent"] == "NO" for row in trace_rows), "ARCH-006 trace comparison must preserve non-equivalence")
    result.require(len(runtime_functions) >= 13 and all(is_safe_relative_path(row["path"]) for row in runtime_functions), "ARCH-006 function catalog is incomplete or unsafe")
    result.require(len(runtime_contracts) >= 10, "ARCH-006 IO contracts are incomplete")
    runtime_flow = (runtime / "ARCH_006_RUNTIME_FLOW.mmd").read_text(encoding="utf-8")
    result.require(runtime_flow.startswith("flowchart "), "ARCH-006 Mermaid does not declare a flowchart")
    result.require("LABEL-BLIND RUNTIME" in runtime_flow and "LABEL ACCESS" in runtime_flow, "ARCH-006 Mermaid omits label boundary")
    result.require("RuntimeTraceV1" in (runtime / "ARCH_006_TRACE_HASH_CHAIN.md").read_text(encoding="utf-8"), "ARCH-006 trace authority boundary is missing")
    result.require("SAFE_BUT_WEAKER_THAN_D0_D2" in (runtime / "ARCH_006_D1_FREEZE_BOUNDARY.md").read_text(encoding="utf-8"), "ARCH-006 freeze classification is missing")

    d0_dir = rcc_root / "architecture" / "07_d0_detector"
    required_d0 = {
        "ARCH_007_REPORT.md", "ARCH_007_D0_ROLE.md", "ARCH_007_FEATURE_CONTRACT.md",
        "ARCH_007_SPE_DEFINITION.md", "ARCH_007_D0_STATE_MACHINE.md",
        "ARCH_007_ARTIFACT_LINEAGE.csv", "ARCH_007_FREEZE_BOUNDARY.md",
        "ARCH_007_OUTPUT_LEVELS.md", "ARCH_007_FUNCTION_CATALOG.csv",
        "ARCH_007_IO_CONTRACTS.csv", "ARCH_007_D0_FLOW.mmd", "ARCH_007_MISMATCHES.md",
    }
    for name in required_d0:
        result.require((d0_dir / name).is_file(), f"ARCH-007 output missing: {name}")
    if not d0_dir.is_dir() or any(not (d0_dir / name).is_file() for name in required_d0):
        return
    with (d0_dir / "ARCH_007_ARTIFACT_LINEAGE.csv").open("r", encoding="utf-8", newline="") as handle:
        d0_artifacts = list(csv.DictReader(handle))
    with (d0_dir / "ARCH_007_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        d0_functions = list(csv.DictReader(handle))
    with (d0_dir / "ARCH_007_IO_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        d0_contracts = list(csv.DictReader(handle))
    result.require(len(d0_artifacts) >= 8, "ARCH-007 artifact lineage is incomplete")
    result.require(len(d0_functions) >= 14 and all(is_safe_relative_path(row["path"]) for row in d0_functions), "ARCH-007 function catalog is incomplete or unsafe")
    result.require(len(d0_contracts) >= 12, "ARCH-007 IO contracts are incomplete")
    d0_flow = (d0_dir / "ARCH_007_D0_FLOW.mmd").read_text(encoding="utf-8")
    result.require(d0_flow.startswith("flowchart ") and "LABEL-BLIND DURABLE FREEZE" in d0_flow, "ARCH-007 Mermaid omits flow or label boundary")
    result.require("score == threshold" in (d0_dir / "ARCH_007_D0_STATE_MACHINE.md").read_text(encoding="utf-8"), "ARCH-007 threshold equality semantics missing")
    result.require("FAR/hour" in (d0_dir / "ARCH_007_OUTPUT_LEVELS.md").read_text(encoding="utf-8"), "ARCH-007 output-level distinction missing")

    d1_dir = rcc_root / "architecture" / "08_d1_rule_only"
    required_d1 = {
        "ARCH_008_REPORT.md", "ARCH_008_D1_EVALUATED_OBJECT.md", "ARCH_008_OUTPUT_LEVELS.md",
        "ARCH_008_ATTACK_EVENT_EVALUATION.md", "ARCH_008_NORMAL_FALSE_ALARMS.md",
        "ARCH_008_D0_D1_OVERLAP.csv", "ARCH_008_COMPLEMENTARITY_BOUNDARY.md",
        "ARCH_008_RULE_ONLY_UTILITY.md", "ARCH_008_RESULT_LINEAGE.md",
        "ARCH_008_ARTIFACT_LINEAGE.csv", "ARCH_008_CLAIM_MATRIX.csv",
        "ARCH_008_PROFESSOR_RULE_ONLY_NOTE.md", "ARCH_008_FUNCTION_CATALOG.csv",
        "ARCH_008_IO_CONTRACTS.csv", "ARCH_008_D1_EVALUATION_FLOW.mmd", "ARCH_008_MISMATCHES.md",
    }
    for name in required_d1:
        result.require((d1_dir / name).is_file(), f"ARCH-008 output missing: {name}")
    if not d1_dir.is_dir() or any(not (d1_dir / name).is_file() for name in required_d1):
        return
    with (d1_dir / "ARCH_008_D0_D1_OVERLAP.csv").open("r", encoding="utf-8", newline="") as handle:
        overlap_rows = list(csv.DictReader(handle))
    with (d1_dir / "ARCH_008_ARTIFACT_LINEAGE.csv").open("r", encoding="utf-8", newline="") as handle:
        d1_artifacts = list(csv.DictReader(handle))
    with (d1_dir / "ARCH_008_CLAIM_MATRIX.csv").open("r", encoding="utf-8", newline="") as handle:
        d1_claims = list(csv.DictReader(handle))
    with (d1_dir / "ARCH_008_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        d1_functions = list(csv.DictReader(handle))
    with (d1_dir / "ARCH_008_IO_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        d1_contracts = list(csv.DictReader(handle))
    result.require([(row["category"], int(row["count"])) for row in overlap_rows] == [("BOTH", 10), ("D0_ONLY", 1), ("D1_ONLY", 3), ("NEITHER", 0)], "ARCH-008 overlap table mismatch")
    result.require(len(d1_artifacts) >= 9, "ARCH-008 artifact lineage is incomplete")
    result.require(len(d1_claims) >= 9, "ARCH-008 claim matrix is incomplete")
    result.require(len(d1_functions) >= 9 and all(is_safe_relative_path(row["path"]) for row in d1_functions), "ARCH-008 function catalog is incomplete or unsafe")
    result.require(len(d1_contracts) >= 10, "ARCH-008 IO contracts are incomplete")
    d1_flow = (d1_dir / "ARCH_008_D1_EVALUATION_FLOW.mmd").read_text(encoding="utf-8")
    result.require(d1_flow.startswith("flowchart ") and "LABEL ACCESS" in d1_flow and "PILOT ONLY" in d1_flow, "ARCH-008 Mermaid omits flow or pilot label boundary")
    output_levels = (d1_dir / "ARCH_008_OUTPUT_LEVELS.md").read_text(encoding="utf-8")
    for marker in ("6,031", "788", "630", "626", "574", "40.50255787059723"):
        result.require(marker in output_levels, f"ARCH-008 output levels omit {marker}")
    result.require("UNVALIDATED" in (d1_dir / "ARCH_008_RULE_ONLY_UTILITY.md").read_text(encoding="utf-8"), "ARCH-008 utility boundary missing")
    result.require("T2 Agentic Rule-only" in (d1_dir / "ARCH_008_PROFESSOR_RULE_ONLY_NOTE.md").read_text(encoding="utf-8"), "ARCH-008 professor terminology boundary missing")

    d2_dir = rcc_root / "architecture" / "09_d2_fusion"
    required_d2 = {
        "ARCH_009_REPORT.md", "ARCH_009_D2_ROLE.md", "ARCH_009_INPUT_AUTHORITY.md",
        "ARCH_009_D0_PRESERVATION.md", "ARCH_009_V1_POLICY.md", "ARCH_009_V2_POLICY.md",
        "ARCH_009_POLICY_COMPARISON.csv", "ARCH_009_D2_PREDICTION_SCHEMA.md",
        "ARCH_009_ADDED_ALARM_TAXONOMY.md", "ARCH_009_MISS_RECOVERY.md",
        "ARCH_009_COMPLEMENTARITY_INTERPRETATION.md", "ARCH_009_RESULT_LINEAGE.md",
        "ARCH_009_CLAIM_MATRIX.csv", "ARCH_009_FUNCTION_CATALOG.csv",
        "ARCH_009_IO_CONTRACTS.csv", "ARCH_009_FUSION_FLOW.mmd", "ARCH_009_MISMATCHES.md",
    }
    for name in required_d2:
        result.require((d2_dir / name).is_file(), f"ARCH-009 output missing: {name}")
    if not d2_dir.is_dir() or any(not (d2_dir / name).is_file() for name in required_d2):
        return
    with (d2_dir / "ARCH_009_POLICY_COMPARISON.csv").open("r", encoding="utf-8", newline="") as handle:
        d2_comparison = list(csv.DictReader(handle))
    with (d2_dir / "ARCH_009_CLAIM_MATRIX.csv").open("r", encoding="utf-8", newline="") as handle:
        d2_claims = list(csv.DictReader(handle))
    with (d2_dir / "ARCH_009_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        d2_functions = list(csv.DictReader(handle))
    with (d2_dir / "ARCH_009_IO_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        d2_contracts = list(csv.DictReader(handle))
    result.require(len(d2_comparison) >= 13, "ARCH-009 policy comparison is incomplete")
    result.require(len(d2_claims) >= 10, "ARCH-009 claim matrix is incomplete")
    result.require(len(d2_functions) >= 10 and all(is_safe_relative_path(row["path"]) for row in d2_functions), "ARCH-009 function catalog is incomplete or unsafe")
    result.require(len(d2_contracts) >= 10, "ARCH-009 IO contracts are incomplete")
    d2_flow = (d2_dir / "ARCH_009_FUSION_FLOW.mmd").read_text(encoding="utf-8")
    result.require(d2_flow.startswith("flowchart ") and "LABEL ACCESS" in d2_flow and "TEST1-INFORMED" in d2_flow, "ARCH-009 Mermaid omits label or development boundary")
    result.require("decision_physical_row_index" in (d2_dir / "ARCH_009_V1_POLICY.md").read_text(encoding="utf-8"), "ARCH-009 V1 same-second semantics missing")
    result.require("TEST1_INFORMED_DEVELOPMENT" in (d2_dir / "ARCH_009_V2_POLICY.md").read_text(encoding="utf-8"), "ARCH-009 V2 chronology boundary missing")
    result.require("0/3" in (d2_dir / "ARCH_009_MISS_RECOVERY.md").read_text(encoding="utf-8"), "ARCH-009 miss recovery missing")

    metric_dir = rcc_root / "architecture" / "10_metrics_integrity"
    required_metric = {
        "ARCH_010_REPORT.md", "ARCH_010_OBJECT_LEVELS.md", "ARCH_010_ATTACK_EVENT_CONSTRUCTION.md",
        "ARCH_010_EVENT_HIT_RULE.md", "ARCH_010_RECALL_DEFINITION.md", "ARCH_010_EPISODE_CONSTRUCTION.md",
        "ARCH_010_FALSE_EPISODE_DEFINITION.md", "ARCH_010_FAR_DEFINITION.md",
        "ARCH_010_METHOD_NORMALIZATION.md", "ARCH_010_RESULT_SCHEMA.md", "ARCH_010_RESULT_INTEGRITY.md",
        "ARCH_010_FUNCTION_CATALOG.csv", "ARCH_010_IO_CONTRACTS.csv",
        "ARCH_010_FROZEN_PILOT_RESULTS.csv", "ARCH_010_CLAIM_MATRIX.csv",
        "ARCH_010_METRIC_FLOW.mmd", "ARCH_010_MISMATCHES.md",
    }
    for name in required_metric:
        result.require((metric_dir / name).is_file(), f"ARCH-010 output missing: {name}")
    if not metric_dir.is_dir() or any(not (metric_dir / name).is_file() for name in required_metric):
        return
    with (metric_dir / "ARCH_010_FROZEN_PILOT_RESULTS.csv").open("r", encoding="utf-8", newline="") as handle:
        pilot_rows = list(csv.DictReader(handle))
    with (metric_dir / "ARCH_010_FUNCTION_CATALOG.csv").open("r", encoding="utf-8", newline="") as handle:
        metric_functions = list(csv.DictReader(handle))
    with (metric_dir / "ARCH_010_IO_CONTRACTS.csv").open("r", encoding="utf-8", newline="") as handle:
        metric_contracts = list(csv.DictReader(handle))
    with (metric_dir / "ARCH_010_CLAIM_MATRIX.csv").open("r", encoding="utf-8", newline="") as handle:
        metric_claims = list(csv.DictReader(handle))
    result.require([row["method"] for row in pilot_rows] == ["D0", "D1", "D2_V1", "D2_V2"], "ARCH-010 frozen table methods mismatch")
    result.require([row["detected_units"] for row in pilot_rows] == ["11", "13", "11", "11"], "ARCH-010 frozen Recall numerators mismatch")
    result.require(all(row["normal_exposure_seconds"] == "51019" for row in pilot_rows), "ARCH-010 exposure must be shared")
    result.require([row["normal_false_episodes"] for row in pilot_rows] == ["7", "574", "10", "98"], "ARCH-010 false episode counts mismatch")
    result.require(len(metric_functions) >= 14 and all(is_safe_relative_path(row["path"]) for row in metric_functions), "ARCH-010 function catalog is incomplete or unsafe")
    for row in metric_functions:
        source_path = rcc_root.parent / row["path"]
        result.require(source_path.is_file(), f"ARCH-010 function path does not exist: {row['path']}")
        if source_path.is_file():
            source_text = source_path.read_text(encoding="utf-8")
            symbol_pattern = re.compile(rf"^(?:def|class)\s+{re.escape(row['symbol'])}\b", re.MULTILINE)
            result.require(bool(symbol_pattern.search(source_text)), f"ARCH-010 function symbol does not exist: {row['path']}::{row['symbol']}")
    result.require(len(metric_contracts) >= 12, "ARCH-010 IO contracts are incomplete")
    result.require(len(metric_claims) >= 12, "ARCH-010 claim matrix is incomplete")
    metric_flow = (metric_dir / "ARCH_010_METRIC_FLOW.mmd").read_text(encoding="utf-8")
    result.require(metric_flow.startswith("flowchart ") and "PILOT ONLY" in metric_flow, "ARCH-010 Mermaid omits pilot boundary")
    result.require("PA-FREE" in (metric_dir / "ARCH_010_EVENT_HIT_RULE.md").read_text(encoding="utf-8"), "ARCH-010 point-adjustment boundary missing")
    result.require("Result integrity ≠ scientific validation" in (metric_dir / "ARCH_010_REPORT.md").read_text(encoding="utf-8") or "Integrity PASS" in (metric_dir / "ARCH_010_REPORT.md").read_text(encoding="utf-8"), "ARCH-010 integrity/science boundary missing")

    gap_dir = rcc_root / "architecture" / "gap_000_pre_validation"
    required_gap = {
        "GAP_000_REPORT.md", "GAP_000_RAW_FINDINGS.csv", "GAP_000_ROOT_ISSUES.csv",
        "GAP_000_REMEDIATION_MATRIX.csv", "GAP_000_EXPERIMENT_GATES.csv",
        "GAP_000_CORE_VALIDATION_GATE.md", "GAP_000_EXP01_GATE.md", "GAP_000_EXP03_GATE.md",
        "GAP_000_EXP05_GATE.md", "GAP_000_CODE_FIX_QUEUE.md", "GAP_000_EXPERIMENT_REQUIREMENTS.md",
        "GAP_000_CLAIM_LIMITATIONS.md", "GAP_000_MINIMUM_THESIS_PATH.md",
        "GAP_000_USER_DECISIONS_REQUIRED.md", "GAP_000_REMEDIATION_ORDER.md",
        "GAP_000_PILOT_PRESERVATION.md",
    }
    for name in required_gap:
        result.require((gap_dir / name).is_file(), f"GAP-000 output missing: {name}")
    if not gap_dir.is_dir() or any(not (gap_dir / name).is_file() for name in required_gap):
        return
    with (gap_dir / "GAP_000_RAW_FINDINGS.csv").open("r", encoding="utf-8", newline="") as handle:
        gap_raw = list(csv.DictReader(handle))
    with (gap_dir / "GAP_000_ROOT_ISSUES.csv").open("r", encoding="utf-8", newline="") as handle:
        gap_roots = list(csv.DictReader(handle))
    with (gap_dir / "GAP_000_REMEDIATION_MATRIX.csv").open("r", encoding="utf-8", newline="") as handle:
        gap_matrix = list(csv.DictReader(handle))
    with (gap_dir / "GAP_000_EXPERIMENT_GATES.csv").open("r", encoding="utf-8", newline="") as handle:
        gap_gates = list(csv.DictReader(handle))
    result.require(len(gap_raw) == 120, "GAP-000 raw inventory must contain 120 findings")
    severity = {level: sum(row["source_severity"] == level for row in gap_raw) for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW")}
    result.require(severity == {"CRITICAL": 0, "HIGH": 54, "MEDIUM": 55, "LOW": 11}, "GAP-000 raw severity census mismatch")
    per_arch = {arch: sum(row["source_arch"] == arch for row in gap_raw) for arch in {row["source_arch"] for row in gap_raw}}
    result.require(per_arch == {"ARCH-000":15,"ARCH-001":8,"ARCH-002":7,"ARCH-003":9,"ARCH-004":10,"ARCH-005":11,"ARCH-006":13,"ARCH-007":10,"ARCH-008":13,"ARCH-009":12,"ARCH-010":12}, "GAP-000 per-ARCH inventory mismatch")
    root_ids = {row["gap_id"] for row in gap_roots}
    result.require(len(gap_roots) == 19 and len(root_ids) == 19, "GAP-000 root issue count or IDs mismatch")
    result.require(all(row["duplicate_group"] in root_ids for row in gap_raw), "GAP-000 raw finding has an unknown root group")
    result.require(len(gap_matrix) == 19 and {row["gap_id"] for row in gap_matrix} == root_ids, "GAP-000 remediation matrix does not cover every root")
    dispositions = {
        "P0_FIX_BEFORE_EXPANDED_VALIDATION", "P1_FIX_BEFORE_SPECIFIC_EXPERIMENT",
        "EXPERIMENT_DESIGN_REQUIREMENT", "ENGINEERING_HARDENING",
        "CLAIM_DOCUMENTATION_CORRECTION", "ACCEPTABLE_THESIS_LIMITATION", "FUTURE_WORK_ONLY",
    }
    result.require(all(row["disposition"] in dispositions and row["priority"] in {"P0","P1","P2","P3"} for row in gap_matrix), "GAP-000 disposition or priority enum mismatch")
    result.require(all(row["status"] == "TRIAGED_NOT_IMPLEMENTED" for row in gap_matrix), "GAP-000 must not claim remediation implementation")
    result.require([row["experiment_id"] for row in gap_gates] == ["EXP-01","EXP-02","EXP-03","EXP-04","EXP-05","EXP-06","NEW-HELD-OUT","FRESH-MACHINE"], "GAP-000 experiment gates are incomplete or reordered")
    gate_status = {row["experiment_id"]: row["ready_now"] for row in gap_gates}
    result.require(gate_status == {"EXP-01":"BLOCKED","EXP-02":"READY_WITH_CONDITIONS","EXP-03":"BLOCKED","EXP-04":"BLOCKED","EXP-05":"BLOCKED","EXP-06":"NOT_REQUIRED","NEW-HELD-OUT":"BLOCKED","FRESH-MACHINE":"CONDITIONAL"}, "GAP-000 gate statuses mismatch")
    result.require("No audited defect proves the frozen INNER pilot invalid" in (gap_dir / "GAP_000_REPORT.md").read_text(encoding="utf-8"), "GAP-000 pilot preservation wording missing")
    result.require("ARCH-011 read-only before remediation" in (gap_dir / "GAP_000_REMEDIATION_ORDER.md").read_text(encoding="utf-8"), "GAP-000 ARCH-011 position missing")
    result.require("NOT NEEDED FOR THESIS" in (gap_dir / "GAP_000_MINIMUM_THESIS_PATH.md").read_text(encoding="utf-8"), "GAP-000 minimum path is incomplete")
    result.require("Canonical RuleV1" in (gap_dir / "GAP_000_USER_DECISIONS_REQUIRED.md").read_text(encoding="utf-8"), "GAP-000 authority decision is missing")
    bootstrap_gap = rcc_root / "bootstrap" / "GAP_000"
    for name in (
        "GAP_000_REPORT.md", "GAP_000_RAW_FINDINGS.csv", "GAP_000_ROOT_ISSUES.csv",
        "GAP_000_REMEDIATION_MATRIX.csv", "GAP_000_EXPERIMENT_GATES.csv",
        "GAP_000_CORE_VALIDATION_GATE.md", "GAP_000_EXP01_GATE.md", "GAP_000_EXP03_GATE.md",
        "GAP_000_EXP05_GATE.md", "GAP_000_CODE_FIX_QUEUE.md", "GAP_000_EXPERIMENT_REQUIREMENTS.md",
        "GAP_000_CLAIM_LIMITATIONS.md", "GAP_000_MINIMUM_THESIS_PATH.md", "GAP_000_USER_DECISIONS_REQUIRED.md",
    ):
        result.require((bootstrap_gap / name).read_bytes() == (gap_dir / name).read_bytes(), f"GAP-000 bootstrap copy differs: {name}")
    evidence = json.loads((bootstrap_gap / "GAP_000_EVIDENCE.json").read_text(encoding="utf-8"))
    result.require(evidence.get("raw_findings") == 120 and evidence.get("root_issues") == 19, "GAP-000 evidence counts mismatch")
    result.require(evidence.get("past_pilot") == "INTERPRETABLE_WITH_QUALIFICATIONS" and evidence.get("invalidated_artifacts") == 0, "GAP-000 evidence invalidates pilot")
    result.require(all(value == 0 for value in evidence.get("safety", {}).values()), "GAP-000 safety counters must remain zero")

    arch011 = rcc_root / "architecture" / "11_outer_reproducibility"
    required_arch011 = {
        "ARCH_011_REPORT.md", "ARCH_011_OLD_OUTER_TIMELINE.md", "ARCH_011_NEW_HELDOUT_REQUIREMENTS.md",
        "ARCH_011_REPRODUCTION_LEVELS.md", "ARCH_011_ENVIRONMENT_MATRIX.csv",
        "ARCH_011_PATH_MACHINE_ASSUMPTIONS.csv", "ARCH_011_ARTIFACT_PORTABILITY.csv",
        "ARCH_011_PILOT_V1_REPRODUCTION.md", "ARCH_011_VALIDATION_V2_VERSIONING.md",
        "ARCH_011_AUTHORITY_OPTIONS.csv", "ARCH_011_FRESH_MACHINE_PROTOCOL.md",
        "ARCH_011_RELEASE_SCOPE.md", "ARCH_011_MISMATCHES.md", "ARCH_011_GAP_UPDATE.md",
    }
    for name in required_arch011:
        result.require((arch011 / name).is_file(), f"ARCH-011 output missing: {name}")
    if not arch011.is_dir() or any(not (arch011 / name).is_file() for name in required_arch011):
        return
    report011 = (arch011 / "ARCH_011_REPORT.md").read_text(encoding="utf-8")
    result.require("NOT_RETRYABLE_BY_PROTOCOL" in report011 and "STUDY_DESIGN_REQUIRED" in report011, "ARCH-011 OUTER boundary missing")
    result.require("PILOT V1" in report011 and "VALIDATION V2" in report011, "ARCH-011 version separation missing")
    with (arch011 / "ARCH_011_ENVIRONMENT_MATRIX.csv").open("r", encoding="utf-8", newline="") as handle:
        env_rows = list(csv.DictReader(handle))
    with (arch011 / "ARCH_011_ARTIFACT_PORTABILITY.csv").open("r", encoding="utf-8", newline="") as handle:
        portability_rows = list(csv.DictReader(handle))
    with (arch011 / "ARCH_011_AUTHORITY_OPTIONS.csv").open("r", encoding="utf-8", newline="") as handle:
        authority_rows = list(csv.DictReader(handle))
    result.require(len(env_rows) >= 10 and any(row["dependency"] == "NumPy" and row["risk"] == "HIGH" for row in env_rows), "ARCH-011 environment matrix incomplete")
    result.require(len(portability_rows) >= 10 and any("no persisted GDN model checkpoint" in row["notes"] for row in portability_rows), "ARCH-011 artifact portability is incomplete")
    result.require([row["option"] for row in authority_rows] == ["A_RULEV1_END_TO_END", "B_FORMAL_V4", "C_VERIFIED_CANONICAL_TO_V4_BRIDGE"], "ARCH-011 authority option ordering mismatch")
    result.require(authority_rows[2]["assessment"] == "RECOMMENDED_PROSPECTIVE_TARGET_PENDING_DEC020", "ARCH-011 bridge recommendation mismatch")
    protocol011 = (arch011 / "ARCH_011_FRESH_MACHINE_PROTOCOL.md").read_text(encoding="utf-8")
    result.require("The first rehearsal stops after Stage 7" in protocol011 and "Optional science" in protocol011, "ARCH-011 fresh-machine stop boundary missing")
    bootstrap011 = rcc_root / "bootstrap" / "ARCH_011"
    evidence011 = json.loads((bootstrap011 / "ARCH_011_EVIDENCE.json").read_text(encoding="utf-8"))
    result.require(evidence011.get("old_outer", {}).get("feature_byte_reads") == 0 and evidence011.get("old_outer", {}).get("metrics") == 0, "ARCH-011 evidence overstates OUTER access/result")
    result.require(evidence011.get("gap_update", {}) == {"changed_priorities": 0, "new_root_blockers": 0, "removed_blockers": 0, "pilot_invalidated_artifacts": 0}, "ARCH-011 GAP update mismatch")
    result.require(all(value == 0 for value in evidence011.get("safety", {}).values()), "ARCH-011 safety counters must remain zero")


def validate_registry(
    rcc_root: Path,
    *,
    repo_root: Path | None = None,
    check_git: bool = True,
    check_outputs: bool = True,
    check_privacy: bool = True,
) -> ValidationResult:
    root = rcc_root.resolve()
    repository = (repo_root or root.parent).resolve()
    result = ValidationResult()
    for relative in REQUIRED_RCC_DIRS:
        result.require((root / relative).is_dir(), f"required directory missing: {relative}")
    required = REQUIRED_RCC_FILES + (GENERATED_FILES if check_outputs else ())
    for relative in required:
        result.require((root / relative).is_file(), f"required file missing: {relative}")
    if result.errors:
        return result
    try:
        data = load_registry(root)
    except (OSError, csv.Error, json.JSONDecodeError) as exc:
        result.errors.append(f"registry parse failed: {type(exc).__name__}")
        return result
    _validate_headers_and_cells(root, data, result)
    _validate_unique_ids(data, result)
    _validate_authority(data, result)
    _validate_enums(data, result)
    _validate_dates(data, result)
    _validate_references(data, result)
    _validate_history(data, result, repository, check_git)
    _validate_paths(data, result, repository, check_git)
    _validate_architecture(root, data, result, repository, check_git)
    if check_git:
        _validate_git_authorities(repository, result)
    if check_outputs:
        _validate_outputs(root, data, result)
    if check_privacy:
        _validate_privacy(root, result)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rcc-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--registry-only", action="store_true", help="validate source registries before generation")
    parser.add_argument("--no-git-path-check", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    result = validate_registry(
        args.rcc_root,
        check_git=not args.no_git_path_check,
        check_outputs=not args.registry_only,
    )
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if not result.ok:
        print("RCC_REGISTRY_VALIDATION_BLOCKED")
        for error in result.errors:
            print(f"- {error}")
        return 1
    scope = "registry" if args.registry_only else "registry+generated"
    print(f"RCC_REGISTRY_VALIDATION_PASS scope={scope} private_exposures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
