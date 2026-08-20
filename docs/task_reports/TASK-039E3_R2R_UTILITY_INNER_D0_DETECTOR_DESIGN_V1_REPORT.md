# TASK-039E3-R2R D0 Detector Design V1 Report

Status: `passed_task039e3_r2r_utility_inner_d0_detector_baseline_design_and_freeze_v1`

The primary reference detector is frozen as `D0_PCA_SPE_V1`, family
`PCA_RECONSTRUCTION_SPE`, under design authority
`357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`.
This task performed public/static design only: all train/test/label value reads,
training executions, threshold computations, and detector executions were zero.

The exact complete P1 public feature authority contains 37 ordered identities.
Its set hash is
`6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515`
and its order hash is
`a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57`.

The frozen model-fit scope is exact normal train1+train2. Normal train3 is the
only threshold-calibration split. Normal train4 is sanity-evaluation only after
freeze. Test1 is INNER evaluation only, while test2 remains sealed OUTER.

Preprocessing is population mean and `ddof=0` population standard deviation,
with scale floor `1e-12`. PCA retains the smallest component count reaching
explained variance `0.95`, while preserving at least one residual dimension.
The anomaly score is SPE. Threshold calibration uses the non-interpolated
normal-train3 order statistic at alpha `0.001`, and alarms require strict
`score > threshold`.

The episode and primary metric identities exactly match the frozen D1 utility
authorities. D1 performance, its metric artifact, and its prediction content
were not used or read. Only the frozen D1 RulePrediction hash is bound for
future D2 custody.

Static tests: 12 passed. Independent semantic attacks: 71 rejected. Accepted
invalid: 0. D0, D2, detector execution, and OUTER remain unauthorized.

Exact next task:
`TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-NORMAL-TRAINING-AND-CALIBRATION-V1`.
