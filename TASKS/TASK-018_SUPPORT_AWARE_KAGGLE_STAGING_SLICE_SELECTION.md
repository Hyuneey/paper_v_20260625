---
id: TASK-018
title: Support-aware Kaggle staging slice selection
status: complete
depends_on: [TASK-017]
phase_gate: null
suggested_branch: task-018-support-aware-staging-slice
---

# TASK-018: Support-Aware Kaggle Staging Slice Selection

## 1. Goal

Find a Kaggle/local staging calibration slice with sufficient normal transition
support for predeclared actuator-sensor relation profiling.

This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.

## 2. Dataset policy

- Use `SWAT_DATA_ROOT`.
- Use `merged.csv` as the only staging timeline source.
- Do not combine `normal.csv`, `attack.csv`, and `merged.csv`.
- Use `StagingSwatMirrorManifest`, not `OfficialSwatProvenanceManifest`.
- Keep DEC-007 unresolved.
- Do not use labels for support-based slice selection.

## 3. Selection policy

Selection criteria are fixed in
`configs/data/task018_support_aware_staging.json` before scanning:

- minimum trigger count: 1
- minimum matched response count: 1
- maximum right-censored ratio: 0.5
- allowed sources: `MV101`, `P101`, `P102`, `MV201`
- allowed targets: `FIT101`, `LIT101`, `AIT201`, `AIT202`
- maximum slice length: 4096 rows
- search step: 512 rows
- labels policy: `ignored_for_selection_audit_only`
- require complete configured pipeline features
- require regular timestamp sampling

## 4. Outputs

- `configs/data/task018_support_aware_staging.json`
- `docs/task_reports/TASK-018_SUPPORT_SCAN_REPORT.json`
- `docs/task_reports/TASK-018_DRY_RUN_REPORT.json`
- `docs/task_reports/TASK-018_REPORT.md`

## 5. Completion notes

- The support scan used only `merged.csv`.
- The selected loaded range was `[12800, 15912]`.
- The selected calibration range was `[13332, 15380]`.
- The selected slice had 2 supported predeclared pairs by aggregate support
  criteria.
- The support-aware dry-run produced 2 verified template rules.
- Runtime executed deterministically on the staging validation split with 0
  firings.
- No raw rows, windows, or plots were tracked.
- This remains a staging implementation-debugging result only.
