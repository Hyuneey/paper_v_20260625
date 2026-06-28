---
id: TASK-016
title: Kaggle SWaT staging adapter and development run
status: complete
depends_on: [TASK-015]
phase_gate: null
suggested_branch: task-016-kaggle-swat-staging
---

# TASK-016: Kaggle SWaT Staging Adapter and Development Run

## 1. Goal

Implement a staging-only SWaT mirror data path for the existing local/Kaggle CSV
files. The path supports implementation debugging, schema inspection, local
data loading, column normalization, metadata mapping, and aggregate staging
reports.

This task does not resolve DEC-007 and does not produce final benchmark claims.

## 2. Architecture context

The adapter sits in `src/paperworks/data/` beside the official SWaT provenance
schema, but it deliberately uses a separate `StagingSwatMirrorManifest` rather
than `OfficialSwatProvenanceManifest`.

## 3. Preconditions

- DEC-007 remains open.
- TASK-015/TASK-015A official provenance schema exists but is not used here.
- Local CSV files are accessed only through `SWAT_DATA_ROOT`.
- Raw CSV files remain ignored and untracked.

## 4. Inputs

- `SWAT_DATA_ROOT/normal.csv`
- `SWAT_DATA_ROOT/attack.csv`
- `SWAT_DATA_ROOT/merged.csv`
- `configs/metadata/swat_variables.json`
- `configs/data/task016_kaggle_staging.json`

## 5. Required outputs

- `StagingSwatMirrorManifest`
- `StagingSwatFileRecord`
- `StagingSwatDevelopmentReport`
- `docs/task_reports/TASK-016_STAGING_REPORT.json`
- `docs/task_reports/TASK-016_REPORT.md`

## 6. In scope

- staging-only schema inspection,
- staging-only data loading,
- header whitespace normalization,
- SHA-256 hashing,
- row and label aggregate counts,
- timestamp/index column recording,
- inferred sampling interval from sampled timestamps,
- metadata coverage check against the project SWaT metadata file.

## 7. Out of scope

- resolving DEC-007,
- opening official sealed final test data,
- running a final SWaT benchmark,
- using Kaggle/local results as final thesis claims,
- committing raw rows, windows, plots, or derived redistributable samples,
- tuning thresholds, K, prompts, or rules from staging performance.

## 8. Required report language

Every TASK-016 report must state:

"This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim."

## 9. Acceptance criteria

1. `StagingSwatMirrorManifest` records source kind, staging status, filenames,
   hashes, row counts, columns, label schema, timestamp/label columns, inferred
   sampling interval, and known limitations.
2. The implementation does not use `OfficialSwatProvenanceManifest`.
3. Tests cover successful manifest creation, JSON round trip, env-root loading,
   header normalization, irregular sampling recording, unsafe paths, and
   final-claim blocking.
4. Actual local development report is aggregate-only and contains no raw rows or
   windows.
5. `git ls-files dataset external` remains empty.

## 10. Completion notes

- Added staging-only manifest and report schemas.
- Added synthetic tests for adapter behavior and governance constraints.
- Generated aggregate staging development report from local files through
  `SWAT_DATA_ROOT`.
- DEC-007 remains unresolved.
