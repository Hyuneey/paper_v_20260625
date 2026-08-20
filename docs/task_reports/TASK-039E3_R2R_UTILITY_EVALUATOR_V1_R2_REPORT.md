# TASK-039E3 R2 Utility Evaluator Provenance Remediation

Status: `passed_task039e3_r2r_utility_evaluator_v1_bounded_remediation_r2`

R2 closes `BLOCKER_EVALUATOR_R1_RULE_PREDICTION_HISTORICAL_IMPLEMENTATION_IDENTITY_ACCEPTED` without changing scientific semantics. `EvaluatorImplementationAuthorityV1` now has one owner in the authority module, uses control revision `R2`, and derives implementation identity `e7a61070c0be96e305f6706b90308c9976bc8d521c8b97adea93836c3fd28cef`.

RulePredictionArtifact issuance now requires an exact factory-custodied current R2 implementation-authority object bound to the exact supplied evaluator bundle. The identity is derived internally. The legacy raw-identity keyword remains only as an unconditional fail-closed compatibility trap; historical, R1, correct-R2, random, malformed, and explicit-null raw identities all reject.

Prediction issuance metadata binds the exact artifact weak reference, artifact hash, R2 implementation identity, and evaluator authority bundle hash. Validation requires this issuance custody, current-R2 provenance, and all prior semantic/hash replay.

Focused results: 20/20 invalid provenance attacks rejected. The unchanged historical blocker test passes. All ten historical R1 invalid reproductions remain rejected. R1 remediation suites passed 7/7, 4/4, and 11/11. Original evaluator suites passed 9/9, 13/13, 6/6, 11/11, and 6/6. Lower regressions passed 36/36, 62/62, 51/51, 8/8, 13/13, and 15/15.

Two pre-existing test files received provenance-only fixture/assertion updates: the original metrics test now uses a factory-issued R2 authority instead of an arbitrary caller hash; the R1 remediation authority positive-current assertion now binds the mandated R2 revision and identity. No scientific assertion changed. Frozen independent tests were not modified.

Canonical synthetic source-event, opportunity, rule-state, alarm, attack-event, recall, and FAR behavior is unchanged. Only control/provenance identities and hashes transitively containing them rotate.

No private registry, locator, HAI split, label, or attack interval was accessed. No real utility, detector, provider, scientific LLM, API key, or audit-runtime network operation occurred. Real utility remains `NOT_EXECUTED`.

Exact next task: `TASK-039E3-R2R-UTILITY-EVALUATOR-V1-R2-INDEPENDENT-REAUDIT-AND-COMPLETION`.
