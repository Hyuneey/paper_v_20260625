# Captured Rule Semantic Audit

TASK-027 audits the fixed TASK-026Q rule with Python AST parsing only. The
captured module was not imported or executed, and no provider was contacted.

## Frozen Lineage

- ARGOS commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Request SHA-256:
  `14af5d91248f3ca579a445527768264f148497d58d85b49b96b39b8873918aca`
- Response SHA-256:
  `f7a1241323c98b716c651dac797cd502c0fd2c7b3c2a7b6142f34e8bbb418810`
- Rule SHA-256:
  `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659`
- Selected KPI ID: `05f10d3a-239c-3bef-9bdc-a2feeb0037aa`

The rule hash was rechecked before semantic parsing, frozen-policy validation,
risk review, and report persistence. All four checks matched.

## Redacted AST Findings

- Top-level statements: one import and one function definition.
- Imported module: `numpy` only.
- Defined function: one `inference` function.
- Input access: all rows from column index `0`.
- Output: a one-dimensional label array sized from the input row count.
- Numeric constants with context: `18` records.
- Assignments: `27` redacted expression records.
- Comparisons: `3` redacted expression records.
- Derived threshold records: `6`.
- Subscript and slicing records: `10`.
- Loops: `2`, both with AST-recorded bound sources.
- Output initialization sites: `1`.
- Output mutation sites: `1`.

The complete redacted expressions and numeric contexts are in
`docs/task_reports/TASK-027_RULE_SEMANTIC_AUDIT.json`. The report contains no
raw rule text or private KPI rows.

## Semantic Risk Review

- Empty input has an explicit zero-length return before column access.
- Constant-series handling has a positive scale floor and an absolute boundary.
- Partial nonfinite values are masked, while all-nonfinite input returns the
  initialized output. This remains a medium-risk static inference until tested.
- Short-series ranges are clamped to valid bounds.
- Exclusive upper slice bounds require manual off-by-one review.
- No uninitialized output path was identified by the AST review.
- One-dimensional or zero-column input is not guarded and may fail.
- Nonnumeric column values may fail during floating-point conversion.

These findings describe code semantics only. They do not establish rule
correctness, anomaly-detection performance, explanation quality, or ARGOS
benchmark fidelity.

## Frozen Static Policy

Observed calls exactly matched this fixed allowlist:

```text
max
min
numpy.abs
numpy.any
numpy.asarray
numpy.empty
numpy.flatnonzero
numpy.isfinite
numpy.maximum
numpy.median
numpy.nanmedian
numpy.zeros
range
```

Observed attributes exactly matched the frozen attribute list in the TASK-027
config. Any new import, call, attribute, dynamic attribute operation, dunder
attribute, global mutation, or executable top-level statement is rejected.
Allowing `numpy` does not permit arbitrary `numpy.*` APIs.

## Provider Request Lineage

- TASK-026: two separately approved provider-error requests.
- TASK-026R: one separately approved provider-error request.
- TASK-026Q: one separately approved successful request.
- Total separately approved provider requests: `4`.

TASK-026Q itself used exactly one request. No response-driven prompt tuning
occurred. DEC-030 remains consumed and was not re-enabled.
