# ARCH-004 Agentic Claim Boundary

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

## Implemented capability

T2 implements a bounded, project-controlled proposal -> parser -> deterministic validity -> revise/retrieve/no_rule loop. The LLM does not control orchestration, grant validity, introduce new evidence, or grant runtime authority.

## Observed frozen execution

- eligible relations: 42;
- accepted on first call: 39;
- non-repairable `no_rule`: 3;
- revise: 0;
- retrieve: 0;
- follow-up generations: 0;
- feedback recoveries: 0.

## Claim decision

Allowed: “A bounded verifier-feedback construction path was implemented.”

Allowed with pilot qualifier: “In the frozen 42-relation construction cohort, T2 accepted 39 first-call proposals and returned three fail-closed no-rule outcomes.”

Forbidden from current evidence: “Agentic feedback improved rule quality,” “T2 was superior,” “the loop improved detection,” or “COMMON-42 is an Agentic rule set.” No feedback action occurred, and construction validity is not detection utility.

Future EXP-03 must use a budget-matched cohort in which repairable failures actually occur and measure parser success, validity acceptance, repair recovery, stability, unsupported-reference rate, calls, cost and latency. That validation is not a fourth construction arm and was not run here.
