# DEC-029 — MULTI_PANEL_ATTACK_ACCESS_WITH_CONDITIONAL_LABEL_LEASE

Date: 2026-09-05 (Asia/Seoul)

Decision: `APPROVED_CONDITIONAL_TWO_PHASE`

The research owner approved Phase A feature-only attack access for
`HAI23_TEST2_PRIMARY_HELDOUT_V1`, `HAI22_EXTERNAL_REPLICATION_V1`, and
`HAI21_EXTERNAL_REPLICATION_V1`, followed by exactly one conditional
label/scenario lease only after all three panels have a durably replayed global
prediction freeze.

The approval preserves the following constraints:

- all three panels must complete prediction custody before any label/scenario value opens;
- the lease is single-issue and single-consume;
- predictions and method authorities are immutable after the lease;
- no method tuning, provider call, GDN training, or professor submission is authorized.

## Pre-access execution disposition

Status: `BLOCKED_DG05_AUTHORITY_REPLAY`

The approved public authority files replay byte-for-byte and retain their
approved self-hashes. However, independent implementation audit found that the
approved design cannot yet be executed with the required fail-closed semantics:

1. the state-chain implementation accepts any syntactically valid evaluation-policy hash rather than requiring the approved preregistration hash;
2. result receipts accept arbitrary SHA-256 values without reopening and replaying the corresponding result-authority bytes;
3. no complete immutable label/scenario, denominator, and per-version result-authority construction/replay path exists;
4. the frozen P1-only mapping makes `OUT_OF_SCOPE` unreachable for a known non-P1 attacked identity: an unlisted identity is classified `UNRESOLVED`;
5. scenario metric inputs are not cryptographically bound to the prediction, projection, timestamp, row-count, and scenario-authority records they evaluate;
6. the label custodian is represented by an arbitrary zero-argument callback and does not technically prevent closure capture of predictions;
7. the approved 72-cell method census has no production execution adapter, including method-specific detector replay and multipanel Formal V4/Fusion dispatch.

These are pre-access contract gaps, not observed attack results. Repair would
require a separately reviewed and re-frozen pre-DG05 authority/implementation
closure. The approved authorities were not edited or regenerated.

## Safety outcome

- attack/test payload files opened: `0`
- label/scenario values opened: `0`
- lease issues: `0`
- lease consumes: `0`
- predictions produced: `0`
- provider calls: `0`
- GDN training runs: `0`
- frozen scientific artifacts changed: `0`

This decision record does not authorize a bypass. Phase A and Phase B remain
unstarted until the pre-access contract is corrected and explicitly re-frozen.
