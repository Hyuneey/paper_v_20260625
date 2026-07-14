# Legacy to V1 Artifact Crosswalk

## DSL

| Legacy field | TASK-030 field | Mapping | Information loss / action |
|---|---|---|---|
| `RuleAst.rule_id` | `rule_id` | direct | none |
| `schema_version` | `schema_version` | renamed/versioned | require explicit adapter version |
| `source` / `target` | `source_variables` / `target_variables` | direct to singleton arrays | none for MVP |
| `relation_type` and `rule_family` | `relation_type` | merged | reject non-MVP values |
| `ChangedToPredicate` | `trigger.state_changes_to` | derived | preserve from/to states |
| `IncreaseWithinPredicate` | `expected_effect`, `lag`, `window` | split | implicit window alignment must be declared |
| `ResponseMissingPredicate` | `output_semantics.violation_direction` | renamed | fixed to `missing_expected_response` |
| `CalibrationValueRef` | `parameter_refs`, `tolerance_ref` | split | resolved value moves to registry |
| `candidate_pair_artifact_id` | `graph_edge_refs` | unsupported without lookup | adapter needs explicit edge mapping |
| `metadata_artifact_id` | provenance/reference set | derived | registry artifact mapping required |
| `PlannerProvenance` | `provenance.created_by` and review history | split | preserve source artifact IDs |
| `description_template` | renderer input, not rule semantics | moved | exclude from executable semantics |

## Verifier

| Legacy field/symbol | TASK-030 target | Mapping | Migration required |
|---|---|---|---|
| `VerificationConfig` | verifier policy artifact | derived | version all stage policies |
| `VerificationDataset` | split/evidence references | split | preserve split and fingerprint IDs |
| `FeedbackIssue` | `violations`/`warnings` | split | add repairability classification |
| `VerificationReport.status` | verifier status | renamed | `passed` -> `accepted`; `rejected` -> `rejected` |
| report ID | `verifier_result_id` | direct hash concept | hash v1 canonical payload |
| `metrics` | warnings/support diagnostics | derived | not acceptance authority by itself |
| `duplicate_references` | duplicate/conflict records | split | add typed records |
| `verify_rule_json` | structural entry point | replace later | standard schema then semantic stages |
| `verify_rule` | deterministic authority | reuse checks, new orchestration | implement 20-stage result |

## Runtime

| Legacy symbol | TASK-030 target | Mapping | Migration required |
|---|---|---|---|
| `VerifiedRuleLibrary` | accepted rule bundle | wrapper | verify rule/parameter/result hashes |
| `RuntimeRuleEngine` | deterministic interpreter | adapt later | v1 operators and trace contract |
| `RuntimeFiringRecord` | satisfaction trace detail | split | include satisfied and abstained branches |
| `AlarmInterval` | explanation time interval | direct/derived | preserve alignment provenance |
| `RuntimeExplanation` | trace + explanation + renderer | split | remove mixed text/semantics responsibility |
| `RuntimeEvaluation` | execution collection | replace later | per-execution v1 records plus aggregates |

## E2E

`run_task011_template_feasibility` is a synthetic legacy pipeline harness. Its
candidate-to-profile-to-template-to-verifier-to-runtime ordering is reusable as
an integration-test pattern, but its artifacts and acceptance criteria cannot
be relabeled as v1. TASK-032F must use new v1 fixtures and explicit adapters.

All migrations require source and target hashes and a migration report. No
legacy file may be rewritten silently.
