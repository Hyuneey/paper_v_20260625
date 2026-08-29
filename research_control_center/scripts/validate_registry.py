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
EVENT_TYPES = {"CHECKPOINT", "DECISION", "IMPLEMENTATION", "EXECUTION", "AUDIT", "BLOCKER", "DOCUMENTATION"}

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
        "decision_id", "date", "title", "decision", "reason", "status", "source",
        "source_commit", "affected_components", "supersedes", "user_approved",
    ),
    "timeline": (
        "event_id", "date", "event_type", "title", "summary", "source", "source_commit", "status",
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
    "decisions": {"OPEN", "APPROVED", "SUPERSEDED"},
    "timeline": {"PLANNED", "CURRENT", "COMPLETED", "BLOCKED", "SUPERSEDED"},
}

LIFECYCLE_STAGES = {
    "DESIGN_COMPLETE", "CODE_IMPLEMENTED", "INTEGRATED", "EXECUTED", "AUDITED", "REPRODUCED", "CLAIM_READY",
}
REQUIRED_RCC_FILES = (
    "START_HERE.md", "SOURCE_AUTHORITY.md", "CURRENT_CONTEXT.md", "SESSION_HANDOFF.md",
    "MY_TODO.md", "DECISION_INBOX.md", "registry/README.md", "registry/current_state.yaml",
    "registry/components.csv", "registry/experiments.csv", "registry/claims.csv",
    "registry/risks.csv", "registry/artifacts.csv", "registry/decisions.csv", "registry/timeline.csv",
    "wiki/README.md", "history/README.md", "architecture/README.md",
    "dashboard/assets/rcc.css", "dashboard/assets/rcc.js",
    "scripts/build_dashboard.py", "scripts/validate_registry.py", "scripts/refresh_all.py",
    "scripts/open_dashboard.bat",
)
GENERATED_FILES = (
    "dashboard/index.html", "generated/GPT_BRIEF.md", "generated/CURRENT_STATUS.md",
    "generated/CHANGE_SUMMARY.md", "generated/RCC_002_USER_SUMMARY.md",
    "CURRENT_CONTEXT.md", "MY_TODO.md", "DECISION_INBOX.md",
)
REQUIRED_RCC_DIRS = (
    "registry", "wiki", "history", "history/decisions", "history/checkpoints",
    "architecture", "dashboard", "dashboard/assets", "generated", "scripts",
    "bootstrap/RCC_000",
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
    result.require(state.get("last_completed_task") == "RCC-002", "last completed task mismatch")
    result.require(state.get("exact_next_task") == "RCC-003 — Research Timeline & Decision Backfill", "exact next task mismatch")
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
    result.require(state.get("recommended_next_management_task") == "RCC-003 — Research Timeline & Decision Backfill", "next management task mismatch")
    result.require(state.get("recommended_next_architecture_task") == "ARCH-000 — Full Architecture Overview Audit", "next architecture task mismatch")
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
    for registry in ("decisions", "timeline"):
        for row in data[registry]:
            result.require(row["source_commit"] == AUTHORITY_COMMIT, f"{registry} row has a non-authoritative source commit")
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
    for row in data["timeline"]:
        result.require(row["event_type"] in EVENT_TYPES, "timeline has invalid event_type")


def _validate_dates(data: Mapping[str, Any], result: ValidationResult) -> None:
    for registry in ("decisions", "timeline"):
        for row in data[registry]:
            try:
                parsed = datetime.strptime(row["date"], "%Y-%m-%d")
            except ValueError:
                result.errors.append(f"{registry} has an invalid ISO date")
                continue
            result.require(parsed.strftime("%Y-%m-%d") == row["date"], f"{registry} date is not canonical YYYY-MM-DD")


def _validate_references(data: Mapping[str, Any], result: ValidationResult) -> None:
    component_ids = {row["component_id"] for row in data["components"]}
    experiment_ids = {row["experiment_id"] for row in data["experiments"]}
    artifact_ids = {row["artifact_id"] for row in data["artifacts"]}
    decision_ids = {row["decision_id"] for row in data["decisions"]}
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
        result.require(row["decision_id"] not in _split_refs(row["supersedes"]), f"decision {row['decision_id']} cannot supersede itself")


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
        for heading in (
            "CURRENT STATE", "MY TASKS", "DECISION INBOX", "ARCHITECTURE OVERVIEW",
            "COMPONENT STATUS", "EXPERIMENT STATUS", "CLAIM &amp; EVIDENCE", "RISKS",
            "SOURCE AUTHORITY", "RECENT CHANGE / NEXT TASK",
        ):
            result.require(heading in dashboard, f"dashboard omits required section {heading}")


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
