# My Research TODO

This page contains research-owner work, not low-level implementation chores.
Items assigned to Codex are separated so the user does not need to perform
them manually.

## Decision Needed

No unresolved user decision is open in RCC-001. The two RCC-000 source-policy
decisions are approved and recorded in `registry/decisions.csv` and
`history/decisions/`.

## Understanding Needed

### U-001

- Priority: `HIGH`
- Task: Explain the end-to-end architecture in your own words, from candidate
  discovery through verified rule runtime and bounded utility evaluation.
- Why user involvement is required: Thesis defense and scope decisions require
  the research owner to distinguish the scientific contribution from its
  supporting detector and evaluation infrastructure.
- Linked component/experiment: `PROJECT_WIDE`
- Status: `OPEN`

### U-002

- Priority: `HIGH`
- Task: Confirm your understanding of the status ladder: implemented,
  executed, audited, reproduced, and claim-ready.
- Why user involvement is required: These labels determine which statements
  can safely appear in the thesis and which still need evidence.
- Linked component/experiment: `PROJECT_WIDE`
- Status: `OPEN`

### U-003

- Priority: `MEDIUM`
- Task: Understand the difference between GDN candidate discovery output and
  a scientifically validated unique GDN contribution.
- Why user involvement is required: The implementation exists, but the unique
  contribution hypothesis remains unvalidated and should not be overstated.
- Linked component/experiment: `GDN_DISCOVERY` / `EXP-GDN-CONTRIBUTION`
- Status: `OPEN`

### U-004

- Priority: `MEDIUM`
- Task: Understand how D1 rule-only alarms differ from detector alarms and why
  rule validity does not by itself establish practical Rule-only utility.
- Why user involvement is required: Correct thesis wording depends on keeping
  validity, runtime behavior, and utility evidence separate.
- Linked component/experiment: `D1_RULE_ONLY` / `EXP-RULE-ONLY-UTILITY`
- Status: `OPEN`

## Review Needed

### R-001

- Priority: `HIGH`
- Task: Review and approve the RCC-001 navigation, phase statement, and source
  authority display.
- Why user involvement is required: RCC-002 should not expand an information
  architecture that the research owner finds unclear or misleading.
- Linked component/experiment: `PROJECT_WIDE`
- Status: `OPEN`

### R-002

- Priority: `HIGH`
- Task: Review the conservative claim wording in `CURRENT_CONTEXT.md` and the
  dashboard.
- Why user involvement is required: Final thesis wording is a research-owner
  judgment, while the RCC must continue to enforce the pinned evidence limits.
- Linked component/experiment: `EXP-GDN-CONTRIBUTION`;
  `EXP-RULE-ONLY-UTILITY`; `EXP-DETECTOR-RULE-FUSION`
- Status: `OPEN`

### R-003

- Priority: `MEDIUM`
- Task: Review the fresh-machine reproducibility assessment before authorizing
  a future held-out study.
- Why user involvement is required: The public checkpoint is traceable but is
  not yet a one-command reproduction capsule.
- Linked component/experiment: `OUTER_EVALUATION`
- Status: `OPEN`

## Waiting on Implementation

### I-001

- Priority: `HIGH`
- Task: Populate the complete current-state registry in RCC-002.
- Why user involvement is required: No user implementation work is required;
  the user only reviews the resulting inventory and claim boundaries.
- Linked component/experiment: `PROJECT_WIDE`
- Status: `WAITING_ON_CODEX`
