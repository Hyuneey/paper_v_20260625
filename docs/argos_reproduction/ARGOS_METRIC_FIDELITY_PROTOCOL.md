# ARGOS Metric Fidelity Protocol

TASK-034 reports two deliberately separate metric groups.

## Direct diagnostics

`direct_binary_validation_diagnostics` compares the frozen binary rule output
with validation labels. It reports confusion counts, precision, recall, and
point F1 with zero division set to `0.0`. It performs no point adjustment and
no threshold search.

## Source-faithful supplementary diagnostics

The supplementary adapter reproduces these pinned source paths:

| Source | Git blob |
|---|---|
| `common/common.py` | `2c1bd7546df4c547770b6055eea49ea169ea64a4` |
| `eval_metrics/point_f1.py` | `a96440baf55a0859a7d08831eeaee6871d170bf1` |
| `eval_metrics/point_f1pa.py` | `ec4b57072086fb907b23b6cce73cb50585c17c42` |
| `eval_metrics/event_f1pa.py` | `ef7c77ab087500b70ada062f81d75d0125258348` |
| `agent/review_agent.py` | `83936fdfc2875d245f79cd556b9ded96c6d1af25` |

Binary predictions are smoothed with `window_size=3`. Point-F1, Point-F1-PA,
and squeeze-mode Event-F1-PA then use validation labels only. PA search entries
are stably sorted by descending score. The source uses strict F1 improvement,
so the first encountered optimum survives a tie. Pinned Point-F1 does not retain
the corresponding sklearn threshold and reports its default `-1` value.

Frozen synthetic arrays are checked before private validation metrics. Failure
of any expected score, metric, or Event-F1-PA threshold closes E2 with
`failed_metric_fidelity`; no substitute event metric is allowed.
