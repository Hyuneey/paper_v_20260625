# AGENTS.md

## 1. Project mission

This repository implements a feasibility-first research prototype for:

> **Graph-guided, training-time agentic verified rule construction for explainable multivariate time-series anomaly detection.**

The system should:

1. discover plausible variable-pair candidates from normal multivariate time-series data,
2. profile their normal temporal relations,
3. construct executable rules,
4. verify those rules deterministically, and
5. execute only verified rules at runtime without calling an LLM.

The central contribution is **training-time agentic verified rule construction**, not a new state-of-the-art detector.

---

## 2. Reviewed external references

The following upstream projects are references, not drop-in dependencies:

- ARGOS: `https://github.com/microsoft/ARGOS`
  - reviewed snapshot: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
  - license: MIT
  - intended reuse: agent-loop architecture, rule-generation concepts, repair/review workflow
- GDN: `https://github.com/d-ailin/GDN`
  - reviewed snapshot: `9853899da860682669a134e4af315d036aab4eca`
  - license: MIT
  - intended reuse: model architecture and relation-candidate idea
- SWaT:
  - preferred source: official iTrust request/download
  - optional local mirror under review: Kaggle URL supplied by the researcher

TASK-000 must verify and pin exact upstream commits before any code reuse. Do not track a moving `main` branch in reproducibility records.

## Upstream repositories

- `external/argos` and `external/gdn` are read-only references.
- Never edit, commit, format, or run automatic migrations inside them.
- Do not import upstream packages directly into production code unless a task
  explicitly approves it.
- Record inspected upstream files and commit SHAs in
  `docs/UPSTREAM_SOURCES.md`.
- Reimplement only the approved minimal interfaces under `src/`.

---

## 3. Current implementation scope

Unless a task explicitly expands scope, the current milestone supports only:

- dataset: **SWaT**
- relation-learning source: normal data only
- initial relation type: **binary actuator → continuous sensor**
- candidate discovery: metadata/statistical universe + GDN Top-K relations
- relation profile: trigger events, response delay, response magnitude
- minimal DSL:
  - `changed_to`
  - `increase_within`
  - `response_missing`
- construction order:
  1. deterministic template baseline,
  2. deterministic verifier,
  3. runtime rule engine,
  4. LLM planner only after the deterministic path passes its gate
- runtime: **LLM-free**

### Out of scope unless explicitly requested

- WADI support
- full DyGraphAD implementation
- causal discovery or root-cause proof
- broad multi-type DSL coverage
- composite rule synthesis
- production deployment
- online retraining
- detector fusion before deterministic feasibility is proven

---

## 4. Research invariants

These rules are non-negotiable.

### 4.1 No test leakage

- Never use held-out test attack labels, intervals, outcomes, or plots for:
  - candidate discovery,
  - model training,
  - preprocessing choice,
  - relation profiling,
  - calibration,
  - rule generation,
  - rule refinement,
  - threshold selection,
  - checkpoint selection,
  - verifier tuning, or
  - hyperparameter selection.
- The final test split is evaluation-only.

### 4.2 GDN relations are candidates, not causes

- Never label a GDN edge as causal, physical ground truth, or root cause.
- Use `candidate relation`, `predictive relation`, or `data-guided pair`.

### 4.3 LLM authority is constrained

- An LLM may use only the supplied candidate variables.
- An LLM may not invent or modify `Delta t`, thresholds, durations, or magnitudes.
- Numeric rule parameters must reference normal-data calibration artifacts.
- An LLM may not approve its own rule.

### 4.4 Runtime must be LLM-free

- Runtime detection and explanation execute deterministic verified DSL rules only.
- Runtime packages must not import LLM providers or planning modules.

### 4.5 Synthetic anomalies are auxiliary only

- Synthetic violations may be used for stress testing or auxiliary validation.
- They must not be final test data.
- They must not be exposed as a hidden answer that an LLM can copy.

### 4.6 Reproducibility is mandatory

Store:

- random seeds,
- config snapshots,
- split manifests,
- code commit,
- data fingerprints,
- upstream source revisions,
- package versions,
- artifact provenance.

### 4.7 No hard-coded scientific conclusions

- Do not hard-code SWaT relation pairs in library logic.
- Explicit pairs are allowed only in clearly labeled tests, examples, or pre-registered evaluation sets.

### 4.8 Do not silently decide research questions

- Record alternatives and required decisions in `docs/DECISIONS_REQUIRED.md`.
- Stop when a decision materially changes a scientific claim or evaluation protocol.

### 4.9 Do not weaken tests

- Never delete, skip, or relax relevant tests merely to make code pass.

---

## 5. SWaT data-governance policy

SWaT data is user-provided, local-only research data.

### 5.1 Storage rules

