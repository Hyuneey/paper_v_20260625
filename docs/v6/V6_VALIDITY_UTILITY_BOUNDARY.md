# V6 Validity and Utility Boundary

## Deterministic Validity

Validity covers structure, source/target compatibility, graph/evidence
binding, parameter provenance, split compliance, operational contract, and
claim boundaries. The canonical verifier remains the authority.

## Label-Aware Utility

Utility covers normal false-fire, inner attack coverage, detector FN recovery,
added false positives, duplicate firing, safety budgets, and no-op-aware
selection.

## Artifact Separation

- normal evidence records relation support and grants no validity;
- construction outcomes record candidates or construction termination;
- verifier results determine validity outside P1B;
- governance outcomes consume an accepted-rule reference and decide selected
  rule versus `no_op`;
- runtime traces retain canonical evaluated/abstained semantics.

Attack-label performance cannot accept an invalid rule. A valid rule can still
be rejected as `no_op`. A selected rule can still `abstain` at runtime. These
states are not interchangeable.
