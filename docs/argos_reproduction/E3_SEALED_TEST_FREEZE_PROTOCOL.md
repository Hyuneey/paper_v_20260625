# E3 Sealed-Test Freeze Protocol

TASK-034 freezes one validation-selected operating point for a later one-way E3
run. The operating point is the squeeze-mode Event-F1-PA threshold selected on
validation scores produced by `smooth_labels(window_size=3)`.

The freeze record binds the rule, KPI ID, split manifest, validation input,
labels, predictions, smoothed scores, metric protocols, immutable container
image, configuration, and clean execution commit by hash.

This evaluator threshold is separate from the captured rule's internal numeric
comparisons. It is not a detector threshold or a normal-data calibration
parameter.

TASK-034 leaves E3 in all three states:

- `not_run`
- `sealed_not_accessed`
- `not_authorized`

No later E3 task may alter the rule, smoothing policy, threshold, split, or
metric protocol after opening the test partition.
