# TASK-039E3-R1B Offline Recovery Implementation

Status: `passed_task039e3_r1b_recovery_implementation`.

The executable recovery source is frozen at R1B Commit A
`93c2e8a6333829446c5353f1ca9b61c967f8a7a7`. The historical E3 capability
block and blocked R1 result remain unchanged. R1B contacted no provider, did
not inspect `OPENAI_API_KEY`, executed no capability probe or scientific call,
and accessed neither real E1 evidence nor historical E3 private custody.

## Implemented boundary

The additive recovery path replaces model self-report authority with exact
provider response metadata for model identity and observed strict-schema parse
and validation for structured-output support. The prompt and schema remain
bound to the R0 hashes, and the historical live transport is reused unchanged
under the prospective R1A authority of 30.0 seconds per transport attempt.

A future run remains impossible without a separate self-hashed R2
authorization binding the exact Commit A and source manifest. The runner
orders R0/R1A, Git, clean-state, source-manifest, historical-custody,
private-root, and public scientific-preflight checks before its sole deferred
credential lookup. It freezes the corrected capability slot in durable private
hash-chained custody before E1 can become reachable. A capability block keeps
E1 closed.

The recovery serializer recursively normalizes immutable mappings, mappings,
tuples, lists, and JSON primitives; rejects unsupported types; verifies the
repository-compatible self-hash and JSON round trip; and uses flush, fsync,
and atomic replacement. Historical E3 writers and scientific sources were not
modified.

## Frozen science

T0, T1, T1-B, T2, deterministic validity, controller, retrieval, metrics,
direct-number comparison, relation order, and all budgets remain unchanged.
The schedule remains 42 T1, 126 T1-B, 42 to 126 T2, and 42 direct-number calls,
with scientific concurrency one and no scientific retry.

## Verification

All 50 unique R1B tests passed on exact clean Commit A. Historical E3 tests
passed 49/49, the compatible E2 suite passed 39/39, E1 passed 28 with one
optional `jsonschema` skip, and E0 passed 59/59. Compilation, 510 JSON parses,
126 self-hash checks, two recovery-schema checks, `pip check`, leak scanning,
and `git diff --check` passed.

A deliberately broad E2 diagnostic retained four historical nonblocking
failures: three worktree-byte prompt hashes are Windows line-ending sensitive,
although the Git blob identities remain frozen; one E2-preparation test expects
the later E3 authorization artifact not to exist. These diagnostics do not
alter the compatible E2 result and were not patched.

Five implementation/audit lanes and two read-only exact-Commit-A test lanes
were used. File ownership conflicts, contradictory results, concurrent
authoritative writes, parallel provider calls, and concurrent private-custody
writes were all absent. The coordinator alone integrated and committed.

## Authority

R1B grants no provider-contact, recovery-probe, scientific-execution, Rule v2,
runtime, utility-evaluation, or winner-selection authority. The only next
authorized task is `TASK-039E3-R1B-AUDIT`, which must remain provider-offline.
