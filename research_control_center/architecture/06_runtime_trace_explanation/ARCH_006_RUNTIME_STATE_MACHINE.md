# Frozen D1 runtime state machine

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

The frozen D1 path is the task-specific V4 evaluator, not canonical `RuleV1` runtime.

| State | Actual object or condition | Producer | Transition |
|---|---|---|---|
| authority loaded | `EvaluatorAuthorityBundleV1` plus validated `RealPrivateNumericResolverV1` | `_load_public_authorities_v1`; `build_real_private_numeric_resolver_v1` | exact V4, registry, descriptor, split, and grant checks must pass |
| source census | retained and cross-source-isolated source events | `enumerate_real_full_census_v1` | each event is joined to every matching COMMON-42 descriptor |
| opportunity formed | `_RealOpportunityEnvelopeV1` | `enumerate_real_full_census_v1` | deterministic sort by physical row, relation binding, opportunity ID |
| source qualified | 5-row pre/post median step passes threshold, direction, and 0.8 stability checks | `execute_real_rule_v1` | mismatch is a hard execution error; incomplete source context abstains |
| target context available | 5-row baseline and 3-row response at the frozen horizon are complete | `execute_real_rule_v1` | missing context becomes `abstain` |
| expected response | response median delta strictly exceeds the target noise scale in the expected direction | `execute_real_rule_v1` | `evaluated_expected_response`; no alarm |
| anomalous response | the expected-direction response test fails | `execute_real_rule_v1` | `evaluated_anomaly`; alarm at the last response-window row |
| abstained | a formed opportunity lacks source or target boundary context | `_real_rule_result_v1` | no alarm and no decision index |
| system error | custody, authority, schema, source replay, or transition mismatch | fail-closed exception | never converted to PASS, FAIL, or ABSTAIN |

There is no per-row “source not triggered” result. Non-trigger timestamps never become opportunities. Source absence is therefore not equivalent to an evaluated normal result or to ABSTAIN.

Within each same-source single-link cluster whose adjacent candidates are at most 10 seconds apart, the census retains the largest absolute step amplitude. An exact-amplitude tie retains the earliest event index. Cross-source isolation is then applied within an inclusive ±2-second radius.

## Generic pseudocode

```text
for retained isolated source event in deterministic order:
    for COMMON descriptor matching source and source direction:
        verify authority, descriptor, frame, census, and ten references
        if source window unavailable: ABSTAIN
        replay the sustained-step predicate
        if predicate differs from census: SYSTEM ERROR
        read baseline [t-5, t) and response [t+h, t+h+3)
        if either window unavailable: ABSTAIN
        delta = median(response) - median(baseline)
        matched = delta > noise for increase, delta < -noise for decrease
        if matched: EXPECTED_RESPONSE, no alarm
        else: ANOMALY, alarm at t+h+2
```
