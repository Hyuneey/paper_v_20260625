# RCC Registry Contract

Registry version: `0.1.0`
Schema version: `rcc-registry-v1`
Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

RCC-002 populates the current 32-component inventory, six-experiment plan,
conservative claim boundary, ten principal risks, and all 26 RCC-000 artifact
inventory entries.

RCC-003 adds a separate historical layer: 15–30 curated milestone events,
10–20 consequential decisions, major method phases, professor-feedback lineage,
superseded directions, terminology safeguards, and a small user-confirmation
queue. Historical records explain current architecture; they never overwrite
RCC-002 current state or promote a claim in `claims.csv`.

## Serialization

- CSV files use UTF-8, LF, RFC 4180 quoting, and their exact frozen headers.
- Multi-value cells use semicolons. `NONE` is the only null sentinel.
- Booleans are lowercase `true` or `false`.
- IDs match `^[A-Z][A-Z0-9_-]*$` and are unique within a registry.
- Registry values may not start with spreadsheet formula markers `=`, `+`, or
  `@`. Generated HTML escapes every registry value.
- `current_state.yaml` is a JSON-compatible YAML 1.2 document so the RCC has no
  PyYAML dependency.
- `history.yaml` is the JSON-compatible historical narrative registry used to
  generate full history views and decision records.
- `top_priorities` holds exactly three scientific priorities;
  `user_todo_items` holds structured user actions; and `top_user_todo` holds
  exactly three research-owner review actions for the dashboard and handoff.

## Two-axis status model

RCC status is not one linear lifecycle and must never be converted to a single
completion percentage.

**Implementation / engineering state** describes whether a component is
designed, present in code, integrated, or used in an execution path:

`DESIGN_COMPLETE`, `CODE_IMPLEMENTED`, `INTEGRATED`, `EXECUTED`.

**Scientific evidence state** describes what kind of evidence exists:

`SOURCE_EVIDENCE_REVIEWED`, `RESULT_INTEGRITY_AUDITED`,
`INDEPENDENTLY_REPRODUCED`, `SCIENTIFICALLY_VALIDATED`.

These axes are independent. A governance or documentation component can have
its source evidence reviewed without being a scientific executable. Code
existing does not mean it ran; execution does not mean performance validation;
result-integrity audit does not mean independent reproduction; and reproduction
does not automatically establish a broad scientific claim.

### Backward-compatible component fields

- `audited=true` means the component's source or evidence status was reviewed
  against the pinned authority. In the dashboard this is called
  **Evidence-reviewed**. It does not mean a scientific result was audited and
  does not validate performance. This is why the evidence-reviewed count may
  exceed the executed count.
- A **Result-integrity audit** exists only when an explicit result-specific
  integrity artifact is registered. It checks custody, immutability, access
  ordering, and metric arithmetic. It does not establish superiority,
  generalization, or scientific performance validity.
- `reproduced=true` means an independent reproduction was completed under its
  required environment and custody. Source review and integrity audit are not
  reproduction.
- `claim_ready=true` is retained for schema compatibility. It means only that
  the component supports at least one allowable narrow implementation or
  contract claim. It is not shown as a component headline and never means that
  the component's scientific performance is validated.
- `claims.csv` is the sole authoritative scientific claim view. A scientific
  claim's status must not be inferred from component `status`, `audited`, or
  `claim_ready` fields.

Component `status` values:

`IMPLEMENTED_EXECUTED_AUDITED`, `IMPLEMENTED_EXECUTED`,
`IMPLEMENTED_NOT_EXECUTED`, `RESEARCH_ONLY`, `DESIGN_ONLY`, `PARTIAL`,
`BLOCKED`, `LEGACY_OR_SUPERSEDED`, `UNKNOWN`.

Experiment `status` values:

`NOT_STARTED`, `DESIGN_ONLY`, `IMPLEMENTED_NOT_EXECUTED`,
`EXECUTED_NOT_AUDITED`, `EXECUTED_AUDITED_PILOT`, `BLOCKED`, `SUPERSEDED`,
`UNKNOWN`.

