# Confirmation Audit

Verdict: PASS.

For each source direction, the profiler evaluates two target signs over five horizons. Records are eligible only when the chosen direction strictly exceeds the opposite in both train1 and train2. One record is selected by pooled consistency, robust effect, shorter horizon, and lexical tie-break before the fit gate. No lower-ranked fallback exists.

Train3 consumes exactly the 45 fit-supported directional records. Source, target, source sign, target sign, horizon, source/target parameter references, window policy, refractory, and isolation radius are frozen. The gate requires support ≥5, selected direction greater than opposite, consistency ≥0.60, effect ≥1.0, and unchanged fit parameters. No new relation, alternate horizon, opposite direction, fallback, or retuning is available.

Frozen result: 42 confirmed directions, three conflicts, 23 pair contexts with at least one confirmed relation, and two fit-supported contexts with none.

Detailed evidence: `agents/agent_b_confirmation.json`.

