# Thesis RQ-to-Result Mapping V1

Status: `FROZEN_FOR_MASTER_DRAFT_V1`

This document is the bridge between the Method, Results, Discussion, and
Conclusion chapters. It prevents a result from being used to answer a broader
question than the evidence permits.

## Summary mapping

| RQ | Required evidence | Result sections | Answer | Claim status |
|---|---|---|---|---|
| RQ1 Evidence-bound construction feasibility | Candidate attrition, confirmation, E1 materialization, arm acceptance | 6.1–6.4 | Feasible within the 42-relation HAI P1 cohort | A/B `SUPPORTED` |
| RQ2 Strategy comparison | Paired validity, T1-B behavior, T2 controller, call accounting | 6.4–6.5 | Validity ceiling for T0/T1/T1-B; limited T1-B robustness; negative T2 result | C `PARTIALLY_SUPPORTED`; D/E `NOT_SUPPORTED` |
| RQ3 Numeric estimation accuracy | Direct-number role-wise normalized errors | 6.6 | Schema-valid estimates were numerically inaccurate; calibration rationale supported | F `SUPPORTED` |
| RQ4 Fail-closed admission | Three unsupported-variable T2 proposals and final outcomes | 6.4–6.5 | All three invalid proposals were excluded as `no_rule` | G `SUPPORTED` at admission layer |

## RQ1 evidence chain

### Input-to-construction attrition

| Stage | Input | Authorized result | Interpretation |
|---|---:|---:|---|
| Candidate discovery | 144-pair P1 universe | 47-pair unscored union from three top-20 lists | Candidate plausibility only |
| D1 relation fitting | 47 pairs / 94 directions | 25 supported pairs / 45 supported directions | Normal-only fit support |
| D2 confirmation | 45 directions | 42 confirmed directions across 23 pairs | One-way normal calibration confirmation |
| E1 materialization | 42 confirmed directions | 42 evidence records, 42 numeric bundles, 462 bindings | Construction input authority |
| Construction | 42 relation directions per arm | T0/T1/T1-B 42 accepted; T2 39 accepted + 3 `no_rule` | Verifier-admissibility only |

### RQ1 answer text

> Within the frozen HAI P1 cohort, the candidate-to-evidence pipeline produced
> 42 confirmed directional relations with deterministic numeric-reference
> authority. These inputs were transformable into verifier-admissible rule
> candidates for all 42 relations under T0, T1, and T1-B and for 39 under T2.
> The result supports bounded construction feasibility, not downstream anomaly
> utility.

### Tables and figures

- Table 1: candidate discovery.
- Table 2: D1 fitting and D2 confirmation.
- Table 3: construction arm validity.
- Figure 1: seven-stage evidence-to-admission pipeline.
- Optional Figure 2: evidence attrition 144 → 47 → 25/45 → 42.

## RQ2 evidence chain

### Paired construction outcomes

| Arm | Provider calls | Accepted | `no_rule` | Calls per accepted | Interpretation |
|---|---:|---:|---:|---:|---|
| T0 | 0 | 42 | 0 | N/A | Deterministic baseline; verifier ceiling |
| T1 | 42 | 42 | 0 | 1.000 | One-call feasibility for cohort/run |
| T1-B | 126 | 42 | 0 | 3.000 | Same final yield as T1 at 3× calls |
| T2 | 42 | 39 | 3 | 1.077 | Three fewer accepted than T1 at equal call count |

T0, T1, and T1-B were completely concordant. Comparisons of each against T2
contained three discordances, all favoring the non-T2 arm; the absolute
difference was 7.14 percentage points and the supplementary exact two-sided
paired p-value was 0.25.

### T1-B robustness evidence

- Provider calls: 126.
- Materialized proposals: 125.
- Admissible proposals: 122.
- Verifier-rejected proposals: 3.
- Schema-parse failures: 1.
- Cumulative yield after calls 1/2/3: 41/41/42.
- Marginal recovery after calls 2/3: 0/1.
- Selected-call distribution 1/2/3: 41/0/1.

### T2 controller evidence

- Calls: 42.
- Accepted / `no_rule`: 39/3.
- Feedback eligible: 0.
- Revise / retrieve / follow-up / recovery: 0/0/0/0.
- Three issues: unsupported variables, classified non-repairable.

### RQ2 answer text

> Deterministic template, one-shot LLM, and repeated-sampling construction all
> reached 42/42 relation-level verifier acceptance, producing a validity
> ceiling. T1 achieved that result with 42 calls. T1-B used 126 calls and
> recovered one first-draw rejection on call 3, providing limited stochastic
> robustness at three times T1's call cost. T2 accepted 39/42 with 42 calls.
> Its feedback path was not exercised, and incremental validity benefit was not
> observed.

