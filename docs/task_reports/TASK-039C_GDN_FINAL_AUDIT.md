# TASK-039C-GDN-AUDIT - Independent Final GDN Audit

Status: `passed_task039c_gdn_final_audit`

Integration readiness: `READY_FOR_THREE_ARM_INTEGRATION`

This audit did not read raw HAI feature values, rerun real HAI GDN training, alter a ranking, create the final CandidateUniverse, or authorize TASK-039D.

## Audit conclusion

The compatibility-closed GDN result passes the independent source, compatibility, seed, ranking, data-boundary, artifact-integrity, and commit-separation audits. The three private seed ledgers were locally available; their self-hashes were verified without printing or copying private contents, and they independently reproduce the public 39-candidate GDN ranking and its frozen hash.

META and STAT remain bound to the passed independent parallel review at `058b5e2023b66ccbf6704c5baf1f6c677f17b07a`, which has zero blocking findings. Their public result artifacts alone were used for overlap.

## Findings

- BLOCKING: 0.
- IMPORTANT_NONBLOCKING: 1. The exact legacy PyG 1.5 synthetic oracle remains unavailable. This is nonblocking because the official-source audit, independent pure-PyTorch reference, forward and backward parity, index/self-loop parity, GNNLayer parity, tiny full-GDN gate, and tiny training-loop gate all pass.
- DOCUMENTATION_OR_HYGIENE: 2. Guarded discovery requires compatible environment/commit interpretation, and the unrelated untracked `tmp/` in the original checkout was excluded through a fresh worktree.

## Lineage and identities

The complete ancestry is exact:

| Stage | Implementation | Result | Historical status |
|---|---|---|---|
| Initial GDN | `229cb29cfec567e6491515de34c495a863c6e5fa` | `c0efdb6218385ec326be1a929371242314e63cb6` | `blocked_optional_dependency` |
| GDNR | `914e5159e719271262c8caa5bf94a2a806efc589` | `6474816068aae786a490c634c28d665772bc2243` | `failed_gdn_training` |
| GDNC | `19249db6e0f15afb492d6930e9297bcdd9c63d2e` | `932c3c7e58e853959b006a6a023743620dd4457d` | `failed_gdn_final_attempt` |
| GDNP | `6790505e08ea06d6b3f6d34f9fd533d381696b1f` | `1204ff4e6d790c2cd0e8268f778a8f071e5eea4b` | `passed_task039c_gdn_candidate_discovery` |

No historical result was rewritten or deleted. The passing GDNP result supersedes the earlier results scientifically while preserving them in Git history.

Frozen bindings match:

- Result artifact: `2c58308d0d97d93cf671907064c805dbadcb01508ed8571090a448be6c855bfc`.
- Ranking: `8f549a292dec33f63ca0551fd876444ac9f4902b022c804cdeaa603d063bfab3`.
- Compatibility closure: `fe59877405b17c7268c800690c434b267056a3e8a0c7b50715cec8df12f61f44`.
- Exact environment: `d0602e4f591073d58881aa1f918b788176ed888d5265f5e253fd272e060109c6`.
- Original fidelity: `93821469e465a942ff94c779c6798355383e35003b13db24c19b9760ca3266c4`.
- Data access: `241a7dfb622c0ac0cad5f376b1893854d480cdb6a9bdccc0fbfc61012de6e771`.

## Compatibility closure

Compatibility status is `passed_pyg15_to_pyg28_gdn_port_compatibility_closure`. The drift matrix contains 17 exact rows, 3 adapted rows, and 0 unresolved rows.

The three adapted rows are:

1. MessagePassing default `node_dim`: PyG 1.5 default 0 versus PyG 2.8 default -2, bound explicitly as `MessagePassing(aggr="add", node_dim=0)`.
2. Aggregation dimension: the same documented default drift is closed explicitly so edge-count dimension 0 is aggregated by addition.
3. Sparse-softmax positional signature: old `softmax(src, index, num_nodes)` meaning is preserved as `softmax(src, index=index, num_nodes=num_nodes)`.

All are `documented_non_scientific_api_adapter` changes. Addition aggregation, source/destination meanings, custom attention equations, graph edges, model architecture, and frozen hyperparameters are unchanged. The independent pure-PyTorch reference is test-only and is not the production backend.

The synthetic softmax, GraphLayer forward/backward, index/self-loop, GNNLayer, tiny full-GDN, and tiny training-loop gates were independently rerun in the exact existing environment: 14 passed and the optional legacy-oracle test was skipped.

## Patch scope and commit separation

Between `932c3c7...` and Commit A, the sole production scientific-source delta is the explicit `node_dim=0` dependency binding; the prior softmax adapter remains unchanged. No forbidden method, architecture, objective, training, universe, or ranking choice changed.

Commit B changes only:

- `TASK-039C_GDNP_DATA_ACCESS_AUDIT.json`
- `TASK-039C_GDNP_EXECUTION_RECEIPT.json`
- `TASK-039C_GDNP_REPORT.md`
- `TASK-039C_GDN_RESULT.json`

No scientific source, formula, config, compatibility adapter, or hyperparameter changed after real execution began.

## Seed and ranking audit

