# Decisions Required

## Resolved Decisions

### DEC-001: Implementation repository and raw-data placement

- Status: resolved
- Owner: researcher
- Needed before: TASK-001
- Final decision: Use the current directory as the implementation repository, but do not keep raw SWaT data inside the Git working tree. At minimum, strongly ignore raw and derived time-series files before Git initialization; preferably move raw files outside the repository and access them via `SWAT_DATA_ROOT`.
- Decision date: 2026-06-25
- Actions:
  - Add `.gitignore` entries for `dataset/`, `data/raw/`, `data/swat/`, `*.csv`, `*.xlsx`, and unapproved `*.parquet`.
  - Access SWaT through `SWAT_DATA_ROOT`.
  - Do not commit raw SWaT rows, extracted windows, fixtures derived from SWaT, raw-sequence plots, or downloadable derived copies.
- Consequences for claims/evaluation: The code repository remains shareable without distributing SWaT data.

### DEC-002: SWaT source and terms

- Status: resolved
- Owner: researcher
- Needed before: TASK-001
- Final decision: Treat the current SWaT CSV files as unverified local data until provenance is confirmed.
- Decision date: 2026-06-25
- Actions:
  - Create a dataset manifest draft.
  - Record file names, row counts, column names, label schema, timestamp/index column, sampling interval, feature count, SHA-256 hashes, claimed source, and terms-of-use status.
  - Mark source and terms-of-use status as unverified until manually confirmed.
  - Do not upload these files to GitHub.
- Consequences for claims/evaluation: Current files may support smoke tests but not official SWaT claims.

### DEC-003: Treatment of current CSV files

- Status: resolved
- Owner: researcher
- Needed before: TASK-001
- Final decision: Treat `normal.csv`, `attack.csv`, and `merged.csv` as smoke-test / feasibility inputs only.
- Decision date: 2026-06-25
- Actions:
  - For TASK-001 to TASK-003, support reading these files for local smoke tests.
  - Do not treat `normal.csv` and `attack.csv` as official SWaT train/test files.
  - Do not use them for final evaluation claims.
  - Prefer `merged.csv` only for schema inspection and preliminary timeline reconstruction.
  - Add `dataset_status: local_unverified_smoke_test` to the manifest draft.
- Consequences for claims/evaluation: Official SWaT files or approved provenance are required before final evaluation.

### DEC-004: GDN implementation strategy

- Status: resolved
- Owner: researcher
- Needed before: TASK-004
- Final decision: Use a modern PyTorch/PyG port. Do not depend directly on the legacy upstream GDN environment.
- Decision date: 2026-06-25
- Actions:
  - Use `d-ailin/GDN` only as a read-only reference.
  - Implement project-owned GDN modules under `src/`.
  - Use modern supported PyTorch/PyG versions.
  - Apply CandidateUniverse `C_i` masking before Top-K.
  - Exclude self-edges from exported candidate relation artifacts.
  - Separate message-passing self-loops from candidate relation edges.
  - Do not reuse upstream `report=best` or test-label threshold selection logic.
- Consequences for claims/evaluation: Candidate extraction remains compatible with project split and provenance rules.

### DEC-005: Canonical rule view and optional GDN view

- Status: resolved
- Owner: researcher
- Needed before: TASK-001
- Final decision: For TASK-001 to TASK-003, use only the 1-second canonical rule view.
- Decision date: 2026-06-25
- Actions:
  - Define canonical rule view as the high-resolution time series used for relation profiling, response-delay calibration, and DSL rule execution.
  - Do not introduce a downsampled GDN view yet.
  - Add `sampling_period_seconds` and `source_view: canonical_rule_view` to data artifacts.
  - Defer optional downsampled GDN view until after data contracts and candidate universe modules are stable.
- Consequences for claims/evaluation: Early calibration preserves 1-second response timing and avoids premature downsampling assumptions.

### DEC-006: Evaluation metric and point adjustment

- Status: resolved
- Owner: researcher
- Needed before: TASK-014
- Final decision: Use PA-free metrics as primary. Point-adjusted metrics may be reported only as supplementary.
- Decision date: 2026-06-25
- Actions:
  - Primary metrics include PA-free F1, AUROC/AUPRC where appropriate, and event-level or range-based metrics if implemented.
  - Do not use point-adjusted metrics for model selection, rule selection, threshold selection, or headline claims.
  - Label any point-adjusted metrics explicitly as supplementary.
  - Do not reuse upstream ARGOS or GDN best-test-label threshold selection.
- Consequences for claims/evaluation: Evaluation remains conservative and reproducible.

### DEC-010: Modern PyTorch/PyG GDN backend environment

- Status: resolved
- Owner: researcher
- Needed before: closing TASK-004 with real GDN training
- Final decision: Use a current CPU-only PyTorch/PyG environment for the first modern GDN backend.
- Decision date: 2026-06-25
- Actions:
  - Install PyTorch from the official CPU wheel index.
  - Install PyG / `torch_geometric` from PyPI.
  - Record installed versions in `docs/ENVIRONMENT_STRATEGY.md`.
  - Keep GPU/CUDA support deferred until the CPU path is reproducible.
- Resolved environment:
  - Python `3.12.13`
  - `torch 2.12.1+cpu`
  - `torch_geometric 2.8.0`
  - `torch.cuda.is_available() == False`
- Consequences for claims/evaluation: TASK-004 can proceed to a CPU synthetic GDN trainer without relying on the legacy upstream GDN environment. Performance claims remain out of scope until real-data protocol and Phase Gate A are approved.

### DEC-008: Candidate feasibility gate criteria

- Status: resolved
- Owner: researcher
- Needed before: TASK-005 / Phase Gate A
- Final decision: Use smoke feasibility as the TASK-005 pass/fail gate.
- Decision date: 2026-06-25
- Pass criteria:
  1. Candidate artifacts are generated successfully from the approved configuration.
  2. Every exported GDN candidate edge belongs to the precomputed CandidateUniverse `C_i`.
  3. No self-edge is exported as a candidate relation.
  4. Message-passing self-loops, if used internally, are not persisted as relation candidates.
  5. The same config and seed produce identical or hash-stable candidate artifacts.
  6. Required provenance fields are present: candidate origin, source variable, target variable, rank, score if available, seed, K, config hash, and data manifest reference.
  7. No sealed test labels or attack labels are used for candidate generation, filtering, thresholding, or pass/fail decisions.
  8. The final report clearly states: "This is a smoke feasibility result.", "This is not a final performance claim.", and "This does not validate anomaly detection performance."
- Explicitly out of scope:
  - benchmark-style candidate recall,
  - final SWaT attack-variable coverage,
  - strict relation checklist coverage,
  - point-adjusted or detection metrics,
  - K tuning based on observed smoke results,
  - enabling fallback candidates after seeing results.
- Consequences for claims/evaluation: TASK-005 verifies implementation correctness, reproducibility, mask enforcement, and data-leakage prevention only. Seed/K stability may be logged descriptively but is not a pass/fail gate.

### DEC-009: Real-data candidate policy for statistical and fallback origins

- Status: resolved
- Owner: researcher
- Needed before: enabling statistical or fallback origins on SWaT smoke runs
- Final decision: For the first TASK-005 smoke run, use metadata same-stage candidates only.
- Decision date: 2026-06-25
- Required config behavior:
  - `candidate_policy_name: metadata_same_stage_only_smoke`
  - `candidate_origins.metadata_same_stage: true`
  - `candidate_origins.normal_statistical_top_m: false`
  - `candidate_origins.type_compatible_fallback: false`
- Constraints:
  1. Do not enable statistical candidates after seeing the first smoke result.
  2. Do not enable fallback candidates to fix empty or weak outputs after observing the result.
  3. If statistical or fallback candidates are tested later, create a separate pre-registered config before running.
  4. The TASK-005 report must clearly state which candidate origins were enabled.
  5. If some targets have no metadata same-stage candidates, report them as empty-target cases rather than silently filling them with fallback candidates.
- Consequences for claims/evaluation: The first smoke run remains conservative, auditable, and free of hidden data-dependent tuning.

### DEC-011: TASK-006 synthetic-smoke calibration policy

- Status: resolved
- Owner: implementation agent
- Needed before: TASK-006 synthetic fixture completion
- Final decision: For TASK-006 implementation tests only, use an explicit `task006_synthetic_smoke` profiling configuration.
- Decision date: 2026-06-25
- Required config behavior:
  - `relation_type: binary_actuator_to_continuous_sensor`
  - `source_view: canonical_rule_view`
  - trigger operator: `changed_to` from `0.0` to `1.0`
  - response operator: `increase_within`
  - `max_response_delay_samples: 4`
  - `min_matched_response_count: 2`
  - `delay_quantile: 1.0`
  - `magnitude_quantile: 0.0`
  - `irregular_sampling_policy: reject`
- Constraints:
  1. This policy is only a synthetic smoke-test implementation contract.
  2. It must not be used as a final SWaT calibration policy or benchmark claim without researcher approval.
  3. Unsupported pairs must produce explicit `INSUFFICIENT_NORMAL_SUPPORT` status and must not fabricate calibration values.
  4. Calibration must use `calibration_normal` and `canonical_rule_view` only.
- Consequences for claims/evaluation: TASK-006 can validate deterministic profiling and provenance behavior without deciding final research calibration thresholds.

### DEC-012: TASK-009 synthetic-smoke verifier thresholds

- Status: resolved
- Owner: implementation agent
- Needed before: TASK-009 synthetic verifier completion
- Final decision: For TASK-009 implementation tests only, use an explicit `task009_synthetic_smoke` verifier configuration.
- Decision date: 2026-06-25
- Required config behavior:
  - `normal_false_firing` split: `calibration_normal`
  - `validation_coverage` split: `validation`
  - test split: prohibited
  - `max_normal_false_fire_rate: 0.0`
  - `min_validation_coverage: 0.5`
  - `firing_overlap_jaccard_threshold: 0.8`
  - `min_calibration_support_count: 2`
  - `parameter_neighborhood_relative_tolerance: 0.0`
