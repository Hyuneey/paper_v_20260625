# TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-AUTHORIZATION-TEST1-CUSTODY-RESTORATION-V1

Status: active

Restore only the exact official HAI 23.05 `hai-test1.csv` and
`label-test1.csv` raw payloads, update only the ignored `HAI_DATA_ROOT`
binding while preserving every D0/private binding, and use the frozen D0
authorization contract in one fresh-process custody preflight and one
authorization issuance.

Frozen authority:

- base: `00327ef31ecd96a4c8f3a2e842bf8cd8d236511a`
- authorization contract A: `4229e7c108c350174c03e4de0023ede3da8c1034`
- independent audit B: `c6481e201a11708ed0ef3d746e8057f627fb97d0`
- official HAI commit: `2a814cebc9a66b06c9e5cd545e2d72e65d383737`
- feature SHA-256: `78c7f1d4de1f2ab9ccc2f8c719f80f831033543adb0c81d0d78f84f40838d4be`
- label SHA-256: `eaf69edb9c5834bc393afd7bf658b5e408d34fd7bfc3261f80516765fb818fbc`

Hard boundaries: no scientific feature parsing, label parsing, D0 execution,
D1 rerun, D2, test2, OUTER, retraining, recalibration, design/model/threshold
change, or private path/value disclosure. Historical blocker evidence is
immutable. The next task on PASS is
`TASK-039E3-R2R-UTILITY-INNER-D0-EXECUTION-V1`.
