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
- Evidence available: Current files are fingerprinted and marked `local_unverified_smoke_test`; researcher supplied the Kaggle page `https://www.kaggle.com/datasets/vishala28/swat-dataset-secure-water-treatment-system`.
- Recommendation from implementation agent: Keep current files smoke-test-only until Kaggle terms, file list, and split semantics are confirmed.
- Final decision:
- Decision date:
- Consequences for claims/evaluation:
