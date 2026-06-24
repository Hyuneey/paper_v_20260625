# Variable Metadata Schema

TASK-002 implements provenance-aware variable metadata under `src/paperworks/metadata`.

## Purpose

Variable metadata supports candidate-universe construction, pair-type constraints, profiling, explanations, and deterministic verifier type checks. It must not encode final relation pairs or causal claims.

## Implemented modules

- `paperworks.metadata.schema`
- `paperworks.metadata.MetadataRegistry`
- `configs/metadata/swat_variables.json`
- `TEMPLATES/VARIABLE_METADATA_TEMPLATE.json`

## Schema

```python
@dataclass(frozen=True)
class VariableMetadata:
    name: str
    role: VariableRole
    value_type: ValueType
    physical_type: PhysicalType
    subsystem: str | None
    stage: str | None
    unit: str | None
    allowed_states: tuple[str, ...] | None
    source_method: MetadataSourceMethod
    source_reference: str | None
    confidence: float | None
    review_status: ReviewStatus
    schema_version: str
```

Enums:

- `VariableRole`: `sensor`, `actuator`, `unknown`
- `ValueType`: `continuous`, `binary`, `categorical`, `unknown`
- `PhysicalType`: `valve`, `pump`, `flow`, `level`, `pressure`, `quality`, `other`, `unknown`
- `MetadataSourceMethod`: `dataset_documentation`, `name_pattern`, `manual_review`, `inferred`, `unknown`
- `ReviewStatus`: `unreviewed`, `reviewed`, `rejected`

## SWaT metadata draft

`configs/metadata/swat_variables.json` contains 51 variable records matching the current local SWaT feature list.

The source is recorded as the researcher-supplied Kaggle page:

`https://www.kaggle.com/datasets/vishala28/swat-dataset-secure-water-treatment-system`

The metadata remains:

- `dataset_status: local_unverified_smoke_test`
- `source_method: dataset_documentation`
- `review_status: unreviewed`
- `terms_of_use_status: unverified` in the dataset manifest draft

## Review policy

Name-pattern or dataset-description metadata is not physical ground truth. It remains unreviewed until a human reviewer confirms it.

If a field is not confidently known, use `unknown` or `null` and let the coverage report surface it.

## Validation rules

Implemented validation includes:

- duplicate-name rejection,
- invalid enum rejection,
- invalid actuator/continuous combinations,
- invalid sensor pump/valve combinations,
- invalid actuator flow/level/pressure/quality combinations,
- confidence range checking,
- manual-review status consistency,
- feature coverage mismatch detection.

## Coverage reports

`MetadataRegistry.coverage_report(expected_features)` reports:

- expected feature count,
- metadata record count,
- missing features,
- extra metadata,
- unknown field counts,
- source-method counts,
- review-status counts.

TASK-002 tests verify that the SWaT metadata draft covers all 51 current feature names exactly once.

## Non-goals

- No final relation pairs.
- No causal claims.
- No attack-label-derived metadata inference.
- No hard-coded rule conclusions.

