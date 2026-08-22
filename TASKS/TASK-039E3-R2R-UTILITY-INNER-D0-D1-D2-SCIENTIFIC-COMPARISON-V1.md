# TASK-039E3-R2R-UTILITY-INNER-D0-D1-D2-SCIENTIFIC-COMPARISON-V1

Freeze a local post-hoc INNER comparison of the exact integrity-audited D0,
D1, and D2 prediction artifacts. Parse the exact label once only after the
comparison implementation and tests are committed. Reproduce primary metrics,
anonymous event-set overlap, detector-miss recovery potential/retention, and
false-alarm burden without executing or changing any arm.

Prohibited: model, detector, rule, or fusion execution; rule reevaluation; D0
score access; redesign or candidate sweep; test1 feature access; test2; OUTER;
private/event-coordinate leakage; remote egress; push.

PASS freezes the negative D2 V1 INNER result, keeps OUTER unauthorized, and
sets the exact next task from the independently derived D0-miss overlap.
