# HAI P1/P3 Delayed-Response Feasibility

The TASK-039B screening family is:

```text
reviewed transition into a discrete destination state
-> continuous target response within 1, 5, 10, 30, or 60 seconds
```

Screening uses train1 and train2 for fit support and train3 for independent
normal-period confirmation. It never crosses a file boundary. The selected
diagnostic direction and horizon maximize directional consistency, then robust
effect ratio, then prefer the shortest horizon.

The fit gate requires 20 isolated triggers in total, at least five in each fit
file, 0.70 pooled and 0.60 per-file directional consistency, robust effect
ratio 2.0, and matching per-file directions. Calibration requires five
isolated train3 triggers, the same direction, 0.60 consistency, and robust
effect ratio 1.0.

Confirmed increase relations count toward current Rule v1 readiness.
Confirmed decrease relations remain future-family candidates. Neither class
is a causal or invariant claim, and no screening output is a final calibration
parameter or CandidateUniverse artifact.

## TASK-039B Result

The eligibility stage produced zero source variables in both P1 and P3, so no
pair entered screening. Fit support, calibration confirmation, increase-ready,
and future-decrease counts were all zero. This is a minimum-gate failure, not a
negative delayed-response estimate for preselected pairs.
