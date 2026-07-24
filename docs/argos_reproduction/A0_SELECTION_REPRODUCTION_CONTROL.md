# A0 Selection Reproduction Control

A0 is a reproduction control, not a new experiment. TASK-038D uses the same
83 candidate predictions, detector artifacts, inner labels, direct PA-free
metrics, independent FN/FP policy, and no-op rule as TASK-037E.

All forty selected candidate types, rule hashes, slot IDs, and protocol hashes
must match the TASK-037E freeze. Expected totals are nineteen FN rules, one FN
no-op, two FP rules, and eighteen FP no-ops. Any mismatch stops TASK-038D
before A1-A3 selection results are accepted.
