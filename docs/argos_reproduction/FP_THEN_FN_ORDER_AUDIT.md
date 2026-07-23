# FP-Then-FN Order Audit

The pinned ARGOS `ReviewAgent.combined_inference()` applies the FP rule first
and the FN rule second:

1. `train-combined-fp`
2. `train-combined-fn`

The corresponding `combine_labels()` implementation uses elementwise minimum
for FP correction and elementwise maximum for FN compensation.

Primary source:

- `external/argos/agent/review_agent.py`, pinned ARGOS commit
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`, lines 704 onward.
- `external/argos/common/common.py`, same commit, `combine_labels()`.

TASK-037E freezes the same order as `max(min(D, R_FP), R_FN)`. Tests use a
counterexample where reversing the order changes the output. This establishes
source-aligned binary composition only; it does not establish exact ARGOS
reproduction.
