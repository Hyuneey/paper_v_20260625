---
id: TASK-023
title: ARGOS historical alignment and offline reproduction harness
status: complete
depends_on: [TASK-022]
phase_gate: ARGOS_REPRODUCTION_GATE_B
suggested_branch: task-023-argos-historical-alignment
---

# TASK-023: ARGOS Historical Alignment and Offline Reproduction Harness

## 1. Goal

Resolve the source-alignment portion of DEC-027 and implement an offline,
mock-only ARGOS reproduction harness.

This task does not approve real LLM/API calls, execution of actual
LLM-generated Python, full ARGOS training, detector-plus-rule benchmarking,
SWaT experiments, DEC-007 resolution, or changes to `src/paperworks`.

## 2. Inputs

- `external/argos` read-only reference.
- ARGOS paper `https://arxiv.org/abs/2501.14170`.
- TASK-022 protocol and gate documents.
- Current repository commit `7154ea9`.

## 3. In scope

- Fetch sufficient ARGOS history for README and code-path alignment audit.
- Record current upstream HEAD and pinned commit.
- Select first rule-only reproduction commit and mode.
- Defer combined reproduction with a precise historical candidate.
- Recommend one initial public dataset/subset.
- Specify isolated environment and sandbox boundary.
- Add mock-only offline harness outside `src/paperworks`.
- Record leakage and metric matrix.

## 4. Out of scope

- real LLM/API calls,
- API key use,
- actual LLM-generated Python execution,
- full ARGOS training,
- detector-plus-rule benchmark,
- SWaT experiments,
- DEC-007 resolution,
- `src/paperworks` changes,
- benchmark or thesis claims.

## 5. Outputs

- `docs/argos_reproduction/HISTORICAL_ALIGNMENT.md`
- `docs/argos_reproduction/DATASET_SELECTION.md`
- `docs/argos_reproduction/ENVIRONMENT_AND_SANDBOX.md`
- `docs/argos_reproduction/LEAKAGE_AND_METRIC_MATRIX.md`
- `experiments/argos_reproduction/README.md`
- `experiments/argos_reproduction/mock_harness.py`
- `configs/argos_reproduction/task023_offline_harness.json`
- `docs/task_reports/TASK-023_OFFLINE_HARNESS_REPORT.json`
- `docs/task_reports/TASK-023_REPORT.md`

## 6. Completion notes

- Current ARGOS upstream HEAD equals pinned commit `6b24161...`.
- No ARGOS git tags were found.
- `train-LLM-only` at `6b24161...` is frozen as the first rule-only target.
- Combined detector-plus-rule reproduction is deferred.
- KPI Finals phase2 one-series subset is recommended for the future first
  public reproduction dataset.
- Offline harness ran with mock provider, static checks, and no generated-code
  execution.
