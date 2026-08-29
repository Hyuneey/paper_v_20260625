# ARCH-007 SPE Definition

For one 37-feature row \(x_i\), the implementation performs:

1. \(z_i=(x_i-\mu)/s\), where \(\mu\) and population standard deviation \(s\) come from normal train1+train2 and `s=max(std, 1e-12)`.
2. \(\hat z_i=(z_iW_k)W_k^T\), where `W_k` contains the retained PCA loadings.
3. \(r_i=z_i-\hat z_i\).
4. \(SPE_i=\sum_{j=1}^{37} r_{ij}^2\).

One finite nonnegative `float64` SPE is produced per timestamp. It is squared reconstruction-residual magnitude in standardized feature space. It is not a probability, calibrated likelihood, causal score, or episode metric. No score smoothing, dilation, or point adjustment is performed.

The frozen policy retains the smallest number of components reaching cumulative explained variance `>= 0.95`; the authorized fit selected `k=10`, leaving 27 residual dimensions. `k=10` is a frozen outcome, not the configured design constant.

Evidence: `score_spe_v1`, `compute_spe_float64_v1`, the model receipt, and the independent PCA oracle.

