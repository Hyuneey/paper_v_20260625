---
id: TASK-000
title: Repository, upstream, environment, and SWaT provenance audit
status: ready
depends_on: []
phase_gate: Milestone 0
suggested_branch: task-000-repository-audit
---

# TASK-000: Repository, Upstream, Environment, and Dataset Audit

## 1. Goal

Inspect the target repository, the reviewed ARGOS/GDN references, and the researcher-local SWaT files without modifying production source code. Produce an implementation-ready audit and a list of decisions required before coding.

## 2. Architecture context

This task prevents four high-risk failures:

1. creating a parallel codebase without understanding the repository,
2. installing incompatible ARGOS/GDN environments together,
3. assuming an unverified SWaT edition or schema,
4. copying unsafe upstream evaluation or generated-code execution patterns.

## 3. Preconditions

- `AGENTS.md` and `IMPLEMENTATION_PLAN.md` are present.
- Target repository is accessible.
- ARGOS and GDN repositories are accessible.
- If available, SWaT is mounted locally through `SWAT_DATA_ROOT`.

## 4. Inputs

- full target-repository tree,
- existing README/config/test/CI files,
- `microsoft/ARGOS`, reviewed snapshot `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`,
- `d-ailin/GDN`, reviewed snapshot `9853899da860682669a134e4af315d036aab4eca`,
- local SWaT paths, if present,
- work-order pack.

## 5. Required outputs

Create or update documentation only:

- `docs/REPO_AUDIT.md`
- `docs/UPSTREAM_SOURCES.md`
- `docs/DATASET_PROVENANCE.md`
- `docs/ENVIRONMENT_STRATEGY.md`
- `docs/IMPLEMENTATION_NOTES.md`
- `docs/DATA_CONTRACTS.md` (proposal only)
- `docs/RESEARCH_INVARIANTS.md`
- `docs/DECISIONS_REQUIRED.md`
- `THIRD_PARTY_NOTICES.md` (initial draft)

## 6. Required investigation

## Upstream repository review

Inspect the following repositories as read-only references:

- https://github.com/microsoft/ARGOS
- https://github.com/d-ailin/GDN

Before using any upstream code:

1. Resolve and record the exact commit SHA.
2. Read the license.
3. Identify the exact files relevant to this project.
4. Separate:
   - concepts to reuse,
   - code that can be adapted,
   - code that must not be reused.
5. Record findings in `docs/UPSTREAM_SOURCES.md`.
6. Do not edit upstream repositories.
7. Do not copy whole modules into production code.
8. Do not make architectural changes merely to match upstream code.
   Our project specification takes precedence.

### 6.1 Target repository

- current package structure,
- exact install/test/lint/type-check commands,
- existing data loaders,
- existing model code,
- existing artifact conventions,
- CI behavior,
- nested `AGENTS.md` files,
- reusable components and conflicts.

### 6.2 ARGOS reference

Document:

- Python/environment requirements,
- dataset contract,
- Detection/Repair/Review/Mutation architecture,
- test/validation behavior,
- any use of `exec` or dynamically generated Python,
- reusable concepts versus prohibited direct reuse.

### 6.3 GDN reference

Document:

- legacy dependency stack,
- preprocessing assumptions,
- train/validation split behavior,
- Top-K graph construction,
- absence or presence of `C_i` masking,
- candidate self-edge behavior,
- test-label or `report=best` scoring behavior,
- modern-port recommendation.

### 6.4 SWaT local files

If `SWAT_DATA_ROOT` is available, inspect metadata only and compute:

- local relative filenames,
- SHA-256 hashes,
- file formats,
- column names,
- feature count,
- timestamp and label columns,
- label encoding,
- inferred sampling interval,
- likely edition/version,
- any evidence of prior downsampling.

Do not copy raw rows into docs or terminal output retained in Git.

If SWaT is unavailable, document the exact blocker and manifest fields still required.

## 7. Required decisions to surface

1. GDN modern port versus isolated legacy reference environment.
2. Official iTrust source versus Kaggle mirror for the canonical dataset.
3. Canonical rule-view sampling resolution.
4. Optional GDN-view preprocessing.
5. ARGOS code reuse boundary.
6. Final metric family and point-adjustment policy.

Do not make these decisions silently.

## 8. In scope

- non-destructive inspection,
- safe existing fast tests,
- hashes and aggregate schema inspection,
- proposed adapted module boundaries,
- license and provenance register.

## 9. Out of scope

- no production source changes,
- no dependency upgrades,
- no model training,
- no SWaT redistribution,
- no automatic dataset download,
- no full preprocessing run that produces Git-tracked data.

## 10. Acceptance criteria

1. Exact development commands are documented and verified where safe.
2. Upstream revisions and licenses are recorded.
3. The audit explicitly identifies GDN `C_i` masking and self-edge adaptation needs.
4. The audit explicitly prohibits ARGOS-style arbitrary Python execution.
5. SWaT provenance is documented or clearly marked unavailable/unverified.
6. GDN environment strategy is recommended with tradeoffs.
7. No file outside approved documentation paths is modified.
8. The audit explicitly states whether TASK-001 may begin.

## 11. Required checks

- repository status before and after,
- list modified files,
- inspect Git ignore rules for data/artifacts,
- verify no raw SWaT file is tracked,
- verify existing tests without altering data.

## 12. Stop conditions

Stop and report if:

- repository access is incomplete,
- local SWaT inspection would expose or copy raw data,
- upstream commit cannot be pinned,
- environment setup requires an unapproved scientific choice,
- terms of use or data source are unclear enough to block implementation.

## 13. Required final report

Include a recommended TASK-001 configuration and any edits required in later tickets.
