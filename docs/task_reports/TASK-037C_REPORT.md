# TASK-037C Report

Final status: `passed_frozen_diagnostic_fusion`.

The complete two-detector by four-rule by two-operator diagnostic
matrix was computed for all ten frozen KPI series. All source and
derived prediction hashes were frozen before label access. No fusion
arm, detector variant, or rule arm was selected.

TASK-037C uses generic TASK-035B rules with source-faithful binary
max/min composition. It is not the paper-faithful detector-error-
conditioned ARGOS rule-generation or full Aggregator experiment.

No detector training, threshold selection, rule generation, provider
call, point adjustment, score-level fusion, or sealed-test access
occurred. Metric magnitude was not a completion criterion.

Across both unresolved LSTMAD variants, maximum fusion increased macro recall
for all four rule arms. Best-1 and Top-3 also increased macro point F1, while
Coverage-3 and All-10 incurred large false-positive costs and reduced macro
point F1. Minimum fusion reduced false positives but removed detector true
positives; its point-F1 effect varied by rule arm and detector variant.

These observations describe directional complementarity only. No arm was
selected, no superiority claim is made, and paper-faithful FN/FP-conditioned
rule generation remains future work.
