# Generic Rule Diagnostic Fusion Protocol

TASK-037C evaluates all frozen pairings of two TASK-037B LSTMAD detector
variants and four TASK-035B rule arms. The diagnostic operators are exact
binary elementwise maximum for false-negative compensation and exact binary
elementwise minimum for false-positive filtering.

The matrix is fixed before metric access:

- detectors: `LSTMADalpha`, `LSTMADbeta`;
- rules: Best-1, Top-3 OR, Coverage-3 OR, All-10 OR;
- operators: `fn_union_max`, `fp_intersection_min`;
- total: sixteen arms, each evaluated on all ten KPI series.

No score fusion, weighting, voting, smoothing, point adjustment, threshold
selection, arm selection, or detector-variant selection is permitted.

## Artifact order

1. Verify all tracked report self-hashes and frozen commits.
2. Verify every detector and rule prediction hash.
3. Re-materialize missing derived inner rule-arm arrays only by exact OR of the
   committed member rules' hash-verified inner predictions. This requires no
   labels and performs no inference or selection.
4. Freeze all inner and outer fusion prediction hashes.
5. Load inner labels and compute diagnostic metrics without changing the matrix.
6. Load outer labels only after every outer fusion prediction is frozen.

Any source hash, split, length, binary-domain, or lineage mismatch fails closed.
No test artifact may be discovered or loaded.
