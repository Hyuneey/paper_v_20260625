# TASK-039C Parallel Candidate-Arm Review

Status: `passed_task039c_parallel_review_gdn_remediation_recommended`

Recommendation: `READY_FOR_BOUNDED_GDN_ENVIRONMENT_REMEDIATION`

## Review conclusion

META and STAT comply with the exact frozen TASK-039C0 protocol and are
technically ready for later TASK-039C integration. GDN passed the frozen
upstream-fidelity review and failed closed before HAI access because neither
already-approved environment contained both exact dependencies. The GDN block
is `environmental_not_scientific`.

There are no blocking findings. This review did not access real HAI feature
values, rerun STAT on HAI, train GDN, install dependencies, create the final
CandidateUniverse, authorize TASK-039D, or claim a three-arm comparison.

## Frozen identities and lineage

- Review base: `b6522fb83c4cb92d355f98af778f9a6a3c73362f`
- C0 protocol bundle: `41aab751d6bbbaadc72a95ef3289ea6440c26659fb38f640bf17fb0688836dff`
- Pair universe: `fc072d3e18ce4623972c2cb64f6266727092ecae03fdb0f0dd929d705e1d8557`
- Sources: 12; source identity hash
  `0af3f80f18a3eab59b9783af64d306c8d774eeb69b3a72c24c10048abd4ed234`
- Targets: 12; target identity hash
  `063037980aae4f0eaf45fbebb59f2aa0a924fbad583f3818107a793dfe7248e7`
- Directed P1 Boiler pairs: 144

All three remote arm tips descend directly through their stated implementation
commit from the exact C0 base. Each result commit immediately follows its
implementation commit:

| Arm | Implementation / Phase A | Result tip |
| --- | --- | --- |
| META | `2b3df4443619b8d0d19434bbcd1ded3b31a1b8ea` | `b8a744c4b2cc70cd70bfc73ce45408c2ec8b5824` |
| STAT | `629f022d35bb0db6130e7e69faaf48408b49aa9a` | `9359a8b8085b1948bde23171ec886e996fbd37b3` |
| GDN | `229cb29cfec567e6491515de34c495a863c6e5fa` | `c0efdb6218385ec326be1a929371242314e63cb6` |

The META and STAT result commits add only their public result, access audit,
and report. The GDN result commit adds only its blocked result, access audit,
and report. No scientific code, formula, policy, or hyperparameter changed
after execution began.

## Findings

### BLOCKING

None.

### IMPORTANT_NONBLOCKING

1. Direct TASK-032 execution is unavailable in the current approved
   environments because the optional JSON Schema date/date-time validator is
   absent. Installing it is prohibited by this task. Guarded discovery passed,
   and the committed arm receipts bind the frozen 106-test result.

### DOCUMENTATION_OR_HYGIENE

1. The unrelated `tmp/` directory is untracked local state only. The remote GDN
   tree and arm history contain no `tmp/` entry, and no arm scientific path
   depends on it.
2. Frozen byte-level regressions combine LF contract-source receipts with eight
   CRLF TASK-032E fixture receipts. Exact bytes were reproduced only in a
   disposable test worktree. No branch content changed.

## META compliance

META passes the metadata-only policy.

- Policy hash:
  `5fc43a043f0e75a56cab855a466a97a394fc1a6fdb67461b17696034547e4af3`
- Result hash:
  `0e3b055df911c74bd0e0993b7b3bb122860b265192ad0cf91d54edc1e74635bf`
- Private evidence-ledger hash:
  `efc495f5754d5cd31b0017847df5423bece170da8ea87358d44daac1ee9b4c62`
- Access-audit hash:
  `1a21a4c1a67c053c2be576299cc77584f0f9c4cc7e3e62d738cd083cf4025a68`
- Evaluated 144; supported 30; unsupported 114.
- Tiers: M1 = 12, M2 = 11, M3 = 7, unsupported = 114.
- Top-10 = 10, top-20 = 20, available top-30 for the top-40 request;
  shortfall = 10. No unsupported pair padded a budget.
- The single ranking is M1 before M2 before M3, then independent official
  reference count descending, source identity, and target identity.
