# Current project state

## Research in one paragraph

This project studies graph-guided agentic construction of verified rules for
explainable multivariate time-series anomaly detection. COMMON-42 and the exact
D1 Rule-only result remain frozen. The primary reference-detector design is now
preregistered independently of D1 performance; training, calibration,
execution, and comparison remain separate future authority layers.

## Current completed milestone

The public/static D0 baseline design is frozen as `D0_PCA_SPE_V1`, family
`PCA_RECONSTRUCTION_SPE`, under exact design hash
`357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`.
The full public P1 schema has 37 ordered features and replays the existing
canonical order authority. The design used no HAI values, labels, D1
performance, training, calibration, detector execution, or test2 access.

## Frozen design

- Model fit: exact normal train1 + train2.
- Threshold calibration: exact normal train3 only.
- Normal sanity evaluation: train4 only after model and threshold freeze.
- INNER evaluation: test1 only under a later authorization.
- Preprocessing: population mean/std (`ddof=0`), scale floor `1e-12`.
- PCA: deterministic CPU linear algebra; smallest `k` reaching `0.95`, with a
  mandatory residual dimension.
- Score: squared prediction error.
- Threshold: alpha `0.001`, non-interpolated empirical order statistic.
- Alarm: strict `score > threshold`.
- Episodes and primary metrics: exact frozen D1-compatible identities.

## Authorization boundary

D0 model training, threshold calibration, train4 sanity evaluation, INNER D0
execution, D2, detector runtime authority, fusion, test2/OUTER, and any
result-driven tuning remain unauthorized. The D1 result and COMMON-42 remain
unchanged. The frozen R3 evaluator's real-execution authority remains false.

## Exact next task

`TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-NORMAL-TRAINING-AND-CALIBRATION-V1`.
It must consume the exact D0 design hash, use only authorized normal splits,
freeze model and threshold artifacts before any test1 access, and remain
independent of D1 performance.

## Canonical evidence

- D0 Design Commit A: `4bdb16701a84b383f713629524a20900bba27d95`
- Independent Audit Commit B: `4e4e904cca8779e5dde62bcea697e6d40d58a867`
- Design Freeze Commit C: `2528632fca2c64e1bd4a293d57bed56cc3e5665b`
- D0 design hash: `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`
- Feature set hash: `6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515`
- Feature order hash: `a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57`
- Readiness: `533e62761efce660e1d10726268187c2a9ba5e0d2b0763814b64bd75b0473c4e`
- Bundle: `8fa5ab4b81a4dad0f7d1d13bd356b3aad21a45e747cd3b047ada697450ce3034`
- Receipt: `61299eba73c09faaf9396a6174ad487e4736c6271e274a2c18dd3cb60fd0c8b5`
- Frozen D1 RulePrediction for future D2:
  `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`

## No-claim boundary

The design freeze certifies a preregistered reference-detector contract only.
It is not a trained detector, threshold, prediction, result, scientific
comparison, deployment claim, or D0/D2 execution authorization.
