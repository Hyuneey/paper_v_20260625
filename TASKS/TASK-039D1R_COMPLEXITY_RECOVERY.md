# TASK-039D1R — Semantics-Preserving Complexity Recovery

TASK-039D1R preserves the passed TASK-039D0 scientific protocol and replaces
only two execution-complexity paths in the D1 execution layer.

- The aborted A1 commit is
  `d70f90b297bf7a6737652777f8f3059864c0c158`.
- Its failure is classified as
  `non_scientific_execution_complexity_defect`.
- The defect is repeated whole-sequence validation inside the source event
  index loop, which makes the reference execution path effectively quadratic.
- The recovery event adapter validates each file-local sequence once and then
  applies the exact frozen five-sample windows, threshold, stability, direction,
  and ten-second clustering semantics.
- The recovery isolation adapter uses sorted other-source indexes and bisect
  while preserving the inclusive plus/minus two-second, all-12-source policy.
- The frozen D0 functions remain the semantic oracle on bounded synthetic
  fixtures. The optimized target-response adapter is retained unchanged.

No D0 formula, policy, gate, candidate identity, arm-blindness rule, data split,
or claim boundary changes. Recovery implementation and testing access no HAI
feature values. A real rerun is authorized only from a clean recovery Commit
A2 after parity, structural complexity, patch-scope, and boundary tests pass.

The rerun may read only HAI train1 and train2 and must start from empty external
private storage. The historical partial execution state is never reused. Any
new implementation defect after the first new feature-value read terminates the
run without another patch or retry.
