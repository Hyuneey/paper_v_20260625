# TASK-037D: Detector-Error-Conditioned Rule Cohort

Status at Commit A: implementation, support audit and 96-slot provider manifest
frozen; provider execution pending.

TASK-037D retains both LSTMAD variants, all ten KPI series and both FN/FP
directions. It selects generation-only target/contrast pairs deterministically,
uses exact pinned combined prompt templates, permits one provider request per
slot, applies the frozen static audit and checks static-valid rules in the
isolated values-only runtime.

The task performs no inner or outer evaluation, fusion, detector retraining,
threshold reselection, RepairAgent, ReviewAgent or sealed-test access.
