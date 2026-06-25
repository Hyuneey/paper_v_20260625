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