- Attempted/completed: `[11, 23, 37]` / `[11, 23, 37]`.
- Retries: 0.
- Completed epochs: seed 11 = 23; seed 23 = 19; seed 37 = 28.
- Frozen hyperparameter hash for every seed: `68fbd006af1bc71468c157ba90888f54b8c0cbeba1aa7aba1121701a5b87870e`.
- Evaluated pairs: 144.
- Supported pairs: 39.
- Top10/top20/top40: 10 / 20 / 39.
- Top40 shortfall: 1; no unsupported padding.

The independent reconstruction counted selections in the three private ledgers, divided by exactly 3, took the median similarity across all three seeds, and sorted by descending frequency, descending median similarity, source, then target. It exactly matches the public ranking and frozen ranking hash.

`edge_selection_frequency` is learned-graph stability evidence. `median_upstream_graph_similarity` is method-specific ranking evidence. Neither is numerically comparable to META tiers or STAT correlations, and neither confirms causality, physical truth, rule validity, anomaly performance, root cause, or GDN superiority.

## Data and artifact boundary

The arm receipt records train1/train2 access and no train3, train4, test, label, attack, P2/P3/P4, BR2 pair-outcome, META, or STAT access. The audit itself did not open train1/train2 or any other HAI values.

The P1 candidate-learning view and 37-feature-order bindings match their frozen hashes. No checkpoint, raw window, node embedding, private ledger content, or absolute local path is committed. Nine relevant public self-hashes and seven schema instances pass; all three private ledger self-hashes also pass.

## Three-arm overlap

All overlap is descriptive and unscored.

| Budget | Union | META&STAT | META&GDN | STAT&GDN | Triple |
|---|---:|---:|---:|---:|---:|
| Top10 | 28 | 1 | 1 | 0 | 0 |
| Top20 | 47 | 11 | 1 | 1 | 0 |
| Sensitivity: META30/STAT40/GDN39 | 76 | 24 | 7 | 5 | 3 |

Top10 origin decomposition is META-only 8, STAT-only 9, GDN-only 9, META+STAT-only 1, META+GDN-only 1, STAT+GDN-only 0, and all-three 0.

Top10 exactly-two identities:

- META+STAT only: `P1_FCV01D -> P1_FT02Z`.
- META+GDN only: `P1_FCV02D -> P1_TIT01`.
- STAT+GDN only: none.
- All three: none.

Top20 origin decomposition is META-only 8, STAT-only 8, GDN-only 18, META+STAT-only 11, META+GDN-only 1, STAT+GDN-only 1, and all-three 0.

The primary audit-only `union(META top20, STAT top20, GDN top20)` contains 47 pairs. Its deterministic preview hash is `81a7b6e0dfffdd6ce1b49799721c3dfcfb484af247a194d87b0602e76ac551ff`. The JSON retains per-arm provenance/evidence without a merged score, global rank, serialization rank, or confirmed-relation flag.

Sensitivity uses META’s available top30, STAT top40, and GDN’s available top39. META and GDN are not padded. The union is 76; per-arm-only counts are META 2, STAT 14, and GDN 30. This cohort is not the primary TASK-039D input.

## Regressions independently rerun

- GDNP: 14 passed, 1 legacy-oracle skip.
- Frozen GDNC: 21 passed at `19249db...`.
- Frozen GDNR: 23 passed at `914e515...`.
- GDN: 19; C0: 38; P1D: 18.
- BR0/BR1/BR2: 101.
- TASK-032: 106.
- Candidate/profiling: 22.
- Total targeted passes: 362.
- Public Python compile: 449 files.
- Public JSON parse: 449 files.
- v6 schema meta-validation: 79 schemas.
- Exact and existing environment `pip check`, `git diff --check`, frozen Rule v1/Verifier v1/Runtime v1 receipt hashes, relevant self-hashes, and task-local public/private/checkpoint/path leak scans passed.

Guarded discovery ran 808 runnable tests: 801 passed and 7 diagnostics were classified. The six previously reported diagnostics are all `expected environment incompatibility`: two require pandas absent from the exact no-install GDN environment, three require Torch/PyG to be absent despite the exact GDN environment intentionally containing them, and one observes Windows CRLF bytes for eight TASK-032E fixtures whose LF-normalized hashes exactly match the frozen inventory. Regression = 0; unknown = 0.

The successful branch exposes one additional expected commit-context diagnostic: the historical GDNC patch-scope guard rejects the later separately authorized GDNP `node_dim=0` change. Its complete 21-test frozen suite passes at the GDNC execution-code commit. This is not an unexplained scientific regression.

## Independent versus receipt-bound checks

Independently rerun: lineage/ancestry, source diff, Commit-A/B diff, compatibility suites, private-ledger self-hashes and ranking reconstruction, public overlap and preview construction, targeted regressions, guarded discovery, compile/JSON/schema checks, pip checks, diff checks, and leak scans.

Verified from committed receipts and hashed private ledgers without raw-value replay: real-data file access, seed epoch/best-state execution facts, and the fact that no prohibited real-data file was opened. The audit did not rerun HAI training or inspect raw HAI values.

## Decision

`READY_FOR_THREE_ARM_INTEGRATION`

This authorizes only later TASK-039C integration under the frozen unscored-union policy. TASK-039D remains unauthorized.

Audit JSON artifact hash: `8f40aec0dddd48b487c6ca503fc9b71791626aef2cb3b3cf8935b182a34e6357`.
