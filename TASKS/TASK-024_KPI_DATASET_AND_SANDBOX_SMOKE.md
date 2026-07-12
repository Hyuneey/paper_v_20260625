---
id: TASK-024
title: KPI Dataset Preparation and Fixed-Rule Sandbox Execution Smoke
status: completed
depends_on: [TASK-023]
phase_gate: ARGOS_REPRODUCTION_GATE_B
---

# TASK-024: KPI Dataset Preparation and Fixed-Rule Sandbox Execution Smoke

## Scope

Prepare one public KPI series for the first ARGOS rule-only reproduction smoke
and execute only the repository-owned fixed mock rule from TASK-023 inside the
approved sandbox boundary.

## Frozen Upstream Decision

```yaml
initial_reproduction_mode: train-LLM-only
initial_source_commit: 6b24161ff08de069840a1fb4fbaecf7bf8e393f1
combined_mode_status: deferred
future_aggregator_candidate_commit: c03427f
```

## Outputs

- `docs/argos_reproduction/KPI_DATASET_MANIFEST.md`
- `docs/argos_reproduction/KPI_PREPROCESSING_PROTOCOL.md`
- `docs/argos_reproduction/FIXED_RULE_SANDBOX_POLICY.md`
- `experiments/argos_reproduction/kpi_prepare.py`
- `experiments/argos_reproduction/sandbox_runner.py`
- `experiments/argos_reproduction/container/`
- `configs/argos_reproduction/task024_kpi_sandbox_smoke.json`
- `docs/task_reports/TASK-024_KPI_DATASET_MANIFEST.json`
- `docs/task_reports/TASK-024_SANDBOX_SMOKE_REPORT.json`
- `docs/task_reports/TASK-024_REPORT.md`
- `tests/test_task024_argos_kpi_sandbox.py`

## Result

Selected KPI ID:

```text
05f10d3a-239c-3bef-9bdc-a2feeb0037aa
```

The fixed mock rule smoke completed with exit code 0. Output shape and binary
domain checks passed.

## Boundaries

- real provider calls: false
- API key use: false
- actual LLM-generated Python execution: false
- full ARGOS training: false
- combined detector-plus-rule path: false
- SWaT access: false
- `src/paperworks` changes: false
- benchmark claims: false
- thesis claims: false

Docker/Podman were unavailable in the local environment, so the executed smoke
used the restricted subprocess fallback. Actual LLM-generated Python remains
gated behind a future approved containerized sandbox run.
