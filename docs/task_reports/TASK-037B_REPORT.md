# TASK-037B Report

Final status: `passed_dual_arm_detector_outer_validation`.

Both frozen official EasyTSAD variants, `LSTMADalpha` and `LSTMADbeta`, were
fit independently for all ten frozen KPI series. Generation-only fitting and
normalization, inner-only threshold selection, and one-way outer validation
followed the pre-registered protocol. No detector variant was selected.

Outer inference received values only and was replayed exactly from frozen
checkpoints. Direct PA-free point/event metrics, AUROC and AUPRC were computed
after the outer score and prediction freeze. Generation TP/FN/FP/TN segments
were prepared privately but were not used for rule generation.

No provider, ARGOS agent, generated rule, detector-rule fusion, sealed-test
value, sealed-test label, or `TestLabels` artifact was used or created. Metric
magnitude was not a completion criterion.
