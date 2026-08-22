# Current project state

## Research in one paragraph

The exact integrity-audited D0, D1, and D2 predictions remain frozen. The
failure diagnostic found mixed structural mismatch: one D0-missed recovery
event was single-source-only; two had three sources event-wide but never two
sources in the same second; same-source multi-relation collapse also appeared.
All three normal D2 recovery false positives contained true exact-second
multi-source corroboration. D2 V2 redesign is scientifically justified but
not authorized; OUTER remains sealed.

## D2 result integrity audit

- Status: `passed_task039e3_r2r_utility_inner_d2_result_integrity_audit_v1`.
- Scientific state: `D2_RESULT_INTEGRITY_AUDITED`.
- Remote state: `LOCAL_ONLY_NOT_PUSHED`.
- Base: `33202f21d47b6bf29b12156374c9a7760f5c70f1`.
- Audit Commit A: `251fc953ad09f337a4e11bb956b3d1de1438e526`.
- Audit Report Commit B: `f7ae8f10e8e69e631c43184d6ea9cd3604829a9c`.
- Freeze audit: `ed2519a4023b6d258eaa8ad86f65b15e63c50336a8cf9b4f503027fd477e2496`.
- Fusion oracle: `0c3148c2f651f5707f5aa39ae018400653b7c375f027cddb8c06a223fb76feb5`.
- Prediction audit: `2bd70a56a7e9c5cfd255e54dda0d43697c7d5e3922d58a21e978614f74e2ea72`.
- Episode oracle: `c20e9e32624950e786c055e6c2ba200ca20e78b06685812727e553e738f3f653`.
- Metric oracle: `d933d62b4a067e0f71f6dac22b11b32ff1811857b047fde9e4d1f7e947116483`.
- Readiness: `56e49e58eea4693bf23e2a8b0fb17851f68e679015aa84fbcc874ce07161111c`.
- Bundle: `19ef39ab23c54f5e1c6a626f95f0e6d886e5fd22b7ac904e9221175d44477c91`.
- Receipt: `c45db852c6d5571ec7930fc12d815b383a29e31939e711eb5f2e84c69807b448`.
- Report self-hash: `01f770f1a6304e1bbf5b43934a32bd44aee99cd7ac718d0b116e89908432bbed`.

## Permanent attempt and safety accounting

- Historical D2 attempts: `1`.
- Recovery D2 attempts: `1`.
- Total D2 attempts: `2`.
- Infrastructure-aborted attempts: `1`.
- Completed scientific executions: `1`.
- Result-driven retries: `0`.
- Additional authorized attempts remaining: `0`.
- Third attempt authorized: `false`.
- Historical path exposure: `1`, `EPHEMERAL_PRIVATE_PATH_DISCLOSURE`.
- Recovery private-path exposures: `0`.
- Tracked private-path leaks: `0`.
- D0/D1 reruns, D0 scores, rule reevaluation, test1 feature access, test2,
  OUTER, result-driven changes, and push: `0`.

## Exact next task

`TASK-039E3-R2R-UTILITY-INNER-D2-V2-REDESIGN-DECISION-AND-PREREGISTRATION-V1`

That task may define one structurally motivated policy and preregister it. It
may not execute candidates, sweep parameters, access test2 or OUTER, rerun any
arm, or push.

## Frozen D2 recovery-signal failure diagnostic V1

- Status: `passed_task039e3_r2r_utility_inner_d2_recovery_signal_failure_diagnostic_v1`.
- Commit A/B: `78e016d4ff781581d998b445022dd2c35f61491a` / `0c40a0118c1c5f14cf3ca2d42178c34875d4dbed`.
- Failure classes: one `SINGLE_SOURCE_ONLY`, two `MULTI_SOURCE_ASYNCHRONOUS`.
- Dominant mechanism: `GATE_FAIL_MIXED_MECHANISMS`.
- Normal gate reference: `3 / 574` D1 false-alarm episodes satisfy the exact gate.
- D2 V2 redesign scientifically justified: `true`; authorized: `false`.
- Receipt: `58b0a68ad4a9e4e6938e14d031ae8f6e80a7e75a071081e651ac33e5f6872f0e`.

## Frozen INNER D0/D1/D2 comparison V1

- Status: `passed_task039e3_r2r_utility_inner_d0_d1_d2_scientific_comparison_v1`.
- Commit A/B: `f1d26f83ab5d13c28a7f82909c4ae7e69d3b7aaf` / `f4e21a2a73adad16bd15898cbb5c01bb19646ba3`.
- D0/D1/D2 detected attack events: `11 / 13 / 11` of `14`.
- D0/D1/D2 normal false-alarm episodes: `7 / 574 / 10`.
- D0 misses detected by D1/D2: `3 / 0`.
- Classification: `RULE_SIGNAL_HAS_DETECTOR_MISS_RECOVERY_POTENTIAL_BUT_D2_GATE_FAILED_TO_RETAIN_IT`.
- D2 V1 incremental utility supported: `false`.
- OUTER disposition: `HOLD_PENDING_INNER_D2_FAILURE_DIAGNOSTIC`.
- Readiness/bundle/receipt: `4101e47bd2e93303c74f078e2b5cd21172a10b260554f6d2a3f84b32b7582023` / `168a3566f6e8310168a8c282c6927d2d992dbd674235952bb9b1aa9a79ff5469` / `d444ed1f7979270b945c03f2656b92e8ef7ebf8e98eca2f88f976999da00216e`.
