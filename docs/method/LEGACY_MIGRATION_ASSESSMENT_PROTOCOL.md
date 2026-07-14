# Legacy Migration Assessment Protocol

## Boundary

TASK-032A assesses serialized Phase 1 rule envelopes. It does not create a v1
rule, modify an input, execute a rule, fill external references, or approve a
calibration value. Every result enforces `target_artifact_created: false`.

Recognized inputs declare:

- `source_schema_identifier: minimal_rule_schema_v1`;
- `source_artifact_type: rule_candidate`;
- an immutable legacy payload;
- assessment-only source/target type context.

## Statuses

- `convertible_delayed_response_pending_context`: the serialized shape matches
  the frozen one-source binary-actuator to one-target continuous-sensor
  `changed_to -> increase_within -> response_missing` boundary.
- `unsupported_legacy_artifact`: the schema identifier, artifact type,
  cardinality, relation combination, or executable/dynamic field is outside the
  allowed boundary.
- `invalid_legacy_artifact`: the declared legacy payload is malformed or
  internally contradictory.

The first status is an assessment result, not migration approval. It requires
graph edge, evidence package, matched normal reference, parameter records,
operating regime, dataset version, and approved verifier policy context before
any later conversion task can be proposed.

## Provenance and Loss

The source hash is computed from canonical JSON before assessment. Field
mappings describe only a future mapping plan. Legacy resolved numeric values
cannot become approved parameter records, and synthetic-smoke calibration is
explicitly retained as non-approved evidence. Unsupported inputs are never
partially converted.

The four TASK-032A fixtures are synthetic and contain no KPI, SWaT, WADI,
Kaggle, provider, ARGOS, or captured-rule material.
