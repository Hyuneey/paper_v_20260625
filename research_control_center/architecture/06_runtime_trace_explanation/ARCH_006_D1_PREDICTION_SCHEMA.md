# Frozen D1 prediction schema

The frozen prediction is a `ScientificRulePredictionArtifactV1`. It is not a dense 54,000-row Boolean vector.

## Artifact bindings

The top level binds the committed authorization, D1 bridge source identity, V4/evaluator authority, COMMON-42 descriptor and private-registry identities, dataset/split/feature identities, full-census identity, denominator policy, and aggregate counts.

## Per-opportunity record

| Field | Meaning |
|---|---|
| `opportunity_id` | one retained isolated source event joined to one matching relation descriptor |
| `source_event_identity_hash` | public-safe source-event identity |
| `relation_binding_hash` | relation/descriptor binding |
| `final_state` | expected response, anomaly, or abstain |
| `alarm_emitted` | true only for `evaluated_anomaly` |
| `decision_physical_row_index` | end of the selected response window, or null on abstain |
| `numeric_reference_identities` | the ten V4 authority references |
| `computation_identity` | hash binding frame, event, rule, authority, and references |
| `trace_hash` | hash of the task-specific rule execution trace payload |

## Aggregation semantics

- A rule-record alarm is one anomalous opportunity record.
- A point alarm at a physical second exists when at least one anomalous record has that decision index.
- Simultaneous violations remain separate records in the prediction artifact.
- For metrics only, decision indices are deduplicated, sorted, and consecutive unique seconds are merged into episodes.
- There is no runtime smoothing, point adjustment, count threshold, or alarm persistence policy.

The frozen artifact has 6,031 opportunity records and 788 alarming records. Static inspection shows those alarms occupy 630 unique decision seconds; the downstream metric artifact records 626 episodes. `alarm_count=788` must not be described as 788 unique point alarms.