- No numerical weighting, cross-arm score, HAI feature access, general LLM
  semantic inference, causal claim, or confirmed-relation claim was used.
- The official graph remains a weak relation reference, not causal truth.

The independent reference count is the number of distinct approved official
evidence-source categories represented by a pair's serialized reference IDs.
The only categories are the official HAI technical manual and the official P1
physical graph. Multiple locators or reference IDs from the same category count
once. Nineteen records contain more serialized IDs than counted categories.
The private evidence input and ledger reproduce this rule uniformly for all 144
pairs; all counts, tiers, and the complete supported ranking match the public
result. No per-pair manual count override was found.

## STAT compliance

STAT passes the frozen train1/train2-only policy.

- Policy hash:
  `2e3413ee190dbce7106876ff5dd053161a17e18e80d142e75c05e50430c008e3`
- Result hash:
  `7351e295be7e5bdd2b1cb9677091426899e5a2616c60245f953ff6602d106950`
- Ranking hash:
  `5f9b97b9a7b426f1aa2036b4f6f82423801ecb3335093e08a5a61e3bad73e1a4`
- Private ledger hash:
  `6333ff8f235d62fec1b86d78f1637f47ec66c0b4fb73e7476a094e49564f59d2`
- Access-audit hash:
  `9588682c8c6c52afdc4dea960c1ccfbe221501a7f756ff9de2893474eb0099e4`

The code computes, for each file independently,
`dx(t)=x(t)-x(t-1)`, `dy(t)=y(t)-y(t-1)`, and
`PearsonCorr(dx(t),dy(t+h))` for `h = 1, 5, 10, 30, 60`. It creates neither a
cross-file difference nor a cross-file lag pair and does not pool train1 and
train2 before file-specific correlations. No train3, train4, test, label, or
BR2 pair-level input is accepted.

Finite, nonzero, same-sign correlations in both files are required. Stability
strength is `min(abs(r_train1),abs(r_train2))`; the strongest stable horizon is
selected, with the shortest horizon winning an exact strength tie. There is no
minimum correlation threshold and no unstable padding. The private ledger
self-hash, all 144 horizon selections, the stable-before-unstable ranking, and
all public prefixes were independently reproduced. Synthetic NumPy float64
parity against the `math.fsum` reference passed at absolute and relative
tolerance `1e-12`. Real HAI correlation was not rerun.

The 141 stable candidates are not 141 confirmed relations. They are 141 pairs
with a finite, nonzero, same-sign lagged change correlation in both fit files
under the frozen no-minimum-threshold ranking policy. The public report states
this claim boundary without overclaiming causality, physical strength, rule
validity, anomaly evidence, or delayed-response confirmation.

## GDN compliance and dependency boundary

GDN passes fidelity and boundary review and remains blocked before execution.

- Policy hash:
  `9c2387a98312ef6c96ddcd17a871ceb70a96b670eb4a39a7269878101f2ba41a`
- Fidelity status: `passed_upstream_gdn_fidelity`
- Fidelity hash:
  `93821469e465a942ff94c779c6798355383e35003b13db24c19b9760ca3266c4`
- Backend classification: `upstream_aligned_validated`
- Arm status: `blocked_optional_dependency`
- Upstream commit: `9853899da860682669a134e4af315d036aab4eca`
- Required environment: `torch==2.12.1` and
  `torch-geometric==2.8.0`
- Seeds attempted/completed: 0 / 0
- Evaluated pairs: 0
- HAI feature access: false
- Candidate ranking or top-K: absent

The pinned checkout is clean and detached at the exact commit. All seven
frozen Git blob IDs and canonical blob SHA-256 values were independently
verified. All material fidelity fields are resolved. The dedicated backend is
separate from the existing deterministic and Torch/PyG smoke trainers; those
remain synthetic smoke only. No smoke or fallback backend, META/STAT output,
BR2 pair result, HAI file, attention-primary score, or post-hoc XAI path was
used. The common pair universe remains a future-execution binding only.

