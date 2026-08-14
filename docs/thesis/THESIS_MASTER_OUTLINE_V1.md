# Thesis Master Outline V1

Status: `FROZEN_FOR_MASTER_DRAFT_V1`

Each subsection below has a defined purpose, RQ/claim role, and evidence or
visual requirement. Results stay in Chapter 6; earlier chapters may explain
protocols and anticipated measures but must not reveal outcomes prematurely.

## Chapter 1 — Introduction

| Section | Purpose | RQ/claim served | Required evidence/table/figure |
|---|---|---|---|
| 1.1 CPS anomaly-detection context | Motivate interpretable multivariate relation rules as a complement to opaque detection | Context for all RQs | Literature only; no result claim |
| 1.2 Construction problem | Explain why evidence binding, numeric authority, and independent verification are needed | RQ1/RQ3; C1/C2/C3 | Conceptual evidence-to-admission diagram |
| 1.3 Research gap | Distinguish bounded rule construction from unconstrained generation and from detector evaluation | All RQs | Related-work synthesis |
| 1.4 Objective and scope | State HAI P1, continuous-step delayed-response family, construction-validity endpoint, and utility exclusion | Claim boundary | Scope table |
| 1.5 Research questions | Present RQ1–RQ3 and secondary RQ4 exactly | All | RQ-to-evidence table |
| 1.6 Contributions | State C1–C4 at the construction/governance layers | C1–C4 | Contribution-to-RQ matrix |
| 1.7 Study boundary | State that utility, detector integration, Rule v2/runtime, deployment, and winner selection were not evaluated | Prevent overclaim | No figure required |
| 1.8 Thesis organization | Guide the reader through Chapters 2–8 | Navigation | Chapter map |

## Chapter 2 — Related Work

| Section | Purpose | RQ/claim served | Required evidence/table/figure |
|---|---|---|---|
| 2.1 Multivariate CPS anomaly detection | Position relation rules within CPS monitoring | Application context | Literature taxonomy |
| 2.2 Explainable and rule-based anomaly methods | Review interpretable rule representations and governance needs | C1/C3 context | Comparison table with claim scope |
| 2.3 Relation and graph candidate discovery | Review metadata, statistical, and graph-based candidate evidence | RQ1; C1 | Method-family comparison; avoid causal wording |
| 2.4 Normal-data relation profiling | Review normal-only evidence and delayed-response patterns | RQ1; C1/C2 | Relation-evidence taxonomy |
| 2.5 LLM-assisted structured construction | Review constrained structured generation versus unconstrained rule authoring | RQ2; C4 | Capability/boundary table |
| 2.6 Verification and fail-closed governance | Review deterministic verification, rejection, and explicit terminal states | RQ4; C3 | Governance-state comparison |
| 2.7 Numerical parameter authority | Review calibration versus direct generated numerics | RQ3; C2 | Calibration-source comparison |
| 2.8 Research gap summary | Show the missing integration of evidence, calibration, bounded construction, and independent admission | C1–C4 | Gap-to-contribution table |

Related work must not claim that this thesis produced detector-performance or
runtime results.

## Chapter 3 — Problem Formulation

| Section | Purpose | RQ/claim served | Required evidence/table/figure |
|---|---|---|---|
| 3.1 Dataset and process scope | Define HAI 23.05 P1, one-second sampling, and bounded process scope | Scope for all RQs | Dataset/process authority table |
| 3.2 Relation family and notation | Define source, target, directions, delay horizon, and continuous-step delayed response | RQ1 | Synthetic relation schematic |
| 3.3 Scientific units and denominators | Distinguish pair, directional relation, proposal, provider call, and relation-arm cell | RQ1/RQ2 | Unit/denominator table |
| 3.4 Evidence-to-rule problem | Formalize transformation from confirmed relation plus references to structured proposal | RQ1; C1 | Input/output formalism |
| 3.5 Numeric-authority problem | Define authoritative reference roles and prohibit generated numeric authority | RQ3; C2 | Numeric-role diagram |
| 3.6 Construction strategies | Define T0/T1/T1-B/T2 under a common contract | RQ2; C4 | Arm policy matrix |
| 3.7 Verification and outcome states | Define admissible, rejected, accepted, `no_rule`, provider failure, `no_op`, and abstain | RQ4; C3 | State-transition diagram |
| 3.8 Evaluation constructs | Separate construction validity, robustness, call cost, utility, and runtime authority | All | Construct/authority matrix |
| 3.9 Research questions and evaluation objectives | Connect RQs to observable endpoints | All | RQ-endpoint table |
| 3.10 Scope exclusions | Exclude utility, detector improvement, causality, production runtime, and winner claims | Claim boundary | No figure required |

