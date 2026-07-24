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

Final status: `passed_four_branch_outer_comparison`

The exact registry contained 249 logical records and 146 deduplicated physical
execution units. All physical predictions replayed deterministically. The 320
branch-arm, 76 Review-transfer, and 13 Repair-utility predictions froze before
outer-label access, and A0 reproduced all 80 TASK-037E arm/KPI controls.

The outer partition was previously exposed. Results are descriptive
component-wise evidence, not untouched confirmation, benchmark performance,
or a superiority claim. Every sealed test remains unrun and unauthorized.
