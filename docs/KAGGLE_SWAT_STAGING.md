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

## TASK-018 Support-Aware Slice Selection

TASK-018 scans `merged.csv` for aggregate transition support on the same
predeclared actuator-sensor pairs, without using labels for selection.

The selection policy is fixed in
`configs/data/task018_support_aware_staging.json` before scanning. It requires
minimum trigger and matched-response support, a maximum right-censored ratio,
complete configured pipeline features, regular timestamp sampling, and a fixed
search step.

The generated reports are:

- `docs/task_reports/TASK-018_SUPPORT_SCAN_REPORT.json`
- `docs/task_reports/TASK-018_DRY_RUN_REPORT.json`

The selected loaded range was `[12800, 15912]`, and the selected calibration
range was `[13332, 15380]`. The selected slice had 2 supported predeclared
pairs by aggregate support criteria. The staging dry-run on that slice produced
2 verified template rules and 0 runtime firings.

This remains a Kaggle/local staging implementation-debugging result only. It is
not an official SWaT benchmark result and must not be used as a final thesis
performance claim.

## TASK-019 Rule Evidence Audit

TASK-019 reconstructs the two verified rules from TASK-018 as staging-only
evidence cards for human review.

The generated reports are:

- `docs/task_reports/TASK-019_RULE_EVIDENCE_AUDIT.json`
- `docs/task_reports/TASK-019_RULE_EVIDENCE_AUDIT.md`

Audited pairs:

- `MV201 -> AIT201`
- `MV201 -> AIT202`

The cards include source/target metadata, relation support counts, calibration
parameters, rule AST summaries, verifier aggregate metrics, runtime firing
counts, and blank human-review notes fields. They are implementation-debugging
artifacts only and are not performance or explanation-quality claims.

## TASK-020 Robustness and Synthetic Replay

TASK-020 scans additional fixed-stride support-aware staging slices and replays
the audited rules on synthetic non-SWaT mini-series.

The generated reports are:

- `docs/task_reports/TASK-020_RULE_ROBUSTNESS_REPORT.json`
- `docs/task_reports/TASK-020_SYNTHETIC_VIOLATION_REPLAY.json`

The robustness scan used only `merged.csv`, scanned 2,810 slices, and found 464
support-aware passing slices. Synthetic replay confirmed that both audited rules
fire on generated missing-response cases and do not fire when the generated
expected response occurs.

This is still staging implementation evidence only. It is not an official SWaT
benchmark result, final anomaly-detection performance, or explanation-quality
claim.

## Limitations

- DEC-007 remains unresolved.
- Current local/Kaggle files remain staging-only implementation inputs.
- The report is not an official iTrust provenance record.
- `normal.csv`, `attack.csv`, and `merged.csv` are all listed, so aggregate row
  and label counts may double-count merged plus label-filtered files.
- Staging outputs must not be used as final thesis performance claims.
