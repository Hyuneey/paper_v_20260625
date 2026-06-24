---
id: TASK-XXX
title: Replace with a narrow, testable task
status: draft
depends_on: []
phase_gate: null
suggested_branch: task-xxx-short-name
---

# TASK-XXX: Title

## 1. Goal

State one concrete, observable result.

## 2. Architecture context

Explain where this task sits in the research pipeline and why it is needed.

## 3. Preconditions

- dependency tickets,
- approved decisions,
- local data availability,
- required upstream revisions.

## 4. Inputs

List files, schemas, configs, upstream artifacts, and permitted split roles.

## 5. Required outputs

List code, APIs, artifacts, reports, and documentation.

## 6. In scope

- item 1,
- item 2.

## 7. Out of scope

- item 1,
- item 2.

## 8. Required interfaces and schemas

Provide exact or proposed signatures and fields.

## 9. Data-governance requirements

State whether the task touches SWaT. If yes:

- use `SWAT_DATA_ROOT`,
- do not copy raw data into Git,
- do not commit real rows/windows,
- state which data view and split role are permitted,
- state required manifest/fingerprint fields.

## 10. Upstream-reference requirements

State whether ARGOS or GDN code is referenced, adapted, or copied. Include pinned revision and license obligations.

## 11. Research constraints

Restate task-relevant invariants:

- no test leakage,
- no causal claim,
- no numeric hallucination,
- no generated-code execution,
- runtime LLM-free where applicable.

## 12. Acceptance criteria

1. Objective criterion.
2. Objective criterion.

## 13. Required tests

- unit tests,
- negative tests,
- leakage tests,
- deterministic tests,
- integration tests,
- synthetic fixtures only in CI.

## 14. Artifacts and provenance

Specify artifact path, schema, source view, sampling period, upstream IDs, seed, config, and code revision.

## 15. Documentation updates

List required docs.

## 16. Stop conditions

List cases in which Codex must stop rather than guess.

## 17. Required final report

1. Summary
2. Changed files
3. Interfaces
4. Design decisions
5. Commands run
6. Tests/results
7. Artifacts
8. Data-governance checks
9. Research-invariant checks
10. Limitations
11. Decisions required
12. Recommended next task
