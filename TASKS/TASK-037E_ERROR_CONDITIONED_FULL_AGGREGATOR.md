# TASK-037E: Error-Conditioned Full Aggregator

Final status: `passed_error_conditioned_full_aggregator_outer_validation`.

Commit A froze the implementation, exact 83-rule candidate registry, DEC-069,
and protocol. Commit B froze deterministic inner predictions and independent
FN/FP selections before outer access. Commit C records the one-way outer
results.

TASK-037E independently selects at most one FN and one FP rule per frozen
detector/KPI unit using inner-only direct PA-free metrics and an explicit no-op
candidate. Selection must be committed before outer execution.

The outer phase replays only selected rules and evaluates detector-only,
detector-plus-FN, detector-plus-FP, and the source-aligned FP-then-FN full
Aggregator. All predictions freeze before outer labels are loaded.

Provider calls, agents, detector training, threshold selection, joint FN/FP
search, outer reselection, sealed-test access, and raw artifact tracking remain
prohibited.

Execution summary:

- 83/83 rules passed two-run deterministic inner replay.
- FN selection: 19 executable rules and one no-op.
- FP selection: two executable rules and 18 no-ops.
- 21 selected non-no-op rules passed two-run deterministic outer replay.
- All four Aggregator arms for both variants and all ten KPI series were frozen
  before outer labels were loaded.
- The outer partition was previously exposed by earlier work; this is
  descriptive follow-up validation, not untouched confirmation.
