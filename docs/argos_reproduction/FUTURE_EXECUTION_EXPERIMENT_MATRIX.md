# Future ARGOS Execution Experiment Matrix

## Freeze policy

Every experiment requires a separate approval and immutable input manifest.
Hashes marked `required before run` must be populated before execution. Test
data cannot be used for rule, detector, threshold, or candidate selection.

| Experiment | Dataset split | Metric or output | Random seed | Rule hash | Detector artifact hash | Selection data | Final evaluation data | Allowed claim |
|---|---|---|---|---|---|---|---|---|
| E1 Rule candidate runtime smoke (`executed`, TASK-033) | Synthetic non-KPI only | Shape, binary domain, exceptions | Fixed in fixture manifest | `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659` | Not applicable | None | None | Container/runtime plumbing only; `passed_runtime_smoke` |
| E2 Rule-only KPI validation (`executed`, TASK-034) | KPI validation | Prediction-label artifact; PA-free diagnostics plus separately labeled paper-faithful metrics | Deterministic frozen rule | `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659` | Not applicable | Validation only | None; test sealed | `passed_validation_feasibility`; validation feasibility only |
| E3 Rule-only KPI test (`not_run`, sealed, unauthorized) | Sealed KPI test | Frozen rule predictions and predeclared metrics | Same deterministic rule and E2 freeze | E2 frozen hash | Not applicable | E2 validation freeze record | Sealed test, one-way | Rule-only result for the declared series only |
| E4 Detector-only baseline | Same KPI train/validation/test protocol | Frozen detector prediction labels | Required before detector run | Not applicable | Required before fusion | Train/validation only | Same sealed test | Detector baseline under the frozen protocol |
| E5 FN fusion | Validation then sealed test | `max(detector, rule)` predictions and predeclared metrics | Inherited frozen artifacts | Required | Required | Validation only | Same sealed test | FN-composition result, no universal superiority claim |
| E6 FP fusion | Validation then sealed test | `min(detector, rule)` predictions and predeclared metrics | Inherited frozen artifacts | Required | Required | Validation only | Same sealed test | FP-composition result, no universal superiority claim |
| E7 RepairAgent effect | KPI train/validation; no test during repair | Before/after syntax, runtime, and frozen validation comparison | Required before run | Both hashes required | Not applicable | Train error plus validation protocol | None until candidate frozen | Repair effect on the approved fixture only |
| E8 ReviewAgent selection effect | KPI train/validation | Candidate versus selected validation result | Required before run | Candidate and selected hashes | Optional only for predeclared combined arm | Validation only | None until selection frozen | Selection behavior, not test improvement |
| E9 Random-seed sensitivity | Train/validation first; test only after one predeclared aggregation policy | Distribution across frozen seeds | Seed list required before run | Hash per seed | Hash per detector run | Train/validation only | One sealed protocol after freeze | Sensitivity under declared seeds |
| E10 Multivariate extension readiness | Approved multivariate train/calibration/validation | Interface and feasibility checks | Required before run | DSL artifact hashes | Candidate/detector hashes as applicable | No final test | No final test until separate gate | Readiness only after E1-E8 evidence |

## Required manifest fields

Each later run must record dataset edition and split manifest, metric protocol,
seed, code commit, rule hash, detector artifact hash, selection-data IDs,
final-evaluation-data ID, threshold provenance, execution approval, and allowed
claim text. E3, E5, and E6 must share the same sealed-test boundaries and must
not retune after access.

## Current status

At the TASK-029 freeze, **All experiments are `not_run`**. That statement is
retained as the historical non-executing-audit status.

E1 was executed under TASK-033 with synthetic non-KPI inputs only and passed its
runtime-plumbing gate. E2-E10 remain `not_run`. TASK-033 reports no anomaly-
detection performance and does not authorize KPI, detector, fusion, RepairAgent,
ReviewAgent, or provider execution.

TASK-034 executed E2 from clean commit `b81468c4` and passed the validation
feasibility gate with deterministic fresh-container predictions. The direct
metrics are PA-free validation diagnostics; ARGOS label-aware metrics are
supplementary validation diagnostics. E3 remains sealed, unexecuted, and
unauthorized.
