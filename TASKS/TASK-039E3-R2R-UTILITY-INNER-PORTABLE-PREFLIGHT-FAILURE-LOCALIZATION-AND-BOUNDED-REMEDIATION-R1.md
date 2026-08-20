# TASK-039E3-R2R-UTILITY-INNER-PORTABLE-PREFLIGHT-FAILURE-LOCALIZATION-AND-BOUNDED-REMEDIATION-R1

Execution mode: private diagnostic/custody work is single-coordinator only;
an optional audit agent is public/read-only. No D1 scientific execution and
no manual private-path input are authorized.

## Purpose and exact base

Localize the previously sanitized `PORTABLE_RECOVERY_BLOCKED_PREFLIGHT`,
remediate only the proven defect, independently audit it, make one new real
preflight attempt, and issue the existing exact INNER D1 authorization only
after PASS. Branch from
`ad045dcc1c84f018522baf20ab23ba66ff1fe9ce`; preserve blocker
`b1daa7f915785b66ce07fa0a9c6fa91e9eba4738`, Portable Contract A
`1d7b47daf053ffbcbf69499b55b68ce7c2838e83`, and Portable Audit B
`da3872530f45fb0093d815c9f50fe08216cc2fda`. Require clean, exact lineage,
no rebase, and no unrelated merge.

## Frozen science and custody

- Portfolio `COMMON-42`, 42 relations, T2 false.
- MAIN registry hash
  `9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0`.
- Supplement registry hash
  `12ec7f50a953e097cd7cbe3ac93c7cabfb669130612d7f30ab3b19df85289aaf`.
- Test1 feature hash
  `78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be`.
- Test1 label hash
  `eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc`.
- Portable control starts at `R1_PORTABLE_PRIVATE_CUSTODY`, policy
  `PORTABLE_PRIVATE_LOCATOR_POLICY_V1`; historical locator equality is not a
  current-machine criterion.

Do not recalibrate, change formulas/windows/relations, derive authority from
test1, access test2, execute rules/detectors, compute metrics, or expose any
path, registry value, raw row, label, interval, environment value, exception,
or traceback.

## Fixed-stage diagnostic

Add
`scripts/audit_task039e3_r2r_inner_portable_preflight_failure_v1.py`. It
loads only the five approved ignored bindings, suppresses all internal output,
does not call `perform_inner_execution_custody_preflight_v1()`, and reports
only `PASS`/`BLOCK` for these fixed stages:

1. `D01_ENV_BINDINGS`
2. `D02_MAIN_REGISTRY_FILE`
3. `D03_MAIN_LOCATOR_FILE`
4. `D04_MAIN_MATERIALIZATION_AUTHORITY`
5. `D05_MAIN_LOCATOR_SCHEMA`
6. `D06_MAIN_LOCATOR_REGISTRY_BINDING`
7. `D07_MAIN_REGISTRY_DOCUMENT`
8. `D08_MAIN_REGISTRY_CANONICAL_HASH`
9. `D09_SUPPLEMENT_REGISTRY_FILE`
10. `D10_SUPPLEMENT_LOCATOR_FILE`
11. `D11_SUPPLEMENT_MATERIALIZATION_AUTHORITY`
12. `D12_SUPPLEMENT_LOCATOR_SCHEMA`
13. `D13_SUPPLEMENT_LOCATOR_REGISTRY_BINDING`
14. `D14_SUPPLEMENT_REGISTRY_DOCUMENT`
15. `D15_SUPPLEMENT_REGISTRY_CANONICAL_HASH`
16. `D16_HAI_ROOT`
17. `D17_TEST1_FEATURE_FILE`
18. `D18_TEST1_FEATURE_HASH`
19. `D19_TEST1_LABEL_FILE`
20. `D20_TEST1_LABEL_HASH`
21. `D21_FULL_PREFLIGHT_REPLAY`

Unexpected failures emit only `UNEXPECTED_FAIL_CLOSED`. Classify one of:
local wiring, MAIN locator compatibility, supplement locator compatibility,
materialization replay, registry validation, HAI/test1 custody, or
authorization-preflight logic. Wrong registry/data/authorization identity is
a terminal non-remediable blocker.

## Bounded remediation

Wiring defects modify only ignored bindings. Locator/runtime defects may
modify only
`src/paperworks/v6/task039e3_r2r_utility_inner_execution_authorization_v1.py`.
Never modify the R3 evaluator, V4, MAIN authority, supplement authority,
calibration, data, COMMON, or metrics. Historical materialization validators
remain frozen. A required production repair rotates only the control revision
to `R2_PORTABLE_PREFLIGHT`; scientific authorization version and scope remain
unchanged.

Runtime locator custody requires exact artifact/schema/authority/purpose,
canonical self-hash, local-only and never-commit flags, regular non-symlink
files outside Git, exact configured registry target, exact canonical registry
hash, and exact frozen materialization authorization. It does not require a
historical path, locator hash, timestamp value, or finalizer transaction.

Commit A contains only this specification, the diagnostic harness, bounded
INNER authorization repair if proven, focused tests, and minimal fixtures.
After A freezes, Commit B contains independent tests only. Reject wrong
registry/locator/authorization, target swaps, malformed/repo/symlink cases,
historical replay confusion, self-rehash, cross-authority substitution,
reconstructed preflight/authorization, and D0/D2/detector/OUTER escalation.
Accepted invalid is zero.

## Static and real gates

Before real custody, run diagnostic, portable/remediation/independent,
authorization static/independent, exact R3, V4, MAIN, supplement, compileall,
pip, diff, self-hash, and leak checks. Require D01-D20 PASS and exact MAIN,
supplement, feature, and label identities. Test2 remains untouched.

This new task authorizes one call to
`perform_inner_execution_custody_preflight_v1()`. No retry. After PASS, issue
one `InnerExecutionAuthorizationV1` and validate it with `require_real=True`.
Exact scope is `HAI_23_05_P1_TEST1_COMMON42_D1_RULE_ONLY_INNER_V1`: D1 true;
D0, D2, detector, fusion, OUTER, test2, recalibration, rule regeneration, and
metric modification false. Stop before utility parsing, events, rules,
metrics, detector, or any real utility computation.

## Reports, commits, and continuity

Create the ten requested self-hashed diagnostic, root-cause, remediation,
independent-audit, preflight, authorization, readiness, bundle, receipt, and
Markdown reports with no private content. Leak scan outputs only PASS/BLOCK.
Commit C contains reports/authorization artifacts only. Commit D contains
only `docs/project_state` updates, including sanitized root cause. Push and
require divergence `0 0` and clean worktree/index.

PASS status is
`passed_task039e3_r2r_utility_inner_portable_preflight_failure_localization_and_bounded_remediation_r1`.
Set INNER authorization and D1 issuance true; D1 executed, OUTER, and real
utility authorization remain false. The exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D1-EXECUTION-V1`, followed by the separate D1
result-integrity audit. On any frozen identity mismatch, leak, test2 access,
or unresolved scientific authority issue, freeze a sanitized blocker and
STOP without broadening remediation.
