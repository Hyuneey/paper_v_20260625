# D0-miss recovery

The three units are anonymized as `RECOVERY_MISS_01` through
`RECOVERY_MISS_03` in the frozen diagnostic.

Frozen aggregate: **D1 response 3/3; V1 admission 0/3; V2 admission 0/3**.

| Unit | D1 responded? | V1 admitted? | V2 admitted? | Frozen explanation |
|---|---|---|---|---|
| RECOVERY_MISS_01 | YES | NO | NO | V1: three sources existed event-wide but never two at one row (`MULTI_SOURCE_ASYNCHRONOUS`); no public per-unit V2 failure trace is frozen |
| RECOVERY_MISS_02 | YES | NO | NO | V1: one source only (`SINGLE_SOURCE_ONLY`), so both two-source policies exclude it by design |
| RECOVERY_MISS_03 | YES | NO | NO | V1: three sources existed event-wide but never two at one row (`MULTI_SOURCE_ASYNCHRONOUS`); no public per-unit V2 failure trace is frozen |

The frozen diagnostic also records same-source multi-relation collapse as a
mechanism: even two relation records at one row can resolve to one source. V2
expanded temporal activity but still admitted no alarm overlapping these three
units. Apart from the single-source exclusion, public sanitized evidence does
not freeze a per-unit V2 reason for the two asynchronous cases. Therefore the
supported statement is: **D1 response does not imply D2 policy admission**.
