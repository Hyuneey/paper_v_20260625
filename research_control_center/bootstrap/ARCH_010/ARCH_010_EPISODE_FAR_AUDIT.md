# Episode and FAR Audit

- Alarm indices are set-deduplicated, sorted, and merged only across exact `+1` row adjacency.
- Episodes and attack units use half-open intervals.
- A normal false episode has no attack-unit overlap; mixed episodes are not split and are excluded from the false-episode numerator.
- Normal exposure is 51,019 strict label-0 rows at one second per row.
- FAR/hour is normal false episodes divided by exposure hours, not point FPR.
- Counts: D0 7 / 0.4939336325682589; D1 574 / 40.50255787059723; V1 10 / 0.7056194750975128; V2 98 / 6.915070855955625.
