# TASK-006 Completion Report

## Summary

Implemented high-resolution relation profiling and normal-data calibration for
the first supported relation type: binary actuator to continuous sensor.

The implementation uses only `calibration_normal` and `canonical_rule_view`.
It derives deterministic trigger/response summaries, calibration records, and
aggregate evidence packs from synthetic fixtures. No raw SWaT rows were loaded
or persisted.

## Changed files

- `src/paperworks/profiling/__init__.py`
- `src/paperworks/profiling/relations.py`
- `src/paperworks/__init__.py`
- `tests/test_relation_profiling.py`
- `configs/profiling/task006_synthetic_smoke.json`
- `docs/RELATION_PROFILING.md`
- `docs/DECISIONS_REQUIRED.md`
- `TASKS/TASK-006_RELATION_PROFILING_AND_CALIBRATION.md`
- `docs/task_reports/TASK-006_REPORT.md`

## Interfaces added or changed

Added:

- `RelationProfilingConfig`
- `TriggerEvent`
- `ResponseEvent`
- `RelationProfile`
- `CalibrationRecord`
- `RelationEvidencePack`
- `profile_binary_actuator_to_continuous_sensor()`
- `calibrate_relation_profile()`
- `build_relation_evidence_pack()`

Changed:

- Exported `paperworks.profiling` from the root package.

## Design decisions and rationale

- Kept TASK-006 scoped to binary-actuator to continuous-sensor pairs only.
- Rejected non-`calibration_normal` splits through the existing split permission policy.
- Rejected non-`canonical_rule_view` inputs to prevent GDN-view downsampling from entering rule calibration.
- Used explicit `INSUFFICIENT_NORMAL_SUPPORT` status instead of fabricating parameters for weak profiles.
- Added DEC-011 for the synthetic-smoke calibration policy:
  - trigger `0.0 -> 1.0`,
  - response as first positive target increase within the configured window,
  - delay quantile `1.0`,
  - magnitude quantile `0.0`,
  - minimum matched normal responses `2`,
  - irregular timestamp gaps rejected.
- Marked DEC-011 as an implementation smoke policy only, not a final SWaT calibration or evaluation decision.

## Commands run

```powershell
$env:PYTHONPATH="C:\Users\hyun\Desktop\paperworks\260625\src"
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_relation_profiling -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q src tests
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m json.tool configs\profiling\task006_synthetic_smoke.json
git diff --check
```

## Test, lint, and type-check results

TASK-006 tests:

```text
Ran 10 tests
OK
```

Full unit suite:

```text
Ran 59 tests
OK
```

`compileall` passed. The TASK-006 config passed JSON validation.
`git diff --check` passed with Git CRLF warnings only. Dedicated lint/type-check
commands are not configured yet.

## Artifacts produced

- `configs/profiling/task006_synthetic_smoke.json`
- `docs/RELATION_PROFILING.md`
- `docs/task_reports/TASK-006_REPORT.md`

The profiling/calibration artifact schemas are implemented in code and covered
by round-trip tests. No raw sequence artifact was written to Git.

## Research-invariant checks

- No test split, attack label, or sealed test outcome is accepted for profiling or calibration.
- Runtime remains LLM-free; no LLM code path was added.
- GDN relations remain candidate inputs only; no causal language or root-cause claim was added.
- Numeric calibration values come only from deterministic normal-data profile records.
- Evidence packs contain aggregate/provenance fields, not raw SWaT rows.
- The implementation uses synthetic fixtures only for tests.

## Known limitations

- The policy is synthetic-smoke only and does not finalize SWaT calibration thresholds.
- Only positive responses to binary actuator `0.0 -> 1.0` transitions are supported.
- The irregular sampling policy currently supports reject-only behavior.
- No real SWaT profiling run was performed in this task.

## Unresolved decisions / recommended next task

- DEC-007 remains open for official SWaT provenance and final evaluation protocol.
- Before real SWaT calibration, approve or replace DEC-011 with a research-grade calibration policy.
- Recommended next task: TASK-007 minimal DSL and schema registry.
