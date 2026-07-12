---
id: TASK-022
title: ARGOS reproduction audit and paper-code alignment protocol
status: complete
depends_on: [TASK-021]
phase_gate: ARGOS_REPRODUCTION_GATE_A
suggested_branch: task-022-argos-reproduction-audit
---

# TASK-022: ARGOS Reproduction Audit and Paper-Code Alignment Protocol

## 1. Goal

Prepare a reproducible and safety-controlled protocol for reproducing ARGOS
before implementing the multivariate extension.

This task is an audit and protocol-definition task only. It does not approve
real LLM provider calls, execution of LLM-generated Python, a full ARGOS
experiment, or modifications to the existing `paperworks` proposed-method
pipeline.

## 2. Inputs

- ARGOS repository: `https://github.com/microsoft/ARGOS`
- Local ARGOS reference: `external/argos`
- ARGOS reviewed snapshot: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- ARGOS paper: `https://arxiv.org/abs/2501.14170`
- Current repository starting commit: `5ce6647`

## 3. In scope

- Verify ARGOS local reference commit and license.
- Compare the published paper's ARGOS workflow with the pinned code.
- Identify paper-code alignment gaps around detector-plus-rule aggregation.
- Define a safety-controlled reproduction protocol.
- Record required future decisions before any real ARGOS reproduction run.

## 4. Out of scope

- real LLM provider calls,
- API key use,
- execution of LLM-generated Python,
- full ARGOS experiments,
- opening official sealed final SWaT test data,
- changes to the existing multivariate `paperworks` proposed-method pipeline,
- benchmark or thesis performance claims.

## 5. Outputs

- `docs/ARGOS_REPRODUCTION_PROTOCOL.md`
- `docs/phase_gates/ARGOS_REPRODUCTION_GATE_A.md`
- `docs/task_reports/TASK-022_ARGOS_REPRODUCTION_AUDIT.json`
- `docs/task_reports/TASK-022_REPORT.md`

## 6. Completion notes

- Confirmed ARGOS local reference at commit
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
- Confirmed ARGOS repository license as MIT.
- Confirmed current ARGOS README documents `train-LLM-only`,
  `train-LLM-only-parallel`, and `train-evolution`.
- Confirmed current ARGOS code still exposes `train-combined-fn`,
  `train-combined-fp`, and `eval-combined` code paths.
- Confirmed paper-code alignment remains unresolved for the Aggregator /
  detector-plus-rule reproduction path.
- Did not run ARGOS training, call an LLM, execute generated Python, or modify
  the proposed-method pipeline.
