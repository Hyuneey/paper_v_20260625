# HAI Process Selection Policy

P1 and P3 receive the same minimum gate. A process must have at least two
eligible source variables, three eligible continuous targets, three confirmed
increase pairs, two distinct confirmed sources, two distinct confirmed
targets, and fit-to-calibration transfer of at least 0.50. Both candidate-fit
files and the calibration file are mandatory; guard values and prohibited data
must remain unread.

If exactly one process passes, it is selected. If neither passes, selection is
blocked. If both pass, an unweighted Pareto comparison maximizes confirmed
source/target coverage, increase-ready pairs, transfer, calibration support,
and manual coverage while minimizing unresolved metadata, non-isolated
triggers, and missing/nonfinite values.

Dominance requires no worse performance on every core metric and strict
improvement on at least two. The official graph does not score, process ID is
not a tie-breaker, and no weighted score exists. A nondominated tie blocks the
freeze.
