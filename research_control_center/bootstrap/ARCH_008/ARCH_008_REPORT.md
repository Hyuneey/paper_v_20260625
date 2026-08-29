# ARCH-008 Report

Status: PASS.

The audit mapped the frozen D1 object, eight output levels, event semantics, false-alarm burden, D0/D1 overlap, integrity lineage, terminology, and claim boundaries without executing science or recomputing metrics.

Key findings:

1. D1 is COMMON-42 Verified Relational Rule-only, not T2 Agentic Rule-only.
2. 6,031 opportunities produced 788 anomalous rule records at 630 unique seconds and 626 total episodes.
3. D1 overlapped 13 of 14 operational attack-event units.
4. There were 574 normal false episodes over 51,019 normal seconds, FAR 40.50255787059723 episodes/hour.
5. D0/D1 overlap was 10 both, 1 D0-only, 3 D1-only, 0 neither; this is pilot response diversity, not validated complementarity.
6. The prediction was label-blind and complete before labels but lacked a durable pre-label file gate.
7. Rule-only operational utility and held-out generalization remain unvalidated.

Mismatches: 13 total; CRITICAL 0, HIGH 8, MEDIUM 5, LOW 0.

Safety: scientific executions 0; test1 feature accesses 0; test1 label accesses 0; test2 accesses 0; scientific source changes 0; frozen result changes 0; private exposures 0.
