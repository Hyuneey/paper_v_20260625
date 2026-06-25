# Mock-Only LLM Rule Planner

TASK-012 implements a provider-neutral planner interface under a restricted
mock-only scope.

Approved scope:

- `LLMProvider` protocol,
- `MockLLMProvider`,
- provider-neutral request and response schemas,
- prompt assembly from aggregate evidence,
- redaction audit,
- JSON DSL parsing,
- `RuleSchemaRegistry` validation,
- provenance and retention-safe planner result artifacts.

Not approved:

- real provider calls,
- network execution,
- API key use,
- raw SWaT transfer,
- final test access,
- runtime LLM execution.

TASK-013 is separately approved for a mock-only verifier-feedback refinement
loop. That approval does not permit real providers, network calls, runtime LLM
execution, final test access, or benchmark claims.

## Default Provider

Tracked config:

- `configs/planning/task012_mock_llm_planner.json`

Default provider fields:

```text
provider.name: mock
provider.allow_network: false
provider.require_api_key: false
provider.temperature: 0
model_or_deployment: mock-llm-provider
api_version: none
```

## Retention

Tracked planner results store:

- provider config hash,
- planner config hash,
- prompt template ID/hash,
- evidence hash,
- request hash,
- raw response hash,
- redacted prompt summary,
- redacted response summary,
- parse status,
- DSL validation result,
- provider metadata.

Tracked planner results do not store:

- full assembled prompt,
- full raw provider response,
- raw evidence payload,
- raw SWaT-derived sequence data.

## Safety

The planner rejects:

- invented variables,
- mutated numeric parameters,
- missing calibration references,
- unsupported predicates,
- Python/shell/code-like payloads,
- malformed JSON,
- provider errors,
- raw rows/windows/sequences in prompt payloads.

The deterministic verifier remains authoritative. The planner never approves
its own output.
