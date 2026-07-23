# Detector Threshold Freeze Protocol

Each KPI, variant, and seed receives an independent threshold selected from the
unique finite inner scores. Candidate predictions use `score >= threshold`.
The selected candidate maximizes direct PA-free point F1, then the highest
threshold, then stable original order. Undefined point metrics are zero.

Checkpoint and inner-score hashes are frozen before inner labels are loaded.
Inner labels may choose only this operating point; they cannot choose a
variant, hyperparameter, epoch, architecture, normalization, or KPI. Outer and
sealed-test labels cannot select or modify thresholds.

The threshold record binds variant, KPI, seed, checkpoint, inner score and
inner label hashes, candidate count, confusion counts, direct metrics, and the
protocol hash. Point adjustment is disabled.
