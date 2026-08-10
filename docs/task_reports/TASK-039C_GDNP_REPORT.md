# TASK-039C-GDNP Port Compatibility Closure and GDN Candidate Discovery

Status: `passed_task039c_gdn_candidate_discovery`

The PyG 1.5 to 2.8 compatibility matrix has no unresolved rows. The existing sparse-softmax keyword adapter and explicit `node_dim=0` binding are classified as `documented_non_scientific_api_adapter`; model equations, learned graph construction, hyperparameters, data policy, and ranking are unchanged.
All three frozen seeds completed and the denominator-three ranking was produced once.

## Compatibility

- Closure receipt: `fe59877405b17c7268c800690c434b267056a3e8a0c7b50715cec8df12f61f44`.
- Environment receipt: `d0602e4f591073d58881aa1f918b788176ed888d5265f5e253fd272e060109c6`.
- Fidelity receipt: `93821469e465a942ff94c779c6798355383e35003b13db24c19b9760ca3266c4`.
- API drift rows: `17` exact, `3` adapted, `0` unresolved.
- Sparse-softmax compatibility: `passed_semantics_preserving_pyg_softmax_compatibility`.
- MessagePassing compatibility: PyG 1.5 `node_dim=0` aggregation semantics restored explicitly; aggregation remains addition and all custom attention equations are unchanged.
- Additional compatibility adapters: none beyond the previously approved sparse-softmax keyword binding and the explicit `node_dim=0` binding.
- Legacy oracle: `blocked_official_legacy_environment_unavailable` (nonblocking).
- GraphLayer forward/backward, index/self-loop, GNNLayer, tiny full-GDN, and tiny training-loop gates passed before HAI access.

## Execution

- Seeds attempted: `[11, 23, 37]`.
- Seeds completed: `[11, 23, 37]`.
- Seed retries: `0`.
- Per-seed completed epochs: seed 11 = `23`, seed 23 = `19`, seed 37 = `28`.
- Evaluated candidates: `144`.
- Supported candidates: `39`.
- Top10/top20/top40 counts: `10` / `20` / `39`.
- Candidate shortfall: top10 = `0`, top20 = `0`, top40 = `1`.
- Ranking hash: `8f549a292dec33f63ca0551fd876444ac9f4902b022c804cdeaa603d063bfab3`.
- Private seed-ledger hashes: seed 11 = `322e1d3a31d4c07a3e2249d0e99d9ae1fd3cfa84ac683d2b7519cb150aaff978`, seed 23 = `7cd7cfec18d5c97323cd6a55a1c87c563a5ec4a8d07ba33c90d9f708d6106338`, seed 37 = `d6b1fa41076eac845642bf4ede3fbf84d9f7f08e80e79ec4fe1bcfb637ebde10`.
- Data-access audit: `241a7dfb622c0ac0cad5f376b1893854d480cdb6a9bdccc0fbfc61012de6e771`.

## Verification and regressions

- GDNP: `14` tests passed; the one skipped test is the unavailable optional legacy PyG 1.5 oracle.
- Frozen GDNC: `21` tests passed at its execution-code commit.
- Frozen GDNR: `23` tests passed at its execution-code commit.
- GDN: `19` tests passed; C0: `38`; P1D: `18`; BR0/BR1/BR2: `101`; TASK-032: `106`; candidate/profiling: `22`.
- Post-result GDN/C0/candidate/profiling group: `79` tests passed.
- Public Python compile, `446` JSON parses, `79` v6 schema meta-validations, result/access/execution instance validation, public self-hashes, exact-environment and existing-environment `pip check`, `git diff --check`, frozen Rule v1/Verifier v1/Runtime v1 Git-blob hashes, public leak scans, private-ledger self-hashes, and checkpoint exclusion passed.
- Guarded public discovery enumerated and ran `794` tests from a normalized frozen checkout: `788` passed. The remaining six are environment-sensitive baseline checks unrelated to the GDNP patch: two require pandas, which is not installed in the exact no-install GDN environment; three require Torch/PyG to be absent, which conflicts with this exact execution environment; and one compares external-checkout worktree bytes affected by Windows CRLF conversion. Their relevant frozen targeted suites passed in isolated compatible environments. No dependency, historical test, or source was changed to mask these diagnostics.

## Data and claim boundary

Train1/train2 accessed: `True` / `True`. Train3, train4, test, labels, attacks, P2/P3/P4 values, BR2 pair outcomes, META output, and STAT output were not accessed. No checkpoint, state dictionary, raw row, raw window, or embedding was committed.

Recommended next path: `PROCEED_WITH_THREE_ARM_INTEGRATION`.

GDN output is learned-graph candidate evidence only. It does not establish causality, a confirmed relation, rule validity, anomaly performance, root cause, or GDN superiority.
