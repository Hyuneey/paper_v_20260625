# Fusion Contribution Metrics

TASK-037C reports aggregate PA-free metrics together with directional costs.

For `max(D,R)`, the report pairs detector false-negative recovery with added
true positives, added false positives, recovered events, precision/F1 changes,
and false-alarm changes. A reduced false-negative count is not interpreted as
useful when the accompanying false-positive cost is excessive.

For `min(D,R)`, the report pairs detector false-positive removal with removed
true positives, removed false-alarm events, lost anomaly events, recall/F1
changes, and false-alarm changes. Precision improvement is not reported without
the corresponding true-positive loss.

Prediction disagreements are partitioned into `D=0,R=0`, `D=0,R=1`,
`D=1,R=0`, and `D=1,R=1`, then split by ground truth. Events are maximal
contiguous positive runs and are never joined across KPI boundaries. Undefined
ratios use zero.

Primary metrics are direct binary precision, recall, point F1, one-to-one
overlap event precision/recall/F1, predicted-positive rate, FP points per
10,000 normal points, and false-alarm events per 10,000 points. AUROC and AUPRC
are not computed for binary fusion.
