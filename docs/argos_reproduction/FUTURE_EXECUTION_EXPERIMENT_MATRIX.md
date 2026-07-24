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
| E5 FN fusion (`diagnostic TASK-037C executed; paper-faithful not_prepared`) | Inner and outer executed; test sealed | `max(detector, rule)` for diagnostic track | Inherited frozen artifacts | TASK-035B frozen arms | TASK-037B frozen detector predictions | No selection | Outer executed once; test sealed | FN recovery and added-FP accounting, no superiority claim |
| E6 FP fusion (`diagnostic TASK-037C executed; paper-faithful not_prepared`) | Inner and outer executed; test sealed | `min(detector, rule)` for diagnostic track | Inherited frozen artifacts | TASK-035B frozen arms | TASK-037B frozen detector predictions | No selection | Outer executed once; test sealed | FP removal and removed-TP accounting, no superiority claim |
| E7 RepairAgent effect (`executed`, TASK-038B) | Generation runtime evidence only for Repair; no outer/test | Before/after extraction, static and runtime-contract recovery | Inherited frozen inputs | Initial and repaired hashes frozen | Matching frozen detector lineage only | Generation value-only runtime errors | None until later committed freeze | Repair operability and cost only |
| E8 ReviewAgent component effect (`executed`, TASK-038C; outer follow-up executed in TASK-038E) | Inner-only Review followed by pre-registered, previously exposed outer validation; test sealed | Direct PA-free paired branch diagnostics under frozen max/min semantics | Inherited frozen inputs; TASK-038E bootstrap `20260726` | Initial/repaired/reviewed hashes frozen | Matching frozen TASK-037B detector prediction | Inner-only TASK-038D selection | TASK-038E outer completed after exact registry; sealed test not run | Component-wise descriptive outer transfer, not superiority or confirmation |
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
frozen as non-selective diagnostics; TASK-037C subsequently executed their
inner and outer matrices, while all test partitions remain sealed.

TASK-037C executed the complete diagnostic E5/E6 matrix: two detector variants,
four existing rule arms and exact binary max/min operators. All sixteen arms
were retained across ten KPI series, and all inner and outer prediction hashes
were frozen before label access. No fusion arm or detector variant was
selected. The result remains diagnostic and does not constitute paper-faithful
error-conditioned ARGOS reproduction.

TASK-037D completed the paper-aligned error-conditioned generation stage for
both LSTMAD variants. It used generation FN/TN evidence for FN rules and
generation FP/TP evidence for FP rules through 96 independent one-shot
requests. All 96 responses produced static-valid rules, 83 passed both
value-only runtime contracts, and the frozen cohort adequacy gate passed.
TASK-037E subsequently completed rule selection and inner/outer Aggregator
evaluation. All sealed tests remain unrun and unauthorized.

TASK-037E executed the follow-up error-conditioned selection and full Aggregator
protocol. All 83 rules completed deterministic inner replay. Independent
selection retained 19 FN rules and one FN no-op, plus two FP rules and 18 FP
no-ops. The 21 selected non-no-op rules completed deterministic outer replay,
and detector-only, detector-plus-FN, detector-plus-FP, and FP-then-FN full
Aggregator predictions were frozen before outer labels were loaded. The status
is `passed_error_conditioned_full_aggregator_outer_validation`. The shared
outer partition was previously exposed, so the result is descriptive follow-up
validation rather than untouched confirmation; every sealed test remains
unauthorized.

TASK-038A froze the E7/E8 component protocol without executing either
experiment. The complete 96-slot TASK-037D population maps to 384 immutable
`A0`/`A1`/`A2`/`A3` branch records. Repair is limited to the 13 frozen
runtime-failed rules, Review is executable-rule and inner-only, and every
transformation is bounded to one call without retry. Real provider calls,
generated-code execution, outer access, and sealed-test access all remain
unperformed and unauthorized. TASK-038B requires a separate execution
authorization.

TASK-038B separately authorizes the bounded E7 Repair operability experiment.
Its immutable denominator is the thirteen TASK-037D static-valid runtime
failures. Failure replay and the exact no-retry call manifest must be committed
before provider access. Review, detection metrics, inner/outer execution,
fusion, and every sealed test remain prohibited.

TASK-038B completed E7 with status
`passed_repair_agent_operability_experiment`. All 13 original failures were
reproduced, all 13 one-shot Repair responses were extracted and statically
valid, and all 13 repaired rules passed deterministic two-run target and
contrast contracts. E8 Review remains not run; inner/outer detection metrics,
fusion, and all sealed tests remain prohibited and unexecuted.

TASK-038C separately authorizes E8 as an inner-only Review experiment over 83
executable `A2` parents and 96 executable `A3` parents. Parent predictions,
direct PA-free triggers, bounded regression evidence and the exact call
manifest must freeze before provider access. Each triggered branch receives at
most one independent Review call. Outer access, sealed-test access, branch
selection, RepairAgent calls and DetectionAgent calls remain prohibited.

TASK-038C completed E8 with status
`passed_review_agent_inner_branch_experiment`. The direct PA-free trigger
authorized 77 calls and froze 102 `no_review_needed` identities. All responses
were static-valid and 76 revisions completed deterministic generation and
full-inner replay. The reported effects are inner-only. Branch selection,
outer execution, Full Aggregator comparison and every sealed test remain
unperformed and unauthorized.

TASK-038D completed the branch-specific inner selection freeze with status
`passed_four_branch_selection_freeze`. The immutable A0-A3 executable-output
counts were 83, 96, 82 and 96. All 357 prediction references froze before
inner-label access, and the 160 no-op-aware FN/FP units terminated. A0
reproduced TASK-037E exactly.

TASK-038E completed the previously exposed one-way branch comparison with
status `passed_four_branch_outer_comparison`. The pre-registered 249 logical
records mapped to 146 physical units; 125 new units completed exact two-run
rootless-container replay and 21 exact TASK-037E predictions were reused.
All 320 branch arms, 76 Review pairs and 13 Repair utility predictions froze
before outer-label access. A0 reproduced TASK-037E exactly. No provider/agent
call, fallback, reselection, detector change, or sealed-test access occurred.
The results are descriptive component evidence only; every sealed test remains
unauthorized.

TASK-038F synthesized committed aggregate evidence only and completed with
status `passed_argos_methodological_validity_synthesis`. The overall
classification is `partial_methodological_support`, and the recommendation is
`freeze_ARGOS_reference_track`. No new experiment, provider/agent call,
detector/rule execution, private artifact read, outer access, or sealed-test
access occurred. The reference track is frozen against prompt/model tuning,
new branch selection, detector-variant choice, and exposed-outer result
improvement. A professor-approved joint sealed confirmation remains a separate
optional preregistration; the recommended default is to preserve it and move
the primary effort to the proposed SWaT method.
