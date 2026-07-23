# E5/E6 Error-Rule Claim Boundary

TASK-037D differs from the prior tracks:

- TASK-035B generated generic anomaly-anchored rules.
- TASK-037C combined those generic rules diagnostically with frozen detectors.
- TASK-037D generates new rules directly from detector FN and FP subsets.

TASK-037D is closer to the ARGOS paper training design, but it is not
`exact_ARGOS_full_reproduction`. The exact LSTMAD alpha/beta identity remains
unresolved, RepairAgent and ReviewAgent are not run, the pinned driver does not
wire the complete paper Aggregator, and the contrast adapter is project-owned.

The task may establish that a frozen, detector-error-conditioned one-shot rule
cohort was generated, statically audited and runtime checked. It cannot
establish detection improvement, fusion superiority, rule directional
correctness, inner/outer performance, sealed-test performance or benchmark
reproduction. Selection and Aggregator evaluation remain deferred to a
separately authorized TASK-037E.
