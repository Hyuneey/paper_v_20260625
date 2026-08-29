# ARCH-007 Output Levels

| Level | Meaning | Frozen D0 observation |
|---|---|---|
| SPE score | one continuous squared residual magnitude per test1 row | private values; public content hash only |
| Point alarm | one row where `SPE > threshold` | 876 of 54,000 rows |
| Alarm episode | consecutive alarm indices grouped by the metric policy | 46 total episodes |
| Normal false episode | alarm episode with no attack-timestamp overlap | 7 episodes |
| Attack-event response | independent attack event overlapped by at least one alarm episode | 11 of 14 events |
| Normal FAR/hour | normal false episodes divided by normal labeled exposure hours | 0.4939336325682589 episodes/hour |

`FAR/hour` is not a point-level false-positive rate. Likewise, 876 point alarms, 46 alarm episodes, 7 normal false episodes, and 11 detected attack events are different populations and must not be interchanged.

Metric arithmetic is mapped here only as lineage; its deep audit remains ARCH-010.

