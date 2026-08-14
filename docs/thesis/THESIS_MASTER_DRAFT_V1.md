# Thesis Master Draft V1

Status: `STRUCTURED_MASTER_DRAFT_V1`

Working title:

> **Evidence-Bound and Verifiable Rule Construction for Explainable
> Multivariate CPS Anomaly Detection**

This is a master skeleton, not a submission-ready manuscript. Bracketed notes
identify editorial or literature work that remains. Empirical statements are
restricted to the authorized evidence summarized in
`THESIS_MASTER_EVIDENCE_MAP.md`.

## Abstract

**Intentionally not drafted.** The final abstract remains the last writing
stage. Its claim inventory is limited to:

- a governed evidence-bound pipeline evaluated on 42 confirmed HAI P1
  relation directions;
- T0/T1/T1-B acceptance of 42/42 and T2 acceptance of 39/42;
- cohort/run-bounded T1 one-call feasibility;
- limited T1-B robustness at three times T1's provider-call cost;
- three fail-closed T2 `no_rule` outcomes, with no observed incremental T2
  validity benefit and no exercised feedback path;
- Direct-number evidence supporting deterministic normal-data calibration;
  and
- the material qualification that downstream labeled utility was not
  evaluated.

The abstract must not claim detector improvement, T2 superiority, validated
feedback recovery, production runtime validation, or a useful-rule winner.

# 1. Introduction

## 1.1 Background and motivation

Cyber-physical systems produce multivariate time series in which control
actions and process responses are related across time. Such relations can
support interpretable rule candidates, but a plausible relation alone does not
establish a trustworthy rule. Construction also requires evidence provenance,
numerical parameter authority, a bounded proposal language, and an admission
mechanism independent of the proposing component.

Large language models offer structured proposal capability, yet unconstrained
generation creates two distinct risks: unsupported semantic fields and
invented numeric values. This thesis addresses those risks at the construction
layer. It combines normal-only relation evidence, deterministic numeric
references, bounded proposal construction, and deterministic verification.

## 1.2 Research problem

The central problem is not whether a language model can emit syntactically
valid JSON. It is whether confirmed multivariate CPS relation evidence and
normal-derived numeric authority can be transformed into verifier-admissible
rule candidates under a controlled and reproducible contract. A second problem
is how alternative construction strategies differ when evaluated on the same
relations with distinct relation-level and provider-call denominators.

The intended application is explainable multivariate CPS anomaly detection.
However, verifier-admissibility is not anomaly utility. The completed empirical
study therefore evaluates construction feasibility, validity yield,
stochastic robustness, call cost, numeric estimation error, and fail-closed
admission. Labeled utility and production runtime remain outside the completed
scope.

## 1.3 Research gap

Existing lines of work separately address candidate relations, rule-based
explanation, LLM generation, or validation. The gap addressed here is their
governed integration: candidate evidence is narrowed through normal-data
profiling and confirmation; numeric values retain deterministic provenance;
LLM involvement is constrained to a bounded proposal contract; and acceptance
belongs to an independent deterministic verifier.

[[Add literature-grounded comparison showing which prior approaches omit one
or more of evidence binding, numeric authority, bounded construction, or
independent admission. Do not claim exhaustive novelty without the completed
Related Work review.]]

## 1.4 Research questions

The three primary questions are:

1. **RQ1:** Within the frozen HAI P1 cohort, can confirmed multivariate CPS
   relation directions and deterministic normal-data parameter references be
   transformed into verifier-admissible rule candidates under a bounded
   construction protocol?
2. **RQ2:** How do deterministic template construction, one-shot bounded LLM
   construction, independent repeated LLM sampling, and bounded verifier-
   feedback construction differ in relation-level validity yield, stochastic
   robustness, and provider-call cost?
3. **RQ3:** How accurately does direct LLM estimation reproduce the
   deterministic normal-derived numeric references required by the frozen rule
   contract?

A secondary governance question is:

