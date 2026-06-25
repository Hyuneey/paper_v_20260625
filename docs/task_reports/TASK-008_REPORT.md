# TASK-008 Completion Report

## Summary

Implemented the deterministic template rule builder that converts an approved
`RelationEvidencePack` plus `RuleSchemaRegistry` state into a candidate DSL
`RuleAst`.

The builder is a non-LLM baseline. It uses no raw time-series data, labels, test
split inputs, generated Python, or hard-coded SWaT variable names.

## Changed files

- `src/paperworks/planning/__init__.py`
- `src/paperworks/planning/template.py`
- `src/paperworks/dsl/rules.py`
- `src/paperworks/__init__.py`
- `tests/test_template_rule_builder.py`
- `docs/TEMPLATE_RULE_BUILDER.md`
- `TASKS/TASK-008_TEMPLATE_RULE_BUILDER.md`
- `docs/task_reports/TASK-008_REPORT.md`

## Interfaces added or changed

Added:

- `TemplateRuleBuildResult`
- `TemplateRuleBuildError`
- `build_template_rule()`

Changed:

- Added `RuleSchemaRegistry.metadata_for()`.
- Added `RuleSchemaRegistry.calibration_record_for()`.
- Exported `paperworks.planning` from the root package.

## Design decisions and rationale

- Kept the builder interface to `evidence` and `registry` only so raw/test data cannot enter this planning step.
- Used the existing minimal DSL family instead of adding a new rule family.
- Used fixed initial trigger constants `0.0 -> 1.0` consistent with the TASK-006/TASK-007 smoke contract.
- Constructed every numeric DSL value from a `CalibrationRecord` looked up through the registry.
- Returned explicit unsupported results instead of raising for ordinary unsupported scientific cases.
- Preserved planner provenance with `planner_type: deterministic_template`.

## Commands run

```powershell
$env:PYTHONPATH="C:\Users\hyun\Desktop\paperworks\260625\src"
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_template_rule_builder -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q src tests
git diff --check
```

Also ran an AST-based safety check for dynamic execution calls and risky imports
across `src/paperworks`.

## Test, lint, and type-check results

TASK-008 tests:

```text
Ran 11 tests
OK
```

Full suite, compile, and static safety checks were run before commit.

Full unit suite:

```text
Ran 82 tests
OK
```

`compileall` passed. `git diff --check` passed with Git CRLF warnings only.
The AST safety check returned `[]`. Dedicated lint/type-check commands are not
configured yet.

## Artifacts produced

- `docs/TEMPLATE_RULE_BUILDER.md`
- `docs/task_reports/TASK-008_REPORT.md`

No data artifacts or raw sequence outputs were produced.

## Research-invariant checks

- No LLM dependency or call path was added.
- No test split, attack label, or sealed outcome is accepted by the builder.
- No hard-coded SWaT variable pair appears in library logic.
- GDN/evidence relations remain candidate relations, not causal claims.
- Every generated numeric value references a calibration artifact.
- Unsupported inputs return explicit machine-readable issue codes.

## Known limitations

- Only the initial response-missing template family is supported.
- Trigger states are fixed to the current smoke contract `0.0 -> 1.0`.
- Real rule selection and verifier feedback are deferred to later tasks.

## Unresolved decisions / recommended next task

- DEC-007 remains open for official SWaT provenance and final evaluation protocol.
- DEC-011 remains synthetic-smoke only until a research-grade calibration policy is approved.
- Recommended next task: TASK-009 deterministic verifier.
