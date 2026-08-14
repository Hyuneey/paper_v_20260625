# Thesis Research Questions V1

Status: `FROZEN_FOR_MASTER_DRAFT_V1`

The thesis has three primary research questions and one secondary governance
question. Every question is answerable using already-authorized evidence. No
question requires labeled anomaly utility.

## RQ1 — Evidence-bound construction feasibility

> **Within the frozen HAI P1 cohort, can confirmed multivariate CPS relation
> directions and deterministic normal-data parameter references be transformed
> into verifier-admissible rule candidates under a bounded construction
> protocol?**

### Operationalization

- Scientific unit: confirmed directional relation, N=42.
- Inputs: the 47-pair candidate union, normal-only relation fitting, one-way
  relation confirmation, and deterministic E1 numeric-reference bundles.
- Endpoint: an accepted rule candidate passing the deterministic construction
  verifier, reported separately from `no_rule`.
- Evidence: 25/47 fit-supported pairs, 42/45 confirmed directions, 42 E1
  materializations, and arm-level construction outcomes.

### Answer supported by the evidence

Yes, within this cohort and contract. Every confirmed direction produced an
accepted candidate under T0, T1, and T1-B; T2 produced accepted candidates for
39 directions and `no_rule` for three. This is construction feasibility, not
anomaly-detection utility.

### Claim links

- Claim A: `SUPPORTED`.
- Claim B: `SUPPORTED` for the T1 one-call realization.
- Contribution C1 and the evidence-binding portion of C2.

## RQ2 — Construction-strategy comparison

> **How do deterministic template construction, one-shot bounded LLM
> construction, independent repeated LLM sampling, and bounded verifier-
> feedback construction differ in relation-level validity yield, stochastic
> robustness, and provider-call cost?**

### Operationalization

- Paired unit: the same 42 relations across T0, T1, T1-B, and T2.
- Primary descriptive endpoints: accepted count/rate, `no_rule` count,
  discordant relation counts, and absolute percentage-point differences.
- Robustness endpoints: T1-B admissible-proposal distribution, selected-call
  distribution, parse/rejection accounting, and cumulative yield after each
  call.
- Cost endpoints: provider calls, calls per accepted relation, and accepted
  relations per provider call.
- Supplementary inference: exact paired McNemar/binomial logic for discordant
  binary outcomes; p-values remain secondary.

### Answer supported by the evidence

T0, T1, and T1-B each accepted 42/42, creating a construction-validity
ceiling. T1 did so with 42 calls. T1-B used 126 calls and recovered one
first-draw rejection on call 3; this is limited stochastic robustness at three
times T1's call cost. T2 used 42 calls and accepted 39/42. Its intended
feedback path was not empirically exercised because all three rejected cases
were classified non-repairable. Incremental validity benefit of T2 was not
observed.

### Claim links

- Claim C: `PARTIALLY_SUPPORTED`.
- Claim D: `NOT_SUPPORTED`.
- Claim E: `NOT_SUPPORTED`.
- Contribution C4.

## RQ3 — Direct numeric estimation versus deterministic calibration

> **How accurately does direct LLM estimation reproduce the deterministic
> normal-derived numeric references required by the frozen rule contract?**

This phrasing replaces “sufficiently accurate.” No independent universal
sufficiency threshold was frozen, so the RQ is answered through exact
descriptive normalized errors and threshold exceedance counts.

### Operationalization

- Unit: relation, N=42 per numeric role.
- Roles: source step threshold, source stability tolerance, and target noise
  scale.
- Endpoint: normalized absolute error against the authoritative deterministic
  reference.
- Reporting: mean, median, population SD, type-7 Q1/Q3/P90, range, and counts
  exceeding 0.10, 0.25, 0.50, and 1.00.
- Separation: structured/schema validity is reported independently from
  numerical error.

### Answer supported by the evidence

All 42 outputs were structurally valid, yet numerical errors were substantial.
Every source-step-threshold and target-noise-scale estimate exceeded 0.25
normalized error; target-noise-scale errors were especially large and
dispersed. The evidence supports deterministic normal-data calibration for
this frozen contract. It does not establish that LLM numeric estimation is
universally inaccurate.

### Claim links

- Claim F: `SUPPORTED`.
- Contribution C2.

## Secondary RQ4 — Fail-closed construction admission

> **When a construction proposal violates the frozen contract, can
> deterministic verification and explicit `no_rule` admission prevent it from
> entering the accepted rule set?**

RQ4 is secondary because it is supported by three realized invalid proposals,
not a broad runtime-safety trial.

### Operationalization

- Unit: relation-arm construction cell.
- Evidence: three T2 proposals containing unsupported variables.
- Required behavior: deterministic rejection, non-repairable classification,
  termination as `no_rule`, and no substitution from another arm.
- Endpoint: invalid proposals admitted into the accepted set, expected count
  zero.

### Answer supported by the evidence

Yes at the construction-admission layer in this run. All three unsupported-
variable proposals were rejected and became `no_rule`; none entered the
accepted candidate set. This does not demonstrate downstream utility,
production safety, runtime abstention behavior, or a general safety theorem.

### Claim links

- Claim G: `SUPPORTED`.
- Contribution C3.

## Questions explicitly outside the completed thesis

The following are not research questions in the completed empirical study:

- Do accepted candidates improve anomaly-event recall or false-alarm burden?
- Does T2 `no_rule` produce a favorable utility trade-off?
- Do the rules improve an existing detector's false-negative recovery?
- Which arm is best on downstream utility?
- Does production Rule v2/runtime behavior satisfy the intended contract?
- Does candidate origin causally determine construction success?

All labeled utility questions remain `NOT_EXECUTED`. Utility was not evaluated.

## Chapter mapping

| RQ | Method | Results | Discussion | Main contribution |
|---|---|---|---|---|
| RQ1 | Sections 4.2–4.7; 5.3–5.5 | Sections 6.1–6.4 | Sections 7.1 and 7.3 | C1, part of C2 |
| RQ2 | Sections 4.6–4.7; 5.5–5.6 | Sections 6.4–6.5 | Sections 7.2–7.3 | C4 |
| RQ3 | Sections 4.5; 5.7 | Section 6.6 | Section 7.4 | C2 |
| RQ4 | Sections 4.7; 5.5 | Sections 6.4–6.5 | Section 7.5 | C3 |
