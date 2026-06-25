# Minimal Rule DSL

TASK-007 defines a small JSON/AST DSL for the initial rule family:

```text
IF source changed from state A to state B
AND target did not increase by calibrated magnitude within calibrated delay
THEN anomaly
```

The schema is versioned at:

- `configs/dsl/minimal_rule_schema_v1.json`

The implementation is under:

- `src/paperworks/dsl/`

## Supported Family

Initial compatibility:

```text
binary actuator -> continuous sensor:
  changed_to + increase_within / response_missing
```

Unsupported predicates, extra variables, wrong metadata types, unknown schema
versions, and unreferenced numeric values are rejected.

## Numeric Parameter Rule

Runtime numeric values may be serialized for speed, but every value must retain:

- `parameter_name`
- `calibration_record_id`
- `field_name: value`
- `resolved_value`
- `unit`

The schema registry compares serialized values against supplied
`CalibrationRecord` objects. Mutated numeric values produce a
`NUMERIC_PARAMETER_MUTATED` issue.

## Synthetic Example

```json
{
  "rule_id": "rule.synthetic.A1.S1",
  "schema_version": "1.0",
  "rule_family": "changed_to_increase_within_response_missing",
  "source": "A1",
  "target": "S1",
  "relation_type": "binary_actuator_to_continuous_sensor",
  "trigger_predicate": {
    "predicate": "changed_to",
    "variable": "A1",
    "from_state": 0.0,
    "to_state": 1.0
  },
  "response_predicate": {
    "predicate": "response_missing",
    "expected_response": {
      "predicate": "increase_within",
      "variable": "S1",
      "min_magnitude": {
        "parameter_name": "min_response_magnitude",
        "calibration_record_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "field_name": "value",
        "resolved_value": 2.0,
        "unit": "target_units"
      },
      "max_delay_seconds": {
        "parameter_name": "max_response_delay_seconds",
        "calibration_record_id": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "field_name": "value",
        "resolved_value": 3.0,
        "unit": "seconds"
      }
    }
  },
  "calibration_references": {
    "max_response_delay_seconds": {
      "parameter_name": "max_response_delay_seconds",
      "calibration_record_id": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "field_name": "value",
      "resolved_value": 3.0,
      "unit": "seconds"
    },
    "min_response_magnitude": {
      "parameter_name": "min_response_magnitude",
      "calibration_record_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "field_name": "value",
      "resolved_value": 2.0,
      "unit": "target_units"
    }
  },
  "candidate_pair_artifact_id": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "metadata_artifact_id": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "planner_provenance": {
    "planner_type": "deterministic_template",
    "planner_version": "1.0",
    "source_artifact_ids": [
      "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
    ]
  },
  "description_template": "source transition with missing calibrated target response"
}
```

Human-readable text is formatted from the AST fields, not from
`description_template`.
