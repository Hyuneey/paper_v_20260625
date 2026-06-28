# Kaggle SWaT Staging Path

This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.

## Purpose

TASK-016 adds a staging-only data path for the current local/Kaggle CSV files.
The path is intended for implementation debugging before official SWaT
provenance is resolved.

The staging path may inspect schema, load local CSV metadata, normalize column
headers, map variables to project metadata, and produce aggregate development
reports. It must not be used to resolve DEC-007 or make final SWaT benchmark
claims.

## Manifest

The staging path uses `StagingSwatMirrorManifest`, not
`OfficialSwatProvenanceManifest`.

Tracked fields include:

- `source_kind: kaggle_mirror`
- `dataset_status: staging_only`
- file names
- SHA-256 hashes
- file byte sizes
- row counts excluding header
- column names
- label counts and label schema
- timestamp, index, and label column names
- inferred sampling period from sampled timestamps
- known limitations

## Local Access

Set `SWAT_DATA_ROOT` to the local directory containing:

- `normal.csv`
- `attack.csv`
- `merged.csv`

The implementation must not assume the files are inside the Git working tree.
Raw CSV files, rows, windows, raw sequence plots, and redistributable derived
samples must not be committed.

## Development Report

The aggregate staging report is:

- `docs/task_reports/TASK-016_STAGING_REPORT.json`

It records aggregate metadata only. It does not contain raw time-series rows,
extracted windows, or final benchmark metrics.

## TASK-017 Pipeline Dry-Run

TASK-017 runs a staging-only deterministic pipeline dry-run with exactly one
timeline source:

- `merged.csv`

It does not combine `normal.csv`, `attack.csv`, and `merged.csv`. The split
manifest and dry-run report are:

- `docs/task_reports/TASK-017_STAGING_SPLIT_MANIFEST.json`
- `docs/task_reports/TASK-017_DRY_RUN_REPORT.json`

The configured TASK-017 run produced candidate artifacts and completed
predeclared profiling attempts, but the attempted pairs had insufficient normal
support in the configured staging slice and produced zero verified rules. That
is a staging debug result only, not a performance claim.

## Limitations

- DEC-007 remains unresolved.
- Current local/Kaggle files remain staging-only implementation inputs.
- The report is not an official iTrust provenance record.
- `normal.csv`, `attack.csv`, and `merged.csv` are all listed, so aggregate row
  and label counts may double-count merged plus label-filtered files.
- Staging outputs must not be used as final thesis performance claims.
