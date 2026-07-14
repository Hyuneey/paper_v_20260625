# Graph-Guided Rule Construction Contract

## Status and purpose

This document defines an implementation-ready contract for:

> Graph-Guided Agentic Construction of Verified Relational Rules for
> Explainable Multivariate Time-Series Anomaly Detection

TASK-030 is a specification milestone. It does not implement or experimentally
verify the complete method.

## Frozen ARGOS findings

- Rule-only commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Historical Aggregator commit:
  `c03427f2ab16e377946d4c1176585156ddae7254`
- ARGOS generates unrestricted executable Python from labeled train chunks.
- Its LLM writes internal rule thresholds and control flow.
- RepairAgent executes and rewrites Python.
- ReviewAgent is an LLM code-generation agent, not a deterministic verifier.
- Pinned review regression feedback uses train performance.
- Pinned candidate selection uses validation Event-F1-PA F1.
- Test evaluation and label-aware score-threshold search can occur during
  training iterations.
- FN fusion is elementwise maximum; FP fusion is elementwise minimum.
- The complete paper Aggregator is not fully wired in the pinned driver, and
  detector prediction artifacts are external.

These are **audit findings, not benchmark results**. Captured-rule runtime,
KPI performance, Repair/Review effects, detector performance, fusion
superiority, and paper performance reproduction remain unverified.

## Proposed-method boundary

| Concern | Frozen contract |
|---|---|
| Training-time LLM | May be approved later; prohibited in TASK-030 |
| Runtime LLM | Prohibited |
| Rule representation | Project-owned typed JSON DSL |
| Arbitrary or free-form execution | Prohibited |
| Runtime engine | Deterministic project-owned interpreter |
| Rule acceptance authority | Deterministic verifier only |
| Relation candidates | Graph-guided primary; bounded statistical fallback |
| Numeric values | Deterministic calibration artifacts only |
| ARGOS role | Prior work, reproduction target, and rule/fusion baseline |
| ARGOS production dependency | None |

ARGOS source is not inherited into `src/paperworks`.

## Scientific problem

For a multivariate CPS timeline, a relational rule models:

> When source variable A enters state S, target variable B is expected to show
> effect R within lag interval L, under regime G, within tolerance T.

Every rule binds source and target variables, operating regime, relation
family, lag, temporal window, calibrated tolerance, observed violation, and
supporting evidence. Supported concepts include delayed responses,
directional changes, co-movement, bounded ratios/differences, persistence,
state transitions, trajectory similarity, and recovery to baseline.

Candidate edges and learned graph scores are predictive or associational
evidence. They are not causal or root-cause claims.

## Separation of responsibilities

1. **Anomaly detection** determines whether an accepted rule or detector emits
   a violation signal.
2. **Temporal localization** records the interval and satisfaction steps.
3. **Variable attribution** references registered source/target nodes.
4. **Relational rule construction** selects only registered relation families.
5. **Parameter calibration** produces numeric records from calibration data.
6. **Rule verification** makes the non-overridable acceptance decision.
7. **Detector-rule fusion** combines frozen prediction artifacts under a
   predeclared policy.
8. **Explanation rendering** presents existing trace and provenance without
   modifying semantics.

## Contract pipeline

```text
registered metadata
-> pre-scoring CandidateUniverse
-> directed candidate graph
-> anomaly-anchored evidence curation
-> bounded relation-family selection
-> candidate JSON DSL
-> deterministic parameter calibration
-> deterministic verifier
-> accepted rule library
-> LLM-free runtime trace
-> optional frozen detector-rule fusion
-> provenance-only explanation rendering
```

No final-test label, prediction, threshold, metric, or interval may flow back
into any upstream stage.

## Artifact authority

- Graphs authorize candidate variable pairs, not causality.
- Evidence packages authorize bounded observations, not universal invariants.
- Parameter records authorize numbers only after deterministic calibration and
  approval.
- The verifier authorizes rules.
- Runtime traces report execution facts.
- Explanation records may describe but never change those facts.

## Version changes

A new relation family, operator, trigger, output meaning, parameter role, or
repair permission requires a schema-version change and a recorded research
decision. Agents cannot extend these registries during execution.
