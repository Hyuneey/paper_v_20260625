---
id: TASK-007
title: Implement safe minimal JSON/AST DSL and schema registry
status: blocked
depends_on: [TASK-006]
phase_gate: Milestone 4
suggested_branch: task-007-minimal-dsl
---

# TASK-007: Minimal DSL and Rule Schema Registry

## 1. Goal

Implement a versioned, structured, deterministic rule language for the initial binary-actuator → continuous-sensor relation without executing generated Python.

## 2. Architecture context

ARGOS demonstrates agent-generated rules but may execute generated Python. This project instead constrains both template and LLM outputs to a JSON/AST DSL that a deterministic evaluator interprets.

## 3. Initial predicates

- `changed_to`
- `increase_within`
- `response_missing`

The initial rule form should support:

```text
IF source changed from state A to state B
AND target did not increase by calibrated magnitude within calibrated delay
THEN anomaly
```

## 4. Required outputs

- versioned DSL schema,
- typed AST/model,
- parser/serializer,
- schema registry,
- pair-type compatibility rules,
- calibration-reference model,
- deterministic evaluator interface,
- human-readable formatter,
- documentation and examples using synthetic names.

## 5. Required rule properties

Every rule must include:

```text
rule_id
schema_version
source variable
target variable
relation type
trigger predicate
response predicate
calibration references
candidate pair artifact reference
metadata artifact reference
planner provenance
description template
```

## 6. Numeric parameter policy

- Numeric parameters must be resolved from a `CalibrationRecord` reference.
- The serialized rule may include a resolved value for runtime efficiency, but must also retain the calibration artifact ID and field name.
- Reject unreferenced numeric values unless they are fixed DSL constants explicitly approved in schema.

## 7. Safety policy

Prohibited everywhere:

- `exec`,
- `eval`,
- `compile`,
- dynamic imports,
- arbitrary Python expressions,
- shell commands,
- serialized callables,
- user-provided code blocks.

Only the deterministic evaluator may implement rule semantics.

## 8. Schema-registry role

The registry must serve both:

1. pre-generation constraints for template/LLM planners,
2. post-generation syntax/type validation for the verifier.

Initial compatibility:

```text
binary actuator -> continuous sensor:
  changed_to + increase_within / response_missing
```

## 9. Required interfaces

```python
class RuleSchemaRegistry:
    def allowed_families(self, source_meta, target_meta) -> tuple[str, ...]: ...
    def validate(self, rule: RuleAst) -> list[SchemaIssue]: ...

class RuleEvaluator(Protocol):
    def evaluate(self, rule: RuleAst, window: TimeSeriesWindow) -> RuleEvaluation: ...
```

## 10. Acceptance criteria

1. Valid rules round-trip deterministically.
2. Unsupported predicates are rejected.
3. Extra variables are rejected.
4. Unreferenced or mutated numeric parameters are rejected.
5. Type-incompatible predicates are rejected.
6. Rule evaluation uses no dynamic code execution.
7. Runtime can import evaluator/schema without LLM packages.
8. Human-readable explanation is derived from the AST, not free text.

## 11. Required tests

- valid round trip,
- schema-version handling,
- unsupported predicate,
- extra variable,
- missing calibration reference,
- numeric mutation,
- type mismatch,
- malicious code-like payload rejection,
- evaluator behavior on synthetic timelines,
- deterministic formatting.

## 12. Stop conditions

Stop if DSL semantics or calibration-reference rules require an unapproved choice.
