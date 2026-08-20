# TASK-039E3-R2R-UTILITY-INNER-D1-EXECUTION-V1

## Purpose

Execute the first real scientific utility experiment: exact INNER test1,
COMMON-42, D1 Rule-only. Replay the immutable authorization artifact set from
Commit `7df8edf24993bf42401b487c56a188ce7546da91`, issue one process-local
execution grant, execute the full census exactly once, freeze label-blind rule
predictions, then evaluate the frozen predictions against label-test1 using the
frozen Attack-event recall and normal FAR episodes/hour formulas.

Scientific performance is not a task gate. Results must not cause any rule,
threshold, relation, policy, denominator, or metric change.

## Exact base and authority

- Base: `721b5b60ecbf1e2b33bf03f864ee9171a47800e1`.
- Branch: `task-039e3-r2r-utility-inner-d1-execution-v1`.
- Authorization: `deb08014de20c398d2dcde046e14b505a65af2d52cb6eb309fc8188f020b5834`.
- Custody preflight: `3acff12cb2135b86539720e792d6e01075808ea84b6939b06909d397b1b43129`.
- Scope: `HAI_23_05_P1_TEST1_COMMON42_D1_RULE_ONLY_INNER_V1`.
- R3 implementation: `af74bf3bd9ae240f21c57630b4804eabb997021353f15e7c402904b94f783fb5`.
- Evaluator bundle: `0510da125dd8a799c988927ba49ecb784cad5ea12b05b41e31406effe23051c9`.
- V4 authority: `1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343`.
- MAIN registry: `9b9ca67d858cb88ce934d1d8a6e0b563b7dc9bb01437d2835b68e2d1e61483d0`.
- Supplement registry: `12ec7f50a953e097cd7cbe3ac93c7cabfb669130612d7f30ab3b19df85289aaf`.
- Test1 features: `78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be`.
- Test1 labels: `eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc`.

## Frozen execution contract

The new bridge is outside the seven audited R3 evaluator modules and outside
the frozen INNER authorization module. It accepts no caller scientific knobs.
It defines separate real types and a non-scientific differential-test plane.
At least 30 controlled cases must have zero semantic divergence from R3 before
real data is parsed. Commit A freezes the bridge and synthetic tests; Commit B
contains only independent audit tests.

The real access order is grant replay, MAIN validation, supplement validation,
test1 raw hash, 22-feature parsing, 12-source census, COMMON-42 opportunity
enumeration, rule execution, in-memory prediction freeze, label raw hash,
label parsing, attack-event derivation, alarm-episode formation, metrics,
private evidence freeze, and sanitized public artifacts. Label access before
prediction freeze is prohibited. Scientific execution attempts equal one and
retries equal zero.

## Scientific semantics

- Source windows: 5 pre, 5 post; stability fraction 0.8.
- Refractory clustering: 10 seconds, single-link; largest absolute step;
  earliest physical index on an exact tie.
- Cross-source isolation: inclusive two-second radius over all 12 sources.
- Target baseline: 5 seconds; target response: 3 seconds beginning at the
  frozen selected horizon.
- Terminal states: `evaluated_expected_response`, `evaluated_anomaly`, or
  authorized boundary `abstain`; malformed input is an error.
- Alarm episodes: sorted unique anomaly decision rows merged into maximal
  consecutive half-open intervals.
- Attack events: maximal contiguous strict integer-label-one half-open runs.
- Metrics: event recall and normal false-alarm episodes per labeled normal hour.

## Permanent prohibitions

Test2, OUTER, D0, D2, detector, fusion, runtime LLM, recalibration, rule
regeneration, metric modification, caller relation/source/opportunity subsets,
and caller denominators are prohibited. Raw rows, labels, attack intervals,
private paths, private registry records, and private numeric values never enter
Git or public output. The frozen R3 evaluator constant
`REAL_UTILITY_EXECUTION_AUTHORIZED` remains false.

## Freeze and handoff

Commit C contains only sanitized predictions/results/accounting/readiness/
bundle/receipt/report artifacts. Commit D contains only project-state updates.
On faithful execution the status is
`passed_task039e3_r2r_utility_inner_d1_execution_v1`, with scientific status
`D1_EXECUTED_RESULT_INTEGRITY_AUDIT_PENDING`. The exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D1-RESULT-INTEGRITY-AUDIT-V1`.
