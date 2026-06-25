# Template Rule Builder

TASK-008 implements the deterministic non-LLM baseline planner.

The public interface is:

```python
build_template_rule(evidence: RelationEvidencePack, registry: RuleSchemaRegistry) -> TemplateRuleBuildResult
```

The builder accepts only aggregate relation evidence and schema-registry state.
It does not accept raw time-series windows, split objects, labels, test data, or
LLM output.

## Supported Template

Initial supported template:

```text
binary actuator -> continuous sensor
changed_to(0.0 -> 1.0)
response_missing(increase_within calibrated delay and magnitude)
```

The builder uses the existing minimal DSL rule family:

```text
changed_to_increase_within_response_missing
```

## Numeric Provenance

Every numeric runtime value is created from a `CalibrationRecord` exposed by the
`RuleSchemaRegistry`.

The builder rejects rule generation when:

- a required calibration ID is absent from evidence,
- the registry does not contain the referenced calibration record,
- the calibration record parameter name differs from the expected parameter,
- the evidence value differs from the calibration record value.

## Unsupported Results

Unsupported inputs return `TemplateRuleBuildResult(status="unsupported")` with
a machine-readable issue code, for example:

- `UNSUPPORTED_RELATION_TYPE`
- `UNSUPPORTED_RULE_FAMILY`
- `INSUFFICIENT_NORMAL_SUPPORT`
- `VARIABLE_NOT_FOUND`
- `TYPE_MISMATCH`
- `CALIBRATION_MISSING`
- `CALIBRATION_MISMATCH`
- `NUMERIC_PARAMETER_MUTATED`
- `PROVENANCE_MISSING`

The builder does not infer causality. Generated rules represent deterministic
candidate anomaly checks for approved candidate relations only.
