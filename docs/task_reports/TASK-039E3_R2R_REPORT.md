# TASK-039E3-R2R Request-Contract Remediation

Status: `passed_task039e3_r2r_request_contract_remediation`

Implementation Commit A is `f6749952f4e7f1ec7f7adec967ba7627feab18ac`. It is a direct child of the frozen recovery-protocol Commit B, `8577e7cdf2893adb4ad6da588b2afb4d1896289d`.

## Result

- `RECOVERY_MAIN_PROVIDER_SCHEMA_V2` reproduces the frozen hash `bcbc9debc32ec9e4b02d5781c7f8b512023752ccb90f60154648bb5d9de67aa1`.
- Backward-compatible keyword-only builder injection preserves the V1 default request path. R2R T1, T1-B, and T2 share V2; direct-number remains V1.
- Deterministic admissibility is unchanged. Provider-schema relaxation does not lower the scientific gate, including duplicate/missing/unsupported-variable rejection.
- The durable corrected capability PASS is validated by exact receipt, ledger-head, model, accounting, and disk-authority bindings. R2R exposes no capability-transport or third-probe path.
- The R2R path requires four empty ledgers before injected E1 loading, discards all historical partial results as metric inputs, and starts a fresh 42-relation cohort with 252..336 scientific logical calls. Lifetime accounting remains `1 + actual_r2r_scientific_logical_calls`.
- HTTP-error custody retains at most 65,536 private bytes and reads at most 65,537 bytes. Public projection contains only sanitized hashes/metadata. HTTP 400 remains nonretryable; 429/5xx retry behavior is unchanged.
- The future R2R authorization schema/validator is closed and synthetic-only. No real authorization artifact was created.

## Source freeze

The source-freeze artifact hash is `4d6d3b080b545b2effb98240d413ae085ad1c912ab39e489edd6dc582fa65655`. An independent raw-Git AST reconstruction found 39 active project-local paths including the runner and 38 dependencies. The manifest binds those paths plus one conservative authorization-schema record: 40/40 Git blobs and exact-byte SHA-256 values verified, zero dynamic imports, zero unresolved imports, and zero unbound material dependencies.

## Verification

Focused exact-Commit-A validation ran 128 unit tests: 128 passed, with no failures, errors, or skips. `compileall`, offline runner self-check, closed-schema validation, JSON parsing/self-hashing, source-closure verification, sanitized leak scan, `pip check`, and `git diff --check` passed. The test-report hash is `67942e2ff29d0930fe210bd7a6aecac47e9aeea30e79402a64e3286acca32851`; the implementation-receipt hash is `6852ce81f108c968df23d6961ed41dcde4feac18b9ce6e0729c055d187369714`.

## Multi-agent aggregation

- Lane A: exact request contract and backward-compatible orchestration injection — PASS.
- Lane B: bounded HTTP-error custody and unchanged retry semantics — PASS.
- Lane C: capability reuse, fresh-cohort coordinator, and future closed authorization contract — PASS.
- Conflicting results: none.
- File-ownership violations or concurrent authoritative writes: none.

## Boundaries

Provider contact, credential access/presence checking, capability probing, scientific calls, live execution, real E1 access, and failed-R2 private-root access were all zero/false. Rule v2, runtime, utility evaluation, winner selection, resume, and scientific execution authority remain false. Commit B is restricted to these four report artifacts; no Commit-A implementation, schema, runner, or tests are modified.

The only next authorized task is `TASK-039E3-R2R-INDEPENDENT-AUDIT`.
