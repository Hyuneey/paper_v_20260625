# TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-BASELINE-DESIGN-AND-FREEZE-V1

## 0. Mission and execution boundary

Design, preregister, independently audit, and freeze the primary D0 detector
baseline before any detector training, calibration, INNER execution, D2 design,
or OUTER access. This is public/static design only. Real HAI values, test1,
labels, and test2 are prohibited. No detector execution is authorized.

The primary reference detector is `D0_PCA_SPE_V1`, a normal-only PCA
reconstruction-residual / Squared Prediction Error detector. It is a standard
reference multivariate process-anomaly detector, not a claimed state-of-the-art
detector and not the research contribution.

## 1. Repository and continuity authority

Branch from exact base `91a92fb3ca44d0e34c310b35ab8b6ec88c95be05`
as `task-039e3-r2r-utility-inner-d0-detector-baseline-design-freeze-v1`.
Require clean lineage, clean index/worktree, no rebase or unrelated merge, and
understood origin equality. Read `AGENTS.md`, `docs/project_state/START_HERE.md`,
`CURRENT_STATE.json`, `HANDOFF.md`, `RESEARCH_SCOPE.md`, `AUTHORITY_INDEX.md`,
`DECISION_LOG.md`, `SAFETY_BOUNDARIES.md`, and the D1 integrity
receipt/readiness first. Validate the current-state self-hash.

The required starting state is: the exact D1 RulePrediction artifact
`58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`
is executed, frozen, and integrity-audited; D0, D2, detector, and OUTER remain
unauthorized. D1 must not be modified, rerun, or parsed in this task.

## 2. D1-independence and detector selection

D0 architecture, features, component selection, normal calibration split,
threshold, episode policy, and metrics must be independent of observed D1
performance. D1 metric artifacts and prediction content must not be read for
design. Only the frozen D1 RulePrediction hash may be bound for future D2
custody. No D1 result value or count may enter a D0 design artifact or rationale.

PCA-SPE is selected because it is a standard, deterministic, reproducible,
normal-only multivariate process-monitoring baseline that is computationally
tractable, uses no LLM, is scientifically distinct from the graph-guided rule
mechanism, and does not conflate candidate discovery with the detector baseline.
It is not selected for expected superiority over D1.

`paperworks.gdn` remains candidate extraction, not a complete primary detector.
GDN, another neural model, or another baseline may be added only under a future
separate preregistration and may not replace D0 after results are observed.

## 3. Frozen identity and feature authority

Freeze:

- detector ID: `D0_PCA_SPE_V1`;
- family: `PCA_RECONSTRUCTION_SPE`;
- role: `REFERENCE_MULTIVARIATE_PROCESS_ANOMALY_DETECTOR`;
- training and calibration: `NORMAL_ONLY`;
- scientific LLM: false;
- randomized training: false;
- random seed required: false.

Use the complete verified HAI 23.05 P1 numeric process-variable feature set,
in canonical source-column order. Exclude timestamps, labels, attack metadata,
summary text, and non-P1 variables. Freeze the ordered names, count, set hash,
and order hash from already-frozen public metadata/schema authority without
reading feature values. If this scope is ambiguous, block rather than using the
22-feature D1 runtime union or the 24 candidate endpoints.

## 4. Frozen split roles

- normal train1: model fit;
- normal train2: model fit;
- normal train3: threshold calibration;
- normal train4: normal-only sanity evaluation after model/threshold freeze;
- test1: INNER utility evaluation only;
- label-test1: INNER metric evaluation only;
- test2 and label-test2: sealed OUTER.

Future fitting concatenates exact train1 and train2 without shuffle after hash
validation. Ordering must not alter mean/covariance semantics. No labels are
used. Test1 and its labels may never select preprocessing, PCA dimension,
threshold, alarm policy, or any detector parameter. Train4 may report a normal
sanity result after freeze but may not change the model or threshold.

## 5. Frozen preprocessing and PCA

For each feature, compute the population mean and population standard deviation
over exact train1+train2 with `ddof=0`, then standardize using
`scale=max(sigma,1e-12)`. Freeze `STANDARDIZATION_SCALE_FLOOR=1e-12`. No caller
scaler, robust scaling, or min-max alternative is allowed.

Fit PCA to standardized train1+train2 using covariance/equivalent centered SVD.
Use deterministic CPU `NUMPY_LINEAR_ALGEBRA`; future execution must record the
exact tested NumPy/backend version and prohibit randomized SVD. Order components
by descending explained variance. Select the smallest `k` whose cumulative
explained variance is at least `0.95`, subject to `1 <= k <= d-1`; if the first
qualifying `k` equals `d`, use `d-1`. The target is not tunable. Future training
must fail closed if the cutoff splits an exactly tied eigenvalue block.

Canonicalize each loading sign by locating the largest absolute element,
breaking exact ties by lowest feature index, and orienting that element
nonnegative. Sign is artifact reproducibility metadata, not scientific evidence.

For standardized row `z`, compute the retained-subspace reconstruction and
`SPE=sum((z-z_hat)^2)`. Produce one score per physical second. No smoothing,
dilation, point adjustment, moving average, or caller score override is allowed.

