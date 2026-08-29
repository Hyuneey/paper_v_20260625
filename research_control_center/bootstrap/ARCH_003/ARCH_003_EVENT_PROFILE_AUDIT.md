# Event and Profile Audit

Verdict: PASS with documented row-time dependency.

- Source parameters use file-local first differences pooled only after differencing across normal train1/train2.
- Event candidates use 5-row pre/post medians, threshold equality, and at least 0.80 stability on each side.
- Same-source events use 10-row single-link clustering; the largest absolute change survives, earliest on tie.
- Cross-source isolation is inclusive within ±2 rows across the exact 12-source context.
- Target response is a 5-row baseline versus a 3-row median at horizons 1, 5, 10, 30, or 60.
- Incomplete response windows are right-censored; no imputation occurs.
- Per-file support/direction evidence is preserved, while pooled consistency uses summed matches over summed usable events.
- The profiler treats seconds as row offsets under the frozen one-second sampling contract and does not independently validate timestamp continuity.

Detailed evidence: `agents/agent_a_profiling.json`.

