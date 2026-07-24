# TASK-038A Report

Status: `passed_agent_factorial_protocol_freeze`

TASK-038A freezes a four-branch component-wise protocol for evaluating
one-shot ARGOS rules, RepairAgent, ReviewAgent, and the combined agent path.
The experiment reuses the complete 96-slot TASK-037D initial-rule cohort,
preserves both LSTMAD variants, corrects upstream validation leakage, bounds
every agent to one revision, and prohibits host generated-code execution,
outer access, and sealed-test access. No real agent or provider execution was
performed. This task establishes experimental and safety readiness only and
does not establish Repair, Review, or ARGOS methodological effectiveness.

## Frozen artifacts

- Initial slots: 96
- Initial static-valid rules: 96
- Initial executable rules: 83
- Initial runtime failures and Repair population: 13
- Logical branches: 384
- Branches per initial slot: A0, A1, A2, A3
- Maximum unique primary-study provider calls: 192
- Actual provider calls: 0
- Actual Repair executions: 0
- Actual Review executions: 0

## Safety and leakage boundary

- Repair is generation-only and receives no labels or performance metrics.
- Review is inner-only and triggers only when combined point F1 is below the
  matching detector baseline.
- Regression samples are chronological, non-overlapping, at most three, and at
  most 20 points each.
- Generated code has no host execution API.
- Future execution is container-only.
- Outer and sealed-test readers fail closed.
- Automatic retry, manual retry, and replacement generation are disabled.
- Harmful reviewed outputs cannot be silently reverted.
- Detector-variant selection and joint FN/FP pair search are prohibited.

## Provenance hashes

- Initial registry:
  `c0d2f92807fb7e876319fab0c300973d8c62fdb45e499ee69c1f12786f2e750d`
- Branch registry:
  `6865af148258682a67aab9702fc795216cd4af119333539808c93d9e425b8390`
- Provider budget:
  `c6194be08967ac0e03ac88eb15bc1f05fcffc600dc1bc64f87187a507631f9a1`
- Protocol freeze:
  `972fa2d17f8280245c8c4467b10f57015959c1406fb3705495e939d0410c5bc4`

Only this status authorizes TASK-038B planning. It does not authorize a provider
call automatically.
