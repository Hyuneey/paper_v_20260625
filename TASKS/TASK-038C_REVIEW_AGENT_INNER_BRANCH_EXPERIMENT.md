# TASK-038C: ReviewAgent Inner-Only Branch Experiment

TASK-038C executes one bounded, leakage-corrected Review revision for each
triggered member of the frozen `A2` and `A3` Review parent population.

The experiment uses three commits:

1. implementation and DEC-074 freeze;
2. parent-prediction, trigger and exact call-manifest freeze;
3. aggregate provider, runtime, branch and inner-effect results.

The parent population contains 83 executable and 13 non-applicable `A2`
records plus 96 executable `A3` records. All parent predictions freeze before
inner-label access. Review uses direct PA-free inner point F1 against the
matching frozen detector baseline, bounded inner regression evidence and one
no-retry request per triggered branch.

Every returned rule requires extraction, static audit, generation target and
contrast replay, and deterministic full-inner replay. Harmful or invalid
outputs remain terminal outcomes. Outer access, sealed-test access, branch
selection, RepairAgent calls, DetectionAgent calls and host generated-code
execution are prohibited.

Pre-execution status: `implementation_frozen_results_not_run`