The blocked result arises solely because neither already-approved environment
contains both exact versions. No installation, upgrade, version substitution,
or fallback was attempted. One bounded environment-remediation attempt is
scientifically and operationally justified: establish one preapproved isolated
environment with the exact two versions, then rerun the existing gated GDN arm
without changing its implementation, fidelity receipt, policy, data scope, or
fallback prohibition. This review does not perform or authorize that attempt.

## Cross-arm overlap

The overlap is descriptive only. It is not candidate quality, method
superiority, a combined score, or a global ranking. GDN is excluded because it
produced no ranking.

| View | META available | STAT available | Intersection | META only | STAT only | Jaccard | Unscored union |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Top-10 | 10 | 10 | 1 | 9 | 9 | 1/19 = 0.05263157894736842 | 19 |
| Top-20 | 20 | 20 | 11 | 9 | 9 | 11/29 = 0.3793103448275862 | 29 |
| Top-40 asymmetric | 30 | 40 | 24 | 6 | 16 | 24/46 = 0.5217391304347826 | 46 |

The top-40 row uses META's available top-30 and STAT's top-40. META is not
padded to 40.

## Provisional META plus STAT top-20 preview

The non-authoritative union contains 29 pairs and is de-duplicated only by
`(source,target)`. It has no global rank and no merged score. Exact full-
precision STAT correlations and the common-universe reference are retained in
the JSON review record.

- Preview count: 29
- Preview hash:
  `162638474e57d06d731a6cf1a6a4a224f990f6ea602e982a762d0971da97fb85`

| Source | Target | Origins | META rank/tier | STAT rank/horizon/sign | STAT r1 / r2 / strength |
| --- | --- | --- | --- | --- | --- |
| P1_FCV01D | P1_FT02 | META, STAT | 1 / M1 | 19 / 60 / + | 0.15901519605380818 / 0.23633176875723416 / 0.15901519605380818 |
| P1_FCV01D | P1_FT02Z | META, STAT | 2 / M1 | 3 / 5 / + | 0.6333021690899233 / 0.5670033714609225 / 0.5670033714609225 |
| P1_FCV01D | P1_PIT02 | META, STAT | 13 / M2 | 11 / 10 / - | -0.3604323608701531 / -0.47837993692512615 / 0.3604323608701531 |
| P1_FCV01D | P1_TIT01 | META | 6 / M1 | - | - |
| P1_FCV01Z | P1_FT02 | META, STAT | 14 / M2 | 4 / 1 / + | 0.535276546958903 / 0.4948530361170134 / 0.4948530361170134 |
| P1_FCV01Z | P1_FT02Z | META, STAT | 15 / M2 | 1 / 1 / + | 0.78401032810731 / 0.761456475764756 / 0.761456475764756 |
| P1_FCV01Z | P1_PIT02 | META, STAT | 16 / M2 | 13 / 5 / + | 0.3916379307539734 / 0.33034436278913765 / 0.33034436278913765 |
| P1_FCV02D | P1_FT02 | META | 7 / M1 | - | - |
| P1_FCV02D | P1_FT02Z | META, STAT | 8 / M1 | 14 / 5 / - | -0.26291212542591424 / -0.2855660308208258 / 0.26291212542591424 |
| P1_FCV02D | P1_PIT02 | STAT | - | 8 / 5 / - | -0.39050178021187487 / -0.407637637092625 / 0.39050178021187487 |
| P1_FCV02D | P1_TIT01 | META | 9 / M1 | - | - |
| P1_FCV02Z | P1_FT02 | STAT | - | 20 / 5 / + | 0.15672012733249302 / 0.170977287947114 / 0.15672012733249302 |
| P1_FCV02Z | P1_FT02Z | STAT | - | 7 / 1 / - | -0.3950211512126073 / -0.4270635790394675 / 0.3950211512126073 |
| P1_FCV02Z | P1_PIT02 | STAT | - | 2 / 1 / - | -0.6052714782816841 / -0.6331832853477036 / 0.6052714782816841 |
| P1_FCV03D | P1_FT03 | META | 3 / M1 | - | - |
| P1_FCV03D | P1_FT03Z | META | 4 / M1 | - | - |
| P1_FCV03D | P1_LIT01 | META | 10 / M1 | - | - |
| P1_FCV03Z | P1_FT03 | META, STAT | 17 / M2 | 15 / 1 / + | 0.25613440236115 / 0.24775660215838072 / 0.24775660215838072 |
| P1_FCV03Z | P1_FT03Z | META, STAT | 18 / M2 | 5 / 1 / + | 0.5620438187637141 / 0.4521517989817558 / 0.4521517989817558 |
| P1_LCV01D | P1_LIT01 | META, STAT | 11 / M1 | 18 / 60 / + | 0.19458934285028526 / 0.2115714166705557 / 0.19458934285028526 |
| P1_LCV01D | P1_PIT01 | STAT | - | 16 / 5 / - | -0.2335773450929532 / -0.20408186270652884 / 0.20408186270652884 |
| P1_LCV01Z | P1_FT01Z | STAT | - | 10 / 1 / + | 0.44825830776969006 / 0.3650495762983653 / 0.3650495762983653 |
| P1_LCV01Z | P1_PIT01 | STAT | - | 6 / 1 / - | -0.40822204074307206 / -0.39979940010471254 / 0.39979940010471254 |
| P1_PCV01D | P1_FT01 | META | 19 / M2 | - | - |
| P1_PCV01D | P1_FT01Z | META | 20 / M2 | - | - |
| P1_PCV01D | P1_LIT01 | STAT | - | 12 / 30 / + | 0.34444737583481055 / 0.3356902606589881 / 0.3356902606589881 |
| P1_PCV01D | P1_PIT01 | META, STAT | 5 / M1 | 17 / 5 / + | 0.23880520964919372 / 0.19683975711041937 / 0.19683975711041937 |
| P1_PCV01Z | P1_PIT01 | STAT | - | 9 / 1 / + | 0.43857523858326364 / 0.3753573522136355 / 0.3753573522136355 |
| P1_PP04 | P1_TIT03 | META | 12 / M1 | - | - |

