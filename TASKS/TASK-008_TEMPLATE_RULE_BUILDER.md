---
id: TASK-008
title: Implement deterministic template rule builder
status: blocked
depends_on: [TASK-007]
phase_gate: Milestone 4
suggested_branch: task-008-template-rules
---

# TASK-008: Deterministic Template Rule Builder

## 1. Goal

Implement the non-LLM baseline that deterministically converts an approved evidence pack and schema-registry decision into a candidate DSL rule.

## 2. Architecture context

The template baseline must work before LLM integration. It provides the scientific control needed to determine whether an LLM adds value.

## 3. Inputs

- approved candidate pair,
- variable metadata,
- relation evidence pack,
- calibration records,
- Rule Schema Registry.

## 4. Required outputs

- candidate DSL rule,
- planner provenance `template`,
- selected rule family,
- referenced evidence/calibration fields,
- unsupported reason when no template applies.

## 5. Core behavior

For the initial relation:

```text
binary actuator -> continuous sensor
trigger = configured transition
normal profile supports positive response
calibration records exist
=> response_missing rule template
```

The builder must not contain specific SWaT variable names.

## 6. Required interface

```python
def build_template_rule(
    evidence: RelationEvidencePack,
    registry: RuleSchemaRegistry,
) -> TemplateRuleBuildResult: ...
```

## 7. Research constraints

- No LLM.
- No test data.
- No invented variables or numbers.
- Every numeric value references a calibration artifact.
- Unsupported profiles return explicit status.
- Do not infer causality.

## 8. Acceptance criteria

1. Same evidence produces byte-equivalent or semantically identical rule.
2. No hard-coded SWaT pair appears in library logic.
3. Unsupported relation type is rejected cleanly.
4. Missing calibration prevents rule generation.
5. Generated rule passes the DSL schema validator.
6. Planner provenance and evidence references are complete.

## 9. Required tests

- successful template build,
- missing calibration,
- unsupported pair type,
- metadata type mismatch,
- deterministic output,
- numeric provenance,
- no-test-role guard.

## 10. Stop conditions

Stop if a new rule family is needed beyond the approved minimal DSL.
