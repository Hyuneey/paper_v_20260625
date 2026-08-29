# ARCH-006 D1 Freeze Audit

Classification: `SAFE_BUT_WEAKER_THAN_D0_D2`.

D1 builds, hashes, factory-registers, and replay-validates a label-blind in-memory prediction before the label loader runs. No verified leakage or post-freeze mutation was found. Unlike D0/D2, D1 has no durable pre-label JSON, explicit frozen-state gate, or post-label byte check. The top-level object is frozen but nested record dictionaries are mutable.

See `architecture/06_runtime_trace_explanation/ARCH_006_D1_FREEZE_BOUNDARY.md`.
