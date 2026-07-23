# TASK-037E: Error-Conditioned Full Aggregator

Status at Commit A: implementation, exact 83-rule candidate registry, DEC-069,
and protocol frozen; inner and outer execution pending.

TASK-037E independently selects at most one FN and one FP rule per frozen
detector/KPI unit using inner-only direct PA-free metrics and an explicit no-op
candidate. Selection must be committed before outer execution.

The outer phase replays only selected rules and evaluates detector-only,
detector-plus-FN, detector-plus-FP, and the source-aligned FP-then-FN full
Aggregator. All predictions freeze before outer labels are loaded.

Provider calls, agents, detector training, threshold selection, joint FN/FP
search, outer reselection, sealed-test access, and raw artifact tracking remain
prohibited.
