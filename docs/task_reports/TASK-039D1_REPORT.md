# TASK-039D1 Report

Status: `passed_task039d1_normal_relation_fit_profiling`

Recovery preflight: `passed_task039d1r_semantics_preserving_complexity_recovery`. The historical A1 execution at
`d70f90b297bf7a6737652777f8f3059864c0c158` was aborted without frozen scientific
outcomes or private ledgers. No partial scientific state was reused.

TASK-039D1 executed the common arm-blind normal relation fit protocol once for
the exact 47-pair cohort. The result describes fit-supported normal
delayed-response relation candidates; it does not establish confirmation,
causality, physical truth, rule validity, anomaly performance, or method
superiority.

## Scientific outcomes

- Source parameters supported/unsupported: `12` / `0`.
- Pair fit-supported/unsupported: `25` / `22`.
- Directional fit-supported: `45` of `94`.
- Direction-unstable: `17`.
- Fit-unsupported directional: `32`.
- Source-parameter unsupported directional opportunities: `0`.
- Selected-candidate fit-gate failures: `32`.

Fit-only arm summaries are descriptive and reuse each shared pair outcome:

- META: `16/20` pairs (`0.8`), `29` directions.
- STAT: `17/20` pairs (`0.85`), `33` directions.
- GDN: `5/20` pairs (`0.25`), `7` directions.

No candidate-method winner was selected.

## Protocol validity and boundaries

- Exact D0 bundle: `888e3d642eba6f8ad8784d428bc4b27d7db7592d34779ba9a1f817860d76e1eb`.
- Commit A: `edf2727d33d30f615aa2be48756fc209afdcd95c`.
- Profiling identities: `47`; directional opportunities: `94`.
- Arm evidence visible during scientific profiling: `false`.
- Shared-pair D1 outcome invariant: `true`.
- Lower-ranked fallback used: `false`.
- Train1/train2 accessed: `true` / `true`.
- Train3/train4/test/labels/attacks accessed: `false`.
- BR2 pair results accessed: `false`.
- Raw values, windows, event timestamps, and absolute paths persisted publicly: `false`.
- Merged or cross-arm score used: `false`.
- Rule v2 authorized: `false`.
- TASK-039D2 authorized: `false`.

The required next task is `TASK-039D1-AUDIT`. No D2 authorization artifact was
created.
