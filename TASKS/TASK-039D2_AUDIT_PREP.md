# TASK-039D2 Synthetic Independent Audit Harness Preparation

Status: `passed_task039d2_audit_preparation`

This task prepares an independent, synthetic-only oracle for a later audit of
a completed TASK-039D2 result. It is based at
`301fb636b6944e2d2d86be4646605a3d38585165` and binds the frozen confirmation
policy hash
`83419f6acefaeb21ebc329d5ff9df8563e9636da72ad5367318a172df8fb0b27`.

The audit reference directly reconstructs the frozen D0/BR1 mathematics. It
does not import or call the TASK-039D2 top-level confirmation function. It
applies frozen D1-shaped synthetic parameters, extracts file-local source
events, isolates them against all 12 sources at the inclusive two-second
boundary, evaluates the exact target direction and horizon, computes response
counts, consistency and robust effect, and applies the all-conditions D2 gate.
No direction, horizon, threshold, tolerance, scale, window, radius, search or
fallback can be changed.

The future in-memory ledger audit requires exactly 45 directional results over
exactly 25 D1-supported pairs. It verifies exact D1 record bindings, each
record self-hash, the private confirmation-ledger self-hash, the independent
gate-derived direction partition, pair confirmation, transfer denominators,
source/target coverage, D0 arm metrics, cross-arm overlap, outcome-before-
provenance ordering, and Commit A/B separation.

Only clearly marked synthetic value maps are accepted. This branch cannot
open train3 or any other HAI file, cannot read D1 private ledgers, and rejects
a supplied D2 authorization before file I/O. It creates no D2 audit result,
Rule v2 authority, construction primitive set, Agent, verifier or runtime.
