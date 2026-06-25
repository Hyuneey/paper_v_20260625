# DEC-007 Precheck Report

## Summary

Prepared the next-step DEC-007 provenance precheck package after TASK-014.

This work records public iTrust dataset/terms evidence, preserves DEC-007 as
unresolved, and adds a pending final SWaT protocol config that keeps final test
access disabled.

## Changed files

- `docs/DEC007_SWAT_PROVENANCE_PRECHECK.md`
- `configs/evaluation/dec007_final_swat_protocol_pending.json`
- `docs/DECISIONS_REQUIRED.md`
- `docs/task_reports/DEC-007_PRECHECK_REPORT.md`

## Interfaces added or changed

No code interfaces were added.

## Design decisions and rationale

- Did not resolve DEC-007 without researcher-owned source and terms decisions.
- Recorded official iTrust public pages as provenance evidence.
- Kept the current Kaggle/local CSV files as smoke-test-only.
- Added a pending final protocol config with final test access disabled.

## Commands run

```powershell
Get-Content -LiteralPath configs\evaluation\dec007_final_swat_protocol_pending.json | python -m json.tool | Out-Null
git diff --check
git ls-files dataset external
```

## Test, lint, and type-check results

No code changed. JSON validation, diff whitespace check, and raw-data tracking
checks were run before commit.

## Artifacts produced

- `docs/DEC007_SWAT_PROVENANCE_PRECHECK.md`
- `configs/evaluation/dec007_final_swat_protocol_pending.json`

## Research-invariant checks

- DEC-007 remains unresolved.
- No final test data was accessed.
- No raw SWaT data was read, copied, or tracked.
- No final SWaT benchmark was run.
- No benchmark or thesis-result claim was made.

## Known limitations

- Public iTrust pages establish request/terms context, but not this project's
  dataset approval record.
- Kaggle file-level provenance and terms remain unverified.
- Final evaluation remains blocked until the researcher resolves DEC-007.

## Unresolved decisions / recommended next task

Resolve DEC-007 by choosing official iTrust files or an approved Kaggle mirror
policy, acknowledging terms, recording exact file hashes, and approving the
final split and metric protocol.
