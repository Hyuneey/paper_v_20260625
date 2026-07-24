# Repair Semantic Drift Boundary

RepairAgent is asked to correct an execution failure, but its replacement can
also change rule behavior. TASK-038B therefore reports label-free descriptive
drift without claiming semantic equivalence.

Tracked diagnostics include source-length and AST-node deltas, numeric-literal
counts and change status, comparison and control-flow deltas, import-set
change, and signature preservation. Literal values and source text are not
tracked.

When TASK-037D already produced a valid prediction on the non-failing fixture,
the original and repaired prediction hashes, preservation status, and changed
point count are reported. This comparison is not a detection metric and uses no
labels.

Drift does not independently reject a runtime-valid Repair revision. Degenerate
all-zero, all-one, near-all-positive, near-all-negative, and identical
target/contrast outputs are retained for later Review and selection.
