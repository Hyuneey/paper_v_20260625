# Directional Relation Semantics

Step-up and step-down events are evaluated independently. For each source-step
direction, increase and decrease target responses are evaluated independently
at 1, 5, 10, 30, and 60 seconds.

A direction/horizon is eligible only when its directional consistency is
strictly greater than the opposite direction in both train1 and train2.
Equality fails. Eligible combinations are ordered by pooled consistency,
pooled robust effect ratio, shortest horizon, then lexical target direction.
The single selected combination is gated once. If it fails, the state is
`fit_unsupported`; a lower-ranked horizon or opposite direction is never tried.

`DirectionalRelationIdentityV1` comprises source, source-step direction,
target, and target-response direction. Horizon is a selected parameter, not an
identity field. Each source-target pair can therefore support zero, one, or two
directional relations.
