# HAI Source-Exclusion Audit

TASK-039B remains frozen: P1 had 37 variables and P3 had 7, but each had zero
eligible reviewed, nonconstant binary/discrete control sources. No pair was
screened and no process was selected.

## Primary Causes

| Primary category | P1 | P3 |
|---|---:|---:|
| documented continuous control command | 6 | 2 |
| documented continuous actuator feedback/state | 7 | 0 |
| control semantics but constant | 9 | 0 |
| documented setpoint | 1 | 2 |
| documented process sensor | 13 | 3 |
| semantic role unresolved | 1 | 0 |

Documented control variables therefore do exist. Most viable changing control
representations are continuous rather than discrete. Several P1 discrete
control/feedback tags are constant in the authorized fit/calibration files.
The observed binary P1 command without an exact manual binding remains
semantically unresolved; data behavior was not used to promote it.

The 44-record detailed exclusion ledger remains private. Its frozen hash is
`3df659ddfa0971933643f54aa203b207679ec0bedc4ed3b58268ce9cd7b52d4a`.
No raw value, transition timestamp, or sequence is present in the public
summary.
