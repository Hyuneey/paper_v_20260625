# TASK-039C Three-Arm Integration

## Operation

`integrate_candidate_union_v1` consumes META top20, STAT top20, and GDN top20.
It visits arms in that order, de-duplicates by exact `(source, target)`, and
retains origin arms, arm-local ranks, and SHA-256 evidence bindings.

The encounter order is deterministic storage order only. Each output entry has
`serialization_position`, `global_rank = null`, `global_score = null`, and
`serialization_order_is_scientific_rank = false`.

## Expected overlap

The primary top-20 union has 47 pairs. META and STAT overlap on 11; META and
GDN on 1; STAT and GDN on 1; no pair occurs in all three. Low overlap is not a
failure. Under the preregistered interpretation, the arms expose substantially
different candidate sets and therefore offer a meaningful common-protocol
comparison opportunity.

The sensitivity view uses META's available top30, STAT top40, and GDN's
available top39. Its union of 76 is descriptive only; META and GDN are not
padded, and this view is not the TASK-039D primary cohort.

## Public-only boundary

Integration loads only six committed public JSON artifacts: C0, three arm
results, the preliminary review, and the final GDN audit. It opens no HAI data
and no private ledger. BR2 pair outcomes are not ground truth for integration.