- Constraints:
  1. This policy is only a synthetic smoke-test implementation contract.
  2. It must not be used as a final SWaT verifier, rule-selection, or performance threshold without researcher approval.
  3. Reports must contain aggregate metrics and feedback codes only, not raw time-series rows.
  4. Final test data remains prohibited.
- Consequences for claims/evaluation: TASK-009 can validate deterministic verifier mechanics without deciding final research acceptance thresholds.

### DEC-013: TASK-010 synthetic-smoke runtime aggregation policy

- Status: resolved
- Owner: implementation agent
- Needed before: TASK-010 synthetic runtime completion
- Final decision: For TASK-010 implementation tests only, use an explicit `task010_synthetic_smoke` runtime configuration.
- Decision date: 2026-06-25
- Required config behavior:
  - source view: `canonical_rule_view`
  - severity mode: binary
  - binary severity: `1.0`
  - aggregate rule score: max fired-rule severity
  - alarm interval merge policy: merge overlapping or adjacent intervals within one sampling period
  - LLM calls, dynamic code execution, and test-data access: prohibited
- Constraints:
  1. This policy is only a synthetic smoke-test implementation contract.
  2. It must not be used as a final SWaT severity, scoring, or alarm-merge policy without researcher approval.
  3. Runtime explanations must be derived from rule AST fields and observed aggregate violation values.
  4. Runtime artifacts may contain row/timestamp ranges, but tracked reports must not contain reconstructive raw sequences.
- Consequences for claims/evaluation: TASK-010 can validate runtime determinism and provenance without deciding final alarm scoring semantics.

### DEC-014: Phase Gate B approval and TASK-012 LLM policy

- Status: resolved
- Owner: researcher
- Needed before: TASK-012
- Final decision: TASK-012 may start under a mock-only provider-neutral LLM planner scope.
- Decision date: 2026-06-25
- Approved scope:
  - `LLMProvider` protocol/interface,
  - `MockLLMProvider`,
  - provider-neutral request/response schemas,
  - prompt template assembly from approved aggregate evidence,
  - JSON DSL parsing,
  - schema validation,
  - provenance recording,
  - redaction checks,
  - tests proving invented variables, invented parameters, raw rows, and malformed DSL outputs are rejected.
- Not approved:
  - real provider calls,
  - network execution,
  - API key use,
  - raw data transfer,
  - LLM-based final rule approval,
  - runtime LLM execution,
  - TASK-013 refiner loop.
- Consequences for claims/evaluation: TASK-012 can validate planner plumbing and safety constraints only. It does not validate LLM value, final rule quality, or SWaT performance.

### DEC-015: TASK-012 provider scope

- Status: resolved
- Owner: researcher
- Needed before: TASK-012
- Alias from researcher decision: DEC-010 - Provider Scope
- Final decision: Use `MockLLMProvider` only for TASK-012 implementation and tests.
- Decision date: 2026-06-25
- Default provider config:
  - `provider.name: mock`
  - `provider.allow_network: false`
  - `provider.require_api_key: false`
  - `provider.temperature: 0`
- Optional real provider adapter skeletons may be added only in a future approved task if disabled by default, offline in CI, no API keys required, no network calls performed, and execution requires separate approval.
- Consequences for claims/evaluation: TASK-012 validates interfaces, parsing, safety, and provenance, not real LLM behavior.

### DEC-016: TASK-012 data-transfer policy

- Status: resolved
- Owner: researcher
- Needed before: TASK-012
- Alias from researcher decision: DEC-011 - Data Transfer Policy
- Final decision: Prompts may contain aggregate evidence only.
- Decision date: 2026-06-25
- Allowed prompt inputs:
  - variable names,
  - variable metadata,
  - candidate provenance,
  - relation profile summaries,
  - calibration IDs,
  - calibrated parameter values,
  - normal support counts,
  - allowed DSL predicates,
  - allowed rule families,
  - verifier feedback codes,
  - synthetic fixture summaries.
- Forbidden prompt inputs:
  - raw SWaT rows,
  - raw SWaT windows,
  - full time-series sequences,
  - downloadable derived SWaT samples,
  - final test intervals,
  - final test labels,
  - sealed test metrics,
  - any restricted data artifact that can reconstruct raw sequences.
- Consequences for claims/evaluation: LLM planning uses calibrated evidence summaries only.

### DEC-017: TASK-012 prompt and response retention policy

- Status: resolved
- Owner: researcher
- Needed before: TASK-012
- Alias from researcher decision: DEC-012 - Prompt and Response Retention Policy
- Final decision: Store prompt templates and hashes, but do not store full per-run prompts or raw provider responses by default.
- Decision date: 2026-06-25
- Allowed tracked fields:
  - prompt template file,
  - prompt template hash,
  - evidence hash,
  - request hash,
  - raw response hash,
  - redacted prompt summary,
  - redacted response summary,
  - parse status,
  - DSL schema version,
  - validation result,
  - provider metadata.
- Do not store by default:
  - full assembled prompt,
  - full raw LLM response,
  - raw evidence payload,
  - raw SWaT-derived sequence data.
- Debug exception: Full prompt/response capture requires separate explicit approval and must be local-only under an ignored directory such as `artifacts/private_llm_debug/`.
- Consequences for claims/evaluation: Reproducibility uses templates, hashes, schema versions, and redacted summaries without creating data-governance risk.

### DEC-018: TASK-012 reproducibility and provenance fields

- Status: resolved
- Owner: researcher
- Needed before: TASK-012
- Alias from researcher decision: DEC-013 - Reproducibility and Provenance Fields
- Final decision: TASK-012 artifacts must record provider, model, prompt, evidence, parser, schema, calibration, candidate, verifier, config, code, and network provenance.
- Decision date: 2026-06-25
- Required fields:
  - `provider_name`
  - `provider_type`
  - `model_or_deployment`
  - `api_version`
  - `temperature`
  - `seed`
  - `seed_supported`
  - `prompt_template_id`
  - `prompt_template_hash`
  - `evidence_hash`
  - `request_hash`
  - `raw_response_hash`
  - `redaction_status`
  - `parse_status`
  - `dsl_schema_version`
  - `allowed_rule_families`
  - `allowed_predicates`
  - `calibration_artifact_ids`
  - `candidate_artifact_ids`
  - `verifier_feedback_ids`
  - `config_hash`
  - `code_commit`
  - `created_at`
  - `network_allowed: false`
- Mock provider defaults:
  - `model_or_deployment: mock-llm-provider`
  - `api_version: none`
- Consequences for claims/evaluation: TASK-012 planner artifacts remain auditable before real provider approval.

### DEC-019: TASK-013 verifier-feedback refiner scope

- Status: resolved
- Owner: researcher
- Needed before: TASK-013
- Final decision: TASK-013 may start under a mock-only verifier-feedback refinement scope after TASK-012 approval.
- Decision date: 2026-06-25
- Approved scope:
  - implement a bounded verifier-feedback refiner loop,
  - use `MockLLMProvider` only,
  - consume structured deterministic verifier feedback codes,
  - re-plan candidate DSL JSON,
  - re-run JSON DSL parsing and `RuleSchemaRegistry` validation,
  - preserve deterministic verifier authority,
  - record iteration provenance,
  - stop after configured maximum iterations,
  - test safe failure modes.
- Not approved:
  - real provider calls,
  - network execution,
  - API key use,
  - raw SWaT rows/windows/sequences in prompts,
  - final test access,
  - runtime LLM,
  - LLM self-approval,
  - replacing the deterministic verifier,
  - benchmark or SWaT performance claims.
- Required implementation confirmations:
  - `planner_config_hash` is recorded separately from `provider_config_hash`.
  - Redaction tests reject `test_label`, `test_interval`, `normal.csv`, `attack.csv`, `merged.csv`, and timestamp-like raw payloads.
  - Refinement artifacts include explicit `max_iterations` and `stop_reason` fields.
  - Iteration provenance records `iteration_index`, `previous_rule_hash`, `verifier_feedback_ids`, `feedback_codes`, `revised_rule_hash`, `parse_status`, `schema_validation_status`, and `stop_reason`.
- Consequences for claims/evaluation: TASK-013 validates bounded feedback-loop mechanics only. It does not validate LLM value, SWaT performance, benchmark quality, or explanation quality.

### DEC-020: Phase Gate C and TASK-014 evaluation-harness scope

- Status: resolved
- Owner: researcher
- Needed before: TASK-014
- Final decision: TASK-013 is approved and Phase Gate C is approved as a mock-only synthetic feasibility review. TASK-014 may start only under a restricted evaluation-harness scope.
- Decision date: 2026-06-25
- Phase Gate C confirms:
  - template-only deterministic pipeline exists,
  - one-shot mock planner exists,
  - mock planner plus verifier-feedback loop exists,
  - loop mechanics are bounded and reproducible,
  - safety, redaction, and provenance checks are implemented.
- Approved TASK-014 scope:
  - implement evaluation report structure,
  - implement metric interfaces,
  - implement PA-free primary metric reporting,
  - implement supplementary point-adjusted metric support only if clearly labeled,
  - implement sealed-test access guards,
  - implement config-freezing checks,
  - implement provenance and manifest checks,
  - implement synthetic or toy fixture tests for evaluation code,
  - document final evaluation protocol requirements.
- Not approved:
  - opening sealed final test data,
  - running final SWaT benchmark evaluation,
  - using unverified local SWaT files for final claims,
  - tuning thresholds or K using final test labels,
  - reporting point-adjusted metrics as primary,
  - detector fusion as a headline result,
  - real LLM provider calls,
  - benchmark or thesis-result claims.
