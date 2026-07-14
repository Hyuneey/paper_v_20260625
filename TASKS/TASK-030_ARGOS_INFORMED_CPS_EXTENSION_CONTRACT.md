---
id: TASK-030
title: ARGOS-Informed Multivariate CPS Extension Contract
status: complete
depends_on: [TASK-029]
phase_gate: MULTIVARIATE_METHOD_SPECIFICATION_GATE
---

# TASK-030: ARGOS-Informed Multivariate CPS Extension Contract

## Result

TASK-030 converts the frozen ARGOS audit into an implementation-ready method
contract. It defines graph, evidence, relation-family, rule DSL, parameter,
calibration, verifier, agent, runtime, fusion, explanation, research-question,
split, threshold, and claim boundaries.

Seven Draft 2020-12 JSON schemas and synthetic valid/invalid fixtures define
the artifact interfaces. Offline tests validate schema structure and cross-
artifact references without importing production code or reading datasets.

## Not implemented or verified

- complete proposed method;
- graph learner or candidate generator;
- LLM planner/reviewer;
- deterministic calibrators/verifier/runtime;
- detector or fusion execution;
- KPI, SWaT, WADI, or Kaggle experiment;
- anomaly-detection or explanation performance.

## Boundaries

- Provider/LLM calls: false
- Generated Python loading/execution: false
- ARGOS agent execution: false
- Dataset/private artifact access: false
- Docker/Podman work: false
- `src/paperworks` changes: false
- Benchmark/thesis performance claims: false
