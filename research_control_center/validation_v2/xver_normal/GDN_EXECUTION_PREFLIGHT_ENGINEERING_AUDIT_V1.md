# Pre-run custody hardening

No scientific run has started. Initial HAI22 bounded normal preflight under
execution authority V1 passed, but independent source QA found two custody
gaps before run1: current context projection bundle was not compared to its
execution-freeze hash, and imported sparse-softmax/neighbor mathematical
dependencies were not included in the explicit implementation hash list.

Execution authority V2 adds those checks/hashes and TF32 reporting; it does
not alter any model, optimizer, evidence equation, scaler, purge, seed, or
scientific scope. Historical V1 and its preflight receipt remain immutable.
V2 has separate preflight identities and requires both version preflights to
replay before scientific execution. A resealed projection mutation regression
must fail. No empirical results were used to choose any method change.

The existing frozen global inference body has exact AST equality after only
the two HAI23 input-identity guards are replaced by external custody checks.
Training calls the original EXP01C function unchanged. Missing auxiliary
events/edges remain scientific absence, never substituted with global values.
