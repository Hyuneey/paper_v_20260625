# ARCH-007 Calibration Audit

Normal train3 produces one SPE per row using the already-frozen scaler/PCA. Threshold policy is `q=.999`, zero-based index `ceil(q*n)-1` (125873 for 126000 rows), stable ascending sort, no interpolation, and strict `score > threshold`; equality is not an alarm.

The threshold artifact is hash-bound and persisted before train4 sanity/test1 use. Labels, test1 outcomes, D1 results, and test2 are excluded. Train3's separate relation-confirmation role is an `ACCEPTABLE_WITH_SCOPE_LIMITATION` coupling, not verified leakage.

