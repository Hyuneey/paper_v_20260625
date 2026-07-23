# Full Aggregator Execution Protocol

Outer execution starts only from a clean commit containing both complete
direction-specific selection freezes. Only selected non-no-op rules execute on
outer values, and every selected rule executes twice in fresh isolated
containers. An outer failure cannot trigger substitution or conversion to
no-op.

For detector prediction `D`, selected FP rule `R_FP`, and selected FN rule
`R_FN`, the project-owned adapter applies:

```text
after_FP = min(D, R_FP)
full = max(after_FP, R_FN)
```

A missing FP or FN rule is the identity operation for that stage. The frozen
outer arms are detector-only, detector plus FN, detector plus FP, and the full
FP-then-FN Aggregator.

All twenty detector/KPI prediction bundles and their hashes are frozen before
outer labels are loaded. Metrics are direct PA-free point and one-to-one event
metrics. Binary Aggregator arms receive no AUROC/AUPRC, threshold search,
smoothing, weighting, or point adjustment.

The TASK-037E outer partition is a previously exposed follow-up validation
partition. Rule generation used only the generation partition and rule
selection used only the inner partition, but the broader experiment design
followed prior inspection of outer results. Therefore TASK-037E does not
support an untouched confirmatory superiority claim.
