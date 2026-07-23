# TASK-037B: Dual LSTM Detector Validation

Status at Commit A: implementation and execution protocol frozen.

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
