---
id: TASK-017
title: Kaggle staging pipeline dry-run
status: complete
depends_on: [TASK-016]
phase_gate: null
suggested_branch: task-017-kaggle-staging-dry-run
---

# TASK-017: Kaggle Staging Pipeline Dry-Run

## 1. Goal

Run the existing deterministic pipeline on Kaggle/local staging data for
implementation debugging only.

This is not an official SWaT benchmark and must not be used as a final thesis
performance claim.

## 2. Dataset policy

- Use `SWAT_DATA_ROOT`.
- Use `StagingSwatMirrorManifest`, not `OfficialSwatProvenanceManifest`.
- DEC-007 remains unresolved.
- Use exactly one declared staging timeline source.
- Default and actual pipeline source: `merged.csv`.
- Do not combine `normal.csv`, `attack.csv`, and `merged.csv`.

## 3. In scope

- load `merged.csv` as a staging timeline,
- normalize CSV headers,
- infer timestamp sampling,
- build staging split manifest,
- run metadata coverage,
- run candidate discovery smoke,
- run relation profiling smoke on a small predeclared subset,
- invoke template/rule/verifier path when supported profiles exist,
- run deterministic runtime on the staging validation split,
- write aggregate staging artifacts and reports.

## 4. Out of scope

- final SWaT benchmark,
- official sealed final test access,
- DEC-007 resolution,
- real provider or network calls,
- runtime LLM,
- point-adjusted primary metrics,
- threshold/K/prompt/rule tuning from staging performance,
- committing raw rows, windows, raw sequence plots, or downloadable derived samples.

## 5. Required report statement

"This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim."

## 6. Outputs

- `configs/data/task017_kaggle_staging_dry_run.json`
- `docs/task_reports/TASK-017_STAGING_SPLIT_MANIFEST.json`
- `docs/task_reports/TASK-017_DRY_RUN_REPORT.json`
- `docs/task_reports/TASK-017_REPORT.md`

## 7. Completion notes

- The dry-run used only `merged.csv` as the pipeline timeline source.
- `normal.csv` and `attack.csv` were not combined into the pipeline timeline.
- Candidate discovery ran on the configured feature subset.
- The predeclared profiling subset completed but produced
  `INSUFFICIENT_NORMAL_SUPPORT` for all attempted pairs in the configured
  staging slice.
- No verified rule was produced, so there is no detection-performance result.
- Runtime still executed on the validation split with an empty verified-rule
  library, producing zero firings.
- No raw rows, windows, or plots were tracked.
