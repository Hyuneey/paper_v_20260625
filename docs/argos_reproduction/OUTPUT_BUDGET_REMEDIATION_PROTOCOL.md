# Output-Budget Remediation Protocol

TASK-035AR creates 100 new one-shot slots: the same 50 TASK-035A anchors with
replicates 3 and 4. Every anchor receives exactly two requests. The frozen
system prompt, user prompt, serialized chunk, provider, model, extraction
policy, static policy, and container policy remain unchanged.

The only generation change is `max_output_tokens: 6000`. Temperature and seed
are omitted, and no reasoning parameter, structured-output mode, examples,
prior rules, error feedback, RepairAgent, or ReviewAgent content is added.

Each slot receives a private receipt before its single request. Automatic and
manual retries are prohibited. Raw requests, responses, and extracted rules
remain under ignored private storage. Tracked reports contain only hashes,
counts, statuses, and redacted provider usage metadata.

Commit A-R freezes code, configuration, approval, tests, and protocols before
execution. Commit B-R records aggregate terminal results only.
