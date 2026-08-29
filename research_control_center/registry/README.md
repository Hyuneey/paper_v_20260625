# RCC Registry Contract

Registry version: `0.1.0`
Schema version: `rcc-registry-v1`
Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

RCC-001 provides deliberately small seed registries. RCC-002 will populate the
broader project inventory after user review.

## Serialization

- CSV files use UTF-8, LF, RFC 4180 quoting, and their exact frozen headers.
- Multi-value cells use semicolons. `NONE` is the only null sentinel.
- Booleans are lowercase `true` or `false`.
- IDs match `^[A-Z][A-Z0-9_-]*$` and are unique within a registry.
- Registry values may not start with spreadsheet formula markers `=`, `+`, or
  `@`. Generated HTML escapes every registry value.
- `current_state.yaml` is a JSON-compatible YAML 1.2 document so the RCC has no
  PyYAML dependency.
- `highest_priority_work` holds the three current project priorities, while
  `top_user_todo` holds exactly three research-owner review actions for the
  dashboard and GPT handoff.

## Lifecycle model

The lifecycle is ordered but not interchangeable:

`DESIGN_COMPLETE → CODE_IMPLEMENTED → INTEGRATED → EXECUTED → AUDITED → REPRODUCED → CLAIM_READY`

Code existing does not mean it ran. Execution does not mean validation.
Validation does not mean generalization. Generalization does not automatically
make a thesis claim ready.

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
- `artifacts.csv`: exactly the public-safe artifact custody fields.
- `decisions.csv`: all task-specified fields plus source commit.
- `timeline.csv`: all task-specified fields plus source commit.

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
- Source paths are POSIX repository-relative paths. Drive paths, UNC paths,
  root paths, home expansion, environment expansion, backslashes, and `..` are
  rejected. Source paths are checked against the pinned Git tree, never the
  stale checkout.
- Documentation-overlay content cannot establish a scientific implementation
  or result claim.

All RCC-001 artifact seeds are `PUBLIC_SAFE`. No raw data, private locations,
private model values, labels, scores, or hidden metric evidence belong in these
registries.
