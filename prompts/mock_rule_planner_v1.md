# Mock Rule Planner Prompt Template v1

Use only the supplied aggregate evidence.

Return JSON only. The JSON must conform to the project DSL schema version
`1.0`.

Allowed predicates:

- `changed_to`
- `increase_within`
- `response_missing`

Forbidden:

- adding variables,
- changing calibrated numeric values,
- inventing calibration IDs,
- adding unsupported predicates,
- returning Python or shell code,
- using raw rows, windows, sequences, test labels, or final test intervals.

The deterministic verifier is authoritative. The planner does not approve its
own output.
