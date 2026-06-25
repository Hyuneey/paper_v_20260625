# TASK-015 Completion Report

## Summary

Prepared the DEC-007 official SWaT provenance resolution package.

The project now has a local-only official SWaT provenance manifest schema,
approved-file SHA-256 helper, official iTrust request/approval checklist,
terms acknowledgement fields, final split/metric freeze template, Git artifact
policy, and sealed-test one-way execution log template.

DEC-007 remains unresolved and no final SWaT evaluation was run.

## Changed files

- `TASKS/TASK-015_DEC007_OFFICIAL_SWAT_PROVENANCE.md`
- `src/paperworks/data/official_swat.py`
- `src/paperworks/data/__init__.py`
- `tests/test_official_swat_manifest.py`
- `docs/DEC007_OFFICIAL_SWAT_RESOLUTION_PACKAGE.md`
- `TEMPLATES/OFFICIAL_SWAT_PROVENANCE_MANIFEST_TEMPLATE.json`
- `docs/templates/SEALED_TEST_EXECUTION_LOG_TEMPLATE.md`
- `configs/evaluation/task015_dec007_resolution_freeze_template.json`
- `docs/DECISIONS_REQUIRED.md`
- `docs/task_reports/TASK-015_REPORT.md`

## Interfaces added or changed

Added:

- `OfficialSwatFileRecord`
- `OfficialSwatProvenanceManifest`
- `OfficialSwatManifestError`
- `hash_approved_swat_file()`
- `build_official_swat_file_record()`

Changed:

- Exported official SWaT provenance helpers from `paperworks.data`.

## Design decisions and rationale

- Kept the official iTrust request route as the preferred final-evaluation source.
- Kept local/Kaggle CSV files as `local_unverified_smoke_test`.
- Implemented hashing and manifest schema without opening final test data.
- Blocked `final_test_opened=true` in the TASK-015 manifest schema.
- Kept point-adjusted metrics supplementary only in the freeze template.

## Commands run

```powershell
$env:PYTHONPATH="C:\Users\hyun\Desktop\paperworks\260625\src"
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_official_swat_manifest -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q src tests
Get-Content -LiteralPath configs\evaluation\task015_dec007_resolution_freeze_template.json | & "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m json.tool | Out-Null
Get-Content -LiteralPath TEMPLATES\OFFICIAL_SWAT_PROVENANCE_MANIFEST_TEMPLATE.json | & "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m json.tool | Out-Null
git diff --check
git ls-files dataset external
```

Static safety scan:

```powershell
# AST scan over src/paperworks for exec/eval/compile/__import__/subprocess/requests calls.
# Result: []
```

## Test, lint, and type-check results

TASK-015 tests:

```text
Ran 5 tests
OK
```

Full test suite:

```text
Ran 151 tests in 0.272s
OK
```

Additional checks:

- `python -m compileall -q src tests`: passed.
- `python -m json.tool configs\evaluation\task015_dec007_resolution_freeze_template.json`: passed.
- `python -m json.tool TEMPLATES\OFFICIAL_SWAT_PROVENANCE_MANIFEST_TEMPLATE.json`: passed.
- `git diff --check`: passed; Git reported CRLF normalization warnings only.
- `git ls-files dataset external`: no tracked raw dataset or upstream reference files.
- Static AST safety scan: no `exec`, `eval`, `compile`, `__import__`, `subprocess`, or `requests` calls found under `src/paperworks`.

## Artifacts produced

- `docs/DEC007_OFFICIAL_SWAT_RESOLUTION_PACKAGE.md`
- `TEMPLATES/OFFICIAL_SWAT_PROVENANCE_MANIFEST_TEMPLATE.json`
- `docs/templates/SEALED_TEST_EXECUTION_LOG_TEMPLATE.md`
- `configs/evaluation/task015_dec007_resolution_freeze_template.json`

## Research-invariant checks

- DEC-007 remains unresolved.
- No sealed final test was opened.
- No final SWaT benchmark was run.
- No raw SWaT rows, windows, raw sequence plots, or downloadable derived samples were committed.
- Current local/Kaggle CSV files remain smoke-test-only.
- No point-adjusted metric was promoted to primary.

## Known limitations

- This task prepares the resolution package; it does not supply the private
  iTrust request/approval record.
- The researcher must still acknowledge terms and provide approved file hashes.
- Final split and metric protocols must be filled and approved before final test access.

## Unresolved decisions / recommended next task

DEC-007 can be resolved only after the eight researcher-approved criteria are
complete: source, terms, edition/files, hashes, split protocol, metric protocol,
sealed-test policy, and Git artifact policy.
