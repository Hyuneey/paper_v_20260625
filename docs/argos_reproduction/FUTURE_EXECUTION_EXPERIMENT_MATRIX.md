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
| E2X-S/V Inner selection and outer validation (`executed`, TASK-035B) | KPI inner then outer | Direct PA-free point/event metrics and paired KPI bootstrap | `20260715` for bootstrap | 146 frozen executable rules; 100-rule balanced panel before labels | Not applicable | Inner only | Outer only after committed arm freeze | `passed_multi_rule_outer_validation`; frozen compositions evaluated once on outer validation, no test claim |
| E2X-T Expanded sealed test (`not_run`, sealed, unauthorized) | Sealed KPI test | Not approved | Not approved | Not frozen for test | Not applicable | Frozen future selection only | Sealed one-way | No claim authorized |
| E3 Rule-only KPI test (`not_run`, sealed, unauthorized) | Sealed KPI test | Frozen rule predictions and predeclared metrics | Same deterministic rule and E2 freeze | E2 frozen hash | Not applicable | E2 validation freeze record | Sealed test, one-way | Rule-only result for the declared series only |
| E4 Detector-only baseline (`executed`, TASK-037B) | Generation fit, inner threshold, outer one-way; test sealed | Frozen detector scores/predictions for both LSTMAD variants | `20260723` | Not applicable | Frozen variant-specific artifacts; test absent | Inner threshold only | Outer executed once; test sealed | Detector provenance sensitivity, no winner selection |
| E5 FN fusion (`diagnostic TASK-037C frozen_pending; paper-faithful not_prepared`) | Inner then outer; test sealed | `max(detector, rule)` for diagnostic track | Inherited frozen artifacts | TASK-035B frozen arms | TASK-037B frozen detector predictions | No selection | Outer pending; test sealed | FN recovery and added-FP accounting, no superiority claim |
| E6 FP fusion (`diagnostic TASK-037C frozen_pending; paper-faithful not_prepared`) | Inner then outer; test sealed | `min(detector, rule)` for diagnostic track | Inherited frozen artifacts | TASK-035B frozen arms | TASK-037B frozen detector predictions | No selection | Outer pending; test sealed | FP removal and removed-TP accounting, no superiority claim |
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
gate. At that historical gate, this authorized TASK-035B planning only; the
separate TASK-035B protocol subsequently authorized E2X-S/V execution.

TASK-035B registered E2X-S and E2X-V with a label-independent ten-rule panel
per KPI, direct PA-free metrics, four fixed inner-selected OR arms, and a
commit-separated one-way outer run. E2X-T remains sealed and unauthorized.

E2X-S and E2X-V completed under TASK-035B. The full-inner gate retained 145 of
146 rules and at least 12 per KPI; the frozen 100-rule panel replayed
deterministically on inner and outer partitions. Coverage-3 OR increased macro
recall relative to Best-1 but decreased point F1 and precision and raised the
false-positive burden. This is outer-validation evidence only and does not
authorize E2X-T, a benchmark claim, or a superiority claim.

TASK-037A audited E4 detector provenance and froze E4/E5/E6 protocols without
running them. ARGOS identifies generic LSTMAD but does not disambiguate official
EasyTSAD `LSTMADalpha` and `LSTMADbeta`; both are retained as non-selected
co-primary provenance arms. Their isolated synthetic smoke passed. At the
TASK-037A milestone, real KPI training, outer validation, fusion and test were
all `not_run`.

TASK-037B executed E4 as a dual-arm detector-only experiment using both frozen
official LSTMAD variants. All twenty units completed generation-only fitting,
inner threshold freezing, deterministic outer replay and one-way outer
validation. Neither variant was selected as the ARGOS detector. E5/E6 remain
frozen but `not_run`, and all test partitions remain sealed.

TASK-037C freezes the complete diagnostic E5/E6 matrix: two detector variants,
four existing rule arms and exact binary max/min operators. All sixteen arms
must be retained, prediction hashes must be frozen before label access, and no
fusion arm or detector variant may be selected. Execution remains diagnostic
and does not constitute paper-faithful error-conditioned ARGOS reproduction.
