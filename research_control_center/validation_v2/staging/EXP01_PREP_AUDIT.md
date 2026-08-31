# EXP-01 GDN Contribution — Preparation Audit

Status: `PREPARED_NOT_EXECUTED`

Scope: static source/test/audit inspection only. This preparation did not read HAI values, test1, test2, held-out data, labels, private ledgers, or provider state. It did not import Torch, train GDN, profile a relation, compute an experimental metric, or alter PILOT V1.

## 1. Multi-agent record

| Field | Record |
|---|---|
| multi-agent feasibility | Suitable as one bounded read-only preparation track; implementation ownership must remain singular because the backend, result contract, and preregistration hashes are shared authority surfaces. |
| available | yes |
| used | yes; this document is the `v2_exp01_prep` specialist output |
| role | GDN contribution preparation auditor |
| parallelized work | Static EXP-01 evidence mapping only; no shared-file implementation |
| shared-file owner | parent coordinator / future single EXP-01 implementation writer |
| files written by this agent | this audit and `EXP01_PREREGISTRATION_DRAFT.json` only |
| conflicts | none observed; unrelated GAP-FIX-METRIC working changes were not touched |
| independent QA | required after implementation and again after execution; not performed by this preparation agent |

## 2. Source-supported current state

1. The current passing scientific GDN identity is the upstream-aligned path in `paperworks.gdn.upstream_candidate_backend_v1`, not `paperworks.gdn.masked`, `paperworks.gdn.torch_backend`, or an earlier blocked path.
2. `UpstreamGDNTrainingConfigV1` freezes seeds `(11, 23, 37)`, a 37-node full-P1 context, a five-step input window, one-step forecast, CPU execution, and internal learned-graph `Top-5`.
3. `UpstreamAlignedGDN.forward` and final graph extraction both compute the full embedding cosine matrix and call `torch.topk(..., k=5)` without masking the diagonal first. Self similarity can therefore consume one internal neighbor slot.
4. `train_upstream_aligned_seed_v1` later projects selected graph edges onto the exact 144 source-target universe. Because source and target role sets are disjoint, no exported self-pair survives, but post-projection removal cannot restore the consumed internal slot.
5. `project_seed_record_to_universe_v1` and `aggregate_and_rank_gdn_candidates_v1` already enforce exact universe membership, all three seeds, common hyperparameters, complete similarity coverage, fail-closed seed completion, frequency-first ranking, deterministic ties, and no padding.
6. Candidate Top-10/20/40 are prefixes of one ranking. Top-20 was preregistered before test1 but its scientific optimality was not established.
7. Downstream relation fit/confirmation is arm-blind and normal-only: train1/train2 are fit roles and train3 is the confirmation role. `test1` remains development-only and is outside EXP-01 selection.
8. A learned GDN edge is candidate/predictive graph evidence. It is not a confirmed delayed response, physical truth, cause, root cause, or attention explanation.

## 3. Required V2 implementation boundary

Do not behaviorally modify the frozen V1 backend or overwrite its artifacts. Add a separately versioned V2 EXP-01 path.

Recommended new modules:

- `src/paperworks/gdn/upstream_candidate_backend_v2.py`
  - `GDNNeighborPolicyV2`
  - `UpstreamGDNTrainingConfigV2`
  - `build_self_excluded_neighbor_graph_v2`
  - `train_upstream_aligned_seed_v2`
  - `evaluate_frozen_graph_mask_intervention_v2`
- `src/paperworks/validation_v2/exp01_gdn_v1.py`
  - `EXP01PreregistrationV1`
  - `EXP01ArmV1`
  - `EXP01SeedRunV1`
  - `EXP01SplitRunV1`
  - `EXP01CandidateStabilityV1`
  - `EXP01FunctionalMaskResultV1`
  - `EXP01ResultV1`
  - `build_exp01_preregistration_v1`
  - `validate_exp01_authority_v1`
  - `compute_seed_stability_v1`
  - `compute_split_stability_v1`
  - `join_arm_blind_confirmation_v1`
  - `evaluate_graph_guided_inclusion_rule_v1`
