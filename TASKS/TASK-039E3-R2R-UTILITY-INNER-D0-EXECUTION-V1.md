# TASK-039E3-R2R Utility INNER D0 Execution V1

## Mission

Perform the first and only authoritative real INNER execution of the already
frozen and independently audited `D0_PCA_SPE_V1` detector on exact HAI 23.05
P1 test1. Freeze a label-blind detector prediction before opening labels, then
compute only the preregistered attack-event Recall and normal FAR
episodes/hour. Poor detector performance is not task failure and may not cause
any model, threshold, feature, alarm, or metric change.

The exact base is `dd2d103d20e3d61aa31167740929cbe31cf8b942`. The task branch
is `task-039e3-r2r-utility-inner-d0-execution-v1`. No rebase, main update,
unrelated merge, D1 rerun, D2, fusion, test2, OUTER, retraining,
recalibration, or result-driven change is authorized.

## Frozen scientific authority

- Detector: `D0_PCA_SPE_V1`; family: `PCA_RECONSTRUCTION_SPE`.
- Design: `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`.
- Feature count: 37.
- Feature set: `6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515`.
- Feature order: `a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57`.
- Preprocessing: `baae5495094b211731e4fcdf7bab2870e3c81e7c973bfe052fc87b457ccb6270`.
- PCA model: `f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b`.
- Threshold: `7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695`.
- Retained components: 10; residual dimensions: 27.
- Threshold alpha: 0.001; q-index: 125873; comparator: strict
  `score > threshold`.
- Runtime: CPython 3.12.13, NumPy 2.3.5, CPU
  `NUMPY_LINEAR_ALGEBRA`, float64 only.

## Committed execution grant

Replay the complete exact authorization set from authorization-freeze commit
`01cd15831246f94b2111fd3d9c0589e639f2d254`:

- restoration report `dc25f9aa51dc1a31d068110399dd29a7698f273d7cff9621f1634d7e16715ab9`;
- preflight `033f1f9981bb5323e2830fa30d7e6613ce49b7a530e14a50ca2c4df75b848131`;
- authorization `a155fbb2659dc2a8b233db179706a13338a58ae41610f5c6db01f90f3b76a1ef`;
- accounting `98493fe49d1c816c713ae2068276717137d6bd321b92e65dd0b23e0ff91b47fe`;
- readiness `3a105a529fc1adbb85fae1d2a1cfe2a5777e858059ef7cd6a51651b8bea5b93c`;
- bundle `618f5add4ad13f8c999414add7a294ee25946323baa775b54e4b90838c97e1a0`;
- receipt `10540956fe37ccd025d82d1e7a7c61eef26d869c1e9f97c7bda9b2415d4e12f2`.

Every current file must be byte-identical to that commit, self-hashed, and
cross-bound. The process-local authorization object is not reconstructed or
reissued. `CommittedD0InnerExecutionGrantV1` derives only from the complete
committed set and issues one process-local, single-use execution token.

The committed authorization must grant D0 INNER prediction, test1 feature
scientific parsing, and label metric evaluation; it must deny label access
before prediction freeze, D1 execution/rerun, D2, fusion, test2, OUTER,
retraining, recalibration, feature/model/threshold change.

## Private custody and data boundary

Load only the ignored bindings `HAI_DATA_ROOT`,
`TASK039E3_D0_PCA_SPE_PREPROCESSING_V1`,
`TASK039E3_D0_PCA_SPE_MODEL_V1`, and
`TASK039E3_D0_PCA_SPE_THRESHOLD_V1`, path-silently. All private artifacts must
be regular non-symlink files outside Git and must match their exact canonical
self-hashes, schemas, provenance, feature order, backend versions, and frozen
scientific identities. Private preprocessing values, PCA values, threshold,
scores, labels, intervals, denominators, and paths remain outside Git.

Before scientific parsing, raw `hai-23.05/hai-test1.csv` must match SHA-256
`78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be`,
size 31,255,559 bytes. Parse exactly once into a finite `(54000, 37)` float64
frame in the frozen P1 order. Timestamp is retained only for custody alignment,
never as a model feature. No filtering, imputation, clipping, smoothing, or
adjustment is permitted.

For every physical row compute frozen standardization, retained-subspace
projection, residual, and SPE. Freeze a private self-hashed score evidence
artifact containing exactly 54,000 canonical float-hex scores. Public output
may expose only hashes. Alarm exactly when SPE is strictly greater than the
private threshold; equality is not an alarm. No hysteresis, debounce, minimum
duration, suppression, or point adjustment exists.

## Prediction-before-label boundary

Build `ScientificDetectorPredictionArtifactV1` with exactly 54,000 ordered
records. Each record contains only physical row index, alarm boolean, and
detector decision identity. The indices must be exactly `0..53999`, unique and
complete. The artifact binds the committed authorization, implementation,
detector/model/schema/data identities, score-vector content hash, point alarm
count, and self-hash.

Persist it atomically and fsync it to
`docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json`.
Reopen and validate its exact bytes and self-hash before changing execution
state to `PREDICTION_FROZEN`. Any label access before that state fails closed.
After metrics, the bytes must remain unchanged.

Only then raw `label-test1.csv` may be opened. It must match SHA-256
`eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc`,
contain exactly 54,000 aligned rows, and encode labels only as exact string
tokens `0` or `1`. Parse it once.

Attack events are maximal contiguous exact-label-one runs with half-open,
file-local intervals. Reload the persisted DetectorPrediction artifact as the
metric authority. Its alarm seconds are sorted, unique, and merged only when
consecutive into maximal half-open episodes.

Compute only:

1. Attack-event Recall = attack events overlapped by at least one alarm episode
   divided by all attack events; undefined only for no attack events.
2. Normal FAR episodes/hour = alarm episodes with zero attack overlap divided
   by normal labeled seconds/3600; undefined only for no normal exposure.

Private metric evidence binds the label/event/episode hashes, private
numerators and denominators, score evidence, and frozen prediction. Public
metrics expose only the allowed values, defined states, formula identities,
counts, and hashes.

## Implementation, audit, execution, and commits

The no-knob implementation is
`src/paperworks/v6/task039e3_r2r_d0_inner_execution_v1.py`. Static tests are
synthetic only. Commit A contains only this task, that module, and
`tests/test_task039e3_r2r_d0_inner_execution_v1.py`. It is frozen before any
real test1 scientific parse.

After Commit A, add only
`tests/test_task039e3_r2r_d0_inner_execution_v1_independent.py` in Commit B.
Production is immutable after Commit A. The independent suite attacks grant
reconstruction, committed substitution, private artifact substitution,
alternate k/order/comparator/smoothing, prediction closure and leakage,
prediction-before-label order, D1/D2/test2/retry/result-driven operations, and
private threshold/score leakage. Accepted invalid must be zero. Numeric
differential divergence must be zero.

After all gates pass, the coordinator alone performs exactly one real
scientific execution, with zero retries. A failure after feature parsing begins
blocks permanently; do not rerun or alter any scientific parameter.

Commit C contains only the label-blind prediction and sanitized implementation
audit, metrics, accounting, readiness, bundle, receipt, and report. Commit D
contains only project-state continuity updates. The result remains uninterpreted
and awaits an independent exact-byte result-integrity audit.

## PASS and next task

PASS status is
`passed_task039e3_r2r_utility_inner_d0_execution_v1`; scientific state is
`D0_EXECUTED_RESULT_INTEGRITY_AUDIT_PENDING`. Metric magnitude is not a PASS
criterion.

After PASS, stop. The exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-AUDIT-V1`. Do not start it,
compare D0 with D1, design D2, or access test2.
