---
id: TASK-010
title: Implement LLM-free deterministic runtime rule engine
status: complete
depends_on: [TASK-009]
phase_gate: Milestone 4
suggested_branch: task-010-runtime-engine
---

# TASK-010: Runtime Rule Engine

## 1. Goal

Implement deterministic execution of a verified rule library on canonical rule-view time series and produce traceable alarm/explanation artifacts without any LLM or dynamic-code dependency.

## 2. Architecture context

Runtime reproducibility is a core contribution. Explanations must be derived from executed DSL rules and observed values, not generated post hoc by an LLM.

## 3. Inputs

- canonical rule-view stream or batch,
- verified rule library,
- metadata,
- calibration records,
- runtime config.

## 4. Required outputs

- point or interval firing records,
- aggregated rule score,
- alarm intervals,
- explanation artifacts,
- runtime provenance and performance statistics.

Example explanation fields:

```text
alarm_start
alarm_end
rule_id
variables
expected_relation
observed_violation
calibration_basis
candidate_provenance
source_view
sampling_period_seconds
```

## 5. Runtime constraints

- No LLM imports or calls.
- No dynamic code execution.
- Use only verified DSL rules.
- Use canonical high-resolution rule view.
- Runtime must validate schema and calibration references before execution.
- Explanation text must be deterministically formatted from rule AST and measured violation.

## 6. Aggregation scope

Initial implementation:

```text
S_rule(t) = max over fired rule severities or configured binary firing
```

Composite rule synthesis and detector fusion are out of scope for this ticket.

## 7. Required interface

```python
class RuntimeRuleEngine:
    def load_library(self, library: VerifiedRuleLibrary) -> None: ...
    def evaluate(self, data: TimeSeriesBatch) -> RuntimeEvaluation: ...
```

## 8. Data governance

- Local runtime artifacts may reference row/timestamp ranges, but Git-tracked reports must not contain reconstructive raw sequences.
- CI uses synthetic fixtures.
- Do not send runtime data to external services.

## 9. Acceptance criteria

1. Runtime package has no dependency on planning/LLM provider modules.
2. Verified rule produces expected synthetic alarm interval.
3. Explanation references exact rule and calibration provenance.
4. Malformed/unverified rules are rejected.
5. Same input/library yields identical output.
6. Time units respect the data-view manifest.
7. No arbitrary code path exists.

## 10. Required tests

- expected synthetic firing,
- non-firing normal case,
- multiple-rule aggregation,
- malformed library rejection,
- invalid calibration reference,
- wrong data-view rejection,
- deterministic explanation,
- import-boundary test proving no LLM dependency,
- malicious payload rejection.

## 11. Stop conditions

Stop if severity/aggregation semantics or alarm-interval merging policy requires an unapproved decision.

## 12. Completion notes

- Implemented LLM-free runtime engine under `src/paperworks/runtime/`.
- Added synthetic-smoke runtime policy in `configs/runtime/task010_synthetic_smoke.json`.
- Recorded DEC-013 to limit runtime severity and merge semantics to implementation smoke tests.
- Runtime validates verified libraries through `RuleSchemaRegistry` before execution.
- Runtime accepts canonical rule-view batches only.
- Runtime emits firing records, merged alarm intervals, deterministic explanations, aggregate score, and provenance statistics.
