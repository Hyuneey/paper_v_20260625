# TASK-039E1-AUDIT — Independent Construction-Evidence Audit

This task independently replays the 42-record TASK-039E1 construction-evidence
materialization from the frozen E0 identity cohort and the D1/D2 private
scientific ledgers. The audit implementation uses standard-library canonical
JSON and SHA-256 and does not import the production E1 materializer, its
numeric-reference resolver, or its runner.

The execution-code commit precedes every private-ledger read. The real replay
must use four explicit, distinct, outside-Git custody roots: the frozen D1, D2,
and E1 roots plus a fresh audit-only output root. It must reproduce all 42
private records, all 462 numeric references, the eleven-role frequency vector,
the D0 window bundle, and the public manifest/cohort artifacts exactly.

The audit has no HAI loader, no provider/model path, and no rule-generation
authority. A passing result may authorize TASK-039E2 configuration/protocol
freeze only; it may not authorize a provider call, real construction, Rule v2,
or detector/runtime execution.
