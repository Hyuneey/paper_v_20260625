# ARGOS Methodological Validity Criteria

The later TASK-038 synthesis evaluates six dimensions separately.

1. **Operational validity:** Repair recovery, runtime success, safety success,
   and cost.
2. **Incremental Review value:** paired A2-A0 and A3-A1 effects, regression
   rate, and no-review-needed rate.
3. **Generalization:** inner improvement, outer improvement, their gap, KPI
   win/tie/loss, and alpha/beta direction consistency.
4. **Detector complementarity:** FN recovery with added FP, and FP removal with
   removed TP and true events.
5. **Efficiency:** calls, tokens, elapsed time, improvement per call, and
   improvement per million tokens.
6. **Safety and reproducibility:** container-only execution, bounded calls,
   immutable split guards, deterministic replay, and hash-complete provenance.

Allowed conclusions are `strongly_supported`, `partially_supported`, and
`not_supported`. Strong support requires material Repair recovery, Review outer
generalization, A3 improvement over A0 and detector-only with acceptable
costs, consistent variant direction, and sealed-test confirmation.

TASK-038A cannot assign any effectiveness conclusion. Its protocol schema
rejects a strong conclusion without sealed-test confirmation.