## Chapter 4 — Proposed Framework

| Section | Purpose | RQ/claim served | Required evidence/table/figure |
|---|---|---|---|
| 4.1 Framework overview | Present the seven-stage evidence-to-admission pipeline | All; C1–C4 | Primary architecture figure |
| 4.2 Candidate universe | Define the frozen P1 source-target universe | RQ1; C1 | Universe summary |
| 4.3 Candidate discovery | Explain META, STAT, GDN, and unscored provenance-preserving integration | RQ1; C1 | Candidate-method contract table |
| 4.3.1 META | Define metadata/manual evidence and claim limits | RQ1 context | Input/authority row |
| 4.3.2 STAT | Define normal-data lagged change-correlation evidence | RQ1 context | Statistic/horizon definition |
| 4.3.3 GDN | Define upstream-aligned learned-graph candidate evidence | RQ1 context | Seed/ranking definition |
| 4.3.4 Integration | Define exact de-duplication and no merged score | RQ1; C1 | Provenance-union diagram |
| 4.4 Normal relation profiling | Define arm-blind source-event and response fitting on train1/train2 | RQ1; C1/C2 | Profiling flow |
| 4.5 One-way confirmation | Define frozen train3 replay without adaptation | RQ1; C1/C2 | Fit-to-confirmation flow |
| 4.6 Evidence and numeric materialization | Bind relation evidence and normal-derived references | RQ1/RQ3; C2 | Numeric-reference table |
| 4.7 Common proposal contract | Define bounded execution-relevant fields and prohibited literals/variables | RQ1; C1/C2 | Schema summary |
| 4.8 Construction arms | Explain common inputs and policy differences | RQ2; C4 | Four-arm architecture |
| 4.8.1 T0 | Deterministic template baseline | RQ2 | Policy row |
| 4.8.2 T1 | One-shot bounded LLM construction | RQ2 | Policy row |
| 4.8.3 T1-B | Three independent calls and lowest-admissible-index selection | RQ2 | Selection flow |
| 4.8.4 T2 | Bounded verifier-feedback controller | RQ2/RQ4 | Controller state diagram |
| 4.9 Deterministic verifier | Enumerate schema, identity, evidence, direction, horizon, reference, literal, and variable checks | RQ1/RQ4; C3 | Verification checklist |
| 4.10 Fail-closed admission | Separate accepted candidate and `no_rule` from other states | RQ4; C3 | Outcome-state table |
| 4.11 Direct-number experiment | Define direct numeric estimation as a calibration-authority ablation | RQ3; C2 | Error formula/role table |
| 4.12 Downstream authority boundary | Show labeled utility and LLM-free runtime outside completed empirical scope | Boundary | Dashed out-of-scope box |

## Chapter 5 — Experimental Design

| Section | Purpose | RQ/claim served | Required evidence/table/figure |
|---|---|---|---|
| 5.1 Frozen dataset/process/cohort | Bind HAI P1 and final 42-direction cohort | All | Experimental binding table |
| 5.2 Sequential normal-data roles | Explain train1/train2 profiling and one-way train3 confirmation | RQ1; internal validity | Data-role timeline |
| 5.3 Candidate experiment | Specify top-20 policies and unscored integration | RQ1 | Candidate design table |
| 5.4 Relation fitting and confirmation | Specify D1/D2 gates and no-adaptation rule | RQ1 | Stage-gate table |
| 5.5 Construction comparability | Bind common evidence, schema, model-visible request, model, and sampling contract | RQ2 | Fairness matrix |
| 5.6 Call budgets and stopping | Define T0=0, T1=1, T1-B=3, and bounded T2 calls | RQ2 | Budget table |
| 5.7 T1-B sampling/selection | Define independent draws and deterministic selected index | RQ2; claim C | Selection pseudocode |
| 5.8 T2 controller | Define repairability, revise, retrieve, and `no_rule` | RQ2/RQ4; claims D/G | Action matrix |
| 5.9 Construction-validity endpoint | Define accepted rate, `no_rule`, and N=42 relation denominator | RQ1/RQ2/RQ4 | Endpoint table |
| 5.10 Paired comparisons | Define concordance, discordance, percentage-point effects, and supplementary exact test | RQ2 | Paired 2×2 design |
| 5.11 Robustness/call efficiency | Define cumulative yield, recovery, parse handling, calls/accepted, accepted/call | RQ2 | Measure table |
| 5.12 T2 activation analysis | Define eligible/action/follow-up/recovery counts | RQ2 | Controller metric table |
| 5.13 Direct-number analysis | Define normalized error, type-7 quantiles, population SD, exceedances | RQ3 | Statistical formula table |
| 5.14 Origin subgroup | Define overlapping exploratory membership | Claim H | Caveat table |
| 5.15 Statistical hygiene | Preserve all 42 relations and separate relation/call denominators | RQ2 | Denominator table |
| 5.16 Reproducibility and custody | Describe frozen artifacts, hashes, public/private separation, and no provider rerun | All | Authority-chain figure |
| 5.17 Utility stopping boundary | Record post-result/pre-label chronology and why execution remained unauthorized | Limitation | Governance timeline; no utility table |

