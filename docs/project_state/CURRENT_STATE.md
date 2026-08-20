# Current project state

## Research in one paragraph

This project studies graph-guided agentic construction of verified rules for
explainable multivariate time-series anomaly detection. HAI 23.05 P1 normal
evidence and metadata support candidate relations, deterministic calibration,
bounded rule construction, deterministic verification, and an LLM-free
runtime. The current utility portfolio is COMMON-42; validity and utility are
separate authority layers.

## Current completed milestone

Utility Evaluator V1 R3 completed full independent re-audit at
`1a961eadc4813acfc959580c0558f0bf33aa5c7c`. Its independent receipt is
`6f671aff17ea193ebf862af0739ee0bee22634f3f337944c14c90172acde34e0`.

## Current active task

`TASK-039E3-R2R-UTILITY-INNER-EXECUTION-AUTHORIZATION-V1-PATH-SILENT-RECOVERY`
preserves the passed authorization contract and independent audit, performs one
path-silent custody preflight, and may issue only the exact INNER D1 grant.

## Latest blocker

The prior authorization task blocked because one private custody path appeared
in coordinator output while recovering an absent locator binding. This was an
operational privacy failure, not a scientific, evaluator, or contract failure.
No custody file or scientific input was opened and no authorization was issued.

## Authorization boundary

Authorized now: public replay, continuity bootstrap, immutable synthetic/static
authorization tests, and the bounded coordinator-only custody recovery defined
by the active task.

Not authorized now: D1 execution, D0, D2, detector, fusion, test2/OUTER,
recalibration, rule regeneration, metric changes, runtime LLM, or scientific
result generation.

## Exact next task after PASS

`TASK-039E3-R2R-UTILITY-INNER-D1-EXECUTION-V1`

## Canonical receipts to replay

- R3 independent receipt: `docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_INDEPENDENT_RECEIPT.json`
- R3 completion audit: `docs/task_reports/TASK-039E3_R2R_UTILITY_EVALUATOR_V1_R3_INDEPENDENT_COMPLETION_AUDIT.json`
- Historical authorization blocker: `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_EXECUTION_AUTHORIZATION_V1_BLOCKER.json`

## No-claim boundary

The evaluator implementation is independently audited. Real utility has not
executed. No real Attack-event recall, normal FAR, D0/D1/D2 comparison, or
detector result exists.
