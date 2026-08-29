# Cross-method Metric Audit

Classification: `SEMANTICALLY_EQUIVALENT`; fairness: `FAIR_WITH_LIMITATIONS`.

D0 and D2 provide complete Boolean timelines. D1 contributes only anomaly decision rows, deduplicated by physical row. Non-opportunity, non-alarm, and abstain produce no alarm timestamp at the common interface; frozen abstain count is zero. All arms share test1, event units, exposure, overlap, episode, Recall, and FAR semantics. Separate wrappers and D1's opportunity-driven native semantics remain visible.

The per-arm paths are traceable. The frozen cross-arm comparison artifact exists, but its aggregation source is not discoverable in the current scientific tree; that reporting edge is PARTIAL.
