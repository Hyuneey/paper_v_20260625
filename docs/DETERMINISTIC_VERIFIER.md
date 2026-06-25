# Deterministic Rule Verifier

TASK-009 implements the deterministic verifier for candidate DSL rules.

The verifier is authoritative for rule acceptance. It uses the deterministic DSL
evaluator only and does not execute generated Python, call LLMs, call external
APIs, or access final test data.

## Synthetic Smoke Policy

The tracked config is:

- `configs/verification/task009_synthetic_smoke.json`

Synthetic smoke thresholds:

- `max_normal_false_fire_rate: 0.0`
- `min_validation_coverage: 0.5`
- `firing_overlap_jaccard_threshold: 0.8`
- `min_calibration_support_count: 2`
- `parameter_neighborhood_relative_tolerance: 0.0`

These thresholds are implementation smoke-test thresholds only. They are not
final SWaT rule-selection or performance thresholds.

## Verification Stages

The verifier performs:

- DSL schema parsing for JSON payloads,
- variable existence and metadata/type compatibility through `RuleSchemaRegistry`,
- calibration provenance and numeric integrity checks,
- minimum calibration normal-support checks,
- normal false-firing measurement on `calibration_normal`,
- validation firing coverage measurement on `validation`,
- structural duplicate detection,
- same pair/family parameter-neighborhood duplicate detection,
- validation firing Jaccard overlap duplicate detection.

Final `test` split use is prohibited.

## Feedback Codes

Reports use machine-readable feedback codes, including:

- `DSL_SCHEMA_INVALID`
- `VARIABLE_NOT_FOUND`
- `TYPE_MISMATCH`
- `CALIBRATION_MISSING`
- `CALIBRATION_MISMATCH`
- `NUMERIC_PARAMETER_MUTATED`
- `INSUFFICIENT_NORMAL_SUPPORT`
- `NORMAL_FP_TOO_HIGH`
- `VALIDATION_COVERAGE_TOO_LOW`
- `STRUCTURAL_DUPLICATE`
- `FIRING_OVERLAP_DUPLICATE`

Human-readable messages are supplemental. Logic must use codes and numeric
fields, not free text.

## Report Contents

`VerificationReport` stores aggregate metrics only:

- normal window count,
- normal false-fire count/rate,
- validation window count,
- validation fire count/coverage,
- duplicate references,
- issue codes and observed/limit values.

Reports must not store raw SWaT rows or long raw sequences.