4. **RQ4:** When a construction proposal violates the frozen contract, can
   deterministic verification and explicit `no_rule` admission prevent it
   from entering the accepted rule set?

No RQ requires labeled anomaly utility.

## 1.5 Contributions

This thesis makes four bounded contributions:

- **C1:** an evidence-bound candidate-to-rule construction pipeline;
- **C2:** deterministic normal-data numeric authority and reference binding;
- **C3:** deterministic verification and fail-closed `no_rule` admission; and
- **C4:** a controlled relation-paired comparison of T0/T1/T1-B/T2 that
  preserves validity yield, stochastic robustness, call cost, and negative
  findings.

The contributions are empirical at the construction-validity and calibration
layers and methodological at the authority-separation layer. They are not
claims of downstream anomaly performance.

## 1.6 Scope and boundaries

The empirical scope is HAI 23.05 P1, the continuous-step delayed-response
relation family, 42 confirmed directional relations, and one frozen
provider/model execution contract. Candidate-origin summaries are exploratory.
Detector integration, labeled utility, Rule v2, production runtime,
deployment, and winner selection are excluded.

## 1.7 Thesis organization

Chapter 2 reviews related work. Chapter 3 formalizes the construction problem
and authority layers. Chapter 4 presents the seven-stage framework. Chapter 5
defines the experimental design. Chapter 6 reports authorized results. Chapter
7 interprets the validity ceiling, construction strategies, calibration
evidence, fail-closed admission, and utility boundary. Chapter 8 answers the
RQs and closes at the demonstrated construction-governance scope.

# 2. Related Work

## 2.1 Multivariate CPS anomaly detection

[[Review model-based, data-driven, and hybrid CPS anomaly-detection methods.
Separate detector performance from rule-construction and explanation claims.]]

## 2.2 Explainable and rule-based approaches

[[Review rule representations, traceability, and explainability. Distinguish
human-readable rules from empirically validated explanation quality.]]

## 2.3 Relation and graph candidate discovery

[[Review metadata/knowledge-driven, statistical, and graph-neural candidate
discovery. Maintain the distinction between candidate/predictive relations and
causality.]]

## 2.4 Normal-data relation profiling

[[Review methods that infer stable process relations from normal operation,
including delayed responses and calibration transfer.]]

## 2.5 LLM-assisted structured construction

[[Review constrained structured generation, tool use, feedback loops, and
known numeric-reasoning limitations. Avoid describing the present T2 result in
the literature section.]]

## 2.6 Deterministic verification and governance

[[Review independent validation, typed contracts, fail-closed outcomes, and
separation of validity from utility.]]

## 2.7 Gap summary

The thesis targets the combined gap: a traceable path from heterogeneous
candidate evidence through normal relation confirmation and deterministic
numeric authority to bounded proposal construction and independent admission.

# 3. Problem Formulation

## 3.1 Dataset and process scope

The study uses the verified HAI 23.05 edition at one-second nominal sampling
and is bounded to P1 Boiler. The process freeze establishes morphology and
scope; it does not provide causal, rule, runtime, or anomaly-performance
authority.

## 3.2 Relation family

A construction input is a confirmed directional relation connecting a bounded
source stream and target stream. The relation specifies source-step direction,
target-response direction, and a selected delay horizon under the frozen
continuous-step delayed-response protocol. Normal-derived references define
the source step threshold, source stability tolerance, target response scale,
and window constants.

[[Insert formal notation for source x, target y, direction d, delay h,
reference bundle theta, proposal p, verifier V, and outcome o.]]

## 3.3 Units and denominators

The primary construction unit is the directional relation, N=42. A proposal is
one materialized candidate object. A provider call may or may not materialize a
proposal. A relation-arm cell has one final accepted/`no_rule` outcome.
Repeated calls are not independent relation samples.

## 3.4 Evidence-to-rule transformation

For relation r with normal-relation evidence e and numeric-reference bundle
theta, a construction policy produces a bounded proposal p. The deterministic
verifier evaluates p against r, e, theta, and the frozen schema. Acceptance
means construction-contract conformity only.

