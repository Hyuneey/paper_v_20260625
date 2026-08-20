# Current project state

## Research in one paragraph

This project studies graph-guided agentic construction of verified rules for
explainable multivariate time-series anomaly detection. COMMON-42 on HAI 23.05
P1 remains frozen, deterministic, and LLM-free at runtime. Rule validity,
execution authorization, label-aware utility, and result-integrity audit remain
separate authority layers.

## Current completed milestone

The exact authorized D1 Rule-only INNER test1 experiment executed once. Its
label-blind full-census RulePrediction artifact and frozen metric outputs are
committed in Result Freeze Commit
`9fe9192c6da4e2d1f3c7a42ecdd28006e8534449`. The result has not yet passed
the required independent integrity audit.

## Authorization boundary

D1 execution authorization remains exact and was consumed without broadening.
D0, D2, detector, fusion, test2/OUTER, recalibration, rule regeneration,
metric modification, runtime LLM, and any retry remain unauthorized.

## Exact next task

`TASK-039E3-R2R-UTILITY-INNER-D1-RESULT-INTEGRITY-AUDIT-V1`. It must inspect
the exact frozen result bytes and must not rerun D1.

## Canonical evidence

- Authorization: `deb08014de20c398d2dcde046e14b505a65af2d52cb6eb309fc8188f020b5834`
- Execution Bridge Commit A: `936296cdcf9f5d87658a0c9993856ccc7d9222b2`
- Independent Audit Commit B: `c880042d1a49c12e2a6788d618bfb9b5491e1be0`
- Result Freeze Commit C: `9fe9192c6da4e2d1f3c7a42ecdd28006e8534449`
- RulePrediction artifact: `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`
- Execution run: `97bc0ef15508957d32427188205d7446fa58bc2234cade577d0bc93c3ce52e73`
- Result receipt: `0966c35ec6865ed9f97651092876b2ff67322f59daa8ff09a425614d28b74c8e`

## No-claim boundary

The D1 outputs are frozen facts pending independent arithmetic, custody,
label-independence, and full-census verification. They are not yet
scientifically accepted or interpreted. No D0/D1/D2 comparison or detector
result exists. `REAL_UTILITY_EXECUTION_AUTHORIZED` remains false inside the
frozen evaluator.
