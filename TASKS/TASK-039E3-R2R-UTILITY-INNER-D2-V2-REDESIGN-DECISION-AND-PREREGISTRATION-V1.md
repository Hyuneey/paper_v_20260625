# TASK-039E3-R2R-UTILITY-INNER-D2-V2-REDESIGN-DECISION-AND-PREREGISTRATION-V1

## Mode and boundary

Local INNER-development design and preregistration only. No D0, D1, D2 V1,
or D2 V2 execution; no rule reevaluation; no alternative-policy performance;
no parameter sweep; no test1 feature or label-file access; no test2, OUTER,
push, remote branch, or PR.

Base is exactly `07c3b1a6f90a36c819621662a6bc1d5f33948716` on branch
`task-039e3-r2r-utility-inner-d2-v2-redesign-decision-preregistration-v1`.
D2 V1 remains the immutable, thesis-visible negative-result baseline.

## Frozen evidence and purpose

The frozen diagnostic established three D0-missed events detected by D1 but
none recovered by D2 V1. Two events had multi-source asynchronous evidence;
one was single-source-only. No recovery event met the exact-same-second
two-source gate, while all three normal D2 V1 rule-recovery false positives
did. This task may consume that frozen development evidence but may not reopen
labels or calculate V2 performance.

Freeze exactly one policy:

- ID: `D2_V2_D0_PLUS_NATIVE_HORIZON_MULTI_SOURCE_CORROBORATION_V1`.
- Family: `DETECTOR_PRESERVING_NATIVE_HORIZON_ASYNCHRONOUS_MULTI_SOURCE_CORROBORATION`.
- Role: `INNER_LABEL_INFORMED_DEVELOPMENT_POLICY`.
- Target: `MULTI_SOURCE_ASYNCHRONOUS_RECOVERY_SIGNAL`.
- D0/D1/source-map identities remain exact and immutable.
- D0 alarms are preserved; no D0 score or rule reevaluation is permitted.
- Single-source fallback is false.
- Required distinct-source count remains two and is not searched.

## Native temporal authority gate

Before design freeze, replay exact COMMON-42 public authority. Each of the 42
relation bindings must resolve uniquely to the existing canonical rule field
`selected_horizon_seconds`, whose frozen source field is
`selected_delay_horizon_seconds`. The exact relation set must match the frozen
D2 source map. Missing, foreign, ambiguous, label-derived, or test1-derived
horizons block with
`D2_V2_DESIGN_BLOCKED_NATIVE_TEMPORAL_HORIZON_AUTHORITY_UNAVAILABLE`.

No diagnostic gap becomes a parameter. No fixed global window, multiplier,
clipping based on INNER outcomes, or new numeric estimation is allowed. The
already-public horizon values may remain public because their exact values are
already tracked in the frozen executable-equivalence authority.

## Frozen V2 semantics

For an alarming D1 decision at physical second `d_i` for relation `r_i`, the
causal evidence token starts at `d_i` and expires inclusively at
`d_i + H(r_i)`, clipped only by the physical split end. Evidence is never
backdated. At second `t`, `S_t` is the set of distinct sources with at least
one active token. Corroboration is `|S_t| >= 2`; same-source duplicates count
once. D2 V2 emits `D0_alarm(t) OR corroboration(t)`.

Trigger classes are `NONE`, `D0_ONLY`, `RULE_RECOVERY_NATIVE_HORIZON`, and
`D0_AND_RULE_CORROBORATION_NATIVE_HORIZON`. Exact-same-second corroboration
remains included. No anti-false-positive heuristic or single-source branch is
added.

## Future execution and metrics

Future execution requires a separate authorization. It must validate the
design, D0 prediction, D1 prediction, source map, and native-horizon map;
construct causal tokens; freeze `ScientificCombinedPredictionArtifactV2`
before any label access; and then use the existing attack-event Recall, Normal
FAR episodes/hour, and four incremental metric formulas. Test2 remains sealed
for final confirmatory generalization.

## Freeze sequence

Commit A contains only this task, the design module, self-hashed config, and
static tests. Commit B contains only independent tests and does not modify
production. Commit C contains only sanitized self-hashed design reports.
Commit D contains only project-state continuity. No result is observed, no
execution is authorized, and no push occurs.

Exact next task after PASS:
`TASK-039E3-R2R-UTILITY-INNER-D2-V2-EXECUTION-AUTHORIZATION-V1`.
