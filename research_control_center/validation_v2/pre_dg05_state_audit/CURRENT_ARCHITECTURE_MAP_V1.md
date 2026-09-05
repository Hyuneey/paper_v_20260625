# Current Architecture Map V1

Audited authority: `validation-v2@a90d0e669b4a5ab87177c9188695345faf81e2ea`. This is a static public-safe map, not an executable authority.

## Scientific pipeline

| Stage | Purpose | Input → output | Split | Main implementation | Stochastic / LLM | Frozen state |
|---|---|---|---|---|---|---|
| META prior | Domain-reviewed candidate identity | Frozen reviewed metadata → directed pair identities | no feature values | `paperworks.candidates.metadata_candidate_discovery_v1` | no / no | frozen prior; lost private input must not be reconstructed |
| STAT | Statistical candidate/evidence view | projected normal features → lagged association/rank or split-pure aggregate | train1/train2 normal | `paperworks.candidates.statistical_candidate_discovery_v1` | no / no | algorithm and candidate budget frozen |
| Candidate union | Primary admission | META ∪ STAT Top-K → directed cohort | normal-only | cross-version preparation scripts/authorities | no / no | HAI23/22/21 cohorts frozen |
| Structural temporal evidence | Semantic direction/horizon evidence | source events → 20 tuple rows/pair | train1 provider; train2 hidden | `validation_v2.xver_structural_v1`, EXP-03B evidence modules | no / no | SCI-01 frozen |
| GDN GLOBAL5 | Learned-graph supporting evidence | three fixed-seed checkpoints → five horizon rows | split-pure train1/train2 | `exp01c_backend_v1`, `xver_gdn_execution_v1`, `xver_gdn_roles_v1` | yes / no | normal-only evidence frozen |
| GDN EVENT10 | Auxiliary corroboration | SCI-01 events ∩ purged validation → direction × horizon states | train1/train2 only | `xver_gdn_roles_v1` | yes / no | frozen and isolated; no provider/verifier use |
| T0 | Deterministic semantic induction | frozen train1 structural fields → RULE_SET/NO_RULE | train1 | `exp03b_semantic_v2.t0` | no / no | once/pair; portfolios frozen |
| T2 | Verifier-guided semantic induction | structural + STAT + GLOBAL5 → semantic proposal | train1 + bounded train2 feedback | `exp03b_*_v2`, `xver_prompt_v1`, `xver_provider_execution_v1` | yes / yes | historical provider executions complete; no DG-05 calls |
| Hidden verifier | Admit or repair semantic proposal | proposal + train2 structural authority → admitted decision/issues | train2 | `exp03b_hidden_v2`, `exp03b_admission_verifier` | no / no | thresholds/issues frozen |
| Semantic confirmation | Development normal reference | admitted semantic set → confirmed set | HAI23/22 train3; HAI21 Block A | `exp01_relation_confirmation_v2`, `xver_confirmation_v1` | no / no | frozen; not causal truth |
| SCI-02B | Bind execution numerics | confirmed semantics + train1/train2 statistics → numeric roles | normal-only | `exp03b_binder_v2`, `exp03b_numeric_v1`, `xver_numeric_closure_v1` | no / no | `n7-q0.90-s2-f0.05`; no 37-grid reselection |
| Formal V4 | Executable rule authority | semantic + numeric + provenance → Rule descriptors/runtime authority | normal-only construction | `formal_v4_authority_v1`, `runtime_v1` | no / no | frozen portfolios |
| Normal guard | Fail-closed normal-operation guard | executable Rules + guard normal split → retained portfolio | train4/Block B | `exp03b_evaluation`, `exp03b_guard_v1` | no / no | one-way; no feedback |
| PCA/IF | Detector comparators | frozen detector models + feature projection → alarm mask | future held-out feature-only | `pca_spe_v2`, `isolation_forest_v1`, `xver_detector_v1` | model-fit historical / no LLM | method-specific subauthorities frozen |
| Rule runtime | LLM-free relational evaluation | frozen descriptor/numeric authority + rows → PASS/FAIL/ABSTAIN mask/trace | future held-out feature-only | `runtime_v1`, `dg05_execution_closure_v1._rule` | no / no | frozen, but census handoff has audit findings |
| Fusion | Bounded detector/Rule comparison | detector alarm OR qualifying same-row Rule FAIL sources | future held-out feature-only | `dg05_execution_closure_v1.fuse_dense_masks_v1` | no / no | no redesign |
| Custody/eligibility | Prediction-before-label separation | projections → predictions/freezes → isolated scenarios/denominator | future two-phase | `multipanel_custody_v1`, `dg05_label_custodian_v1`, `dg05_execution_closure_v1` | no / no | contracts frozen; production orchestration gap |
| Metrics | Version-specific result surface | prediction + scenario/denominator + normal burden → 228 identifiers | Phase B only | `dg05_metric_surface_*`, `multipanel_etapr_v2` | no / no | synthetic surface closure frozen; production bindings incomplete |

