# TASK-039D1 Arm-Blind Normal Relation Fit Profiling

TASK-039D1 executes the frozen TASK-039D0 protocol once for the exact 47-pair
P1 Boiler profiling cohort. Scientific profiling consumes only the frozen
identity view and the 24 authorized P1 variables from `hai-train1.csv` and
`hai-train2.csv`.

Commit A freezes the access guards, shared source/target parameter derivation,
all-12-source event isolation, two-direction response profiling, direction and
horizon selection, fit gate, no-fallback behavior, contracts, schemas, CLI,
and synthetic tests before real values are opened. Real execution must start
from that clean commit.

Private source, target, and directional numeric ledgers remain outside Git.
The 47 pair outcomes are frozen before the separate provenance-analysis view
is opened. META, STAT, and GDN provenance is then joined only to calculate the
preregistered descriptive fit-only top-20 summaries.

Train3, train4, test, labels, attacks, P2/P3/P4 values, BR2 pair results,
candidate-arm evidence in the profiler, lower-ranked fallback, merged scores,
Rule v2, runtime authority, and TASK-039D2 authorization are prohibited. A
scientifically negative fit result remains a valid execution result. The next
task after a passing D1 is an independent `TASK-039D1-AUDIT`.
