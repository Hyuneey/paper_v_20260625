# TASK-037D: Detector-Error-Conditioned Rule Cohort

Status: `passed_error_conditioned_rule_cohort`.

Commit A froze the implementation, support audit, and 96-slot provider
manifest. Execution consumed every slot exactly once, captured 96 responses,
extracted 96 static-valid rules, and found 83 rules executable on both their
target and contrast value chunks. No retry or replacement call occurred.

TASK-037D retains both LSTMAD variants, all ten KPI series and both FN/FP
directions. It selects generation-only target/contrast pairs deterministically,
uses exact pinned combined prompt templates, permits one provider request per
slot, applies the frozen static audit and checks static-valid rules in the
isolated values-only runtime.

The task performs no inner or outer evaluation, fusion, detector retraining,
threshold reselection, RepairAgent, ReviewAgent or sealed-test access.
