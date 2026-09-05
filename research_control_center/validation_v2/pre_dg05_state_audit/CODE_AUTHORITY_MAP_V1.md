# Code Authority Map V1

Static inventory at `a90d0e669b4a5ab87177c9188695345faf81e2ea`. Classifications describe current routing and do not rename or modify files.

| Path/module | Major entry points | Caller / inputs → consumer / outputs | Classification | Audit note |
|---|---|---|---|---|
| `src/paperworks/candidates/metadata_candidate_discovery_v1.py` | `discover_metadata_pair_records_v1`, `rank_supported_metadata_records_v1` | reviewed metadata/C0 → frozen META prior | `CURRENT_SUPPORTING_CODE` | no reconstruction authorized |
| `src/paperworks/candidates/statistical_candidate_discovery_v1.py` | lagged correlation/select/rank functions | projected normal train1/2 → STAT evidence/candidates | `CURRENT_SUPPORTING_CODE` | statistical, not causal |
| `scripts/prepare_xver_candidates_v2.py` | `main` | portable META + STAT Top-K → external candidate union | `CURRENT_SUPPORTING_CODE` | historical producer; GDN admission false |
| `src/paperworks/validation_v2/exp01_relation_confirmation_v2.py` | fit/confirm union functions | candidate union + normal splits → confirmation evidence | `CURRENT_SUPPORTING_CODE` | normal reference only |
| `src/paperworks/validation_v2/xver_structural_v1.py` | structural evidence builder | normal split → 20 semantic tuples/pair | `CURRENT_SUPPORTING_CODE` | SCI-01 |
| `src/paperworks/validation_v2/exp01c_backend_v1.py` | checkpoint validation/inference | frozen checkpoint/config → learned evidence | `CURRENT_SUPPORTING_CODE` | historical training path |
| `src/paperworks/validation_v2/xver_gdn_execution_v1.py` | global/event extraction | external split checkpoint → typed evidence | `CURRENT_SUPPORTING_CODE` | no DG-05 runtime use |
| `src/paperworks/validation_v2/xver_gdn_roles_v1.py` | aggregate/project roles | three seeds → GLOBAL5/EVENT10 | `CURRENT_SUPPORTING_CODE` | types intentionally isolated |
| `src/paperworks/validation_v2/exp03b_semantic_v2.py` | proposal parser, T0 | structural evidence → semantic Rule set | `CURRENT_SUPPORTING_CODE` | T0 consumes structural fields only |
| `src/paperworks/validation_v2/exp03b_hidden_v2.py` | verifier/feedback/retrieval | train2 authority + proposal → admission/issues | `CURRENT_SUPPORTING_CODE` | hidden verifier |
| `src/paperworks/validation_v2/xver_prompt_v1.py` | request rendering | train1 structural/STAT/GLOBAL5 → provider payload | `HISTORICAL_FROZEN` | provider execution complete |
| `src/paperworks/validation_v2/xver_provider_execution_v1.py` | gate/runner | frozen approval + sanitized payload → T2 responses | `HISTORICAL_FROZEN` | not used at DG-05 |
| `src/paperworks/validation_v2/exp03b_binder_v2.py` | binding authorization/roles | confirmed semantics + normal summaries → numeric roles | `CURRENT_SUPPORTING_CODE` | SCI-02B |
| `src/paperworks/validation_v2/exp02_bindings_v2a.py` | event/parameter helpers | frozen normal summaries and descriptors → bound execution inputs | `CURRENT_SUPPORTING_CODE` | reused by current DG-05 Rule runtime; not only historical EXP-02 |
| `src/paperworks/validation_v2/exp03b_evaluation.py` | `GuardRuleInput`, `run_guard_portfolio` | confirmed/bound Rules + normal guard matrix → retained portfolio | `CURRENT_SUPPORTING_CODE` | unversioned name but imported by current binders/closures |
| `src/paperworks/validation_v2/exp03b_guard_v1.py` | guard/census helpers | guarded per-Rule results → portfolio census | `CURRENT_SUPPORTING_CODE` | one-way normal guard support |
| `src/paperworks/validation_v2/xver_numeric_closure_v1.py` | external T0 binding | external admissions + normal authority → numeric Rules | `CURRENT_SUPPORTING_CODE` | frozen portfolios |
| `src/paperworks/validation_v2/xver_t2_closure_v1.py` | external T2 binding | external T2 admissions → numeric/guard inputs | `CURRENT_SUPPORTING_CODE` | frozen portfolios |
| `src/paperworks/validation_v2/formal_v4_authority_v1.py` | portfolio/runtime authority builders | descriptors + numeric provenance → immutable authority | `CURRENT_SUPPORTING_CODE` | source of frozen portfolio authorities |
| `src/paperworks/validation_v2/runtime_v1.py` | `evaluate_formal_v4_semantics_v1` | frozen Rule semantics + rows → outcomes | `CURRENT_EXECUTABLE_AUTHORITY` | LLM-free |
| `src/paperworks/validation_v2/pca_spe_v2.py` | fit/score/calibrate | HAI23 normal fit → detector | `CURRENT_SUPPORTING_CODE` | fit frozen; not refit in DG-05 |
| `src/paperworks/validation_v2/isolation_forest_v1.py` | fit/score/calibrate | normal fit → secondary detector | `CURRENT_SUPPORTING_CODE` | comparator |
| `src/paperworks/validation_v2/xver_detector_v1.py` | external PCA/IF scorers | external frozen model + projection → scores | `CURRENT_EXECUTABLE_AUTHORITY` | fit path historical; scoring current |
| `src/paperworks/validation_v2/dg05_execution_closure_v1.py` | registries, projection, executor, cell, freeze, lease, scenario, denominator | predecessor executable authority + files/methods → Phase A/B primitives | `CURRENT_EXECUTABLE_AUTHORITY` | mixed predecessor/current ownership; V3 routing blocker |
| `src/paperworks/validation_v2/multipanel_custody_v1.py` | file/allowlist/lease types | authority-bound paths → custody objects | `CURRENT_EXECUTABLE_AUTHORITY` | prospective only |
| `src/paperworks/validation_v2/dg05_label_custodian_v1.py` | `consume_and_extract_v1` | one-shot lease + allowlist → scenarios | `CURRENT_EXECUTABLE_AUTHORITY` | production V3 launcher absent |
| `scripts/run_dg05_label_custodian_v1.py` | CLI `main` | resource policy/request → isolated custodian output | `CURRENT_SUPPORTING_CODE` | isolation capable, not V3-orchestrated |
| `src/paperworks/validation_v2/dg05_executable_v3.py` | `initialize_dg05_executable_v3_preaccess` | V3 + predecessor public authorities → preaccess dict | `CURRENT_EXECUTABLE_AUTHORITY` | no adapter into typed prediction state |
| `src/paperworks/validation_v2/dg05_metric_surface_execution_v1.py` | primitive builder, final close | frozen execution inputs → metric primitive/result state | `CURRENT_EXECUTABLE_AUTHORITY` | single-interval, timestamp, normal-burden findings |
| `src/paperworks/validation_v2/dg05_metric_surface_v1.py` | complete surface builder | primitive + contract → 228 surface payloads | `CURRENT_EXECUTABLE_AUTHORITY` | Rule episode default issue |
| `src/paperworks/validation_v2/dg05_metric_surface_oracle_v1.py` | path-based verifier | primitive/result/contract → arithmetic receipt | `CURRENT_EXECUTABLE_AUTHORITY` | provenance begins at primitive |
| `src/paperworks/validation_v2/dg05_expected_surface_v1.py` | census builder | contract → expected identifier set | `CURRENT_SUPPORTING_CODE` | 228 IDs |
| `src/paperworks/validation_v2/dg05_surface_completeness_v1.py` | exact set equality | expected/builder/verifier declarations → PASS | `CURRENT_SUPPORTING_CODE` | semantic correctness not inspected |
| `src/paperworks/validation_v2/etapr_exchange_v1.py` | pinned official wrapper | ranges → eTaPR | `CURRENT_EXECUTABLE_AUTHORITY` | secondary metric |
| `src/paperworks/validation_v2/multipanel_etapr_v2.py` | namespaced union | file-local ranges → same-version union | `CURRENT_EXECUTABLE_AUTHORITY` | no cross-version union |
| `src/paperworks/validation_v2/dg05_connected_rehearsal_v3.py` | connected synthetic rehearsal | synthetic V2 manifest/data → V3 metric rehearsal | `TEST_ONLY` | does not prove exact V3 transition |
| `src/paperworks/validation_v2/dg05_result_oracle_v1.py` | predecessor full-path verifier | many persisted authority paths → historical result receipt | `HISTORICAL_FROZEN` | confusing but isolated; stronger provenance inputs, not used by V3 metric close |
| `src/paperworks/validation_v2/front_*`, `exp04_protocol_v1.py` | development runner pieces | HAI23 test1 development → EXP-04 | `HISTORICAL_FROZEN` | not current DG-05 route |
| unversioned `exp03b_prompt.py`, `exp03b_provider_gate.py`, `exp03b_execution.py`, `exp03b_reporting.py` | early EXP-03B APIs | earlier provider path | `HISTORICAL_FROZEN` | confusing but isolated; `_v2` path is frozen result route |
| `experiments/argos_reproduction/*` | ARGOS reference experiment | frozen reference only | `HISTORICAL_REFERENCE_ONLY` | no continuation authorization |
| `src/paperworks/dsl/*`, `verification/*`, legacy `runtime/*` | legacy RuleAst/runtime | historical compatibility | `HISTORICAL_FROZEN` | no current validation_v2 imports found |
| `research_control_center/**`, `docs/**` | records, reports, public authorities | decisions/results → human/governance context | `RCC / DOCUMENTATION` | several stale selectors documented separately |

