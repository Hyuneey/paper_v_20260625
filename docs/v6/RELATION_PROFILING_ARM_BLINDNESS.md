# Relation-Profiling Arm Blindness

`ProfilingIdentityViewV1` is the only scientific input view. Each record has
only source, target, process, relation family, and cohort hash. It cannot carry
META rank or tier, STAT correlation or candidate horizon, GDN rank, frequency
or similarity, origin-arm count, or overlap category.

`CandidateProvenanceAnalysisViewV1` retains the accepted public arm evidence.
It is not a profiler input and may be joined on `(source, target)` only after
relation outcomes are immutable. Thus the required invariant is: the same pair
produces the same profiling outcome regardless of proposing arm.

Events are isolated against the complete frozen 12-source P1 context rather
than an arm-specific source subset. Target scales are derived once per target,
not once per pair or arm.
