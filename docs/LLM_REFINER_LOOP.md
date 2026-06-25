# Mock-Only Verifier-Feedback Refiner Loop

TASK-013 implements a bounded training-time refinement loop under the approved
mock-only scope.

Approved scope:

- consume structured deterministic verifier feedback codes,
- call `MockLLMProvider` only,
- re-plan candidate JSON DSL,
- re-run JSON parsing and `RuleSchemaRegistry` validation,
- re-run the deterministic verifier,
- retain ordered iteration provenance,
- stop after configured maximum iterations or an explicit safe stop reason.

Not approved:

- real provider calls,
- network execution,
- API key use,
- raw SWaT rows, windows, or sequences in prompts,
- final test access,
- runtime LLM execution,
- LLM self-approval,
- replacement of the deterministic verifier,
- benchmark or SWaT performance claims.

## Interfaces

- `RefinementPolicy`
- `RefinementIteration`
- `RefinementSessionResult`
- `refine_rule_with_feedback()`

## Required Provenance

Each session records:

- `max_iterations`,
- `stop_reason`,
- `policy_hash`,
- `provider_config_hash`,
- `planner_config_hash`,
- `verifier_config_hash`,
- `code_commit`,
- `created_at`,
- `network_allowed: false`,
- `redaction_status`.

Each iteration records:

- `iteration_index`,
- `previous_rule_hash`,
- `verifier_feedback_ids`,
- `feedback_codes`,
- `revised_rule_hash`,
- `parse_status`,
- `schema_validation_status`,
- `verification_status`,
- `stop_reason`.

## Stop Reasons

Implemented stop reasons:

- `verifier_passed`,
- `initial_planner_not_planned`,
- `non_recoverable_feedback`,
- `provider_failure_limit`,
- `schema_validation_failed`,
- `repeated_rule`,
- `no_improvement`,
- `max_iterations_exhausted`.

The deterministic verifier remains authoritative. A refined rule is only a
candidate until it passes deterministic verification.

## Safety

The refiner uses the TASK-012 prompt redaction audit. Tests cover restricted
payloads including:

- `test_label`,
- `test_interval`,
- `normal.csv`,
- `attack.csv`,
- `merged.csv`,
- timestamp-like raw payloads.

Tracked artifacts store hashes and redacted summaries, not full prompts, raw
provider responses, raw evidence payloads, or raw SWaT-derived sequence data.
