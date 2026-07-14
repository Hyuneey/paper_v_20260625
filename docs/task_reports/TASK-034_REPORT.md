# TASK-034 Report

Status: `passed_validation_feasibility`

TASK-034 executed the frozen TASK-033 ARGOS rule on the validation partition of
the selected KPI series. This is a validation-only feasibility result. It is
not a benchmark or thesis-performance claim.

## Frozen execution

- Execution code commit: `b81468c4da9eaa52596088e6b0768e11739c8072`
- Rule SHA-256: `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659`
- Validation range: `[81902, 102378)`; 20,476 rows
- Held-out test range: `[102378, 146255)`; sealed and unparsed
- Container image ID: `sha256:536b8ca5008d864a300d731518b5c10efafc439677e3a08b225602d52fd3825d`
- Fresh container runs: 2
- Prediction SHA-256 for both runs: `911acaac45a1c7b6a40f60ddb114e6be74993be4687c9c7f94031be9ef671824`
- Predicted positives for both runs: 39

Isolation, output shape, binary domain, finite output, immutable image binding,
and deterministic replay checks passed. Validation labels were not mounted into
the container. No provider, ARGOS agent, detector, or fusion path ran.

## Validation diagnostics

Primary direct binary diagnostics were PA-free and used no threshold search:

- Precision: `0.8461538461538461`
- Recall: `0.18857142857142858`
- Point F1: `0.3084112149532711`
- Confusion counts: TP 33, FP 6, TN 20,295, FN 142

Supplementary source-faithful ARGOS validation diagnostics were kept separate:

- Point-F1: `0.36799999999999994`
- Point-F1-PA: `0.5537190082644624`
- Event-F1-PA: `0.6666666666666661`

Metric magnitude was not a TASK-034 pass criterion and did not trigger rule
repair, regeneration, or selection.

## E3 freeze

The validation Event-F1-PA operating point is frozen at
`2.6666666666666665` for scores from `smooth_labels(window_size=3)`. This is an
evaluator score threshold, not an internal rule threshold, detector threshold,
or calibration parameter.

E3 remains `not_run`, `sealed_not_accessed`, and `not_authorized`.

## Verification

- TASK-034 targeted tests: 17 passed.
- TASK-023 through TASK-034 ARGOS regression set: 77 passed.
- TASK-030 through TASK-032C contract set: 66 passed.
- TASK-032D/E contract set: 41 passed.
- TASK-032F replay set: 10 passed.
- Legacy DSL/verifier/runtime set: 35 passed.
- Full discovery: 324 tests executed; 8 existing collection errors remain
  because `torch` is absent. All eight are in the known GDN-dependent boundary,
  and no new failure occurred outside it.
- `pip check`, JSON parsing, report self-hash checks, compileall, and
  `git diff --check` passed.
