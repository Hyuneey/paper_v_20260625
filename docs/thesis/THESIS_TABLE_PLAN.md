# Thesis Table Plan

The main Results chapter uses eight tables. All values come from authorized,
sanitized public artifacts. Candidate-origin diagnostics may appear as a
supplementary table. No utility-performance table is permitted.

## Table 1 - Candidate discovery

Purpose: show how the three evidence methods formed the 47-pair union without
creating a cross-arm winner.

| Quantity | META | STAT | GDN | Union |
|---|---:|---:|---:|---:|
| Primary candidates | 20 | 20 | 20 | 47 |
| Method-only | 8 | 8 | 18 | - |
| META-STAT overlap | 11 | 11 | - | 11 |
| META-GDN overlap | 1 | - | 1 | 1 |
| STAT-GDN overlap | - | 1 | 1 | 1 |
| Three-way overlap | 0 | 0 | 0 | 0 |

Sources: C integration receipt `5d53e195...`, overlap `70a9f3db...`, and arm
results `0e3b055d...`, `7351e295...`, `2c58308d...`.

Required note: scores are not comparable; overlap is not correctness or
causality.

## Table 2 - D1 fitting and D2 confirmation

Purpose: summarize evidence attrition and overlapping origin views.

| Stage/quantity | Overall | META | STAT | GDN |
|---|---:|---:|---:|---:|
| D1 candidate pairs | 47 | 20 | 20 | 20 |
| D1 fit-supported pairs | 25 | 16 | 17 | 5 |
| D1 supported directions | 45 | 29 | 33 | 7 |
| D2 confirmed pairs | 23 | 15 | 17 | 3 |
| D2 confirmed directions | 42 | 28 | 32 | 5 |
| D2 conflicts | 3 | - | - | - |

Sources: D1 result `a2767945...`, D1 arm summary `65899300...`, D2 result
`3b5bdce6...`, D2 arm summary `afc9ea42...`.

Required note: origin columns overlap; D2 is one-way normal-data calibration
confirmation, not causality or anomaly performance.

## Table 3 - Construction arm validity

| Arm | Materialized | Admissible | Rejected | Parse failures | Accepted | no_rule | Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| T0 | 42 | 42 | 0 | 0 | 42 | 0 | 100.00% |
| T1 | 42 | 42 | 0 | 0 | 42 | 0 | 100.00% |
| T1-B | 125 | 122 | 3 | 1 | 42 | 0 | 100.00% |
| T2 | 42 | 39 | 3 | 0 | 39 | 3 | 92.86% |

Source: construction analysis `2175fca3...`.

Required note: accepted relations and proposals have different denominators;
verifier validity is not anomaly utility.

## Table 4 - Provider-call / validity efficiency

| Arm | Calls | Accepted | Calls/accepted | Accepted/call | Frontier interpretation |
|---|---:|---:|---:|---:|---|
| T0 | 0 | 42 | N/A | N/A | Deterministic baseline |
| T1 | 42 | 42 | 1.000 | 1.000 | Non-dominated provider arm |
| T1-B | 126 | 42 | 3.000 | 0.333 | Dominated by T1 |
| T2 | 42 | 39 | 1.077 | 0.929 | Dominated by T1 |

Source: efficiency analysis `3c830fd1...`.

Required note: construction-validity/call frontier only; no utility score or
winner.

## Table 5 - T1-B repeated-sampling robustness

| Stage | Calls | Admissible | Rejected | Parse failures | Cumulative accepted | Marginal recovery | Selected |
|---|---:|---:|---:|---:|---:|---:|---:|
| Call 1 | 42 | 41 | 1 | 0 | 41 | 41 | 41 |
| Call 2 | 42 | 39 | 2 | 1 | 41 | 0 | 0 |
| Call 3 | 42 | 42 | 0 | 0 | 42 | 1 | 1 |

Source: T1-B analysis `9ef7ce42...`.

Required note: 126 calls are not 126 independent relations; the parse failure
was consumed but did not materialize a proposal.

## Table 6 - T2 controller behavior

| Quantity | Count |
|---|---:|
| Provider calls | 42 |
| Accepted | 39 |
| Non-repairable no_rule | 3 |
| Feedback eligible | 0 |
| Revise | 0 |
| Retrieve | 0 |
| Follow-up | 0 |
| Recovery | 0 |

Source: T2 analysis `ae38ea48...`.

Required note: feedback recovery was not empirically exercised; incremental
validity benefit was not observed.

## Table 7 - Direct-number normalized errors

| Role | Mean | Median | SD | Q1 | Q3 | P90 | >.10 | >.25 | >.50 | >1.00 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Source step threshold | 0.6621 | 0.5984 | 0.2529 | 0.4811 | 0.7443 | 0.9938 | 42 | 42 | 27 | 2 |
| Source stability tolerance | 1.1381 | 0.4904 | 1.7716 | 0.1728 | 0.9765 | 5.3937 | 32 | 24 | 18 | 8 |
| Target noise scale | 39.6043 | 0.9839 | 92.6787 | 0.8232 | 28.4537 | 86.5962 | 42 | 42 | 40 | 14 |

Source: Direct-number analysis `b653a530...`.

Required note: N=42 per role; normalized absolute error; type-7 quantiles;
population SD; schema validity is not numerical accuracy.

## Table 8 - Claim/evidence status

| Claim | Status |
|---|---|
| A - pipeline feasibility | SUPPORTED |
| B - one-call T1 feasibility | SUPPORTED |
| C - repeated-sampling robustness | PARTIALLY_SUPPORTED |
| D - T2 validity improvement | NOT_SUPPORTED |
| E - T2 efficiency advantage | NOT_SUPPORTED |
| F - deterministic calibration rationale | SUPPORTED |
| G - deterministic no_rule safety | SUPPORTED |
| H - candidate-origin effect | INCONCLUSIVE |
| Labeled utility claims | NOT_EXECUTED |

Source: claim analysis `3cccbaa4...` plus final utility-stop receipt
`dc019968...`.

## Supplementary table - Candidate-origin construction diagnostics

| Origin | Eligible | T0/T1/T1-B/T2 accepted | T2 no_rule | T1-B rejected/parse |
|---|---:|---:|---:|---:|
| META | 28 | 28/28/28/28 | 0 | 0/1 |
| STAT | 32 | 32/32/32/30 | 2 | 2/1 |
| GDN | 5 | 5/5/5/3 | 2 | 1/0 |

Source: origin analysis `562de702...`.

Required note: memberships overlap; subgroup inference is exploratory; GDN
N=5.

## Prohibited table

Do not create an arm-level utility, anomaly recall, precision, false-alarm,
detector-recovery, or cost-utility table. No such experiment was executed.
