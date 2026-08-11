# TASK-039E2-AUDIT-PREP — Independent Construction Execution Configuration Audit Preparation

## Scope

Prepare a standard-library-only, provider-free oracle that can later audit a
frozen TASK-039E2 construction-execution configuration. This task audits no
real E2 result, reads no E1 private evidence, makes no provider call, and
grants no E3, rule, or runtime authority.

## Frozen base and branch

- Base: `4a6b5875b59bdcc7c3bd0957e90fa27b71e0e9fb`
- Branch: `task-039e2-audit-prep`
- Status: `passed_task039e2_audit_preparation`

## Independent checks prepared

- Exact provider, endpoint, snapshot, reasoning, sampling, token, seed,
  streaming, storage, and fallback settings.
- Complete prompt, structured-schema, rendering, retrieval, T0-template,
  schedule, retry, and direct-number policy hash bindings.
- Closed structured-output syntax without relation-specific answer leakage;
  semantic deterministic validity remains a separate check.
- Equal initial scientific content for T1, three T1-B calls, and T2 call 1.
- T1-B independence, lowest-admissible-index selection, and no fourth call.
- One-action T2 retrieval constrained to the initial E1 evidence identity set.
- Direct-number isolation of exactly three calibrated roles.
- A relation-major 42-relation schedule with one local T0, 42 T1 calls, 126
  T1-B calls, at most 126 T2 calls, 42 direct-number calls, concurrency one,
  and a maximum of 336 scientific provider calls.
- Transport-only retry classification with two transport retries, zero
  scientific retries, and full-run failure without relation skipping.
- A provider-free capability receipt with no account, contact, or seed
  determinism claim.

## Hard boundary

The preparation module exposes no file reader, provider client, credential
reader, model invocation, construction runner, or runtime-authority path. Its
provider interaction function always fails before client or credential use.
All tests use `SYNTHETIC_*` identities and fake values.

## Outputs

- `src/paperworks/v6/task039e2_audit_prep_v1.py`
- `src/paperworks/contracts/task039e2_audit_prep_v1.py`
- `schemas/v6/task039e2_*_schema.json`
- `tests/task039e2_audit_support.py`
- `tests/test_task039e2_audit_*.py`
- `docs/task_reports/TASK-039E2_AUDIT_PREP_REPORT.md`
