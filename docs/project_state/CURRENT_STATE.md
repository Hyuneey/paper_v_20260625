# Current project state

## Research in one paragraph

This project studies graph-guided agentic construction of verified rules for
explainable multivariate time-series anomaly detection. The exact D1 Rule-only
result remains frozen and integrity-audited. The independent
`D0_PCA_SPE_V1` detector has now completed its first and only authorized INNER
test1 execution. Its label-blind prediction and public result are frozen;
result-integrity audit and scientific interpretation remain pending.

## D0 execution state

- Status: `passed_task039e3_r2r_utility_inner_d0_execution_v1`.
- Scientific state: `D0_EXECUTED_RESULT_INTEGRITY_AUDIT_PENDING`.
- Implementation Commit A: `c117087ec43d6e58167e77087e13b6a8a9226d42`.
- Independent Audit Commit B: `f45c71c9990984f6fa0c552060c8ab51e1e5c9a4`.
- Result Freeze Commit C: `78d758f50657413eed28dc838212be9a1edeffc7`.
- Authorization: `a155fbb2659dc2a8b233db179706a13338a58ae41610f5c6db01f90f3b76a1ef`.
- DetectorPrediction: `a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6`.
- Execution run: `0593d05790fef3b9264af587c451ece6186db438541a8b14edabbb2ee4bdeeb9`.
- Readiness: `b25ec0663b8595cbbaff36c97b28e29a7364dc586adc0bfc8c7558f36de8ee18`.
- Bundle: `253b78a7a76f45669dd9289e931c2e8719c14bcc3bdc1723d222de23ea9e0a23`.
- Receipt: `62dab615ab8f95d7c65d4edfd605abd7543f28a09d54032b52ffd36f971b71da`.

The run used the exact frozen 37-feature preprocessing, PCA model, and strict
threshold under CPython 3.12.13 and NumPy 2.3.5. It produced 54,000 scores and
54,000 label-blind prediction records. The prediction artifact was persisted
and byte-validated before the label file was opened. The label was then parsed
once for the two preregistered metrics. Scientific execution attempts were one,
retries were zero, and result-driven changes were zero.

## Authority boundary

D0 execution and result freeze are complete, but result integrity has not been
independently audited and D0 result interpretation is not ready. D1 remains
unchanged and frozen. D1 content reads, D1 executions, D2 executions, OUTER
executions, and test2 accesses were all zero. D2 and OUTER remain
unauthorized. Private paths, raw scores, model values, preprocessing values,
threshold values, labels, and attack intervals remain outside Git.

## Exact next task

`TASK-039E3-R2R-UTILITY-INNER-D0-RESULT-INTEGRITY-AUDIT-V1`.

It must independently audit the exact Commit-C bytes and must not rerun D0.
Only after that audit passes may D0 and D1 be compared scientifically.
