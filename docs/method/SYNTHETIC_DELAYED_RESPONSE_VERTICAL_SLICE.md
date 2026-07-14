# Synthetic Delayed-Response Vertical Slice

TASK-032F connects the delayed-response contract path using synthetic serialized
inputs only:

```text
Phase 1 mappings
-> explicit graph/evidence/parameter adapters
-> typed contract artifacts
-> predeclared candidate Rule v1
-> twenty-stage deterministic verifier
-> accepted rule
-> runtime authorization receipt
-> eight synthetic runtime windows
-> canonical traces
-> deterministic explanations
```

The graph and evidence targets are created directly by TASK-032C adapters. Lag,
tolerance, duration, and support adapters create `calibrated` records, preserving
DEC-039. The runner then requires field-for-field lineage agreement, excluding
only self-hash and approval fields, with the explicit approved synthetic records
already established by TASK-032D. Severity remains an explicit canonical
parameter and is never adapter-generated.

The candidate is loaded with `status: candidate` and a null
`verified_rule_hash`. All references must exist before verification, but that
precheck grants no authority. All twenty verifier stages must pass before an
accepted rule is materialized. Runtime execution is possible only after a fresh
authorization receipt is created and revalidated.

The eight predeclared cases cover response present, response missing, no
trigger, multiple triggers, regime mismatch, missing input, first-sample
trigger, and insufficient post-trigger coverage. Their comparison field is
`contract_expectation_matched`; it is not an accuracy or performance metric.

No raw arrays are retained in integration records or tracked reports.
