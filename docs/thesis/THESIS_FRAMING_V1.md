# Thesis Framing V1

Status: `FROZEN_FOR_MASTER_DRAFT_V1`

Authoritative evidence base: commit
`3e998b12941e2b7065408d1796c5c416461b1e7a` and the seven consolidated
documents under `docs/thesis` created by that commit.

## Recommended primary framing

> **Evidence-Bound and Verifiable Rule Construction for Explainable
> Multivariate CPS Anomaly Detection**

The thesis studies how normal-only multivariate relation evidence,
deterministic numeric references, bounded proposal construction, and
deterministic verification can be assembled into a governed rule-construction
pipeline. Its empirical endpoint is construction validity: whether a proposal
is verifier-admissible under the frozen contract.

In this title, **verifiable** means deterministically checkable at construction
admission. It does not mean verified anomaly utility, detector improvement,
runtime explanation quality, deployment safety, or production validation.
"For ... anomaly detection" names the intended application context; it does
not claim that labeled anomaly performance was demonstrated.

## Ranked title candidates

### 1. Evidence-Bound and Verifiable Rule Construction for Explainable Multivariate CPS Anomaly Detection

- **Strength:** Captures the evidence pipeline, deterministic verification,
  and intended application without centering the LLM or T2.
- **Risk:** Readers may interpret "verifiable" as downstream performance or
  interpret "for anomaly detection" as a demonstrated utility claim.
- **Claim scope:** Construction evidence, normal-derived parameter authority,
  deterministic verifier-admissibility, and fail-closed admission. The
  Introduction must state the utility boundary immediately.

### 2. Governed Construction of Verifier-Admissible Rules from Normal-Data CPS Relations

- **Strength:** Most precisely matches the completed empirical layer and makes
  the normal-data and admission boundaries explicit.
- **Risk:** More technical and less accessible as a title.
- **Claim scope:** Candidate-to-rule construction, deterministic calibration,
  verification, and `no_rule`; no downstream anomaly-performance implication.

### 3. Comparing Deterministic and Bounded LLM-Assisted Rule Construction for Multivariate CPS Anomaly Detection

- **Strength:** Clearly foregrounds the controlled T0/T1/T1-B/T2 comparison.
- **Risk:** Over-centers the LLM comparison and may be mistaken for an agentic-
  superiority study.
- **Claim scope:** Construction-validity yield, stochastic robustness, and
  provider-call cost only.

The first title is the default. The second is the safest alternative if a
supervisor judges that the application phrase in the default title implies an
unmeasured utility claim.

## One-sentence thesis position

> Confirmed multivariate CPS relations and deterministic normal-derived
> numeric references can support a governed, bounded construction pipeline in
> which proposals are admitted only after deterministic verification, while
> construction validity, downstream utility, runtime authority, and
> deployment claims remain separate.

## What this thesis is

- An evidence-bound candidate-to-rule construction study.
- A deterministic numeric-authority and calibration study.
- A controlled relation-paired comparison of T0, T1, T1-B, and T2 at the
  construction-validity layer.
- A governance study of deterministic admission and explicit `no_rule`.
- A transparent account of a validity ceiling, a negative T2 result, and an
  intentionally unexecuted utility stage.

## What this thesis is not

- An agentic-superiority study.
- A detector-performance or labeled anomaly-utility study.
- Evidence that T2 feedback recovery improved construction.
- Evidence that accepted candidates improve anomaly detection.
- A production Rule v2, runtime, deployment, or winner-selection study.
- A causal-discovery or root-cause study.

## Narrative spine

1. Multivariate CPS rule construction needs relation evidence and numerical
   authority, not unconstrained text generation.
2. Candidate evidence is narrowed through normal-only profiling and one-way
   confirmation before any rule proposal is constructed.
3. Rule parameters are bound to deterministic normal-derived references.
4. Deterministic, one-shot LLM, repeated-sampling, and bounded verifier-
   feedback strategies are compared under the same construction contract.
5. A deterministic verifier separates admissible proposals from `no_rule`.
6. The experiment shows feasibility, a validity ceiling, limited repeated-
   sampling robustness, a negative T2 result, and a calibration rationale.
7. Downstream labeled utility remains scientifically relevant but was not
   evaluated because the protocol never reached audited execution authority.

## Terminology policy

| Prefer | Meaning | Avoid or qualify |
|---|---|---|
| rule construction | The bounded proposal-to-admission process | rule learning when no learning claim is intended |
| proposal / rule candidate | Structured object before verifier acceptance | rule if acceptance or utility is ambiguous |
| accepted rule candidate | Proposal admitted by the deterministic verifier | useful rule, effective rule |
| verifier-admissible | Conforms to the frozen construction contract | valid without naming the validity layer |
| construction validity | Relation-level deterministic admission endpoint | anomaly validity, utility |
| normal-derived numeric reference | Authoritative value from frozen normal-data calibration | LLM-generated threshold |
| deterministic calibration | Project-side numerical authority | tuning on labeled utility data |
| fail-closed construction admission | Invalid proposal does not enter the accepted set | deployed safety guarantee |
| `no_rule` | Construction terminates without an accepted candidate | `no_op`, abstain, provider failure |
| bounded LLM-assisted construction | T1/T1-B proposal generation under frozen constraints | autonomous rule authoring |
| bounded verifier-feedback construction | Technical description of T2 | agentic as a headline contribution |
| provider-call cost | Frozen generation-call count | utility-adjusted cost or winner score |
| utility was not evaluated | Correct final study boundary | failed/negative/zero utility result |

Use **agentic** only when technically identifying the bounded T2 architecture.
It must not be the title, primary contribution, or empirical-superiority claim.

## Fixed empirical framing

- T0, T1, and T1-B: 42/42 verifier-admissible relations.
- T2: 39/42 verifier-admissible relations and three `no_rule` outcomes.
- T1-B: one relation recovered after the first draw at three times T1's
  provider-call cost.
- T2: no feedback-eligible case and no revise, retrieve, follow-up, or recovery
  action.
- Direct-number: structured output did not imply numerical accuracy, supporting
  deterministic normal-data calibration for the frozen contract.
- Candidate-origin effect: `INCONCLUSIVE`.
- Labeled utility: `NOT_EXECUTED`; utility was not evaluated.

## Abstract boundary

The final abstract is intentionally not drafted in V1. Later abstract writing
must use only the allowed-claim inventory in
`THESIS_RESULT_CLAIM_MATRIX.md` and must include the material qualification
that downstream labeled utility was not evaluated.
