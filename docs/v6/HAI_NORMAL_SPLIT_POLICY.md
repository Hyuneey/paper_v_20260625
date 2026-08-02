# HAI Normal Split Policy

TASK-039B freezes file-level roles before any screening:

| Role | Raw file use |
|---|---|
| `normal_candidate_fit` | train1 and train2 values |
| `normal_relation_calibration` | train3 values |
| `normal_guard` | train4 hash, header, row count, and range only |

Each process receives identical comparison ranges. No random row split or
cross-file window is allowed. The fixed purge is 120 samples, satisfying
`window_size - 1 + maximum_required_lag` for the frozen 60-second context and
60-second lag boundary.

After selection, only the selected process split manifests become public
authoritative artifacts. Train4 feature values remain unread and reserved for
future normal false-fire governance.
