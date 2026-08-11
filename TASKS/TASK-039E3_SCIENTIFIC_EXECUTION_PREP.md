# TASK-039E3-PREP — Mock Rule-Construction Scientific Execution Harness Preparation

## Scope

Prepare the deterministic orchestration and artifact-custody machinery for a
future TASK-039E3 execution using only `SYNTHETIC_*` fixtures and an injectable
in-memory mock transport.

This preparation:

- binds public E2 protocol bundle
  `2295f6e57aff47081419d70e942af02101de33fa545a758ea4a7e6476a46e6e8`;
- reuses the frozen E2 prompt, schema, rendering, schedule, and retry policies;
- delegates proposal validity to project-owned `task039e0_validity_v2`;
- prepares T0, T1, T1-B, T2, and direct-number orchestration;
- prepares append-only provider-call, proposal/validity, outcome, failure, and
  sanitized metric custody;
- contains no network client, credential reader, live runner, real E1 loader,
  rule authority, or runtime authority.

## Frozen execution identity

- Base: `3c263277d5b30217058601bd0e12876d2cf58ba4`
- Branch: `task-039e3-scientific-execution-prep`
- Provider identity: `openai`
- Endpoint: `https://api.openai.com/v1/chat/completions`
- Exact model: `gpt-5.4-2026-03-05`
- Maximum scientific slots: `336`
- Capability slot: one separate non-scientific mock slot
- Status: `passed_task039e3_scientific_execution_preparation`

## Hard locks

`LIVE_PROVIDER_TRANSPORT_ENABLED = false`.

The task-owned live-transport, credential-read, and live-request functions
always fail before I/O. There is no `--live` flag or runnable provider path.
A future additive live runner must separately validate an exact E3
authorization, clean execution commit, E2 bundle, E1 private-ledger hash, and
capability-probe PASS before any scientific call.

## Scientific separations

- Mock calls are not provider or LLM calls.
- Provider refusal and invalid structured output consume their scientific
  calls and follow frozen arm-specific `no_rule` handling; they are not
  transport retries.
- Transport retries reuse the same precommitted scientific slot.
- T2 retrieval only re-presents identities already in the initial corpus.
- Direct-number error metrics remain separate from main validity metrics.
- No utility labels or candidate-method outcomes enter construction validity.
- Individual structured proposals remain private by default.

## Outputs

- `src/paperworks/v6/task039e3_execution_prep_v1.py`
- `src/paperworks/v6/task039e3_orchestration_v1.py`
- `src/paperworks/contracts/task039e3_execution_prep_v1.py`
- `schemas/v6/task039e3_*_schema.json`
- `tests/task039e3_support.py`
- `tests/test_task039e3_*.py`
- `docs/task_reports/TASK-039E3_PREP_REPORT.md`
