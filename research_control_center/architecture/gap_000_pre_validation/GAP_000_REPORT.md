# GAP-000 Pre-Validation Remediation & Risk Triage

Scientific authority: `origin/research-v6-thesis-checkpoint` @ `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`  
RCC authority gate: `0346736f20cd99544f56685344d8119fba9e6d56`  
Verdict: **PASS — TRIAGE COMPLETE; REMEDIATION NOT IMPLEMENTED**

## Outcome first

No audited defect proves the frozen INNER pilot invalid, and no verified leakage, metric tampering, or authority substitution was found. The pilot remains interpretable with its existing qualifications. Future final evidence is not ready: two global implementation/contract fixes and two global experimental-design gates must be closed before expanded core detection validation.

The 120 raw findings are not 120 separate projects. They reduce to 19 root gaps. Original severities are `0 critical / 54 high / 55 medium / 11 low`; remediation urgency was reassigned independently.

## Root triage

| Primary disposition | Root gaps |
|---|---:|
| ACCEPTABLE_THESIS_LIMITATION | 3 |
| CLAIM_DOCUMENTATION_CORRECTION | 1 |
| ENGINEERING_HARDENING | 3 |
| EXPERIMENT_DESIGN_REQUIREMENT | 6 |
| FUTURE_WORK_ONLY | 1 |
| P0_FIX_BEFORE_EXPANDED_VALIDATION | 2 |
| P1_FIX_BEFORE_SPECIFIC_EXPERIMENT | 3 |

## Primary disposition: global pre-validation fixes

1. `GAP-001`: choose and version the final scientific rule/verifier/runtime authority.
2. `GAP-002`: add a durable D1 prediction-before-label byte/state gate.

These two rows have primary disposition `P0_FIX_BEFORE_EXPANDED_VALIDATION`. Separately, their urgency priority is `P0`. `GAP-003` and `GAP-004` have a different primary disposition (`EXPERIMENT_DESIGN_REQUIREMENT`) but the same urgency priority `P0`: freeze validation/final-test roles and freeze the event-unit/evaluation policy. They must not be disguised as code cleanup.

## Primary disposition: experiment-specific fixes

These rows have primary disposition `P1_FIX_BEFORE_SPECIFIC_EXPERIMENT`; this does not mean that “P1” is the same field as urgency priority.

- EXP-01: correct or explicitly ablate the GDN self-neighbor Top-5 convention.
- EXP-03: separate `no_rule` from provider, parse, verifier, retrieval and budget failures.
- EXP-05: connect the evaluated runtime trace to its deterministic renderer.

## What not to over-engineer

- train3 dual normal-only use is a disclosed limitation, not verified leakage.
- human explanation usefulness may remain unvalidated unless it becomes a core thesis claim.
- D1 high FAR needs honest limitation wording; a causal diagnosis is not required before preserving the pilot.
- runtime LLM, complex relation hierarchies, causal analysis, and a multi-agent runtime are future work only.

## Contribution conditions

- **Graph-Guided** remains provisional until EXP-01 demonstrates stable, unique, functionally useful graph contribution.
- **Agentic** remains provisional until EXP-03 actually exercises feedback and shows a budget-matched benefit. If feedback remains unused, the valid conclusion is implementation capability without demonstrated benefit.
- The current D1 result remains **COMMON-42 Verified Relational Rule-only**, not direct LLM Rule-only or Agentic Rule-only.

## Pilot preservation

`PILOT V1` artifacts are immutable historical evidence. None is rewritten. The future remediated path must be versioned separately as `VALIDATION V2`. Current qualifications remain: test1 development pilot, 14 contiguous event units with independence unestablished, V4 runtime authority, weaker D1 pre-label custody, and no held-out generalization.

## Ordered path

1. Complete GAP-000 and approve its two real research-owner decisions.
2. Run read-only ARCH-011 before remediation to pin OUTER, environment, custody, and portability facts.
3. Resolve `GAP-001`; then implement `GAP-002`, `GAP-012`, and `GAP-013` narrowly.
4. Close only the experiment-specific code gate needed for the next approved experiment.
5. Freeze experiment protocols before results.
6. Run development/validation experiments without final-test access.
7. Complete fresh-machine rehearsal.
8. Authorize one new preregistered held-out study.

No remediation, experiment, LLM call, metric recomputation, test2 access, or scientific execution occurred in GAP-000.
