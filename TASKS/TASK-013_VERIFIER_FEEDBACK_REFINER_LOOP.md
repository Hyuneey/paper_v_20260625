---
id: TASK-013
title: Implement bounded verifier-feedback LLM rule refinement loop
status: blocked
depends_on: [TASK-012]
phase_gate: Phase Gate C
suggested_branch: task-013-agentic-refiner-loop
---

# TASK-013: Verifier-Feedback Rule Refiner Loop

## 1. Goal

Implement a bounded training-time loop in which structured deterministic verifier feedback is supplied to an LLM refiner, revised DSL rules are re-verified, and the complete revision history is retained without exposing raw data or allowing numeric/variable mutation.

## 2. Loop

```text
aggregate Evidence Pack
→ LLM Planner
→ Candidate DSL Rule
→ Deterministic Verifier
→ Pass: library candidate
→ Fail: structured feedback
→ LLM Refiner
→ Revised DSL Rule
→ Verifier
```

Use microsoft/ARGOS as a reference for the planner–repair–review workflow.

Do not reproduce:

- univariate dataset assumptions,
- execution of arbitrary LLM-generated Python,
- evaluation on sealed test data during rule construction,
- provider-specific Azure OpenAI coupling.

LLM output must conform to the project's JSON DSL schema and be evaluated
only by the deterministic rule engine.

## 3. Inputs

- initial planner result,
- evidence pack,
- Rule Schema Registry,
- structured verifier report,
- approved refinement policy,
- provider configuration.

No final test data or raw time-series rows may enter the loop.

## 4. Termination conditions

- verifier pass,
- maximum refinement count,
- repeated identical semantic rule,
- no improvement in check outcomes,
- unsupported relation profile,
- non-recoverable verifier code,
- provider failure threshold.

## 5. Refinement permissions

Allowed:

- choose another supplied rule family when approved,
- add or remove allowed conditions using supplied variables,
- simplify a rule,
- respond to structured verifier feedback.

Forbidden:

- add variables,
- change calibrated values,
- create new numeric values,
- use unsupported predicates,
- execute or return Python,
- access test information.

## 6. Required outputs

- revision-session artifact,
- every rule version,
- every verifier report,
- prompt/model versions and hashes,
- termination reason,
- final status,
- redaction status,
- comparison-ready metadata.

Raw provider responses may be retained only under approved local policy and must never contain raw SWaT data. Git-tracked artifacts should store hashes and redacted structured outputs.

## 7. Deterministic-control policy

- Verifier remains authoritative.
- Free-text feedback is never used by deterministic logic.
- Numeric and variable integrity are checked after every iteration.
- The loop must be bounded.
- Same mocked provider sequence must reproduce the same history.

## 8. Acceptance criteria

1. A recoverable mocked failure can be refined to pass.
2. Numeric mutation is rejected.
3. Variable addition is rejected.
4. Executable-code payload is rejected.
5. Infinite-loop prevention is tested.
6. Revision history is complete and ordered.
7. No raw restricted data enters prompts or tracked outputs.
8. Template, one-shot LLM, and feedback-loop results share common artifact schemas.

## 9. Required tests

- successful refinement,
- non-recoverable failure,
- repeated-rule termination,
- max-iteration termination,
- no-improvement termination,
- prohibited variable addition,
- prohibited numeric change,
- code-payload rejection,
- redaction test,
- deterministic mocked history,
- no-test-role guard.

## 10. Phase Gate C report

Produce a focused comparison:

```text
Template-only
vs
One-shot LLM
vs
LLM + verifier feedback
```

Do not claim LLM value without evidence. Report cost, failure rate, verification pass rate, rule complexity, and explanation quality where available.
