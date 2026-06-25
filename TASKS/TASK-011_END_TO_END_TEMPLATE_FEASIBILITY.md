---
id: TASK-011
title: Run validation-only deterministic end-to-end feasibility gate
status: complete
depends_on: [TASK-010]
phase_gate: Phase Gate B
suggested_branch: task-011-e2e-template-kill-test
---

# TASK-011: End-to-End Deterministic Feasibility Test

## 1. Goal

Run and document the complete deterministic path from local SWaT manifests to verified-rule alarms on approved validation data, without any LLM integration and without opening the final test set.

## 2. Required pipeline

```text
dataset/view/split manifests
→ variable metadata
→ candidate universe
→ masked GDN candidate pair
→ relation profile/calibration
→ template DSL rule
→ deterministic verifier
→ verified library
→ validation runtime alarm/explanation
```

## 3. Inputs

- approved artifacts from TASK-001 through TASK-010,
- canonical rule view,
- approved validation split,
- no final test data.

## 4. Required outputs

- one reproducible workflow/command,
- artifact dependency graph,
- feasibility report,
- all attempted pairs and outcomes,
- at least one detailed case study if supported,
- normal firing and validation coverage summaries,
- restricted-data audit,
- explicit Phase Gate B recommendation.

## 5. Required report questions

1. Does the deterministic pipeline run without library-level hard-coded pairs?
2. Are candidate edges proven to obey `C_i`?
3. Are temporal parameters derived from canonical high-resolution calibration artifacts?
4. Are runtime explanations derived from fired DSL rules?
5. Does the rule behave differently on normal and validation intervals?
6. Which candidates/profiles/rules were unsupported or rejected?
7. Is LLM integration scientifically justified as the next step?
8. Is the final test still sealed?

## 6. Research constraints

- No final test access.
- No LLM calls.
- No cherry-picking without reporting selection criteria.
- Report unsupported pairs and failed rules.
- Do not copy raw SWaT sequences into Git-tracked reports.
- Runtime must remain LLM-free and generated-code-free.

## 7. Acceptance criteria

1. One command or documented workflow reproduces the validation result.
2. Every artifact has complete provenance.
3. Runtime imports no LLM package.
4. Template baseline metrics are saved for later comparison.
5. No raw restricted data is tracked.
6. Final test access audit passes.
7. Phase Gate B decision is explicit.

## 8. Required tests/checks

- clean-environment smoke test,
- artifact provenance graph validation,
- no-test-access assertion,
- runtime import-boundary check,
- deterministic rerun comparison,
- Git status restricted-data scan.

## 9. Stop condition

Do not start TASK-012 until Phase Gate B is reviewed and approved.

## 10. Completion notes

- Implemented deterministic end-to-end template feasibility workflow under `src/paperworks/e2e/`.
- Added tracked workflow config at `configs/e2e/task011_template_feasibility.json`.
- Generated machine-readable smoke report at `docs/task_reports/TASK-011_E2E_REPORT.json`.
- Added human-readable workflow notes in `docs/END_TO_END_TEMPLATE_FEASIBILITY.md`.
- Smoke path covers candidate universe, masked GDN edge extraction, profiling/calibration, template rule build, deterministic verification, verified library loading, and runtime alarm/explanation.
- Phase Gate B recommendation is `proceed_to_phase_gate_b_review`; TASK-012 must not start until reviewed and approved.
