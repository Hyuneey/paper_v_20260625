# TASK-039E3 R2R Utility Normal-Only Authority V1 R1 — Focused Independent Re-audit

Status: `blocked_task039e3_r2r_utility_normal_only_authority_v1_r1_focused_independent_reaudit`

The re-audit independently confirms five of the six R1 closures. It does not pass because the public receipt still accepts numeric JSON values at one boolean-only nested field.

## Finding-by-finding result

| Finding | Independent evidence | Result |
|---|---|---|
| COMMON authority replay bypass | Seven attacker-self-consistent mutations were rejected through replay and downstream registry/receipt boundaries; canonical 42/420 replay passed. | CLOSED |
| Locator precheck after value parse | Five invalid output/locator cases produced zero loader and parser calls; valid preflight reached the normal input identity gate. | CLOSED |
| Caller-selected builder authority | Arbitrary commit and forged authorization objects were rejected; canonical R1 exposes no caller commit and real authorization remains pending. | CLOSED |
| Public receipt open schema leakage | Unknown keys are rejected, but self-rehashed `scientific_result_evaluable = 1` and `1.0` are accepted because equality with `True` is not strict type validation. | **OPEN** |
| Locator file path not revalidated | An external regular locator passed; an inside-Git copy and symlink path were rejected. | CLOSED |
| Locator/receipt builder cross-binding | Separate locator, receipt, and execution-control identity mutations were rejected. | CLOSED |

## Blocking evidence

The following receipt mutations were independently reconstructed and self-rehashed:

- `construction_provenance.scientific_result_evaluable = 1` → accepted unexpectedly
- `construction_provenance.scientific_result_evaluable = 1.0` → accepted unexpectedly
- `False`, `"true"`, and `null` → rejected

Python/JSON equality permits `1 == True` and `1.0 == True`. The receipt therefore does not yet enforce the promised exact recursive type schema. No production fix was attempted because this is an audit-only task.

## Regression and boundary checks

- Focused independent tests: 9/9 passed
- Original V1 tests: 24/24 passed
- Prior independent audit tests: 28/28 passed
- R1 remediation tests: 10/10 passed
- `compileall`, `pip check`, and `git diff --check`: passed
- Production source modified: false
- Prior tests modified: false
- HAI normal/test/label access: 0/0/0
- Utility computations: 0
- Provider/API-key/scientific calls: 0/false/0

Minimal scientific invariants remain unchanged: COMMON 42/0, 420 utility references, 462 historical bindings, authority-definition hash `6e7a286a37a5048a7887e8bea69f9ec0a9c3ff76c538cbb475e886fba276e4de`, calibration-policy hash `4f2622050637e3e83205dec59400fa6bf9ed2bd1a41f6b8ceb1900dc9f69b881`, and T2 utility authorization remains false.

## Readiness

`NORMAL_ONLY_AUTHORITY_PROTOCOL_AUDITED = false`

`NORMAL_ONLY_AUTHORITY_REAL_MATERIALIZATION_READY = false`

`NORMAL_ONLY_AUTHORITY_MATERIALIZED = false`

`UTILITY_EVALUATOR_IMPLEMENTATION_READY = false`

`UTILITY_EXECUTION_AUTHORIZATION_READY = false`

There is no automatic next task. Return to the user for a scope/remediation decision.
