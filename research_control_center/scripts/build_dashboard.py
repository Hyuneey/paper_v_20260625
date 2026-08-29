#!/usr/bin/env python3
"""Build deterministic, public-safe RCC views from the frozen registries.

This module uses only the Python standard library.  It reads public RCC
metadata; it never imports or invokes scientific project code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


AUTHORITY_COMMIT = "2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e"
REGISTRY_FILES = (
    "current_state.yaml",
    "components.csv",
    "experiments.csv",
    "claims.csv",
    "risks.csv",
    "artifacts.csv",
    "decisions.csv",
    "timeline.csv",
    "history.yaml",
)

ARCHITECTURE_FILES = (
    "00_overview/ARCH_000_SOURCE_MAP.csv",
    "00_overview/ARCH_000_DATAFLOW.csv",
    "00_overview/ARCH_000_ARTIFACT_LINEAGE.csv",
    "00_overview/ARCH_000_COMPONENT_DETAIL.csv",
    "01_data_and_splits/ARCH_001_LEAKAGE_MATRIX.csv",
    "01_data_and_splits/ARCH_001_INPUT_CONTRACTS.csv",
    "01_data_and_splits/ARCH_001_FUNCTION_CATALOG.csv",
    "02_candidate_discovery/ARCH_002_ARM_COMPARISON.csv",
    "02_candidate_discovery/ARCH_002_CANDIDATE_PROVENANCE.csv",
    "02_candidate_discovery/ARCH_002_FUNCTION_CATALOG.csv",
    "02_candidate_discovery/ARCH_002_IO_CONTRACTS.csv",
    "03_relation_and_numeric/ARCH_003_RELATION_LINEAGE.csv",
    "03_relation_and_numeric/ARCH_003_NUMERIC_AUTHORITY.csv",
    "03_relation_and_numeric/ARCH_003_FUNCTION_CATALOG.csv",
    "03_relation_and_numeric/ARCH_003_IO_CONTRACTS.csv",
    "04_rule_construction/ARCH_004_EVIDENCE_LINEAGE.csv",
    "04_rule_construction/ARCH_004_ARM_OUTCOMES.csv",
    "04_rule_construction/ARCH_004_FUNCTION_CATALOG.csv",
    "04_rule_construction/ARCH_004_IO_CONTRACTS.csv",
    "05_verifier_common42/ARCH_005_VERIFIER_STAGES.csv",
    "05_verifier_common42/ARCH_005_VALIDITY_EQUIVALENCE.csv",
    "05_verifier_common42/ARCH_005_ARM_PORTFOLIO_MAPPING.csv",
    "05_verifier_common42/ARCH_005_HASH_CHAIN.csv",
    "05_verifier_common42/ARCH_005_FUNCTION_CATALOG.csv",
    "05_verifier_common42/ARCH_005_IO_CONTRACTS.csv",
    "06_runtime_trace_explanation/ARCH_006_TRACE_SCHEMA.csv",
    "06_runtime_trace_explanation/ARCH_006_FUNCTION_CATALOG.csv",
    "06_runtime_trace_explanation/ARCH_006_IO_CONTRACTS.csv",
    "07_d0_detector/ARCH_007_ARTIFACT_LINEAGE.csv",
    "07_d0_detector/ARCH_007_FUNCTION_CATALOG.csv",
    "07_d0_detector/ARCH_007_IO_CONTRACTS.csv",
)


def default_rcc_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_registry(rcc_root: Path) -> dict[str, Any]:
    """Load the JSON-compatible YAML state and every CSV registry."""

    registry_dir = rcc_root / "registry"
    state = json.loads((registry_dir / "current_state.yaml").read_text(encoding="utf-8"))
    history = json.loads((registry_dir / "history.yaml").read_text(encoding="utf-8"))
    data = {
        "state": state,
        "history": history,
        "components": _read_csv(registry_dir / "components.csv"),
        "experiments": _read_csv(registry_dir / "experiments.csv"),
        "claims": _read_csv(registry_dir / "claims.csv"),
        "risks": _read_csv(registry_dir / "risks.csv"),
        "artifacts": _read_csv(registry_dir / "artifacts.csv"),
        "decisions": _read_csv(registry_dir / "decisions.csv"),
        "timeline": _read_csv(registry_dir / "timeline.csv"),
    }
    detail = rcc_root / "architecture" / "00_overview" / "ARCH_000_COMPONENT_DETAIL.csv"
    data["architecture_details"] = _read_csv(detail) if detail.is_file() else []
    return data


def registry_digest(rcc_root: Path) -> str:
    """Hash names and bytes of every file that can affect generated views."""

    digest = hashlib.sha256()
    registry_dir = rcc_root / "registry"
    for name in REGISTRY_FILES:
        payload = (registry_dir / name).read_bytes()
        digest.update(name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    architecture_dir = rcc_root / "architecture"
    for name in ARCHITECTURE_FILES:
        path = architecture_dir / name
        if not path.is_file():
            continue
        payload = path.read_bytes()
        digest.update(name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _short_commit(commit: str) -> str:
    return commit[:12] + "\u2026"


def _badge_class(status: str) -> str:
    if status in {"IMPLEMENTED_EXECUTED_AUDITED", "AUDITED", "REPRODUCED", "CLAIM_READY", "COMPLETED", "ACTIVE", "ACTIVE_CONTEXT"}:
        return "badge-green"
    if status in {"IMPLEMENTED_EXECUTED", "IMPLEMENTED_NOT_EXECUTED", "CODE_IMPLEMENTED", "INTEGRATED", "SUPPORTED_IMPLEMENTATION"}:
        return "badge-blue"
    if status in {"PARTIAL", "EXECUTED_AUDITED_PILOT", "PILOT_ONLY", "CONDITIONAL", "MITIGATING", "CURRENT", "HISTORICAL"}:
        return "badge-yellow"
    if status in {"BLOCKED", "HIGH"}:
        return "badge-orange"
    if status in {"NOT_SUPPORTED", "CRITICAL"}:
        return "badge-red"
    return "badge-gray"


COMPONENT_STATUS_LABELS = {
    "IMPLEMENTED_EXECUTED_AUDITED": "CODE PRESENT · EXECUTED · EVIDENCE REVIEWED",
    "IMPLEMENTED_EXECUTED": "CODE PRESENT · EXECUTED",
    "IMPLEMENTED_NOT_EXECUTED": "CODE PRESENT · NOT EXECUTED",
    "RESEARCH_ONLY": "RESEARCH SCOPE ONLY",
    "DESIGN_ONLY": "DESIGNED ONLY",
    "PARTIAL": "PARTIAL",
    "BLOCKED": "BLOCKED",
    "LEGACY_OR_SUPERSEDED": "LEGACY OR SUPERSEDED",
    "UNKNOWN": "UNKNOWN",
}

EXPERIMENT_STATUS_LABELS = {
    "NOT_STARTED": "NOT STARTED",
    "DESIGN_ONLY": "DESIGNED ONLY",
    "IMPLEMENTED_NOT_EXECUTED": "CODE PRESENT · COMPARISON NOT EXECUTED",
    "EXECUTED_NOT_AUDITED": "EXECUTED · EVIDENCE REVIEW PENDING",
    "EXECUTED_AUDITED_PILOT": "EXECUTED · EVIDENCE-REVIEWED PILOT",
    "BLOCKED": "BLOCKED",
    "SUPERSEDED": "SUPERSEDED",
    "UNKNOWN": "UNKNOWN",
}


def _badge(status: str, label: str | None = None) -> str:
    displayed = label or status.replace("_", " ")
    return f'<span class="badge {_badge_class(status)}">{_escape(displayed)}</span>'


def _cards(
    rows: Sequence[Mapping[str, str]],
    *,
    title_key: str,
    id_key: str,
    status_key: str,
    body_keys: Sequence[tuple[str, str]],
    status_labels: Mapping[str, str] | None = None,
) -> str:
    rendered: list[str] = []
    for row in rows:
        status = row[status_key]
        searchable = " ".join(str(value) for value in row.values()).lower()
        details = "".join(
            f'<div class="card-field"><dt>{_escape(label)}</dt><dd>{_escape(row[key])}</dd></div>'
            for label, key in body_keys
        )
        rendered.append(
            "\n".join(
                (
                    f'<article class="registry-card" data-status="{_escape(status)}" data-search="{_escape(searchable)}">',
                    '<div class="card-heading">',
                    f'<div><p class="eyebrow">{_escape(row[id_key])}</p><h3>{_escape(row[title_key])}</h3></div>',
                    _badge(status, (status_labels or {}).get(status)),
                    "</div>",
                    f"<dl>{details}</dl>",
                    "</article>",
                )
            )
        )
    return "\n".join(rendered)


def _bullet_list(items: Iterable[object], *, empty: str = "No items recorded.") -> str:
    values = list(items)
    if not values:
        return f'<p class="empty-state">{_escape(empty)}</p>'
    return "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in values) + "</ul>"


def _source_marker(state: Mapping[str, Any], digest: str) -> str:
    return (
        f'RCC_GENERATED registry_version={state["registry_version"]} '
        f'registry_digest={digest} authority={state["scientific_authority"]["commit"]}'
    )


def render_dashboard(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    checkout = state["non_authoritative_checkout"]
    unresolved = [row for row in data["decisions"] if row["status"] == "OPEN"]
    current_events = sorted(
        (row for row in data["timeline"] if row["date_precision"] == "DAY"),
        key=lambda row: (row["date"], row["event_id"]),
        reverse=True,
    )
    all_statuses = sorted(
        {row["status"] for group in (data["components"], data["experiments"], data["claims"]) for row in group}
        | {row["severity"] for row in data["risks"]}
        | {"CRITICAL"}
    )
    status_options = "".join(
        f'<option value="{_escape(status)}">{_escape(status.replace("_", " "))}</option>'
        for status in all_statuses
    )

    component_cards = _cards(
        data["components"],
        title_key="name",
        id_key="component_id",
        status_key="status",
        body_keys=(("Role", "research_role"), ("Recorded lifecycle token", "lifecycle_stage"), ("Next", "next_action")),
        status_labels=COMPONENT_STATUS_LABELS,
    )
    experiment_cards = _cards(
        data["experiments"],
        title_key="name",
        id_key="experiment_id",
        status_key="status",
        body_keys=(("Question", "research_question"), ("Evidence", "current_evidence"), ("Limit", "limitations"), ("Next", "next_action")),
        status_labels=EXPERIMENT_STATUS_LABELS,
    )
    claim_cards = _cards(
        data["claims"],
        title_key="claim_text",
        id_key="claim_id",
        status_key="status",
        body_keys=(("Allowed wording", "allowed_wording"), ("Forbidden wording", "forbidden_wording"), ("Validation needed", "validation_needed")),
    )
    risk_cards = _cards(
        data["risks"],
        title_key="description",
        id_key="risk_id",
        status_key="severity",
        body_keys=(("Status", "status"), ("Likelihood", "likelihood"), ("Evidence", "evidence"), ("Mitigation", "mitigation"), ("Owner", "owner")),
    )
    decision_content = _cards(
        unresolved,
        title_key="title",
        id_key="decision_id",
        status_key="status",
        body_keys=(("Decision", "decision"), ("Reason", "reason")),
    ) if unresolved else '<p class="empty-state">No unresolved user decisions.</p>'
    event_by_id = {row["event_id"]: row for row in data["timeline"]}
    history_events = [event_by_id[event_id] for event_id in data["history"]["dashboard_event_ids"]]
    history_markup = "".join(
        f'<article class="timeline-item"><time>{_escape(row["date"])}</time><div><strong>{_escape(row["title"])}</strong><p>{_escape(row["summary"])}</p><small>{_escape(row["source"])} · {_escape(row["notes"])}</small></div>{_badge(row["status"])}</article>'
        for row in history_events
    )
    active_decisions = [row for row in data["decisions"] if row["status"] in {"ACTIVE", "CONDITIONAL"}]
    key_decisions_markup = "".join(
        f'<li><strong>{_escape(row["decision_id"])} · {_escape(row["title"])}</strong><span>{_escape(row["current_relevance"])}</span></li>'
        for row in active_decisions[-8:]
    )
    recent = current_events[:3]
    recent_markup = "".join(
        f'<article class="timeline-item"><time>{_escape(row["date"])}</time><div><strong>{_escape(row["title"])}</strong><p>{_escape(row["summary"])}</p></div>{_badge(row["status"])}</article>'
        for row in recent
    )
    phases = "".join(
        f'<li class="phase-step {"phase-current" if phase == state["current_phase"] else ""}">{_escape(phase.replace("_", " "))}</li>'
        for phase in state["phase_progression"]
    )
    components = data["components"]
    component_counts = {
        "Total": len(components),
        "Implemented": sum(row["status"].startswith("IMPLEMENTED") for row in components),
        "Executed": sum(row["executed"] == "true" for row in components),
        "Evidence-reviewed": sum(row["audited"] == "true" for row in components),
        "Independently reproduced": sum(row["reproduced"] == "true" for row in components),
    }
    experiment_counts = {
        "Total": len(data["experiments"]),
        "Pilot": sum(row["status"] == "EXECUTED_AUDITED_PILOT" for row in data["experiments"]),
        "Unvalidated": sum(row["status"] == "IMPLEMENTED_NOT_EXECUTED" for row in data["experiments"]),
        "Conditional": sum(row["status"] == "DESIGN_ONLY" for row in data["experiments"]),
    }
    claim_counts = {
        "Supported implementation": sum(row["status"] == "SUPPORTED_IMPLEMENTATION" for row in data["claims"]),
        "Pilot only": sum(row["status"] == "PILOT_ONLY" for row in data["claims"]),
        "Unvalidated": sum(row["status"] == "UNVALIDATED" for row in data["claims"]),
        "Not supported": sum(row["status"] == "NOT_SUPPORTED" for row in data["claims"]),
        "Conditional": sum(row["status"] == "CONDITIONAL" for row in data["claims"]),
    }
    risk_counts = {
        "Critical / high": sum(row["severity"] in {"CRITICAL", "HIGH"} for row in data["risks"]),
        "Medium": sum(row["severity"] == "MEDIUM" for row in data["risks"]),
        "Low": sum(row["severity"] == "LOW" for row in data["risks"]),
    }
    summaries = (("Components", component_counts), ("Experiments", experiment_counts), ("Claims", claim_counts), ("Risks", risk_counts))
    summary_markup = "".join(
        '<article class="summary-card"><h3>' + _escape(title) + "</h3><dl>" + "".join(
            f'<div><dt>{_escape(label)}</dt><dd>{count}</dd></div>' for label, count in counts.items()
        ) + "</dl></article>"
        for title, counts in summaries
    )
    component_by_id = {row["component_id"]: row for row in components}
    architecture_markup = "".join(
        "\n".join((
            f'<details class="architecture-detail" id="arch-{_slug(row["section_id"])}">',
            f'<summary><span>{_escape(row["section_id"])}</span><strong>{_escape(row["name"])}</strong></summary>',
            '<dl class="architecture-contract">',
            f'<div><dt>ROLE</dt><dd>{_escape(row["role"])}</dd></div>',
            f'<div><dt>INPUT</dt><dd>{_escape(row["input"])}</dd></div>',
            f'<div><dt>OUTPUT</dt><dd>{_escape(row["output"])}</dd></div>',
            f'<div><dt>CODE</dt><dd><code>{_escape(row["code"])}</code></dd></div>',
            f'<div><dt>EXECUTED?</dt><dd>{_badge("IMPLEMENTED_EXECUTED" if row["executed"] == "true" else "UNKNOWN", row["executed"].upper())}</dd></div>',
            f'<div><dt>FROZEN RESULT USED?</dt><dd>{_badge("AUDITED" if row["frozen_result_used"] == "true" else "DESIGN_ONLY", row["frozen_result_used"].upper())}</dd></div>',
            f'<div><dt>VALIDATION STATE</dt><dd>{_escape(row["validation_state"])}</dd></div>',
            f'<div><dt>NEXT DEEP REVIEW</dt><dd>{_escape(row["next_deep_review"])}</dd></div>',
            '</dl></details>',
        ))
        for row in data["architecture_details"]
    )
    governance = state["data_governance"]
    split_markup = "".join(
        '<article class="summary-card"><p class="eyebrow">'
        + _escape(item["badge"])
        + "</p><h3>"
        + _escape(item["id"])
        + "</h3><p>"
        + _escape(item["role"])
        + "</p></article>"
        for item in governance["splits"]
    )
    discovery = state["candidate_discovery"]
    discovery_markup = "".join(
        '<article class="summary-card"><p class="eyebrow">'
        + _escape(arm["id"])
        + "</p><h3>"
        + _escape(arm["method"])
        + "</h3><dl>"
        + f'<div><dt>INPUT</dt><dd>{_escape(arm["input"])}</dd></div>'
        + f'<div><dt>OUTPUT</dt><dd>{_escape(arm["output"])}</dd></div>'
        + f'<div><dt>TOP-K</dt><dd>{_escape(arm["top_k"])}</dd></div>'
        + f'<div><dt>FROZEN EXECUTION?</dt><dd>{_badge("AUDITED", "YES")}</dd></div>'
        + f'<div><dt>SCIENTIFIC VALIDATION?</dt><dd>{_badge("UNVALIDATED", arm["scientific_validation"])}</dd></div>'
        + "</dl></article>"
        for arm in discovery["arms"]
    )
    relation = state["relation_numeric_authority"]
    construction = state["rule_construction_authority"]
    verifier = state["verifier_common42_authority"]
    runtime = state["runtime_trace_explanation"]
    d0 = state["d0_detector"]
    construction_arms = (
        ("T0", "NO", "0", "NONE", "0", "42/42 accepted proposals"),
        ("T1", "YES", "1", "NONE", "0", "42/42 accepted proposals"),
        ("T1-B", "YES", "3 fixed", "NO FEEDBACK", "0", "42/42 selected proposals"),
        ("T2", "YES", "3 max", "REVISE / RETRIEVE", "0", "39/42 accepted; 3 no_rule"),
    )
    construction_markup = "".join(
        '<article class="summary-card"><p class="eyebrow">'
        + _escape(arm)
        + "</p><dl>"
        + f'<div><dt>LLM?</dt><dd>{_escape(llm)}</dd></div>'
        + f'<div><dt>CALL BUDGET</dt><dd>{_escape(budget)}</dd></div>'
        + f'<div><dt>FEEDBACK CAPABILITY</dt><dd>{_escape(feedback)}</dd></div>'
        + f'<div><dt>OBSERVED FEEDBACK</dt><dd>{_escape(observed)}</dd></div>'
        + f'<div><dt>FROZEN OUTCOME</dt><dd>{_escape(outcome)}</dd></div>'
        + '<div><dt>SCIENTIFIC CLAIM</dt><dd>IMPLEMENTATION / PILOT ONLY</dd></div>'
        + "</dl></article>"
        for arm, llm, budget, feedback, observed, outcome in construction_arms
    )
    marker = _source_marker(state, digest)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="rcc-registry-version" content="{_escape(state['registry_version'])}">
  <meta name="rcc-registry-digest" content="{digest}">
  <meta name="rcc-scientific-authority" content="{_escape(authority['commit'])}">
  <!-- {marker} -->
  <title>Research Control Center</title>
  <link rel="stylesheet" href="assets/rcc.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="hero">
    <div class="hero-inner">
      <p class="eyebrow">RESEARCH CONTROL CENTER · RCC {_escape(state['rcc_version'])}</p>
      <h1>Thesis research, with evidence boundaries visible.</h1>
      <p class="hero-summary">{_escape(state['current_phase_statement'])}</p>
      <div class="authority-strip">
        <div><span>Scientific authority</span><strong title="{_escape(authority['commit'])}">{_escape(authority['ref'])} @ {_short_commit(authority['commit'])}</strong></div>
        <div class="authority-warning"><span>Current historical checkout</span><strong title="{_escape(checkout['commit'])}">{_escape(checkout['ref'])} @ {_short_commit(checkout['commit'])} · NOT AUTHORITATIVE</strong></div>
      </div>
      <ol class="phase-track" aria-label="Research phase">{phases}</ol>
    </div>
  </header>

  <nav class="section-nav" aria-label="Dashboard sections">
    <a href="#current-state">Current state</a><a href="#data-governance">Data</a><a href="#my-tasks">My tasks</a>
    <a href="#candidate-discovery">Discovery</a><a href="#relation-numeric">Relation / Numeric</a><a href="#rule-construction">Rule construction</a><a href="#verifier-common42">Verifier</a><a href="#runtime-trace-explanation">Runtime / Trace</a><a href="#d0-detector">D0</a><a href="#decisions">Decisions</a><a href="#architecture">Architecture</a>
    <a href="#components">Components</a><a href="#experiments">Experiments</a>
    <a href="#claims">Claims</a><a href="#risks">Risks</a><a href="#history">History</a>
  </nav>

  <main id="main">
    <section id="current-state" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">01</p><h2>CURRENT STATE</h2></div>
      <div class="two-column"><div><h3>Established</h3>{_bullet_list(state['established_facts'])}</div><div><h3>Not established</h3>{_bullet_list(state['not_established'])}</div></div>
      <div class="status-snapshot">
        <div><span>Engineering</span><strong>{_escape(state['research_status_summary']['engineering'])}</strong></div>
        <div><span>Result integrity</span><strong>{_escape(state['research_status_summary']['result_integrity'])}</strong></div>
        <div><span>Scientific validation</span><strong>{_escape(state['research_status_summary']['scientific_validation'])}</strong></div>
        <div><span>Reproducibility</span><strong>{_escape(state['research_status_summary']['reproducibility'])}</strong></div>
        <div><span>Generalization</span><strong>{_escape(state['research_status_summary']['generalization'])}</strong></div>
        <div><span>Claims</span><strong>{_escape(state['research_status_summary']['claims'])}</strong></div>
      </div>
      <div class="summary-grid">{summary_markup}</div>
      <p class="summary-note">These counts are not a single completion percentage. Component Evidence-reviewed means source or evidence status was reviewed; explicit scientific result-integrity audits are shown separately. Scientific claim counts come only from <code>claims.csv</code>.</p>
      <aside class="principle">Code existence, execution, evidence review, independent reproduction, and scientific validation are separate states.</aside>
    </section>

    <section id="relation-numeric" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">RELATION</p><h2>RELATION &amp; NUMERIC AUTHORITY</h2></div>
      <div class="status-snapshot">
        <div><span>Candidates</span><strong>{relation['candidate_pairs']}</strong></div>
        <div><span>Profiled opportunities</span><strong>{relation['directional_opportunities']}</strong></div>
        <div><span>Fit-supported</span><strong>{relation['fit_supported_pair_contexts']} contexts / {relation['fit_supported_directions']} directions</strong></div>
        <div><span>Confirmed</span><strong>{relation['confirmed_pair_contexts']} contexts / {relation['confirmed_directions']} relations</strong></div>
        <div><span>Construction-bound</span><strong>462 references</strong></div>
        <div><span>Runtime-bound</span><strong>420 references + descriptor horizon</strong></div>
      </div>
      <div class="two-column">
        <div><h3>Profiling and confirmation</h3><dl class="architecture-contract">
          <div><dt>SOURCE SPLIT</dt><dd>{_escape(relation['profiling_splits'])}</dd></div>
          <div><dt>SOURCE EVENT</dt><dd>{_escape(relation['source_event'])}</dd></div>
          <div><dt>TARGET RESPONSE</dt><dd>{_escape(relation['target_response'])}</dd></div>
          <div><dt>CONFIRMATION</dt><dd>{_escape(relation['confirmation_split'])}</dd></div>
        </dl></div>
        <div><h3>Numeric custody</h3><dl class="architecture-contract">
          <div><dt>CONSTRUCTION</dt><dd>{_escape(relation['construction_authority'])}</dd></div>
          <div><dt>RUNTIME</dt><dd>{_escape(relation['runtime_authority'])}</dd></div>
          <div><dt>RELATIONSHIP</dt><dd>{_escape(relation['authority_relationship'])}</dd></div>
          <div><dt>TRACEABILITY</dt><dd>{_escape(relation['traceability'])}</dd></div>
        </dl></div>
      </div>
      <aside class="principle">{_escape(relation['warning'])}</aside>
      <p><a href="../architecture/03_relation_and_numeric/ARCH_003_REPORT.md">Open the deep relation/numeric audit</a> · <a href="../architecture/03_relation_and_numeric/ARCH_003_CONSTRUCTION_RUNTIME_AUTHORITY.md">Construction/runtime authority</a> · <a href="../architecture/03_relation_and_numeric/ARCH_003_MISMATCHES.md">Relation/numeric mismatches</a></p>
      <p><strong>Next deep review:</strong> {_escape(relation['next_deep_review'])}</p>
    </section>

    <section id="rule-construction" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">RULE</p><h2>EVIDENCE-BOUND RULE CONSTRUCTION</h2></div>
      <p class="architecture-flow">Evidence Pack → closed Rule DSL → T0 / T1 / T1-B / T2 → deterministic validity handoff</p>
      <div class="two-column"><div><h3>What enters</h3><p>{_escape(construction['evidence_view'])}</p></div><div><h3>What stays out</h3><p>{_escape(construction['withheld'])}</p></div></div>
      <div class="summary-grid">{construction_markup}</div>
      <aside class="principle">{_escape(construction['warning'])}</aside>
      <aside class="principle">{_escape(construction['agentic_claim'])}</aside>
      <p><a href="../architecture/04_rule_construction/ARCH_004_REPORT.md">Open the deep construction audit</a> · <a href="../architecture/04_rule_construction/ARCH_004_RULE_DSL.md">Rule DSL boundary</a> · <a href="../architecture/04_rule_construction/ARCH_004_AGENTIC_CLAIM_BOUNDARY.md">Agentic claim boundary</a></p>
      <p><strong>Next deep review:</strong> {_escape(construction['next_deep_review'])}</p>
    </section>

    <section id="verifier-common42" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">VERIFIER</p><h2>VERIFIER / COMMON-42 / AUTHORIZATION</h2></div>
      <p class="architecture-flow">Proposal → Task Validity → Executable Equivalence → COMMON-42 V4 Portfolio → Evaluator Authority → Committed D1 Grant</p>
      <div class="status-snapshot">
        <div><span>Canonical Verifier</span><strong>20 deterministic stages</strong></div>
        <div><span>Task ↔ Canonical</span><strong>PARTIALLY OVERLAPPING</strong></div>
        <div><span>COMMON-42</span><strong>42 V4 descriptors</strong></div>
        <div><span>T2 utility</span><strong>NOT AUTHORIZED</strong></div>
        <div><span>Frozen D1 authority</span><strong>V4 + evaluator + committed grant</strong></div>
        <div><span>Preferred D1 term</span><strong>{_escape(verifier['preferred_d1_term'])}</strong></div>
      </div>
      <div class="two-column"><div><h3>What is bound</h3><dl class="architecture-contract">
        <div><dt>COMMON-42</dt><dd>{_escape(verifier['common42'])}</dd></div>
        <div><dt>D1 AUTHORITY</dt><dd>{_escape(verifier['d1_authority'])}</dd></div>
        <div><dt>NUMERIC REBINDING</dt><dd>{_escape(verifier['numeric_rebinding'])}</dd></div>
      </dl></div><div><h3>What remains separate</h3><dl class="architecture-contract">
        <div><dt>TASK VS CANONICAL</dt><dd>{_escape(verifier['task_canonical_relationship'])}</dd></div>
        <div><dt>T2</dt><dd>{_escape(verifier['t2_boundary'])}</dd></div>
        <div><dt>NO_RULE</dt><dd>{_escape(verifier['no_rule'])}</dd></div>
      </dl></div></div>
      <aside class="principle">Verifier acceptance is not scientific validation.</aside>
      <aside class="principle">Verifier acceptance is not runtime authorization.</aside>
      <p><a href="../architecture/05_verifier_common42/ARCH_005_REPORT.md">Open the deep verifier/COMMON-42 audit</a> · <a href="../architecture/05_verifier_common42/ARCH_005_COMMON42.md">COMMON-42 definition</a> · <a href="../architecture/05_verifier_common42/ARCH_005_RUNTIME_AUTHORIZATION.md">Runtime authorization</a></p>
      <p><strong>Next deep review:</strong> {_escape(verifier['next_deep_review'])}</p>
    </section>

    <section id="runtime-trace-explanation" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">RUNTIME</p><h2>RULE RUNTIME / TRACE / EXPLANATION</h2></div>
      <p class="architecture-flow">COMMON-42 → Rule Evaluation → Task Trace → D1 Prediction → In-memory Freeze → Label Access → Metrics</p>
      <div class="status-snapshot">
        <div><span>Runtime authority</span><strong>V4 TASK-SPECIFIC</strong></div>
        <div><span>Runtime LLM</span><strong>NO — FROZEN R0/D1</strong></div>
        <div><span>Determinism</span><strong>{_escape(runtime['determinism'])}</strong></div>
        <div><span>Trace authority</span><strong>TASK-SPECIFIC / NON-EQUIVALENT</strong></div>
        <div><span>Durable pre-label freeze</span><strong>NO</strong></div>
        <div><span>Explanation human validation</span><strong>{_escape(runtime['human_usefulness'])}</strong></div>
      </div>
      <div class="two-column"><div><h3>Runtime contract</h3><dl class="architecture-contract">
        <div><dt>AUTHORITY</dt><dd>{_escape(runtime['authority'])}</dd></div>
        <div><dt>TRIGGER</dt><dd>{_escape(runtime['trigger'])}</dd></div>
        <div><dt>TARGET RESPONSE</dt><dd>{_escape(runtime['target_response'])}</dd></div>
        <div><dt>TOLERANCE / PERSISTENCE</dt><dd>{_escape(runtime['tolerance'])} {_escape(runtime['persistence'])}</dd></div>
      </dl></div><div><h3>Prediction and trace boundary</h3><dl class="architecture-contract">
        <div><dt>D1 PREDICTION</dt><dd>{_escape(runtime['prediction'])}</dd></div>
        <div><dt>FREEZE</dt><dd>{_escape(runtime['freeze_classification'])}; durable persistence = NO</dd></div>
        <div><dt>LABEL ACCESS</dt><dd>{_escape(runtime['label_access'])}</dd></div>
        <div><dt>TRACE</dt><dd>{_escape(runtime['trace_type'])}; {_escape(runtime['canonical_trace_relationship'])}</dd></div>
        <div><dt>EXPLANATION</dt><dd>{_escape(runtime['explanation'])}</dd></div>
      </dl></div></div>
      <aside class="principle">{_escape(runtime['warning'])}</aside>
      <p><a href="../architecture/06_runtime_trace_explanation/ARCH_006_REPORT.md">Open the deep runtime audit</a> · <a href="../architecture/06_runtime_trace_explanation/ARCH_006_D1_FREEZE_BOUNDARY.md">D1 freeze boundary</a> · <a href="../architecture/06_runtime_trace_explanation/ARCH_006_TRACE_SCHEMA.csv">Trace comparison</a> · <a href="../architecture/06_runtime_trace_explanation/ARCH_006_EXPLANATION_RENDERER.md">Explanation boundary</a></p>
      <p><strong>Next deep review:</strong> {_escape(runtime['next_deep_review'])}</p>
    </section>

    <section id="d0-detector" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">D0</p><h2>PCA-SPE REFERENCE DETECTOR</h2></div>
      <p class="architecture-flow">normal train1+train2 → scaler/PCA → normal train3 q=.999 calibration → test1 SPE → strict point alarm → durable prediction freeze → label metrics</p>
      <div class="status-snapshot">
        <div><span>Role</span><strong>REFERENCE DETECTOR</strong></div>
        <div><span>Input</span><strong>{d0['features']} ordered P1 features</strong></div>
        <div><span>PCA</span><strong>0.95 target → k={d0['selected_components']}</strong></div>
        <div><span>Calibration</span><strong>train3 · q=.999</strong></div>
        <div><span>Prediction</span><strong>test1 · PILOT</strong></div>
        <div><span>Baseline strength</span><strong>{_escape(d0['baseline_strength'])}</strong></div>
      </div>
      <div class="two-column"><div><h3>Model and decision</h3><dl class="architecture-contract">
        <div><dt>FIT</dt><dd>{_escape(d0['fit_split'])}; labels used = NO</dd></div>
        <div><dt>STANDARDIZATION</dt><dd>{_escape(d0['standardization'])}</dd></div>
        <div><dt>SPE</dt><dd>{_escape(d0['spe'])}</dd></div>
        <div><dt>THRESHOLD</dt><dd>{_escape(d0['threshold'])}</dd></div>
        <div><dt>COMPARATOR</dt><dd>{_escape(d0['comparator'])}</dd></div>
      </dl></div><div><h3>Frozen pilot and custody</h3><dl class="architecture-contract">
        <div><dt>LABEL ORDER</dt><dd>{_escape(d0['prediction_freeze'])}</dd></div>
        <div><dt>DETERMINISM</dt><dd>{_escape(d0['determinism'])}</dd></div>
        <div><dt>ATTACK EVENTS</dt><dd>{_escape(d0['attack_event_response'])}</dd></div>
        <div><dt>NORMAL FAR</dt><dd>{d0['normal_far_episodes_per_hour']} episodes/hour</dd></div>
        <div><dt>OUTPUT LEVELS</dt><dd>{d0['point_alarms']} point alarms; {d0['alarm_episodes']} alarm episodes; {d0['normal_false_alarm_episodes']} normal false episodes</dd></div>
      </dl></div></div>
      <aside class="principle">{_escape(d0['warning'])}</aside>
      <p><a href="../architecture/07_d0_detector/ARCH_007_REPORT.md">Open the deep D0 audit</a> · <a href="../architecture/07_d0_detector/ARCH_007_SPE_DEFINITION.md">SPE definition</a> · <a href="../architecture/07_d0_detector/ARCH_007_FREEZE_BOUNDARY.md">Prediction freeze</a> · <a href="../architecture/07_d0_detector/ARCH_007_OUTPUT_LEVELS.md">Output levels</a></p>
      <p><strong>Next deep review:</strong> {_escape(d0['next_deep_review'])}</p>
    </section>

    <section id="data-governance" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">DATA</p><h2>DATA GOVERNANCE</h2></div>
      <div class="status-snapshot">
        <div><span>Dataset</span><strong>{_escape(governance['dataset'])}</strong></div>
        <div><span>Process</span><strong>{_escape(governance['process'])}</strong></div>
        <div><span>Feature / role scope</span><strong>{_escape(governance['source_scope'])}</strong></div>
        <div><span>Leakage status</span><strong>{_escape(governance['leakage_status'])}</strong></div>
        <div><span>Test1</span><strong>{_escape(governance['test1_status'])}</strong></div>
        <div><span>Test2</span><strong>{_escape(governance['test2_status'])}</strong></div>
      </div>
      <div class="summary-grid">{split_markup}</div>
      <aside class="principle">{_escape(governance['label_access'])}</aside>
      <p><a href="../architecture/01_data_and_splits/ARCH_001_REPORT.md">Open the deep data/split audit</a> · <a href="../architecture/01_data_and_splits/ARCH_001_LABEL_ACCESS_TIMELINE.md">Label-access timeline</a> · <a href="../architecture/01_data_and_splits/ARCH_001_MISMATCHES.md">Data/split mismatches</a></p>
      <p><strong>Next deep review:</strong> {_escape(governance['next_deep_review'])}</p>
    </section>

    <section id="candidate-discovery" class="section panel-feature">
      <div class="section-heading"><p class="eyebrow">DISCOVERY</p><h2>CANDIDATE DISCOVERY</h2></div>
      <div class="status-snapshot">
        <div><span>Universe</span><strong>{_escape(discovery['candidate_universe'])}</strong></div>
        <div><span>Union</span><strong>{_escape(discovery['union'])}</strong></div>
        <div><span>Learned graph</span><strong>USED</strong></div>
        <div><span>Attention as final evidence</span><strong>NO</strong></div>
        <div><span>Post-hoc XAI</span><strong>NO</strong></div>
        <div><span>GDN contribution</span><strong>UNVALIDATED</strong></div>
      </div>
      <div class="summary-grid">{discovery_markup}</div>
      <aside class="principle">{_escape(discovery['warning'])}</aside>
      <p><a href="../architecture/02_candidate_discovery/ARCH_002_REPORT.md">Open the deep candidate-discovery audit</a> · <a href="../architecture/02_candidate_discovery/ARCH_002_GDN_PROFESSOR_ANSWER.md">GDN professor answer</a> · <a href="../architecture/02_candidate_discovery/ARCH_002_MISMATCHES.md">Discovery mismatches</a></p>
      <p><strong>Next deep review:</strong> {_escape(discovery['next_deep_review'])}</p>
    </section>

    <section id="my-tasks" class="section">
      <div class="section-heading"><p class="eyebrow">02</p><h2>MY TASKS</h2></div>
      <p class="section-intro">Highest-priority research work recorded in the current-state registry.</p>
      {_bullet_list(state['top_user_todo'])}
    </section>

    <section id="decisions" class="section">
      <div class="section-heading"><p class="eyebrow">03</p><h2>DECISION INBOX</h2></div>
      {decision_content}
    </section>

    <section id="architecture" class="section panel-dark">
      <div class="section-heading"><p class="eyebrow">04</p><h2>ARCHITECTURE OVERVIEW</h2></div>
      <p class="architecture-flow">{_escape(state['architecture_flow'])}</p>
      <p class="section-intro">ARCH-000 verified real source, execution, and artifact lineage. Open a domain to see its high-level contract; unverified links remain visible in the detailed maps.</p>
      <div class="architecture-detail-grid">{architecture_markup}</div>
      <p><a href="../architecture/00_overview/ARCH_000_REPORT.md">Open the full architecture audit</a> · <a href="../architecture/00_overview/ARCH_000_MISMATCHES.md">Review documented mismatches</a> · <a href="../architecture/00_overview/DEEP_REVIEW_INDEX.md">Deep-review index</a></p>
    </section>

    <section class="section explorer" aria-label="Registry explorer">
      <div><label for="registry-search">Search registry</label><input id="registry-search" type="search" placeholder="Search names, evidence, risks, next actions…"></div>
      <div><label for="status-filter">Filter status</label><select id="status-filter"><option value="">All statuses</option>{status_options}</select></div>
      <p id="filter-count" aria-live="polite"></p>
    </section>

    <section id="components" class="section">
      <div class="section-heading"><p class="eyebrow">05</p><h2>COMPONENT STATUS</h2></div>
      <p class="section-intro">Legacy component tokens are translated for display. Evidence-reviewed is source/evidence review, not performance validation. A result-integrity audit requires an explicit result-specific artifact.</p>
      <div class="card-grid">{component_cards}</div>
    </section>

    <section id="experiments" class="section">
      <div class="section-heading"><p class="eyebrow">06</p><h2>EXPERIMENT STATUS</h2></div>
      <p class="section-intro">An evidence-reviewed pilot has checked evidence and artifacts within its recorded scope; it is not automatically a scientifically validated finding.</p>
      <div class="card-grid">{experiment_cards}</div>
    </section>

    <section id="claims" class="section">
      <div class="section-heading"><p class="eyebrow">07</p><h2>CLAIM &amp; EVIDENCE</h2></div>
      <p class="section-intro"><code>claims.csv</code> is the authoritative scientific claim view. Component compatibility fields do not determine scientific claim status.</p>
      <div class="card-grid">{claim_cards}</div>
    </section>

    <section id="risks" class="section">
      <div class="section-heading"><p class="eyebrow">08</p><h2>RISKS</h2></div><div class="card-grid">{risk_cards}</div>
    </section>

    <section id="history" class="section panel-history">
      <div class="section-heading"><p class="eyebrow">09</p><h2>RESEARCH HISTORY</h2></div>
      <p class="section-intro">A curated history of pivots and decisions, not an exhaustive commit log. USER_CONTEXT entries preserve uncertainty and never override current <code>claims.csv</code>.</p>
      <div class="timeline history-timeline">{history_markup}</div>
      <h3>Key active or conditional decisions</h3>
      <ul class="decision-list">{key_decisions_markup}</ul>
      <p><a href="../history/PROJECT_TIMELINE.md">Open the full research evolution</a> · <a href="../history/PROFESSOR_FEEDBACK_LINEAGE.md">Professor-feedback lineage</a> · <a href="../history/SUPERSEDED_DIRECTIONS.md">Superseded directions</a></p>
    </section>

    <section id="source-authority" class="section authority-detail">
      <div class="section-heading"><p class="eyebrow">10</p><h2>SOURCE AUTHORITY</h2></div>
      <dl>
        <div><dt>Scientific source</dt><dd>{_escape(authority['ref'])}<br><code>{_escape(authority['commit'])}</code></dd></div>
        <div><dt>Immutable pin</dt><dd>{_escape(state['immutable_scientific_pin']['tag'])}<br><code>{_escape(state['immutable_scientific_pin']['commit'])}</code></dd></div>
        <div><dt>Documentation overlay</dt><dd>{_escape(state['documentation_overlay']['ref'])}<br><code>{_escape(state['documentation_overlay']['commit'])}</code><br>{_escape(state['documentation_overlay']['role'])}</dd></div>
      </dl>
      <p>Scientific code and result claims derive from the scientific authority. Narrative context from the overlay cannot override it.</p>
    </section>

    <section id="recent-change" class="section">
      <div class="section-heading"><p class="eyebrow">11</p><h2>RECENT CHANGE / NEXT TASK</h2></div>
      <div class="timeline">{recent_markup}</div>
      <div class="next-task"><span>Exact next task</span><strong>{_escape(state['exact_next_task'])}</strong></div>
    </section>
  </main>

  <footer>Generated from RCC registry snapshot {_escape(state['generated_at'])} · Authority <code>{_escape(authority['commit'])}</code></footer>
  <script src="assets/rcc.js"></script>
</body>
</html>
"""


