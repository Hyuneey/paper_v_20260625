---
id: TASK-015
title: Prepare DEC-007 official SWaT provenance resolution package
status: complete
depends_on: [TASK-014]
phase_gate: DEC-007
suggested_branch: task-015-dec007-official-swat-provenance
---

# TASK-015: DEC-007 Official SWaT Provenance Resolution Package

## 1. Goal

Prepare the official iTrust SWaT provenance resolution package needed before
DEC-007 can be marked resolved and before any sealed final test data can be
opened.

This task prepares checklists, schemas, templates, hashing procedures, frozen
protocol templates, and governance documents. It does not open final test data
and does not run a final SWaT benchmark.

## 2. Approved scope

- prepare official iTrust request/approval record checklist,
- record terms acknowledgement status,
- define local-only official SWaT file manifest schema,
- implement or document SHA-256 hashing procedure for approved local files,
- record exact dataset edition/version/file names,
- freeze final split protocol before opening sealed test,
- freeze final metric protocol,
- document allowed Git-tracked aggregate artifacts,
- prepare sealed-test one-way execution log template.

## 3. Not approved

- opening sealed final test,
- running final SWaT benchmark,
- using Kaggle/local CSV files for final claims,
- changing thresholds, K, prompts, rules, or fusion weights after test access,
- reporting point-adjusted metrics as primary,
- committing raw rows, windows, raw sequence plots, or downloadable derived samples.

## 4. DEC-007 resolution criteria

DEC-007 may be marked resolved only after:

1. official source or explicitly approved alternative source is selected;
2. terms are acknowledged;
3. exact edition/version/file list is recorded;
4. approved files are hashed locally;
5. split protocol is frozen;
6. metric protocol is frozen;
7. sealed-test access policy is approved;
8. Git artifact policy is approved.

## 5. Completion notes

- Added `OfficialSwatProvenanceManifest` and `OfficialSwatFileRecord` schema.
- Added local SHA-256 approved-file helper and synthetic tests.
- Added official SWaT provenance resolution package documentation.
- Added manifest template and sealed-test one-way execution log template.
- Added pending final protocol freeze config with final test access disabled.
- DEC-007 remains unresolved.