## 3.5 Construction strategies

T0 is deterministic template construction. T1 is one bounded LLM call per
relation. T1-B uses three independent calls without verifier feedback and
selects the lowest-index admissible proposal. T2 is a bounded verifier-feedback
controller with deterministic repairability classification and explicit
`no_rule` termination.

## 3.6 Outcome and authority states

`no_rule` means no candidate was admitted for a construction cell. It is not
provider failure, `no_op`, runtime abstention, or a utility outcome. An accepted
candidate is not a runtime-authorized rule. Construction validity, utility,
runtime, deployment, and winner authority remain distinct.

## 3.7 Evaluation constructs

RQ1 uses relation-level verifier acceptance. RQ2 uses paired relation outcomes,
repeated-sampling traces, and provider-call accounting. RQ3 uses normalized
numeric error against deterministic references. RQ4 uses invalid-proposal
exclusion and final `no_rule` outcomes.

# 4. Proposed Framework

## 4.1 Overview

The framework has seven stages: candidate discovery, normal relation
profiling, one-way confirmation, deterministic numeric calibration,
construction, deterministic verification, and construction analysis. Figure 1
will show labeled utility and runtime as a dashed, out-of-scope downstream
layer.

[[Insert the architecture diagram from `THESIS_METHOD_STORY_V1.md`.]]

## 4.2 Candidate discovery

META, STAT, and GDN generate complementary candidate evidence from the frozen
P1 universe. Each contributes a primary top-20 list. Integration is an unscored
union with exact de-duplication and provenance retention. Candidate-origin
scores are not merged or compared as though they shared one measurement scale.

## 4.3 Normal relation profiling

The arm-blind D1 protocol evaluates the 47-pair union on normal train1/train2.
It tests directional continuous-step delayed-response support under frozen
gates. Candidate origin cannot change a pair's scientific outcome.

## 4.4 One-way relation confirmation

D2 replays the D1-supported directions on train3 with no retuning, fallback,
opposite-direction search, or alternative-horizon search. The output is a
calibration-confirmed normal relation direction, not a causal relation.

## 4.5 Deterministic calibration and evidence materialization

E1 binds each confirmed relation to normal-derived source thresholds,
stability tolerances, target scales, horizons, and window references. These
references—not provider-generated numbers—are authoritative during
construction.

## 4.6 Common proposal contract

All arms use one structured contract containing the relation identity,
variables, directions, selected horizon, numeric-reference identities, window
references, and runtime-logic family. Unsupported variables, arbitrary numeric
literals, reference mismatches, and structural errors are verifier failures.

## 4.7 Construction arms

The construction arms differ in proposal policy and call budget while sharing
the same evidence/reference contract. Provider-arm initial requests use the
same frozen prompt, schema, model, sampling contract, and relation input; arm
identity is not model-visible.

### 4.7.1 T0 deterministic template

T0 projects the frozen evidence/reference contract into a deterministic
proposal and uses no provider call.

### 4.7.2 T1 one-shot bounded LLM

T1 requests one structured proposal for each relation. No feedback or second
draw is available.

### 4.7.3 T1-B independent repeated sampling

T1-B makes three independent calls per relation without feedback and selects
the lowest-index admissible proposal. All three calls are consumed even if an
earlier proposal is admissible, preserving the frozen sampling design.

### 4.7.4 T2 bounded verifier-feedback construction

T2 may revise or retrieve only after a deterministic repairability decision
and within its fixed budget. Non-repairable issues terminate as `no_rule`.
This subsection defines an architecture; whether the feedback path was
exercised is reported only in Chapter 6.

## 4.8 Deterministic verification and admission

The verifier checks structural, relation, evidence, direction, horizon,
numeric-reference, numeric-origin, variable, and literal requirements. The
verifier is independent of the proposing arm. Accepted candidates and
`no_rule` outcomes remain relation-arm specific; no cross-arm substitution is
permitted.