- Constraint while DEC-007 remains unresolved: TASK-014 must produce only evaluation harness code, documentation, configs, and synthetic tests.
- Consequences for claims/evaluation: TASK-014 can prepare reproducible evaluation machinery but cannot generate final SWaT claims until official provenance, terms, dataset edition/version, split protocol, sealed-test access policy, metric list, and Git-trackable artifact policy are resolved.

### DEC-021: TASK-015 official SWaT provenance resolution package scope

- Status: resolved
- Owner: researcher
- Needed before: TASK-015
- Final decision: DEC-007 precheck package is approved, but DEC-007 remains unresolved. TASK-015 may prepare the official SWaT provenance resolution package using the official iTrust request route as the preferred final-evaluation source.
- Decision date: 2026-06-25
- Approved TASK-015 scope:
  - prepare official iTrust request/approval record checklist,
  - record terms acknowledgement status,
  - define local-only official SWaT file manifest schema,
  - implement or document SHA-256 hashing procedure for approved local files,
  - record exact dataset edition/version/file names,
  - freeze final split protocol before opening sealed test,
  - freeze final metric protocol,
  - document allowed Git-tracked aggregate artifacts,
  - prepare sealed-test one-way execution log template.
- Not approved:
  - opening sealed final test,
  - running final SWaT benchmark,
  - using Kaggle/local CSV files for final claims,
  - changing thresholds, K, prompts, rules, or fusion weights after test access,
  - reporting point-adjusted metrics as primary,
  - committing raw rows, windows, raw sequence plots, or downloadable derived samples.
- DEC-007 resolution criteria:
  1. official source or explicitly approved alternative source is selected,
  2. terms are acknowledged,
  3. exact edition/version/file list is recorded,
  4. approved files are hashed locally,
  5. split protocol is frozen,
  6. metric protocol is frozen,
  7. sealed-test access policy is approved,
  8. Git artifact policy is approved.
- Consequences for claims/evaluation: Current local/Kaggle CSV files remain `local_unverified_smoke_test` and cannot be used for final SWaT performance claims.

### DEC-022: TASK-015A DEC-007 manifest tightening

- Status: resolved
- Owner: researcher
- Needed before: DEC-007 resolution
- Final decision: Tighten the official SWaT provenance manifest schema before DEC-007 can be marked resolved.
- Decision date: 2026-06-25
- Required changes:
  - track `terms_source_url`,
  - track `required_credit_statement`,
  - track `no_sharing_acknowledged`,
  - track `publication_notification_acknowledged`,
  - block DEC-007 readiness if no-sharing acknowledgement is false,
  - block DEC-007 readiness if publication notification acknowledgement is false,
  - block DEC-007 readiness if terms source URL is missing,
  - block DEC-007 readiness if required credit statement is missing.
- Source-route policy:
  - DEC-007 final primary benchmark resolution is official iTrust only.
  - Current local/Kaggle CSV files remain smoke-test-only.
- Not approved:
  - opening sealed final test,
  - running final SWaT benchmark,
  - reading, copying, or tracking raw SWaT data.
- Consequences for claims/evaluation: DEC-007 cannot be resolved with an alternative source for the final primary benchmark unless a future decision explicitly replaces this policy.

### DEC-023: TASK-016 Kaggle/local staging path

- Status: resolved
- Owner: researcher
- Needed before: TASK-016
- Final decision: Treat current local/Kaggle CSV files as `kaggle_mirror_staging` for implementation debugging only.
- Decision date: 2026-06-28
- Required behavior:
  - Use a separate `StagingSwatMirrorManifest`.
  - Do not use `OfficialSwatProvenanceManifest`.
  - Record `source_kind: kaggle_mirror` and `dataset_status: staging_only`.
  - Access local files through `SWAT_DATA_ROOT`.
  - Record file names, hashes, row counts, column names, label schema, timestamp/index columns, inferred sampling interval, and known limitations.
  - Include the required report statement: "This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim."
- Allowed:
  - schema inspection,
  - data loading,
  - column normalization,
  - metadata mapping,
  - staging-only smoke reports,
  - aggregate non-final metrics.
- Not approved:
  - resolving DEC-007,
  - opening official sealed final test,
  - final SWaT benchmark claims,
  - using Kaggle/local results as final thesis results,
  - committing raw rows, windows, plots, or redistributable derived samples,
  - tuning thresholds, K, prompts, or rules from staging performance without recording the run as exploratory.
- Consequences for claims/evaluation: TASK-016 can debug implementation paths with local/Kaggle files, but all outputs remain staging-only and non-final.

### DEC-024: TASK-017 single-source Kaggle staging dry-run

- Status: resolved
- Owner: researcher
- Needed before: TASK-017
- Final decision: Run the staging pipeline dry-run using exactly one declared staging timeline source, defaulting to `merged.csv`.
- Decision date: 2026-06-28
- Required behavior:
  - Use `SWAT_DATA_ROOT`.
  - Use `StagingSwatMirrorManifest`, not `OfficialSwatProvenanceManifest`.
  - Keep DEC-007 unresolved.
  - Do not combine `normal.csv`, `attack.csv`, and `merged.csv` into one timeline.
  - Allow `normal.csv` and `attack.csv` only for schema cross-checking unless separately configured.
  - Include the required report statement: "This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim."
- Allowed:
  - load `merged.csv` as a staging timeline,
  - normalize headers,
  - infer timestamp sampling,
  - build staging split manifest,
  - run metadata coverage,
  - run candidate discovery smoke,
  - run relation profiling smoke on a small predeclared subset,
  - run deterministic runtime on the staging validation split,
  - write aggregate staging artifacts and reports.
- Not approved:
  - final SWaT benchmark,
  - official sealed final test access,
  - DEC-007 resolution,
  - real provider or network calls,
  - runtime LLM,
  - point-adjusted primary metrics,
  - threshold/K/prompt/rule tuning from staging performance,
  - committing raw rows, windows, raw sequence plots, or downloadable derived samples.
- Consequences for claims/evaluation: TASK-017 may expose implementation issues and negative staging outcomes, but all results remain non-final debugging artifacts.

### DEC-025: TASK-018 support-aware Kaggle staging slice selection

- Status: resolved
- Owner: researcher
- Needed before: TASK-018
- Final decision: Find a support-aware Kaggle/local staging calibration slice using only aggregate transition support on predeclared actuator-sensor pairs.
- Decision date: 2026-06-28
- Required behavior:
  - Use `SWAT_DATA_ROOT`.
  - Use `merged.csv` as the only staging timeline source.
  - Use `StagingSwatMirrorManifest`, not `OfficialSwatProvenanceManifest`.
  - Keep DEC-007 unresolved.
  - Do not combine `normal.csv`, `attack.csv`, and `merged.csv`.
  - Do not use labels for support-based slice selection.
  - Define selection criteria in config before scanning.
  - Persist only aggregate support summaries and selected index ranges.
  - Include the required report statement: "This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim."
- Fixed selection policy:
  - minimum trigger count: 1,
  - minimum matched response count: 1,
  - maximum right-censored ratio: 0.5,
  - allowed source variables: `MV101`, `P101`, `P102`, `MV201`,
  - allowed target variables: `FIT101`, `LIT101`, `AIT201`, `AIT202`,
  - maximum slice length: 4096 rows,
  - search step: 512 rows,
  - labels policy: `ignored_for_selection_audit_only`,
  - require complete configured pipeline features,
  - require regular timestamp sampling.
- Not approved:
  - final SWaT benchmark,
  - official sealed final test access,
  - DEC-007 resolution,
  - threshold/K/prompt/rule tuning based on staging performance,
  - using attack labels for support-based slice selection,
  - committing raw rows, raw windows, raw sequence plots, or downloadable samples,
  - point-adjusted primary metrics,
  - real provider or network calls.
- Consequences for claims/evaluation: TASK-018 may identify a better staging slice for implementation debugging, but it remains non-final and cannot support benchmark or thesis performance claims.

### DEC-026: TASK-020 staging rule robustness and synthetic replay

- Status: resolved
- Owner: researcher
- Needed before: TASK-020
- Final decision: Assess TASK-018/TASK-019 staging verified rules with fixed support-aware slice scanning, sampled rule rebuild stability, and synthetic non-SWaT runtime replay.
- Decision date: 2026-06-29
- Required behavior:
  - Use `SWAT_DATA_ROOT`.
  - Use `merged.csv` as the only staging timeline source.
  - Use predeclared TASK-018 support-aware criteria.
  - Do not use labels for slice selection.
  - Do not select slices based on anomaly performance.
  - Compare rule IDs, calibration values, support counts, and verifier status across predeclared support-aware slices.
  - Use generated non-SWaT mini time-series for synthetic violation replay.
  - Include the required report statement: "This is a Kaggle/local staging run for implementation debugging only. It is not an official SWaT benchmark result and must not be used as a final thesis performance claim."
- Not approved:
  - final SWaT benchmark,
  - official sealed final test access,
  - DEC-007 resolution,
  - using Kaggle/local results as thesis final results,
  - threshold/K/prompt/rule/verifier tuning based on staging performance,
  - committing raw rows, raw windows, raw sequence plots, or downloadable samples,
  - real provider or network calls,
  - runtime LLM.
- Consequences for claims/evaluation: TASK-020 may support whether staging evidence candidates are worth keeping for further implementation review, but it remains non-final and cannot support benchmark or thesis performance claims.

## Open Decisions

### DEC-007: Official SWaT provenance upgrade

