# Prototype Result Tables

## Evidence Ledger

| Evidence block | Frozen task | Evidence type | Not established |
|---|---|---|---|
| Proposed contract vertical slice | TASK-032F | Synthetic deterministic implementation | Real-data effectiveness |
| One-shot generation and runtime | TASK-033 to TASK-035AR | Operability and public-KPI validation | General rule quality |
| Rule-only panel | TASK-035B | Ten-KPI follow-up outer validation | Sealed superiority |
| Detector and generic fusion | TASK-037A to TASK-037C | Dual LSTMAD sensitivity and diagnostic fusion | Exact ARGOS detector identity |
| Error-conditioned Aggregator | TASK-037D/E | FN/FP generation, selection, and Full composition | Universal aggregation benefit |
| Repair/Review components | TASK-038A to TASK-038E | Bounded component ablation and descriptive transfer | Exact reproduction or sealed confirmation |

## Generation Operability

| Cohort | Calls | Output budget | Responses | Static-valid | Executable |
|---|---:|---:|---:|---:|---:|
| TASK-035A | 100 | 2,000 | 84 | 61 | 55 |
| TASK-035AR | 100 | 6,000 | 100 | 100 | 91 |
| Combined executable cohort | 200 | Frozen separate cohorts | - | - | 146 |

## Rule-Only Validation

| Arm | Precision | Recall | Point F1 | FP / 10k normal |
|---|---:|---:|---:|---:|
| Best-1 | 0.7178 | 0.4589 | 0.4801 | 22.08 |
| Top-3 OR | 0.5820 | 0.5975 | 0.5360 | 105.56 |
| Coverage-3 OR | 0.3982 | 0.6968 | 0.3320 | 2084.04 |
| All-10 OR | 0.3181 | 0.6993 | 0.3156 | 2242.19 |

## Component Evidence

| Component | Key evidence | Judgment |
|---|---|---|
| One-shot generation | Yield depends on output budget; frozen execution deterministic | Partial |
| Repair operability | 13/13 recovered | Strong |
| Repair performance | Useful 4, equal 4, regressive 5 | Partial |
| Review inner effect | 72 improvements among 77 calls; one equal, three regressions, one invalid | Strong |
| Review outer transfer | All 19 selected reviewed rules positive relative to parent | Strong descriptive |
| Full A3 robustness | Alpha negative, Beta positive versus A0 | Partial |
| FP safety | 14 harmful classifications among 19 selected FP rules | Partial; unsafe without guards |
| Overall ARGOS | Components valid; full superiority unproven | Partial methodological support |

## Four-Branch Outer Results

Macro direct PA-free point F1 on the previously exposed outer partition:

| Variant | Detector | A0 Full | A1 Full | A2 Full | A3 Full |
|---|---:|---:|---:|---:|---:|
| LSTMADalpha | 0.3541 | 0.4884 | 0.4544 | 0.5047 | 0.4666 |
| LSTMADbeta | 0.4233 | 0.3880 | 0.3895 | 0.4215 | 0.4245 |

| Comparison | Alpha Full F1 delta | Beta Full F1 delta | Direction |
|---|---:|---:|---|
| A1 - A0 | -0.0340 | +0.0015 | Mixed |
| A2 - A0 | +0.0163 | +0.0335 | Same positive |
| A3 - A0 | -0.0218 | +0.0364 | Mixed |

## FP Safety and Agent Cost

| Item | Result |
|---|---:|
| Selected A2/A3 FP rules | 19 |
| Safe classifications | 4 |
| Costly classifications | 14 |
| Harmful classifications | 14 |
| Ineffective classifications | 1 |
| Unique Repair calls | 13 |
| Unique Review calls | 77 |
| Total unique agent calls | 90 |
| Provider-reported tokens | 404,399 |

FP classifications overlap. A rule can be both costly and harmful. Monetary
cost is not computed because no pricing artifact was frozen before execution.

## Boundary

The outer partition was previously exposed, no sealed test was accessed, and
no Alpha/Beta or branch winner was selected. These tables do not establish
final performance, exact ARGOS reproduction, or proposed-method validity.
