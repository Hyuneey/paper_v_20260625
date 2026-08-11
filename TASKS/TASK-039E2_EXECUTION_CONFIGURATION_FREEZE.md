# TASK-039E2 — Rule Construction Execution Configuration Freeze

TASK-039E2 freezes the complete provider, model snapshot, stateless sampling,
prompt, strict structured-output, evidence-rendering, retrieval, deterministic
T0, relation-major schedule, retry, response-custody, and direct-number
configuration before any proposal exists.

The exact provider/model binding is OpenAI Chat Completions at
`/v1/chat/completions` with `gpt-5.4-2026-03-05`. Alias, automatic-upgrade,
and alternative-model fallback are prohibited. Account availability is not
probed in this task.

The shared main prompt is byte-identical for T1, all three T1-B calls, and T2
call 1 for a given relation. Arm and call provenance remain local. T2 may only
receive its own bounded deterministic verifier feedback and one targeted
re-presentation of evidence already present in the original approved E1
corpus.

This task does not read the E1 private ledger, HAI, credentials, or provider
responses. It performs no capability probe, model call, direct-number
execution, or real T0 generation and creates no E3, Rule v2, Agent, detector,
or runtime authority. A passing result proceeds only to TASK-039E2-AUDIT.
