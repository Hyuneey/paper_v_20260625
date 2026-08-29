# D2 V1 policy

## Plain-language rule

At each physical decision row, retain the frozen D0 alarm. Independently gather
all alarming D1 records whose `decision_physical_row_index` equals that row,
resolve each relation to its frozen source identity, collapse duplicates, and
add an alarm only when at least two distinct sources remain.

```text
sources[t] = set(source_map[r.relation] for alarming D1 record r at index t)
corroborated[t] = len(sources[t]) >= 2
D2_V1[t] = D0[t] or corroborated[t]
```

“Same-second” is therefore the same `decision_physical_row_index` in the
one-second test1 grid. It is not episode overlap, source-trigger time, or a
window around an event. Multiple relations from one source count once.

## Frozen result explanation

The frozen diagnostic reports mixed mechanisms for the three D0-missed units:
single-source recovery signal, multi-source temporal desynchronization, and
same-source multi-relation collapse. None satisfied the exact-same-index
two-source gate. All three V1 `RULE_RECOVERY` episodes instead had zero attack
overlap and were normal false episodes. No new diagnostic was derived here.
