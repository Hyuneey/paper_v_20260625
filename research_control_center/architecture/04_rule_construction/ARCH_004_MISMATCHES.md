# ARCH-004 Mismatches

Scientific authority: `origin/research-v6-thesis-checkpoint@2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`

| ID | Documented or tempting wording | Audited implementation | Severity | Action |
|---|---|---|---|---|
| A004-M01 | “Evidence Pack contains all support/stability summaries” | The model-visible E3 view contains fixed relation facts, the horizon as a separate relation field, 10 numeric value/reference bindings, evidence identities and bounded metadata; profiling summaries remain behind evidence references | MEDIUM | Describe the actual rendered view |
| A004-M02 | “The LLM writes the full executable Rule v1” | It returns a closed candidate core; canonical materialization and runtime authority are false at this stage | HIGH | Keep proposal, Rule v1, portfolio and runtime states separate |
| A004-M03 | “42/42 means runtime-authorized rules” | It means 42 relation-level `accepted_proposal` outcomes after task-specific validity | HIGH | Label numerator and denominator explicitly |
| A004-M04 | “T1-B and T2 used equal realized calls” | Both have a three-call opportunity cap, but T1-B used 126 fixed calls and T2 stopped after 42 first calls | MEDIUM | Say budget-cap comparable, not realized-cost equal |
| A004-M05 | “T2 feedback improved construction” | Feedback actions and recoveries were zero | HIGH | Limit claim to implemented capability |
| A004-M06 | “no_rule is parser/provider failure” | The three frozen T2 no-rule cases were deterministic non-repairable unsupported-variable outcomes | MEDIUM | Describe fail-closed terminal cause |
| A004-M07 | “LLM provides numeric authority” | E1 normal-only evidence supplies values and references; proposal returns references only | HIGH | Preserve external numeric authority wording |
| A004-M08 | “accepted construction proves detection utility” | Utility was not tested by the construction outcome artifacts | HIGH | Keep EXP-03 construction metrics separate from D1/D2 utility |
| A004-M09 | “Every admissible candidate can be materialized one-to-one as canonical Rule v1 MVP” | The candidate core permits both source signs and both target directions, while the current canonical MVP parser has a narrower supported subset; the bridge is not proven here | HIGH | Audit the exact canonical materialization bridge in ARCH-005 |
| A004-M10 | “Every construction `no_rule` denotes insufficient or unstable normal evidence” | The task-specific orchestrator also maps response/schema failure, verifier rejection and exhausted call budget to `no_rule`, while the frozen protocol and generic outcome contract require these failures to remain distinct | HIGH | Preserve concrete reason codes; audit and repair the contract boundary in a separately authorized implementation task |

Critical 0; High 7; Medium 3; Low 0. No frozen source or result was changed.
