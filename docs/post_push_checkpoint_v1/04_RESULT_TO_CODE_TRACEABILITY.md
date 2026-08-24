# Result-to-code traceability

No experiments or metric computations were rerun. Public frozen metric and
integrity artifacts on the remote ref were compared with the professor package.

| Arm | Recall | Normal FAR/hour | Additional fact | Traceability |
|---|---:|---:|---|---|
| D0 PCA-SPE | 0.7857142857142857 | 0.4939336325682589 | 11/14 events | frozen D0 metric and integrity-oracle artifacts → D0 design/training/execution modules |
| D1 verified rules | 0.9285714285714286 | 40.50255787059723 | covers D0 misses 3/3; union 14/14 | frozen D1 prediction/metric/integrity artifacts → COMMON-42 evaluator/runtime |
| D2 V1 | 0.7857142857142857 | 0.7056194750975128 | D0 recovery 0/3 | frozen D2 V1 prediction/metric/integrity artifacts → exact same-second fusion module/config |
| D2 V2 | 0.7857142857142857 | 6.915070855955625 | D0 recovery 0/3 | frozen D2 V2 prediction/metric/completion artifacts → native-horizon fusion module/config |

The event and episode implementation exposes maximal contiguous attack events,
maximal contiguous one-second alarm episodes, event overlap recall, and normal
episodes/hour. D2 code preserves D0 alarms, rejects score access, freezes the
combined prediction before labels, and binds exact D0/D1 prediction hashes.

**Result/code mismatches: none found.** The result interpretation remains
`RULE_SIGNAL_PRESENT_BUT_CURRENT_FUSION_UTILITY_UNSUPPORTED`; 14 attack events
do not support a statistical-superiority claim.
