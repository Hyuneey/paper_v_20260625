# V6 GDN Backend Use Policy

Only an `upstream_aligned_validated` backend may be identified as GDN in the
future RQ1 experiment arm.

A `synthetic_smoke_only` backend is restricted to:

- unit and import tests;
- artifact plumbing;
- synthetic shape checks;
- historical TASK-004/005 regression.

It must not be used for HAI candidate ranking, RQ1 GDN results, thesis
performance, process selection, or scientific edge-stability claims.

The masked candidate extractor may be composed with a future accepted backend,
but it is not a complete model and grants no backend fidelity by itself.

## Future Decision

Production graph ranking remains `pending_TASK039A_B_feasibility`. After HAI
schema and one-process feasibility are known, TASK-039C must choose one of:

1. a project-owned, source-aligned minimal GDN port;
2. another learned graph ranker explicitly named as such.

The existing smoke backend cannot be silently promoted or relabeled as GDN.
Completing TASK-039P1D closes the foundation migration, not the production
backend decision.
