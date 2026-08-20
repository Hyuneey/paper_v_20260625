# Current project state

## Research in one paragraph

This project studies graph-guided agentic construction of verified rules for
explainable multivariate time-series anomaly detection. The current portfolio
is COMMON-42 for HAI 23.05 P1, with deterministic verification and LLM-free
runtime. Rule validity, execution authorization, and label-aware utility remain
separate authority layers.

## Current completed milestone

Utility Evaluator V1 R3 has a complete independent audit. The exact HAI INNER
feature and label payload has now also been reproducibly materialized from the
pinned official source authority. Both frozen hashes and sizes match, the
ignored local HAI binding is configured, and test2 payload access is zero.

## Current active task

None. Code-materialized HAI recovery stopped at the mandatory private numeric
authority binding gate before custody preflight.

## Latest blocker

`AUTHORIZATION_RECOVERY_BLOCKED_MAIN_PRIVATE_BINDING_MISSING`. Neither the MAIN
registry/locator pair nor the supplement registry/locator pair was present in
the approved local binding layer. This is a private-custody availability
blocker, not a HAI provenance, materialization, evaluator, contract, or
scientific blocker.

## Authorization boundary

Authorized now: public continuity maintenance and retention/revalidation of the
exact private HAI cache and ignored local HAI binding.

Not authorized: custody preflight, D1, D0, D2, detector, fusion, test2/OUTER,
recalibration, rule regeneration, metric changes, runtime LLM, or scientific
result generation. No private authority may be regenerated in this task.

## Exact next task

`NONE`. A new explicit task must establish the exact existing MAIN and
supplement private bindings without disclosure or regeneration before
authorization recovery can resume.

## Canonical evidence

- Materialization report: `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_AUTHORIZATION_CODE_MATERIALIZED_HAI_V1_MATERIALIZATION.json`
- Blocker: `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_AUTHORIZATION_CODE_MATERIALIZED_HAI_V1_BLOCKER.json`
- R3 independent receipt: `docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_INDEPENDENT_RECEIPT.json`

## No-claim boundary

Real utility has not executed. No real Attack-event recall, normal FAR,
D0/D1/D2 comparison, or detector result exists. No INNER authorization has
been issued.
