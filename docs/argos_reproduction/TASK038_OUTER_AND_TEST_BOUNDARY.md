# TASK-038 Outer and Test Boundary

TASK-038A is protocol-only. It does not access inner labels for real execution,
outer values or labels, or any sealed-test artifact.

The sequence is:

1. TASK-038B: bounded Repair experiment on 13 failures.
2. TASK-038C: A2/A3 Review on inner only.
3. TASK-038D: branch-specific inner selection freeze.
4. TASK-038E: one-way, previously exposed outer validation.
5. TASK-038F: qualified methodological synthesis.
6. TASK-038G: sealed-test preregistration.
7. TASK-038H: one-time sealed-test execution only after explicit approval.

Outer access before a committed TASK-038D selection freeze is prohibited. Outer
results cannot change rules, branch membership, detector variants, thresholds,
or selection policy. TASK-038E will remain descriptive because that outer
partition was exposed by prior experiments.

Sealed-test values, labels, scores, predictions, prompts, and feedback remain
unavailable until TASK-038H authorization.