def _markdown_marker(state: Mapping[str, Any], digest: str) -> str:
    return f"<!-- {_source_marker(state, digest)} -->"


def _md_bullets(values: Iterable[object]) -> str:
    items = list(values)
    return "\n".join(f"- {item}" for item in items) if items else "- None recorded."


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def render_gpt_brief(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    experiments = "\n".join(
        f"- **{row['experiment_id']} · {row['name']}** — "
        f"`{EXPERIMENT_STATUS_LABELS.get(row['status'], row['status'])}`; "
        f"scope: {row['result_scope']}."
        for row in data["experiments"]
    )
    claims = "\n".join(
        f"- **{row['claim_id']} · {row['status']}** — {row['allowed_wording']}"
        for row in data["claims"]
    )
    risks = "\n".join(
        f"- **{row['severity']} / {row['status']}** — {row['description']}"
        for row in data["risks"] if row["severity"] in {"CRITICAL", "HIGH"}
    )
    phases = data["history"]["phases"]
    phase_names = " → ".join(phase["title"] for phase in phases[:9])
    return f"""{_markdown_marker(state, digest)}
# GPT Brief — Research Control Center

Generated from RCC registry version `{state['registry_version']}` at `{state['generated_at']}`.
Scientific authority: `{authority['ref']}` @ `{authority['commit']}`.

> Chat memory must not override the scientific authority or RCC registry.

## Research objective

{state['research_objective']}

## Current phase

**{state['current_phase']}** — {state['current_phase_statement']}

Phase progression: {' → '.join(state['phase_progression'])}.

## How to read RCC status

Engineering and scientific evidence are separate. Component `audited=true` means
**Evidence-reviewed**, not performance validated. A **Result-integrity audit** checks custody
and arithmetic, not generalization. Reproduction remains absent at component level. Scientific
claim status comes only from `claims.csv`; `claim_ready` supports narrow implementation or
contract wording.

These counts are not a single completion percentage.

## Architecture in one line

{state['architecture_flow']}

## Data and split boundary

HAI 23.05 P1 is selected. train1/train2 fit normal evidence; train3 confirms relations and
calibrates D0; train4 is a guard. test1 is pilot evidence. OUTER produced no result. D1 lacks
durable pre-label persistence; D2 V2 is test1-informed.

## Candidate-discovery boundary

META, STAT, and GDN separately rank the 144-pair universe; their Top-20 views form an unscored
47-pair union. Attention is not ranking evidence, XAI is absent, and GDN benefit is unvalidated.

## Relation and numeric-authority boundary

The lineage is 47 pairs → 94 directions → 25/45 fit-supported → 23/42 confirmed. Confirmation
cannot search or retune. Construction and runtime numeric identities remain separate. Repeated
normal response is not causal proof.

## Rule-construction boundary

E3 exposes a fixed relation, horizon, and normal-only references to a closed proposal schema.
`accepted_proposal` grants neither runtime authority nor detection performance. T2 feedback was zero.

## Frozen D1 runtime boundary

Frozen D1 uses task V4 with zero LLM calls. Its 788 anomalous records collapse to 630 seconds
and 626 metric episodes. Prediction preceded labels but was not durably persisted; its trace is
not `RuntimeTraceV1`, and no D1 explanation was rendered.

## Frozen D0 detector boundary

D0 is a 37-feature normal-only PCA-SPE reference. Train1+train2 fit custom NumPy PCA; train3
calibrates a no-interpolation q=.999 threshold; test1 uses strict `score > threshold`. Prediction
bytes were frozen before labels. The 11/14 pilot is neither SOTA nor thesis-contribution evidence.

## How we got here

The recorded evolution is **{phase_names}**. Early motives remain partly `USER_CONTEXT`.
ARGOS became partial support; deterministic verification survived the earlier Verifier framing.
HAI P1, META/STAT/GDN, normal-only profiling and numeric authority led to COMMON-42 and the
14-event pilot. OUTER ended in a custody blocker. History explains this lineage but cannot override current state.

## Established facts

{_md_bullets(state['established_facts'])}

The frozen discovery and construction counts establish pipeline execution and custody,
not causality, physical truth, unique GDN benefit, or agentic-feedback advantage. T2
performed zero feedback actions in the current cohort.

## Frozen INNER pilot observations

The INNER evaluation contains 14 independent attack events. D0 PCA-SPE responded to
11/14 with Normal FAR 0.4939336325682589 episodes/hour. D1 verified Rule-only responded
to 13/14 with Normal FAR 40.50255787059723 episodes/hour. Their event overlap was both
10, D0-only 1, D1-only 3, neither 0. D2 V1 and D2 V2 each responded to 11/14 and each
recovered 0/3 D0-missed events; their Normal FAR values were 0.7056194750975128 and
6.915070855955625 episodes/hour respectively. These are exact public frozen pilot
observations, not new calculations.

> 14 attack events are pilot evidence only. Do not describe current detection numbers as validated performance.

## Unresolved scientific questions

{_md_bullets(state['not_established'])}

Graph-Guided and Agentic remain provisional contribution labels. GDN produced candidate
evidence, but unique stable downstream usefulness remains unvalidated. The T2 control
path exists, but current evidence does not support a verifier-feedback advantage.

## Current experiments

{experiments}

## Claim boundaries

{claims}

## Current risks

{risks}

## Top user TODO

{_md_bullets(state['top_user_todo'])}

## Source-policy boundary

The read-only documentation overlay is `{state['documentation_overlay']['ref']}` @
`{state['documentation_overlay']['commit']}`. It provides narrative context only.
The historical checkout `{state['non_authoritative_checkout']['ref']}` @
`{state['non_authoritative_checkout']['commit']}` is not an authority for scientific claims.

## Exact next task

Management: **{state['recommended_next_management_task']}**

Following architecture review: **{state['recommended_next_architecture_task']}**

Scientific direction: preregister expanded Rule-only and detector comparison evidence,
then separately test GDN stability and an actually activated budget-matched feedback arm.
"""


def render_current_status(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    components = data["components"]
    component_summary = {
        "Implemented": sum(row["status"].startswith("IMPLEMENTED") for row in components),
        "Executed": sum(row["executed"] == "true" for row in components),
        "Evidence-reviewed": sum(row["audited"] == "true" for row in components),
        "Independently reproduced": sum(row["reproduced"] == "true" for row in components),
    }
    component_summary_rows = "\n".join(f"- **{label}:** {value}" for label, value in component_summary.items())
    component_rows = "\n".join(
        f"| {row['component_id']} | {COMPONENT_STATUS_LABELS.get(row['status'], row['status'])} | {row['next_action']} |"
        for row in components
    )
    experiment_rows = "\n".join(
        f"| {row['experiment_id']} | {EXPERIMENT_STATUS_LABELS.get(row['status'], row['status'])} | {row['result_scope']} |"
        for row in data["experiments"]
    )
    claim_rows = "\n".join(
        f"| {row['claim_id']} | {row['status']} | {row['allowed_wording']} |"
        for row in data["claims"]
    )
    return f"""{_markdown_marker(state, digest)}
# RCC Current Status

Scientific authority: `{authority['ref']}` @ `{authority['commit']}`
Registry version: `{state['registry_version']}`
Registry snapshot: `{state['generated_at']}`

## Current phase

**{state['current_phase']}**

{state['current_phase_statement']}

## How to read status

- **Implemented / executed:** engineering state only.
- **Evidence-reviewed:** the backward-compatible component `audited` field; source or
  evidence status was reviewed against the pinned authority. This is not performance validation.
- **Result-integrity audited:** only explicit result-specific integrity artifacts; custody,
  immutability, ordering, and arithmetic checks. This is not scientific validation.
- **Independently reproduced:** an independent reproduction under required environment and custody.
- **Scientifically validated:** adequate independent evidence for a stated hypothesis; never
  inferred from component status and governed by `claims.csv`.

These counts are not a single completion percentage. An evidence-reviewed governance or
documentation component need not be a scientific executable, so Evidence-reviewed may exceed Executed.

## Component summary

{component_summary_rows}

## Data / split audit

- **Dataset / process:** {state['data_governance']['dataset']} / {state['data_governance']['process']}
- **Label access:** {state['data_governance']['label_access']}
- **Leakage:** {state['data_governance']['leakage_status']}
- **Test1:** {state['data_governance']['test1_status']}
- **Test2:** {state['data_governance']['test2_status']}

## Frozen D1 runtime / trace audit

- **Authority:** {state['runtime_trace_explanation']['authority']}
- **Prediction:** {state['runtime_trace_explanation']['prediction']}
- **Freeze:** {state['runtime_trace_explanation']['freeze_classification']}; durable pre-label persistence = no.
- **Trace:** {state['runtime_trace_explanation']['canonical_trace_relationship']}
- **Explanation:** {state['runtime_trace_explanation']['explanation']}

## Components

| Component | Engineering / evidence display | Next action |
|---|---|---|
{component_rows}

The compatibility field `claim_ready` is intentionally omitted from this headline. It means
only that a component supports at least one narrow implementation or contract claim.

## Experiments

| Experiment | Status | Result scope |
|---|---|---|
{experiment_rows}

## Authoritative claim view

Claim status comes only from `registry/claims.csv`.

| Claim | Status | Allowed wording |
|---|---|---|
{claim_rows}

## Research dimensions

- **Engineering:** {state['research_status_summary']['engineering']}
- **Result integrity:** {state['research_status_summary']['result_integrity']}
- **Scientific validation:** {state['research_status_summary']['scientific_validation']}
- **Reproducibility:** {state['research_status_summary']['reproducibility']}
- **Generalization:** {state['research_status_summary']['generalization']}
- **Claims:** {state['research_status_summary']['claims']}

## Boundaries

Not established:

{_md_bullets(state['not_established'])}

## Exact next task

**{state['exact_next_task']}**
"""


def render_arch001_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    return f"""{_markdown_marker(state, digest)}
# 우리가 어떤 데이터를 쓰고 있는가

## 한 문장 답

우리는 공식 provenance가 고정된 HAI 23.05의 P1 Boiler 범위를 사용하며, 정상 학습
split과 INNER pilot, 아직 결과가 없는 held-out test2를 서로 다른 권한으로 다룬다.

## Split 한눈에 보기

| Split | 역할 | 무엇을 정하는 데 사용? | Label 사용? | 최종평가? |
|---|---|---|---|---|
| train1 | NORMAL FIT | 후보·관계·수치 authority·D0 fit | 아니오 | 아니오 |
| train2 | NORMAL FIT | train1과 독립적인 file-local fit 근거 | 아니오 | 아니오 |
| train3 | CONFIRMATION / CALIBRATION | 관계 확인과 D0 threshold 보정 | 아니오 | 아니오 |
| train4 | SANITY | normal guard와 D0 정상 sanity | 아니오 | 아니오 |
| test1 | PILOT EVALUATION | frozen 방법의 INNER 개발·예비 비교 | prediction 뒤에만 | 아니오 |
| test2 | HELD-OUT / UNAVAILABLE | 의도상 one-way 일반화 평가 | 실행되지 않음 | 결과 없음 |

## 왜 여러 train split이 있는가?

같은 normal data를 한 단계에서 만들고 같은 단계에서 확인하는 것을 피하려고 역할을
나눈다. train1/train2는 fit, train3는 독립 확인과 D0 threshold calibration, train4는
normal sanity에 사용된다. train3를 두 arm이 함께 쓰는 것은 확인된 leakage가 아니지만,
비교 독립성의 범위를 제한하므로 `ACCEPTABLE_WITH_SCOPE_LIMITATION`으로 기록했다.

## Rule을 만들 때 공격 답을 본 적이 있는가?

찾아본 현재 frozen 경로에서는 아니다. 후보 탐색, 관계 profiling, normal numeric
authority, evidence pack, T0/T1/T1-B/T2, verifier, COMMON-42는 normal-only evidence를
사용한다. test1 결과로 individual rule을 뒤에서 삭제하거나 COMMON-42를 다시 고른
경로도 확인되지 않았다.

## D0 threshold는 어디서 결정되는가?

D0는 train1과 train2로 표준화와 PCA를 fit하고, train3의 normal SPE 분포로 threshold를
calibrate한다. test1 label이나 test1 outcome은 model fit과 threshold 결정에 들어가지 않는다.

## Label은 언제 보이는가?

D0와 D2는 prediction file을 atomic하게 기록하고 다시 읽은 뒤 label을 연다. D1도
label-blind prediction object를 먼저 만들고 self-hash를 검증하지만, public prediction
file은 metric 뒤에 기록된다. 그래서 D1은 decision-before-label은 확인됐지만 durable
file-before-label 보장은 부족하다. 이것은 HIGH governance gap이며 leakage가 확인됐다는
뜻은 아니다.

## test1은 왜 final test가 아닌가?

현재 14개 사건은 작은 INNER pilot이다. 특히 D2 V2 policy는 앞선 INNER 결과를 알고
설계되었다고 명시되어 있다. 따라서 test1 수치는 개발·예비 관찰이며 독립 성능 검증이나
일반화 증거가 아니다.

## test2는 왜 결과가 없는가?

OUTER recovery는 test2 feature custody 확인에서 멈췄다. 파일 접근 시도는 한 번 있었지만
feature byte, hash, semantic parse는 0이고 label·prediction·metric도 0이다. 따라서
성능이 실패한 것이 아니라 **held-out result unavailable**이다.

## 현재 leakage 우려는 무엇인가?

**NO VERIFIED LEAKAGE FOUND.** 다만 D1 durable persistence gap, task별로 분산된 split
enforcement, train3 dual use, test1-informed D2 V2 때문에 “leakage impossible”이라고는
말할 수 없다.

## 다음 파트 전에 이해할 것

1. feature 파일과 label 파일은 별도 authority다.
2. 86 dataset points, 37 P1 features, 12×12 role universe는 같은 숫자가 아니다.
3. label-blind object와 durable prediction file은 서로 다른 보장이다.
4. test1은 pilot이고 test2는 결과가 없다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch002_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    return f"""{_markdown_marker(state, digest)}
# 관계 후보는 왜 세 방식으로 고르는가

## 한 문장 답

144개 가능한 source→target 쌍을 META·STAT·GDN이 서로 다른 근거로 20개씩 제안하고,
중복을 접은 47개만 다음 normal relation profiling이 검사한다.

| 방식 | 무엇을 보는가 | 무엇을 내놓는가 | 아직 말할 수 없는 것 |
|---|---|---|---|
| META | reviewed metadata와 physical graph | domain-prior 후보 Top-20 | 물리적 진실·인과 |
| STAT | normal train1/train2의 lagged 변화 상관 | association 후보 Top-20 | confirmed response·인과 |
| GDN | 정상 multivariate next-value prediction | learned-graph 후보 Top-20 | 고유 유용성·인과·attention 설명 |

## 왜 관계 후보를 먼저 줄이는가?

모든 가능한 쌍을 규칙으로 만들지 않고 서로 다른 약한 근거로 profiling 대상만 제한하기
위해서다. 이 단계는 관계를 확정하는 단계가 아니다.

## 144개는 어디서 나오는가?

P1의 ordered source 역할 12개와 target 역할 12개의 directed cross product다. 두 역할
집합은 현재 freeze에서 겹치지 않으므로 12×12=144다.

## META는 무엇을 보는가?

실제 센서 값을 읽지 않고 reviewed official metadata와 directed physical graph를 본다.
명시 연결, graph adjacency, subsystem support 순으로 분류하고 공식 reference 수와
identity로 결정적으로 정렬한다. 학습 score는 없다.

## STAT은 무엇을 보는가?

train1과 train2 각각에서 source/target의 1초 변화량을 만들고 여러 lag에서 Pearson
association을 계산한다. 두 파일에서 부호가 안정적인지 확인하고 약한 쪽 strength로
정렬한다. 후속 delayed-response profiling과는 별개다.

## GDN은 무엇을 학습하는가?

37개 P1 node의 5초 history로 다음 1초 값을 예측한다. 학습된 node embedding의 cosine
similarity로 target별 neighbor graph를 만들고 세 seed에서 반복 선택된 edge를 우선한다.
현재 Top-5는 diagonal/self를 먼저 제거하지 않아 자기 node가 내부 슬롯을 차지할 수 있다.
후속 disjoint-role projection이 exported self-pair는 제거하지만 기능적 영향은 미검증이다.

## GDN attention을 쓰는 것인가?

모델 내부 message passing에는 attention을 쓴다. 그러나 attention coefficient를 후보
ranking이나 최종 관계 evidence로 쓰지 않는다. 후보 authority는 embedding-cosine
learned graph다. 별도 XAI나 SHAP도 쓰지 않는다.

## GDN edge는 어떤 의미인가?

target 예측에 선택된 neighbor/input dependency **후보**다. 원인, root cause, 확정된
시간 관계가 아니다.

## 20+20+20인데 왜 47개인가?

세 arm에서 겹친 pair를 exact directed identity로 한 번만 남기기 때문이다. META-only 8,
STAT-only 8, GDN-only 18, 두 arm 공통 13, 세 arm 공통 0으로 총 47이다. Arm score는
합치거나 비교하지 않으므로 47개 전체 순위도 없다.

## 다음 단계에서 무엇을 검증하는가?

47개 cohort를 normal delayed-response profiling에 넘겨 step event, response direction,
horizon과 안정성을 별도로 확인한다. 그 전에는 최종 relation이라고 부르면 안 된다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch003_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    return f"""{_markdown_marker(state, digest)}
# 47개 후보는 어떻게 42개 실행 관계가 되는가

## 한 문장 답

47개 pair를 정상 train1·train2의 반복 source step과 delayed target response로 검사하고,
선택된 relation만 train3에서 검색·재조정 없이 확인한 뒤, 별도 numeric authority를 붙여
실행 가능하게 만든다.

## 단계별 숫자

| 단계 | 수 | 의미 |
|---|---:|---|
| Candidate pairs | 47 | discovery가 제안한 source-target 조합 |
| Source-direction opportunities | 94 | pair마다 step_up·step_down을 별도로 검사 |
| Fit-supported | 25 contexts / 45 directions | train1·train2 gate 통과 |
| Confirmed | 23 contexts / 42 relations | 고정 identity가 train3 gate 통과 |

## 1. 47개 후보 중 무엇을 검사하는가?

source가 정상 구간에서 충분히 크고 지속적인 step을 만들었을 때 target이 일정 시간 뒤
같은 방향으로 반복 반응하는지 검사한다. 후보는 아직 관계가 아니고, source sign,
target sign, horizon이 정해져야 relation이 된다.

## 2. Source event와 target response

Source event는 직전 5행과 이후 5행 median 차이가 normal-derived threshold 이상이고 양쪽이
안정적일 때 생긴다. 같은 source의 가까운 event는 single-link 10행 cluster로 묶고, 다른
source event가 ±2행 안에 있으면 isolation에서 제외한다.

Target response는 event 전 5행 median을 baseline으로 하고, horizon 뒤 3행 median에서
baseline을 뺀 값이다. 파일 끝의 불완전 window는 버리며 보간하지 않는다.

## 3. Lag/horizon은 무엇이며 왜 여러 개를 보는가?

반응이 즉시 오지 않을 수 있어 1, 5, 10, 30, 60행 지연을 미리 고정해 비교한다. 각
source direction에서 consistency, effect, 짧은 horizon 순으로 하나만 고른다. 선택된
horizon은 이 유한 grid의 규칙상 winner이지 물리적 최적값이 아니다.

## 4. Consistency와 effect

Consistency는 usable event 중 target response가 선택 방향의 normal noise scale을 넘은
비율이다. Effect는 target response median의 절댓값을 target noise scale로 나눈 비율이다.
Support, consistency, effect, 두 fit file의 방향 우세를 모두 통과해야 한다.

## 5. 왜 train3에서 다시 확인하는가?

train1·train2에서 골랐던 relation이 다른 normal file에서도 유지되는지 보기 위해서다.
train3는 source/target/sign/horizon/parameter를 바꾸지 않고 같은 항목만 검사한다. 실패하면
conflict로 남고 다른 horizon이나 방향을 찾지 않는다.

## 6. 23 pair contexts와 42 relations의 차이

한 source-target pair에서 `step_up`과 `step_down`이 각각 별도 relation이 될 수 있다.
그래서 23개의 pair context 안에 42개의 directional relation이 존재한다.

## 7. Numeric authority는 무엇인가?

실행 숫자가 어느 normal split, relation, 계산 함수, artifact, hash에서 왔는지를 함께
고정한 권한이다. LLM은 authoritative number를 정하지 않는다.

Construction 시점에는 relation마다 11개 reference, 총 462개가 있었다. Frozen D1 runtime은
새 version의 normal-only authority에서 relation마다 10개 private role, 총 420개를 사용하고,
horizon은 canonical descriptor에서 사용한다. Focused audit는 공유 420개 value가 E1과 정확히
일치함을 확인했지만, 두 authority identity 자체가 같다는 뜻은 아니다.

## 8. 왜 causal relation이라고 부르면 안 되는가?

정상 데이터에서 반복되는 순서와 방향을 operationalize했을 뿐, intervention이나 물리 법칙,
root-cause를 검증하지 않았다. Held-out 일반화도 아직 확인되지 않았다.

## 다음 파트 전에 이해할 것

1. candidate, fit-supported, confirmed, runtime-bound는 서로 다른 단계다.
2. train3는 재탐색이 아니라 고정 relation의 확인이다.
3. value equality와 authority identity equality는 다르다.
4. relation numeric authority와 D0 PCA-SPE threshold는 별개다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch004_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    construction = state["rule_construction_authority"]
    return f"""{_markdown_marker(state, digest)}
# Rule은 어떻게 만들어지는가

## Evidence Pack

정상 데이터에서 확인한 relation을 제한된 construction view로 만든다. E1의 11개 role 중
horizon은 fixed relation field로, 나머지 10개는 값과 reference로 보인다. raw HAI, label,
attack, test/utility outcome, D0/D1 result와 runtime authority는 포함되지 않는다.

## LLM과 DSL 경계

LLM은 값을 볼 수 있지만 output에는 승인 reference만 반환한다. strict proposal schema에는
arbitrary numeric literal, Python, file/network access, 새 operator, free-form runtime logic가 없다.
새 variable이나 relation/horizon mismatch는 뒤의 deterministic validity가 거부한다.

## 네 construction arm

| Arm | LLM | Call policy | Frozen relation outcome |
|---|---|---|---|
| T0 | no | local deterministic template | 42/42 accepted proposal |
| T1 | yes | one call | 42/42 accepted proposal |
| T1-B | yes | three stateless calls, earliest admissible | 42/42 selected proposal |
| T2 | yes | maximum three, bounded feedback | 39/42 accepted; 3 no_rule |

T1-B는 126 calls를 모두 썼고, T2는 42 calls 모두 call 1에서 종료했다. 따라서 maximum
opportunity budget은 비교 가능하지만 realized cost가 같다고 말할 수 없다.

## Feedback은 실제 사용됐는가?

{construction['agentic_claim']}

T2의 세 no_rule은 unsupported-variable non-repairable validity issue였다. revise 0, retrieve 0,
follow-up 0이다. 따라서 “feedback improved quality”라고 말할 수 없다.

주의: task-specific orchestrator는 response/schema failure, verifier rejection, budget exhaustion도
`no_rule`로 합칠 수 있다. 이는 generic/frozen protocol의 explicit-failure 분리와 맞지 않는 HIGH
contract gap이며, frozen 세 건의 구체 원인을 바꾸지는 않는다.

## 42/42의 정확한 뜻

relation-level `accepted_proposal` 수다. canonical Rule v1 materialization, COMMON-42 membership,
runtime authorization 또는 detection performance 수가 아니다. `no_rule`은 construction의
fail-closed outcome이며 runtime `abstain`과 다르다.

## 재현성

T0는 frozen input에서 deterministic하다. LLM arms는 model/config, prompt, evidence, request,
response와 ledger hash가 추적되지만 temperature 0.7, seed 없음이므로 bitwise deterministic하지 않다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch005_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    verifier = state["verifier_common42_authority"]
    return f"""{_markdown_marker(state, digest)}
# Proposal부터 COMMON-42와 D1까지

Proposal은 frozen relation에 묶인 construction 후보이고, canonical `DelayedResponseRuleV1`은
graph/evidence/parameter/output까지 포함하는 다른 계약이다. 두 validity layer는
`PARTIALLY_OVERLAPPING`이며 frozen path에서 lossless bridge는 발견되지 않았다.

Canonical `VerifierV1`은 20단계로 contract와 binding을 검사하지만 scientific truth, causality,
utility, optimality 또는 generalization을 증명하지 않는다. Accepted도 runtime authorization이 아니다.

COMMON-42는 T0/T1/T1-B가 공통으로 가진 42개 executable projection을 하나의 V4 descriptor
portfolio로 중복 제거한 것이다. T2는 39 accepted와 3 no_rule이며 D1 utility authority에서
제외됐다. 따라서 D1 권장 명칭은 **{verifier['preferred_d1_term']}**이다.

Frozen D1은 canonical RuntimeAuthorizationBundleV1이 아니라 V4 authority, evaluator bundle,
private numeric custody와 committed one-attempt INNER grant를 사용했다. 420 shared values는 exact
match였지만 runtime authority/reference identity는 별도로 rebound됐다.

세 frozen T2 no_rule은 unsupported-variable non-repairable validity outcome으로 확인됐다. 그러나
일반 orchestration은 response/parse/rejection/budget failure도 no_rule로 합칠 수 있어 code-fix risk가 남는다.

기억할 한 문장: **Verifier acceptance는 scientific validation도 runtime authorization도 아니다.**

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch006_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    runtime = state["runtime_trace_explanation"]
    return f"""{_markdown_marker(state, digest)}
# Rule은 실제 시계열에서 어떻게 판단하는가

## 1. Rule은 언제 발동하는가?

Frozen D1은 매 초 모든 Rule을 판정하는 방식이 아니다. 5개 행의 source 전·후 median이
수치 권한의 magnitude·stability 조건과 방향을 만족하면 하나의 **opportunity**가 생긴다.
같은 source의 10초 single-link cluster에서는 절대 step amplitude가 가장 큰 후보를 남기며,
정확히 동률이면 가장 이른 index를 남긴다. 다른 source event와 ±2초로 겹치는 후보도 제외한다.

## 2. 발동하지 않으면 정상인가, abstain인가?

둘 다 아니다. source event가 없으면 opportunity 자체가 없고 terminal outcome도 없다.
`abstain`은 이미 형성된 opportunity를 미래 window 부족 등으로 평가할 수 없을 때만 나온다.

## 3. Rule이 깨졌다는 것은 무엇인가?

고정 horizon 뒤 target의 3개 행 median이 정상 데이터에서 결속된 expected direction과
noise 조건을 만족하지 못했다는 실행 계약상의 뜻이다. 물리적 원인이나 causal root cause를
증명하는 뜻이 아니다.

## 4. PASS와 FAIL은 무엇인가?

- PASS shorthand는 실제 코드의 `evaluated_expected_response`이며 alarm이 아니다.
- FAIL shorthand는 `evaluated_anomaly`이며 그 decision index에 alarm을 만든다.
- ABSTAIN은 평가 불가능 상태이고 alarm이 아니다.
- 권한·custody·replay 오류는 hard system error이며 abstain이 아니다.

## 5. 42개 결과를 어떻게 D1 alarm으로 만드는가?

어느 Rule이든 `evaluated_anomaly`이면 해당 decision second가 D1 alarm이 된다. Frozen artifact는
6,031 opportunity record와 788 anomalous rule record를 담지만, 같은 시점 중복을 제거하면
630 unique alarm seconds다. 이어진 seconds를 묶은 626 episodes는 metric 단계의 별도 산출물이다.

## 6. Trace에는 무엇이 들어가는가?

Frozen D1 trace는 opportunity, source-event hash, relation hash, terminal state, alarm,
decision index, numeric reference IDs, computation identity를 묶은 task-specific terminal hash다.
단계별 `RuntimeTraceV1` 객체는 저장하지 않았다.

## 7. D1 prediction은 label보다 먼저 정해지는가?

그렇다. 전체 label-blind prediction object를 만든 뒤 검증하고 shallow-frozen 상태로 custody를
확인한 후에 label-test1을 연다. 그래서 현재 분류는 **{runtime['freeze_classification']}**이다.

## 8. 왜 durable file freeze가 더 강한가?

현재 object는 top-level frozen dataclass이지만 내부 record dict는 mutable이고, public prediction
file은 metric 계산 뒤에 저장된다. Label 전에 bytes를 atomic하게 저장·재개방하고 label 뒤 동일
bytes를 다시 확인하면 process boundary가 생겨 더 강한 증거가 된다. Frozen pilot은 수정하지 않는다.

## 9. Runtime은 정말 LLM-free인가?

Frozen fixed-rule R0/D1 runtime에서는 LLM, provider, network call이 0이다. 이 문장을 미래 R1이나
전체 가능한 runtime 설계까지 일반화하면 안 된다.

## 10. 설명은 trace를 얼마나 그대로 반영하는가?

Canonical `RuntimeTraceV1`용 deterministic template renderer는 variable·lag·provenance binding을
재검증한다. 그러나 frozen V4 D1은 `RuntimeTraceV1`을 만들지도 renderer를 호출하지도 않았으며,
frozen D1 explanation artifact도 없다.

## 11. 설명이 root cause를 말할 수 있는가?

아니다. Canonical renderer는 causal/root-cause flag를 금지한다. 현재 보장 가능한 것은 canonical
synthetic path의 구조적 binding뿐이며 사람에게 유용한지는 **UNVALIDATED**다.

## 12. 현재 가장 중요한 runtime 위험은 무엇인가?

V4 frozen path와 canonical Rule/Trace 설명을 혼동하는 것, label 전 durable persistence가 없는 것,
그리고 설명 구현이 frozen D1에 실제 연결된 것처럼 표현하는 것이 가장 중요한 위험이다.

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_arch007_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    d0 = state["d0_detector"]
    return f"""{_markdown_marker(state, digest)}
# D0 PCA-SPE를 쉽게 이해하기

## 1. PCA는 왜 쓰는가?

37개 P1 변수가 정상일 때 함께 움직이는 큰 패턴을 작은 수의 축으로 요약하기 위해 쓴다.
D0는 이 정상 패턴에서 벗어난 정도를 보는 단순한 비교 기준선이다.

## 2. 정상 패턴을 어떻게 학습하는가?

Normal train1과 train2만 사용한다. 각 변수의 평균과 population 표준편차로 표준화하고,
custom NumPy PCA에서 누적 설명분산 0.95 이상이 되는 최소 축 수를 고른다. Frozen fit은
10개 축을 선택했고 27개 residual dimension을 남겼다.

## 3. SPE는 무엇인가?

한 시점의 37개 값을 PCA 정상 공간으로 복원한 뒤, 원래 표준화 값과 복원값 차이의 제곱을
합한 값이다. SPE가 크다는 것은 정상 PCA 공간으로 잘 설명되지 않는다는 뜻이다. Probability나
causal score는 아니다.

## 4. Threshold는 누가 정하는가?

이미 고정된 model로 normal train3의 SPE를 만들고 q=.999의 exact order statistic을 사용한다.
Interpolation은 없고, 정확한 판정은 `score > threshold`다. 같은 값은 alarm이 아니다.

## 5. Attack label을 보고 threshold를 정했는가?

아니다. Fit은 train1+train2 normal, calibration은 train3 normal이고 artifact에는
`labels_used=false`, `test_used=false`가 결속돼 있다. Test1 label은 durable prediction 파일을
쓰고 다시 검증한 뒤에만 열린다.

## 6. test1에서는 무엇을 하는가?

54,000개 test1 feature row에 frozen scaler/PCA/threshold를 적용해 label-blind Boolean prediction을
만든다. 공개 prediction은 raw score나 private threshold가 아니라 row index, alarm 여부와 hash를 담는다.

## 7. 11/14와 FAR/hour는 무엇인가?

| Level | Frozen pilot meaning |
|---|---|
| Point alarm | 876개 row가 threshold를 넘음 |
| Alarm episode | 연속 alarm point를 묶은 46개 구간 |
| Attack-event response | 14개 독립 사건 중 11개가 alarm episode와 겹침 |
| Normal false episode | 46개 중 attack timestamp와 겹치지 않은 7개 |
| Normal FAR/hour | 7개 normal false episode를 normal exposure hour로 나눈 `{d0['normal_far_episodes_per_hour']}` |

FAR/hour는 point false-positive rate가 아니다. 11/14도 point recall이 아니라 attack-event recall이다.

## 8. 왜 D0를 SOTA detector라고 하면 안 되는가?

D0는 선형 PCA residual을 쓰는 단순하고 추적 가능한 reference detector다. 현재 비교는 강한 최신
multivariate TSAD 전체를 대표하지 않는다. D0는 thesis contribution이 아니며 frozen 결과는 14-event
INNER pilot일 뿐이다.

## 9. D0와 Rule-only를 비교하는 목적은 무엇인가?

서로 다른 원리의 reference detector와 verified relational Rule-only가 어떤 사건에 반응하고 어떤
false-alarm trade-off를 보이는지 분리해서 관찰하는 것이다. 현재 결과로 어느 쪽의 일반적 우수성을
결론내리면 안 된다.

## 10. 앞으로 stronger detector가 왜 필요한가?

Rule-only 기여를 설득력 있게 평가하려면 새 독립 사전등록에서 더 많은 사건과 적어도 하나의 더
강한 multivariate detector baseline이 필요하다. ARCH-007은 그 detector를 선택하거나 구현하지 않았다.

기억할 한 문장: **D0는 normal-only로 고정된 단순 reference detector이고, 점수·point·episode·event를
구분해야 하며, 14-event 수치는 pilot evidence다.**

다음 task는 **{state['exact_next_task']}**이다.
"""


def render_change_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    events = sorted(data["timeline"], key=lambda row: (row["date"], row["event_id"]), reverse=True)
    rows = "\n".join(
        f"- **{row['date']} — {row['title']}** (`{row['status']}`): {row['summary']}"
        for row in events
    )
    return f"""{_markdown_marker(state, digest)}
# RCC Change Summary

Scientific authority: `{authority['ref']}` @ `{authority['commit']}`
Registry version: `{state['registry_version']}`

## Recorded timeline

{rows}

## Next

**{state['exact_next_task']}**
"""


def render_current_context(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    authority = state["scientific_authority"]
    pilot = state["pilot_observations"]
    return f"""{_markdown_marker(state, digest)}
# Current Research Context

Last updated: {state['last_updated']}
Scientific authority: `{authority['ref']}` @ `{authority['commit']}`
Documentation overlay: `{state['documentation_overlay']['ref']}` @ `{state['documentation_overlay']['commit']}`
RCC version: `{state['rcc_version']}`

## Current Phase

ARCHITECTURE_COMPLETE → **EVALUATION_SCOPE_EXPANSION (CURRENT)** → HYPOTHESIS_VALIDATION

Architecture implementation and pilot operation are complete. Scientific validation is partial,
held-out generalization is unconfirmed, and fresh-machine reproduction is incomplete.

## HOW TO READ STATUS

- Implemented and Executed describe engineering state.
- Evidence-reviewed is the backward-compatible component `audited` field: source or evidence
  status was reviewed. It does not mean performance validation.
- Result-integrity audited applies only to an explicit result-specific integrity artifact and
  checks custody and arithmetic. It does not mean scientific validation.
- Independently reproduced is a separate state and is currently zero at component level.
- `claims.csv` alone controls authoritative scientific claim status. Component `claim_ready`
  supports narrow implementation or contract wording only.

These states are not a single completion percentage. Evidence-reviewed can exceed Executed
because governance and documentation evidence can be reviewed without scientific execution.

## WHAT EXISTS

The pinned repository contains the end-to-end HAI 23.05 P1 INNER path: provenance and
split governance, a 144-pair role universe, META/STAT/GDN candidate discovery, a 47-pair
union, normal temporal profiling, normal-only numeric authority, typed evidence, bounded
T0/T1/T1-B/T2 construction, deterministic verification, COMMON-42, LLM-free fixed-rule
runtime, D0/D1/D2 evaluation, event/episode metrics, and integrity audits.

## DATA / SPLIT FOUNDATION

- **Dataset / process:** {state['data_governance']['dataset']} / {state['data_governance']['process']}.
- **Roles:** train1/train2 normal fit; train3 relation confirmation plus D0 calibration;
  train4 normal sanity; test1 INNER pilot; test2 held-out result unavailable.
- **Label ordering:** {state['data_governance']['label_access']}
- **Leakage finding:** {state['data_governance']['leakage_status']}

## CANDIDATE DISCOVERY FOUNDATION

- **Universe:** {state['candidate_discovery']['candidate_universe']}.
- **META:** reviewed metadata domain-prior candidate ranking.
- **STAT:** normal train1/train2 directional lagged-association candidate ranking.
- **GDN:** embedding-cosine learned-graph candidate ranking; attention is internal message passing, not final evidence; post-hoc XAI is absent.
- **Union:** {state['candidate_discovery']['union']}.
- **Boundary:** {state['candidate_discovery']['warning']}

## RULE CONSTRUCTION FOUNDATION

- **Evidence view:** {state['rule_construction_authority']['evidence_view']}.
- **Withheld:** {state['rule_construction_authority']['withheld']}.
- **Lifecycle:** {state['rule_construction_authority']['lifecycle']}.
- **Agentic boundary:** {state['rule_construction_authority']['agentic_claim']}

## FROZEN D1 RUNTIME / TRACE FOUNDATION

- **Authority:** {state['runtime_trace_explanation']['authority']}
- **Evaluation:** {state['runtime_trace_explanation']['evaluator']}
- **Prediction:** {state['runtime_trace_explanation']['prediction']}
- **Freeze / labels:** {state['runtime_trace_explanation']['label_access']}
- **Trace:** {state['runtime_trace_explanation']['canonical_trace_relationship']}
- **Explanation:** {state['runtime_trace_explanation']['explanation']}

## WHAT WAS EXECUTED

- All three discovery arms produced evidence-reviewed top-20 rankings.
- Profiling produced 23 pair contexts and 42 frozen directed relations.
- T0, T1, T1-B, and T2 executed; their accepted counts were 42, 42, 42, and 39.
- Frozen integrity-audited INNER results exist for D0, D1, D2 V1, and D2 V2.
- The OUTER bridge produced a blocker record only; it produced no scientific outcome.

## WHAT WAS OBSERVED

- D0: {pilot['d0']}
- D1: {pilot['d1']}
- Event overlap: {pilot['overlap']}.
- D2 V1: {pilot['d2_v1']}.
- D2 V2: {pilot['d2_v2']}.
- T2 feedback actions: zero; the current cohort did not exercise feedback recovery.

These are frozen observations from 14 independent INNER attack events. They are pilot
evidence only and are not validated performance conclusions.

## WHAT IS VALIDATED

The narrow implementation statements are supported: deterministic authority controls exist;
normal-data evidence can be transformed into bounded executable rules; the verifier checks
structural, evidence, parameter, split, and operational contracts; and the current fixed-rule
runtime is LLM-free and deterministic given frozen authorities. Integrity audits validate
artifact custody and arithmetic, not generalization, superiority, causality, or human usefulness.

## WHAT REMAINS UNKNOWN

{_md_bullets(state['current_unvalidated'])}

## Current highest-priority work

{_md_bullets(state['top_priorities'])}

Exact next management task: **{state['recommended_next_management_task']}**
Following architecture task: **{state['recommended_next_architecture_task']}**
"""


def render_my_todo(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    grouped: dict[str, list[Mapping[str, str]]] = {}
    for item in state["user_todo_items"]:
        grouped.setdefault(item["category"], []).append(item)
    headings = ("DECISION NEEDED", "UNDERSTANDING NEEDED", "REVIEW NEEDED", "WAITING ON CODEX")
    sections: list[str] = []
    for heading in headings:
        items = grouped.get(heading, [])
        body = "\n\n".join(
            f"- **ID:** {item['id']}\n  **Priority:** {item['priority']}\n  **Task:** {item['task']}\n  **Why your involvement is required:** {item['why']}\n  **Linked:** {item['linked']}\n  **Status:** {item['status']}"
            for item in items
        ) or "No items."
        sections.append(f"## {heading.title()}\n\n{body}")
    return f"""{_markdown_marker(state, digest)}
# My Research TODO

This page contains research-owner actions, not low-level development chores.

{chr(10).join(sections)}

Scientific authority: `{state['scientific_authority']['commit']}`
"""


def render_decision_inbox(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    unresolved = [row for row in data["decisions"] if row["status"] == "OPEN"]
    body = "\n\n".join(
        f"## {row['decision_id']} — {row['title']}\n\n{row['decision']}\n\nReason: {row['reason']}"
        for row in unresolved
    ) or "There are no unresolved user decisions. RCC-000 decisions 001 and 002 remain approved in `registry/decisions.csv`."
    return f"""{_markdown_marker(state, digest)}
# Decision Inbox

{body}

Scientific authority: `{state['scientific_authority']['commit']}`
"""


def render_user_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    pilot = state["pilot_observations"]
    top_risks = [row["description"] for row in data["risks"] if row["severity"] in {"CRITICAL", "HIGH"}][:5]
    return f"""{_markdown_marker(state, digest)}
# 지금 연구는 어디까지 왔나

## 한 문장 상태

HAI 23.05 P1을 대상으로 한 전체 INNER 연구 경로는 구현되고 예비 실행 및 무결성
감사까지 끝났지만, 과학적 가설 검증·홀드아웃 일반화·새 컴퓨터 재현은 아직 끝나지 않았다.

## 상태 라벨 읽는 법

- **구현됨 / 실행됨**은 엔지니어링 상태다. 성능 검증을 뜻하지 않는다.
- **Evidence-reviewed**는 소스나 공개 증거 상태를 고정 권한과 대조했다는 뜻이다.
  과학적 성능을 감사하거나 검증했다는 뜻이 아니다.
- **Result-integrity audited**는 명시된 고정 결과의 보관·불변성·순서·산술을 확인했다는
  뜻이다. 우수성이나 일반화를 입증하지 않는다.
- **Independently reproduced**는 필요한 환경과 custody에서 독립 재현했다는 별도 상태다.
- 과학적 주장의 허용 범위는 오직 `claims.csv`가 결정한다. 구성요소의 호환용
  `claim_ready` 필드는 좁은 구현·계약 문구만 지원하며 과학적 성능 검증을 뜻하지 않는다.

이 숫자들은 하나의 연구 완료율이 아니다.

## 이미 만들어진 것

데이터 출처와 분할 통제에서 시작해 META·STAT·GDN 후보 탐색, 관계 프로파일링,
normal-only 수치 권한, 규칙 생성, 결정론적 검증기, COMMON-42 고정 규칙, LLM 없는
고정 규칙 런타임, D0/D1/D2 평가와 결과 무결성 감사까지 이어지는 구조가 있다.

## 실제 실행된 것

- 144개 가능한 관계에서 META·STAT·GDN이 각각 top-20을 만들었고 합집합은 47개였다.
- 23개 pair context에서 42개 방향성 시간 관계가 확인되어 COMMON-42로 고정되었다.
- T0/T1/T1-B/T2 규칙 생성 경로가 모두 실행되었고 승인 수는 42/42/42/39였다.
- D0, D1, D2 V1, D2 V2의 INNER 결과가 고정되고 독립 무결성 감사를 받았다.
- OUTER는 실행 결과가 아니라 차단 기록만 있다.

## 현재 관찰된 결과

- D0: {pilot['d0']}.
- D1: {pilot['d1']}.
- 두 신호의 사건 겹침: {pilot['overlap']}.
- D2 V1: {pilot['d2_v1']}.
- D2 V2: {pilot['d2_v2']}.

이 수치는 독립 공격 사건 14개의 INNER 예비 관찰이다. 검증된 일반 성능으로 표현하면 안 된다.

## 아직 증명되지 않은 것

{_md_bullets(state['current_unvalidated'])}

특히 GDN의 고유 기여와 Agentic 피드백의 이점은 아직 가설이다. 현재 T2에서는 피드백
행동이 0회였으므로 Agentic 장점이 실험된 것으로 볼 수 없다. D1은 D0와 다른 사건에
반응했지만 정상 FAR가 높아 실용성을 주장할 수 없다. 현재 D2 정책도 개선 주장을 지지하지 않는다.

## 가장 큰 위험 5개

{_md_bullets(top_risks)}

## 다음에 해야 할 것

{_md_bullets(state['top_priorities'])}

관리 작업의 다음 단계는 **{state['recommended_next_management_task']}** 이고, 이후 전체
구조 검토는 **{state['recommended_next_architecture_task']}** 이다. 둘 다 사용자 승인 전에
자동으로 시작하지 않는다.

## 내가 직접 확인할 것

{_md_bullets(state['top_user_todo'])}

Scientific authority: `{state['scientific_authority']['commit']}`
"""


def render_project_timeline(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    phase_sections = []
    for index, phase in enumerate(data["history"]["phases"], start=1):
        phase_sections.append(
            f"""## {index}. {phase['title']}

**Period:** {phase['period']} (`{phase['date_precision']}`)

**Source class:** `{phase['source_class']}`

**Status:** `{phase['status']}` · **Confidence:** `{phase['confidence']}`

### Goal at the time

{phase['goal']}

### What was implemented / investigated

{phase['investigated']}

### What problem was found

{phase['problem']}

### Decision

{phase['decision']}

### What survived into the current method

{phase['survived']}

### What was abandoned or deferred

{phase['abandoned_or_deferred']}

### Evidence

{phase['evidence']}
"""
        )
    return f"""{_markdown_marker(state, digest)}
# Research Evolution

Scientific authority: `{state['scientific_authority']['commit']}`

This narrative explains why the architecture changed. It is not a replacement for
`registry/current_state.yaml` or `registry/claims.csv`. Early user-context stages keep
their approximate dates and confidence labels; later Git milestones use exact evidence.

{chr(10).join(phase_sections)}

## Current State

The architecture is substantially implemented and the INNER path has frozen pilot
observations. Scientific validation remains partial, held-out generalization remains
unconfirmed, and fresh-machine reproduction remains incomplete. The exact next task is
**{state['exact_next_task']}**.
"""


def render_professor_feedback_lineage(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    rows = "\n".join(
        f"| {item['date']} ({item['date_precision']}) | {item['feedback']} | {item['interpretation']} | {item['decision_ref']} | {item['effect']} | {item['classification']} / {item['confidence']} |"
        for item in data["history"]["professor_feedback_lineage"]
    )
    return f"""{_markdown_marker(state, digest)}
# Professor Feedback Lineage

Scientific authority: `{state['scientific_authority']['commit']}`

This is a decision lineage, not an email archive. Dates describe the evidence basis shown
in the final column. Retrospective response matrices do not create contemporaneous proof.

| Date | Professor feedback or record | Research interpretation | Decision | Implementation / experiment effect | Evidence class |
|---|---|---|---|---|---|
{rows}

## Temporal safeguards

- The pairwise continuous-step protocol was frozen on **2026-08-03**. The user-context
  2026-08-04 feedback may have reinforced or clarified pairwise-first scope; it did not
  originate the already-frozen protocol.
- **2026-08-18** is an internal progress update, not professor feedback.
- **2026-08-24** is the Git-supported professor-package preparation milestone, not proof
  of professor approval.
- **2026-08-26** is integrated report preparation in user context, not automatically new
  professor feedback.
"""


def render_superseded_directions(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    rows = "\n".join(
        f"| {item['direction']} | {item['period']} | {item['why_explored']} | {item['why_reduced']} | {item['survived']} | {item['replacement']} | {item['status']} | {'Yes' if not item['current_claim'] else 'No'} |"
        for item in data["history"]["superseded_directions"]
    )
    return f"""{_markdown_marker(state, digest)}
# Superseded and Conditional Directions

Scientific authority: `{state['scientific_authority']['commit']}`

Old documents may use these framings. Preserve them historically; do not reuse them as
current claims without current evidence.

| Direction | Period | Why explored | Why reduced or abandoned | What survived | Replacement | Status | Do not use as current claim? |
|---|---|---|---|---|---|---|---|
{rows}
"""


def render_terminology_guide(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    rows = "\n".join(
        f"| {item['term']} | {item['historical']} | {item['current']} | {item['deprecated']} |"
        for item in data["history"]["terminology"]
    )
    return f"""{_markdown_marker(state, digest)}
# Historical Terminology Guide

Scientific authority: `{state['scientific_authority']['commit']}`

| Term | Historical meaning | Current preferred meaning | Deprecated or guarded wording |
|---|---|---|---|
{rows}

Historical documents remain untouched. This guide controls current-facing interpretation.
"""


def render_history_confirmation(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    questions = []
    for item in data["history"]["confirmation_questions"]:
        questions.append(
            f"""## {item['id']}

**Question:** {item['question']}

**Why it matters:** {item['why']}

**Evidence found:** {item['evidence']}

**Suggested interpretation:** {item['suggested']}

**Confidence:** `{item['confidence']}`
"""
        )
    return f"""{_markdown_marker(state, digest)}
# History Confirmation Needed

Only high-value uncertainties are listed. Until confirmed, the conservative interpretation
in each item remains the RCC history boundary.

{chr(10).join(questions).rstrip()}
"""


def render_decision_record(row: Mapping[str, str], state: Mapping[str, Any], digest: str) -> str:
    return f"""{_markdown_marker(state, digest)}
# {row['decision_id']} — {row['title']}

## Date

{row['date']} (`{row['date_precision']}`)

## Status

`{row['status']}`

## Context

{row['context']}

## Alternatives Considered

{_md_bullets(row['alternatives_considered'].split(';'))}

## Decision

{row['decision']}

## Why

{row['reason']}

## Consequence

{row['consequence']}

## Current Relevance

{row['current_relevance']}

## Supersedes

{row['supersedes']}

## Superseded By

{row['superseded_by']}

## Evidence

Source class: `{row['source']}`

Reference: {row['source_ref']}

Source commit: `{row['source_commit']}`

## Confidence

`{row['confidence']}`
"""


def render_rcc003_history_summary(data: Mapping[str, Any], digest: str) -> str:
    state = data["state"]
    inheritance = data["history"]["current_method_inheritance"]
    return f"""{_markdown_marker(state, digest)}
# 우리 연구가 어떻게 여기까지 왔나

## 처음 무엇을 하려 했는가

사용자 기록에 따르면 2025년 말부터 DHAG 확장과 PoC를 검토했고, 2026년 봄에는
ARGOS·LLMAD 같은 관련 연구와 설명 충실도 검증 중심의 방향을 탐색했다. 이 초기
시기는 Git에 동시대 기록이 충분하지 않으므로 정확한 실패 원인이나 날짜를 확정하지
않는다.

## 왜 방향이 바뀌었는가

자유로운 LLM 규칙이나 설명을 과학적 권한으로 쓰면 변수·숫자·검증·실행의 책임이
불명확해진다. 7월의 저장소 기록은 ARGOS를 그대로 복제하기보다 유용한 요소만 남기고,
규칙 구조·수치 근거·검증·런타임을 분리하는 CPS 관계 규칙 방향을 보여 준다. HAI에서
기존 이산 제어원 가정이 실패했을 때도 기준을 완화하지 않고 연속 step-response 계열을
새로 사전등록했으며, 그 결과 P1만 선택되었다.

## 지금 방법에 남은 핵심 아이디어

- DHAG 시기: {inheritance['from_dhag']}
- ARGOS 탐색: {inheritance['from_argos']}
- Verifier 시기: {inheritance['from_verifier']}
- 교수님 피드백 재정리: {inheritance['from_professor_reframing']}
- 현재 조합: {inheritance['current_combination']}

## 버린 것 / 보류한 것

현재 핵심에서 제외된 것은 DHAG를 전면 방법으로 삼는 주장, Faithfulness Verifier가
과학적 진실을 증명한다는 주장, ARGOS의 직접 복제, HAI 이산 제어원 경로, 그리고
ARTIST식 학습 기반 segment 선택이다. 복잡한 관계와 runtime LLM은 틀렸다고 판정한
것이 아니라 별도 설계가 필요한 조건부 과제로 남아 있다.

## 교수님 피드백이 실제로 바꾼 것

2026-08-04 피드백은 사용자 기록으로 보존한다. pairwise-first 프로토콜은 이미
8월 3일 고정되어 있었으므로 이 피드백은 그 기원을 만든 사건이라기보다 범위와 표현을
강화한 것으로 기록한다. Rule-only를 fusion 안에 숨기지 않고 별도로 보며, verifier와
GDN과 agent라는 단어를 좁게 쓰고, 실행과 검증을 구분하는 방향이 이후 구현에 남았다.
8월 18일은 내부 진행 업데이트이고, 8월 26일은 통합 보고서 준비이지 새 교수님 피드백이 아니다.

## 현재 위치

HAI 23.05 P1에서 후보 탐색, normal-only 관계·수치 근거, COMMON-42, 고정 규칙 런타임,
D0/D1/D2 INNER 예비 평가와 결과 무결성 감사까지 구현되었다. 그러나 14개 사건 수치는
pilot evidence일 뿐이다. Rule-only 실용성, D2 개선, GDN 고유 기여, Agentic 이점,
사람 대상 설명 유용성, 홀드아웃 일반화는 아직 검증되지 않았다.

## 앞으로는 무엇을 검증해야 하는가

새 독립 사전등록 아래 더 많은 사건과 더 강한 다변량 탐지기 기준선으로 Rule-only와
detector 비교를 확장해야 한다. GDN 안정성과 고유 기여, 실제 피드백이 발생하는 T2 비교,
fresh-machine 재현도 별도로 검증해야 한다. 다음 관리 작업은 **{state['exact_next_task']}**이다.
"""


def generate_history_documents(rcc_root: Path, data: Mapping[str, Any], digest: str) -> list[Path]:
    history_dir = rcc_root / "history"
    decisions_dir = history_dir / "decisions"
    history_dir.mkdir(parents=True, exist_ok=True)
    decisions_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        history_dir / "PROJECT_TIMELINE.md": render_project_timeline(data, digest),
        history_dir / "PROFESSOR_FEEDBACK_LINEAGE.md": render_professor_feedback_lineage(data, digest),
        history_dir / "SUPERSEDED_DIRECTIONS.md": render_superseded_directions(data, digest),
        history_dir / "TERMINOLOGY_GUIDE.md": render_terminology_guide(data, digest),
        history_dir / "HISTORY_CONFIRMATION_NEEDED.md": render_history_confirmation(data, digest),
    }
    for row in data["decisions"]:
        name = f"{row['decision_id']}-{_slug(row['title'])}.md"
        payloads[decisions_dir / name] = render_decision_record(row, data["state"], digest)
    for path, payload in payloads.items():
        path.write_text(payload, encoding="utf-8", newline="\n")
    return list(payloads)


def build_dashboard(rcc_root: Path) -> Path:
    data = load_registry(rcc_root)
    digest = registry_digest(rcc_root)
    output = rcc_root / "dashboard" / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_dashboard(data, digest), encoding="utf-8", newline="\n")
    return output


def generate_summaries(rcc_root: Path) -> list[Path]:
    data = load_registry(rcc_root)
    digest = registry_digest(rcc_root)
    generated = rcc_root / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    outputs = {
        "GPT_BRIEF.md": render_gpt_brief(data, digest),
        "CURRENT_STATUS.md": render_current_status(data, digest),
        "CHANGE_SUMMARY.md": render_change_summary(data, digest),
        "RCC_002_USER_SUMMARY.md": render_user_summary(data, digest),
        "RCC_003_HISTORY_SUMMARY.md": render_rcc003_history_summary(data, digest),
        "ARCH_001_USER_SUMMARY.md": render_arch001_user_summary(data, digest),
        "ARCH_002_USER_SUMMARY.md": render_arch002_user_summary(data, digest),
        "ARCH_003_USER_SUMMARY.md": render_arch003_user_summary(data, digest),
        "ARCH_004_USER_SUMMARY.md": render_arch004_user_summary(data, digest),
        "ARCH_005_USER_SUMMARY.md": render_arch005_user_summary(data, digest),
        "ARCH_006_USER_SUMMARY.md": render_arch006_user_summary(data, digest),
        "ARCH_007_USER_SUMMARY.md": render_arch007_user_summary(data, digest),
    }
    paths: list[Path] = []
    for name, payload in outputs.items():
        path = generated / name
        path.write_text(payload, encoding="utf-8", newline="\n")
        paths.append(path)
    navigation_outputs = {
        "CURRENT_CONTEXT.md": render_current_context(data, digest),
        "MY_TODO.md": render_my_todo(data, digest),
        "DECISION_INBOX.md": render_decision_inbox(data, digest),
    }
    for name, payload in navigation_outputs.items():
        path = rcc_root / name
        path.write_text(payload, encoding="utf-8", newline="\n")
        paths.append(path)
    paths.extend(generate_history_documents(rcc_root, data, digest))
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rcc-root", type=Path, default=default_rcc_root())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dashboard-only", action="store_true")
    mode.add_argument("--summaries-only", action="store_true")
    args = parser.parse_args(argv)
    root = args.rcc_root.resolve()

    written: list[Path] = []
    if not args.summaries_only:
        written.append(build_dashboard(root))
    if not args.dashboard_only:
        written.extend(generate_summaries(root))
    for path in written:
        print(path.relative_to(root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
