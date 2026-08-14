# Discussion Draft

## 7.1 Defensible thesis position

The results support a thesis about **governed, evidence-bound rule
construction for explainable multivariate CPS anomaly detection**. The
contribution is not an empirically superior agentic arm. It is the controlled
construction and governance framework: normal-only relation evidence,
deterministic numeric references, bounded structured proposals, deterministic
validity admission, explicit `no_rule`, separated utility authority, and an
intended LLM-free execution boundary.

The empirical contribution ends at construction validity and numerical
calibration. Downstream anomaly utility, detector integration, Rule v2, and
production runtime were not evaluated.

## 7.2 Discussion branch C: T2 below T1-B

On the observed construction-validity endpoint, T2 accepted 39/42 relation
directions while T1-B accepted 42/42. The three discordances all favored
T1-B. This is a negative T2 construction result and should appear explicitly:

> Incremental validity benefit of T2 was not observed in this run.

The result is not evidence that feedback repair is ineffective in general,
because the feedback pathway was never eligible. All three rejected T2
proposals used unsupported variables and were classified non-repairable.
Feedback eligibility, revise, retrieve, follow-up generation, and successful
recovery were all zero. The realized T2 treatment was therefore one initial
generation followed by deterministic fail-closed termination, not an
empirical test of feedback recovery.

T2 remains defensible as a bounded verifier-feedback architecture with
explicit fail-closed behavior. It is not defensible as the empirical
superiority headline.

## 7.3 Discussion branch D: validity ceiling and limited discrimination

T0, T1, and T1-B each obtained 42/42 verifier acceptance. This ceiling has
three consequences.

First, deterministic verifier-admissibility is achievable by the template
baseline for every relation in this cohort. That demonstrates the consistency
of the evidence projection and verifier, but it prevents validity alone from
showing incremental value from LLM generation.

Second, T1's 42/42 result is still meaningful. It shows that a single bounded
LLM call can populate the frozen proposal contract for all 42 relations in
this cohort and realized run. It does not establish general provider
reliability or general CPS rule-construction competence.

Third, T1-B's final 42/42 yield cannot be interpreted as a broad superiority
result. It recovered one relation that failed on its first draw, but the second
draw recovered none and the third recovered one, at 84 additional calls beyond
the first-draw budget. Repeated sampling therefore supplied limited stochastic
robustness at three times T1's provider-call cost.

The ceiling does not make T0 the scientifically best arm. It means that the
current endpoint cannot distinguish downstream usefulness. Labeled utility
would be needed for such a determination, and it was not evaluated.

## 7.4 Deterministic calibration

The Direct-number experiment provides the clearest empirical evidence for a
design choice. All 42 responses satisfied the output structure, with no
missing, nonfinite/parse, or sign-domain failures, yet their normalized errors
were often large. Every source-step-threshold and target-noise-scale estimate
exceeded 0.25 normalized absolute error; target-noise-scale error was highly
dispersed, with mean 39.6043 and P90 86.5962.

The appropriate conclusion is not that LLM numerical estimation is universally
impossible. It is that, under the frozen cohort, model, prompt, and numeric
roles, schema correctness was not numerical accuracy. This directly supports
project-side calibration from authorized normal data and the policy that LLM
proposals reference rather than invent authoritative numeric values.

## 7.5 Fail-closed `no_rule`

The three T2 `no_rule` outcomes are positive evidence for construction
governance but negative evidence for T2 yield. The deterministic verifier and
controller prevented unsupported-variable proposals from entering the
accepted set. That supports claim G at the admission layer.

The result must not be extended to deployed-system safety. `no_rule` did not
measure attack coverage, false alarms, detector behavior, runtime abstention,
or beneficial utility. It means only that invalid construction proposals were
not accepted and were not replaced post hoc by another arm.

## 7.6 Candidate discovery and origin

META, STAT, and GDN exposed different candidate sets, and the unscored top-20
union contained 47 pairs. Subsequent D1/D2 evidence was computed arm-blind for
each unique pair, so a shared pair had the same scientific outcome regardless
of its origin memberships. This design prevents origin labels from changing
the evidence result.

Origin summaries remain exploratory. Memberships overlap, and only five final
construction relations had GDN membership. The concentration of two T2
`no_rule` outcomes among those five is too small and too confounded by overlap
to establish a candidate-origin effect.

## 7.7 Utility boundary

Utility was scientifically motivated precisely because validity saturated and
does not measure anomaly performance. A post-result, pre-label protocol was
frozen to control label-aware choices. Independent auditing found unresolved
evaluator-authority issues. After bounded remediation, the focused re-audit
still found an unbound abstention denominator and fail-closed input/state gaps.

Stopping was the scientifically correct action. Real labels and test features
were not accessed, and utility was not computed. This governance outcome
protects the claim boundary, but it substantially weakens any thesis framing
that promises anomaly-detection effectiveness. It does not erase the narrower
construction/governance contribution.

## 7.8 Contribution synthesis

The demonstrated contributions are:

1. a controlled candidate-to-confirmed-relation pipeline for one bounded HAI
   P1 cohort;
2. deterministic normal-data numerical calibration and reference binding;
3. bounded structured construction across deterministic, one-shot,
   repeated-sampling, and verifier-feedback strategies;
4. deterministic validity admission separated from downstream utility;
5. explicit fail-closed `no_rule` handling;
6. a transparent comparison that preserves both positive and negative
   construction results; and
7. governance that prevented unauthorized label-aware evaluation.

The LLM-free downstream boundary is part of the design, not a validated
runtime result.

## 7.9 Positions to avoid

- T2 improves validity or its feedback recovery was validated.
- T0, T1, or T1-B is the useful-rule winner.
- The rules improve anomaly detection or detector false-negative recovery.
- T1 demonstrates general LLM reliability.
- T1-B generally improves reliability or is cost-effective.
- `no_rule` establishes deployment safety.
- Candidate origin causes construction success.
- Direct-number output proves a universal inability to estimate numbers.
- Utility failed, was negative, or was zero.

## 7.10 Future-work boundary

Future work may revisit labeled utility only under a complete, independently
audited evaluator authority. It must not be framed as a promised positive
result or a rescue experiment for T2. Detector integration, Rule v2/runtime
validation, external datasets, and an experiment that actually encounters
repairable feedback cases remain possible future directions, not completed
evidence.

No additional scientific experiment is required for a narrowly scoped
construction-and-governance master's thesis. The immediate work is editorial:
align the title, questions, methods, Results, Discussion, and later abstract
with this boundary. If the thesis retains a primary claim of anomaly-detection
effectiveness, labeled utility becomes necessary; that broader claim should be
removed rather than implied without evidence.
