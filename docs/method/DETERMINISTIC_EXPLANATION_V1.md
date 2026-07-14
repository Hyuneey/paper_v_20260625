# Deterministic Explanation v1

## Grounding

DEC-045 permits explanation fields only from the accepted rule, accepted
verifier result, authorized runtime trace, graph/evidence/normal/parameter
references, and window offsets. Trace, rule, verifier, window, and parameter
hash bindings are checked before rendering.

The canonical trace has no measured lag or magnitude field, so
`lag.observed` is always null. The renderer uses a bounded deterministic text
template and one of four observed-behavior sentences: trigger absent, response
observed, response missing, or abstention.

## Claim Boundary

Detector and fusion results are unavailable. The rule result contains a binary
label and score only for evaluated traces; abstention contains neither. The
record fixes `causal_claim_made` and `root_cause_claim_made` to false and cannot
introduce variables, thresholds, physical causality, root cause, or universal
invariants.

Explanation hashes prove artifact integrity and deterministic rendering only.
They do not establish explanation quality, physical correctness, or anomaly-
detection performance.
