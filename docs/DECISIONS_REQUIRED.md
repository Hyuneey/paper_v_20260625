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

- Status: open
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

- Status: open
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
  - Actual LLM-generated Python execution: still not approved
  - Future requirement: approve and verify Docker/Podman sandbox before executing any actual LLM-generated Python.
- Final decision: DEC-027 remains open for real provider approval, actual LLM-generated Python execution approval, Docker/Podman sandbox run approval, detector-plus-rule execution approval, and benchmark/thesis claim approval.
- Decision date: 2026-07-13
- Consequences for claims/evaluation: First ARGOS reproduction may target only mock/offline or future approved rule-only `train-LLM-only` behavior at the pinned commit. Detector-plus-rule claims, real provider claims, generated-code execution claims, and benchmark claims remain prohibited.
