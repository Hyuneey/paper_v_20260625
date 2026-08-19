# TASK-039E3 R2R Utility Normal-Only Authority V1 — Remediation R1

Status: `passed_task039e3_r2r_utility_normal_only_authority_v1_bounded_remediation_r1`

This additive R1 control revision closes the six execution/authority/custody findings from the blocked independent audit without changing the scientific authority version, calibration formulas, relation set, reference identities, or data boundary.

## Closure summary

| Finding | Closure |
|---|---|
| COMMON authority replay bypass | Every authority-bearing boundary replays the exact 42 relations, executable semantics, 420 references, binding-set hash, and definition hash. Seven semantic mutations fail closed. |
| Locator precheck after value parse | An explicit output/custody preflight now rejects missing or mismatched locator state, Git-contained paths, and existing outputs before any normal-value loader is called. |
| Caller-selected builder authority | The compatibility API accepts only the frozen scientific V1 commit. The canonical R1 path has no caller commit argument and remains disabled until a separately frozen execution authorization exists. |
| Public receipt open schema | The receipt enforces an exact 33-key top-level schema, exact nested schemas, and strict scalar types. Unknown keys fail even after recomputed self-hash. |
| Locator path not revalidated | Final validation checks the locator file itself is an existing regular non-symlink outside the repository before and after reading it. |
| Locator/receipt builder mismatch | Locator, receipt, private registry, and execution-control identities are cross-bound; independently rehashed mismatches fail closed. |

## Scientific invariants

- COMMON: 42 accepted / 0 `no_rule`
- Utility numeric references: 420 (42 × 10)
- Historical bindings: 462 (42 × 11)
- Only excluded utility role: `selected_delay_horizon_seconds`, already frozen in executable semantics
- Authority-definition hash: `6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de`
- Calibration-policy hash: `4f2622050637e3e83205dec59400fa6bf9ed2bd1a41f6b8ceb1900dc9f69b881`
- T2 utility remains unauthorized.
- Historical E1 and historical numeric-registry identities remain unrestored.

## Verification

- Original V1 synthetic suite: 24/24 passed
- Unchanged independent audit suite: 28/28 passed
- R1 focused remediation suite: 10/10 passed
- `compileall`, `pip check`, and `git diff --check`: passed

All fixtures were synthetic. HAI normal/test/label accesses, utility computations, provider calls, API-key access, and scientific LLM calls were all zero.

## Boundary after freeze

`NORMAL_ONLY_AUTHORITY_PROTOCOL_AUDITED = false`

`NORMAL_ONLY_AUTHORITY_REAL_MATERIALIZATION_READY = false`

`NORMAL_ONLY_AUTHORITY_MATERIALIZED = false`

`UTILITY_EVALUATOR_IMPLEMENTATION_READY = false`

`UTILITY_EXECUTION_AUTHORIZATION_READY = false`

Exact next task: `TASK-039E3-R2R-UTILITY-NORMAL-ONLY-AUTHORITY-V1-R1-FOCUSED-INDEPENDENT-REAUDIT`.
