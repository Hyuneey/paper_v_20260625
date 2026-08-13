# TASK-039E3 R2R Thesis Decision Memo

## Recommended thesis position

The defensible contribution is a governed, evidence-bound construction pipeline with deterministic validity admission and deterministic numeric calibration—not an empirically superior T2 feedback agent. On the 42 frozen relations, T0, T1, and T1-B all reached 42/42 relation-level validity, while T2 reached 39/42 and never activated feedback. Direct-number outputs were schema-valid but numerically inaccurate. The smallest coherent thesis story is therefore: the pipeline can construct admissible rules; one-shot construction was sufficient under the current verifier; repeated sampling bought limited robustness at high call cost; deterministic no_rule prevented invalid admission; and deterministic calibration is warranted.

Utility evaluation is **ESSENTIAL** to distinguish T0, T1, T1-B, and T2 scientifically because deterministic validity is saturated by three arms and does not measure detector benefit, false fires, duplicate behavior, or usefulness.

## What the experiment showed

1. The pipeline produced verifier-admissible outputs for every relation under T0, T1, and T1-B, and for 39/42 under T2.
2. T0 already saturated the deterministic validity verifier with zero provider calls. This is a validity-ceiling/discrimination limitation, not proof that T0 is the best useful arm.
3. T1 produced 42/42 admissible first calls in this frozen run. This supports bounded one-shot feasibility, not general LLM reliability.
4. T1-B was robust to one parse failure and recovered one relation on call 3, but spent 84 extra calls beyond its first-draw budget and did not exceed T1's final yield.
5. T2's three rejected proposals contained non-repairable unsupported variables. The controller correctly emitted no_rule, so revise/retrieve/follow-up were ineligible and never occurred.
6. Consequently, incremental validity benefit of T2 was not observed, and feedback recovery was not empirically tested.
7. Valid Direct-number JSON did not imply numerical accuracy. Median normalized errors were about 0.598, 0.490, and 0.984; target-noise error had extreme dispersion.
8. Candidate-origin results are exploratory. T2 no_rule was concentrated outside META and touched two of five GDN-member relations, but groups overlap and GDN is too small for an origin-effect claim.

## Is T2 defensible as the main contribution?

Not as an empirically superior construction method from this experiment. It remains defensible as a bounded, fail-closed architectural mechanism: it refused three non-repairable proposals rather than admitting them. Because no repairable rejection occurred, the feedback loop itself must be described as unexercised, not validated.

## Alternative position

A weaker alternative is a methodological thesis centered on controlled comparison and governance: independent sampling, deterministic feedback eligibility, explicit no_rule, transactional custody, and deterministic calibration form a reproducible evaluation framework. T2 can appear as one bounded mechanism whose negative result establishes where the current verifier/controller offers no incremental benefit.

## Positions to avoid

- “T2 improves validity” or “feedback recovery was validated.”
- “T0 is the winner” or “T1 is the winner”; utility is untested and winner selection is unauthorized.
- “Best-of-three generally improves LLM reliability.”
- “Candidate origin causes construction success differences.”
- “Schema-valid Direct-number output is numerically accurate.”
- “The three T2 no_rule relations are intrinsically invalid.” T0, T1, and T1-B accepted all three.

## Do not add a rescue experiment

Do not rerun until T2 happens to receive a repairable error, tune prompts/verifier thresholds after observing these results, exclude the three T2 failures, redefine denominators, or add post-hoc metrics merely to create a positive agentic headline. The next justified gate is a preregistered utility-feasibility and authorization decision using the preserved accepted rules—not another construction rerun.

## Discussion branches

- **C — T2 < T1-B:** T2 accepted 39/42 versus T1-B 42/42 in the realized run.
- **D — validity discrimination is problematic:** T0, T1, and T1-B all saturated deterministic validity, so validity alone cannot identify useful differences.
