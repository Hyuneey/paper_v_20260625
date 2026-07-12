---
id: TASK-025
title: ARGOS Rule-Only Prompt Fidelity and Provider-Ready Generation Capture
status: completed
depends_on: [TASK-024]
phase_gate: ARGOS_REPRODUCTION_GATE_C
---

# TASK-025: ARGOS Rule-Only Prompt Fidelity and Provider-Ready Generation Capture

## Scope

Reconstruct the pinned ARGOS `train-LLM-only` prompt path for the selected KPI
series and capture a mock provider response without executing generated Python.

## Frozen Inputs

```yaml
argos_commit: 6b24161ff08de069840a1fb4fbaecf7bf8e393f1
mode: train-LLM-only
combined_mode_status: deferred
kpi_source_commit: d06bda15d511d930cbf4e6a6de14bd94d790f0f2
selected_kpi_id: 05f10d3a-239c-3bef-9bdc-a2feeb0037aa
converted_csv_sha256: f6a6d834e23417da5cd0e87af227ae62f0c12a73f080afa08b08a2d332aa5d55
```

## Outputs

- `docs/argos_reproduction/ARGOS_PROMPT_FIDELITY.md`
- `docs/argos_reproduction/KPI_PROMPT_CHUNK_MANIFEST.md`
- `docs/argos_reproduction/PROVIDER_AND_RETENTION_POLICY.md`
- `experiments/argos_reproduction/prompt_capture.py`
- `configs/argos_reproduction/task025_prompt_capture.json`
- `configs/argos_reproduction/task025_provider_approval.template.json`
- `docs/task_reports/TASK-025_PROMPT_CHUNK_MANIFEST.json`
- `docs/task_reports/TASK-025_PROMPT_CAPTURE_REPORT.json`
- `docs/task_reports/TASK-025_REPORT.md`
- `tests/test_task025_argos_prompt_capture.py`

## Result

- TASK-024 restricted subprocess fallback evidence fields were corrected.
- Pinned ARGOS prompt path was mapped to files/functions.
- Chunk size resolved to pinned code default `1000`.
- Selected prompt chunk: positions `[0, 1000)`, label counts `0=996`, `1=4`.
- Full prompt, selected rows, raw response, and quarantined rule text were
  written only under ignored `artifacts/`.
- Mock response was captured and statically validated.
- Generated Python execution was not performed.
- No performance metric was reported.

## Boundaries

- real provider calls: false
- API key use: false
- actual generated Python execution: false
- Docker claim without Docker/Podman run: false
- full ARGOS training: false
- RepairAgent or ReviewAgent execution: false
- detector-plus-rule combined mode: false
- KPI benchmark evaluation: false
- SWaT access: false
- `src/paperworks` changes: false
- benchmark or thesis claims: false
