# Agent Branch Semantics

The factorial unit is one frozen TASK-037D initial slot.

| Branch | Repair action | Review action | Initial failure behavior |
|---|---|---|---|
| A0 | never | never | remains non-executable |
| A1 | once for runtime failure | never | repaired result or explicit failure |
| A2 | never | once only if executable and regressive | `review_not_applicable_non_executable` |
| A3 | identity or shared Repair | once only after executable input and regression trigger | Repair failure terminates before Review |

The exact initial rule hash is shared by all four records. Rules cannot move
between detector variants, KPI series, FN/FP directions, or target/contrast
lineage.

## Future branch selection

Each branch later repeats TASK-037E selection independently for every detector,
KPI, and direction. Every unit contains all executable branch rules plus an
explicit no-op. At most one FN and one FP rule are selected without joint pair
search.

The full Aggregator remains:

1. `after_FP = min(detector, selected_FP)`
2. `full = max(after_FP, selected_FN)`

No branch can be omitted because its inner result is unfavorable.
