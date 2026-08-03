# Continuous-Step Process Selection Policy

P1 and P3 receive the same feasibility gate: at least two documented sources
with fit thresholds, three eligible targets, three calibration-confirmed
directional pairs, two distinct sources, two distinct targets, and transfer
rate 0.50. Train1/2 must be fit, train3 calibration, normal guard unread, and
prohibited access zero.

Exactly one feasible process is selected. If both pass, unweighted Pareto
comparison maximizes source/target/pair diversity, transfer, calibration
support, and metadata coverage while minimizing unresolved metadata,
non-isolation, and missing/nonfinite rates. Dominance requires no worse result
on every metric and strict improvement on at least two. Non-dominance is
`blocked_continuous_process_selection_indeterminate`.

Variable count, BR0 morphology count, official graph, attacks, detector
performance, convenience, and process ID cannot select a process.
