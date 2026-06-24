# TASK-001 Completion Report

## Summary

Implemented the first data foundation: local-only dataset manifests, data-view manifests, split manifests, split-role permission guards, raw-range validation, purge-gap calculation, and split-before-window generation. Tests use synthetic data only.

## Changed files

- `pyproject.toml`
- `src/paperworks/__init__.py`
- `src/paperworks/data/__init__.py`
- `src/paperworks/data/contracts.py`
- `src/paperworks/data/files.py`
- `src/paperworks/data/splits.py`
- `tests/__init__.py`
- `tests/test_data_contracts.py`
- `docs/DATA_CONTRACTS.md`
- `docs/DATASET_PROVENANCE.md`

## Interfaces added or changed

Added:

- `DatasetFile`
- `DatasetManifest`
- `DataViewManifest`
- `DataViewName`
- `SplitManifest`
- `SplitRole`
- `CsvMetadata`
- `WindowSpec`
- `resolve_data_root()`
- `sha256_file()`
- `validate_local_files()`
- `inspect_csv_metadata()`
- `build_data_view_manifest()`
- `build_sequential_split_manifests()`
- `generate_split_windows()`
- `assert_split_permitted()`
- `assert_no_overlapping_ranges()`
- `required_purge_gap()`

## Design decisions and rationale

- Used stdlib dataclasses and explicit validation to avoid early dependency churn.
- Used stable canonical JSON hashes for manifest IDs.
- Required `SWAT_DATA_ROOT` for local data access.
- Kept current SWaT CSVs smoke-test-only through `dataset_status: local_unverified_smoke_test`.
- Implemented split-before-windowing by generating windows only inside each split range.
- Added explicit split-role permissions so `test` cannot be used for training, profiling, calibration, or refinement.

## Commands run

```powershell
$env:PYTHONPATH="C:\Users\hyun\Desktop\paperworks\260625\src"
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q src tests
git check-ignore -v dataset/swat/normal.csv dataset/swat/attack.csv dataset/swat/merged.csv external/argos/README.md external/gdn/README.md
git ls-files dataset external
git status --short --branch
```

## Test, lint, and type-check results

Unit tests:

```text
Ran 9 tests
OK
```

`compileall` passed.

`pytest` was not run because it is not installed in the bundled Python environment. No lint or type-check command is configured yet.

## Artifacts produced

No research data artifacts were produced. TASK-001 produced source modules, documentation updates, and synthetic tests only.

## Research-invariant checks

- No raw SWaT rows or windows were committed.
- Tests use synthetic CSV rows only.
- `dataset/` and `external/` remain ignored and untracked.
- Split-role guards reject prohibited uses of `test`.
- View manifests record sampling period and upstream dataset manifest hash.

## Known limitations

- No CLI wrapper yet.
- Sequential split generation is implemented, but a full scientific split policy remains future work.
- Official SWaT provenance remains DEC-007.
- Optional downsampled GDN view is intentionally deferred.

## Unresolved decisions / recommended next task

Open decision:

- DEC-007: Official SWaT provenance upgrade before final evaluation / TASK-014.

Recommended next task:

- TASK-002: variable metadata schema and validation.

