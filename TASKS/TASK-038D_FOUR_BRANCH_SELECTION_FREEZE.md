# TASK-038D: Four-Branch Selection Freeze

TASK-038D reconstructs the executable A0-A3 branch outputs, freezes every
candidate prediction before inner-label access, reproduces the TASK-037E A0
control, and independently selects at most one FN and FP rule per
branch/detector/KPI/direction unit with an explicit no-op.

The task uses two commits:

1. implementation, branch registry, and candidate-prediction freeze;
2. A0 reproduction, A1-A3 selections, aggregate inner diagnostics, and status.

Provider and agent calls, outer access, detector changes, joint FN/FP search,
rule ensembles, and sealed-test access are prohibited.
