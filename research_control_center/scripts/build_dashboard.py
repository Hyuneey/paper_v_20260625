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
    return {
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
        '<div class="architecture-lane"><h3>' + _escape(lane["lane"]) + '</h3><div class="architecture-nodes">' + "".join(
            f'<a class="architecture-node {_badge_class(component_by_id[node]["status"])}" href="#components" title="{_escape(component_by_id[node]["status"])}">{_escape(component_by_id[node]["name"])}</a>'
            for node in lane["nodes"]
        ) + "</div></div>"
        for lane in state["architecture_overview"]
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
    <a href="#current-state">Current state</a><a href="#my-tasks">My tasks</a>
    <a href="#decisions">Decisions</a><a href="#architecture">Architecture</a>
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
      <div class="architecture-map">{architecture_markup}</div>
      <p>Node color follows the component registry. Open <code>../architecture/</code> for the future deep review; this is a high-level RCC view only.</p>
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
        f"- **{row['experiment_id']} · {row['name']}** — `{EXPERIMENT_STATUS_LABELS.get(row['status'], row['status'])}`. {row['current_evidence']}"
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

The architecture is implemented and pilot-operational. Scientific validation is partial,
held-out generalization is unconfirmed, and fresh-machine reproduction is incomplete.

## How to read RCC status

Implementation and engineering state is separate from scientific evidence state.
`audited=true` on a component is displayed as **Evidence-reviewed**: source or evidence
status was reviewed against the pinned authority. It is not a performance-validation flag.
An explicit **Result-integrity audit** checks custody, immutability, ordering, and arithmetic
for a named frozen result; it still does not establish scientific performance. Independent
reproduction is a separate state and remains absent at component level. Scientific claim
status comes only from `claims.csv`. The compatibility `claim_ready` field supports narrow
implementation or contract wording only and is not a scientific-validation state.

These counts are not a single completion percentage.

## Architecture in one line

{state['architecture_flow']}

## How we got here

The recorded evolution is **{phase_names}**. The first four stages are partly or wholly
`USER_CONTEXT`: Git does not independently prove their exact dates or motivations. The
repository-supported lineage begins on 2026-06-25 with graph-constrained candidates,
typed rules, a deterministic verifier, and an LLM-free runtime foundation. The July ARGOS
track was frozen as partial methodological support rather than copied wholesale. Its useful
ideas survived inside a project-owned CPS contract. HAI provenance and the failed discrete-
source gate then led to a separately preregistered continuous-step family and P1 selection.
META, STAT, and GDN remained distinct candidate-evidence arms; normal-only profiling and
numeric authority produced COMMON-42. D1, D0, and D2 were finally executed as a frozen
14-event INNER pilot. The OUTER attempt produced a custody blocker, not a scientific result.
History explains this lineage but cannot override RCC-002 current state or `claims.csv`.

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

Professor-driven priority is the scientific status of verified Rule-only behavior: it
showed distinct pilot event responses, but its high normal false-alarm burden prevents an
operational-utility claim. Expanded validation should preserve event-level metrics and
include at least one stronger multivariate detector baseline under a new preregistration.

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

{chr(10).join(questions)}
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
