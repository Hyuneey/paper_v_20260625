# HAI 23.05 Schema Audit

The time-series audit is streaming and bounded-memory. It records encoding,
delimiter, exact header hash, timestamp field, row count, first and last
timestamps, continuity counts, malformed rows, empty-field total, ordered
header agreement, process-prefix inventory, and reconciliation with 86 SCADA
points.

Test files receive structural inspection only. The audit does not calculate
per-feature extrema, moments, correlations, constant-feature status, anomaly
scores, attack-window plots, or any process-specific performance statistic.

The real schema audit was not executed because the official Git-LFS objects
were unavailable. HAI schema readiness and timestamp continuity remain
unverified.
