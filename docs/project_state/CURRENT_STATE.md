# Current project state

## Research in one paragraph

This project studies graph-guided agentic construction of verified rules for
explainable multivariate time-series anomaly detection. COMMON-42 and the exact
D1 Rule-only result remain frozen and integrity-audited. The independent
reference detector is frozen as `D0_PCA_SPE_V1`; its normal-only PCA model and
normal-train3 threshold are frozen and integrity-audited. D0 execution remains
unauthorized pending exact test1 raw-byte custody restoration.

## Current authorization state

The frozen D0 design, model, threshold, and model-threshold integrity
authorities remain exact. The D0 execution-authorization contract was frozen
at `4229e7c108c350174c03e4de0023ede3da8c1034` and its independent audit at
`c6481e201a11708ed0ef3d746e8057f627fb97d0`. All 26 public artifacts and 50
cross-bindings replayed; 90 static/regression tests passed and 88 independent
invalid attacks were rejected.

The sole real preflight failed closed because both exact test1 raw files were
unavailable at the approved local HAI binding. The attempt was not retried and
no authorization was issued. No test1 feature or label scientific parsing,
detector execution, metric computation, D1/D2 execution, test2 access, or
private path/value exposure occurred.

## Frozen custody

- D0 detector: `D0_PCA_SPE_V1`.
- Preprocessing content hash:
  `baae5495094b211731e4fcdf7bab2870e3c81e7c973bfe052fc87b457ccb6270`.
- PCA model content hash:
  `f32943cc2172100c77514d9ce8f6731978b51934e753234b2d34b5154127b54b`.
- Threshold content hash:
  `7ac0628cad5983b9864d31a9984bd414867b80f175248dbdf5cd69d7589f3695`.
- Model receipt:
  `913f4a4bcf1771146f9493cded893b10eb97d2d177fe224f855c289d81ef1362`.
- Threshold receipt:
  `2ee6fc8aba25d23449c14b08deae2eca0c5b739f6a251e43ead41923c978d326`.
- Readiness:
  `fcba1018b1e42ff7fdda9467a02a4f902ec6803486a3847675752508537cda29`.
- Bundle:
  `fa041f5e0006fc56665d22c82eb0fdea51917e573ffc4946c8a3f83bf4ada1e6`.
- Receipt:
  `b4142789cbe99513c1763df15e0207588b75453829d2abe1aba4eaa60da75357`.

Private means, scales, eigenvalues, loadings, threshold value, and paths remain
outside Git. Their hashes, not their local paths, are public custody identity.

## Authorization boundary

D0 INNER execution remains unauthorized and unexecuted. D1 remains frozen,
D2 and OUTER remain unauthorized, and test2 remains sealed. The frozen D0
model and threshold were not retrained or recalibrated.

## Exact next task

`TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-AUTHORIZATION-TEST1-CUSTODY-RESTORATION-V1`.

It must restore only the exact official test1 feature and label raw-byte
custody at the approved ignored binding, verify their frozen sizes and hashes,
and perform a newly authorized authorization preflight process. It must not
parse scientific values, access test2, retrain, recalibrate, or execute D0.

## Canonical evidence

- Training Implementation Commit A: `34edab1dc148fdd82a050c3446e87d6eda4f95fe`
- Independent Audit Commit B: `1041b6ed1efc335b8f5c5fe50dbfc22a87ec6d44`
- Model/Threshold Freeze Commit C: `44ce989d7f50e2722eed70963e030ba1ba44fadf`
- D0 Authorization Contract Commit A: `4229e7c108c350174c03e4de0023ede3da8c1034`
- D0 Authorization Independent Audit Commit B: `c6481e201a11708ed0ef3d746e8057f627fb97d0`
- D0 Authorization Blocker Report Commit: `bb2e77c396bf321d61e1c9b7247582a0ccaa3636`
- D0 Authorization Blocker: `480123d5398d064834ffe904c43611ec7043a1508581f5ec66487747dfb0a584`
- D0 design hash: `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`
- Implementation audit: `545a9082e84dd350dfc2df941f70021932879e73020462cdb76075b6c20d58a5`
- Accounting: `ca7f038c1c91b24feee38101c9d8b19cfe97a3dc417c32cee879f47942eed5f4`
- Readiness: `fcba1018b1e42ff7fdda9467a02a4f902ec6803486a3847675752508537cda29`
- Bundle: `fa041f5e0006fc56665d22c82eb0fdea51917e573ffc4946c8a3f83bf4ada1e6`
- Receipt: `b4142789cbe99513c1763df15e0207588b75453829d2abe1aba4eaa60da75357`

## No-claim boundary

This task certifies protocol-faithful normal-only training, calibration, and
freeze. It does not certify model quality, authorize test evaluation, compare
D0 with D1, or authorize D2/OUTER.

## D0 model/threshold integrity audit PASS

The exact frozen D0 preprocessing, PCA model, threshold, and Commit-C public
bytes passed independent integrity audit. Audit-only NumPy recomputation
reproduced all three private content hashes, selected `k=10`, 27 residual
dimensions, no exact tied cutoff, `q_index=125873`, and the frozen train4
sanity arithmetic. The audit performed zero authoritative fits and zero
authoritative calibrations.

- Audit Commit A: `0a5f8ef4a6eea38e2661fe2a6a3d24c849133f2d`
- Audit Report Commit B: `0dd53fbbc36b0483d90a5161caab7946ddd6d1fc`
- Readiness: `4849661e894bb3c6d31e3a97451ae3cb596bfb4cf231388514935e64ee460b19`
- Bundle: `5769e397c078680ab66bff7f698ccbd0c65f929430465543320a06714b7707ce`
- Receipt: `4a66590a223f17bf363521f1d2e5e2b8f184b85d43500a8f6683b88f9648119c`

D0 INNER is authorization-ready but remains unauthorized and unexecuted. D2
and OUTER remain unauthorized. Exact next task:
`TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-AUTHORIZATION-V1`.
