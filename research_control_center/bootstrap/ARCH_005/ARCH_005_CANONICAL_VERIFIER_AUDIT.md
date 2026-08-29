# Canonical Verifier Audit

`VerifierV1` was statically mapped to exactly 20 ordered stages. Structural-stage failure skips later stages; otherwise issues accumulate. Outputs are `accepted`, `needs_repair`, or `rejected`. Acceptance binds an accepted Rule v1 but leaves runtime authorization false. Scope is structural, provenance, split, execution-contract and claim-boundary validity—not scientific truth or utility.