- Status: resolved for one approved TASK-026 API attempt
- Owner: researcher
- Needed before: final evaluation / TASK-014
- Question: When official SWaT files or confirmed Kaggle/iTrust provenance are available, what exact manifest and split policy replaces the local smoke-test manifest?
- Why it matters scientifically: Final claims require approved source, terms, edition/version, and split semantics.
- Options:
  1. Official iTrust files with documented edition and terms.
  2. Researcher-supplied Kaggle mirror with documented file list, edition/version, and terms.
  3. Continue using local smoke-test files only for non-claim implementation checks.
- Evidence available:
  - Current files are fingerprinted and marked `local_unverified_smoke_test`.
  - Researcher supplied the Kaggle page `https://www.kaggle.com/datasets/vishala28/swat-dataset-secure-water-treatment-system`.
  - Public iTrust dataset page confirms that SWaT is an available dataset and says dataset requests may take up to three working days.
  - Public iTrust request form includes SWaT and requires agreement to iTrust dataset terms.
  - Public iTrust terms require credit to iTrust/SUTD, publication notice to iTrust, and no dataset sharing.
  - Public iTrust summary lists SWaT `A1 & A2 Dec 2015` among available datasets.
  - DEC-022 sets the final primary benchmark source route to official iTrust only.
  - See `docs/DEC007_SWAT_PROVENANCE_PRECHECK.md`.
- Recommendation from implementation agent: Use the official iTrust request route as the required final primary benchmark source. Keep current local/Kaggle files smoke-test-only until an official request/approval record is recorded with terms acknowledgement, exact file list, hashes, edition/version, split protocol, sealed-test access policy, and allowed tracked artifacts.
- Final decision:
- Decision date:
- Consequences for claims/evaluation:

### DEC-027: ARGOS paper-code reproduction alignment

- Status: resolved for second approved TASK-026 API attempt
- Owner: researcher
- Needed before: any real ARGOS reproduction run / ARGOS_REPRODUCTION_GATE_B
- Question: Which ARGOS source path and safety model should be used for the first paper-faithful reproduction attempt?
- Why it matters scientifically: The paper emphasizes detector-plus-rule aggregation, but the pinned README documents only `train-LLM-only`, `train-LLM-only-parallel`, and `train-evolution`, while combined FN/FP code paths remain present but underdocumented. Running the wrong path would blur rule-only, detector-only, and detector-plus-rule claims.
- Evidence available:
  - ARGOS paper `https://arxiv.org/abs/2501.14170` describes training-time LLM rules, Detection/Repair/Review agents, top-k selection, and detector-plus-rule aggregation.
  - Local ARGOS reference is pinned at `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
  - TASK-023 fetched ARGOS upstream refs/tags and confirmed current upstream `origin/main` is `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
  - No ARGOS git tags were found during TASK-023.
  - ARGOS license is MIT.
  - Current ARGOS README documents `train-LLM-only`, `train-LLM-only-parallel`, and `train-evolution`.
  - Historical README docs at `5209273`, `c3c28af`, and `c03427f` document `Argos w/o Aggregator` and `Argos w/ Aggregator`, including a `train-combined-fp` example and a TODO for base-detector incorrect-example artifacts.
  - Current `driver.py` still exposes `train-combined-fn`, `train-combined-fp`, and `eval-combined`.
  - Current `common/common.py` implements combined label behavior with `np.maximum` for FN compensation and `np.minimum` for FP compensation.
  - Current `datasets/dataset.py`, `agent/prompts/detection.py`, `agent/prompts/review.py`, `agent/review_agent.py`, and `runtime/engine.py` contain combined-mode support.
  - TASK-023 added an offline mock-only harness under `experiments/argos_reproduction/`.
- Options:
  1. Start with current pinned commit rule-only reproduction, then separately audit combined mode.
  2. Use current pinned commit combined FN/FP paths as the first detector-plus-rule reproduction candidate.
  3. Fetch/inspect historical ARGOS commits or upstream release guidance before choosing a reproduction commit.
  4. Build a minimal paper-faithful adapter around the pinned combined paths to standardize base-detector outputs, artifacts, and run manifests.
- Not approved until resolved:
  - real LLM calls,
  - API key use,
  - execution of LLM-generated Python,
  - full ARGOS experiment,
  - changing the `paperworks` proposed-method pipeline,
  - benchmark or thesis performance claims.
- Recommendation from implementation agent: First fetch or otherwise inspect complete ARGOS history/release guidance, then run a rule-only reproduction before attempting detector-plus-rule aggregation. If combined mode is selected, define base-detector output artifacts and an isolated generated-Python sandbox before execution.
- Source-alignment subdecision:
  - Status: resolved for first rule-only reproduction stage
  - Decision date: 2026-07-13
  - `initial_reproduction_mode`: `train-LLM-only`
  - `initial_source_commit`: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
  - `combined_mode_status`: deferred
  - Best detector-plus-rule candidate for future audit: `c03427f`, because it is the latest inspected historical README commit retaining Aggregator-oriented documentation.
  - Minimal paper-faithful adapter: not approved now; build only if pinned combined paths cannot be executed reproducibly with explicit base-detector artifacts.
- Dataset subdecision:
  - Status: prepared for fixed-rule smoke in TASK-024; not approved for benchmark claims
  - Dataset: KPI public GitHub dataset from `https://github.com/NetManAIOps/KPI-Anomaly-Detection`
  - Initial package: `Finals_dataset/phase2_train.csv.zip` with Git blob SHA `f07375e9ec10789d9f473301734c9cb00e9b6279`; paired ground truth `Finals_dataset/phase2_ground_truth.hdf.zip` with Git blob SHA `41397b55ae955849357eb7006334f2c11a32bca6`
  - TASK-024 source repository commit: `d06bda15d511d930cbf4e6a6de14bd94d790f0f2`
  - TASK-024 selected KPI ID: `05f10d3a-239c-3bef-9bdc-a2feeb0037aa`
  - TASK-024 converted CSV SHA-256: `f6a6d834e23417da5cd0e87af227ae62f0c12a73f080afa08b08a2d332aa5d55`
  - TASK-024 package and converted CSV files remain under ignored `artifacts/` paths and are not tracked.
- Fixed-rule sandbox subdecision:
  - Status: fixed repository-owned mock rule smoke completed in TASK-024
  - Docker/Podman status in local run: unavailable; restricted subprocess fallback used
  - TASK-025 correction: restricted subprocess is not treated as a secure sandbox and does not claim network, repository-write, CPU, or memory isolation.
  - Actual LLM-generated Python execution: still not approved
  - Future requirement: approve and verify Docker/Podman sandbox before executing any actual LLM-generated Python.
- Prompt-capture subdecision:
  - Status: mock provider-gated prompt capture completed in TASK-025
  - Pinned prompt source: `external/argos/agent/prompts/detection.py::DETECTION_AGENT_V3_DEFAULT_PROMPT_TEMPLATE`
  - Chunk size source: pinned ARGOS `driver.py` and `runtime/engine.py` default `chunk_size=1000`
  - Selected prompt chunk: positions `[0, 1000)`, label counts `0=996`, `1=4`
  - Provider approval artifact: template only, `approved: false`
  - Real provider calls: still not approved
  - Generated Python execution: still not approved
- Final decision: DEC-027 remains open for real provider approval, actual LLM-generated Python execution approval, Docker/Podman sandbox run approval, detector-plus-rule execution approval, and benchmark/thesis claim approval.
- Decision date: 2026-07-13
- Consequences for claims/evaluation: First ARGOS reproduction may target only mock/offline or future approved rule-only `train-LLM-only` behavior at the pinned commit. Detector-plus-rule claims, real provider claims, generated-code execution claims, and benchmark claims remain prohibited.

### DEC-028: Initial ARGOS real-LLM capture provider

- Status: consumed_provider_error
- Owner: researcher
- Needed before: TASK-026 approved API capture
- Question: Which provider/model/budget can be used for exactly one frozen ARGOS `train-LLM-only` prompt response capture?
- Why it matters scientifically: TASK-026 is the first step that may contact a real provider. The provider, model/version, budget, retention, and approval owner must be explicit before any request is made.
- Required fields before resolution:
  - provider,
  - model,
  - model/version identifier,
  - temperature,
  - maximum calls: exactly `1`,
  - maximum input tokens,
  - maximum output tokens,
  - maximum cost,
  - credential environment variable names,
  - prompt/response retention policy,
  - approval owner,
  - approval date.
- Current approval artifact:
  `configs/argos_reproduction/task026_provider_approval.json`
- First approved configuration:
  - provider: `openai_responses`,
  - model: `gpt-oss-120b`,
  - model/version identifier: `gpt-oss-120b`,
  - temperature: `0`,
  - maximum calls: exactly `1`,
  - maximum input tokens: `20000`,
  - maximum output tokens: `2000`,
  - maximum cost: `1.0` USD,
  - credential environment variable name: `OPENAI_API_KEY`,
  - prompt/response retention: ignored private raw prompt/response, tracked hashes and redacted metadata only,
  - approval owner: `Hyuneey`,
  - approval date: `2026-07-13`.
- Execution outcome:
  - one API request was made,
  - provider returned HTTP `404`,
  - provider error: `Model not found gpt-oss-120b`,
  - no rule response text was captured,
  - generated Python was not executed,
  - no performance metric was computed.
- Second approved configuration:
  - provider: `openai_responses`,
  - model: `gpt-5.6-luna`,
  - model/version identifier: `gpt-5.6-luna`,
  - temperature: `0`,
  - maximum calls: exactly `1`,
  - maximum input tokens: `20000`,
  - maximum output tokens: `2000`,
  - maximum cost: `1.0` USD,
  - credential environment variable name: `OPENAI_API_KEY`,
  - prompt/response retention: ignored private raw prompt/response, tracked hashes and redacted metadata only,
  - approval owner: `Hyuneey`,
  - approval date: `2026-07-13`.
