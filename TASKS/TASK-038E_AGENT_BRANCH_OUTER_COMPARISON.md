# TASK-038E: Agent Branch Outer Comparison

TASK-038E executes the one-way, previously exposed outer-validation comparison
of the frozen `A0` one-shot, `A1` Repair-only, `A2` Review-only, and `A3`
Repair-plus-Review branches.

The task uses three commits:

1. implementation and exact logical/physical outer execution registry;
2. value-only deterministic outer prediction freeze;
3. label-gated aggregate outer reports.

The registered evidence contains 320 branch-arm predictions, 76 Review
parent/revision pairs, and 13 repaired-rule utility records. A0 must reproduce
TASK-037E exactly. No provider or agent call, detector training, threshold
change, outer reselection, selected-rule fallback, or sealed-test access is
authorized.

Planned passing status: `passed_four_branch_outer_comparison`
