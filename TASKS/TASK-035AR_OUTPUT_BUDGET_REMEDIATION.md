# TASK-035AR: Output-Budget Remediation

Status: completed, `passed_balanced_generation_cohort`

## Scope

Create two new independent one-shot generations for each of the 50 frozen
TASK-035A anchors. Replicate IDs are 3 and 4. The only provider change is an
increase from 2,000 to 6,000 maximum output tokens.

## Boundaries

- TASK-035A slots and status are immutable.
- No prompt, provider, model, anchor, chunk, static-policy, or runtime-policy
  change is permitted.
- No retries, RepairAgent, ReviewAgent, selection, validation, detector,
  fusion, or test access is permitted.
- Raw prompts, responses, rules, arrays, and runtime outputs remain ignored.
- Results are generation-operability diagnostics, not anomaly performance.

## Gate

The frozen adequacy criteria are declared in
`configs/argos_reproduction/task035ar_output_budget_remediation.json` and may
not be lowered after execution. Only `passed_balanced_generation_cohort`
authorizes TASK-035B.

Execution produced 100 non-empty, extracted, and static-valid rules; 91 passed
the isolated runtime contract. The combined immutable cohort contains 146
executable rules and passed every frozen balance threshold. No performance
evaluation occurred.
