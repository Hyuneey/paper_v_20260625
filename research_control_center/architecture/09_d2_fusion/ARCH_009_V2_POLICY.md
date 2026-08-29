# D2 V2 policy

V2 retains the same pointwise D0 OR rule and the same threshold of two distinct
source identities. Its difference is temporal support.

Each alarming D1 record at decision index `i` is converted into an active token
bound to the relation's frozen `selected_horizon_seconds = h`. The token is
active on the inclusive interval:

```text
i <= t <= i + h
```

At each row `t`, V2 deduplicates the sources of all active tokens and admits D1
evidence when at least two sources are active. This is the audited meaning of
“native-horizon persistence”; it is not a learned persistence model, a label-
derived window, or an arbitrary multiplier.

The V2 provenance explicitly records that the V1 negative result and prior
test1-label diagnostic informed the problem formulation. No V2 prediction or
metric was seen before V2 freeze, but evaluation reused test1. Classification:
**TEST1_INFORMED_DEVELOPMENT**, not independent confirmation.
