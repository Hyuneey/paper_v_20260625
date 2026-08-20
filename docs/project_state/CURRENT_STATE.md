# Current project state

## Research in one paragraph

This project studies graph-guided agentic construction of verified rules for
explainable multivariate time-series anomaly detection. COMMON-42 on HAI 23.05
P1 remains frozen, deterministic, and LLM-free at runtime. Rule validity,
execution authorization, and label-aware utility remain separate layers.

## Current completed milestone

The portable INNER preflight failure was localized and closed. The exact MAIN
and supplement registries and both test1 assets passed custody preflight. One
typed authorization was issued for D1 Rule-only INNER test1 under control
revision `R2_PORTABLE_PREFLIGHT`.

## Root cause

`CLASS_G_AUTHORIZATION_PREFLIGHT_LOGIC`: the authorization preflight invoked a
two-input canonical MAIN authority builder without its frozen public inputs.
The registry itself was exact. The bounded repair supplies those two committed,
self-hashed public documents; no scientific authority or formula changed.

## Authorization boundary

Authorized: the next task may consume the exact committed authorization
`deb08014de20c398d2dcde046e14b505a65af2d52cb6eb309fc8188f020b5834`
for COMMON-42 D1 Rule-only INNER test1.

Not authorized: D0, D2, detector, fusion, test2/OUTER, recalibration, rule
regeneration, metric modification, runtime LLM, or any alternate scope.

## Exact next task

`TASK-039E3-R2R-UTILITY-INNER-D1-EXECUTION-V1`. It must consume—not recreate—
the issued authorization, keep test2 sealed, execute D1 once, then stop for a
separate result-integrity audit.

## Canonical evidence

- Authorization report commit: `7df8edf24993bf42401b487c56a188ce7546da91`
- Custody preflight: `3acff12cb2135b86539720e792d6e01075808ea84b6939b06909d397b1b43129`
- Authorization: `deb08014de20c398d2dcde046e14b505a65af2d52cb6eb309fc8188f020b5834`
- Final receipt: `080823c300b3afc8b4660cf48dfc55b134ae05d599f1f851322710b20ebc1ab1`

## No-claim boundary

D1 has not executed. No real Attack-event recall, normal FAR, D0/D1/D2
comparison, or detector result exists. `REAL_UTILITY_EXECUTION_AUTHORIZED`
remains false in the frozen evaluator.
