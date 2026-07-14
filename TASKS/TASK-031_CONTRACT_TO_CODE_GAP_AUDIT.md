# TASK-031: Contract-to-Code Gap Audit and MVP Migration Freeze

## Status

Completed as a static source audit and migration plan.

## Scope

- Inventory Phase 1 public interfaces through AST/source inspection.
- Map graph, evidence, parameter, DSL, verifier, runtime and explanation
  contracts.
- Freeze the delayed-response MVP and explicit migration policy.
- Audit the TASK-030 fixture validator without installing dependencies.
- Define a bounded, gated implementation sequence.

## Boundaries

No `src/paperworks` changes, dependency changes, dataset access, provider calls,
generated-code execution, ARGOS execution, experiment reruns, or performance
claims are permitted.

## Decision Outcome

- DEC-035: standard validator recommendation proposed, not installed.
- DEC-036: delayed-response MVP scope resolved and frozen.
- DEC-037: explicit deterministic legacy adapter recommended; silent conversion
  prohibited.

See `docs/task_reports/TASK-031_REPORT.md` and the method migration documents.
