# RCC-000 Agent B Evidence — Artifact, Privacy, and Preservation

## Scope and safety boundary

- Role: read-only artifact/privacy/preservation audit.
- Scientific executions: `0`.
- Metric recomputations: `0`.
- Test2 feature-byte accesses: `0`.
- Test2 label accesses: `0`.
- Private scientific payload opens: `0`.
- Remote pushes, merges, checkouts, and tag changes: `0`.
- Evidence was collected from Git objects, public reports, public custody metadata,
  the exact-blob path-disposition manifest, and local preservation-file metadata.
  No private locator or private value is reproduced below.

## Principal refs and packages observed

| Item | Commit | Evidence-backed role |
|---|---|---|
| `origin/research-v6-thesis-checkpoint` | `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` | Audited remote scientific/report checkpoint; source, frozen public INNER results, professor package, path disposition, and post-push audit are present. |
| `thesis-v1-post-push-audit` | `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` | Immutable annotated anchor for the audited checkpoint. |
| `thesis-v1-first-results` | `5aa7c61ee37fb232c9b487e448ddbd30e3628872` | Earlier professor-ready pre-audit checkpoint. |
| `origin/task-039e3-r2r-thesis-draft-scaffold-v1` | `ebc5a57bfdb7d8266f96f2990338effb9d0a2743` | Documentation child of the audited checkpoint containing the thesis draft scaffold. |
| `docs/professor_submission_v1/` | introduced at `87033702d0c16abaf141c03983098f69e6a8cb16` | Professor-facing synthesis; included in the audited checkpoint. |
| `docs/post_push_checkpoint_v1/` | introduced at `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` | Whole-repository remote checkpoint audit. |

## Frozen/public-safe artifact authority inventory

All identities below are public artifact self-hashes when the artifact exposes
one; otherwise the recorded identity is the public Git blob SHA. Counts are
reported only where already published.

