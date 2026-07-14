# Research Questions and Baselines

## Research questions

### RQ1 - Rule controllability

Does a typed DSL with bounded relation families reduce invalid and uncontrolled
generation compared with ARGOS unrestricted Python?

Future measures: schema-valid candidate rate, verifier acceptance rate,
prohibited-operation rate, repair iterations, and parameter-provenance
completeness.

### RQ2 - Reproducibility

Does deterministic calibration and execution improve repeated-run consistency?

Future measures: rule-structure agreement, parameter stability, output
agreement, and variation across provider seeds/models.

### RQ3 - Multivariate explainability

Can graph-guided relational rules localize interpretable time-variable-lag
relationships?

Future measures: variable Recall@K, NDCG@K, time-variable mask agreement,
relation plausibility review, and provenance completeness. Plausibility is not
causality.

### RQ4 - Detection complementarity

Can verified relational rules complement a base detector?

Future arms: detector-only, rule-only, FN union, FP intersection,
confidence-gated fusion, and sealed-test PA-free metrics.

### RQ5 - Human usefulness

Are accepted rules and traces understandable and actionable?

Future measures: reviewer comprehension, traceability, consistency,
actionability, and unsupported-claim rate.

## Baseline matrix

| ID | Name | Current status |
|---|---|---|
| B0 | detector_only | specification only |
| B1 | ARGOS_rule_only | pending container execution |
| B2 | ARGOS_detector_rule_fusion | pending rule and detector artifacts |
| B3 | proposed_DSL_without_graph_guidance | not implemented |
| B4 | proposed_graph_guided_DSL_without_deterministic_verifier | not implemented; research ablation only |
| B5 | complete_proposed_method | not implemented |

Required ablations remove graph guidance, deterministic verifier, calibration
provenance, matched normal reference, repair loop, or fusion one at a time under
the same frozen split and metric protocol.

TASK-030 defines these comparisons but produces no experimental result.
