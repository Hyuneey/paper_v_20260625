# Expanded KPI Cohort Protocol

TASK-035A pre-registers E2X-G as 10 lexicographically selected eligible KPI
series, five deterministic anomaly-anchored generation chunks per series, and
two identical one-shot requests per chunk. Selection uses only row counts and
the frozen generation/inner/outer eligibility counts. It never uses generated
rule behavior.

For each series, `train_pool_end=int(N*0.7)`,
`outer_train_end=int(train_pool_end*0.8)`, and
`generation_end=int(outer_train_end*5/7)`. Value and label parsing stops before
`train_pool_end`; the sealed-test suffix is counted but not parsed.

Five event ranks use `floor((j+0.5)*event_count/5)`. A 1,000-row chunk is
centered around each selected generation event and clamped to the generation
range. Hash collisions advance to the next chronological event. Raw arrays and
event content remain under ignored private storage.

This protocol prepares a generation cohort only. It does not evaluate KPI
validation performance or establish rule quality.