- Second attempt status:
  - one API request was made,
  - provider returned HTTP `400`,
  - provider error: `Unsupported parameter: 'temperature' is not supported with this model.`,
  - no rule response text was captured,
  - generated Python was not executed,
  - no performance metric was computed.
- API client policy:
  - TASK-026 currently supports only the explicit `openai_responses` route.
  - Unsupported provider names must block rather than being routed implicitly.
- Still not approved:
  - any additional provider call under TASK-026 without a separate approval update,
  - retries,
  - prompt tuning after seeing a response,
  - generated Python execution,
  - RepairAgent or ReviewAgent execution,
  - KPI benchmark evaluation,
  - detector-plus-rule mode,
  - benchmark or thesis claims.
- Final decision: Approve exactly one additional API request for TASK-026 using `gpt-5.6-luna`, after the first approved one-call attempt with `gpt-oss-120b` returned `Model not found`.
- Decision date: 2026-07-13
- Consequences for claims/evaluation: TASK-026 records two provider-error attempts, not a successful real LLM rule capture. Generated Python execution, performance metrics, retries, and benchmark claims remain prohibited. A further provider call requires a separate approval update.

### DEC-029: TASK-026R Luna compatibility-remediation capture

- Status: consumed_provider_error
- Owner: researcher
- Needed before: one TASK-026R API compatibility-remediation request
- Decision: Approve exactly one additional request using `openai_responses` and
  `gpt-5.6-luna`, with the `temperature` parameter omitted entirely.
- Approval artifact:
  `configs/argos_reproduction/task026r_provider_approval.json`
- Execution config:
  `configs/argos_reproduction/task026r_real_capture.json`
- Approval owner: `Hyuneey`
- Approval date: `2026-07-13`
- Maximum calls: exactly `1`
- Maximum input tokens: `20000`
- Maximum output tokens: `2000`
- Maximum cost: `1.0` USD
- Credential environment variable name: `OPENAI_API_KEY`
- Frozen request hash:
  `14af5d91248f3ca579a445527768264f148497d58d85b49b96b39b8873918aca`
- Scientific rationale: the second TASK-026 request was rejected during request
  validation because `gpt-5.6-luna` does not accept the submitted
  `temperature` parameter. TASK-026R changes only provider-request
  compatibility; it does not change the prompt, chunk, selection policy, or
  evaluation behavior.
- One-shot enforcement: the harness writes an ignored private call receipt
  before network execution and blocks the same config after any attempted
  request, including transport or provider failures.
- Still prohibited:
  - a second TASK-026R provider request,
  - response-driven prompt tuning,
  - execution of generated Python,
  - RepairAgent or ReviewAgent execution,
  - KPI performance evaluation,
  - detector-plus-rule mode,
  - SWaT access,
  - benchmark or thesis claims.
- Consequences for claims/evaluation: TASK-026R can establish only whether one
  frozen request yields a capturable, statically analyzable response. It cannot
  establish rule quality or anomaly-detection performance.
- Execution outcome:
  - one approved request was made,
  - `temperature` was omitted,
  - provider returned HTTP `429`,
  - provider error code: `insufficient_quota`,
  - no rule response was generated,
  - no generated Python was captured or executed,
  - no performance metric was computed,
  - the one-shot private receipt blocks another TASK-026R request.
- Final status: DEC-029 is consumed. Any later call after billing/quota repair
  requires a separate task and approval; this artifact must not be re-enabled.

### DEC-030: TASK-026Q post-quota-remediation capture

- Status: consumed_success
- Owner: researcher
- Needed before: one TASK-026Q API request after quota repair
- Decision: Approve exactly one request using `openai_responses` and
  `gpt-5.6-luna` after the researcher confirmed billing remediation.
- Approval artifact:
  `configs/argos_reproduction/task026q_provider_approval.json`
- Execution config:
  `configs/argos_reproduction/task026q_real_capture.json`
- Approval owner: `Hyuneey`
- Approval date: `2026-07-13`
- Maximum calls: exactly `1`
- Maximum input tokens: `20000`
- Maximum output tokens: `2000`
- Maximum cost: `1.0` USD
- Temperature parameter: omitted
- Frozen request hash:
  `14af5d91248f3ca579a445527768264f148497d58d85b49b96b39b8873918aca`
- Scientific rationale: this call changes only external billing/quota state.
  The prompt, chunk, model, token budget, selection policy, and static-analysis
  policy remain unchanged.
- Still prohibited:
  - a second TASK-026Q request,
  - response-driven prompt tuning,
  - execution of generated Python,
  - RepairAgent or ReviewAgent execution,
  - KPI performance evaluation,
  - detector-plus-rule mode,
  - SWaT access,
  - benchmark or thesis claims.
- Execution outcome:
  - one approved request was made,
  - provider returned HTTP `200`,
  - one response and one Python code fence were captured,
  - response hash:
    `f7a1241323c98b716c651dac797cd502c0fd2c7b3c2a7b6142f34e8bbb418810`,
  - rule hash:
    `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659`,
  - required `inference` signature was valid,
  - static safety checks passed,
  - generated Python was not executed,
  - no performance metric was computed.
- Final status: DEC-030 is consumed successfully. No additional TASK-026Q
  request is approved.

### DEC-031: Captured ARGOS rule container execution approval

- Status: open_not_approved
- Owner: researcher
- Needed before: any execution of the TASK-026Q captured rule
- Frozen rule hash:
  `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659`
- Current approval template:
  `configs/argos_reproduction/task027_captured_rule_execution_approval.template.json`
- Current approval value: `false`
- Current container preflight: `unavailable`
- Required decision:
  - explicitly approve exactly one synthetic non-KPI execution,
  - name Docker or Podman as the runtime,
  - record the immutable image digest,
  - preserve all TASK-027 static and runtime controls.
- Restricted subprocess fallback: prohibited for captured rules.
- KPI performance evaluation: prohibited by the current template.
- TASK-027 did not execute the rule and does not resolve DEC-031.
- TASK-028 environment precheck on `2026-07-14` found neither Docker nor
  Podman. The task stopped before activating a non-template approval artifact,
  preparing synthetic inputs, or accessing the private rule.
- TASK-028 launch attempts: `0`; approval-consumption count: `0`.
- DEC-031 therefore remains `open_not_approved` until a verified Docker or
  Podman runtime is available and TASK-028 is resumed under its one-shot gate.

### DEC-032: Windows container runtime remediation after TASK-028I

- Status: resolved_deferred_by_researcher
- Owner: researcher
- Selected runtime: Docker Desktop, per-user, WSL 2, Linux containers
- Installer verification: passed
- Installer version: `4.82.0.233772`
- Installer SHA-256:
  `a5b5837542f2f57fadbb09db90a60c84f8efc0a65f8d6dcd2e5b9fca3a2b87e6`
- Installation outcome: timed out without progress after `900` seconds.
- Selected option: `bounded_docker_cleanup_and_one_retry`
- Docker retry count allowed: `1`
- Podman fallback: deferred; it may be selected only after the clean Docker
  retry fails.
- Official uninstaller: attempted once with `uninstall`; it timed out after
  `300` seconds and removed registration and most program files.
- Bounded residual cleanup: completed for deletion-manifested TASK-028I and
  official-uninstaller paths only. Existing `Ubuntu-22.04` was preserved.
- Clean Docker retry: launched exactly once with `install --user`; no quiet or
  automatic license-acceptance flag was used.
- Docker installation decision: `deferred_by_researcher`
- Deferred until: `full_experiment_execution_phase`
- Installer retry consumed: true
- TASK-029 terminated the two remaining installer processes without relaunch.
- Remaining partial per-user Docker files are recorded as environment debt and
  were not deleted by TASK-029.
- Restart pending: false
- Podman fallback attempted: false
- Additional Docker retry allowed: false
- TASK-028 resume allowed: false
- Captured-rule execution allowed: false
- Required future action: create a new explicit environment decision during the
  full experiment execution phase. DEC-032 does not permit another Docker retry.
- Captured rule access/execution: false

### DEC-033: ARGOS non-executing audit closure and future execution order

- Status: resolved_non_executing_audit_complete
- Owner: researcher
- Pinned rule-only source:
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Historical Aggregator reference:
  `c03427f2ab16e377946d4c1176585156ddae7254`
- Confirmed without execution:
  - Detection, Repair, Review, validation selection, and iteration control flow;
  - LLM-written rule thresholds are distinct from label-aware evaluation
    thresholds;
  - FN fusion is elementwise maximum;
  - FP fusion is elementwise minimum;
  - the complete paper Aggregator path is not directly runnable from the pinned
    driver without explicit detector artifacts and a paper-faithful adapter.
- Initial future execution order: E1 rule runtime smoke, E2 rule-only validation,
  E3 frozen rule-only test, E4 detector baseline, E5/E6 fusion, E7/E8 agent
  effects, E9 seed sensitivity, then E10 multivariate readiness.
- Generated-code execution approval: not granted.
- ARGOS performance reproduction: not complete.
- Fusion superiority claim: prohibited until frozen experiments are run.
- TASK-029 changes the source audit and experiment protocol only; it does not
  resolve DEC-031 or permit TASK-028 resume.

### DEC-034: ARGOS-informed multivariate method contract

- Status: resolved_specification_frozen
- Owner: researcher
- Method representation: project-owned typed JSON DSL; arbitrary generated
  Python and free-form expression execution are prohibited.
- Candidate boundary: pre-scoring CandidateUniverse followed by graph ranking;
  no unregistered variables or candidate edges may be introduced.
- Evidence term: `anomaly-anchored evidence curation`.
- Relation registry: 14 versioned families; runtime additions require a schema
  version and separate decision.
- Numeric authority: deterministic calibration artifacts only; an LLM cannot
  approve values, confidence intervals, splits, or stability conclusions.