| Artifact | Representative path | Producer commit | Classification | Public-safe identity | Frozen / audited / current | Notes |
|---|---|---|---|---|---|---|
| Candidate profiling cohort | `docs/task_reports/TASK-039C_CANDIDATE_PROFILING_COHORT.json` | `9ac4578603b81385dc9592cd5db5076d83a3fb66` | public aggregate scientific artifact | `6d488da608c2804e8cf3a183c4904403eb9904ad858c85beb34b48cb8bd79254` | yes / yes / yes | Published cohort has 47 unique source-target pairs. |
| Confirmed relation cohort | `docs/task_reports/TASK-039E0_CONFIRMED_RELATION_COHORT.json` | `20ca2e6f561ce0cdfaf822198f7b64d8e143215c` | public aggregate scientific artifact | `e71fa69999dbc18310ebb1730fd1d0ea36403763e891b99841ab8cef7ec18732` | yes / yes / yes | Published cohort has 23 pairs and 42 directed relations; principal COMMON-42 relation authority. |
| COMMON-42 authority check | `docs/task_reports/TASK-039E3_R2R_UTILITY_COMMON42_AUTHORITY_CHECK.json` | `6b3b912aa6b69394a06697c3244589cfe98ecd4a` | public authority metadata | `3bd07e1c2baf375bde86a2310b529dda40962e027edbd77485f431dc244730ff` | yes / yes / yes | Binds the utility portfolio without exposing private numeric values. |
| Normal-only numeric authority receipt | `docs/task_reports/TASK-039E3_R2R_UTILITY_NORMAL_ONLY_AUTHORITY_V1_MATERIALIZED_RECEIPT.json` | `e971c8c8543f49b31aba2a57cf60257d190b76d5` | public hash/receipt metadata; payload private | Git blob `80e5f4491c1daf19e788f36621e188364af6ae00` | yes / yes / yes | Private numeric registry/model values remain outside Git. |
| T0/T1/T1-B/T2 construction synthesis | `docs/task_reports/TASK-039E3_R2R_RESULT_ANALYSIS_REPORT.md` and adjacent `RESULT_ANALYSIS_*.json` | `bc3d930237f1e6b52c6afc02d643d4b6cc1bb0d8` | public aggregate result analysis | report blob `2c722f53e1ba5a25cc2f98c1e88e6bde0f302cda` | yes / yes / yes | Public report records T0/T1/T1-B 42/42 executable rules and T2 39/42 plus 3 `no_rule`; no private numeric authority is disclosed. |
| D0 prediction | `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_DETECTOR_PREDICTION_ARTIFACT_V1.json` | `78d758f50657413eed28dc838212be9a1edeffc7` | public frozen scientific artifact | `a4b58f1c78b9bb53125da1a009f3fd05b02e1c83a789772a341a7679fddca0f6` | yes / yes / yes | Result-to-code traceability PASS. |
| D0 metrics | `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D0_METRICS_V1.json` | `78d758f50657413eed28dc838212be9a1edeffc7` | public frozen metric summary | `bec8629e2dbdc178d750e795ada7b74aaf0f1475c32c5881c13a2e65c0a92cbf` | yes / yes / yes | Public professor values agree with the frozen artifact. |
| D1 prediction | `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_RULE_PREDICTION_ARTIFACT_V1.json` | `9fe9192c6da4e2d1f3c7a42ecdd28006e8534449` | public frozen scientific artifact | `58c3c49f9657f68d35c830b12eeb493ce4bbf7669c90f04813fb80246c3c2682` | yes / yes / yes | COMMON-42 runtime output; integrity-audited. |
| D1 metrics | `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D1_METRICS_V1.json` | `9fe9192c6da4e2d1f3c7a42ecdd28006e8534449` | public frozen metric summary | `b11a785dd243f30cac8820c49b978e194d993282c728537137b6a803b16d70d1` | yes / yes / yes | Public professor values agree with the frozen artifact. |
| D2 V1 prediction | `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_COMBINED_PREDICTION_ARTIFACT_V1.json` | `9078c4a1639c35d848cad28194fb4195eb5daca5` | public frozen scientific artifact | `cf1005a03d98481b57c3ce2ad74db3e2e5d2dc3a1983d60e0aedb4f46c83b3f5` | yes / yes / yes | Same-second deterministic fusion result. |
| D2 V1 metrics | `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_METRICS_V1.json` | `9078c4a1639c35d848cad28194fb4195eb5daca5` | public frozen metric summary | `dacf0c8c7e43b3f48bbbd635ad5c824a338ecf4e52476402ec244eef4012c84d` | yes / yes / yes | Negative fusion evidence; 0/3 D0-miss recovery in the published result. |
| D2 V2 prediction | `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_COMBINED_PREDICTION_ARTIFACT_V1.json` | `55d41c543e110a9a6f0f5e2e2671857dba938aaa` | public frozen scientific artifact | `31035da56e140141917437df5b3473b803153621c7e1022830cccde52f61c0b3` | yes / yes / yes | Native-horizon deterministic fusion result. |
| D2 V2 metrics | `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_METRICS_V1.json` | `55d41c543e110a9a6f0f5e2e2671857dba938aaa` | public frozen metric summary | `8fabdccc0c9a9b502497aa58163131647303d5e27acefb995a06ca9d43850ba7` | yes / yes / yes | Negative fusion evidence; 0/3 D0-miss recovery in the published result. |
| D2 V2 integrity completion | `docs/task_reports/TASK-039E3_R2R_UTILITY_INNER_D2_V2_RESULT_INTEGRITY_COMPLETION_V1.json` | `228f1e94baed531ae8d9503cb3c5ec0a3aa47f6b` | public integrity authority | `b7034829527d7469459298735d253693b41f20bde6f0ab867bac71e804fa7d06` | yes / yes / yes | Canonical result-integrity completion authority. |
| OUTER recovery blocker | `docs/task_reports/TASK-039E3_R2R_UTILITY_OUTER_D0_D1_D2V1_EXECUTION_RECOVERY_V1_BLOCKER.json` | `c2670f0a49fb704799e62648805188983fb6ef83` | public custody/accounting metadata; no OUTER result | `5949aa9aa16df04143bed4bd58a4061306f5e1ed392fc45b39b6cb23c3951d8e` | yes / custody-audited / yes | Public evidence states feature bytes 0, label accesses 0, executions 0, predictions/metrics none, generalization unconfirmed. |
| Professor submission | `docs/professor_submission_v1/03_FIRST_RESULTS_REPORT.md` | `87033702d0c16abaf141c03983098f69e6a8cb16` | public scientific synthesis | Git blob `8627ae77fd3ea31366c4070596fd0488342d3c62` | yes / validated / yes | Synthesis only; frozen artifacts above remain authoritative. |
| Post-push implementation audit | `docs/post_push_checkpoint_v1/08_IMPLEMENTATION_COMPLETENESS.md` | `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e` | public repository audit | Git blob `29e571213a54a12e48b01ad7a6d5000cb6259740` | yes / yes / yes | Records INNER architecture and thesis method implemented, empirical validation and portable release partial. |
| Thesis working draft | `docs/thesis_draft_v1/15_FULL_THESIS_WORKING_DRAFT.md` | `ebc5a57bfdb7d8266f96f2990338effb9d0a2743` | public provisional synthesis | Git blob `5c9d4d0612d26695a2eb160704fdf68abaff6f4d` | yes / document-validated / current on thesis branch only | Not present at the audited checkpoint commit; professor decisions remain provisional. |

## Private/public boundary findings

The canonical remote tree contains public code, schemas, configs, frozen public
predictions/metrics, aggregate reports, and hash-only custody/identity records.
The following remain intentionally outside Git and were not opened:

- raw HAI payloads, including test1/test2 feature data and labels;
- private normal-only numeric registries and their calibrated numeric values;
- private PCA model/threshold payloads;
- private D1 relation-evidence payloads where governed as private;
- private FusionEvidenceV2 and MetricEvidenceV2 payloads;
- provider credentials and raw private provider-response material;
- machine-local private-custody locators.

`git ls-tree` found no tracked raw/private data directory and no private
scientific payload named as FusionEvidenceV2 or MetricEvidenceV2. The two
tracked files containing those role names are sanitized identity reports, not
the private payloads. `.gitignore` blocks local raw/derived data, CSV by
default, private binary formats, runtime artifacts, local environments, and
`.env` files.

