# Multi-Rule Provider Protocol

TASK-035A authorizes at most 100 sequential OpenAI Responses API requests to
`gpt-5.6-luna`. Every slot uses the pinned ARGOS DetectionAgent V3 system
prompt, a `pandas.DataFrame.to_string(index=False, header=False)` generation
chunk, no previous rule, no temperature, and no provider seed.

All requests are constructed and hashed before network access. Each anchor's
two replicates have byte-identical request bodies. A private receipt is written
before transmission, and any response, HTTP error, timeout, or transport error
consumes the slot. There is no automatic or manual retry under DEC-055.

Credential, permission, model, quota, billing, or provider-wide rate failures
stop the sequence and mark all remaining slots `not_attempted_global_block`.
Raw requests and responses remain ignored; tracked reports contain only hashes,
counts, usage totals, and sanitized statuses.

This is a bounded generation capture, not full ARGOS training. RepairAgent,
ReviewAgent, mutation, response-driven prompt changes, and performance
evaluation are prohibited.
