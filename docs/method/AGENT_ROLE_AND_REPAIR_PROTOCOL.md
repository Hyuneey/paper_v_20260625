# Agent Role and Repair Protocol

## Evidence Curator

Input: approved graph candidates, event metadata, available train/calibration
references, and a pre-registered selection policy.

Output: evidence IDs, matched-normal IDs, source/target IDs, and candidate lag
range. It cannot output rules, numeric thresholds, or causal claims.

## Rule Planner

Input: graph edges, evidence records, relation-family registry, DSL schema, and
parameter-role registry.

Output: candidate DSL, parameter-role requests, and evidence-reference
justifications. It cannot emit Python, approve parameters, add variables, or
create relation families.

## Parameter Calibrator

This role is deterministic code, not an LLM. It consumes parameter requests,
evidence/normal references, and calibration policy, then returns a parameter
record, stability result, and uncertainty result.

## Rule Reviewer

Input: candidate DSL, structured verifier violations, approved evidence, and
approved parameter records.

Output: a revised candidate and field-level change summary. It may modify only
fields explicitly listed in `repairable_fields`. It cannot run rules, alter
immutable references or values, or override the verifier.

## Explanation Renderer

Input: accepted rule, runtime satisfaction trace, graph/evidence/parameter
provenance, and verifier result.

Output: machine-readable explanation and optional natural language. It cannot
change semantics, variables, thresholds, attribution, or claim status.

## Bounded repair loop

```text
candidate DSL
-> deterministic verifier
-> structured violations
-> bounded Rule Reviewer revision
-> deterministic verifier
```

Frozen policy:

- maximum repair iterations: 3;
- same-violation repeat limit: 1;
- terminate on no semantic change;
- complexity increase limit: at most 2 operator points per revision and never
  above the global schema budget;
- mutable fields: trigger, registered relation type, expected effect, lag/window
  structure, persistence, parameter references, output, severity, abstention;
- immutable fields: rule ID, schema/dataset versions, evidence/graph references,
  verified numeric values, final-test boundaries.

Termination states are `accepted`, `rejected_non_repairable`,
`rejected_max_iterations`, `rejected_repeated_violation`, and
`rejected_no_change`.

Repair feedback contains stable verifier codes and field paths. Python
tracebacks, arbitrary exceptions, raw rows, test metrics, and free-text LLM
self-approval are prohibited.
