# ReviewAgent Leakage Correction

ARGOS ReviewAgent is a label-aware code-revision agent, not a deterministic
verifier. TASK-038A preserves that role but confines optimization to the inner
partition.

## Trigger

For the matching detector variant, KPI, and direction:

- FN composition: `max(detector, rule)`
- FP composition: `min(detector, rule)`

If combined inner point F1 is at least detector-only inner point F1, the state
is `no_review_needed` and no provider call is made. A lower combined point F1
authorizes one Review call. Point adjustment is disabled.

Review accepts executable rules only. A2 cannot review a failed initial rule.
A3 must complete Repair successfully before Review.

## Regression evidence

Regression points satisfy:

`detector baseline correct AND current combined result wrong`

At most three chronological, non-overlapping inner windows are included. Each
window has at most 20 points and may contain inner values, labels, detector
predictions, rule predictions, and combined predictions. No other KPI,
detector variant, outer partition, or sealed-test evidence is permitted.

## Revision semantics

The pinned combined-mode Review system prompt and source hash are verified
without importing ARGOS. A valid Review response replaces the branch rule even
when it performs worse. The harness cannot silently restore the pre-review rule.
An invalid reviewed rule terminates that branch state.

This corrects the audited upstream use of train performance and test evaluation
during training iterations. TASK-038A performs no real Review call and reads no
inner labels.
