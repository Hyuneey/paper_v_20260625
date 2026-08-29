# RCC-000 Agent A — Git / Source Lineage Evidence

## Scope and safety

- Role: Git / Source Lineage Auditor.
- Method: Git metadata, committed public documents, `git show`, `git ls-tree`, and static source-symbol inspection only.
- Scientific executions: `0`.
- Test1/test2 data accesses: `0`.
- Checkout, merge, tag mutation, push, and branch mutation: `0`.
- This file is the only file created by Agent A. Worktree paths are deliberately omitted; only public ref names, commit identities, and repository-relative paths are recorded.

## Commands and direct evidence

Executed read-only commands included:

- `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, `git remote -v`
- `git branch --all`, `git tag --list`, `git for-each-ref`
- `git log --all --decorate --oneline --graph`, targeted `git log --all -- <path>`
- `git worktree list --porcelain`
- `git show <ref>:<path>`, `git ls-tree -r <ref>`, `git merge-base --is-ancestor`

The repository has no `.gitmodules` entry at either the current checkout or the audited canonical remote tree. The local Git environment contains 159 local branch refs, 119 `origin` remote-tracking refs, two tags, and 143 registered worktrees (122 branch worktrees and 21 detached worktrees). The large worktree set is historical operational state; its filesystem locators are not reproduced here. Its cleanup/retention status was not inferred.

## Current checkout versus canonical remote

| Item | Ref / commit | Evidence-based disposition |
|---|---|---|
| Current checkout | `task-039c-gdn` / `c0efdb6218385ec326be1a929371242314e63cb6` | Historical blocked GDN-arm checkout; not the current research source authority. It has 1,253 tracked tree entries and multiple unrelated untracked workspace directories. |
| Canonical remote checkpoint | `origin/research-v6-thesis-checkpoint` / `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` | Audited remote checkpoint. It has 3,021 tracked tree entries and contains the complete later HAI P1 implementation, frozen INNER results, OUTER blocker, professor package, and post-push audit. |
| Thesis draft overlay | `origin/task-039e3-r2r-thesis-draft-scaffold-v1` / `ebc5a57bfdb7d8266f96f2990338effb9d0a2743` | One documentation commit after the canonical checkpoint; 3,037 tree entries. Contains `docs/thesis_draft_v1/`. It is not a newer scientific result authority. |

Ancestry checks passed:

- `origin/main` → canonical remote checkpoint.
- `task-039c-integration` → canonical remote checkpoint.
- D0, D1, D2 V1, D2 V2 result/integrity commits → canonical remote checkpoint.
- OUTER blocker freeze → canonical remote checkpoint.
- professor submission commit → canonical remote checkpoint.
- canonical remote checkpoint → thesis draft overlay.

The current checkout differs materially from the canonical remote (`1,768` additional tracked paths in the canonical tree, net tree comparison spanning 1,781 changed files). Absence from the current checkout must not be interpreted as absence from the project.

## Important refs and lineage roles

| Category | Ref / commit | Role and evidence |
|---|---|---|
| A. Current scientific implementation | `origin/research-v6-thesis-checkpoint` / `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` | Complete audited public source/result checkpoint; recommended working tree source candidate. |
| B. Candidate cohort | `task-039c-integration` / `9ac4578603b81385dc9592cd5db5076d83a3fb66` | Three-arm candidate integration and frozen 47-pair cohort lineage. |
| B. Confirmed relations | `task-039d2-final-audit` / `e655e161c82715638c6c6d398d52dc0babbec7c0` | Train3 confirmation audit; 42 directed relations carried forward. |
| B. Construction configuration | `task-039e2-final-audit` and `origin/main` / `11a5f04a0422049a099020f06c59ec23bc72d130` | T0/T1/T1-B/T2 execution-configuration audit point. `origin/main` stops here and is stale for later utility/results. |
| B. COMMON-42 numeric authority | `task-039e3-r2r-utility-normal-only-authority-v1-materialized-independent-audit` / `e971c8c8543f49b31aba2a57cf60257d190b76d5` | Materialized normal-only authority audit. |
| B. COMMON-42 protocol closure | `task-039e3-r2r-utility-protocol-v4-normal-only-authority-rebind-closure` / `78b26921d8377b3a6d6b401ca3444c56fb73d7fe` | Audited numeric authority rebound to the utility protocol. |
| C. D1 result integrity | `task-039e3-r2r-utility-inner-d1-result-integrity-audit-v1` / `91a92fb3ca44d0e34c310b35ab8b6ec88c95be05` | Integrity-audited D1 lineage; report freeze is `fd54c5cab69927e91d268f344c54f6614f28021f`. |
| C. D0 result integrity | `task-039e3-r2r-utility-inner-d0-result-integrity-audit-report-hash-remediation-r1` / `1c2f9a6272ee711b70b44ed79b9210af1026d3af` | D0 integrity plus report-provenance closure; scientific audit report freeze is `a1ff1929a86e95675431c2c32ace01efa2696a80`. |
| C. D2 V1 result integrity | `task-039e3-r2r-utility-inner-d2-result-integrity-audit-v1` / `f4367ac5b77a28088fab834018b170c8295e66c1` | D2 V1 integrity-audited lineage; report freeze is `f7ae8f10e8e69e631c43184d6ea9cd3604829a9c`. |
| C/D. D2 V2 result freeze | commit `55d41c543e110a9a6f0f5e2e2671857dba938aaa` | First real D2 V2 INNER result freeze. |
| D. D2 V2 integrity completion | report commit `228f1e94baed531ae8d9503cb3c5ec0a3aa47f6b`; lineage tip `9287d5f63dc8df2811c53429b1f141634dd971bc` | Final integrity-completion artifact/report freeze and subsequent continuity. Both are ancestors of the canonical remote checkpoint. |
| E. INNER disposition | `task-039e3-r2r-utility-inner-d2-v1-v2-scientific-disposition-v1` / `634231bb91c57df39eded6d869abe6a2853ae1d1` | Frozen conclusion: rule signal present, current fusion utility unsupported. |
| E. OUTER preregistration | `task-039e3-r2r-utility-outer-d0-d1-d2v1-preregistration-authorization-v1` / `65a9439ff4b16960368c21c9ef96da4394cecee7` | One-shot D0/D1/D2 V1 OUTER preregistration/authorization lineage. |
| E. OUTER consumed blocker | blocker freeze `c2670f0a49fb704799e62648805188983fb6ef83`; continuity `70811efe44246796797299d58125720298e3a380` | Execution stopped at feature custody before feature-byte or label access; no OUTER scientific result. |
| F. Professor first-results package | `task-039e3-r2r-professor-first-results-report-next-plan-v1` / `3f1775745512e5ed1872d727376874248292a81a` | First-results synthesis and handoff. |
| F. Professor submission | `task-039e3-r2r-professor-submission-package-final-qa-v1` / `87033702d0c16abaf141c03983098f69e6a8cb16` | Professor-facing final QA package. |
| G. First-results tag | `thesis-v1-first-results` / peeled commit `5aa7c61ee37fb232c9b487e448ddbd30e3628872` | Professor-ready, path-hygiene-complete pre-audit checkpoint. |
| G. Post-push checkpoint | `origin/research-v6-thesis-checkpoint`; tag `thesis-v1-post-push-audit` / `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` | Remote-wide architecture/result/reproducibility/claim audit. |
| H. Thesis draft | `origin/task-039e3-r2r-thesis-draft-scaffold-v1` / `ebc5a57bfdb7d8266f96f2990338effb9d0a2743` | Documentation-only thesis scaffold, one descendant commit after the checkpoint. |
| I. ARGOS legacy/reference | canonical tree `experiments/argos_reproduction/*`; latest tracked lineage includes `b13f17d8235c1b833a38a596c4ab31cfa7212ee2` | Frozen historical reference track (TASK-022–038), not current HAI P1 scientific authority. |
| J. Superseded implementation | current `task-039c-gdn` checkout and canonical legacy `src/paperworks/dsl/*`, `verification/*`, `runtime/*`, historical `e2e/*` | GDN blocked branch was superseded by port-closure/integration; old DSL/runtime/e2e are compatibility/reference only. |

Only one merge is present on the first-parent path after `origin/main`: `37023d38a413c2b2fc74ed66fb65d2ff4e7b3da9`, which merges the TASK-039E2 final-audit lineage. Later task results are preserved as a predominantly linear lineage rather than a sequence of branch merges. No squash equivalence was inferred without explicit evidence.

## Source authority map

Unless otherwise stated, the source ref is `origin/research-v6-thesis-checkpoint` at `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`. This is the public tree that contains all representative paths below.

| Component | One-line role | Representative path / symbol | Status | Used in frozen result? | Audited? | Major public artifact | Deep-review target |
|---|---|---|---|---|---|---|---|
| DATA_PROVENANCE | Pins HAI source and public-safe provenance. | `src/paperworks/data/hai_provenance_v1.py` / `HAIRepositorySnapshotV1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | HAI provenance reports/manifests | official-source and byte-identity binding |
| SPLIT_GOVERNANCE | Enforces permitted data roles and purge boundaries. | `src/paperworks/data/splits_v2.py` / `assert_operation_permitted_v2` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | dataset/split manifests in `docs/task_reports/` | role permissions and purge math |
| VARIABLE_ROLE_UNIVERSE | Builds the masked source-target universe. | `src/paperworks/candidates/universe.py` / `build_candidate_universe` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039C0_*` | source/target compatibility masks |
| META_DISCOVERY | Produces metadata-only candidate evidence. | `src/paperworks/candidates/metadata_candidate_discovery_v1.py` / `FrozenUniverseBindingV1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039C_META_RESULT.json` | zero-feature-value guarantee |
| STAT_DISCOVERY | Produces lagged statistical candidate evidence. | `src/paperworks/candidates/statistical_candidate_discovery_v1.py` / `PairStatisticalEvidenceV1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039C_STAT_RESULT.json` | file-local horizons and ranking |
| GDN_DISCOVERY | Supplies upstream-aligned graph-ranking candidate evidence. | `src/paperworks/gdn/upstream_candidate_backend_v1.py`; `src/paperworks/candidates/gdn_candidate_discovery_v1.py` / `aggregate_and_rank_gdn_candidates_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039C_GDN_RESULT.json` | upstream fidelity and dependency boundary |
| CANDIDATE_UNION | Forms unscored provenance-preserving union. | `src/paperworks/candidates/candidate_integration_v1.py` / `build_task039c_integration_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039C_CANDIDATE_PROFILING_COHORT.json` | de-duplication and arm provenance |
| RELATION_PROFILING | Fits normal delayed-response relations and confirms on train3. | `src/paperworks/profiling/task039d1_fit_v1.py` / `evaluate_arm_blind_fit_v1`; `task039d2_confirmation_v1.py` / `apply_exact_confirmation_gate_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039D2_RESULT.json` | event isolation and one-way confirmation |
| NUMERIC_AUTHORITY | Separates deterministic calibrated values from LLM proposals. | `src/paperworks/v6/task039e3_r2r_utility_normal_only_authority_v1.py` / `build_common42_authority_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZATION.json` | private registry bootstrap and exact bindings |
| EVIDENCE_PACK | Binds confirmed relations to normal evidence. | `src/paperworks/v6/normal_evidence_v1.py` / `NormalRelationEvidenceV1`; `contracts/normal_evidence_binding_v1.py` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039E1_CONSTRUCTION_EVIDENCE_MANIFEST.json` | public/private evidence split |
| RULE_DSL | Canonical typed Rule v1 contract. | `src/paperworks/contracts/rule_v1.py` / `RuleV1` family | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | TASK-039E0 validity/protocol bundle | schema invariants and delayed-response subset |
| T0_TEMPLATE | Deterministic template construction arm. | `src/paperworks/v6/task039e3_orchestration_v1.py` / `run_t0_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | TASK-039E3 construction results | deterministic equivalence to numeric authority |
| T1_ONE_SHOT | Bounded one-shot provider-assisted arm. | same / `run_t1_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | TASK-039E3 construction results | request schema and provider custody |
| T1B_REPEAT | Budget-matched independent-generation arm. | same / `run_t1b_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | TASK-039E3 construction results | independence and selection policy |
| T2_AGENTIC_FEEDBACK | Bounded verifier-feedback construction arm. | same / `run_t2_v1`; `task039e0_rule_construction_protocol_v1.py` / `T2DeterministicControllerPolicyV1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | TASK-039E3 construction results | feedback budget and revise/retrieve boundaries |
| DETERMINISTIC_VERIFIER | Enforces structure/evidence/parameter/operation/claim checks. | `src/paperworks/contracts/verifier_v1.py` / `RuleVerificationOutcomeV1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | verifier result artifacts | stage ordering and fail-closed issues |
| COMMON42_FREEZE | Freezes the executable 42-rule utility portfolio. | `src/paperworks/v6/task039e3_r2r_utility_protocol_v4.py` / `build_common42_public_authority_v4` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039E3_R2R_UTILITY_COMMON42_AUTHORITY_CHECK.json` | source resolution and exact cardinality |
| RULE_RUNTIME | Executes verified rules without an LLM. | `src/paperworks/v6/task039e3_r2r_utility_evaluator_rule_engine_v1.py` / `execute_rule_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | D1 RulePrediction artifact | window semantics and abstention |
| SATISFACTION_TRACE | Records evaluated temporal predicates. | `src/paperworks/contracts/runtime_v1.py` / `RuntimeTraceV1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | D1 execution evidence | trace completeness and privacy |
| EXPLANATION_RENDERER | Renders trace-grounded non-causal explanation records. | `src/paperworks/contracts/explanation_v1.py` / `render_delayed_response_explanation` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | professor explanation examples | claim boundary and user usefulness |
| D0_PCA_SPE | Reference normal-only PCA-SPE detector. | `src/paperworks/v6/task039e3_r2r_d0_inner_execution_v1.py` / `execute_authorized_d0_inner_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | D0 prediction, metrics, integrity reports | private model/threshold bootstrap |
| D1_RULE_ONLY | COMMON-42 rule-only INNER evaluator. | `src/paperworks/v6/task039e3_r2r_utility_inner_d1_execution_v1.py` / `execute_authorized_inner_d1_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | D1 prediction, metrics, integrity reports | high FAR and source-event accounting |
| D2_V1 | Same-second two-source detector/rule fusion. | `src/paperworks/v6/task039e3_r2r_d2_inner_execution_v1.py` / `fuse_point_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | D2 V1 prediction, metrics, integrity reports | preservation of D0 and corroboration timing |
| D2_V2 | Native-horizon evidence-token fusion. | `src/paperworks/v6/task039e3_r2r_d2_v2_inner_execution_v1.py` / `fuse_native_horizon_timeline_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | D2 V2 prediction, metrics, completion authority | causal horizon expiry and false-alarm expansion |
| EPISODE_CONSTRUCTION | Builds maximal contiguous alarm episodes. | `src/paperworks/v6/task039e3_r2r_utility_evaluator_metrics_v1.py` / `form_alarm_episodes_v1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | D0/D1/D2 metric oracles | file locality and boundary semantics |
| ATTACK_EVENT_RECALL | Builds attack events and overlap recall. | same / `derive_attack_events_v1`, bound metric functions | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | metric and integrity-oracle artifacts | label ordering and overlap policy |
| NORMAL_FAR | Calculates normal false-alarm episodes/hour. | same / `BoundMetricV1` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | metric and integrity-oracle artifacts | exposure denominator and episode counts |
| RESULT_INTEGRITY | Independently replays frozen result/report contracts. | `scripts/audit_task039e3_r2r_d0_result_integrity_v1.py`; D1/D2/V2 audit scripts; `scripts/remediate_task039e3_r2r_d2_v2_r5_report_render_r1.py` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | `TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_COMPLETION_V1.json` and arm-specific receipts | task-specific audit harness versus reusable integrity core |
| OUTER_EVALUATION | Preregistered held-out three-arm execution path. | `src/paperworks/v6/task039e3_r2r_outer_d0_d1_d2v1_execution_recovery_v1.py` / `RecoveryAttemptBoundaryV1` | BLOCKED | no | partial | `TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_EXECUTION_RECOVERY_V1_BLOCKER.json` | portable custody before any future reauthorization |
| REPRODUCIBILITY | Preserves source, environment, public identities, and private bootstrap rules. | `docs/professor_first_results_v1/08_REPRODUCIBILITY_AND_CODE_STATUS.md`; `docs/post_push_checkpoint_v1/07_REPRODUCIBILITY_ASSESSMENT.md` | PARTIAL | yes | partial | preservation manifest and path-disposition manifest | fresh-machine private bootstrap rehearsal |
| PROFESSOR_REPORTING | Synthesizes frozen results without new science. | `docs/professor_submission_v1/03_FIRST_RESULTS_REPORT.md` | IMPLEMENTED_EXECUTED_AUDITED | yes | yes | professor submission package | maintain evidence-to-claim links |
| THESIS_DRAFT | Documentation-only thesis scaffold after checkpoint. | source ref `origin/task-039e3-r2r-thesis-draft-scaffold-v1`; `docs/thesis_draft_v1/15_FULL_THESIS_WORKING_DRAFT.md` | IMPLEMENTED_NOT_EXECUTED | no | partial | thesis draft directory | professor-dependent decisions and bibliography |

## Lineage observations and inconsistencies

1. **Current checkout is stale and misleading for RCC bootstrap.** It ends at the originally blocked GDN arm. The later GDN port closure, candidate integration, rule construction, utility evaluation, frozen results, reports, and thesis materials are visible only through later refs.
2. **`origin/main` is also stale for current science.** It points to TASK-039E2 configuration audit (`11a5f04...`) and is an ancestor of the checkpoint, but it does not name the later utility/result state.
3. **Canonical public checkpoint and thesis draft have different roles.** The thesis branch is exactly one documentation commit after the canonical checkpoint; it must not silently replace the checkpoint as scientific authority.
4. **Root continuity summaries are stale within the canonical tree.** `CURRENT_PROJECT_STATE.md` names `70811efe...` as its basis, while `docs/project_state/HANDOFF.md` still presents an OUTER failure-disposition task as next. The newer committed post-push audit and professor package establish the later human-facing state. Exact frozen receipts remain higher authority than those stale summaries.
5. **Many result task branch refs are local-only, but their commits and artifacts are preserved in the canonical remote ancestry/tree.** RCC should resolve by commit/path in the checkpoint rather than assuming a missing remote task branch means missing evidence.
6. **ARGOS is not the HAI P1 source lineage.** Its code/reports remain reachable as frozen methodological reference only.
7. **Worktree proliferation is visible.** Registered historical and detached worktrees should be treated as inventory/cleanup candidates, not authority, unless their commits are independently identified in Git.

## Canonical candidates (not a final selection)

### Candidate 1 — mutable canonical branch name

- Ref: `origin/research-v6-thesis-checkpoint`
- Commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
- Advantages: complete remotely shared tree; audited source/result/report checkpoint; intended canonical branch name.
- Risk: branch names are movable; RCC must pin the commit as well as the ref.
- Agent A recommendation: preferred RCC scientific source **if stored as ref plus exact commit**.

### Candidate 2 — immutable checkpoint tag

- Ref: `thesis-v1-post-push-audit`
- Commit: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
- Advantages: same audited tree as Candidate 1 with an immutable release-style locator.
- Risk: tag alone does not convey a writable/update branch policy.
- Agent A recommendation: use as the immutable pin paired with Candidate 1, not as a conflicting scientific tree.

### Candidate 3 — thesis documentation overlay

- Ref: `origin/task-039e3-r2r-thesis-draft-scaffold-v1`
- Commit: `ebc5a57bfdb7d8266f96f2990338effb9d0a2743`
- Advantages: includes the complete checkpoint plus the latest thesis draft scaffold.
- Risk: not independently designated/audited as a new scientific checkpoint; professor decisions remain open.
- Agent A recommendation: optional documentation input only. Do not use as the scientific source authority without an explicit user decision.

## Coordinator-facing verdict

- Git/source lineage can support RCC-001, but only with conditions.
- The safe default source pair is `origin/research-v6-thesis-checkpoint` plus exact commit/tag pin `2dc7e6c...` / `thesis-v1-post-push-audit`.
- The thesis draft branch should be mounted as a documentation overlay, not allowed to redefine frozen science.
- The current `task-039c-gdn` checkout and `origin/main` must not be used as RCC's canonical current-research tree.
- A user decision is required to approve the canonical source policy and whether the thesis overlay is ingested separately.

