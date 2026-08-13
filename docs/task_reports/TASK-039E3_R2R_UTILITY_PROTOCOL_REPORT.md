# TASK-039E3 R2R Utility Protocol Freeze

Status: `passed_task039e3_r2r_utility_protocol_freeze`

This is explicitly a **POST_RESULT_PROTOCOL_FREEZE**. It is not a pre-construction preregistration. No label values, attack intervals, HAI test feature values, utility outcomes, provider calls, or scientific calls were accessed or computed.

## Frozen scope

- Dataset: HAI 23.05, P1, 1-second sampling, manifest `5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2`.
- Utility view: `4445c98c0a22e4f53a5679b39b52a984adf342eb02fe893d5d53256ea2133e24`, derived from the frozen P1 preprocessing identity with second-level calibration disabled.
- INNER: test1/label-test1, split `30a7c88d6e0af5c37493237cc83b9520cbcd6f43c2dee7bb50ec3cac2668e7d0`.
- OUTER: test2/label-test2, split `9d76358ff109e4a6d2a712a1ff679c199d08e9cc92239160c8016e9efa063203`.
- SEALED: not materialized and not authorized.
- Coordinates: test1 `[0,54000)`, purge `[54000,54120)`, test2 `[54120,284520)`.

The offline candidate interpreter uses only frozen normal-derived references. It does not instantiate Rule v2, production runtime, deployment, or winner authority. Source steps use the exact five-second pre/post medians, `>=` threshold and `>=0.80` stability, ten-second single-link refractory clustering, and inclusive two-second cross-source isolation. Target responses use a five-second baseline and three-second response window. The decision timestamp is `event_index + h + 2`.

## Scientific comparison

The exact executable-signature audit freezes T0/T1/T1-B as one traceable `COMMON-42` portfolio. All 39 accepted T2 cells match the same per-relation executable projection; T2 differs only through three preserved `no_rule` cells. Identical projections are not treated as independent predictions.

The co-primary endpoints are AttackEvent recall and normal false-alarm AlarmEpisode rate per hour. Point adjustment and weighted utility scores are prohibited. Exact binomial and exact Poisson confidence intervals are frozen; the only primary paired comparison is COMMON-42 versus T2 event coverage, with exact McNemar evidence supplementary.

Utility-driven no-op selection and detector integration remain deferred. INNER is development evidence; OUTER is one-way frozen replay and cannot be cancelled because a valid INNER result is unfavorable. SEALED is outside the current MVP.

## Authority

Protocol bundle: `189c662b83e82ed47137d7e67f52ff97580662ef65e696a5d5715d2dddaae86d`

Protocol receipt: `f6db67c4ec4c3f64f0acc8031e27f583fc3192029170184e42dd721dbaf15949`

Utility protocol is frozen but not independently audited. Utility evaluator implementation and utility execution remain false. The only next task is `TASK-039E3-R2R-UTILITY-PROTOCOL-INDEPENDENT-AUDIT`.