Claim `status` values:

`SUPPORTED_IMPLEMENTATION`, `PILOT_ONLY`, `UNVALIDATED`, `NOT_SUPPORTED`,
`CONDITIONAL`, `SUPERSEDED`.

Timeline `status` values:

`ACTIVE_CONTEXT`, `HISTORICAL`, `SUPERSEDED`, `ABANDONED`, `CONDITIONAL`.

Decision `status` values:

`ACTIVE`, `SUPERSEDED`, `ABANDONED`, `CONDITIONAL`, `OPEN`.

Historical date precision is explicit: `DAY`, `MONTH`, `RANGE`, or
`APPROXIMATE`. A range or month may not be rewritten as an exact day. A
`USER_CONTEXT` source must not claim a Git commit and must carry conservative
confidence. Later retrospective documents may interpret an event but do not
replace contemporaneous evidence.

Risk severity is `CRITICAL|HIGH|MEDIUM|LOW`; likelihood is
`HIGH|MEDIUM|LOW|UNKNOWN`; risk status is
`OPEN|MITIGATING|ACCEPTED|CLOSED`.

## Required schemas

- `components.csv`: all task-specified fields plus `lifecycle_stage`.
- `experiments.csv`: all task-specified fields plus authority, component, and
  artifact bindings.
- `claims.csv`: all task-specified fields plus authority and experiment
  bindings.
- `risks.csv`: all task-specified fields plus authority bindings.
- `artifacts.csv`: public-safe artifacts and symbolic private-custody identities.
- `decisions.csv`: context, alternatives, consequence, current relevance,
  reciprocal supersession, source class/ref/commit, confidence, and approval.
- `timeline.csv`: date precision, event class, source class/ref/commit,
  component and decision references, status, supersession, and evidence notes.
- `history.yaml`: major phases, professor lineage, superseded directions,
  terminology, confirmation questions, dashboard curation, and zero safety counters.

Every header is required. Human-readable cells must not be empty. The permitted
`NONE` fields are documented by the validator and include absent representative
symbols/tests/artifacts, absent contradictory evidence, and decisions that do
not supersede another decision.

## References and paths

- `components.artifact_refs` resolves to `artifacts.artifact_id`.
- `risks.affected_component` and `decisions.affected_components` resolve to a
  component ID or the `PROJECT_WIDE` sentinel.
- Artifact producer/consumer fields resolve to component IDs or one of
  `PROJECT_GOVERNANCE`, `EXTERNAL_GIT`, or `RCC`.
- Typed references use `artifact:<id>`, `experiment:<id>`, or
  `component:<id>` and must resolve.
- Timeline component and decision references must resolve. Decision
  `supersedes` and `superseded_by` links are reciprocal.
- Public source paths are POSIX repository-relative paths. Drive paths, UNC paths,
  root paths, home expansion, environment expansion, backslashes, and `..` are
  rejected. Source paths are checked against the pinned Git tree, never the
  stale checkout.
- Documentation-overlay content cannot establish a scientific implementation
  or result claim.

Private artifacts use only the `PRIVATE` classification and one approved
symbolic custody identity. No raw data, private locations, private model values,
labels, scores, or hidden metric evidence belong in these registries.

## Historical source classes

- `GIT_*`, `SCIENTIFIC_AUTHORITY`, and frozen-report classes establish only the
  fact supported by their cited commit or report.
- `DOCUMENTATION_OVERLAY` supplies narrative context only.
- `USER_CONTEXT` preserves high-value history that Git does not independently
  prove. It must state date precision and confidence and may not be quoted as a
  repository-established fact.
- `LOCAL_RCC_GIT` records RCC governance milestones after the scientific pin;
  it cannot establish a scientific result.

The dashboard shows 8–12 curated milestones rather than every event. Full
history belongs in `history/PROJECT_TIMELINE.md`; old documents remain unchanged.
