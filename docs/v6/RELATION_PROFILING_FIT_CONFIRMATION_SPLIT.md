# Fit and One-Way Confirmation Split

D1 uses only `hai-train1.csv` and `hai-train2.csv`. Its selected relation must
have at least 20 pooled usable responses, at least five in each fit file,
pooled consistency at least 0.70, per-file consistency at least 0.60, robust
effect ratio at least 2.0, and strict direction agreement.

D2 is planned but not authorized by D0. A later explicit authorization may use
`hai-train3.csv` only for one-way confirmation of D1-supported directional
relations. D1 source noise, step threshold, stability tolerance, target scale,
directions, horizon, windows, refractory interval, and isolation radius must be
reused without retuning. Confirmation requires at least five usable responses,
selected consistency strictly above opposite consistency, consistency at least
0.60, and robust effect ratio at least 1.0. No fallback search is permitted.

`hai-train4.csv` remains prohibited throughout D0/D1/D2 and reserved for a
later NORMAL_GUARD stage. Test, labels, attacks, and P2/P3/P4 values remain
prohibited.