## 4.9 Direct-number calibration ablation

The auxiliary Direct-number task asks for numeric values directly under the
same frozen evidence context. Its outputs have no main-rule threshold or
runtime authority. They are compared descriptively with deterministic
references to assess the calibration rationale.

## 4.10 Downstream boundary

The intended downstream architecture is LLM-free. The completed study did not
implement or validate production Rule v2/runtime, detector integration, or
labeled utility.

# 5. Experimental Design

## 5.1 Frozen cohort

The sequential evidence pipeline produced a construction cohort of 42
confirmed directional relations. All 42 are retained in every relation-level
comparison; no post-hoc exclusions are permitted.

## 5.2 Candidate, fitting, and confirmation design

The candidate stage applies pre-frozen top-20 policies and integrates an
unscored union. D1 uses normal train1/train2 for fitting. D2 uses train3 for
one-way confirmation without adaptation. The design prevents confirmation data
from changing the selected direction, horizon, or fit gate.

## 5.3 Arm comparability and call budgets

T0 uses zero provider calls. T1 uses one call per relation. T1-B uses exactly
three independent calls per relation. T2 is bounded to at most three calls per
relation, conditional on repairability and controller action. Provider calls
are counted even when parsing fails; a parse failure is not a proposal.

## 5.4 Construction-validity analysis

Primary outputs are accepted count/rate, `no_rule` count, paired concordance,
discordant counts, and absolute percentage-point difference. Complete
concordance is reported without a test. For discordant binary outcomes, an
exact two-sided paired McNemar/binomial p-value is supplementary.

## 5.5 Robustness and cost analysis

T1-B analysis records materialized, admissible, rejected, and parse-failed
draws; selected-call distribution; cumulative yield after calls 1, 2, and 3;
and marginal recovery. Cost analysis records calls per accepted relation and
accepted relations per provider call. No utility-weighted score is constructed.

## 5.6 T2 controller analysis

Feedback eligibility, revise, retrieve, follow-up generation, and successful
recovery are recorded separately. A feedback architecture is not treated as
empirically exercised unless at least one eligible path activates.

## 5.7 Direct-number analysis

For each of three numeric roles and all 42 relations, normalized absolute
errors are summarized by mean, median, population SD, type-7 quartiles/P90,
range, and counts above four frozen descriptive thresholds. Schema failure and
numeric-domain failure are reported separately from accuracy.

## 5.8 Origin subgroup analysis

META/STAT/GDN memberships overlap and remain exploratory. Full-cohort results
are primary; no causal or independent-sample subgroup inference is performed.

## 5.9 Reproducibility and stopping boundary

Scientific results are bound to frozen artifacts and receipts. The later
utility protocol was developed after the construction result and before label
access. Its focused re-audit left two authority/validation choices unresolved,
so utility execution remained unauthorized. No real label values, real test
features, or real utility values were accessed or computed.

# 6. Results

The relation direction is the primary construction unit. Provider calls and
proposals retain separate denominators.

## 6.1 Candidate discovery — RQ1

META, STAT, and GDN each contributed 20 primary candidates. Their unscored
union contained 47 distinct pairs. Method-only counts were 8, 8, and 18;
pairwise overlaps were 11 for META-STAT, 1 for META-GDN, and 1 for STAT-GDN,
with no three-way overlap. These counts describe candidate diversity rather
than candidate-method accuracy.

[[Insert Table 1 from `THESIS_RESULTS_DRAFT.md`.]]

## 6.2 Normal relation fitting — RQ1

D1 evaluated 47 pairs and 94 directional opportunities. Twenty-five pairs and
45 directions were fit-supported; 17 directions were unstable and 32 were
unsupported. Origin columns overlap and remain descriptive.

## 6.3 Relation confirmation — RQ1

D2 evaluated the 45 supported directions without adaptation. Forty-two
directions were confirmed, three conflicted, and 23 of 25 supported pairs
retained at least one direction. E1 then materialized 42 evidence records, 42
numeric bundles, and 462 bindings.

