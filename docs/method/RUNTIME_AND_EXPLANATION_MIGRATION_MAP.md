# Runtime and Explanation Migration Map

## Runtime Crosswalk

| TASK-030 field | Current source | Migration |
|---|---|---|
| `execution_id` | none | derive from rule, verifier, input and config hashes |
| `rule_id` | firing/evaluation records | direct |
| `rule_hash` | `RuleAst.deterministic_id` available outside output | persist and verify |
| `input_window_id` | `TimeSeriesBatch.batch_id` | rename/derive per evaluated window |
| `status` | none | add typed execution status |
| `trigger_satisfied` | inferred from trigger indices | persist in trace |
| `expected_effect_satisfied` | inverse of missing response only | persist explicitly |
| `violation_detected` | firing presence | direct/derived |
| `violation_score` | binary severity | direct for MVP, provenance required |
| `abstained` | none | add for regime/data insufficiency |
| `satisfaction_trace` | scattered firing values | new structured trace |
| `parameter_values_used` | magnitude/delay values | bind parameter IDs, versions and hashes |
| `verifier_result_ref` | library maps a report ID | bind and verify accepted result |

The current `RuntimeRuleEngine` is deterministic, batch-only, canonical-view
only, and LLM-free. It revalidates the legacy schema but does not verify the
rule hash, parameter artifact hashes, accepted verifier status, operating
regime, or schema registry version. Streaming stays outside the MVP.

## Explanation Separation

`RuntimeExplanation` currently mixes three responsibilities:

- measured facts: alarm interval and observed delta;
- rule semantics: variables, expected relation and calibration values;
- derived formatting: human-readable expected/observed strings.

The migration must produce (1) a runtime satisfaction trace containing only
measured/evaluated facts, (2) a machine-readable explanation record joining
accepted rule, graph, evidence, parameter and verifier provenance, and (3) an
optional renderer. Causal or root-cause language has no legacy support and must
not be introduced.

## Parameter Migration

Legacy `CalibrationRecord` can supply a value, unit, method, quantile/config,
normal support and relation-profile reference. It lacks operating regime,
explicit calibration-window and normal-reference IDs, dataset/calibrator/code
versions in the record, confidence interval, stability, uncertainty, artifact
hash field, and approval identity/date. Only `LAG`, `TOL`, `DURATION`, and
`SUPPORT` are in the first adapter scope. Synthetic-smoke records map to
`proposed` or `calibrated`, never `approved`.

## Graph and Evidence Migration

`CandidateUniverseArtifact` is the pre-ranking membership boundary;
`GDNEdgeArtifact` supplies learned candidate rankings; `RelationProfile` and
`RelationEvidencePack` supply trigger/response aggregates and calibration
references. Wrappers must preserve candidate-before-ranking order, prohibit
self-edges, label learned/statistical edges as non-causal, add explicit matched
normal references and selection-policy hashes, and never persist raw sequences.
