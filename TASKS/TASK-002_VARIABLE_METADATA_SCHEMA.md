---
id: TASK-002
title: Implement provenance-aware variable metadata schema
status: blocked
depends_on: [TASK-001]
phase_gate: Milestone 1
suggested_branch: task-002-metadata-schema
---

# TASK-002: Variable Metadata Schema

## 1. Goal

Implement a validated, versioned metadata schema for SWaT variables without hard-coding individual relation pairs. Record how every metadata field was obtained and whether it has been human-reviewed.

## 2. Architecture context

Metadata supports candidate-universe policies, pair-type constraints, profiling, explanations, and verifier type checks. Human input defines the schema and general policies, not final variable pairs or rules.

## 3. Required fields

```text
name
role: sensor | actuator | unknown
value_type: continuous | binary | categorical | unknown
physical_type: valve | pump | flow | level | pressure | quality | other | unknown
subsystem: optional
stage: optional
unit: optional
allowed_states: optional
source_reference: optional
source_method: dataset_documentation | name_pattern | manual_review | inferred | unknown
confidence: optional
review_status: unreviewed | reviewed | rejected
schema_version
```

## 4. Required outputs

- typed metadata model,
- loader and validator,
- duplicate and invalid-type checks,
- metadata coverage report,
- provenance and review-status report,
- example metadata template with synthetic names,
- project-local metadata file format,
- documentation.

## 5. In scope

- schema and serialization,
- explicit `unknown` handling,
- name-pattern parser as a suggestion mechanism,
- source provenance,
- human-review workflow,
- synthetic fixtures.

## 6. Out of scope

- manual final relation-pair definition,
- inference from attack labels,
- causal claims,
- rule generation,
- silent conversion of inferred metadata into reviewed ground truth.

## 7. Required interfaces

```python
@dataclass(frozen=True)
class VariableMetadata:
    name: str
    role: VariableRole
    value_type: ValueType
    physical_type: PhysicalType
    subsystem: str | None
    stage: str | None
    unit: str | None
    allowed_states: tuple[str, ...] | None
    source_method: MetadataSourceMethod
    source_reference: str | None
    confidence: float | None
    review_status: ReviewStatus
    schema_version: str
```

## 8. Research constraints

- Do not use test attacks to infer metadata.
- Do not use metadata provenance as proof of causal relation.
- Metadata inferred from names must remain labeled `inferred` or `unreviewed` until reviewed.
- Do not hard-code relation pairs in metadata.

## 9. Acceptance criteria

1. All dataset feature names are represented exactly once.
2. Unknown fields are allowed but reported.
3. Invalid role/value-type combinations produce actionable errors.
4. Metadata source and review status survive round trips.
5. Coverage report separates documented, inferred, reviewed, and unknown fields.
6. No real SWaT rows are used in tests.

## 10. Required tests

- round trip,
- duplicate-name rejection,
- invalid enum/type test,
- unknown-value handling,
- inferred-versus-reviewed provenance,
- coverage report correctness,
- feature-list mismatch test.

## 11. Stop conditions

Stop if the approved metadata source or human-review policy is undefined and the next task depends on it.