## 6. Frozen threshold, episodes, and metrics

Calibrate only on normal train3. Freeze `alpha=0.001` and upper quantile `0.999`.
For `n` ascending calibration scores, use zero-based
`ceil(0.999*n)-1`, without interpolation or distributional approximation.
Alarm iff `score > threshold`; equality is not an alarm. The policy must never
be optimized for labels, D1 results, test1, F1, recall, FAR, or D2.

Alarm timestamps are exact integer physical-second indices. Deduplicate, sort,
and merge consecutive seconds into maximal half-open episodes. There is no
tolerance, expansion, or label-selected postprocessing.

Future D0 INNER evaluation uses the exact D1-compatible primary metrics:

- attack-event recall: attack events overlapped by at least one alarm episode
  divided by all attack events;
- normal FAR episodes/hour: alarm episodes with no attack overlap divided by
  normal labeled hours.

Secondary metrics, if any, are descriptive and cannot tune or select D0.

## 7. Future immutable artifacts and D2 boundary

Design a label-blind future `DetectorPredictionArtifactV1` bound to detector
config/model/preprocessing/threshold/schema/dataset/INNER/test1 authorities and
ordered per-second decisions. Public prediction records should expose row index,
alarm, decision identity, and optional score hash/reference rather than raw
scores, training data, or private parameters.

The future model artifact binds exact feature schema, train1/train2 hashes,
preprocessing/model content hashes, target and selected `k`, backend/version,
implementation commit/time, no-label training, and no test access. Numeric model
contents may remain private with a public content hash.

The future threshold artifact binds model hash, exact train3, alpha, order-
statistic policy, score count, private threshold-content hash, and false
label/test use. Once frozen it cannot change.

Future DetectorErrorContext compatibility is supplementary, INNER utility/FN
oriented, and grants neither relation validity nor runtime authority. No context
instance is generated here.

Future D2 must consume the exact frozen D1 RulePrediction hash above and the
future exact frozen D0 DetectorPrediction. Neither arm may be rerun for D2.
Fusion/gating policy is not designed or authorized here.

## 8. Public design authority and config

Create the no-I/O authority module
`src/paperworks/v6/task039e3_r2r_d0_detector_design_v1.py`, with immutable
typed design, feature, split, preprocessing, PCA, threshold, metric,
independence, and future-artifact contracts. A no-argument factory derives the
single canonical authority. Caller hyperparameters are prohibited. Freeze the
complete canonical `D0_DETECTOR_DESIGN_HASH`.

Create the self-hashed path-free config
`configs/v6/task039e3_r2r_d0_pca_spe_detector_v1.json`. It may contain no model
numeric values or D1 performance values. It must declare false D1-performance,
metric-artifact, and prediction-content use; true future-D2 D1-hash custody; and
zero data access, training, and detector executions.

## 9. Tests, independent audit, and access accounting

Static synthetic tests must cover canonical custody, reconstruction rejection,
exact identity/hyperparameters/splits/features/metrics, no caller override,
sealed test2, no label/test use, no D1 performance fields, no GDN/Isolation
Forest/neural substitution, and zero authorization/execution.

After freezing Commit A, an independent suite must adversarially reject alpha,
variance, `k`, scaler, feature membership/order, label/test1/train4 tuning, D1-
dependent design, detector-family, score, smoothing, point/episode/metric,
test2, D2, detector-execution, and OUTER mutations. Accepted invalid must be 0.

Required final access/execution accounting:

- train1/train2/train3/train4/test1 value reads: 0;
- label reads: 0;
- test2 reads: 0;
- detector training executions: 0;
- detector INNER executions: 0;
- private paths/values exposed: 0.

## 10. Commit and report boundaries

Commit A contains only this task specification, authority module, config, and
static tests. Commit B contains only the independent test. No Commit-A
production changes are permitted after the independent audit begins.

Commit C contains only self-hashed sanitized design, feature-scope,
independence, independent-audit, readiness, bundle, receipt, and Markdown
reports. Reports contain the frozen design/hashes/splits/hyperparameters and no
D1 performance values, raw HAI, labels, private paths, or private values.

Commit D contains only `docs/project_state` updates. Append `DEC-D0-001`, record
the frozen PCA-SPE authority and exact next task, and leave all execution
authorization false. Push only after verified clean state and divergence `0 0`.

## 11. PASS, BLOCK, and next task

PASS status is
`passed_task039e3_r2r_utility_inner_d0_detector_baseline_design_and_freeze_v1`.
Set the design-frozen flag true while model-trained, threshold-frozen, D0-
executed, D0-authorized, D2-authorized, and OUTER-authorized remain false.

Block if public P1 schema cannot be resolved exactly, D1 performance is needed,
any data/label/test2 value is read, architecture remains ambiguous, caller
scientific control remains, metric policy differs, GDN is promoted, or any
detector execution occurs. Freeze a sanitized blocker and stop; do not select a
replacement detector automatically.

After PASS, do not start automatically. The exact next task is
`TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-NORMAL-TRAINING-AND-CALIBRATION-V1`.
That separate task may fit/calibrate only under this exact frozen design and
must not open test1 or labels, use D1 results, or execute INNER D0 evaluation.
