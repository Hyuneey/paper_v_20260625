# TASK-026 Real LLM Capture Protocol

TASK-026 captures at most one response for the frozen TASK-025 ARGOS
`train-LLM-only` request. It evaluates response format and static generated-rule
structure only.

It does not execute generated Python, run ARGOS RepairAgent or ReviewAgent,
evaluate KPI performance, access SWaT, or make benchmark/thesis claims.

## Frozen Request

- ARGOS commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Mode: `train-LLM-only`
- Combined mode: deferred
- Selected KPI ID: `05f10d3a-239c-3bef-9bdc-a2feeb0037aa`
- Converted CSV SHA-256:
  `f6a6d834e23417da5cd0e87af227ae62f0c12a73f080afa08b08a2d332aa5d55`
- Chunk positions: `[0, 1000)`
- Chunk SHA-256:
  `550f47a55f37a18337c097ae4033808ef591d75407581c2e9b3cf8da1ed42015`
- Complete request SHA-256:
  `14af5d91248f3ca579a445527768264f148497d58d85b49b96b39b8873918aca`

The complete prompt request remains in ignored private storage under
`artifacts/private_argos_reproduction/task025/`.

## Capture Modes

### Approved API Capture

API capture is blocked unless all conditions hold:

- `configs/argos_reproduction/task026_provider_approval.json` has
  `approved: true`;
- DEC-028 is resolved;
- provider, model, version identifier, temperature, token budget, and cost
  budget are populated;
- `max_calls` is exactly `1`;
- required credential environment variables exist;
- the command includes `--allow-real-provider-call`.

The TASK-026 API client supports only the explicitly approved
`openai_responses` provider route. Unsupported provider names are blocked
instead of routed implicitly.

### Manual Capture

If API integration is not approved, the researcher may manually paste exactly
one provider response into:

```text
artifacts/private_argos_reproduction/task026/manual_response.md
```

Optional metadata may be recorded in:

```text
artifacts/private_argos_reproduction/task026/manual_response_metadata.json
```

Manual capture is labeled `manual_exploratory_capture` and is not a
paper-faithful API reproduction.

## Retention

Private ignored artifacts may contain:

- raw response;
- extracted code fence;
- provider response metadata;
- request ID, token usage, and cost if available.

Tracked artifacts contain only:

- provider/model metadata;
- request, response, and rule hashes;
- token usage and cost totals if available;
- capture status;
- static validation results;
- redacted rule structural summaries.

Tracked artifacts must not contain raw prompts, raw KPI rows, raw provider
responses, generated rule text, API keys, or performance metrics.

## Execution Boundary

Generated Python is not executed in TASK-026. The capture harness does not run
the captured rule with Python, subprocess, Docker, Podman, ARGOS runtime, or
the paperworks runtime.

No retries, prompt tuning, RepairAgent, ReviewAgent, detector-plus-rule mode,
KPI benchmark evaluation, or SWaT access are allowed.

## TASK-026R Compatibility Remediation

TASK-026 produced two provider-validation failures and no generated rule. The
researcher separately approved TASK-026R under DEC-029 for one compatibility
remediation request using `gpt-5.6-luna`.

TASK-026R keeps the complete request hash unchanged and omits the unsupported
`temperature` parameter. This is not response-driven prompt tuning because no
rule response was produced by either failed request.

The remediation uses separate config, private storage, and tracked reports. A
private ignored provider-call receipt is written before the network request.
Once the receipt exists, the harness blocks another request using the same
config, regardless of whether the first attempt succeeds, returns a provider
error, or raises a transport exception.

The approved TASK-026R request returned HTTP `429` with error code
`insufficient_quota` before response generation. DEC-029 is consumed. No retry
is approved under TASK-026R; billing or usage-limit remediation and a separate
future approval are required before another provider request.

## TASK-026Q Post-Quota Outcome

After the researcher confirmed billing remediation, DEC-030 approved one
separate TASK-026Q request. The frozen request completed with HTTP `200`, and
one response and one Python code fence were captured. Static syntax, signature,
import, and prohibited-call checks passed.

The rule remains in ignored private quarantine and was not executed. TASK-026Q
does not evaluate KPI performance or establish rule quality. DEC-030 is
consumed, and the private one-shot receipt blocks another TASK-026Q call.
