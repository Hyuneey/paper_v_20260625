# TASK-034: ARGOS E2 Frozen Rule-Only KPI Validation

Status: completed (`passed_validation_feasibility`).

## Scope

Run the frozen TASK-033 rule twice in fresh isolated containers on the exact
ARGOS chronological validation partition of the selected KPI series. Produce
PA-free binary diagnostics, separately labeled source-faithful ARGOS validation
metrics, and one frozen Event-F1-PA operating point for a future sealed E3 run.

## Hard boundaries

- The held-out test range is not parsed, materialized, executed, or evaluated.
- `phase2_ground_truth.hdf.zip` is not accessed.
- The container receives validation values only.
- No provider, ARGOS agent, detector, fusion path, or host generated-rule
  execution is allowed.
- Raw validation values, labels, predictions, and scores remain ignored.
- E3 remains sealed, not run, and not authorized.

## Two-commit gate

Commit A contains implementation, configuration, protocols, and tests. E2 must
run from that clean commit. Commit B may contain only aggregate reports and
status/freeze documentation updates.

The final execution ran from clean commit
`b81468c4da9eaa52596088e6b0768e11739c8072`. Two fresh validation-container
runs produced the same prediction hash. E3 remains sealed, not run, and not
authorized.