## Concrete routing risks

1. `dg05_executable_v3.py:110-160` returns a plain V3 preaccess state. `dg05_execution_closure_v1.py:762-780` and `1115-1119` require `DG05ExecutableAuthorityManifestV1`. No bound adapter exists.
2. `dg05_connected_rehearsal_v3.py:186-249` creates and uses a synthetic predecessor manifest; this does not prove V3-manifest continuity.
3. `dg05_execution_closure_v1.py:911-936` permits duplicate timestamps, whereas `dg05_metric_surface_execution_v1.py:47-60` rejects them and later uses row offsets for delay/ranges.
4. Scenario records and custodian allow one or more closed intervals, while `dg05_metric_surface_execution_v1.py:130-138` requires exactly one.
5. Production Rule traces omit `rule_alarm_episodes`; `dg05_metric_surface_v1.py` and its oracle default the value to zero.
6. The metric oracle opens only primitive/result/contract; it does not independently reopen the original prediction, scenario, denominator, normal-burden, projection, or trace authorities.

## Dead / duplicate code taxonomy

| Taxonomy | Files/patterns | Basis |
|---|---|---|
| `SAFE_HISTORICAL` | `experiments/argos_reproduction/*`; legacy `dsl`, `verification`, and runtime packages; frozen EXP-04 front path | Explicitly frozen/reference-only and no current validation-v2 routing observed. |
| `CONFUSING_BUT_ISOLATED` | predecessor `dg05_result_oracle_v1.py`; unversioned old EXP-03B provider modules; repeated Wilson/McNemar/range helpers | Explicit imports isolate current routes, but similar names can mislead a manual operator. |
| `POTENTIAL_EXECUTION_RISK` | mixed predecessor/current APIs in `dg05_execution_closure_v1.py`; old authority-freeze scripts callable by hand | Current prediction primitives share a file with historical manifest/result APIs. The concrete V3 transition gap makes routing material. |

No code is deleted or declared globally dead. `exp03b_evaluation.py` is specifically retained as current supporting code despite its unversioned name.

## Ownership note

Formal V4 and DG-05 currently route through `validation_v2/runtime_v1.py`, not `paperworks.contracts/runtime_v1.py`. This is an actual architecture fact, not a recommendation. The adjacent canonical/validation-v2 ownership should be made explicit in a future authorized closure so that a “canonical” import does not silently replace the frozen Formal V4 route.