## Intended DG-05 V3 transition trace

| Transition | Intended checked authority | Current code | Audit status |
|---|---|---|---|
| V3 approval → preaccess | V3 manifest `7ea1e4…`, closure `5b3f0a…`, predecessor bundle | `dg05_executable_v3.initialize_dg05_executable_v3_preaccess` | Replays public artifacts; current manifest still requires user reapproval. |
| Preaccess → raw custody | exact V3 approval hash + attack census | no committed production V3 orchestrator found | `P0`: no bound transition. |
| Custody → positive projection | physical-file authority + allowlist + production adapter | `dg05_execution_closure_v1.project_attack_feature_file_v1` | Primitive exists; accepts nondecreasing timestamps and preserves duplicates. |
| Projection → detector/Rule/Fusion dispatch | method dispatch, detector subauthority, Rule runtime, Fusion | `DG05ProductionExecutorV1`, `execute_prediction_cell_v1` | Requires historical typed `DG05ExecutableAuthorityManifestV1`, not V3 preaccess state. |
| Cells → manifest/freeze | expected cell census, terminal receipts, source authorities | `build_global_prediction_manifest_v1`, `freeze_global_predictions_v1` | Primitive exists; V3 approval continuity not wired. |
| Freeze → lease | exact frozen global manifest/state | `issue_label_lease_v3` and state machine | Historical typed state chain only. |
| Lease → isolated custodian | custodian code hash, resource allowlist, prediction-root denial | `scripts/run_dg05_label_custodian_v1.py` → `consume_and_extract_v1` | CLI exists; no production V3 launcher/binding found. |
| Scenario → P1/denominator | full process scope `0e4fb08…`, P1 V3 `f688fae…` | scenario/denominator builders in `dg05_execution_closure_v1` | Plural closed intervals are valid upstream. |
| Denominator → primitive | predictions, scenarios, timestamps, normal burden | `build_metric_primitives_from_frozen_execution_v1` | Narrows scenarios to one interval and trusts supplied normal-burden components/hashes. |
| Primitive → 228 results | metric contract `48f72f…`, expected surface `d96a62…` | `build_complete_metric_surface_v1` | Arithmetic/surface sets close on synthetic primitives. |
| Results → independent verifier | result/primitive/contract paths | `verify_complete_metric_surface_from_paths_v1` | Recomputes arithmetic but not full source provenance. |
| Verifier → completeness/RCC | oracle `a9c148…`, closure `5b3f0a…` | `close_complete_metric_results_v1` | Identifier completeness yes; production nested integrity not established. |

## Data and authority flow

The scientific construction path is normal-only and version-specific. Runtime is LLM-free. GDN is absent from DG-05 runtime: it has already served construction. During future Phase A, only timestamps and approved feature allowlists may enter prediction. During Phase B, the fresh custodian must be unable to access prediction roots; scenario and eligibility authority must be method-blind. No implementation inspected provided a sanctioned route for label/scenario values to affect Phase-A predictions, but the missing production V3 orchestrator prevents end-to-end enforcement proof.

## 228-surface meaning

The frozen census is 88 HAI23 + 70 HAI22 + 70 HAI21 = 228 identifiers. It comprises 23 panel/method combinations across eight base surface families (184), 17 Rule-capable runtime-census surfaces, 24 paired-contrast surfaces, and three recovery surfaces. The builder and verifier declaration sets are exact matches with no missing identifiers. It is not 228 independent experiments, not 228 scalar estimates, and not proof that every source datum is independently replayed.

## Current architecture boundaries

- `src/paperworks/contracts/` remains the repository’s canonical v6 contract family, but the current Formal V4/DG-05 runtime actually routes through `src/paperworks/validation_v2/`. No `validation_v2` import of legacy `dsl`, `verification`, or `runtime` packages was found.
- `dg05_execution_closure_v1.py` has mixed ownership: predecessor manifest/result APIs and current prediction/custody primitives coexist. The version suffix alone does not make it obsolete.
- `dg05_connected_rehearsal_v3.py` is synthetic-only and instantiates a synthetic predecessor/V2-style manifest; it does not close exact V3 approval continuity.
- The current independent metric oracle is independent arithmetic, not a full independent source-to-result oracle.

## Thesis architecture interpretation

Primary: candidate governance, semantic induction, verification, deterministic binding, Formal V4 execution. Supporting: GDN learned-graph evidence and structural explanation. Secondary: PCA/IF/Fusion comparisons and metric/custody infrastructure. The contribution is not a new detector, a causal graph, or a runtime LLM.
