# TASK-039E3 R2R Scientific Result Analysis

Status: `passed_task039e3_r2r_scientific_result_analysis`

The complete 42-relation result was analyzed without exclusions. T0, T1, and T1-B each accepted 42/42 relations; T2 accepted 39/42. In every T2 discordance, T0, T1, and T1-B accepted the relation. Exact paired inference is supplementary: the three discordances all favor the non-T2 arm, with two-sided exact p = 0.25.

Initial request hashes were identical across T1, all three T1-B calls, and T2 call 1 for all 42 relations. T1-B used 126 calls and recovered one first-draw rejection only on call 3; T2 used 42 calls but all three rejections were non-repairable, so feedback activation and recovery were both zero. The realized comparison was best-of-three sampling versus one draw plus deterministic abstention—not a test of feedback recovery.

Direct-number output was structurally robust (zero missing, parse/nonfinite, or sign violations) but numerically inaccurate. This supports deterministic calibration under the frozen contract. Candidate-origin summaries are non-exclusive and exploratory; the small GDN membership prevents general subgroup claims.

## Table 1 — Construction outcome by arm

| Arm | Accepted | Rate | no_rule |
|---|---:|---:|---:|
| T0 | 42 | 100.0% | 0 |
| T1 | 42 | 100.0% | 0 |
| T1-B | 42 | 100.0% | 0 |
| T2 | 39 | 92.86% | 3 |

## Table 2 — Provider-call / validity efficiency

| Arm | Calls | Accepted | Calls/accepted | Accepted/call | Parse failures | Rejections |
|---|---:|---:|---:|---:|---:|---:|
| T0 | 0 | 42 | N/A | N/A | 0 | 0 |
| T1 | 42 | 42 | 1.000 | 1.000 | 0 | 0 |
| T1-B | 126 | 42 | 3.000 | 0.333 | 1 | 3 |
| T2 | 42 | 39 | 1.077 | 0.929 | 0 | 3 |

## Table 3 — T1-B repeated sampling

| Measure | Call 1 | Calls 1–2 | Calls 1–3 |
|---|---:|---:|---:|
| Cumulative accepted relations | 41 | 41 | 42 |
| Incremental recovery | 41 | 0 | 1 |
| Cumulative calls | 42 | 84 | 126 |

Selected calls were 41/0/1 for calls 1/2/3. Admissible-proposal counts per relation were 0:0, 1:1, 2:2, 3:39.

## Table 4 — T2 controller behavior

| Accepted | no_rule | Feedback eligible | Revise | Retrieve | Follow-up | Recovery |
|---:|---:|---:|---:|---:|---:|---:|
| 39 | 3 | 0 | 0 | 0 | 0 | 0 |

All no_rule cases were `VALIDITY_UNSUPPORTED_VARIABLE` in `variables`, non-repairable, with controller action `no_rule`.

## Table 5 — Direct-number normalized error

| Role | Mean | Median | Q1 | Q3 | P90 | Population SD |
|---|---:|---:|---:|---:|---:|---:|
| source_step_threshold | 0.6621 | 0.5984 | 0.4811 | 0.7443 | 0.9938 | 0.2529 |
| source_stability_tolerance | 1.1381 | 0.4904 | 0.1728 | 0.9765 | 5.3937 | 1.7716 |
| target_noise_scale | 39.6043 | 0.9839 | 0.8232 | 28.4537 | 86.5962 | 92.6787 |

## Table 6 — Candidate-origin subgroup summary

| Origin membership | Eligible | T0/T1/T1-B/T2 accepted | T2 no_rule | T1-B rejection/parse |
|---|---:|---:|---:|---:|
| META | 28 | 28/28/28/28 | 0 | 0/1 |
| STAT | 32 | 32/32/32/30 | 2 | 2/1 |
| GDN | 5 | 5/5/5/3 | 2 | 1/0 |

Memberships overlap; subgroup observations are not independent.

## Table 7 — Claim-evidence matrix

| Claim | Classification |
|---|---|
| A — pipeline produces admissible rules | SUPPORTED |
| B — one-call T1 feasibility | SUPPORTED |
| C — repeated sampling robustness | PARTIALLY_SUPPORTED |
| D — T2 validity improvement | NOT_SUPPORTED |
| E — T2 efficient without unacceptable loss | NOT_SUPPORTED |
| F — deterministic numeric calibration rationale | SUPPORTED |
| G — deterministic no_rule prevents invalid admission | SUPPORTED |
| H — candidate origin materially changes success | INCONCLUSIVE |

Utility evaluation is classified `ESSENTIAL` for scientific arm discrimination. It remains unauthorized pending `TASK-039E3-R2R-UTILITY-FEASIBILITY-AND-AUTHORIZATION-GATE`.
