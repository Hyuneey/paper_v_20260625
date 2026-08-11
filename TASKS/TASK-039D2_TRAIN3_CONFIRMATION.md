# TASK-039D2 — One-Way Train3 Confirmation

TASK-039D2 consumes exactly the 45 D1 fit-supported directional relation
records authorized by the independent D1 audit. It reuses the frozen D1 source
and target parameters, selected source direction, target direction, and horizon
without refitting, retuning, search, or fallback.

The real confirmation engine is arm blind. It reads candidate provenance only
after the private 45-record confirmation ledger and public directional and
47-pair outcome artifacts have been frozen. The only feature-value file
authorized for this task is `hai-23.05/hai-train3.csv`; train1, train2, train4,
test, labels, attacks, BR2 pair results, and P2/P3/P4 values are prohibited.

Passing execution produces calibration-confirmed relation candidates. It does
not create causality claims, a method winner, Rule v2, Agent authority,
detector/runtime authority, or anomaly-performance evidence. An independent
TASK-039D2 audit is required before any construction-stage authorization.
