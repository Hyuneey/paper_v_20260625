# Future R1 input boundary

R1 is conditional and not implemented or executed by ARCH-006.

## Inputs that may be allowed after preregistration

- approved rule or relation descriptor
- normal-only relation evidence and provenance
- authorized numeric references
- current label-blind observations
- intermediate source-trigger or window-availability state that does not reveal the final R0 decision

## Forbidden outcome leakage for an independent detection comparison

- R0 final alarm/normal output
- final satisfied/violated result
- D1 `alarm_emitted` or equivalent final state
- test labels or attack-event identities
- ground-truth anomaly outcome
- final rendered explanation outcome
- detector/fusion outcome unless that comparison explicitly preregisters it as input rather than an independent detector

If R1 receives the final trace outcome, it is explanation or summarization, not an independent detection comparison. The frozen R0/D1 runtime remains LLM-free; this statement must not be generalized to every future runtime design.
