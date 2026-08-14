# Thesis Contributions V1

Status: `FROZEN_FOR_MASTER_DRAFT_V1`

The contributions are stated at the construction, calibration, verification,
and governance layers. None asserts downstream anomaly-detection improvement.

## C1 — Evidence-bound candidate-to-rule construction pipeline

> A bounded pipeline connecting multi-source candidate discovery, normal-only
> relation profiling and confirmation, deterministic parameter references,
> structured proposal construction, and deterministic admission.

### Methodological contribution

The framework preserves explicit boundaries between candidate evidence,
confirmed normal relations, numeric authority, construction proposals,
verifier outcomes, and downstream utility authority. META, STAT, and GDN are
candidate-evidence sources rather than competing causal truths.

### Empirical support

- 47 distinct candidate pairs in the unscored three-method union.
- 25 fit-supported pairs and 45 supported directions after D1.
- 42 confirmed directions after one-way D2 confirmation.
- 42 construction-evidence records and deterministic numeric bundles.
- Accepted candidates for all 42 directions in T0, T1, and T1-B and 39 in T2.

### Boundary

C1 demonstrates bounded construction feasibility within HAI 23.05 P1. It does
not demonstrate causality, anomaly utility, explanation quality, or external
generalization.

## C2 — Deterministic normal-data numeric authority

> A numeric-authority design that binds rule parameters to deterministic
> normal-derived calibration references rather than permitting the LLM to
> invent authoritative values.

### Methodological contribution

Construction proposals refer to frozen source thresholds, stability
tolerances, target scales, delay horizons, and window constants. Numeric
authority remains outside the provider proposal.

### Empirical support

The Direct-number experiment produced structurally valid output for all 42
relations but substantial normalized errors. In particular, every source-step-
threshold and target-noise-scale estimate exceeded 0.25 normalized error.
Schema correctness therefore did not imply numerical accuracy under the
frozen contract.

### Boundary

C2 supports deterministic calibration for this study. It does not claim that
all LLM numeric estimates are inaccurate or that the observed errors imply a
measured downstream utility loss.

## C3 — Deterministic verification and fail-closed construction admission

> A deterministic verifier and explicit `no_rule` admission mechanism that
> prevent verifier-invalid construction proposals from entering the accepted
> rule-candidate set without post-hoc substitution.

### Methodological contribution

The outcome vocabulary distinguishes accepted candidate, `no_rule`, `no_op`,
runtime abstention, provider failure, and parse failure. Acceptance authority
belongs to the deterministic verifier/controller rather than the proposing
arm.

### Empirical support

Three T2 proposals referenced unsupported variables. All three were rejected,
classified non-repairable, and terminated as `no_rule`; none was replaced by a
candidate from T0, T1, or T1-B.

### Boundary

C3 is construction-admission evidence. It does not establish deployment
safety, anomaly utility, runtime abstention quality, or Rule v2 validation.

## C4 — Controlled construction-strategy comparison

> A relation-paired comparison of deterministic template, one-shot bounded
> LLM, independent repeated-sampling, and bounded verifier-feedback
> construction across validity yield, stochastic robustness, and provider-call
> cost, including neutral and negative findings.

### Methodological contribution

All arms operate on the same 42 confirmed relations and share the frozen
evidence/reference contract. Relation-level denominators remain separate from
provider-call/proposal denominators. Exact paired logic is supplementary to
the primary descriptive comparison.

### Empirical support

- T0: 42/42 accepted using zero provider calls.
- T1: 42/42 accepted using 42 calls.
- T1-B: 42/42 accepted using 126 calls; one first-draw rejection recovered on
  call 3 and one unselected schema-parse failure tolerated.
- T2: 39/42 accepted using 42 calls; three `no_rule` outcomes.
- T2 feedback eligibility, revise, retrieve, follow-up, and recovery: all zero.

### Boundary

C4 does not make an arm a downstream winner. It preserves the validity ceiling,
limited T1-B robustness, negative T2 result, and unexercised feedback path.

## Contribution-to-RQ matrix

| Contribution | RQ1 | RQ2 | RQ3 | RQ4 | Evidence status |
|---|---:|---:|---:|---:|---|
| C1 Evidence-bound pipeline | Primary | Supporting | - | Supporting | Supported within cohort |
| C2 Deterministic numeric authority | Supporting | - | Primary | - | Supported within contract |
| C3 Fail-closed admission | Supporting | Supporting | - | Primary | Supported at admission layer |
| C4 Strategy comparison | Supporting | Primary | - | Supporting | Mixed positive/negative result |

## Design principles, not completed empirical results

The following are important framework properties but must not be presented as
empirically validated downstream contributions:

- strict separation of construction validity and labeled utility;
- bounded verifier-feedback architecture for T2;
- intended LLM-free downstream execution;
- private/public custody and staged authorization;
- a post-result utility protocol and the governance decision to stop before
  unauthorized label access.

They support reproducibility and claim discipline. They do not substitute for
utility or runtime observations.

## Prohibited contribution claims

- Improved anomaly detection or detector false-negative recovery.
- T2, agentic, LLM, or candidate-method superiority.
- Empirically validated verifier-feedback recovery.
- LLM semantic-rule superiority over deterministic construction.
- Production Rule v2, runtime, deployment, or safety validation.
- A utility-adjusted construction winner.
