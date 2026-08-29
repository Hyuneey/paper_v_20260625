# ARCH-006 Trace Audit

Frozen D1 trace and canonical `RuntimeTraceV1` are `NON_EQUIVALENT`; only terminal outcome semantics partially overlap. Frozen D1 persists 6,031 compact terminal records and unique trace hashes, not nine-step canonical satisfaction traces. This does not invalidate the integrity-audited D1 alarm result, but it prevents direct canonical explanation rendering and step-level trace claims.

See `architecture/06_runtime_trace_explanation/ARCH_006_TRACE_SCHEMA.csv` and `ARCH_006_TRACE_HASH_CHAIN.md`.
