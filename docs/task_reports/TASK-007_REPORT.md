# TASK-007 Completion Report

## Summary

Implemented the minimal safe JSON/AST DSL and schema registry for the initial
binary-actuator to continuous-sensor response-missing rule family.

The DSL supports:

- `changed_to`
- `increase_within`
- `response_missing`

The evaluator is deterministic and imports no LLM packages. It does not execute
generated Python or user-provided code.

## Changed files

- `src/paperworks/dsl/__init__.py`
- `src/paperworks/dsl/rules.py`
- `src/paperworks/__init__.py`
- `tests/test_dsl_rules.py`
- `configs/dsl/minimal_rule_schema_v1.json`
- `docs/MINIMAL_DSL.md`
- `TASKS/TASK-007_MINIMAL_DSL_AND_SCHEMA_REGISTRY.md`
- `docs/task_reports/TASK-007_REPORT.md`

## Interfaces added or changed

Added:

- `RuleAst`
- `CalibrationValueRef`
- `ChangedToPredicate`
- `IncreaseWithinPredicate`
- `ResponseMissingPredicate`
- `PlannerProvenance`
- `RuleSchemaRegistry`
- `RuleEvaluator`
- `MinimalRuleEvaluator`
- `TimeSeriesWindow`
- `RuleEvaluation`
- `SchemaIssue`
- `parse_rule_json()`
- `serialize_rule_json()`
- `format_rule()`

Changed:

- Exported `paperworks.dsl` from the root package.

## Design decisions and rationale

- Used a narrow AST instead of arbitrary expressions.
- Required rule-level and predicate-level calibration references to match exactly.
- Required serialized numeric values to match supplied `CalibrationRecord` objects.
- Kept compatibility limited to `binary actuator -> continuous sensor`.
- Derived human-readable text from AST fields, not free-form planner text.
- Used stable machine-readable issue codes such as `TYPE_MISMATCH`,
  `CALIBRATION_MISSING`, and `NUMERIC_PARAMETER_MUTATED`.

## Commands run

```powershell
$env:PYTHONPATH="C:\Users\hyun\Desktop\paperworks\260625\src"
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_dsl_rules -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q src tests
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m json.tool configs\dsl\minimal_rule_schema_v1.json
git diff --check
```

## Test, lint, and type-check results

TASK-007 tests:

```text
Ran 12 tests
OK
```

Full unit suite:

```text
Ran 71 tests
OK
```

`compileall` passed. The DSL JSON schema passed JSON parsing.
`git diff --check` passed with Git CRLF warnings only. Dedicated lint/type-check
commands are not configured yet.

## Artifacts produced

- `configs/dsl/minimal_rule_schema_v1.json`
- `docs/MINIMAL_DSL.md`
- `docs/task_reports/TASK-007_REPORT.md`

## Research-invariant checks

- No test labels, attack labels, or sealed outcomes were used.
- Runtime rule evaluation is deterministic and LLM-free.
- Numeric parameters must reference calibration records.
- LLM/planner output is constrained to the JSON DSL AST.
- Human-readable explanations are derived from AST fields.
- No raw SWaT rows or derived raw sequence artifacts were produced.

## Known limitations

- Only one rule family is supported.
- The evaluator handles the initial response-missing semantics only.
- JSON schema parsing is validated, but no external JSON Schema validator
  dependency was added.
- Real rule construction from relation evidence packs is deferred to TASK-008.

## Unresolved decisions / recommended next task

- DEC-007 remains open for official SWaT provenance and final evaluation protocol.
- DEC-011 remains synthetic-smoke only until a research-grade calibration policy is approved.
- Recommended next task: TASK-008 deterministic template rule builder.