- Never commit raw SWaT files.
- Never commit extracted real rows, real windows, or redistributable derived copies.
- Do not use Git LFS, GitHub Releases, Actions artifacts, PR attachments, or issue attachments for SWaT data.
- Do not embed raw SWaT sequences in prompts, logs, screenshots, test fixtures, or reports committed to Git.
- Access SWaT through a local path such as `SWAT_DATA_ROOT`.
- CI must use synthetic fixtures only.

### 5.2 What may be committed

- schemas,
- metadata templates,
- preprocessing configs,
- file hashes,
- aggregate statistics,
- experiment configs,
- aggregate metrics,
- non-reconstructive plots approved by the researcher.

### 5.3 Dataset manifest requirements

Every SWaT run must record:

- source kind: official iTrust / Kaggle mirror / other,
- source URL or request reference,
- dataset edition,
- normal-data version if known,
- local filenames,
- SHA-256 hashes,
- feature count and names hash,
- timestamp column and format,
- sampling interval,
- label column and label encoding,
- preprocessing steps,
- terms-of-use acknowledgement,
- manifest schema version.

If edition or version cannot be verified, mark it `unverified`; do not infer silently.

---

## 6. Data-view and split policy

This project enforces **split-before-windowing** and uses a versioned `CandidateUniverse` artifact downstream.

### 6.1 Canonical views

Maintain separate views when needed:

1. **canonical rule view**
   - highest approved time resolution,
   - used for response-delay profiling, calibration, verification, and runtime rule execution.
2. **optional GDN view**
   - may be downsampled for GDN training,
   - used only for candidate extraction.

Every artifact must include:

- `source_view`,
- `sampling_period_seconds`,
- aggregation method, if any,
- upstream manifest ID.

Do not calibrate second-level temporal rules from an implicitly downsampled GDN view.

### 6.2 Split-before-windowing

Always split the raw timeline before generating sliding windows.

```text
raw timeline
→ train/calibration/validation/test ranges
→ purge boundary context
→ generate windows independently within each split
```

The purge gap must be at least `window_size - 1`; add maximum supported lag when necessary.

### 6.3 Split roles

| Split | Permitted use |
|---|---|
| `train_normal` | GDN or candidate learner training |
| `calibration_normal` | relation profiling and numeric calibration |
| `validation` | deterministic verification and refinement feedback |
| `test` | final evaluation only |

Any API receiving a split must validate its permitted use.

---

## 7. GDN adaptation policy

The upstream GDN repository targets a legacy stack. Do not add the original PyTorch 1.5.1 / PyG 1.5.0 environment as the main project dependency unless explicitly approved.

### 7.1 Preferred strategy

- Implement a minimal modern PyTorch/PyG port of the required GDN components.
- Keep upstream code as a pinned reference.
- Add parity or behavioral tests on synthetic data.

### 7.2 Candidate-universe enforcement

The upstream implementation computes Top-K over a full embedding similarity matrix. This project must explicitly:

1. apply the approved `C_i` mask before Top-K,
2. exclude target `i` from persisted candidate relations,
3. handle empty candidate sets explicitly,
4. distinguish candidate edges from self-loops added only for message passing,
5. assert that every exported edge belongs to `C_i`.

### 7.3 Upstream evaluation code is not authoritative

- Do not reuse `report=best`, test-label threshold selection, or test-tuned checkpoint logic.
- Do not tune K, windows, thresholds, or preprocessing on final test labels.
- Do not reuse upstream train/validation window splitting if windows can overlap across boundaries.

---

## 8. ARGOS adaptation and code-execution safety

ARGOS is a structural reference, not the project runtime.

### 8.1 Reuse conceptually

- Detection/Planning Agent idea,
- Repair/Refiner idea,
- Review/Verifier loop,
- training-time LLM and runtime deterministic rules,
- rule-selection concepts.

### 8.2 Do not directly reuse

- ARGOS univariate `value,label,index` dataset contract,
- test-evaluation behavior inside rule-generation iterations,
- point-adjustment as an unqualified default,
- arbitrary LLM-generated Python execution.

### 8.3 LLM-generated code is prohibited

Never execute LLM output with:

- `exec`,
- `eval`,
- `compile`,
- `importlib`,
- subprocess-created Python files,
- dynamic module loading.

LLM output must be parsed as structured JSON into a versioned DSL schema. Only the deterministic DSL evaluator may execute rule semantics.

---

## 9. LLM provider and privacy policy

- Define an `LLMProvider` interface.
- Support a mock provider for all tests.
- External API calls are forbidden in CI.
- Secrets must come from environment variables or approved secret stores.
- Never commit keys or provider responses containing raw SWaT data.
- Prompts should contain structured aggregate evidence, not raw time-series rows.
- Default planning temperature should be deterministic when supported.

