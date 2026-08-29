<!-- RCC_GENERATED registry_version=0.1.0 registry_digest=c8c7f24b5c73df275f163236e9927800a85e9977c5e794f5ddbb39a40d47622a authority=2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e -->
# My Research TODO

This page contains research-owner actions, not low-level development chores.

## Decision Needed

No items.
## Understanding Needed

- **ID:** USER-ARCH006-001
  **Priority:** HIGH
  **Task:** Can I explain how one Rule runs?
  **Why your involvement is required:** The runtime evaluates source opportunities and one fixed-horizon target response rather than every timestamp.
  **Linked:** ARCH_006_RUNTIME_STATE_MACHINE.md
  **Status:** OPEN

- **ID:** USER-ARCH006-002
  **Priority:** HIGH
  **Task:** Can I explain PASS, FAIL, and ABSTAIN?
  **Why your involvement is required:** A non-trigger is not automatically PASS or ABSTAIN, and a hard authority error is neither.
  **Linked:** ARCH_006_OUTCOME_TAXONOMY.md
  **Status:** OPEN

- **ID:** USER-ARCH006-003
  **Priority:** HIGH
  **Task:** Can I explain how the D1 alarm is formed?
  **Why your involvement is required:** Rule-level anomaly records, unique alarm seconds, and metric episodes are different counts.
  **Linked:** ARCH_006_D1_PREDICTION_SCHEMA.md
  **Status:** OPEN

- **ID:** USER-ARCH006-004
  **Priority:** HIGH
  **Task:** Can I explain what a satisfaction trace contains?
  **Why your involvement is required:** The frozen task trace is a compact terminal hash record, not canonical RuntimeTraceV1.
  **Linked:** ARCH_006_TRACE_SCHEMA.csv
  **Status:** OPEN

- **ID:** USER-ARCH006-005
  **Priority:** HIGH
  **Task:** Can I explain prediction-before-label?
  **Why your involvement is required:** The label-blind prediction object is complete and validated before the label file is opened.
  **Linked:** ARCH_006_D1_FREEZE_BOUNDARY.md
  **Status:** OPEN

- **ID:** USER-ARCH006-006
  **Priority:** HIGH
  **Task:** Can I explain the durable-freeze limitation?
  **Why your involvement is required:** The D1 pilot used an in-memory shallow freeze rather than durable pre-label bytes.
  **Linked:** ARCH_006_D1_FREEZE_BOUNDARY.md
  **Status:** OPEN

- **ID:** USER-ARCH006-007
  **Priority:** HIGH
  **Task:** Can I explain the runtime LLM-free wording?
  **Why your involvement is required:** The claim applies to the frozen fixed-rule R0/D1 runtime, not every future runtime design.
  **Linked:** ARCH_006_REPORT.md
  **Status:** OPEN

- **ID:** USER-ARCH006-008
  **Priority:** HIGH
  **Task:** Can I explain explanation fidelity versus human usefulness?
  **Why your involvement is required:** Canonical structural binding exists, but frozen D1 explanation wiring and human validation do not.
  **Linked:** ARCH_006_EXPLANATION_RENDERER.md
  **Status:** OPEN
## Review Needed

- **ID:** USER-ARCH006-009
  **Priority:** HIGH
  **Task:** Approve or defer starting ARCH-007.
  **Why your involvement is required:** D0 PCA-SPE is the next separate deep detector audit.
  **Linked:** ARCH-007
  **Status:** OPEN
## Waiting On Codex

No items.

Scientific authority: `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`
