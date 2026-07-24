# Repair Provider Execution Protocol

TASK-038B uses the source-hash-verified TASK-038A Repair adapter and pinned
ARGOS Repair prompt. The exact eligible request manifest is frozen and
committed before provider access.

Each reproducibly failed initial rule receives at most one request using:

- provider: OpenAI Responses API
- model: `gpt-5.6-luna`
- maximum output tokens: 6,000
- temperature: omitted
- provider seed: not sent
- automatic retry: disabled
- manual retry: disabled
- replacement generation: disabled

A private receipt is written before each request and permanently consumes the
slot. A successful response, empty response, provider error, transport error,
malformed response, or timeout all consume the slot.

The request may include the current rule, sanitized failure evidence, the
failing generation value-only chunk, and the required `inference(sample)`
contract. It excludes every label, metric, inner/outer/test artifact, detector
result, TASK-037E result, local path, and credential.

Returned code is never executed on the host. Exactly one extracted rule must
pass the frozen static policy before target and contrast execution in fresh
rootless containers.
