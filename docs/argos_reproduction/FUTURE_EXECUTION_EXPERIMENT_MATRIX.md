# Future ARGOS Execution Experiment Matrix

## Freeze policy

Every experiment requires a separate approval and immutable input manifest.
Hashes marked `required before run` must be populated before execution. Test
data cannot be used for rule, detector, threshold, or candidate selection.

| Experiment | Dataset split | Metric or output | Random seed | Rule hash | Detector artifact hash | Selection data | Final evaluation data | Allowed claim |
|---|---|---|---|---|---|---|---|---|
| E1 Rule candidate runtime smoke (`executed`, TASK-033) | Synthetic non-KPI only | Shape, binary domain, exceptions | Fixed in fixture manifest | `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659` | Not applicable | None | None | Container/runtime plumbing only; `passed_runtime_smoke` |
| E2 Rule-only KPI validation (`executed`, TASK-034) | KPI validation | Prediction-label artifact; PA-free diagnostics plus separately labeled paper-faithful metrics | Deterministic frozen rule | `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659` | Not applicable | Validation only | None; test sealed | `passed_validation_feasibility`; validation feasibility only |
| E2X-G Expanded generation cohort (`executed`, insufficient yield, TASK-035A) | KPI generation prefixes only | Response, static, runtime-contract, yield, and diversity statuses; no performance metric | Provider seed unsupported | 100 frozen slots; 55 executable | Not applicable | Generation labels in pre-registered anchors only | None | Cohort construction and runtime plumbing only |
| E2X-GR Balanced output-budget remediation (`executed`, passed, TASK-035AR) | Same KPI generation prefixes and anchors | Response, extraction, runtime-contract yield, balance, and duplicate hashes; no performance metric | Provider seed unsupported | 100 new frozen slots; 91 executable | Not applicable | Same pre-registered anchors only | None | Output-budget generation-operability comparison only |
| E2X-S/V Inner selection and outer validation (`pre-registered`, TASK-035B Commit A) | KPI inner then outer | Direct PA-free point/event metrics and paired KPI bootstrap | `20260715` for bootstrap | 146 frozen executable rules; 100-rule balanced panel before labels | Not applicable | Inner only | Outer only after committed arm freeze | Frozen compositions may be evaluated once on outer validation; no test claim |
| E2X-T Expanded sealed test (`not_run`, sealed, unauthorized) | Sealed KPI test | Not approved | Not approved | Not frozen for test | Not applicable | Frozen future selection only | Sealed one-way | No claim authorized |
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

TASK-035A authorizes E2X-G only. E2X-S and E2X-V remain unexecuted, E2X-T and
E3 remain sealed and unauthorized, and E4 remains deferred until a separate
review of E2X-S/V. TASK-035A reports no KPI validation performance.

E2X-G executed 100 one-shot slots without retry and ended
`insufficient_rule_yield`: 84 non-empty responses, 61 static-valid rules, and
55 container-executable rules. This does not authorize replacement calls or
E2X-S/V.

TASK-035AR executed a separate balanced E2X-GR cohort with replicates 3 and 4
for every original anchor. Its only provider change was the 6,000-token output
budget. All 100 responses were non-empty and static-valid, 91 passed the
runtime contract, and the combined 146-rule cohort passed the frozen balance
gate. This authorizes TASK-035B planning only; it is not a performance result.

TASK-035B pre-registers E2X-S and E2X-V with a label-independent ten-rule panel
per KPI, direct PA-free metrics, four fixed inner-selected OR arms, and a
commit-separated one-way outer run. E2X-T remains sealed and unauthorized.
