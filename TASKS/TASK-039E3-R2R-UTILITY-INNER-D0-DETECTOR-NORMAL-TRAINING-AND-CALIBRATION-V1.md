# TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-NORMAL-TRAINING-AND-CALIBRATION-V1

## Status boundary

This task implements and executes the frozen `D0_PCA_SPE_V1` normal-only
training contract. It authorizes exactly one model fit on exact HAI 23.05 P1
train1 plus train2, exactly one threshold calibration on exact train3, and a
descriptive train4 normal-only sanity evaluation only after both model and
threshold are frozen.

It does not authorize test1, labels, test2, D0 INNER execution, D2, OUTER, or
detector comparison. No D1 result content may be read; only the already-frozen
future-D2 custody hash remains bound by the design authority.

## Frozen authorities

- Base: `50aa2f3939d3bdf84ef4dfbcdfc519b2a1571e5b`
- Detector: `D0_PCA_SPE_V1`
- Design: `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`
- Feature scope: `4e9ba5a52733ae00f8cf755cda9918667c7065e0bc5b6eed2712aab97c3d6dd0`
- Feature set: `6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515`
- Feature order: `a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57`
- Dataset manifest: `5b0c395169fea468f7afd52aceafc4e6dadf062a1bc557c5bbe5dd6b8a761aa2`
- Official snapshot: `2a814cebc9a66b06c9e5cd545e2d72e65d383737`

Normal file authorities are frozen in the implementation module and must
match exact SHA-256, byte size, and row count before scientific parsing.

## Numeric contract

All calculations are deterministic CPU NumPy float64. Preprocessing is the
population mean and population standard deviation (`ddof=0`) on the exact
train1-then-train2 row-major matrix, with scale `max(sigma, 1e-12)`. PCA uses
`(Z.T @ Z) / N`, explicit covariance symmetrization, `numpy.linalg.eigh`,
descending eigenvalues, the smallest `k` reaching 0.95 cumulative explained
variance, and a mandatory residual dimension. A cutoff that splits an exact
tied eigenvalue block fails closed. Retained loading signs use the largest
absolute element, smallest-index tie break, oriented nonnegative.

Train3 calibrates only the empirical order statistic at
`ceil(0.999*n)-1`, without interpolation. Alarm is strictly `score >
threshold`. Train4 cannot alter any frozen artifact.

## Commit and execution gates

1. Commit A freezes this specification, implementation, selective normal-only
   materializer, and synthetic tests before real normal-value access.
2. Commit B adds independent adversarial tests only; production is immutable.
3. After all static gates pass, the coordinator alone performs one scientific
   model fit and one calibration. Private numeric artifacts remain outside Git
   and are represented publicly only by content hashes.
4. Commit C contains sanitized reports only.
5. Commit D contains project-state continuity only.

No retry, alternate detector, changed alpha, changed feature set, test/label
access, or result-driven repair is permitted. The exact next task after PASS is
`TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-MODEL-THRESHOLD-INTEGRITY-AUDIT-V1`.
