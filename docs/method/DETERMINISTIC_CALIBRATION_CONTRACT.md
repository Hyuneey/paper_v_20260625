# Deterministic Calibration Contract

## Shared contract

All calibrators consume typed evidence and matched normal-reference IDs, not
prompts. Eligible input is the calibration split only. Each implementation
must version its input schema, normal-reference policy, statistic, missing and
outlier handling, support gate, uncertainty output, failure status, and code.

| Component | Input schema | Statistical method | Missing/outlier policy | Minimum support | Uncertainty | Failure status |
|---|---|---|---|---|---|---|
| Lag interval | trigger/response event pairs | robust lower/upper delay quantiles | unmatched events counted; right censoring reported; no silent drop | 10 matched events | bootstrap interval and censor ratio | `INSUFFICIENT_LAG_SUPPORT` |
| Response delay | matched transition timestamps | event-delay median/quantile | missing responses separate; extreme values retained then robustly summarized | 10 matches | bootstrap interval | `DELAY_UNSTABLE` |
| Baseline level | matched normal windows by regime | median and robust quantiles | explicit missing fraction; MAD-based predeclared outlier policy | 20 windows | regime/slice stability | `BASELINE_UNSTABLE` |
| Tolerance | normal residuals | MAD or empirical quantile | no imputation across long gaps; predeclared clipping only | 30 residuals | bootstrap interval | `TOLERANCE_UNSTABLE` |
| Rate boundary | timestamp-normalized differences | robust derivative quantile | reject irregular sampling unless approved resampling is recorded | 30 derivatives | slice stability | `RATE_SUPPORT_LOW` |
| Trajectory distance | aligned matched trajectories | predeclared DTW or normalized distance quantile | pairwise complete policy; reject alignment mismatch | 20 trajectories | bootstrap distance range | `TRAJECTORY_UNSTABLE` |
| Persistence duration | state run lengths | lower/upper run-length quantile | censored terminal runs reported | 15 complete runs | bootstrap interval | `DURATION_SUPPORT_LOW` |
| Minimum support | evidence counts | preregistered fixed count/rate | missing and censored counts remain visible | policy-specific | count confidence or not estimated | `SUPPORT_POLICY_FAILED` |

## Normal-reference policy

References must match the same or compatible regime and subsystem under the
pre-registered evidence policy. Tie-breaking is deterministic. A calibrator
cannot search references based on downstream rule performance.

## Prohibited inputs

- sealed final test;
- detector test predictions;
- future anomaly labels;
- generated-rule test behavior;
- provider output containing numeric values;
- validation metrics used to refit parameter values.

## Versioning

Changing a statistic, quantile, missingness threshold, outlier rule, support
gate, unit conversion, or normal-reference matcher increments the calibrator
version and changes the artifact hash. Existing accepted rules do not inherit
new values automatically.
