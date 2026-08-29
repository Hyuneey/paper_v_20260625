# ARCH-007 Independent QA Report

Verdict: **PASS**.

All 20 required QA questions were satisfactory after three pre-PASS corrections: generated-output count was updated to 39, ARCH-007 user TODO count was updated to 8, and GPT_BRIEF was reduced to 1,497 words while retaining its history-authority safeguard.

| # | Question | Answer |
|---|---|---|
| 1 | Is D0 research role accurate? | YES — simple deterministic normal-only reference, not contribution/SOTA |
| 2 | Is feature scope source-supported? | YES — 37 ordered P1 numeric fields; labels/timestamp/non-P1 excluded |
| 3 | Is standardization source-supported? | YES — custom NumPy population mean/std, ddof=0, floor 1e-12 |
| 4 | Is PCA fitting split correct? | YES — normal train1+train2 only |
| 5 | Is explained-variance handling correct? | YES — smallest k reaching >=0.95 with fail-closed cutoff rules |
| 6 | Is k correct? | YES — frozen outcome k=10, residual 27; not hard-coded policy |
| 7 | Is SPE formula correct? | YES — rowwise squared standardized reconstruction residual sum |
| 8 | Is calibration split correct? | YES — normal train3 |
| 9 | Is q correct? | YES — .999 exact empirical order statistic; index 125873; no interpolation |
| 10 | Is comparator resolved? | YES — strict greater-than; equality non-alarm |
| 11 | Are test1 labels excluded from fit/calibration? | YES |
| 12 | Is prediction-before-label durable? | YES — atomic persist, replay, state gate and byte checks |
| 13 | Are frozen numbers correctly interpreted? | YES — 876 points, 46 episodes, 11/14 events, 7 normal false episodes, FAR/hour |
| 14 | Is FAR/hour separate from point FPR? | YES |
| 15 | Are episodes separate from alarm points? | YES |
| 16 | Is determinism correctly classified? | YES — DETERMINISTIC_WITH_ENV_ASSUMPTIONS |
| 17 | Is fresh-machine state conservative? | YES — INCOMPLETE |
| 18 | Is D0 kept as reference rather than contribution? | YES |
| 19 | Is stronger-detector need recorded without implementation? | YES |
| 20 | Did audit execute zero scientific data? | YES |

Catalogs contain 9 artifact rows, 15 function rows and 13 I/O contracts. Mismatches total 10: 0 critical, 1 high, 8 medium, 1 low. Privacy and authority wording are satisfactory. Final validator and full-suite results are recorded after this QA artifact is materialized.

Safety: scientific executions 0; test1 feature/label accesses 0; test2 accesses 0; scientific source changes 0; frozen-result changes 0; private exposures 0.

Final coordinator verification: registry and generated-output validator PASS; `refresh_all.py` PASS; RCC tests 81/81 PASS; privacy exposures 0.