- `scripts/run_validation_v2_exp01.py`
  - one tracked entrypoint after code/config/preregistration freeze
  - one experiment namespace; no concurrent writers
  - explicit dry validation before any authorized normal-value read

The corrected neighbor rule is exact:

```text
cosine = embedding cosine matrix
cosine[target, target] = -infinity for every target
neighbors[target] = stable Top-5 largest remaining cosine values
assert target not in neighbors[target]
assert exactly 5 distinct neighbors when node_count > 5
```

This diagonal mask must be applied identically in the training forward path and post-checkpoint extraction. The 144-pair role projection remains a separate, subsequent output boundary. A broader process-role mask must not be silently introduced as part of this correction because that would change the full-context upstream-aligned model beyond the isolated self-neighbor ablation.

## 4. Frozen-versus-corrected ablation

The ablation has two GDN arms plus the existing non-GDN candidate comparators:

| Arm | Meaning | Scientific use |
|---|---|---|
| `META_REFERENCE` | deterministic metadata candidate ranking | comparator |
| `STAT_REFERENCE` | normal first-difference lag-association ranking | comparator |
| `GDN_FROZEN_SELF_ELIGIBLE` | exact V1 internal Top-5 convention replayed into a new V2 result namespace | ablation/reference only |
| `GDN_CORRECTED_SELF_EXCLUDED` | same upstream-aligned architecture with diagonal set to `-inf` before every internal Top-5 | candidate for V2 primary discovery path |

For the two GDN arms, hold constant the input identities and ordering, windowing, optimizer, architecture, seed set, validation policy, checkpoint policy, number of epochs, early stopping, device, and downstream rank aggregation. The only permitted scientific difference is the neighbor policy. Both must be trained from scratch with the same seed because graph construction participates in training.

Primary corrected analysis uses the combined train1/train2 file-local segments. Split stability additionally repeats the corrected arm on train1-only and train2-only views using the same three seeds and unchanged hyperparameters. Windows must never cross a file boundary.

## 5. Preregistered metrics

### 5.1 Authority and completion gates

- exact upstream repository/commit and approved dependency port verified;
- exact V2 protocol and EXP-01 preregistration hashes bound;
- exact data/split/feature-order identities bound without publishing private paths or values;
- all three seeds complete for every required GDN arm/view;
- failed/nonfinite seed fails the corresponding arm closed;
- no test1/test2/held-out/attack-label input;
- no per-seed hyperparameter variation;
- no candidate padding or result-driven reranking.

### 5.2 Self-neighbor correction

- per seed, count of self identities in the frozen 37×Top-5 graph;
- per seed, count of self identities in corrected graph, required to be zero;
- exact Top-20 overlap and Jaccard between frozen and corrected rankings;
- count of corrected candidates added/removed relative to frozen behavior.

These are mechanics, not evidence that corrected GDN is scientifically better.

### 5.3 Seed stability

For the corrected combined train1/train2 arm:

- pairwise Top-K intersection count and Jaccard for seeds 11/23, 11/37, and 23/37 at K=10,20,40;
- selected-seed frequency distribution (`1/3`, `2/3`, `3/3`);
- aggregate ranking Top-K identities and shortfall;
- a pair is `seed_stable` iff selected by at least two of three seeds.

No stochastic reruns beyond the frozen seeds may be added after seeing results.

### 5.4 Split stability

- aggregate corrected Top-K intersection count and Jaccard between train1-only and train2-only rankings at K=10,20,40;
- membership of combined-ranking candidates in each split-specific Top-K;
- a pair is `split_stable_at_20` iff it belongs to both train1-only and train2-only aggregate Top-20 sets.

Split-specific runs are sensitivity analyses. They do not replace the preregistered combined train1/train2 primary ranking.

### 5.5 Unique candidate provenance

At each K, record exact pair identity and arm membership. A corrected GDN pair is `gdn_unique_at_k` iff it is in corrected GDN Top-K and absent from META Top-K and STAT Top-K. Uniqueness is set provenance only and is not utility.

### 5.6 Confirmed-relation yield

Every union pair receives the same arm-blind normal relation fit and train3 confirmation. Provenance is joined only after outcomes are frozen.

