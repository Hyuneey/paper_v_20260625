# End-to-End Template Feasibility

TASK-011 runs the deterministic template baseline through Phase Gate B smoke
checks.

The tracked workflow config is:

- `configs/e2e/task011_template_feasibility.json`

The machine-readable result is:

- `docs/task_reports/TASK-011_E2E_REPORT.json`

## Scope

This is a deterministic synthetic feasibility smoke result.

It verifies that the project-owned pipeline can connect:

```text
dataset/view/split manifests
-> variable metadata
-> candidate universe
-> masked GDN candidate edge
-> relation profile/calibration
-> template DSL rule
-> deterministic verifier
-> verified rule library
-> validation runtime alarm/explanation
```

No LLM is used. No final test data is accessed. Raw SWaT rows are not loaded.

## Phase Gate B

The smoke report recommends:

```text
proceed_to_phase_gate_b_review
```

This is not approval to start TASK-012 by itself. TASK-012 must wait until
Phase Gate B is reviewed and approved by the researcher.

## Result Shape

The report stores:

- artifact dependency graph,
- attempted candidate pairs and outcomes,
- normal false-firing summary,
- validation firing coverage summary,
- runtime alarm summary,
- one detailed synthetic case study,
- restricted-data audit,
- answers to the required TASK-011 report questions.

It intentionally does not store raw time-series windows.
