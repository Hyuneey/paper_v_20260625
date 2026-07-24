# Prototype Progress Report

## Scope and Claim Boundary

This package summarizes committed aggregate evidence through TASK-038E. No new
experiment, metric, provider call, agent action, detector/rule execution,
private-array access, outer read, or sealed-test access was performed for this
synthesis.

The ARGOS outer partition is previously exposed follow-up validation. These
results are component-wise descriptive evidence, not an untouched
confirmatory result, exact ARGOS reproduction, final benchmark, or validation
of the proposed multivariate method.

## Research Direction

The proposed contribution remains graph-guided, training-time agentic verified
rule construction for multivariate CPS anomaly detection. ARGOS was extended
as a reference track to answer which parts of one-shot generation, Repair,
Review, detector correction, and aggregation are scientifically useful.

The intended v5 architecture is:

```text
graph-constrained candidate pairs
-> matched normal and detector-error evidence
-> typed relational DSL candidate
-> deterministic calibration registry
-> bounded Repair/Review suggestion
-> deterministic verifier authority
-> accepted / rejected / no-op / abstain
-> LLM-free runtime with satisfaction trace
```

## Completed ARGOS Evidence

1. TASK-033 verified deterministic isolated execution of a frozen rule.
2. TASK-034 measured one-rule narrow coverage.
3. TASK-035A/AR showed output-budget-sensitive generation yield.
4. TASK-035B measured rule-only coverage and false-positive trade-offs.
5. TASK-037A/B established the LSTMAD family and dual Alpha/Beta baselines.
6. TASK-037C measured generic max/min complementarity.
7. TASK-037D/E generated error-conditioned FN/FP rules and evaluated the
   no-agent Full Aggregator.
8. TASK-038A-D froze and executed bounded Repair/Review component protocols and
   no-op-aware branch selection.
9. TASK-038E compared A0-A3 on the previously exposed outer partition.

## Generation and Rule-Only Findings

| Output budget | Visible responses | Static-valid rules | Executable rules |
|---|---:|---:|---:|
| 2,000 tokens | 84/100 | 61/100 | 55/100 |
| 6,000 tokens | 100/100 | 100/100 | 91/100 |

The one-rule result had precision 0.8462, recall 0.1886, and point F1 0.3084.
In the ten-KPI rule-only study, Best-1 reached F1 0.4801 at 22.08 FP/10k;
Top-3 OR reached F1 0.5360 at 105.56 FP/10k. Coverage-heavy arms exceeded
2,000 FP/10k. One-shot generation is viable, but rules have variable yield
and limited coverage, while naive accumulation can create severe false alarms.

## Detector and Agent Findings

The exact ARGOS KPI LSTMAD variant remains unresolved, so LSTMADalpha and
LSTMADbeta remain co-primary.

Repair recovered all 13 frozen runtime failures in one no-retry revision each.
Detection utility was mixed: four repaired rules were useful, four equal, and
five regressive; only two survived A1 selection.

Review made 77 calls. Seventy-two revisions improved inner point F1, one was
equal, three regressed, and one was invalid. Seventy-six revisions were
deterministic executables. All 19 reviewed rules selected for A2/A3 had
positive parent-relative outer transfer, although non-selected revisions
included negative and no-transfer outcomes.

## Branch Outer Results

Macro direct PA-free point F1:

| Variant | Detector | A0 Full | A1 Full | A2 Full | A3 Full |
|---|---:|---:|---:|---:|---:|
| LSTMADalpha | 0.3541 | 0.4884 | 0.4544 | 0.5047 | 0.4666 |
| LSTMADbeta | 0.4233 | 0.3880 | 0.3895 | 0.4215 | 0.4245 |

A2 improved over A0 for both variants. A1 was mixed and largely unchanged or
worse. A3 was mixed relative to A0. No branch or detector variant is selected
as a final winner.

FP correction remains the principal safety issue. Of 19 selected A2/A3 FP
rules, four were safe, 14 costly, 14 harmful, and one ineffective under
overlapping descriptive classifications. Review did not remove the need for
TP and true-event-removal guards.

## Methodological Assessment

The overall classification is `partial_methodological_support`.

- Strong component support: bounded Repair runtime recovery; Review inner
  effectiveness; descriptive selected-Review outer transfer.
- Partial component support: one-shot generation, Repair detection utility,
  complete A3 robustness, safety, and efficiency.
- Not established: exact ARGOS reproduction, universal Full Aggregator
  superiority, sealed confirmation, or proposed-method effectiveness.

## Recommended Next Step

Freeze the ARGOS reference track. Do not perform more prompt/model tuning,
branch selection, or detector-variant choice against the exposed outer
partition. Preserve the sealed ARGOS test unless the professor explicitly
requests one joint pre-registered confirmation.

Direct the primary effort to the proposed multivariate SWaT method with typed
DSL authority, deterministic calibration and verification, graph-constrained
candidates, detector-error-conditioned evidence, no-op/abstain states, and
explicit FP/TP/event budgets.
