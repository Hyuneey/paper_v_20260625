# TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-AUTHORIZATION-V1

Status: active.

This task freezes an authorization-only boundary for the exact audited
`D0_PCA_SPE_V1` model and threshold. It replays the complete committed D0
design/training/integrity authority graph, performs one path-silent private
custody preflight, raw-byte hashes only `hai-test1.csv` and
`label-test1.csv`, issues one D0 INNER authorization, and stops.

The task may not parse test features or labels scientifically, score SPE,
form alarms/events, compute metrics, execute D0/D1/D2, touch test2, retrain,
recalibrate, or expose private paths/numeric values. D0 execution requires the
separate next task
`TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-V1`.
