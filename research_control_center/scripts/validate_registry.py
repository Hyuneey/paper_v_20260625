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
)
GENERATED_FILES = (
    "dashboard/index.html", "generated/GPT_BRIEF.md", "generated/CURRENT_STATUS.md",
    "generated/CHANGE_SUMMARY.md", "generated/RCC_002_USER_SUMMARY.md",
    "generated/RCC_003_HISTORY_SUMMARY.md", "history/PROJECT_TIMELINE.md",
    "history/PROFESSOR_FEEDBACK_LINEAGE.md", "history/SUPERSEDED_DIRECTIONS.md",
    "history/TERMINOLOGY_GUIDE.md", "history/HISTORY_CONFIRMATION_NEEDED.md",
    "CURRENT_CONTEXT.md", "MY_TODO.md", "DECISION_INBOX.md",
)
REQUIRED_RCC_DIRS = (
    "registry", "wiki", "history", "history/decisions", "history/checkpoints",
    "architecture", "dashboard", "dashboard/assets", "generated", "scripts",
    "bootstrap/RCC_000", "bootstrap/RCC_003", "bootstrap/RCC_003/agents",
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
    result.require(len(state.get("top_user_todo", [])) == 3, "top_user_todo must contain exactly three entries")
    result.require(state.get("last_completed_task") == "RCC-003", "last completed task mismatch")
    result.require(state.get("exact_next_task") == "ARCH-000 — Full Architecture Overview Audit", "exact next task mismatch")
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
    result.require(state.get("recommended_next_management_task") == "ARCH-000 — Full Architecture Overview Audit", "next management task mismatch")
    result.require(state.get("recommended_next_architecture_task") == "ARCH-000 — Full Architecture Overview Audit", "next architecture task mismatch")
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
            if row["source"] == "USER_CONTEXT":
                result.require(row["source_commit"] == "NONE", f"{registry} USER_CONTEXT row must not claim a Git commit")
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
    result.require(10 <= len(data["decisions"]) <= 20, "decision registry must contain 10 to 20 meaningful decisions")
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
    result.require(professor.get("2026-08-18", {}).get("classification") == "NOT_PROFESSOR_FEEDBACK", "August 18 is mislabeled as professor feedback")
    result.require(professor.get("2026-08-26", {}).get("classification") == "NOT_PROFESSOR_FEEDBACK", "August 26 is mislabeled as professor feedback")
    august_four = professor.get("2026-08-04", {})
    result.require("USER_CONTEXT" in august_four.get("classification", ""), "August 4 feedback source uncertainty is missing")
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
    result.require(all(row["status"] != "OPEN" for row in data["decisions"]), "decision registry contains an unresolved decision; use the confirmation queue for historical uncertainty")


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
        result.require("https://" not in dashboard and "http://" not in dashboard, "dashboard contains an external network resource")
        result.require("NOT AUTHORITATIVE" in dashboard, "dashboard omits historical-checkout warning")
        result.require("These counts are not a single completion percentage." in dashboard, "dashboard omits the no-completion-percentage warning")
        result.require("Code existence, execution, evidence review, independent reproduction, and scientific validation are separate states." in dashboard, "dashboard does not separate status concepts")
        result.require("Evidence-reviewed" in dashboard, "dashboard does not translate the component audited field")
        result.require("Result integrity" in dashboard, "dashboard does not display result integrity separately")
        result.require("claims.csv" in dashboard, "dashboard does not identify the authoritative claim registry")
        result.require("Claim-ready" not in dashboard, "dashboard still headlines component claim-ready status")
        result.require(not re.search(r"\b\d+(?:\.\d+)?\s*%", dashboard), "dashboard contains an overall-looking percentage")
        for heading in (
            "CURRENT STATE", "MY TASKS", "DECISION INBOX", "ARCHITECTURE OVERVIEW",
            "COMPONENT STATUS", "EXPERIMENT STATUS", "CLAIM &amp; EVIDENCE", "RISKS",
            "RESEARCH HISTORY", "SOURCE AUTHORITY", "RECENT CHANGE / NEXT TASK",
        ):
            result.require(heading in dashboard, f"dashboard omits required section {heading}")
    required_semantic_outputs = {
        "generated/CURRENT_STATUS.md": ("Evidence-reviewed", "Result-integrity audited", "claims.csv", "not a single completion percentage"),
        "generated/GPT_BRIEF.md": ("Evidence-reviewed", "Result-integrity audit", "claims.csv", "not a single completion percentage"),
        "generated/RCC_002_USER_SUMMARY.md": ("Evidence-reviewed", "Result-integrity audited", "claims.csv", "하나의 연구 완료율"),
        "generated/RCC_003_HISTORY_SUMMARY.md": ("우리 연구가 어떻게 여기까지 왔나", "pilot evidence", "홀드아웃 일반화"),
        "history/PROJECT_TIMELINE.md": ("Research Evolution", "USER_CONTEXT", "What survived into the current method"),
        "history/PROFESSOR_FEEDBACK_LINEAGE.md": ("2026-08-18", "not professor feedback", "2026-08-26"),
        "history/SUPERSEDED_DIRECTIONS.md": ("Superseded and Conditional Directions", "Do not use as current claim"),
        "history/TERMINOLOGY_GUIDE.md": ("Historical Terminology Guide", "Current preferred meaning"),
        "history/HISTORY_CONFIRMATION_NEEDED.md": ("History Confirmation Needed", "HIST-Q001"),
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
