---
id: TASK-019
title: Staging verified rule evidence audit
status: complete
depends_on: [TASK-018]
phase_gate: null
suggested_branch: task-019-rule-evidence-audit
---

# TASK-019: Staging Verified Rule Evidence Audit

## 1. Goal

Audit the two verified rules produced by TASK-018 as staging-only evidence
cards for implementation debugging and human review.

This is a Kaggle/local staging run for implementation debugging only. It is not
an official SWaT benchmark result and must not be used as a final thesis
performance claim.

## 2. Inputs

- `docs/task_reports/TASK-018_SUPPORT_SCAN_REPORT.json`
- `docs/task_reports/TASK-018_DRY_RUN_REPORT.json`
- `configs/data/task018_support_aware_staging.json`
- `configs/metadata/swat_variables.json`
- local `merged.csv` accessed through `SWAT_DATA_ROOT`

## 3. In scope

- Reconstruct verified rule evidence from the TASK-018 selected staging slice.
- Record source/target metadata.
- Record relation support counts.
- Record calibration parameters.
- Record rule AST summaries.
- Record verifier and runtime aggregate summaries.
- Preserve blank human-review notes fields.

## 4. Out of scope

- final SWaT benchmark,
- DEC-007 resolution,
- official sealed final test access,
- raw rows/windows/plots in Git,
- threshold/K/prompt/rule tuning,
- performance or explanation-quality claims.

## 5. Outputs

- `docs/task_reports/TASK-019_RULE_EVIDENCE_AUDIT.json`
- `docs/task_reports/TASK-019_RULE_EVIDENCE_AUDIT.md`
- `docs/task_reports/TASK-019_REPORT.md`

## 6. Completion notes

- The audit reconstructed 2 TASK-018 verified rules.
- Reconstructed rule IDs and verifier report IDs match TASK-018.
- Audited pairs:
  - `MV201 -> AIT201`
  - `MV201 -> AIT202`
- Both cards are explicitly marked staging/plumbing-only.
- No raw rows, windows, raw sequence plots, or downloadable derived samples were
  persisted.
