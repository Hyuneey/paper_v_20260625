# Evidence Curation Contract

## Standard term

The project uses **anomaly-anchored evidence curation**. It must not be
described as generic chunk optimization.

An evidence package references an event anchor, event window, pre/post context,
matched normal reference, registered variables, regime, candidate lag range,
split, dataset version, selection policy, and hashes. Raw values are not part of
the tracked package.

## Selection policy

The policy is frozen before rule generation and must:

- use train or calibration data only;
- require the same or a compatible operating regime;
- require the same subsystem context;
- use deterministic tie-breaking;
- avoid final-test access;
- avoid future rule or detector performance;
- record a policy ID, version, and SHA-256.

Default tie-breaking is lowest eligible window ID after exact regime and
subsystem matching. A compatible-regime fallback requires a predeclared
compatibility table. A nearest-profile policy must define its distance and then
break ties by stable ID.

## Matched normal references

Each reference stores an ID, regime, subsystem, matching method, tie-breaker,
and artifact hash. It may provide normal variability, typical magnitude, lag,
or trajectory context. It cannot expose final-test information or be selected
after observing candidate performance.

## Allowed evidence claims

- temporal association
- state-conditioned response
- typical lag
- typical direction
- typical magnitude
- normal variability

An evidence package does not establish physical causality, root cause, or a
universal invariant.

## Curator output boundary

The Evidence Curator returns IDs and bounded candidate metadata only. It does
not produce a rule, threshold, calibrated value, test metric, or natural-language
causal conclusion.
