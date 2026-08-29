# ARCH-002 STAT Audit

Verdict: `VERIFIED_WITH_NARROW_CLAIM_BOUNDARY`.

STAT reads only P1 normal train1/train2 authorized columns. It computes file-local first differences and Pearson association between source change at `t` and target change at frozen horizons. Cross-file same-sign stability is required; strength is the weaker absolute association. Frozen evidence: 144 evaluated, 141 supported, 3 sign-unstable, complete Top-20.

STAT is directional lagged-association candidate evidence. It is not downstream delayed-response confirmation or causal evidence.

Scientific executions: 0. Test2 accesses: 0.