- Rule authority: deterministic verifier, non-overridable.
- Repair policy: maximum 3 iterations, one repeated violation allowed, terminate
  on no change, and immutable evidence/graph/value/test-boundary fields.
- Runtime: deterministic, LLM-free, accepted DSL only.
- Fusion: rule-only, detector-only, ARGOS FN union, ARGOS FP intersection,
  confidence-gated, and abstention-aware arms are predeclared without a
  superiority claim.
- Proposed-method primary metrics: PA-free precision, recall, point F1, range
  F1, event recall, and event precision. Point adjustment and ARGOS Event-PA
  are supplementary only.
- Test policy: one-way evaluation; no rule, parameter, threshold, candidate, or
  fusion selection after access.
- Current approval: specification and synthetic schema tests only.
- Not approved: method implementation, provider calls, dataset access,
  experiments, benchmark claims, or TASK-028 resume.

### DEC-035: Production JSON Schema validator

- Status: resolved_implemented
- Owner: researcher
- Approved dependency:
  - package: `jsonschema`
  - extra: `format-nongpl`
  - version: `4.26.0`
- Validator class: `jsonschema.validators.Draft202012Validator`.
- Schema meta-validation: enabled through `check_schema()`.
- Format validation: enabled and fail-closed for `date` and `date-time`.
- Structural role: validate TASK-030 JSON artifacts against Draft 2020-12
  schemas.
- Project-owned semantic role remains mandatory for cross-artifact references,
  units, graph endpoints, split provenance, relation compatibility, and
  status/hash consistency.
- Semantic validation owner: paperworks deterministic verifier.
- Semantic validation status: not implemented by TASK-032A.
- The TASK-030 fixture validator remains a limited synthetic helper and is not
  presented as a complete Draft 2020-12 implementation.
- Implementation boundary: structural registry and reports only; no v1 DSL,
  semantic verifier, runtime, migration conversion, provider, or dataset work.

### DEC-036: First TASK-030 contract implementation slice

- Status: resolved_scope_frozen
- Owner: researcher
- Selected relation family: `delayed_response`.
- Source/target: one binary actuator to one continuous sensor.
- Trigger: `state_changes_to`.
- Expected effect: delayed positive change.
- Violation: `missing_expected_response`.
- Output: binary anomaly.
- Allowed lag types: fixed and interval.
- Allowed window types: event-relative and persistence.
- Excluded: the other thirteen relation families, multi-source/target rules,
  streaming, free-form expressions, and causal claims.
- Consequence: this is the direct contract-compatible successor to Phase 1
  `changed_to`, `increase_within`, and `response_missing` semantics.
- TASK-032A preservation record: relation scope remained frozen; no v1
  delayed-response object was implemented.

### DEC-037: Legacy Phase 1 artifact compatibility

- Status: resolved_policy_frozen
- Owner: researcher
- Policy: deterministic explicit adapter.
- Legacy identifier: `minimal_rule_schema_v1`.
- Legacy status after v1 implementation: read-only; new legacy rule creation is
  prohibited.
- Silent or in-place conversion: prohibited.
- Required migration evidence: source hash, target hash, adapter version, field
  mappings, information-loss declaration, and migration report.
- Unsupported legacy artifact behavior: return
  `unsupported_legacy_artifact`; partial conversion is prohibited.
- Synthetic-smoke calibration records cannot be promoted to approved research
  parameters through migration.
- TASK-032A preservation record: only compatibility assessment was implemented;
  no target artifact, silent conversion, partial conversion, or parameter
  promotion occurred.

### DEC-038: Typed rule document authorization boundary

- Status: resolved_policy_frozen
- Owner: researcher
- Structural validation is not rule approval: true.
- Successful parsing is not rule approval: true.
- Serialized `status` is untrusted until deterministic verifier binding: true.
- Serialized `verified_rule_hash` is untrusted until deterministic verifier
  binding: true.
- TASK-032B rule runtime authorized: false.
- Runtime requires a TASK-032D verifier result: true; the verifier-result
  prerequisite is now implemented, while runtime binding remains deferred to
  TASK-032E.
- A parsed document carrying `status: accepted` receives no additional
  authority.
- The canonical document SHA-256 is a transport/reproducibility hash only and
  is not an accepted-rule hash.
- DEC-035 structural/semantic separation, DEC-036 delayed-response scope, and
  DEC-037 explicit non-silent migration policy remain unchanged.

### DEC-039: External contract artifact integrity and authority

- Status: resolved_policy_frozen
- Owner: researcher
- Structural validity is scientific approval: false.
- Artifact hashes provide integrity only: true.
- Adapter output is rule binding: false.
- Adapter output is verifier acceptance: false.
- Graph edges remain candidate relations: true.
- Causal claims from adapters: prohibited.
- Legacy parameter approval ceiling: `calibrated`.
- Synthetic-smoke parameter promotion: prohibited.
- Runtime authorized: false.

### DEC-040: Canonical external artifact self-hash policy

- Status: resolved_policy_frozen
- Owner: researcher
- Graph, evidence, and parameter hashes exclude only the top-level
  `artifact_hash` field.
- Nested hashes remain included.
- Encoding: UTF-8.
- Keys: sorted.
- ASCII escaping: enabled.
- NaN and infinity: prohibited.
- The policy is deterministic, input-preserving, and integrity-only.
- TASK-032B full-document rule transport hashing remains unchanged.

### DEC-041: Deterministic verification hash and authority binding

- Status: resolved_policy_frozen
- Owner: researcher
- Verification subject: canonical Rule v1 document excluding only top-level
  `status` and `verified_rule_hash`.
- Encoding: UTF-8, sorted keys, compact separators, ASCII escaping, finite JSON
  numbers, SHA-256.
- The TASK-032B full-document hash remains transport/integrity evidence only.
- Accepted materialization deep-copies the candidate, writes `accepted` and the
  verification-subject hash, and reparses through TASK-032B.
- Required binding: accepted-rule hash, verifier-result `rule_hash`, and
  verification-subject hash are identical.
- Verifier-result `artifact_hash` is a separate integrity self-hash.
- Candidate authority preclaims are prohibited.
- TASK-032D runtime authorization: false. TASK-032E binding remains required.

### DEC-042: Delayed-response parameter and lag-binding closure

- Status: resolved_policy_frozen
- Owner: researcher
- Added typed MVP support for `PARAM-SEVERITY-*` / `severity_boundary` without
  changing the canonical parameter schema.
- Phase 1 adapters may not generate severity parameters.
- Accepted rules require approved, stable lag, tolerance, duration, support,
  and severity records with matching provenance.
- Fixed lag binds to an approved `response_delay` value.
- Interval lag binds either to approved `lag_maximum` plus graph/evidence
  minima, or to an approved response-delay confidence interval.
- Milliseconds, seconds, and minutes are converted deterministically before
  comparison. A lone `lag_minimum` is insufficient.
- Severity support does not implement runtime severity calculation.

### DEC-043: Accepted-rule runtime authorization

- Status: resolved_policy_frozen
- Owner: researcher
- Only a successfully constructed `RuntimeAuthorizationBundleV1` exposes the
  non-serialized property `runtime_authorized: true`.
- Accepted rules, verifier results, artifact collections, and TASK-032D
  outcomes remain individually unauthorized.
- Authorization binds and rechecks the accepted rule hash, verifier-result ID
  and self-hash, verifier policy, graph/evidence hashes, exact parameter hashes,
  and verified reference sets.
- The receipt hash excludes only `authorization_hash`; `created_at` is supplied
  explicitly and runtime scope is `synthetic_only`.
- Receipt and verifier bindings are revalidated before every execution.

### DEC-044: Delayed-response MVP operational semantics

- Status: resolved_policy_frozen
- Owner: researcher
- Input: uniformly sampled one-source/one-target synthetic windows only.
- Trigger: transition into the configured state; none is evaluated normal,
  exactly one is evaluated, multiple or first-sample trigger abstains.
- Baseline: target immediately before trigger.
- Response: first target increase reaching approved tolerance inside the
  inclusive approved lag interval.
- Missing response: binary violation with score `1.0`; all other scores `0.0`.
- Persistence is a coverage requirement only. Severity and minimum support are
  bound context and do not alter runtime output.
- Abstention is not an anomaly.

### DEC-045: Deterministic explanation grounding

- Status: resolved_policy_frozen
- Owner: researcher
- Explanation inputs are limited to accepted rule, accepted verifier result,
  authorized runtime trace, bound artifact references, and window offsets.
- Raw arrays, new variables, new thresholds, causal claims, root-cause claims,
  and universal-invariant claims are prohibited.
- `lag.observed` remains null because the canonical trace does not carry a
  grounded observed numeric lag.
- Natural language uses deterministic bounded templates only.
- Detector and fusion results remain unavailable.

### DEC-046: Complete synthetic contract vertical slice

- Status: resolved_policy_frozen
- Owner: researcher
- Source scope: synthetic serialized artifacts only.
- Explicit graph, evidence, and non-severity parameter adapters are required.
- Rule generation is replaced by one predeclared candidate fixture.
- Twenty-stage verification and runtime authorization are mandatory.
- Runtime scope: `synthetic_only`.
- Deterministic full-pipeline replay is required.
- Raw arrays and performance metrics are prohibited in reports.
- Allowed claim: the complete delayed-response contract pipeline is connected
  and deterministically replayable on predeclared synthetic fixtures.
- No real-data, graph-quality, rule-generation, calibration, detection,
  explanation-usefulness, causal, method-completion, or thesis claim follows.

### DEC-047: Synthetic vertical-slice lineage ledger

- Status: resolved_policy_frozen
- Owner: researcher
- The ledger records hashes and status for Phase 1 sources, adapter inputs and
  outputs, candidate and accepted rules, verifier result, authorization
  receipt, runtime windows, traces, explanations, configuration, and pipeline
  version.
