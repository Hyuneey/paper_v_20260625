# Prototype Result Tables

## Evidence ledger

| Evidence block | Frozen source | Evidence type | Not established |
|---|---|---|---|
| Proposed contract vertical slice | TASK-032F | Synthetic implementation and deterministic replay | Real-data performance or explanation usefulness |
| ARGOS E1 | TASK-033 | Isolated frozen-rule runtime plumbing | Detection performance |
| Initial rule validation | TASK-034 | One-rule public-KPI validation | Test or benchmark performance |
| Generation cohort | TASK-035A / TASK-035AR | Response, extraction, and executable yields | Rule accuracy |
| Multi-rule validation | TASK-035B | Ten-KPI frozen outer-validation comparison | Sealed-test or universal superiority |

## Generation-operability results

| Cohort | Slots | Output budget | Response | Extracted | Executable |
|---|---:|---:|---:|---:|---:|
| TASK-035A original | 100 | 2,000 | 84 (84%) | 61 (61%) | 55 (55%) |
| TASK-035AR remediation | 100 | 6,000 | 100 (100%) | 100 (100%) | 91 (91%) |
| Combined frozen cohort | 200 | Mixed frozen cohorts | See separate cohorts | See separate cohorts | 146 |

The original TASK-035A status remains `insufficient_rule_yield`. TASK-035AR is
a separate balanced remediation cohort and does not rewrite that result.

## Initial one-rule public-KPI validation

Metric group: direct binary validation diagnostics, PA-free, no threshold
optimization.

| TP | FP | TN | FN | Precision | Recall | Point F1 |
|---:|---:|---:|---:|---:|---:|---:|
| 33 | 6 | 20,295 | 142 | 0.8462 | 0.1886 | 0.3084 |

ARGOS label-aware and point-adjusted validation diagnostics exist in the
source-faithful reproduction report but are supplementary and are not mixed
with this direct PA-free result block.

## Ten-KPI frozen outer validation

Metric group: equal-KPI macro averages from direct binary PA-free outputs.

| Arm | Precision | Recall | Point F1 | Event recall | FP / 10k normal | False-alarm events / 10k points |
|---|---:|---:|---:|---:|---:|---:|
| Best-1 | 0.7178 | 0.4589 | 0.4801 | 0.7034 | 22.08 | 4.14 |
| Top-3 OR | 0.5820 | 0.5975 | 0.5360 | 0.7856 | 105.56 | 6.97 |
| Coverage-3 OR | 0.3982 | 0.6968 | 0.3320 | 0.8057 | 2084.04 | 8.09 |
| All-10 OR | 0.3181 | 0.6993 | 0.3156 | 0.7724 | 2242.19 | 8.82 |

## Primary comparison

Coverage-3 OR minus Best-1:

| Endpoint | Observed macro difference | Paired bootstrap 95% percentile interval |
|---|---:|---:|
| Recall | +0.2379 | [0.0944, 0.4014] |
| Point F1 | -0.1481 | [-0.3616, 0.0607] |
| Precision | -0.3196 | [-0.5164, -0.1275] |
| FP / 10k normal | +2061.96 | [108.84, 4822.87] |

The bootstrap is descriptive with KPI as the resampling unit. It is not a
formal population-level significance test.

## Split and claim boundary

| Stage | Labels allowed | Selection allowed | Result status |
|---|---|---|---|
| Generation | Predeclared prompt chunks only | No performance selection | Completed |
| Inner selection | Yes, after label-free panel freeze | Four arms frozen | Completed |
| Outer validation | Loaded only after prediction and arm freeze | Prohibited | Completed once |
| Held-out test | No access | Prohibited | Sealed and unauthorized |
