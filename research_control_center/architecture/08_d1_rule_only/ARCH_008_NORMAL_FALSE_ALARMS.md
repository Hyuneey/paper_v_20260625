# ARCH-008 Normal False Alarms

The frozen comparison records 51,019 normal labeled seconds. A D1 alarm episode is a normal false episode only when it overlaps no attack timestamp.

| Quantity | Frozen value | Meaning |
|---|---:|---|
| Unique alarm seconds | 630 | Deduplicated D1 decision seconds across rules |
| Total alarm episodes | 626 | Maximal consecutive runs before label classification |
| Normal false episodes | 574 | Alarm episodes with no attack timestamp |
| Normal exposure | 51,019 seconds | Label-zero denominator |
| Normal FAR | 40.50255787059723 episodes/hour | 574 divided by normal exposure hours |

FAR/hour is not a point-level false-positive rate. The current frozen reports establish a very high normal false-episode burden, but do not provide a validated cause decomposition. Accordingly, the cause is **CAUSE_NOT_YET_ANALYZED** rather than attributed to trigger frequency, tolerance, duplication, or fragmentation.