## Verification

### Independently rerun

- META targeted: 23 passed, 1 expected skip because the ignored private ledger
  is absent from the clean arm worktree; that ledger was checked separately.
- STAT targeted: 24 passed, including NumPy/`math.fsum` parity.
- GDN fidelity and blocked-result targeted: 19 passed.
- C0: 38 passed.
- P1D GDN fidelity: 18 passed.
- BR1: 34 passed.
- BR2: 43 passed.
- Guarded discovery: 572 passed; 40 known optional import boundaries; zero
  failures or errors.
- Public Python compile: 308 META, 308 STAT, and 310 GDN tracked files.
- Tracked JSON parse: 422 META, 422 STAT, and 425 GDN files.
- Draft 2020-12 meta-validation: 66 META, 66 STAT, and 67 GDN v6
  schemas; each arm result and the GDN fidelity document validated.
- Public and private self-hashes, the C0 and policy hashes, source/target/pair
  hashes, all seven GDN upstream blobs, branch ancestry, result-commit diffs,
  public leak boundaries, and exact `pip check` in three existing environments.

Direct TASK-032 execution was attempted but not accepted because the required
optional date/date-time format validator is absent and may not be installed.
TASK-032 remains covered by the committed 106-test receipt and guarded
discovery under the repository's declared optional-import policy.

### Verified from committed receipts or private ledgers only

- META's real-run no-feature-access boundary and official-reference opens.
- STAT's train1/train2-only real execution, file-open counts, and no access to
  train3/train4/test/labels. Real HAI correlation was not rerun.
- GDN's zero HAI access and zero attempted/completed seeds in the blocked run.
- The frozen direct TASK-032 106-test result.

Private ledger contents were neither printed nor copied into public artifacts.

## Final authority

META and STAT are ready inputs for a later authorized TASK-039C integration.
GDN is not a ranking-bearing arm until a separately authorized exact-environment
attempt succeeds. This review creates neither the final CandidateUniverse nor
TASK-039D authority.

Review JSON artifact hash:
`c2f3159a2ca5a0028ea5965c9aec0f69986110640403ffa29edf6f600f88f6b4`
