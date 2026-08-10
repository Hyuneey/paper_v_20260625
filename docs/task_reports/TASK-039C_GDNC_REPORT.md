# TASK-039C-GDNC Softmax Compatibility and Final GDN Attempt

Status: `failed_gdn_final_attempt`

The single correction is classified as `documented_non_scientific_api_adapter`. The project-owned port now binds the upstream third-argument node-count meaning to PyG 2.8's explicit `num_nodes` keyword. No mathematical input, model equation, graph edge, hyperparameter, package, seed, or ranking rule changed.

The final GDN attempt failed closed. No ranking or top-K output was produced.

The pre-HAI full graph-layer forward gate reached the corrected softmax and
then failed at a distinct PyG 2.8 aggregation-broadcast boundary. The frozen
message output had shape `[edges, heads, channels]`, while PyG 2.8 attempted
to broadcast the one-dimensional aggregation index along a different axis.
This raised a `RuntimeError` before any HAI file or seed was opened. A second
compatibility correction is not authorized, so the real GDN execution was not
started.

## Lineage

- Initial GDN: `blocked_optional_dependency`.
- GDNR: exact environment passed; seed 11 failed before completion because the old positional node count bound to PyG 2.8 `ptr`.
- GDNC: one semantics-preserving correction; final attempt seeds attempted `[]` and completed `[]`; retries `0`.

## Receipts

- Compatibility receipt: `e045bae45954b6e78a2873a7560214da71c55afd10ad53e99a2a971dbcd0041d`.
- Environment receipt: `d0602e4f591073d58881aa1f918b788176ed888d5265f5e253fd272e060109c6`.
- Fidelity receipt: `93821469e465a942ff94c779c6798355383e35003b13db24c19b9760ca3266c4`.
- Data-access audit: `186f400f15f0b0165493af8986e9b865176f418d79adfc2c8e865b6ab3e32a3d`.
- Execution receipt: `d79fa4f40c741cd2d3345b1f60373ed2e8c6f78c6725a745c4d04f438937736d`.
- GDN result binding: `f00610c2a334d433949a0ad91957b7a75ccbe8475be9fa3755e9f6eb7f9e6a30`.

## Data and claim boundary

Train1/train2 accessed: `False` / `False`. Train3, train4, test, labels, attacks, BR2 pair supervision, META output, and STAT output were not used. No checkpoint, raw window, raw value, or node embedding was persisted.

Recommended next path: `PROCEED_WITH_META_STAT_INTEGRATION_GDN_UNAVAILABLE`.

## Verification

- GDNC compatibility, execution-contract, and schema tests: 21 passed.
- GDNR tests: 23 passed; existing GDN tests: 19 passed; C0 tests: 38
  passed; P1D tests: 18 passed across their exact and Torch-free environments.
- BR0, BR1, and BR2 regressions: 24, 34, and 43 passed, respectively.
- TASK-032 frozen regressions: 106 passed.
- Guarded public discovery: 599 runnable tests passed; 43 known optional
  import boundaries were classified.
- Public Python compile: 320 files passed; public JSON parse: 434 files
  passed; all 80 public schemas passed their declared-draft checks.
- Public instance and private terminal-record self-hashes, exact-environment
  `pip check`, `git diff --check`, frozen Rule v1 / Verifier v1 / Runtime v1
  hashes, upstream cleanliness, and public leak/raw/checkpoint scans passed.

The full graph-layer forward gate is the terminal failed scientific check; it
is not counted as a passing test or hidden by the passing regression totals.

GDN output is candidate graph evidence only. It does not establish causality, a confirmed relation, rule validity, anomaly performance, or method superiority. TASK-039D remains unauthorized.
