# Review Trigger and Evidence Protocol

TASK-038C uses the matching frozen TASK-037B detector inner prediction for each
parent. FN rules compose by exact binary maximum and FP rules by exact binary
minimum. Point adjustment, smoothing, score fusion and threshold search are
disabled.

A branch requires Review only when its direction-specific combined direct
PA-free inner point F1 is below the matching detector-only point F1. A branch
that reaches or exceeds the detector baseline is an identity
`no_review_needed` outcome and cannot consume a provider slot.

Regression evidence is inner-only and bounded. It contains at most three
chronological, non-overlapping windows of at most 20 points. Windows start from
locations where the detector is correct and the current combined prediction is
wrong. A lower point F1 with no eligible window still authorizes Review using
the rule and aggregate inner metrics only.

No outer value, outer label, outer metric, sealed-test artifact, other KPI,
other detector variant, branch ranking or TASK-037E outer result may enter a
Review request.
