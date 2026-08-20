# Session handoff

- Repository: `Hyuneey/paper_v_20260625`
- D0 Design Commit A: `4bdb16701a84b383f713629524a20900bba27d95`
- Independent Audit Commit B: `4e4e904cca8779e5dde62bcea697e6d40d58a867`
- Design Freeze Commit C: `2528632fca2c64e1bd4a293d57bed56cc3e5665b`
- Latest task: `TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-BASELINE-DESIGN-AND-FREEZE-V1`
- Latest status: `passed_task039e3_r2r_utility_inner_d0_detector_baseline_design_and_freeze_v1`
- Scientific status: `D0_DETECTOR_DESIGN_FROZEN`
- Active task: `NONE`
- Exact next task: `TASK-039E3-R2R-UTILITY-INNER-D0-DETECTOR-NORMAL-TRAINING-AND-CALIBRATION-V1`

## What completed

The reference D0 detector is preregistered as deterministic normal-only
PCA-SPE. The exact complete P1 public feature schema, split roles,
standardization, PCA component policy, SPE score, train3 order-statistic
threshold, alarm episodes, and D1-compatible primary metrics are frozen.
Static tests passed and 71 independent invalid mutations were rejected with
accepted invalid equal to zero.

No feature value, label, test1 value, test2 value, or D1 performance artifact
was read for design. No model fit, threshold computation, or detector execution
occurred.

## Frozen D0 design custody

- Detector: `D0_PCA_SPE_V1`
- Design hash: `357d19d02dee73273d52c7b147b5ddcfa11ead43a7198f2bf089ec78c2d8e174`
- Feature count: `37`
- Feature set hash: `6dea06e82c0d99f35a0d11c5e97503e8bb3a0fc8c1d9963b997986021fd23515`
- Feature order hash: `a612bdb9850ad0dd865dc62b23199bf2b696452c492e4aabe09fe554fa246d57`
- Readiness: `533e62761efce660e1d10726268187c2a9ba5e0d2b0763814b64bd75b0473c4e`
- Bundle: `8fa5ab4b81a4dad0f7d1d13bd356b3aad21a45e747cd3b047ada697450ce3034`
- Receipt: `61299eba73c09faaf9396a6174ad487e4736c6271e274a2c18dd3cb60fd0c8b5`

## Next-task mandate

Consume the exact design authority; do not redesign it. Materialize only the
authorized normal train1/train2/train3 inputs, fit deterministic PCA, select
`k` under the frozen `0.95` policy, and freeze the normal-train3 empirical
threshold at alpha `0.001`. Train4 may be evaluated only after model and
threshold freeze and may not cause tuning.

## Mandatory boundaries

- Do not open test1, label-test1, test2, or label-test2.
- Do not read D1 metrics or prediction content.
- Do not change detector family, P1 feature scope/order, scaler, PCA target,
  threshold policy, episode policy, or metrics.
- Do not authorize or execute D0 INNER, D2, fusion, detector runtime, or OUTER.
- Keep private model/preprocessing/threshold numeric contents and paths out of
  Git and public output; expose only sanctioned hashes and metadata.
- Preserve exact frozen D1 RulePrediction
  `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682`
  for future D2; do not rerun D1.

## Read and replay

1. `AGENTS.md`
2. `docs/project_state/START_HERE.md`
3. `docs/project_state/CURRENT_STATE.json`
4. this handoff
5. the next user-issued task specification
6. the D0 design receipt and report in Design Freeze Commit C
7. the exact design module/config in Commit A
8. the independent audit test in Commit B
9. the frozen D1 result-integrity receipt and RulePrediction hash