- primary arm yield at K=20: distinct arm Top-20 pairs with at least one confirmed directional relation divided by 20;
- unique confirmed count: `gdn_unique_at_20` pairs with at least one confirmed relation;
- stable unique confirmed count: unique confirmed pairs that are both `seed_stable` and `split_stable_at_20`;
- directional confirmation counts remain secondary and may not substitute for distinct-pair yield;
- K=10/40 sensitivity uses the actual unpadded prefix count as denominator and reports nominal budget plus shortfall.

No attack label or test1 development outcome may decide relation confirmation or candidate inclusion.

### 5.7 Functional masking analysis

After arm-blind train3 confirmation is frozen, freeze the primary intervention set as the intersection of corrected GDN Top-20, GDN-unique, seed-stable, split-stable-at-20, and train3-confirmed pairs. Freeze the corrected best checkpoint per combined-view seed. On train4 `NORMAL_SANITY` windows only, evaluate the same checkpoint under:

1. intact corrected learned graph;
2. the frozen primary stable+unique+split-stable+train3-confirmed set removed without refill.

Report baseline MSE, masked MSE, absolute delta, and relative delta per seed plus their median. This is a bounded functional-dependence diagnostic. It does not prove causality, physical relation, anomaly-detection utility, or feature importance. If the primary intersection is empty, the primary diagnostic is `NOT_APPLICABLE`, not zero benefit. A broader stable GDN-unique mask may be reported only as a clearly secondary sensitivity and cannot satisfy the inclusion rule.

An effect is `detectably_positive` for a seed only when the masked MSE increase exceeds `max(1e-12, 1e-9 * abs(baseline_mse))`; this tolerance is a numerical replay guard, not an effect-size claim.

### 5.8 Top-K sensitivity

K is frozen to 20 for the primary result. K=10 and K=40 are sensitivity views from the same ranking. Report candidate count/shortfall, arm overlap, seed/split stability, unique count, confirmed yield, and stable unique confirmed count. Do not select a different K from these results.

## 6. Inclusion and demotion rule

`Graph-Guided` may remain in the primary VALIDATION V2 discovery path only if all of the following are true:

1. every authority, custody, completion, privacy, and integrity gate passes;
2. corrected graphs contain zero self neighbors and forward/extraction graph identities match;
3. at least one corrected Top-20 pair is simultaneously GDN-unique, seed-stable, split-stable, and train3-confirmed by the common arm-blind relation protocol;
4. masking the frozen stable+unique+split-stable+train3-confirmed primary set produces a detectably positive train4 normal-sanity MSE increase in at least two of three seeds and a positive median delta;
5. no prohibited data, post-result K change, reranking, seed addition, or silent fallback occurred.

Disposition:

- all five conditions pass: `RETAIN_GRAPH_GUIDED_CONDITIONALLY`, limited to normal-data candidate guidance;
- valid complete experiment but condition 3 or 4 fails: `DEMOTE_GDN_TO_ABLATION`, and primary V2 candidate discovery uses META+STAT;
- execution/authority/dependency failure: `GDN_CONTRIBUTION_UNRESOLVED_FAIL_CLOSED`; GDN is not retained as a primary claim and the failure is not reported as negative scientific evidence;
- no outcome can authorize causal, root-cause, physical-truth, attention-explanation, or detector-performance wording.

The rule is intentionally based on at least one stable, unique, confirmed, functionally used pair rather than a post-hoc optimized aggregate threshold. It asks whether GDN adds any defensible normal-data candidate information beyond META/STAT; it does not claim GDN is generally superior.

## 7. Candidate implementation tests

Recommended new tests:

- `tests/test_validation_v2_exp01_gdn_backend_v2.py`
  - diagonal is masked before Top-5;
  - no self neighbor and exactly five distinct neighbors;
  - forward graph equals extraction graph;
  - deterministic tie behavior is explicitly fixed;
  - V1 function/source identity is unchanged;
  - only neighbor policy differs in ablation config;
  - optional dependencies fail through project-owned error.
