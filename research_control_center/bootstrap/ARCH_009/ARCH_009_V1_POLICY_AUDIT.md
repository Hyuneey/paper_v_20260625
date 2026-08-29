# V1 policy audit

Verdict: **VERIFIED**.

V1 is pointwise `D0 OR >=2 distinct D1 sources` at exact equal
`decision_physical_row_index`. Relation duplicates from one source collapse.
The threshold is 2, D0 is preserved, invalid authority fails closed, and the
combined artifact is durably frozen before labels. Frozen result: 11/14, FAR
0.7056194750975128, recovery 0/3, 10 normal false episodes.

The three D0 misses failed through two asynchronous multi-source patterns and
one single-source pattern. Every V1-added recovery episode was a normal false
episode in this pilot.
