# ARGOS Methodological Validity Update

## Why the Reference Study Was Extended

The reproduction was extended beyond one-shot rules to isolate the scientific
roles of the detector, FN/FP correction, RepairAgent, ReviewAgent, no-op-aware
selection, and Full Aggregator composition. The result is a paper-aligned,
leakage-corrected component reproduction rather than an exact implementation
claim.

## Headline Results

| Variant | Detector | A0 Full | A1 Full | A2 Full | A3 Full |
|---|---:|---:|---:|---:|---:|
| LSTMADalpha | 0.3541 | 0.4884 | 0.4544 | 0.5047 | 0.4666 |
| LSTMADbeta | 0.4233 | 0.3880 | 0.3895 | 0.4215 | 0.4245 |

These are macro direct PA-free point F1 values on a previously exposed
follow-up outer partition. A2 improved over A0 for both variants. A1 was mixed,
and A3 was mixed relative to A0. No branch or detector variant is a final
winner.

## Component Evidence

| Component | Key evidence | Judgment |
|---|---|---|
| One-shot generation | Yield depended on output budget; frozen execution was deterministic | Partial |
| Repair operability | 13/13 recovered | Strong |
| Repair performance | Useful 4, equal 4, regressive 5 | Partial |
| Review inner effect | 72 improvements among 77 calls; one equal, three regressions, one invalid | Strong |
| Review outer transfer | All 19 selected reviewed rules were positive relative to parent | Strong descriptive |
| Full A3 robustness | Alpha negative, Beta positive versus A0 | Partial |
| FP safety | 14 harmful classifications among 19 selected FP rules | Partial; unsafe without guards |
| Overall ARGOS | Components valid; full superiority unproven | Partial methodological support |

The agent study used 90 unique provider calls and 404,399 provider-reported
tokens. Repair recovered execution but did not reliably improve detection.
Review was effective on inner and selected revisions transferred well
descriptively, but FP correction still removed true-positive and true-event
evidence.

## Design Implications for Research-Note v5

Retain training-time-only LLM use, bounded Repair, candidate Review,
detector-preserving directional correction, executable artifacts, and an
LLM-free runtime. Replace unrestricted Python and LLM-authored thresholds with
a typed relational DSL, deterministic calibration, and deterministic verifier
authority. Add graph-guided variable-pair restriction, matched normal evidence,
explicit FN/FP direction, TP/event-removal guards, no-op/abstain states,
composition verification, and provenance-bound explanations.

## Requested Decisions

1. Approve freezing the ARGOS reference track with no further prompt/model or
   branch tuning on the exposed outer partition.
2. Choose between a professor-approved one-time joint sealed confirmation and
   preserving the sealed ARGOS test while moving directly to the proposed
   SWaT method. The recommended default is preservation and progression.
3. Approve the v5 proposed-method controls, especially typed DSL authority,
   graph-constrained candidates, detector-error-conditioned evidence, and
   explicit FP/TP/event budgets.

## Evidence Boundary

The outer partition was previously inspected before the Repair/Review program
was designed. The results are descriptive component-wise evidence, not final
performance, confirmed superiority, an exact ARGOS reproduction, or validation
of the proposed multivariate CPS method.
