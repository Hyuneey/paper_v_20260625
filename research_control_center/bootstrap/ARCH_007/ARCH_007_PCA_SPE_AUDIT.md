# ARCH-007 PCA / SPE Audit

- Input: 37 ordered P1 numeric fields; timestamp/label/non-P1 excluded.
- Fit: normal train1+train2, custom NumPy population standardization (`ddof=0`, floor `1e-12`).
- PCA: population covariance, `np.linalg.eigh`, stable descending order, sign anchoring, smallest `k` reaching 0.95.
- Frozen result: `k=10`, 27 residual dimensions.
- SPE: rowwise sum of squared standardized reconstruction residuals.
- Classification: `DETERMINISTIC_WITH_ENV_ASSUMPTIONS`.
- Boundary: SPE is not probability, causality, or scientific optimality.

See `architecture/07_d0_detector/ARCH_007_SPE_DEFINITION.md` and `ARCH_007_FUNCTION_CATALOG.csv`.

