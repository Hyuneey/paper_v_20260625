# Limitations and Threats to Validity

## Explicit limitations

1. **Single process and dataset edition.** The empirical cohort is bounded to
   HAI 23.05 P1 Boiler.
2. **Limited relation cohort.** Construction used 42 confirmed directional
   relations from 23 source-target pairs.
3. **Single provider/model snapshot.** T1, T1-B, T2, and Direct-number results
   reflect one frozen provider/model contract and one realized execution.
4. **Validity ceiling.** T0, T1, and T1-B each reached 42/42 deterministic
   verifier acceptance, limiting endpoint discrimination.
5. **Unexercised feedback path.** T2 received no repairable rejection;
   feedback eligibility and all recovery actions were zero.
6. **Overlapping and imbalanced origin groups.** META/STAT/GDN memberships are
   non-exclusive, and GDN contains only five final relations.
7. **No labeled utility result.** Attack coverage, false-alarm burden,
   duplicate firing, precision, and detector benefit were not measured.
8. **No detector integration.** The study did not evaluate false-negative
   recovery, added false positives, or a combined detector-rule system.
9. **No production Rule v2/runtime validation.** The intended LLM-free
   execution boundary was not implemented or evaluated as production runtime.
10. **Post-result utility protocol.** The exact utility protocol was designed
    after construction results were known and was correctly classified as a
    post-result protocol freeze, not preregistration.
11. **Utility stopped before label access.** The final protocol remained
    unaudited because opportunity-denominator authority and fail-closed state
    handling were incomplete. No label or test-feature access occurred.

The final two limitations must remain visible in the thesis. Hiding them would
misrepresent both chronology and governance.

## Construct validity

### Threats

- Deterministic verifier-admissibility measures structural, evidence,
  reference, and policy conformance; it is not anomaly utility.
- `no_rule` measures invalid-proposal exclusion, not runtime safety or useful
  abstention.
- Direct-number normalized error measures numerical agreement with calibrated
  references, not downstream detection loss.
- META, STAT, and GDN provide different forms of candidate evidence with no
  common score scale.
- Confirmed delayed-response relations are normal-data evidence, not causal
  links or root causes.

### Mitigation and residual impact

The study keeps evidence, construction validity, utility, governance, and
runtime authority separate. Claims are worded at their actual layer. The
remaining impact is fundamental: without labeled utility, verifier acceptance
cannot establish anomaly-detection effectiveness.

## Internal validity

### Threats

- Stochastic arm differences may reflect the realized provider draw.
- T2 encountered only non-repairable issues, so the intended feedback
  mechanism could not activate.
- A post-result utility design would create researcher degrees of freedom if
  labels were accessed before the protocol was closed.
- The deterministic template and verifier share a tightly constrained
  projection, contributing to the validity ceiling.

### Mitigation and residual impact

Model-visible initial request construction was identical across T1, each T1-B
draw, and T2 call 1 for all 42 relations. All relations were retained, and
paired comparisons used the same cohort. The utility threat was controlled by
freezing a protocol, auditing it independently, and stopping before label
access when two choices remained underclosed. The residual limitation is that
one realized run cannot establish general stochastic reliability.

## External validity

### Threats

- Results may not transfer to other HAI processes, HAI editions, SWaT, WADI,
  other CPS datasets, or other sampling conditions.
- Only the continuous-step delayed-response family was studied.
- Other provider/model versions may have different structured-output,
  numerical, and proposal behavior.
- No deployed runtime, detector, or operating-regime interaction was tested.
- P1-bounded relation evidence cannot support full-system attack attribution,
  root-cause identification, or causal explanation.

### Residual impact

Generalization claims must be restricted to the frozen HAI P1 cohort and
construction contract. External datasets, relation families, providers, and
runtime settings remain future work.

## Statistical conclusion validity

### Threats

- The primary construction unit is the relation, N=42.
- T1-B's 126 calls are repeated provider draws, not 126 independent scientific
  relations.
- Three T2 discordances yield a supplementary exact two-sided paired p-value
  of 0.25, which is weakly informative at this sample size.
- Ceiling effects reduce power to discriminate T0, T1, and T1-B.
- Origin memberships overlap; subgroup rows are not independent, and GDN N=5
  is especially small.
- Direct-number statistics are descriptive summaries of one complete cohort.
- No utility estimate, confidence interval, or hypothesis test exists because
  utility was not executed.

### Mitigation and residual impact

The analysis uses all 42 relations, paired exact logic for binary
discordances, and separate relation-level and provider-call denominators. It
does not run naive independent-sample tests on T1-B calls or causal subgroup
tests. Statistical inference remains secondary to the exact descriptive
results.

## Conclusion boundary

The limitations do not invalidate the demonstrated construction-governance
result. They do prevent a claim that the constructed rules improve anomaly
detection. The thesis is defensible if its title, questions, contributions,
and abstract remain at the governed construction and deterministic calibration
layers.