- Adapter-produced parameter authority remains capped at `calibrated` under
  DEC-039. TASK-032F binds those outputs to existing explicit TASK-032D
  approved synthetic records only after non-authority fields match exactly.
- Severity is loaded from an explicit canonical approved artifact and is never
  adapter-generated.
- Raw source/target arrays, dataset rows, provider prompts, generated Python,
  and host-private paths are prohibited.

### DEC-048: Full-experiment container runtime re-entry

- Status: resolved_bounded_reentry
- Owner: researcher
- Previous TASK-028 resume: prohibited
- Docker Desktop retry: prohibited
- Selected runtime: WSL-native rootless Podman
- Selected runtime version: `4.9.3`
- WSL distribution: dedicated Ubuntu 24.04.4 LTS, WSL 2
- WSL-native Docker Engine: not installed or selected
- Exactly one runtime selected: true
- Host generated-rule execution: prohibited
- Synthetic harmless-container smoke before rule access: required and passed
- Rootless, Linux-container, network-none, read-only-root, capability,
  no-new-privileges, CPU, memory, PID, timeout, and bounded-tmpfs controls were
  verified before the private rule was accessed.
- This is a new experiment-phase authorization and does not reopen or complete
  TASK-028.

### DEC-049: ARGOS E1 captured-rule runtime smoke

- Status: resolved_synthetic_container_only
- Owner: researcher
- Frozen rule SHA-256:
  `e4855fd898efecf5b8cd542c05e12af2153384634ab6201146c92d8fdf2e0659`
- Allowed input: repository-owned synthetic non-KPI arrays only
- Execution boundary: selected rootless Podman runtime only
- Host execution: prohibited
- In-container network: disabled
- Rule modification or regeneration: prohibited
- KPI, SWaT, WADI, and Kaggle access: prohibited
- Provider, RepairAgent, ReviewAgent, detector, and fusion execution: prohibited
- Performance metrics and benchmark claims: prohibited
- E1 result: `passed_runtime_smoke` for three required non-empty fixtures; the
  empty edge-case fixture also returned a valid deterministic empty output.
- Allowed claim: the frozen rule loaded and satisfied the declared runtime
  shape/domain/determinism contract on predeclared synthetic inputs.

### DEC-050: ARGOS E2 rule-only KPI validation

- Status: resolved_validation_only
- Owner: researcher
- Allowed: verify the frozen converted CSV identity, reproduce pinned split
  boundaries, parse train/validation prefix rows, execute the frozen rule on
  validation values, compute validation diagnostics, and freeze one
  validation-selected paper-faithful operating point.
- Prohibited: parse or execute the held-out test, compute test metrics, change
  or repair the rule, choose another KPI ID, call a provider or agent, or run a
  detector/fusion path.
- Pass/fail is protocol completion and contract validity; metric magnitude is
  not a pass criterion.
- E2 result: `passed_validation_feasibility` from clean execution commit
  `b81468c4da9eaa52596088e6b0768e11739c8072`.
- Two fresh validation-container runs produced the same prediction hash; no
  response-driven repair or rule change occurred.

### DEC-051: KPI chronological split and E3 test seal

- Status: resolved_split_frozen
- Owner: researcher
- Split source: pinned ARGOS `datasets/dataset.py` at commit
  `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`.
- Boundary algorithm: `train_pool_end = int(N * 0.7)`, then
  `train_end = int(train_pool_end * 0.8)`.
- Order: chronological; shuffle, sampling, purge, and gap are disabled for this
  reproduction.
- TASK-034 permits whole-file byte hashing and frozen manifest row count use,
  but its guarded reader stops at the validation end/test start.
- Separate competition ground-truth package access: prohibited.
- E3 status during TASK-034: `not_run`, `sealed_not_accessed`, and
  `not_authorized`.
- Frozen validation Event-F1-PA evaluator threshold:
  `2.6666666666666665`, with `smooth_labels(window_size=3)`.

### DEC-054: Expanded ARGOS KPI rule-generation cohort

- Status: resolved_pre_registered
- Owner: researcher
- Experiment: E2X-G
- Frozen design: 10 eligible KPI series, five deterministic anomaly anchors
  per KPI, two independent one-shot identical requests per anchor, 100 slots.
- Agent path: DetectionAgent V3 prompt only; previous-rule history absent.
- RepairAgent, ReviewAgent, mutation, response-based prompt changes, inner
  selection, outer validation, sealed test, and performance metrics are
  prohibited.
- Allowed claim is limited to generation and audit of the pre-registered
  multi-KPI, multi-anchor, replicated one-shot rule cohort.

### DEC-055: Bounded TASK-035A provider execution

- Status: resolved_exact_slot_budget
- Owner: researcher
- Provider/model: OpenAI Responses API / `gpt-5.6-luna`
- Maximum requests: 100 total and one per frozen slot.
- Maximum tokens: 20,000 input and 2,000 output per call; declared maxima of
  2,000,000 input and 200,000 output tokens in total.
- Temperature and seed are not sent.
- Every attempt consumes its slot after a private receipt is persisted.
- Automatic retry, manual replacement, provider/model switching, repair,
  review, and response-driven prompt tuning are prohibited.
- A global credential, permission, model, quota, billing, or provider-wide
  block stops the sequence and leaves remaining slots explicitly unattempted.
- Execution result: all 100 slots were consumed exactly once; 84 non-empty
  responses were captured with zero provider or transport errors. No retry,
  repair, review, provider switch, or model switch occurred.
- Cohort result: 61 rules passed static checks and 55 passed the isolated
  runtime output contract. The frozen adequacy result is
  `insufficient_rule_yield`; TASK-035B is not authorized by this decision.

### DEC-056: TASK-035A provider-output yield diagnosis

- Status: resolved_before_remediation
- Owner: researcher
- Frozen counts: 100 registered slots, 84 non-empty responses, 16 empty
  visible responses, 61 extracted rules, and 55 runtime-executable rules.
- Provider and transport errors: zero.
- Primary diagnosed mode: `max_output_tokens = 2000`, reasoning tokens equal
  2,000, and no visible response.
- Secondary mode: visible response without one extractable Python rule.
- Tertiary mode: statically valid rule with isolated runtime failure.
- The diagnosis excludes KPI validation, outer validation, test data, and all
  anomaly-performance evidence.

### DEC-057: Balanced output-budget remediation cohort

- Status: resolved_pre_registered
- Owner: researcher
- Design: the same 10 KPIs and 50 anchors, with new replicate IDs 3 and 4,
  producing exactly 100 new balanced slots.
- Provider/model remain OpenAI Responses API / `gpt-5.6-luna`.
- Prompt, chunk, anchor, extraction, static-audit, and container policies are
  frozen unchanged from TASK-035A.
- The sole generation change is `max_output_tokens: 6000`; temperature and
  seed remain omitted and no reasoning parameter is added.
- Exactly one request is allowed per new slot, with no automatic or manual
  retry. All anchors receive two calls regardless of prior outcome.
- TASK-035A remains immutable and `insufficient_rule_yield`.
- Only the frozen combined adequacy gate may authorize TASK-035B.
- Execution result: all 100 remediation requests completed once with zero
  provider or transport errors. All 100 responses were non-empty and produced
  one static-valid rule; 91 rules passed the isolated runtime contract.
- Combined result: 146 executable rules, minimum 12 executable and 12 distinct
  rules per KPI, all 10 KPIs at 10 or more executable rules, and 48 anchors at
  two or more executable rules.
- Gate result: `passed_balanced_generation_cohort`; TASK-035B may start only
  under a separately frozen selection/evaluation scope.

### DEC-058: Balanced primary candidate panel

- Status: resolved_before_metric_access
- Owner: researcher
- Exactly ten full-inner-executable rules are selected per KPI without labels or performance metrics.
- Selection groups by frozen anchor, sorts by rule SHA-256, and performs frozen-anchor round-robin passes.
- All 146 cohort rules must first pass the values-only full-inner runtime gate; fewer than ten eligible rules for any KPI stops before labels.

### DEC-059: Direct PA-free validation metrics

- Status: resolved_before_inner_metrics
- Owner: researcher
- Point and event metrics use direct binary outputs without smoothing, point adjustment, or label-optimized thresholds.
- Events are maximal contiguous positive runs and use deterministic maximum-cardinality one-to-one overlap matching.
- Undefined precision, recall, and F1 are zero.

### DEC-060: Frozen inner-selection arms

- Status: resolved_before_inner_metrics
- Owner: researcher
- Exactly four arms are selected on inner data: Best-1, Top-3 OR, Coverage-3 OR, and All-10 OR.
- Coverage-3 uses the predeclared greedy event-coverage and metric tie policy.
- No weighted vote, majority vote, post-hoc arm, or outer-based change is allowed.
- Execution result: all four arms were frozen for ten KPIs before outer access;
  all 100 panel rules replayed deterministically on outer validation.
- Primary comparison result: Coverage-3 OR increased macro recall but reduced
  macro point F1 and precision and substantially increased false positives.
  No superiority claim is authorized.

### DEC-061: ARGOS KPI base-detector identity

- Status: resolved_by_source_audit
- Identity status: `detector_family_recovered_variant_ambiguous`
- The ARGOS paper and repository identify generic LSTMAD for KPI but do not
  identify EasyTSAD `LSTMADalpha` versus `LSTMADbeta`, the winning config, or
  the training schema.
- EasyTSAD `0.2.0.2` commit `55eff2c6d62f9c792bf6253c046dcc04636efe5a`
  is the time-bounded closest official source, not a claimed exact ARGOS lock.

### DEC-062: Non-performance detector variant policy

- Status: resolved_before_detector_execution
- Both `LSTMADalpha` and `LSTMADbeta` are frozen as co-primary
  `paper_aligned_family_sensitivity` arms.
