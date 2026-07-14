# Runtime Satisfaction Trace

Every canonical runtime trace contains exactly these ordered steps:

1. `regime_check`
2. `trigger_check`
3. `lag_check`
4. `window_check`
5. `relation_check`
6. `tolerance_check`
7. `persistence_check`
8. `abstention_check`
9. `output`

Each step records only a bounded result and the exact variable/parameter IDs
used. No measured input value is persisted. No-trigger traces mark lag through
persistence as not applicable. Abstentions mark the blocking step and
`abstention_check` as abstained. Missing response marks relation, tolerance,
and output as violated.

`parameter_values_used` contains every accepted rule parameter, sorted by ID,
with its artifact hash, value, and unit. The trace self-hash excludes only its
top-level `artifact_hash`; execution IDs bind authorization hash, input-window
hash, runtime version, and caller-supplied time.
