# TASK-039C-STAT Report

Status: `passed_task039c_statistical_candidate_discovery`

## Result

The independent STAT arm evaluated the exact frozen 144-pair P1 source-target
universe from clean implementation commit
`629f022d35bb0db6130e7e69faaf48408b49aa9a`. It used only the preregistered
within-file lagged change-correlation statistic over verified HAI 23.05
train1 and train2.

- Evaluated pairs: 144
- Cross-file sign-stable/supported pairs: 141
- Direction-unstable audit-only pairs: 3
- Top-10 count: 10
- Top-20 count: 20
- Top-40 count: 40
- Candidate shortfall: false
- Ranking hash:
  `5f9b97b9a7b426f1aa2036b4f6f82423801ecb3335093e08a5a61e3bad73e1a4`
- Result artifact hash:
  `7351e295be7e5bdd2b1cb9677091426899e5a2616c60245f953ff6602d106950`
- Data-access audit hash:
  `9588682c8c6c52afdc4dea960c1ccfbe221501a7f756ff9de2893474eb0099e4`
- Private detailed-ledger hash:
  `6333ff8f235d62fec1b86d78f1637f47ec66c0b4fb73e7476a094e49564f59d2`

All three budget views are prefixes of one deterministic supported ranking.
No direction-unstable pair was used to pad a view, and no minimum correlation
threshold was introduced.

## Statistic and numerical policy

For each file independently, the implementation computed source and target
first differences and evaluated Pearson correlation between `dx(t)` and
`dy(t+h)` at horizons 1, 5, 10, 30, and 60 seconds. Files were neither
concatenated before differencing nor pooled before file-specific correlation.

Pearson correlation used pairwise finite aligned observations in float64. Two
finite observations are the mathematical minimum; zero variance and nonfinite
results are unusable. Exact zero remains sign-unstable. The vectorized NumPy
backend passed the independent `math.fsum` reference parity gate at absolute
and relative tolerance `1e-12`. No dependency was installed or upgraded.

The score is statistical candidate evidence and cross-file stability strength.
It is not causal strength, physical relationship strength, rule validity,
anomaly score, or delayed-response proof. TASK-039D remains responsible for
later normal relation support evaluation.

## Data access

- train1 feature values accessed: true
- train2 feature values accessed: true
- train3 feature values accessed: false
- train4 feature values accessed: false
- test accessed: false
- labels accessed: false
- attack summary accessed: false
- private label custody accessed: false
- P2/P3/P4 feature values accessed: false
- BR2 pair supervision used: false
- Cross-arm score used: false

Each authorized training file was opened once by the STAT reader. The same
pass hashed exact bytes and parsed only the frozen 12 source and 12 target
columns. Public artifacts contain correlations and aggregate evidence, not raw
time-series samples, event timestamps, labels, or absolute local paths.

## Verification

- STAT targeted tests: 24 passed.
- C0 regressions: 38 passed.
- TASK-039BR2 regressions: 43 passed.
- TASK-039BR1 regressions: 34 passed.
- TASK-039BR0 regressions: 24 passed.
- Frozen TASK-039B regressions: 27 passed from commit
  `6543ca5b88779262d01c5e0c24e51216dd0835e9`.
- TASK-039A/TASK-039AR regressions: 37 passed.
- P0/P1A/P1B/P1C/P1D and v1-data regressions: 156 passed.
- TASK-032A-F frozen regressions: 106 passed.
- Lightweight candidate and relation-profiling regressions: 22 passed.
- Guarded discovery: 572 runnable tests passed, with 39 known optional imports
  classified (`jsonschema` 21, `pytest` 16, Torch/PyG 2) and no unexplained
  loader error.
- Compilation passed for 308 tracked Python files under `src`, `tests`, and
  `scripts`.
- Parsing passed for 420 tracked JSON files.
- Draft 2020-12 meta-validation passed for all 66 v6 schemas; the STAT result
  also validated against its schema.
- Result, access-audit, and private-ledger self-hashes passed.
- Public raw-value/path leak scans, both installed-environment `pip check`
  runs, and `git diff --check` passed.

The pinned ARGOS reference was exposed to guarded regression tests through a
temporary read-only junction only; the junction was removed afterward and no
upstream reference file was modified.

## Authority

This result ranks P1 statistical candidates only. It creates no Rule v2,
relation calibration, verifier authority, runtime authority, Agent call,
detector result, outer validation, sealed evaluation, or TASK-039D result.