- `tests/test_validation_v2_exp01_gdn_contract_v1.py`
  - exact seed set and fail-closed incomplete seed;
  - exact 144-pair projection and no padding;
  - train1/train2 candidate-learning role only;
  - train3 confirmation role only;
  - train4 masking sanity only;
  - test1/test2/held-out/labels rejected before I/O;
  - exact Top-K prefix and shortfall accounting;
  - seed/split Jaccard and stable-pair predicates;
  - late provenance join and arm-blind confirmation;
  - functional mask set frozen before train4 evaluation;
  - inclusion/demotion/unknown branches;
  - self-hash, schema, stale/wrong-authority, mutation, privacy, and Pilot V1 preservation checks.
- independent QA must replay arithmetic from synthetic records without invoking the tracked EXP-01 runner.

Existing reusable source/tests:

- `src/paperworks/gdn/upstream_candidate_backend_v1.py`
  - `UpstreamGDNTrainingConfigV1`
  - `assert_identical_seed_hyperparameters_v1`
  - `authorize_gdn_data_request_v1`
  - `_segment_windows_v1` (behavior to preserve through a public V2 adapter, not private cross-module import)
  - `train_upstream_aligned_seed_v1` (frozen reference arm only)
- `src/paperworks/candidates/gdn_candidate_discovery_v1.py`
  - `GDNSeedGraphRecordV1`
  - `project_seed_record_to_universe_v1`
  - `aggregate_and_rank_gdn_candidates_v1`
- `src/paperworks/v6/candidate_discovery_protocol_v1.py`
  - `derive_candidate_budget_views_v1`
  - `rank_gdn_candidates_v1`
- `src/paperworks/profiling/task039d2_audit_accounting_v1.py`
  - existing confirmed-yield arithmetic is reference evidence; V2 should expose a separately versioned, arm-blind adapter rather than importing frozen task orchestration wholesale.
- `tests/test_task039c_gdn_remediation_execution.py`
- `tests/test_task039c_gdn_candidates.py`
- `tests/test_task039c_gdn_fidelity.py`
- `tests/test_task039d2_audit_accounting.py`
- `tests/test_validation_v2_protocol_v1.py`

## 8. Required artifacts and freeze order

```text
implementation + tests
→ independent implementation QA
→ EXP01 preregistration finalized and hashed
→ code/config/dependency/data identities frozen
→ Commit A (before scientific outcome)
→ authorized normal-only execution in dedicated namespace
→ raw per-seed/per-split receipts frozen
→ arm-blind confirmation outcomes frozen
→ provenance join + preregistered analysis
→ independent result-integrity audit
→ sanitized result report
→ Commit B
```

Required versioned artifacts include the preregistration, backend/fidelity receipt, per-arm config, per-seed graph receipt, split-stability receipt, candidate provenance, confirmation binding, masking intervention receipt, result, integrity audit, privacy audit, and inclusion-decision receipt. Private values/paths/checkpoints remain outside Git; public artifacts contain identities, hashes, aggregate counts, statuses, and conservative interpretations only.

## 9. Implementation and independent QA status

The preparation implementation now includes a V2-only self-excluded backend,
typed preregistration/authorization/input/seed/bundle/analysis/evidence contracts,
seven embedded closed schemas, fail-closed lineage replay, the functional masking
path, and a three-seed authority-gated runner. The independent adversarial QA
suite passed 18/18 cases, including malformed schema, forged lineage, stale
authority, duplicate, seed-cardinality, strict-Boolean, Top-20, and V1-preservation
checks. This is implementation evidence only; no scientific input was read and no
scientific result exists.

The remaining pre-execution blockers are:

1. The exact approved Torch/PyG dependency environment must be re-verified for V2.
2. A public V2 data-authority receipt must bind the authorized train1/train2,
   train3, and train4 identities before any private scientific read.
3. The frozen META/STAT comparator identities must be replayed or separately
   versioned without using scientific scores as a cross-arm global rank.
4. The final typed preregistration and implementation identities must be frozen
   in Commit A before outcomes.
5. Normal scientific assets are required for execution and remain outside the
   scope of this preparation implementation.

None of these blockers authorizes test1, test2, held-out, labels, provider calls, or a change to PILOT V1.
