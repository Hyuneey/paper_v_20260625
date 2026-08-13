# TASK-039E3 R2R Utility Feasibility and Authorization Gate

Status: `passed_task039e3_r2r_utility_feasibility_and_authorization_gate`

## Decision

Utility remains essential for establishing whether the frozen continuous-step semantics have anomaly-detection value and for measuring the cost/coverage effect of T2's three `no_rule` outcomes. The current repository does not contain an exact, audited TASK-039E3 utility protocol. The defensible classification is therefore `UTILITY_PROTOCOL_FREEZE_REQUIRED`; utility execution authorization is false.

## What was already committed

Before the result became evaluable, v6 froze the validity/utility separation, utility objective categories, inner/outer/sealed split roles, exact operation permissions, inner-only governance, and construction `no_rule` semantics. It explicitly left metric formulas, denominators, detector endpoints, process aggregation, outer exposure, and sealed execution open. Legacy SWaT and ARGOS metric implementations are not current HAI R2R commitments.

## Data readiness

The HAI 23.05 dataset manifest declares label availability and 284,400 labeled test observations at dataset level. The only materialized TASK-039BR2 splits are normal candidate fit, normal relation calibration, and normal guard. No `INNER_UTILITY`, `OUTER_VALIDATION`, or `SEALED_EVALUATION` manifest exists, so no role-bound range, row denominator, purge, view, or sealed status is ready.

The history audit found one authorized TASK-039A label-value access for provenance alignment/domain verification only. It found no HAI utility-role label access and no unauthorized or ambiguous HAI label-value access. This gate read metadata only.

## Evaluator feasibility

No exact continuous-step utility evaluator exists. A separately scoped `OFFLINE_CANDIDATE_UTILITY_INTERPRETER` is conditionally feasible without production Rule v2 or runtime authority. It must resolve only frozen normal-derived references, execute the frozen continuous-step semantics, preserve T2 `no_rule`, use identical preprocessing for all arms, and emit utility-only custody.

The closed verifier makes accepted T0, T1, and selected T1-B proposals executable-semantic equivalents for each relation. Utility can test the shared semantics, but it cannot demonstrate an LLM structural-choice benefit among those arms. T2 differs through three `no_rule` cells. Direct-number outputs remain isolated and cannot tune or replace deterministic parameters.

## Required next freeze

Before any label access, freeze the utility split, label boundary, offline interpreter, primary unit, no-rule scoring and denominator, point/event matching, metrics, aggregation, normal-only threshold resolution, paired statistics, artifact custody, and result authority. That protocol must disclose its post-result timing and receive an independent audit before utility authorization.

Next task only: `TASK-039E3-R2R-UTILITY-PROTOCOL-FREEZE`.
