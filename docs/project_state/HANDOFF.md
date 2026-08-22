# Session handoff

- Repository: `Hyuneey/paper_v_20260625`
- Branch: `task-039e3-r2r-utility-inner-d0-d1-d2-scientific-comparison-v1`
- Base: `f4367ac5b77a28088fab834018b170c8295e66c1`
- Comparison Commit A: `f1d26f83ab5d13c28a7f82909c4ae7e69d3b7aaf`
- Report Freeze Commit B: `f4e21a2a73adad16bd15898cbb5c01bb19646ba3`
- Status: `passed_task039e3_r2r_utility_inner_d0_d1_d2_scientific_comparison_v1`
- Scientific state: `INNER_D0_D1_D2_COMPARISON_FROZEN`
- Remote state: `LOCAL_ONLY_NOT_PUSHED`
- Exact next task: `TASK-039E3-R2R-UTILITY-INNER-D2-RECOVERY-SIGNAL-FAILURE-DIAGNOSTIC-V1`

## Frozen comparison

D0, D1, and D2 detected 11, 13, and 11 of 14 attack events. Their normal
false-alarm episode counts were 7, 574, and 10. D1 detected all three events
missed by D0; D2 detected none of those misses. D2 therefore retained zero of
D1's detector-miss recovery potential and added three normal false-alarm
episodes over D0.

- Classification: `RULE_SIGNAL_HAS_DETECTOR_MISS_RECOVERY_POTENTIAL_BUT_D2_GATE_FAILED_TO_RETAIN_IT`.
- D2 V1 incremental utility supported: `false`.
- Thesis status: `CURRENT_D2_COMBINED_UTILITY_NOT_SUPPORTED_ON_INNER`.
- OUTER disposition: `HOLD_PENDING_INNER_D2_FAILURE_DIAGNOSTIC`.
- Receipt: `d444ed1f7979270b945c03f2656b92e8ef7ebf8e98eca2f88f976999da00216e`.

The next task may diagnose the lost recovery signal using INNER evidence only.
It must not test alternative fusion policies, redesign D2, rerun any arm,
access test2 or OUTER, or push.
