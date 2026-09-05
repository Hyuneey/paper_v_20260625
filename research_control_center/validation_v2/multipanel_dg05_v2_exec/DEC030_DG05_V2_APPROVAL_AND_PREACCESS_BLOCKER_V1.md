# DEC-030 — DG05 Executable V2 Approval and Pre-Access Blocker

Date: 2026-09-05 (Asia/Seoul)

Decision: `APPROVED_CONDITIONAL_TWO_PHASE_EXECUTION`

The research owner reapproved DG-05 under the exact Executable V2 authorities
for HAI 23.05 test2, HAI 22.04, and HAI 21.03. Historical DEC-029 and DG-05 V1
remain preserved, suspended, and unavailable as execution authority.

## Bound approval

- scientific preregistration: `cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61`
- executable manifest: `586202aedc3ea7996646035f29ee5c6fa62824ed4c0a255cd6bff17f0202ac42`
- executable closure: `18dc3203e1b050aca5d052f9b7995cd9ba7a5fe5f3fbe2cfb6d4aae357b482b8`
- result builder/adapter code: `c424b90582e743d841615f5c3e4b9fc1d3fa316b714b271d0553ef3295c39926`
- independent verifier code: `97c182df74ba2d720f5d4e62f8d28dfe533347e246b40aa4aecd1bdd9b41ae5b`
- metric authority: `1222d0c7431376dbfa77451875f811123f41af881ae1472b30cd4a2e0f1f0776`

## Pre-access disposition

Status: `BLOCKED_DG05_V2_EXECUTABLE_AUTHORITY_REPLAY`

All listed hashes replay byte-for-byte. Functional replay nevertheless fails
the approved scientific contract before Phase A: the exact result builder and
the exact independent verifier do not implement the complete frozen metric and
result-integrity surface required by this approval.

The approved builder persists Scenario HIT/MISS, Recall, Wilson interval, and
authority bindings. Its paired helper persists only A-only and B-only counts.
The approved independent verifier independently recomputes Scenario HIT/MISS,
Recall, and Wilson and checks eTaPR coordinate bindings, but it does not compute
or replay the following required outputs:

- eTaP, eTaR, and eTaPR F1 values;
- detection delay and its version-level median/IQR;
- complete paired tables and exact McNemar results;
- Rule response versus actual Fusion recovery;
- Rule runtime census;
- frozen normal-burden metric payloads.

The result replay input type also has no Rule trace paths, so the approved
oracle cannot independently reproduce Rule runtime or Rule/Fusion recovery.
Paired contrast artifacts are not included in the approved result bundle.

Adding these behaviors would change one or both exact approved code hashes and
therefore invalidate the executable manifest and nested replay. The gap cannot
be corrected after Phase A without violating the approval boundary.

## Safety outcome

- Phase A started: `NO`
- attack/test containers opened: `0`
- feature projections produced: `0`
- prediction cells executed: `0`
- label/scenario values opened: `0`
- lease issues / consumes: `0 / 0`
- provider calls / credential reads: `0 / 0`
- frozen scientific artifacts changed: `0`
- private exposure: `0`

The approval is recorded but not exercised. A new pre-access closure must bind
a complete production result builder and independent oracle, followed by a new
exact DG-05 approval. No bypass is authorized.

Exact next task: `DG05-V2-METRIC-VERIFIER-CLOSURE-001`.