### Tables and figures

- Table 3: construction arm validity.
- Table 4: provider-call / validity efficiency.
- Table 5: T1-B repeated-sampling behavior.
- Table 6: T2 controller behavior.
- Optional Figure 3: validity yield versus provider calls, explicitly labeled
  as a construction-validity/cost frontier rather than a utility plot.

## RQ3 evidence chain

| Role | Mean | Median | Q1 | Q3 | P90 | Count >0.25 |
|---|---:|---:|---:|---:|---:|---:|
| Source step threshold | 0.6621 | 0.5984 | 0.4811 | 0.7443 | 0.9938 | 42/42 |
| Source stability tolerance | 1.1381 | 0.4904 | 0.1728 | 0.9765 | 5.3937 | 24/42 |
| Target noise scale | 39.6043 | 0.9839 | 0.8232 | 28.4537 | 86.5962 | 42/42 |

All 42 records were structurally valid, with zero missing, nonfinite/parse, or
sign-domain violations.

### RQ3 answer text

> Direct LLM estimates satisfied the output schema but did not closely
> reproduce the deterministic normal-derived references. The observed errors,
> especially for target noise scale, support retaining project-side
> deterministic calibration for the frozen contract. This is a bounded
> calibration rationale, not a universal statement about LLM numeracy.

### Tables and figures

- Table 7: Direct-number normalized errors and exceedances.
- Optional Figure 4: role-wise error distribution using already-sanitized
  figure-ready summaries only; no new experiment or private values.

## RQ4 evidence chain

Three T2 proposals referenced unsupported variables. The deterministic
verifier/controller rejected each, classified each issue non-repairable, and
returned `no_rule`. No relation was dropped from the 42-relation denominator,
and no T0/T1/T1-B proposal was substituted.

### RQ4 answer text

> For the three invalid proposals observed in this run, deterministic
> verification and explicit `no_rule` admission prevented entry into the
> accepted candidate set. The result supports fail-closed construction
> admission; it does not establish runtime or deployment safety.

### Tables and figures

- Table 3: accepted and `no_rule` outcomes.
- Table 6: T2 controller and non-repairable outcomes.
- No separate safety-performance figure.

## Claim-to-RQ consistency matrix

| Claim | Frozen status | Primary RQ | Required wording |
|---|---|---|---|
| A Pipeline feasibility | `SUPPORTED` | RQ1 | Feasible within this cohort and verifier contract |
| B One-call T1 feasibility | `SUPPORTED` | RQ1/RQ2 | One frozen call per relation in this run |
| C Repeated-sampling robustness | `PARTIALLY_SUPPORTED` | RQ2 | One recovery at 3× T1 call cost |
| D T2 validity improvement | `NOT_SUPPORTED` | RQ2 | Incremental benefit not observed; feedback unexercised |
| E T2 efficiency advantage | `NOT_SUPPORTED` | RQ2 | Did not improve observed validity/call frontier |
| F Calibration rationale | `SUPPORTED` | RQ3 | Schema validity did not imply numerical accuracy |
| G `no_rule` admission safety | `SUPPORTED` | RQ4 | Invalid proposals excluded at construction admission |
| H Candidate-origin effect | `INCONCLUSIVE` | Exploratory | Overlap and GDN N=5 prevent an origin-effect claim |

## Results-to-Discussion mapping

| Result | Discussion interpretation | Prohibited rescue/overclaim |
|---|---|---|
| T0/T1/T1-B 42/42 | Validity ceiling and endpoint discrimination limit | Declaring a useful-rule winner |
| T1 42/42 with 42 calls | One-call feasibility in cohort/run | General LLM reliability |
| T1-B call-3 recovery | Limited stochastic robustness | Best-of-three generally improves reliability |
| T2 39/42 | Negative construction-validity result | T2 superiority |
| T2 feedback counts zero | Mechanism not empirically exercised | Claiming an empirical feedback benefit |
| Three T2 `no_rule` | Fail-closed construction admission | Deployment safety or beneficial utility |
| Direct-number error | Deterministic calibration rationale | Universal LLM numeric incapacity |
| Origin subgroup | Exploratory/inconclusive | Claiming a causal origin effect |
| Utility stop before labels | Governance boundary and thesis limitation | Failed/negative/zero utility result |

## Utility boundary

No RQ is answered with a labeled utility result. U1–U6 retain execution status
`NOT_EXECUTED`. The master draft must state **utility was not evaluated** and
must not include a utility-performance table.
