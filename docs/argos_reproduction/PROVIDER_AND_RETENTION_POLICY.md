# Provider and Retention Policy for ARGOS Prompt Capture

TASK-025 is provider-ready but provider-disabled by default.

## Default Mode

```yaml
provider_mode: mock
real_provider_calls: false
api_key_use: false
network_calls: false
generated_python_execution: false
```

The default harness path captures a repository-owned mock response, extracts a
Python code fence, validates the `inference(sample: np.ndarray) -> np.ndarray`
signature, runs static import/prohibited-call checks, quarantines the code under
ignored `artifacts/`, and stops.

## Approval Artifact

Template only:

```text
configs/argos_reproduction/task025_provider_approval.template.json
```

The template has `approved: false` and null provider/model/budget fields. The
harness refuses real provider mode unless all of the following are true:

- `approved` is true;
- `approved_by` and `approval_date` are populated;
- provider and model are explicit;
- token, cost, and temperature budgets are populated;
- required credentials exist in the environment;
- the command uses `--allow-real-provider-call`.

Codex must not invent or silently approve this artifact.

## Retention

Tracked artifacts may contain:

- prompt template hash;
- system prompt hash;
- user prompt hash;
- chunk hash;
- complete request hash;
- raw response hash;
- rule hash;
- selected chunk indices and counts;
- redacted provider metadata;
- static validation status.

Tracked artifacts must not contain:

- complete prompts;
- raw KPI rows;
- raw provider responses;
- generated rule text;
- API keys or credential values;
- benchmark metrics.

Full prompts, raw responses, selected raw chunks, and quarantined rule text are
written only under ignored `artifacts/private_argos_reproduction/task025/`.

## Boundary

This is an ARGOS rule-only prompt-capture smoke. It is not a benchmark result
and must not be used as a thesis performance claim.
