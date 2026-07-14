# MVP Delayed-Response Vertical Slice

## Status

TASK-031 freezes scope only. It does not implement or authorize the slice.

```yaml
mvp_relation_family: delayed_response
source_cardinality: 1
target_cardinality: 1
source_type: binary_actuator
target_type: continuous_sensor
trigger:
  trigger_type: state_changes_to
expected_effect:
  effect_type: delayed_change
  direction: increase
violation:
  violation_direction: missing_expected_response
runtime_output:
  output_type: binary_anomaly
lag:
  allowed_types: [fixed, interval]
window:
  allowed_types: [event_relative, persistence]
```

The slice is the direct successor to the Phase 1 sequence
`changed_to -> increase_within -> response_missing`. `ChangedToPredicate`
supplies the transition trigger, `IncreaseWithinPredicate` supplies the
positive delayed effect and lag bound, and `ResponseMissingPredicate` supplies
the violation. The migration changes representation and provenance, not the
scientific relation being tested.

The other thirteen TASK-030 relation families, multi-source or multi-target
rules, streaming execution, free-form expressions, and causal claims remain
out of scope.

## Compatibility Freeze

- `minimal_rule_schema_v1` is legacy read-only after a v1 implementation exists.
- New legacy-rule creation is then prohibited.
- TASK-030 schema `1.0.0` is the active target.
- Silent conversion and in-place artifact rewriting are prohibited.
- A deterministic adapter may convert only the supported delayed-response form.
- Every conversion must record source hash, target hash, adapter version, field
  mappings, losses, and an explicit status.
- Unsupported inputs return `unsupported_legacy_artifact`; partial conversion is
  prohibited.
- Synthetic-smoke calibration remains synthetic evidence and cannot become an
  approved research parameter by migration.
