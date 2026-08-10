# Candidate Discovery Statistical Policy

`TASK-039C-STAT` may read P1 feature values from `hai-train1.csv` and
`hai-train2.csv` only. Differences and lagged pairs are formed within each
file; file boundaries are never crossed.

For each eligible pair and horizon in `1, 5, 10, 30, 60` seconds:

```text
dx(t) = x(t) - x(t-1)
dy(t) = y(t) - y(t-1)
r_file(h) = corr(dx(t), dy(t+h))
```

A horizon is stable only when both file correlations are finite, nonzero, and
have the same sign. Its strength is the smaller absolute correlation. The
pair selects the strongest stable horizon, breaking a tie toward the shorter
horizon. No stable horizon yields `direction_unstable` with score zero.

Ranking places stable pairs first, then descending strength, shortest selected
horizon, source identity, and target identity. No minimum correlation threshold
is introduced. This score is candidate-ranking evidence, not causality, rule
validity, or delayed-response proof.

Policy hash: `2e3413ee190dbce7106876ff5dd053161a17e18e80d142e75c05e50430c008e3`.
