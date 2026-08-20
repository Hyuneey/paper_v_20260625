# Current project state

## Research in one paragraph

This project studies graph-guided agentic construction of verified rules for
explainable multivariate time-series anomaly detection. The exact D1 Rule-only
result remains frozen and integrity-audited. The independent
`D0_PCA_SPE_V1` INNER test1 result is now also frozen and independently
integrity-audited. Scientific interpretation of D0 versus D1 may begin, but no
D2 design or execution is yet authorized.

## D0 result-integrity state

- Status: `passed_task039e3_r2r_utility_inner_d0_result_integrity_audit_v1`.
- Scientific state: `D0_RESULT_INTEGRITY_AUDITED`.
- Remote state: `LOCAL_ONLY_NOT_PUSHED`.
- Audit Commit A: `346a9f1ec6d5b1d97a66da45fcff66f44353742e`.
- Audit Report Commit B: `a1ff1929a86e95675431c2c32ace01efa2696a80`.
- Freeze audit: `8e22cb39ba038d3492592f4a3f91cbb64d2640d146dc615b35aab1137635fdc5`.
- Score oracle: `6c6e80549b9bc8f4e047c5db222af3de1647d7c0cee8684497d06eaff701df6e`.
- Prediction audit: `d76903177a1595870c841086aa0aa6debd302f679b71163fa4b38686975b37bc`.
- Metric oracle: `89f7b33e89d24cab74a589ec0efdaaf2c47acacc1693fff24729151a7a07bfaa`.
- Readiness: `b18ccca46ed84e09aedeb258f6089e07444da0c108a60f4da3160fb3a521282d`.
- Bundle: `9b74f9c56571526870f274e0928516ce642e1bc0d692ee3cdd8dce0cceddafc7`.
- Receipt: `15559141048efd729b3b4645b4f0baa4ac6d07ceedb2417cbd7915f49435da70`.

The audit resolved the exact four local execution commits, reproduced the
implementation identity and committed grant, and found zero Result-C
mutations. One audit-only feature parse independently reproduced all 54,000
PCA-SPE scores, the private score-evidence identity, 876 point alarms, 46 alarm
episodes, both frozen metrics, and the private metric-evidence identity. It
performed zero authoritative D0 executions, fits, or calibrations. All 33
invalid mutations were rejected.

## Authority boundary

D0 execution, result freeze, result integrity, and interpretation readiness are
true. D1 remains unchanged. D1 content reads, D1/D2/OUTER executions, test2
accesses, result-driven changes, and private leakage were zero. D2 and OUTER
remain unauthorized. The branch and all audit commits remain local-only; no
push, PR, or upload occurred.

## Exact next task

`TASK-039E3-R2R-UTILITY-INNER-D2-DESIGN-AND-FREEZE-V1`.

It must preregister D2 before any D2 result and consume the exact frozen D0 and
D1 prediction artifacts without rerunning either arm.
