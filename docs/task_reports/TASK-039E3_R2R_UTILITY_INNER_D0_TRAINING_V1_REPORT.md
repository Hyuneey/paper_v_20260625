# TASK-039E3-R2R D0 Normal Training and Calibration V1

Report artifact hash: `4245f7507094abaff01788fe8b9e46d7e5d465b112bd122dcbc6c455d7c53227`

Status: `passed_task039e3_r2r_utility_inner_d0_detector_normal_training_and_calibration_v1`

The frozen `D0_PCA_SPE_V1` design was replayed exactly. One deterministic
float64 PCA model fit used only exact normal train1 plus train2. The selected
component count is 10, leaving 27 residual dimensions; the 0.95 cutoff did not
split an exact tied eigenvalue block. The private preprocessing and model
artifacts were frozen before train3 was opened.

One train3 calibration used the frozen 0.999 empirical order-statistic policy
at zero-based index 125873 and strict `score > threshold`. The private threshold
was frozen before train4 was opened. Train4 descriptive sanity produced 15401
point alarms, 479 maximal alarm episodes, and 8.709090909090909 normal FAR
episodes/hour. This descriptive outcome did not change the model or threshold.

All four normal files matched their frozen SHA-256, size, and row authorities.
There was one model fit, one calibration, zero retries, no D1 performance read,
and zero test1, label, test2, D0 INNER, D2, or OUTER access/execution. No private
path or private preprocessing, PCA, or threshold value is present in this
report.

Exact next task:
`TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-MODEL-THRESHOLD-INTEGRITY-AUDIT-V1`