Record:

- provider,
- model/deployment,
- API version,
- temperature,
- seed if supported,
- prompt template hash,
- evidence artifact hash,
- response hash,
- redaction status.

---

## 10. Artifact and provenance policy

Every persisted research artifact must include:

- `schema_version`,
- `artifact_type`,
- `dataset_manifest_id`,
- `split_name`,
- `source_view`,
- `sampling_period_seconds`,
- `data_fingerprint`,
- config or config hash,
- code commit,
- upstream revisions where relevant,
- random seed,
- creation timestamp,
- upstream artifact identifiers.

Primary artifact types:

1. `dataset_manifest`
2. `split_manifest`
3. `variable_metadata`
4. `candidate_universe`
5. `gdn_candidate_edges`
6. `candidate_stability_report`
7. `relation_profile`
8. `calibration_record`
9. `rule_candidate`
10. `verification_report`
11. `verified_rule_library`
12. `runtime_alarm`
13. `evaluation_report`

---

## 11. Initial module boundaries

Adapt to the repository, but preserve these conceptual boundaries:

```text
src/<package>/
  data/           # local-only data access, manifests, splits, views
  metadata/       # variable metadata schemas and validation
  candidates/     # candidate universe and provenance
  gdn/            # modern GDN port, training, masked edge extraction
  profiling/      # relation profiling and normal-data calibration
  dsl/            # schemas, parser, deterministic evaluator, type rules
  planning/       # template planner and later LLM planner
  verification/   # deterministic checks and feedback codes
  runtime/        # LLM-free rule execution and explanations
  evaluation/     # metrics, reports, case studies
```

Runtime code must not depend on planning or LLM provider modules.

---

## 12. Coding and testing standards

- Use Python type hints for public APIs.
- Prefer dataclasses, Pydantic models, or the repository's established schema system.
- Validate external inputs at module boundaries.
- Separate pure computation from I/O.
- Use structured logging in library code.
- Do not embed secrets, absolute local paths, or raw restricted data.
- Make CLIs non-interactive by default and fail with non-zero exit codes.
- Keep scientific choices in versioned configs.
- Unit tests and CI use synthetic fixtures only.
- Add negative tests for leakage, candidate masks, type errors, and prohibited LLM behavior.

---

## 13. Evaluation policy

- Final test remains sealed until the approved final evaluation task.
- Point adjustment is disabled by default.
- PA-free, event-level, and range-aware metrics must be reported according to an approved protocol.
- If point-adjusted metrics are included, label them supplementary and report the exact adjustment.
- Separate detection performance from explanation quality.
- Negative and unsupported cases must be reported.

---

## 14. Verification feedback codes

Verifier failures must be machine-readable. Initial stable codes include:

- `DSL_SCHEMA_INVALID`
- `VARIABLE_NOT_FOUND`
- `TYPE_MISMATCH`
- `CALIBRATION_MISSING`
- `CALIBRATION_PROVENANCE_INVALID`
- `NORMAL_FP_TOO_HIGH`
- `VALIDATION_COVERAGE_TOO_LOW`
- `INSUFFICIENT_NORMAL_SUPPORT`
- `RELATION_PROFILE_UNSUPPORTED`
- `STRUCTURAL_DUPLICATE`
- `FIRING_OVERLAP_DUPLICATE`
- `PROHIBITED_VARIABLE_ADDITION`
- `PROHIBITED_NUMERIC_MUTATION`
- `MAX_REFINEMENT_REACHED`

Deterministic logic must not depend on free-text feedback.

---

## 15. Third-party notices

- Preserve copyright and license notices for reused or adapted upstream code.
- Maintain `docs/UPSTREAM_SOURCES.md` and `THIRD_PARTY_NOTICES.md`.
- Record whether code was copied, adapted, or only referenced.

---

## 16. Required work discipline

Before coding:

1. Read this file and the active task.
2. Inspect existing code, tests, and configs.
3. Confirm in-scope and out-of-scope items.
4. Identify affected data contracts and artifacts.
5. Confirm required data exists locally without copying it into Git.

Before completing:

1. Run relevant tests, lint, and type checks.
2. Verify no research invariant is violated.
3. Verify no restricted data entered Git-tracked files.
4. Verify artifacts include provenance and schema version.
5. Report exact commands and outcomes.

---

## 17. Stop conditions

Stop and document the issue when:

- required data or schema is unavailable,
- dataset edition/version cannot be determined and the task depends on it,
- repository conventions conflict with the task,
- a research decision has multiple scientifically meaningful alternatives,
- implementation would require test labels,
- upstream code cannot be ported without changing semantics,
- raw SWaT data would need to enter Git or an external API,
- a requested LLM operation would require executing generated code.
