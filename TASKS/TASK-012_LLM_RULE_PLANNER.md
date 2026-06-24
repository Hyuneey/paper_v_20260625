---
id: TASK-012
title: Implement provider-neutral schema-constrained LLM rule planner
status: blocked
depends_on: [TASK-011]
phase_gate: Milestone 5
suggested_branch: task-012-llm-rule-planner
---

# TASK-012: LLM Rule Planner

## 1. Goal

Implement a provider-neutral LLM planner that converts an approved aggregate evidence pack into a structured DSL rule candidate under strict variable, schema, numeric, privacy, and provenance constraints.

## 2. Architecture context

The LLM is added only after the deterministic template path passes Phase Gate B. It must operate on aggregate evidence, never raw SWaT sequences, and its value must be compared against the template baseline.

Use microsoft/ARGOS as a reference for the planner–repair–review workflow.

Do not reproduce:

- univariate dataset assumptions,
- execution of arbitrary LLM-generated Python,
- evaluation on sealed test data during rule construction,
- provider-specific Azure OpenAI coupling.

LLM output must conform to the project's JSON DSL schema and be evaluated
only by the deterministic rule engine.

## 3. Provider abstraction

Define an interface equivalent to:

```python
class LLMProvider(Protocol):
    def generate_rule(
        self,
        request: RulePlanningRequest,
    ) -> RulePlanningResponse: ...
```

Expected implementations:

- `MockLLMProvider` for all tests and CI,
- optional `OpenAIProvider`,
- optional `AzureOpenAIProvider`.

Do not couple core planning logic to ARGOS's Azure-only environment.

## 4. LLM input

- candidate pair,
- variable metadata,
- aggregate relation evidence pack,
- calibrated numeric parameters and references,
- allowed rule families,
- DSL schema/version,
- prompt template version.

The prompt must not contain raw SWaT rows, raw windows, or final test information.

## 5. LLM permissions

Allowed:

- choose among supplied rule families,
- compose a valid DSL skeleton,
- produce rationale referencing supplied evidence fields.

Forbidden:

- add variables,
- alter or invent numeric parameters,
- use unlisted predicates,
- return executable Python,
- access test labels or intervals,
- approve its own rule.

## 6. Output contract

The provider must return structured JSON compatible with the DSL schema. Markdown code blocks are not executable and should not be the primary contract.

Required output metadata:

```text
provider
model_or_deployment
API version
temperature
seed if supported
prompt_template_hash
evidence_artifact_hash
raw_response_hash
redaction_status
parse_status
```

## 7. Secrets and network policy

- API credentials come from environment variables or approved secret stores.
- Never commit secrets.
- External API calls are forbidden in CI.
- Tests use the mock provider.
- Provider errors must fail safely and preserve no raw restricted data.

## 8. Generated-code safety

Reject any response containing or attempting:

- arbitrary Python code,
- `exec`/`eval`,
- imports,
- shell commands,
- unsupported DSL fields.

Only parsed DSL JSON may proceed.

## 9. Required outputs

- provider interface,
- mocked implementation,
- optional approved providers,
- planning request/response models,
- schema-constrained parser,
- prompt templates,
- redaction and provenance records,
- planner result artifact.

## 10. Acceptance criteria

1. Output is validated through the same DSL schema as templates.
2. Extra variables are rejected.
3. Numeric mutation is rejected.
4. Unsupported predicates/code payloads are rejected.
5. All prompts and model settings are versioned.
6. Mocked tests require no network.
7. No raw SWaT sequence enters prompts or tracked responses.
8. No runtime package imports the planner/provider.
9. Planner result is comparable to template output.

## 11. Required tests

- valid mocked JSON output,
- extra-variable rejection,
- numeric mutation rejection,
- unsupported predicate,
- executable-code payload rejection,
- malformed response,
- provider error,
- prompt redaction,
- no-network CI test,
- provenance completeness,
- runtime import-boundary test.

## 12. Stop conditions

Stop if provider/model choice, data-transfer policy, prompt retention, or reproducibility settings are unapproved.