## Chapter 6 — Results

| Section | Purpose | RQ/claim served | Required evidence/table/figure |
|---|---|---|---|
| 6.1 Candidate discovery | Report three top-20 lists, union, and overlaps | RQ1; C1 | Table 1 |
| 6.2 Normal relation fitting | Report 47 pairs, 25 supported pairs, and 45 supported directions | RQ1; C1 | Table 2 |
| 6.3 Relation confirmation | Report 42 confirmed directions and three conflicts | RQ1; C1/C2 | Table 2; optional attrition figure |
| 6.4 Rule-construction validity | Report 42/42/42/39 acceptance and paired comparisons | RQ1/RQ2/RQ4; A/B/D/G | Table 3 |
| 6.5 Robustness and call efficiency | Report T1-B behavior, T2 controller, and call frontier | RQ2/RQ4; C/D/E/G | Tables 4–6 |
| 6.6 Direct-number experiment | Report role-wise numeric errors | RQ3; F | Table 7 |
| 6.7 Candidate-origin subgroup | Report overlapping descriptive membership | H | Supplementary origin table |
| 6.8 Utility evaluation boundary | Report chronology and zero label/test/utility access | Limitation; boundary | No utility-performance table |

Chapter 6 may reuse the already-authorized prose in `THESIS_RESULTS_DRAFT.md`.

## Chapter 7 — Discussion

| Section | Purpose | RQ/claim served | Required evidence/table/figure |
|---|---|---|---|
| 7.1 RQ1: construction feasibility | Interpret the complete evidence-to-construction chain | RQ1; A/B; C1 | Tables 1–3 |
| 7.2 RQ2: construction strategies | Interpret T1 one-shot feasibility, T1-B limited robustness, and negative T2 result | RQ2; C/D/E; C4 | Tables 3–6 |
| 7.3 Validity ceiling and T0 saturation | Explain limited endpoint discrimination without declaring a winner | RQ1/RQ2 | Table 3 |
| 7.4 RQ3: deterministic calibration | Interpret schema-valid yet inaccurate Direct-number outputs | RQ3; F; C2 | Table 7 |
| 7.5 RQ4: fail-closed admission | Interpret three invalid proposals excluded as `no_rule` | RQ4; G; C3 | Tables 3 and 6 |
| 7.6 Candidate-origin result | Preserve `INCONCLUSIVE` exploratory status | H | Supplementary table |
| 7.7 Utility absence | Explain why utility was motivated but not evaluated | Limitation | Governance timeline |
| 7.8 Limitations and threats | Cover construct, internal, external, and statistical threats | All | Threat matrix |
| 7.9 Implications and future work | Separate supported thesis implications from optional future research | C1–C4 | No new result |

Discussion branches remain C (`T2 < T1-B` on observed construction validity)
and D (validity ceiling / discrimination limitation). T2 must not be rescued
narratively.

## Chapter 8 — Conclusion

| Section | Purpose | RQ/claim served | Required evidence/table/figure |
|---|---|---|---|
| 8.1 Answers to RQs | Give one bounded answer per RQ | RQ1–RQ4 | RQ answer table |
| 8.2 Contributions | Restate C1–C4 with empirical/methodological distinction | C1–C4 | Contribution matrix |
| 8.3 Limitations | State utility, runtime, detector, process, provider, and ceiling limits | Claim boundary | No figure required |
| 8.4 Future work | Make utility/runtime/external validation conditional and separately authorized | Boundary | No promised positive result |
| 8.5 Closing statement | End at governed construction and deterministic calibration | Overall thesis | No new claim |

## Abstract placeholder

The final abstract remains intentionally unwritten. The master draft may carry
only an abstract claim inventory containing allowed claims, unsupported claims,
and material qualifications from `THESIS_RESULT_CLAIM_MATRIX.md`.
