# TASK-039D0 — Common Relation-Profiling Protocol Freeze

Status: `passed_task039d0_relation_profiling_protocol_freeze`

TASK-039D0 binds the exact 47-pair TASK-039C cohort and freezes one common,
arm-blind protocol for normal-only relation profiling. It is a protocol task:
no HAI feature value, private BR2 pair result, candidate score, rule, Agent,
detector, verifier, or runtime was accessed or executed.

The frozen sequence is D0 protocol freeze, D1 train1/train2 fit-only
profiling, separately authorized D2 one-way train3 confirmation, and only then
possible future construction. Train4 remains reserved as NORMAL_GUARD.

Scientific profiler input is limited to source, target, P1, relation family,
and cohort hash. META, STAT, and GDN provenance is stored in a separate
analysis view and may be joined only after outcomes are frozen.

The immutable bundle is
`docs/task_reports/TASK-039D0_PROTOCOL_BUNDLE.json`. The sole authority created
by this task is `docs/task_reports/TASK-039D1_AUTHORIZATION.json`.
