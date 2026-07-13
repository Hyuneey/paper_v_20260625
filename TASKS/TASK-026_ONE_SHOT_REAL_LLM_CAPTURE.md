---
id: TASK-026
title: One-Shot Real LLM Rule Capture Without Execution
status: provider_error_no_rule_response
depends_on: [TASK-025]
phase_gate: ARGOS_REPRODUCTION_GATE_D
---

# TASK-026: One-Shot Real LLM Rule Capture Without Execution

## Scope

Capture exactly one real LLM response, or one researcher-supplied manual
response, using the frozen TASK-025 ARGOS `train-LLM-only` prompt request.

This task evaluates response format and static rule characteristics only.

## Frozen Inputs

```yaml
argos_commit: 6b24161ff08de069840a1fb4fbaecf7bf8e393f1
mode: train-LLM-only
combined_mode_status: deferred
selected_kpi_id: 05f10d3a-239c-3bef-9bdc-a2feeb0037aa
converted_csv_sha256: f6a6d834e23417da5cd0e87af227ae62f0c12a73f080afa08b08a2d332aa5d55
chunk_start_position: 0
chunk_end_position_exclusive: 1000
chunk_hash: 550f47a55f37a18337c097ae4033808ef591d75407581c2e9b3cf8da1ed42015
complete_request_hash: 14af5d91248f3ca579a445527768264f148497d58d85b49b96b39b8873918aca
```

## Outputs

- `docs/argos_reproduction/REAL_LLM_CAPTURE_PROTOCOL.md`
- `docs/argos_reproduction/RULE_STATIC_ANALYSIS_SCHEMA.md`
- `experiments/argos_reproduction/provider_capture.py`
- `experiments/argos_reproduction/rule_static_analysis.py`
- `configs/argos_reproduction/task026_provider_approval.json`
- `configs/argos_reproduction/task026_real_capture.json`
- `docs/task_reports/TASK-026_REAL_LLM_CAPTURE_REPORT.json`
- `docs/task_reports/TASK-026_RULE_STATIC_ANALYSIS.json`
- `docs/task_reports/TASK-026_REPORT.md`
- `tests/test_task026_argos_real_capture.py`

## Current Status

- TASK-025 chunk minimum-count enforcement was tightened.
- DEC-028 approved exactly one API request.
- One approved API request was made.
- The provider returned HTTP `404` with `Model not found gpt-oss-120b`.
- A second one-call attempt was approved using `gpt-5.6-luna`.
- The second attempt returned HTTP `400` with `Unsupported parameter:
  'temperature' is not supported with this model.`
- No rule response text was captured.
- Generated Python execution is not performed.
- No performance metric is computed.

TASK-026 is not complete until exactly one approved API response or one
researcher-supplied manual response is captured and statically analyzed.
The first and second approved one-call API budgets have both been consumed. A
further provider call requires a separate approval update.

DEC-029 separately approves TASK-026R as a one-call request-compatibility
remediation. TASK-026R has separate config, private storage, and reports; it
does not overwrite or retroactively complete the TASK-026 provider-error
record.

## Boundaries

- real provider calls: two approved requests were made
- API key use: true via `OPENAI_API_KEY`, with no key value tracked
- generated Python execution: false
- restricted subprocess execution of captured rule: false
- Docker/Podman execution: false
- RepairAgent or ReviewAgent execution: false
- retries or response-driven prompt tuning: false
- KPI benchmark evaluation: false
- detector-plus-rule mode: false
- SWaT access: false
- `src/paperworks` changes: false
- benchmark or thesis claims: false
