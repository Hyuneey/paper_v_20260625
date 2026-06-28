---
id: TASK-020
title: Staging rule robustness and synthetic violation replay
status: complete
depends_on: [TASK-018, TASK-019]
phase_gate: null
suggested_branch: task-020-rule-robustness
---

# TASK-020: Staging Rule Robustness and Synthetic Violation Replay

## 1. Goal

Assess whether the TASK-018/TASK-019 staging verified rules are merely one-off
plumbing artifacts or stable enough to keep as staging evidence candidates.

This is a Kaggle/local staging run for implementation debugging only. It is not
an official SWaT benchmark result and must not be used as a final thesis
performance claim.

## 2. Inputs

- `docs/task_reports/TASK-018_SUPPORT_SCAN_REPORT.json`
- `docs/task_reports/TASK-018_DRY_RUN_REPORT.json`
- `docs/task_reports/TASK-019_RULE_EVIDENCE_AUDIT.json`
- `configs/data/task018_support_aware_staging.json`
- `configs/metadata/swat_variables.json`
- local `merged.csv` accessed through `SWAT_DATA_ROOT`

## 3. In scope

- Scan `merged.csv` with the predeclared support-aware criteria.
- Report pair-level support frequency across fixed-stride slices.
- Rebuild template rules for predeclared support-aware slices.
- Compare rule IDs, calibration values, support counts, and verifier status.
- Replay synthetic non-SWaT missing-response and expected-response cases.

## 4. Out of scope

- final SWaT benchmark,
- DEC-007 resolution,
- official sealed final test access,
- using Kaggle/local results as thesis final results,
- threshold/K/prompt/rule/verifier tuning,
- raw rows, windows, sequence plots, or downloadable samples in Git,
- real provider/network calls,
- runtime LLM.

## 5. Outputs

- `docs/task_reports/TASK-020_RULE_ROBUSTNESS_REPORT.json`
- `docs/task_reports/TASK-020_SYNTHETIC_VIOLATION_REPLAY.json`
- `docs/task_reports/TASK-020_REPORT.md`

## 6. Completion notes

- Scanned 2,810 fixed-stride staging slices.
- Found 464 support-aware passing slices.
- Recorded support frequency for all 8 predeclared pairs.
- Rebuilt 22 rule observations across the selected and first passing slices.
- Synthetic replay passed for both TASK-019 audited rules.
- No raw rows, windows, raw sequence plots, or downloadable derived samples were
  persisted.
