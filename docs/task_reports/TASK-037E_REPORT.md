# TASK-037E Report

Status: `passed_error_conditioned_full_aggregator_outer_validation`

## Scope

TASK-037E evaluated the frozen TASK-037D error-conditioned rule cohort through
inner-only directional selection and one-way outer validation. It did not call
a provider or agent, retrain a detector, change a detector threshold, generate
or repair a rule, or access a sealed test.

The complete path was:

1. replay all 83 executable rules twice on their full inner value windows;
2. freeze every inner prediction before loading inner labels;
3. independently select one FN candidate and one FP candidate per
   detector/KPI, with an explicit no-op candidate;
4. commit the selection freeze;
5. replay only selected non-no-op rules twice on outer values;
6. freeze detector-only, detector-plus-FN, detector-plus-FP, and full
   Aggregator predictions before loading outer labels; and
7. compute direct PA-free point and event metrics once.

The full Aggregator order was FP correction followed by FN compensation:

`max(min(detector, FP rule), FN rule)`

## Execution gates

- Candidate rules registered: 83
- Deterministic inner replays: 83 of 83
- FN selections: 19 executable rules, 1 no-op
- FP selections: 2 executable rules, 18 no-ops
- Selected non-no-op rules replayed on outer: 21
- Deterministic outer replays: 21 of 21
- Detector variants retained: `LSTMADalpha`, `LSTMADbeta`
- KPI series per variant: 10
- Outer reselection: none
- Detector-variant selection: none
- Point adjustment: disabled
- Threshold optimization: none
- Sealed-test access: none

## Outer macro results

All values are equal-weight averages across ten KPI series.

| Variant | Arm | Precision | Recall | Point F1 | Event F1 | FP / 10k normal |
|---|---|---:|---:|---:|---:|---:|
| LSTMADalpha | Detector only | 0.680875 | 0.294491 | 0.354145 | 0.437894 | 24.125 |
| LSTMADalpha | Detector + FN | 0.634191 | 0.511654 | 0.488355 | 0.541527 | 45.516 |
| LSTMADalpha | Detector + FP | 0.680875 | 0.294491 | 0.354145 | 0.437894 | 24.125 |
| LSTMADalpha | Full Aggregator | 0.634191 | 0.511654 | 0.488355 | 0.541527 | 45.516 |
| LSTMADbeta | Detector only | 0.667318 | 0.388594 | 0.423295 | 0.351843 | 33.881 |
| LSTMADbeta | Detector + FN | 0.601648 | 0.581973 | 0.478181 | 0.423498 | 148.399 |
| LSTMADbeta | Detector + FP | 0.704444 | 0.286380 | 0.347552 | 0.418656 | 24.097 |
| LSTMADbeta | Full Aggregator | 0.591703 | 0.487035 | 0.388043 | 0.500163 | 142.270 |

## Interpretation

For `LSTMADalpha`, all FP selections were no-ops. The full Aggregator therefore
matched detector-plus-FN: recall and point/event F1 increased, while precision
decreased and false positives increased.

For `LSTMADbeta`, two FP rules were selected. FP correction reduced false
positives but also removed detector true positives. Subsequent FN compensation
recovered some anomaly evidence and increased recall relative to detector-only,
but the full Aggregator had lower macro point F1 and substantially higher
FP/10k than detector-only.

These outcomes show detector-error-conditioned directional effects and their
costs. They do not establish fusion superiority, select an LSTMAD variant, or
validate the rules on a sealed test.

## Claim boundary

The TASK-037E outer partition is a previously exposed follow-up validation
partition. Rule generation used only the generation partition and rule
selection used only the inner partition, but the broader experiment design
followed prior inspection of outer results. Therefore TASK-037E does not
support an untouched confirmatory superiority claim.

TASK-037E is paper-aligned in its detector-error-conditioned FN/FP generation
and FP-then-FN composition. It is not an exact ARGOS reproduction because the
official LSTMAD alpha/beta identity remains unresolved, RepairAgent and
ReviewAgent were not executed, and the implementation uses a project-owned
deterministic execution and reporting harness.

## Provenance

- Commit A: `95351d560d3659dedb7b1783f84783c65a7b7eff`
- Commit B: `06560b06f636e2a69d7ad1c92b976cc513c310d7`
- Candidate registry hash:
  `f2a70c449485d90284e6c4696ed0a916fdbca89b0bd2b9f956e714ca4c3b2518`
- FN selection freeze hash:
  `e9cf45a768db0eadf4f17308fda36101ba60ff583369e5f9891941404264eaf5`
- FP selection freeze hash:
  `1b9b6d4c0ff19d6b07fba1ec972e9ebe3259e69b3cd2a6452273162c4cf8338f`
- Outer Aggregator report hash:
  `d1af6941b94884eae6a1b7041867b148b8310b2ef6accc2d095f2d16b3778103`
