# Split, Threshold, and Claim Policy

## Dataset boundary

- ARGOS reproduction: one prepared KPI series; no access in TASK-030.
- Proposed primary dataset: official iTrust SWaT; not accessed in TASK-030 and
  still subject to DEC-007.
- Kaggle/local `merged.csv`: staging/debug only; prohibited for final claims.
- WADI and full SWaT P2-P6: not started.

No KPI, SWaT, WADI, Kaggle row, captured ARGOS rule, or detector prediction was
read for this specification.

## Split authority

| Split | Allowed | Prohibited |
|---|---|---|
| Train | graph learning, candidate ranking, rule-structure learning | final claims, test-driven selection |
| Calibration | numeric fitting, normal references, uncertainty and stability | test/validation metric optimization of numeric values |
| Validation | candidate selection, fusion selection, operating-threshold selection | modifying values after test access |
| Test | one-way evaluation only | rule, parameter, threshold, candidate, prompt, graph, or fusion modification |

All graph, rule, parameter, threshold, detector, fusion, code, and metric hashes
are frozen before test access.

## Metrics

Primary PA-free metrics are precision, recall, point F1, range F1, event recall,
and event precision. Metric definitions and zero-division behavior must be
versioned before test.

Point-adjusted metrics and paper-faithful ARGOS Event-PA are supplementary only.
They cannot select a proposed-method rule, parameter, detector, threshold, or
headline claim.

Test-label-optimized thresholds are prohibited for the proposed method.

## Claim classes

Allowed after TASK-030: schema/protocol completeness and synthetic fixture
validation.

Not allowed: anomaly-detection performance, fusion superiority, explanation
quality, causal discovery, physical invariant discovery, official SWaT result,
or thesis final performance.
