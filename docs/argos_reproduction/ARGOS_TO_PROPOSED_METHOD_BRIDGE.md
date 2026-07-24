# ARGOS to Proposed-Method Bridge

## Retain

- training-time-only LLM use;
- executable rule artifacts;
- bounded Repair for syntax or runtime recovery;
- Review for candidate refinement;
- detector-preserving directional correction;
- frozen LLM-free runtime.

## Modify

| ARGOS element | Proposed-method replacement |
|---|---|
| Unrestricted Python rules | Typed relational DSL |
| LLM-authored numeric parameters | Deterministic calibration registry |
| LLM-based final approval | Deterministic verifier authority |
| Review-only F1 objective | FN recovery, FP budget, TP-removal budget, true-event-removal guard, and cross-regime stability |
| Always-use rule assumption | Explicit accepted, rejected, no-op, or abstain state |

## Add

- graph-guided variable-pair candidate restriction;
- matched normal reference evidence;
- detector-error-conditioned evidence;
- explicit FN and FP direction;
- TP-removal and true-event-removal guards;
- composition verification;
- satisfaction trace;
- provenance-bound explanation.

## FP-Correction Approval

FP correction must not be approved solely because it raises inner point F1.
The proposed protocol must require:

- validation FP removal greater than zero;
- removed true-positive points within a pre-frozen budget;
- zero removed true anomaly events;
- precision gain or neutrality;
- point-F1 non-regression;
- stable cross-split direction;
- mandatory no-op candidate.

TASK-038F does not choose a numeric budget. That calibration belongs to the
proposed-method protocol.

## Repair and Review Authority

Repair follows:

`DSL parse or runtime failure -> bounded Repair suggestion -> deterministic verifier -> execution only after all contracts pass`

Review remains training-time, bounded, inner/calibration-only, and
provenance-complete. Neither agent can approve its own output, receive
outer/test feedback, or silently restore a harmful revision.