## Static leak audit

Audited ref: `origin/research-v6-thesis-checkpoint` plus a scanner validation
on its documentation-only thesis child.

| Gate | Result |
|---|---:|
| exact legacy inventory reconciliation | `156` occurrences / `30` base files |
| exact grandfathered blobs in current checkpoint | `29` files / `155` occurrences |
| grandfathered blob hash mismatches | `0` |
| grandfathered paths missing | `0` |
| new unpublished exact-current-host occurrences outside allowlist | `0` |
| current generator absolute-host emission capability | `0` |
| potential AWS/OpenAI/GitHub/private-key/Authorization secret patterns | `0` |
| tracked private binary candidates | `0` |
| tracked raw HAI test-file candidates | `0` |
| private scientific-value exposures established by the frozen path audit | `0` |

The generic host-path pattern also appears in six synthetic negative-test
fixtures. None matches the current host identity; these are test inputs, not
live locators. The remaining 155 occurrences are exact-blob-grandfathered
legacy environment metadata already reachable on origin. They are not counted
as current private exposure, and changing them would break frozen report
identity chains.

Commands/categories used, with match values suppressed:

- `git ls-tree -r --name-only <ref>` for tracked-name and binary/raw suffix census;
- `git grep -Il -E <category-pattern> <ref>` for safe file-name-only secret/path census;
- `git rev-parse <ref>:<path>` for exact-blob allowlist verification;
- `scripts/scan_pre_push_host_paths_v2.py --validate` for exact-blob policy validation;
- public report/manifest reads through `git show <ref>:<path>`.

Verdict: `PRIVATE_EXPOSURES = 0` for the audited canonical snapshot, with the
explicit non-secret legacy locator exception above.

## Preservation audit

| Preservation item | Status | Evidence |
|---|---|---|
| canonical remote branch | PASS | `origin/research-v6-thesis-checkpoint` resolves to `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`. |
| checkpoint tags | PASS | `thesis-v1-first-results` peels to `5aa7c61e...`; `thesis-v1-post-push-audit` peels to `2dc7e6c2...`. |
| thesis draft remote branch | PASS | `origin/task-039e3-r2r-thesis-draft-scaffold-v1` resolves to `ebc5a57b...`. |
| all-refs Git bundle | PASS, STALE FOR LATEST REFS | Local-only bundle exists, SHA-256 `232b6c9c0224e1109878e571ed0f45c2703e38e6e2e20426afe55cd5cd591dd1`, and `git bundle verify` passes complete-history validation. Its recorded HEAD includes `70811efe...` but it does not include `5aa7c61e...`, `2dc7e6c2...`, or `ebc5a57b...`. |
| source-only archive | PASS, PRE-CHECKPOINT SNAPSHOT | Local-only archive exists, SHA-256 `8427aacf47697b045224349ccd898d722a9360dfe99660ffb15a4c87ee7b0b3d`, matching the public preservation manifest. It is the earlier source-only HEAD package and is not a self-describing replacement for the audited remote checkpoint. |
| environment manifest | PASS | `docs/professor_first_results_v1/ENVIRONMENT_MANIFEST.md`; sanitized and tracked. |
| branch/commit inventory | PASS | `docs/professor_first_results_v1/CANONICAL_LOCAL_BRANCH_COMMIT_INVENTORY.md`; public subset. |
| thesis artifact index | PASS | `docs/professor_first_results_v1/THESIS_ARTIFACT_INDEX.md`; public evidence only. |
| professor package | PASS | Frozen on the canonical remote checkpoint. |
| post-push checkpoint audit | PASS | Frozen at the canonical remote checkpoint and tagged. |

The audited remote branch/tag protect the current public checkpoint. The local
bundle/archive are valid but predate the latest remote checkpoint and thesis
draft. A refreshed local bundle is a reasonable future preservation action,
but RCC-000 should not create it without the coordinator/user choosing the RCC
canonical/overlay policy.

## Missing evidence and cautions

1. No fresh network fetch was performed. Remote conclusions are about the
   locally available `origin/*` tracking refs and Git objects.
2. Local preservation assets are untracked by design. Their current hashes
   match the tracked manifest, but the bundle does not contain the latest
   canonical or thesis commits.
3. Private payload presence/health was intentionally not audited; RCC-000 only
   confirms the public boundary and public custody records.
4. The current primary checkout is an older task branch and contains unrelated
   untracked worktree/preservation directories. Artifact authority therefore
   comes from explicit refs, not from current-checkout file presence.

## Agent B verdict

`PASS_WITH_CONDITIONS`

- Artifact authority is recoverable and public/private boundaries are intact.
- The audited remote checkpoint is the strongest current public artifact and
  preservation anchor.
- The thesis draft is a later documentation-only overlay on a separate remote
  branch.
- RCC-001 should wait for a user decision on whether its source is the audited
  checkpoint alone or the checkpoint plus thesis-doc overlay.
- Refreshing the local preservation bundle after that decision is recommended,
  not automatically performed.
