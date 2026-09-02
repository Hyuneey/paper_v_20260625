# VALIDATION V2 Program QA — Normal-only Dual Track

## Verdict

`PASS_WITH_NONBLOCKING_LEGACY_SUITE_LIMITATIONS`

Independent result reviewer: `dualtrack_a_binding_qa`

## Verified

- EXP-01 remains `COMPLETE_QA_PASS`; its negative result and GDN ablation
  disposition were not rewritten.
- Track A and EXP-01B use separate public and private namespaces.
- Track A freezes META 20, STAT 20, a 29-pair union, 39 confirmed directional
  relations, the selected EXP-02 policy, and a 39-rule Formal V4 portfolio.
- EXP-01B freezes nine CUDA runs over three views and seeds 11/23/37.
- Public EXP-01B self-hashes, cross-hashes, 2,736 pair ranking rows, 76 metric
  rows, 6,480 seed ranking rows, and 20 stability rows replay with mismatch 0.
- The preregistered disposition independently replays as `GDN_ABLATION_ONLY`.
- Attention vectorization is semantically equivalent to the explicit mapping;
  private checkpoint caches are atomic, self-hashed, identity-bound, ignored,
  and non-authoritative.
- Applicable Track A/Track B tests: 76 PASS, 2 optional-Torch skips.
- RCC, dashboard, Registry, link, and preservation tests: 172 PASS.
- Registry/generated validation and privacy scan: PASS, private exposures 0.
- PILOT V1 preservation: 3,021/3,021 blobs PASS.

## Full legacy-suite context

The repository-wide discovery run executed 3,917 tests and was not a clean
portable gate: 42 failures, 86 errors, and 38 skips remain in legacy suites
that require optional `torch`/`jsonschema`, an external ARGOS checkout,
private terminal-audit roots, or exact historical commit/worktree bytes. These
pre-existing non-portable and exact-authority tests are outside the scoped
dual-track acceptance set and were not weakened or skipped to obtain the PASS
above. All current EXP-01B, EXP-02/V2A, RCC, dashboard, Registry, privacy, and
PILOT-preservation suites passed independently.

## Safety

- test1: 0
- labels: 0
- test2: 0
- held-out: 0
- provider calls: 0
- post-result tuning: 0
- PILOT V1 changes: 0
- public private-data/path exposure: 0

During independent QA, one diagnostic read replayed nine private derived
lineage-cache JSON documents. It did not open raw HAI, checkpoints, test1,
labels, test2, held-out data, or credentials; no private value or path was
printed, persisted publicly, or modified.

## Boundary

This QA supports normal-only result integrity and implementation consistency.
It does not establish anomaly-detection performance, causality, human
explanation usefulness, or held-out generalization. EXP-04 label-blind
prediction and durable freeze are the exact next scientific gate.
