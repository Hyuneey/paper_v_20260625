# Continuous-Step Parameter Provenance

Feasibility screening, final calibration, and runtime parameters are distinct
classes. Screening values cannot be promoted implicitly. Final numeric values
must be recalibrated by deterministic project-owned artifacts in TASK-039D or
its versioned successor and referenced immutably at runtime.

An Agent may select an approved parameter reference, supported directional
relation, and closed family; request verifier-guided repair; or return
`no_rule`. It cannot invent or rewrite thresholds, stability tolerance, lag,
response threshold, or any number from raw samples. Labels and test
performance are prohibited numerical inputs.
