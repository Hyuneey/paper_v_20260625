# ARGOS Agent Factorial Protocol

TASK-038A freezes a paper-aligned, leakage-corrected ARGOS component
reproduction. It starts from every one of the 96 TASK-037D one-shot rule slots
and creates four logical branches without generating a replacement Detection
rule.

| Branch | Initial executable rule | Initial runtime-failed rule |
|---|---|---|
| A0 | identity initial rule | terminal non-executable |
| A1 | identity initial rule | one Repair revision |
| A2 | inner Review trigger | Review not applicable |
| A3 | Repair identity, then inner Review trigger | shared Repair result, then inner Review trigger if executable |

This produces 384 branch records. The initial rule hash, detector variant, KPI,
FN/FP direction, and target/contrast lineage are immutable across all four
branches.

## Deduplication

One failed initial rule has one Repair request identity. A1 consumes that result
and A3 uses the same result as its Review input. A2 and A3 Review requests
remain separate branch transformations. An executable A1 branch is identity
and makes no Repair call.

## Revision limit

Repair and each Review branch receive at most one provider call. There is no
automatic retry, manual retry, replacement generation, or timeout-driven
revision loop. Invalid and harmful results remain visible as branch outcomes.

## Split roles

- Generation: Repair reproduction, error evidence, and post-repair runtime
  checks.
- Inner: Review trigger, regression evidence, branch diagnostics, and later
  branch-specific selection.
- Outer: prohibited in TASK-038A and allowed only after a committed selection
  freeze in a later task.
- Sealed test: prohibited.

TASK-038A creates no prompts containing real rules or rows, sends no provider
request, and executes no generated code.