[[Insert Table 2.]]

## 6.4 Rule-construction validity — RQ1, RQ2, RQ4

T0, T1, and T1-B produced accepted candidates for 42/42 relations. T2 accepted
39/42 and returned `no_rule` for three. Thus, T0/T1/T1-B reached a relation-
level construction-validity ceiling.

The initial model-visible construction contract matched across T1, all three
T1-B draws, and T2 call 1 for all 42 relations. T0/T1/T1-B were completely
concordant. Each comparison of one of those arms against T2 had three
discordances, all favoring the non-T2 arm, an absolute difference of 7.14
percentage points, and a supplementary exact two-sided p-value of 0.25.

[[Insert Table 3: construction arm validity.]]

## 6.5 Construction robustness and call efficiency — RQ2, RQ4

T1 achieved 42/42 with 42 calls. T1-B used 126 calls, materialized 125
proposals, produced 122 admissible proposals, recorded three verifier
rejections and one schema-parse failure, and still accepted all 42 relations.
Its cumulative yield after calls 1/2/3 was 41/41/42; selected calls were
41/0/1. The extra two draw stages consumed 84 calls and recovered one relation.

T2 used 42 calls, accepted 39 relations, and returned three `no_rule`
outcomes. Feedback eligibility, revise, retrieve, follow-up, and recovery were
all zero. All three rejected proposals contained unsupported variables and
were classified non-repairable.

[[Insert Tables 4–6.]]

## 6.6 Direct-number experiment — RQ3

All 42 Direct-number records were structurally valid, with zero missing,
nonfinite/parse, or sign-domain failures. Numerical errors nevertheless were
substantial. Mean normalized error was 0.6621 for source step threshold, 1.1381
for source stability tolerance, and 39.6043 for target noise scale. Every
source-step-threshold and target-noise-scale estimate exceeded 0.25 error.

[[Insert Table 7 with median, population SD, Q1/Q3/P90, range, and all
threshold exceedances.]]

## 6.7 Candidate-origin subgroup — exploratory

The final relation cohort had overlapping META, STAT, and GDN memberships of
28, 32, and 5. T2 accepted 28/28 META, 30/32 STAT, and 3/5 GDN-member
relations. Because membership overlaps and GDN N=5, candidate-origin effect
remains `INCONCLUSIVE`.

## 6.8 Utility evaluation boundary

Labeled utility was scientifically motivated by the validity ceiling. A post-
result, pre-label protocol was frozen and audited. After bounded remediation,
the focused re-audit still found the opportunity/abstention denominator
underdefined and fail-closed state/input validation incomplete. Execution
authority was therefore not granted. Real label values accessed, real test-
feature values accessed, and real utility values computed were all zero.

> Utility was not evaluated.

This section reports a governance boundary, not a utility outcome. No utility-
performance table belongs in the thesis.

# 7. Discussion

## 7.1 RQ1: evidence-bound construction feasibility

The evidence chain narrowed 47 candidate pairs to 25 fit-supported pairs and
42 confirmed directions, then materialized a complete construction-evidence
record for each direction. T0/T1/T1-B accepted candidates for the full cohort,
and T2 did so for 39. The result supports a bounded candidate-to-rule pipeline
under the frozen verifier. It does not establish causal relations or anomaly
utility.

## 7.2 RQ2: construction strategies and negative findings

T1's 42/42 result shows one-call feasibility for this cohort and realized
provider/model snapshot. T1-B shows limited stochastic robustness: it recovered
one first-draw rejection and tolerated an unrelated parse failure, but required
three times T1's call budget without improving final yield.

T2 accepted fewer relations than T1-B and T1. Incremental validity benefit was
not observed. Because no repairable issue occurred, the feedback-recovery path
was not empirically exercised. T2 is therefore retained as a bounded verifier-
feedback architecture with explicit fail-closed behavior, not as the empirical
headline.

