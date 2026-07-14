# TASK-035B Report

## Final status

Status: `passed_multi_rule_outer_validation`

TASK-035B completed the required Commit A / Commit B / Commit C sequence.

The values-only full-inner gate evaluated all 146 frozen executable cohort
rules. Of these, 145 satisfied the full-window output contract; every KPI
retained at least 12 eligible rules. Exactly ten rules per KPI were selected
without labels, and all 100 panel rules produced deterministic inner and outer
predictions across two fresh-container executions.

Four arms per KPI were selected on inner data and frozen before outer access.
The one-way outer run then computed arm-level direct PA-free metrics only.

## Outer macro results

| Arm | Precision | Recall | Point F1 | Event recall | FP points / 10,000 normal |
|---|---:|---:|---:|---:|---:|
| Best-1 | 0.7178 | 0.4589 | 0.4801 | 0.7034 | 22.08 |
| Top-3 OR | 0.5820 | 0.5975 | 0.5360 | 0.7856 | 105.56 |
| Coverage-3 OR | 0.3982 | 0.6968 | 0.3320 | 0.8057 | 2084.04 |
| All-10 OR | 0.3181 | 0.6993 | 0.3156 | 0.7724 | 2242.19 |

For the predeclared primary comparison, Coverage-3 OR minus Best-1, macro
recall was `+0.2379` with a descriptive paired-bootstrap 95% percentile
interval `[0.0944, 0.4014]`. Macro point F1 was `-0.1481` with interval
`[-0.3616, 0.0607]`. Precision was `-0.3196`, while false-positive points per
10,000 normal points increased by `2061.96`.

This shows greater anomaly coverage together with a substantial false-positive
cost. It does not establish multi-rule superiority. The bootstrap uses ten KPI
series as the resampling unit and supports descriptive uncertainty only, not a
formal population-level significance claim.

The held-out test remains sealed and unauthorized. No provider, generation,
repair, review, detector, fusion, or point-adjustment path is used. Runtime and
metric reports contain hashes and aggregate diagnostics only; raw rules,
values, labels, and predictions remain ignored private artifacts.