- Selection, headline-winner selection, or arm removal based on inner, outer,
  or test performance is prohibited.
- TASK-037B execution remains separately gated.

### DEC-063: Detector split and training-label policy

- Status: resolved_before_real_detector_run
- Generation fits detector and normalization; inner may select the threshold
  but not hyperparameters or variants; outer is one-way; test remains sealed.
- `contaminated_training` is frozen because the official EasyTSAD LSTMAD path
  uses training values without label filtering. Switching policies after
  results is prohibited.

### DEC-064: Detector threshold and metric policy

- Status: resolved_before_real_detector_run
- Primary threshold: unique finite inner scores maximizing direct PA-free point
  F1, tied by highest threshold then stable original order.
- Primary metrics are PA-free point/event metrics plus AUROC/AUPRC. EasyTSAD or
  ARGOS point-adjusted metrics are supplementary only.
- Outer/test labels cannot select detector thresholds.

### DEC-065: Dual-arm LSTMAD detector-only execution

- Status: resolved_before_real_training
- Owner: researcher
- Exactly ten frozen KPI series are authorized for `LSTMADalpha` and
  `LSTMADbeta` under seed `20260723`, producing twenty execution units.
- Both arms use official EasyTSAD defaults, the project-owned closest-
  reproducible `naive` schema, generation-only fit/normalization,
  `contaminated_training`, and the frozen inner threshold protocol.
- Detector-family substitution, hyperparameter search, KPI replacement,
  variant selection, outer tuning and headline-winner selection are prohibited.
- E4 execution does not authorize E5/E6, fusion, provider/agent activity, or
  sealed-test access.

### DEC-066: Exhaustive frozen diagnostic fusion matrix

- Status: resolved_before_fusion_metric_access
- Owner: researcher
- Exactly two detector variants, four frozen rule arms, and two binary
  operators form sixteen diagnostic arms.
- `fn_union_max` is elementwise maximum and `fp_intersection_min` is
  elementwise minimum.
- Fusion-arm, detector-variant, rule-arm, headline-winner, and outer-based
  configuration selection are prohibited.
- All inner and outer fusion prediction hashes must be frozen before outer
  labels are loaded.
- TASK-037C is generic-rule complementarity diagnostics, not paper-faithful
  error-conditioned ARGOS rule generation or full Aggregator reproduction.

### DEC-067: Detector-error-conditioned FN/FP rule cohort

- Status: resolved_before_target_or_prompt_inspection
- Owner: researcher
- Both frozen LSTMAD variants and all ten KPI series are retained.
- FN and FP are audited independently for all forty potential cells.
- Each eligible cell may contribute at most three distinct generation-only
  target chunks, with one one-shot provider request per target.
- The exact request count is frozen after support analysis and before provider
  execution, with an absolute upper bound of 120.
- RepairAgent, ReviewAgent, previous-rule history, retry, replacement
  generation, inner/outer evaluation, fusion and sealed-test access are
  prohibited.

### DEC-068: TASK-037D bounded provider authorization

- Status: resolved_executed
- Owner: researcher
- Provider/model: OpenAI Responses API / `gpt-5.6-luna`.
- `max_output_tokens` is 6,000; temperature and seed are omitted and no
  reasoning parameter is added.
- The exact request count and total declared token budgets must equal the
  frozen eligible-slot manifest and may not exceed 120 calls, 20,000 input
  tokens per call or 6,000 output tokens per call.
- Each private receipt permanently consumes one slot. Automatic retry, manual
  retry and replacement generation are prohibited.
- Execution consumed all 96 frozen slots exactly once with no provider or
  transport error and no retry or replacement call.

### DEC-069: Error-conditioned FN/FP rule selection

- Status: resolved_before_inner_metric_access
- Owner: researcher
- Selection unit: one detector variant, one KPI, and one direction.
- Every unit contains all matching TASK-037D executable rules plus one explicit
  no-op candidate.
- At most one FN and one FP rule may be selected per detector/KPI. FN and FP
  selection are independent; joint pair search and within-direction ensembles
  are prohibited.
- FN ranking: point F1, event F1, FN recovery, added FP/10k, added false-alarm
  events, then rule hash.
- FP ranking: point F1, event F1, FP removal, retained TP points, retained true
  events, then rule hash.
- Exact complete ties with no-op resolve to no-op.
- The decision is frozen before inner label access and cannot change from
  outer results.
- Execution outcome: all 83 candidate rules completed deterministic inner
  replay. The frozen selections retained 19 FN rules and one FN no-op, plus two
  FP rules and 18 FP no-ops. No joint FN/FP search or outer reselection was
  performed.

### DEC-070: ARGOS Repair/Review factorial design

- Status: resolved_before_agent_execution
- Owner: researcher
- The complete immutable TASK-037D population of 96 initial slots is expanded
  into exactly four logical branches per slot: `A0` one-shot, `A1` Repair-only,
  `A2` Review-only, and `A3` Repair plus Review.
- A new DetectionAgent rule is prohibited. Every branch retains the same
  initial rule hash, detector variant, KPI, FN/FP direction, and target/contrast
  lineage.
- One Repair transformation is shared by `A1` and `A3` for each initially
  runtime-failed rule. Initially executable `A1` branches are identity
  branches, and non-executable `A2` branches cannot invoke Review.
- Harmful or invalid Review results remain the terminal branch output and
  cannot be silently replaced by the pre-review rule.

### DEC-071: Leakage-corrected ReviewAgent boundary

- Status: resolved_before_agent_execution
- Owner: researcher
- Review is permitted only for executable rules and uses the matching frozen
  TASK-037B detector prediction plus direct PA-free metrics on the inner split.
- A Review provider call is authorized only when the current FN-max or FP-min
  combined inner point F1 is below the detector-only inner point F1.
- Review may receive at most three chronological, non-overlapping inner
  regression windows of at most 20 points each. Outer values, outer labels,
  sealed-test artifacts, other KPI data, and other detector-variant data are
  prohibited.
- Future outer execution requires a separately committed branch-selection
  freeze. TASK-038A performs no real Review or metric computation.

### DEC-072: Bounded agent provider and execution safety

- Status: resolved_protocol_frozen
- Owner: researcher
- Provider/model are frozen as OpenAI Responses API / `gpt-5.6-luna`, with
  `max_output_tokens=6000`, omitted temperature and seed, one revision per
  eligible transformation, and no retry or replacement generation.
- The maximum logical primary-study budget is 192 unique calls: 13 Repair,
  83 `A2` Review, 83 initially executable `A3` Review, and 13 post-repair
  `A3` Review calls. The exact future eligible-call manifest must be frozen
  before any provider execution.
- Generated or revised Python may execute only in the established WSL-native
  rootless Podman boundary with no network, non-root execution, read-only root,
  dropped capabilities, no new privileges, and bounded CPU, memory, PIDs, and
  time.
- TASK-038A authorizes zero real provider calls, zero real Repair executions,
  zero real Review executions, no host generated-code execution, no outer
  access, and no sealed-test access.

### DEC-073: Bounded RepairAgent operability execution

- Status: resolved_before_provider_execution
- Owner: researcher
- The complete Repair denominator is the thirteen TASK-037D static-valid
  runtime failures frozen by TASK-038A.
- Every initial failure is replayed twice in the unchanged rootless-container
  boundary before request construction. Only reproducibly failed rules receive
  a call slot; non-reproducible failures remain in the primary denominator.
- Provider/model are OpenAI Responses API / `gpt-5.6-luna`, with
  `max_output_tokens=6000`, omitted temperature and provider seed, at most one
  call per initial rule, and no automatic retry, manual retry, or replacement.
- The exact call count, bounded above by thirteen, must be committed before any
  provider access. Every attempted call is receipt-first and permanently
  consumes its slot.
- Returned rules require extraction, frozen static audit, and two fresh
  target plus two fresh contrast container executions. Generated source is
  never imported or executed on the host.
- ReviewAgent calls, inner labels or metrics, outer access, fusion, and sealed
  test are prohibited.

### DEC-074: Bounded leakage-corrected ReviewAgent inner execution

- Status: resolved_before_inner_label_access
- Owner: researcher
- The frozen population is 83 executable `A2` parents, 13 non-applicable `A2`
  records and 96 executable `A3` parents. The 179 executable logical branch
  parents bind to 96 unique executable rules.
- Every parent prediction must be hash-verified or replayed deterministically
  and frozen before inner labels are loaded.
- FN parents compose with the detector by binary maximum; FP parents compose
  by binary minimum. Review is authorized only when the direct PA-free
  combined inner point F1 is below the matching detector-only point F1.
- Provider/model are OpenAI Responses API / `gpt-5.6-luna`, with
  `max_output_tokens=6000`, omitted temperature and seed, at most one call per
  triggered `A2` or `A3` branch, and no retry or replacement.
- Regression evidence is limited to three chronological, non-overlapping inner
  windows of at most 20 points. Outer and sealed-test artifacts are prohibited.
- `A2` and `A3` are independent Review transformations even when their prompt
  payloads match. Their initially executable subgroup measures generation
  variability, not a Repair effect.
- Every revision requires extraction, static audit, generation target and
  contrast replay, and deterministic full-inner replay. Invalid or harmful
  revisions cannot revert to their parent.
- RepairAgent and DetectionAgent calls, branch selection, outer access,
  sealed-test access and host generated-code execution are prohibited.
- Execution outcome: 77 of 179 executable logical parents required Review and
  102 were frozen as `no_review_needed`. All 77 one-shot calls returned a
  static-valid rule; 76 revisions passed deterministic generation and
  full-inner runtime. No retry, replacement, RepairAgent call, DetectionAgent
  call, outer access or sealed-test access occurred.
