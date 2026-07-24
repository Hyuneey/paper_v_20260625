# Agent Branch Outer Execution Protocol

TASK-038E is a one-way follow-up outer-validation execution for the frozen
TASK-038D branches `A0`, `A1`, `A2`, and `A3`. It preserves both LSTMAD
variants, all ten KPI series, the independently selected FN and FP rules, and
every explicit no-op.

Before outer values are opened, the task freezes three logical evidence
blocks:

1. 160 selected direction records that produce 320 branch-arm predictions.
2. 76 reviewed-rule parent/revision pairs.
3. 13 repaired-rule detector-combination records.

Logical records are mapped to physical execution units by the complete tuple
of rule hash, detector variant, KPI, direction, outer input hash, and runtime
hash. Identical physical units execute once, while every logical record remains
separate for reporting.

Existing outer predictions may be reused only when the complete physical
lineage and prediction hash match. Every new physical unit is executed twice
in fresh rootless Podman containers. The container receives one rule and one
KPI's value-only outer array. Labels, detector predictions, metrics,
credentials, repository roots, and sealed-test artifacts are not mounted.

After all physical predictions are verified, branch arms are composed as:

```text
D       = detector
D+FN    = max(D, selected_FN)
D+FP    = min(D, selected_FP)
Full    = max(min(D, selected_FP), selected_FN)
```

No selected-rule failure may trigger substitution, parent restoration, or
no-op conversion. All branch, Review-transfer, and Repair-utility predictions
must be frozen before outer labels are loaded.
