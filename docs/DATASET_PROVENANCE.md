# Dataset Provenance

## Status

Dataset source is **partially identified but unverified**. The researcher supplied the Kaggle page `https://www.kaggle.com/datasets/vishala28/swat-dataset-secure-water-treatment-system` as the current local data source. Local SWaT-like CSV files are present, but exact file provenance, edition, terms-of-use status, and official train/test semantics have not been confirmed.

Resolved TASK-000 decisions classify these files as `local_unverified_smoke_test`. TASK-016 adds a separate staging-only path that treats the same local/Kaggle files as `kaggle_mirror_staging` for implementation debugging. Do not use these files for scientific claims or final evaluation.

TASK-016 required report statement:

> This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim.

## Local files inspected

Root: `dataset/swat`

Claimed source:

- Source kind: Kaggle mirror
- Source reference: `https://www.kaggle.com/datasets/vishala28/swat-dataset-secure-water-treatment-system`
- Public page title observed: `SWaT Dataset: Secure Water Treatment System | Kaggle`
- Notebook/version sync note: researcher reports the dataset will not continually sync with new notebook versions
- Terms-of-use status: unverified
- Dataset edition/version: unverified

## Researcher-supplied Kaggle notes

The researcher supplied the following non-row dataset description for provenance and metadata drafting:

- The dataset contains sensor and actuator measurements collected from the Secure Water Treatment (SWaT) testbed.
- It includes normal operational data and controlled cyber-attack scenarios.
- Measurements are timestamped and labeled with a `Normal/Attack` field.
- Collection was continuous from the SWaT testbed under normal operation and attack scenarios, with real-time logs for flow rates, tank levels, pump status, valve positions, analyzer measurements, and other process parameters.
- The supplied source description states that the data was sourced directly from the Secure Water Treatment industrial testbed operated by the contributing organization.

This information is sufficient for the current metadata draft and smoke-test data contract. It is not sufficient to mark the local files as official iTrust SWaT files, approve final evaluation claims, or mark terms of use as verified.

| File | Bytes | Rows excluding header | SHA-256 |
|---|---:|---:|---|
| `normal.csv` | 402374633 | 1387098 | `efa3dfd271fd33402d04ff4323d92ba739758bb2d4b9c6e9cc205980891f111f` |
| `attack.csv` | 15162438 | 54621 | `81977a6206ba954781df5481481ef1c39e94a405980f4f45b98e9c0a9cedadd2` |
| `merged.csv` | 426855390 | 1441719 | `5472928b8faf51430f4490628c6fe99487d58d5826a41460ab26aee69dde22a4` |

`merged.csv` row count equals `normal.csv + attack.csv`, which suggests `normal.csv` and `attack.csv` are label-filtered partitions of `merged.csv`.

## Schema

- Format: CSV
- Column count: 53
- Timestamp column: `Timestamp`
- Label column: `Normal/Attack`
- Feature count: 51
- Detected timestamp format: `%d/%m/%Y %I:%M:%S %p`
- Initial sampled interval: 1 second for the first inspected intervals

Feature columns:

```text
FIT101, LIT101, MV101, P101, P102, AIT201, AIT202, AIT203, FIT201, MV201,
P201, P202, P203, P204, P205, P206, DPIT301, FIT301, LIT301, MV301, MV302,
MV303, MV304, P301, P302, AIT401, AIT402, FIT401, LIT401, P401, P402, P403,
P404, UV401, AIT501, AIT502, AIT503, AIT504, FIT501, FIT502, FIT503, FIT504,
P501, P502, PIT501, PIT502, PIT503, FIT601, P601, P602, P603
```

## Label counts

| File | Normal | Attack |
|---|---:|---:|
| `normal.csv` | 1387098 | 0 |
| `attack.csv` | 0 | 54621 |
| `merged.csv` | 1387098 | 54621 |

## Timestamp metadata

| File | First timestamp | Last timestamp | Note |
|---|---|---|---|
| `normal.csv` | `2015-12-28 10:00:00` | `2015-12-28 09:59:59` | Full monotonicity not verified; label-filtering may remove timeline context. |
| `attack.csv` | `2015-12-28 10:29:14` | `2016-01-02 13:41:11` | Contains only attack-labeled rows. |
| `merged.csv` | `2015-12-28 10:00:00` | `2016-01-02 13:41:11` | Contains both labels. |

## Data-governance assessment

- Raw data currently resides under the workspace path.
- The root Git repository was initialized after `.gitignore` creation.
- `dataset/swat/*.csv` files are ignored by `.gitignore` and are not tracked by Git.
- Moving raw CSVs outside the repository and accessing them via `SWAT_DATA_ROOT` remains preferred.
- `SWAT_DATA_ROOT` should point to a local data directory; production code should not assume `dataset/swat` inside the repository.

## Blocking issues

1. Source kind is recorded as a researcher-supplied Kaggle mirror, but file-level provenance is still unverified.
2. Terms-of-use acknowledgement is not recorded.
3. Dataset edition/version is unverified.
4. The current files appear label-filtered, so official split semantics are not established.
5. `attack.csv` is not a complete attack-period evaluation timeline because it contains no normal-context rows.

## TASK-001 implementation status

The TASK-001 data-contract implementation supports these files only as local smoke-test inputs:

- `DatasetManifest.dataset_status` may be set to `local_unverified_smoke_test`.
- `resolve_data_root()` requires `SWAT_DATA_ROOT`.
- `validate_local_files()` verifies local fingerprints without copying data.
- `inspect_csv_metadata()` records schema, label counts, and regular sampling metadata without printing rows.
- Split manifests and data-view manifests reference the dataset manifest by stable hash.

Final evaluation remains blocked until DEC-007 is resolved with approved SWaT provenance and split semantics.

## TASK-016 staging implementation status

The TASK-016 staging adapter supports these files only as Kaggle/local staging
inputs:

- `StagingSwatMirrorManifest.source_kind` is fixed to `kaggle_mirror`.
- `StagingSwatMirrorManifest.dataset_status` is fixed to `staging_only`.
- `OfficialSwatProvenanceManifest` is not used.
- `SWAT_DATA_ROOT` is required for local access.
- Header whitespace is normalized before row parsing.
- The aggregate development report is stored at
  `docs/task_reports/TASK-016_STAGING_REPORT.json`.

The report contains file names, SHA-256 hashes, row counts, column names, label
counts, timestamp/label columns, inferred sampled intervals, metadata coverage,
and known limitations. It does not contain raw rows, windows, raw sequence
plots, or final benchmark metrics.
