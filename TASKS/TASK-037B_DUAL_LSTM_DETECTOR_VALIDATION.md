# TASK-037B: Dual LSTM Detector Validation

Final status at Commit C: `passed_dual_arm_detector_outer_validation`.

The task executes E4 using both `LSTMADalpha` and `LSTMADbeta` as non-selected
co-primary provenance arms. Generation-only fit/normalization, inner-only
operating-point selection, frozen outer inference, direct PA-free metrics and
generation error-segment preparation follow the TASK-037A contract.

Commit boundaries:

1. Commit A contains implementation, configuration, tests and protocols only.
2. Commit B freezes checkpoint, normalization, generation/inner score,
   threshold, prediction and error-segment hashes.
3. Commit C records outer replay and aggregate detector-only results.

No provider, rule, agent, fusion, sealed-test access, raw tracked artifact,
variant selection or hyperparameter search is permitted.

All twenty frozen variant/KPI units completed. Checkpoints and inner thresholds
were frozen in Commit B before label-isolated outer inference. Outer inference
was replayed deterministically, after which the predeclared detector-only
metrics were computed once. E5/E6 and sealed-test execution remain unrun.