## 7.3 Validity ceiling and T0 saturation

T0, T1, and T1-B all reached 42/42, showing that deterministic template
construction already saturated the current verifier on this cohort. This is a
construct-validity and discrimination limitation. It does not establish that
T0 is the most useful arm, nor that the three arms have equal downstream
utility. Such a determination would require a labeled utility result, which is
absent.

## 7.4 RQ3: deterministic calibration

The Direct-number result cleanly separates structural compliance from numeric
accuracy. Complete schemas and valid numeric domains did not reproduce the
deterministic references closely. This supplies direct empirical support for
keeping numerical authority in normal-data calibration rather than provider
invention under the frozen contract.

## 7.5 RQ4: fail-closed construction admission

The three unsupported-variable proposals demonstrate the intended admission
boundary: the verifier/controller rejected them and produced `no_rule` rather
than accepting or substituting them. This is positive governance evidence and
simultaneously part of T2's lower yield. The result does not establish runtime
or deployment safety.

## 7.6 Candidate-origin result

No material origin effect can be inferred. The groups overlap, the same
relation retains the same scientific outcome across memberships, and the GDN
membership is small. Origin remains an exploratory provenance descriptor.

## 7.7 Utility absence and thesis strength

The absence of labeled utility materially limits claims about anomaly-event
coverage, false alarms, detector benefit, and useful-rule selection. It does
not erase the construction-governance contribution. Stopping before label
access when evaluator authority remained incomplete is evidence of claim and
data governance, not an empirical utility result.

## 7.8 Limitations and threats

The principal limitations are the single HAI P1 cohort, 42 directions, one
provider/model snapshot, the validity ceiling, the unexercised T2 feedback
path, overlapping origin groups, no detector or utility result, no production
runtime validation, and post-result utility-protocol chronology.

Construct validity is limited because verifier-admissibility is not anomaly
utility. Internal validity is bounded by one stochastic realization and the
unexercised T2 path. External validity is limited to the process, relation
family, dataset edition, and provider/model contract. Statistical conclusions
are constrained by N=42, overlapping subgroups, and ceiling effects.

## 7.9 Implications and future work

The immediate implication is methodological: evidence, numeric authority,
proposal generation, deterministic admission, utility, and runtime should not
be collapsed into one authority layer. Future utility work would require a
complete and independently audited evaluator before any label access. It must
not be designed as a rescue of T2. Detector integration, production runtime,
external datasets, and deliberately exercised repairable feedback cases remain
separate possible studies.

# 8. Conclusion

## 8.1 Answers to the research questions

- **RQ1:** The 42 confirmed HAI P1 directions and their deterministic numeric
  references were transformable into verifier-admissible candidates under the
  bounded protocol, with full yield for T0/T1/T1-B and 39/42 for T2.
- **RQ2:** T1 saturated construction validity with one call per relation;
  T1-B added one marginal recovery at 3× call cost; T2 had lower yield and did
  not exercise feedback recovery.
- **RQ3:** Direct numeric outputs were structurally valid but numerically
  inaccurate relative to deterministic references, supporting project-side
  calibration for this contract.
- **RQ4:** The deterministic verifier and `no_rule` outcome excluded all three
  observed unsupported-variable proposals from the accepted set.

## 8.2 Contribution summary

The thesis contributes an evidence-bound construction pipeline, deterministic
normal-data numeric authority, fail-closed deterministic admission, and a
controlled construction-strategy comparison that retains positive, neutral,
and negative findings.

## 8.3 Final boundary

The study does not provide labeled anomaly utility, detector integration,
production runtime validation, or a useful-rule winner. These limits must
remain visible in the final title explanation, Introduction, Discussion,
Conclusion, and later abstract.

## 8.4 Closing statement

The completed evidence supports a narrow but coherent result: multivariate CPS
relation evidence and deterministic normal-derived references can bound a
reproducible construction and verification process, while explicit governance
prevents invalid proposals and unauthorized downstream claims from being
silently promoted.
