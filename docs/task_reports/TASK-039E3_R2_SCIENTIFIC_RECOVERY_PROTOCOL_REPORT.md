# TASK-039E3-R2 Scientific Recovery Protocol

Status: `passed_task039e3_r2_scientific_recovery_protocol_freeze`

The failed R2 execution remains `ABORTED_NON_EVALUABLE_EXECUTION`. Its first T1 request received HTTP 400, no provider-authored scientific response was returned under the frozen custody semantics, and the preserved error body is unavailable. The evidence supports a frozen-request HTTP rejection, but not a more specific causal diagnosis.

## Frozen decisions

- Reuse the durable corrected capability PASS. The cumulative probe count stays 2/2; no third probe or diagnostic provider call is authorized.
- Start `TASK-039E3-R2R` as a fresh full cohort from relation 0. Do not resume and do not reuse the prior T0 record, failed T1 slot, or any partial ledger record.
- Keep historical aborted-R2 accounting separate: one logical call, one transport attempt, zero provider-authored scientific responses, zero T1 proposals, and zero evaluable scientific results.
- Give the R2R cohort its own 252..336-call scientific budget. Lifetime calls are reported as one historical attempt plus the actual R2R calls.
- Use `RECOVERY_MAIN_PROVIDER_SCHEMA_V2` identically for T1, T1-B, and T2. It removes only provider-facing `$schema`, `minLength`, hash `pattern`, and array `minItems`/`maxItems`/`uniqueItems` constraints while preserving closed objects, all required fields, basic types, enums, and the complete window map.
- Keep project deterministic validation as the final admissibility authority. One canonical case passed and all 25 adversarial cases were rejected; the provider-schema relaxation does not lower the scientific gate.
- Keep the direct-number provider schema unchanged. Prompts, model, endpoint, sampling, concurrency, and generation-retry semantics are unchanged.
- Retain future HTTP error bodies privately with a deterministic 64 KiB bound and sanitized public hashes/metadata. HTTP 400 remains nonretryable and fail-closed.

`uniqueItems` is a high-priority provider-schema compatibility suspect based on the supplied official-document snapshot, not a proven cause of the historical HTTP 400.

## Implementation boundary

This protocol changes no production or scientific source. The next offline remediation must implement the V2 projection, deterministic parity binding, durable capability-PASS reuse, a distinct fresh R2R cohort, bounded HTTP-error custody, and a pre-E1 check that all provider/proposal/outcome/direct recovery ledgers are empty.

The required sequence is:

1. `TASK-039E3-R2R-REQUEST-CONTRACT-REMEDIATION`
2. `TASK-039E3-R2R-INDEPENDENT-AUDIT`
3. `TASK-039E3-R2R-AUTHORIZATION-FREEZE`
4. `TASK-039E3-R2R-SCIENTIFIC-EXECUTION`

No step may be skipped. This task grants no provider contact, capability probe, scientific execution, resume, Rule v2, runtime, utility, or winner-selection authority.

## Verification

At exact Protocol Commit A, the protocol suite passed 11/11 tests, compatible forensic/validity/provider regressions passed 56/56, and compatible execution/custody/failure/authorization regressions passed 26/26. All 93 tests passed. Compileall, pip check, nine Git-object JSON self-hashes, Git diff validation, and the sanitized leak scan passed. Production/scientific/runner/schema changes were zero.

Multi-agent offline lanes A-G agreed. No worker wrote authoritative files, no private custody was read by workers, no provider call occurred, and the coordinator performed exactly one authorized private read of the capability receipt before closing private access.
