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

### DEC-008: Candidate feasibility gate criteria

- Status: open
- Owner: researcher
- Needed before: TASK-005 / Phase Gate A
- Question: What pre-registered candidate recall, stability, and coverage criteria are sufficient to proceed from candidate extraction to relation profiling?
- Why it matters scientifically: A pass threshold must not be invented after seeing candidate results. The decision affects whether GDN/candidate-universe outputs justify downstream profiling.
- Options:
  1. Require only deterministic reproducibility and mask correctness for the first feasibility pass.
  2. Require minimum stability across seeds/K plus coverage of a small pre-registered relation checklist.
  3. Require a stricter benchmark-style candidate recall protocol after official SWaT provenance is confirmed.
- Evidence available: TASK-003 implements deterministic candidate masks and explicit empty-target reports, but has not run a real SWaT candidate feasibility study.
- Recommendation from implementation agent: Use option 2 for TASK-005 if the researcher can pre-register the relation checklist without using test outcomes; otherwise use option 1 for smoke-test feasibility only and label it non-claim.
- Final decision:
- Decision date:
- Consequences for claims/evaluation:

### DEC-009: Real-data candidate policy for statistical and fallback origins

- Status: open
- Owner: researcher
- Needed before: enabling statistical or fallback origins on SWaT smoke runs
- Question: Should TASK-003/TASK-004 real-data runs enable normal-only statistical candidates, configured fallback candidates, or metadata-domain candidates only?
- Why it matters scientifically: Statistical Top-M, lag range, and fallback minimum count change the candidate search space and downstream GDN mask. These must be configured before inspecting results that could influence claims.
- Options:
  1. Metadata same-stage only for the first smoke run.
  2. Metadata same-stage plus normal-only statistical Top-M with pre-registered `M` and max lag.
  3. Metadata plus configured type-compatible fallback for empty targets only.
- Evidence available: TASK-003 implements all three mechanisms with synthetic tests. `configs/candidates/swat_candidate_policy.json` defaults to option 1.
- Recommendation from implementation agent: Keep option 1 as the default until TASK-004 GDN mask enforcement is stable; then approve option 2 for a labeled smoke run if needed.
- Final decision:
- Decision date:
- Consequences for claims/evaluation:
