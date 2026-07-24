# Professor Decision Request

## Current Position

The ARGOS reference track now covers one-shot generation, deterministic
execution, rule-only validation, dual LSTMAD baselines, generic and
error-conditioned fusion, bounded Repair, bounded Review, no-op-aware branch
selection, and A0-A3 outer follow-up. The resulting classification is
`partial_methodological_support`.

Repair is strongly supported as an operability mechanism. Review is strongly
supported for inner refinement and has strong descriptive selected-rule outer
transfer. The complete A3 branch is not robust across LSTMAD variants, and FP
correction remains unsafe without TP/event guards.

## Decision 1: Freeze the ARGOS Reference Track?

Recommended: **approve `freeze_ARGOS_reference_track`**.

Freeze means preserving the track while prohibiting further prompt/model
tuning on the exposed outer partition, new branch selection, detector-variant
choice, or attempts to improve the reported outer values.

Reason: the component questions needed for thesis design have been answered,
and further upstream-fidelity work has diminishing value relative to the
multivariate SWaT contribution.

## Decision 2: Sealed ARGOS Confirmation?

### Option A: Professor-Approved Joint Confirmation

Pre-register both LSTMAD variants and detector-only, A0, A1, A2, and A3.
Execute the sealed partition once without branch selection, fallback, or
policy change. Interpret it as component confirmation, not exact ARGOS
reproduction.

### Option B: Preserve the Sealed Test and Move to SWaT

Recommended when thesis time is limited. Existing outer evidence is adequate
for design decisions, while official SWaT evidence directly addresses the
proposed multivariate method.

Please choose A or B. No recommendation is based on unseen sealed performance.

## Decision 3: Approve v5 Proposed-Method Controls?

Requested approval to prioritize:

1. graph-guided variable-pair candidate restriction;
2. typed relational DSL instead of unrestricted Python;
3. deterministic numeric calibration and verifier authority;
4. matched normal and detector-error-conditioned evidence;
5. explicit FN and FP direction;
6. mandatory no-op/abstain states;
7. TP-removal and true-event-removal guards for FP correction;
8. composition verification, satisfaction traces, and provenance-bound
   explanations.

Repair would be retained only for bounded contract recovery. Review would be
retained as a bounded training-time candidate-refinement mechanism, never as
final authority.

## Evidence Boundary

- Public KPI evidence is not SWaT evidence.
- The TASK-038E outer partition was previously exposed.
- No exact ARGOS reproduction or final branch winner is claimed.
- No sealed-test or proposed-method superiority is established.
