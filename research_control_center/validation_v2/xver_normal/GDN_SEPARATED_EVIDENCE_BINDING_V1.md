# Approved separated GDN evidence roles

User decision: **APPROVED_WITH_SEPARATED_GDN_EVIDENCE_ROLES**.
This prospective amendment resolves the estimator-role choice recorded in
`GDN_EVENT_EVIDENCE_BINDING_DECISION_V1.md`; that historical decision brief and
the historical blocked status remain unchanged. No scientific result has been
used to choose this amendment.

## Provider and bounded train2 retrieval

`EXP03B_COMPATIBLE_SPLIT_PURE_GLOBAL` is the only predictive GDN evidence role.
Five horizon rows (1/5/10/30/60) use all windows in each same-split seed's frozen
purged validation partition. Preserve fixed single-edge deletion, no refill,
signed relative delta MSE, shared-encoder attention, and exact EXP03B medians:
embedding and attention across all three seeds; edge effect across available
graph-member seeds only, with no available effect represented as unavailable.
No best seed selection. Train1 goes only to provider evidence; train2 only to
the bounded retrieval authority. GDN is not a hard verifier gate.

## Auxiliary event evidence

`AUXILIARY_CORROBORATION_ONLY` is a physically separate private sidecar.
Use SCI01 common fixed split-local source events, intersected with each seed's
precommitted same-split purged validation windows. The existing EXP01C window
anchor is `start + history_rows`; do not alter its target indexing. Preserve
two source directions times five horizons as ten rows per pair and seed.
No-event support and missing learned edge are explicit unavailable states,
never fabricated zero effects. Preserve per-seed signed effects and support;
do not select a favorable seed. No new direction-pooling or global/event
aggregation estimator is created.

## Prohibited uses

Event evidence cannot enter provider prompts, retrieval, verifier acceptance,
candidate admission, semantic induction, numeric policy, or global evidence
aggregation. Train3/train4 and selected numeric policy cannot define GDN events.
All source events are file-local and derived only from the corresponding train1
or train2 feature projection. No trained HAI23 weights transfer; no architecture,
optimizer, hyperparameter, seed, candidate, T0, SCI02B or Formal V4 change.

## Execution boundary

Approval resolves the scientific choice, not evidence completion. The 12-run
external schedule still requires committed implementation/custody/environment
and preflight replay before run 1. Exact provider token/cost ceilings require
actual frozen global evidence packs. Provider permission remains absent;
DG-XVER-PROVIDER and DG-05 remain unapproved.
