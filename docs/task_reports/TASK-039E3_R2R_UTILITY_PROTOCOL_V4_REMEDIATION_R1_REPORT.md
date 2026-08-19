# TASK-039E3 R2R Utility Protocol V4 bounded remediation R1

Status: `passed_task039e3_r2r_utility_protocol_v4_bounded_remediation_r1`

The R1 overlay closes the four authority-boundary findings left open by the blocked V4 independent audit. It changes protocol control semantics only. COMMON-42, the audited normal-only numeric descriptor, all 420 numeric references, feature-scope semantics, corrected regression authorities, and numeric values are unchanged.

## Authority transition

- Historical V4 authority: `2864c99017dcea576437efe9f9c5d531cc0d7810504cb2bd8e8585643d2fa0a1`
- V4 R1 authority: `1a6200adce791ddd9be8d87b566d47b65e78c1735829d0f91f4ea22127ad1343`
- Control revision: `R1`
- Source blob: `8ce6e56215246a5ec14ae148de20cdf0680c1658`
- Source SHA-256: `880bc1b08ea9941349042d664314184d8afa8337c13f778563b90404436429f9`

## Four closures

| Finding | R1 closure | Evidence | Result |
|---|---|---|---|
| Opportunity semantic identity | Public coordinate replay derives timestamp identity from frozen file structure and row index | Canonical first/last coordinates pass; deprecated timestamp input has no effect; self-consistent timestamp and row substitutions reject | CLOSED |
| Full-census provenance | Caller opportunity tuples cannot receive authoritative census custody | Empty, singleton, caller-selected 39, and one-row × 42 tuples reject; real enumeration authority remains unavailable | CLOSED |
| Recursive scalar/container policy | Full exact-class, exact-tuple, exact-inner-pair, and exact-scalar replay occurs before JSON hashing | All eight historical list mutations and additional generator, set, nested-pair, subtype, and scalar attacks reject | CLOSED |
| Terminal provenance | Deterministic window/boundary coordinates are public; empirical source/response outcomes require future evaluator evidence | Legacy helpers are explicitly `SYNTHETIC_CONTRACT_ONLY`; synthetic, self-rehashed, and caller-created objects cannot enter authoritative metric custody | CLOSED |

## Coordinate and evidence boundaries

The canonical file-coordinate authority is `6bfa5f41564cc09871463b24026b297ac12a347802b4fcecc8a094c94e3f15a0`, replayed from the frozen CSV structure report `d4f43034e9402806a4f34da943a1e39191503f8f54465d6d1f98b9cdc31bb7c9`.

The enumeration contract is `7f854ef13afb5c2e7f5864faac249ccdd3e39060f2d2b09811e8792481b9db5b`. Caller opportunity sets, counts, denominators, and relation subsets are all unauthorized; real enumeration authority is unavailable.

The runtime evidence contract is `20c7247c31045dc38e99dcac147abce284e7f375799dd45e9232af318e10a15e`. Caller source-window hashes, target-window hashes, `within_split`, and `response_matched` are not authoritative. Deterministic coordinate-boundary abstention remains authorized, but real source and response evidence authorities are both unavailable.

## Tests

- R1 focused: 36/36 PASS
- Original V4 implementation: 51/51 PASS
- V3 regression: 27/27 PASS
- V1/V2: 40 PASS, 2 documented private-custody skips
- Normal-only public/synthetic: 106/106 PASS
- compileall: PASS
- pip check: PASS
- git diff --check: PASS

No private registry, private numeric values, HAI normal/test values, labels, attack intervals, provider, API key, network, scientific LLM, or utility computation was accessed.

## R1 overlay hashes

- Remediation: `da9c028c8ab1173dfe51238176d0d6f55790b608152bb8840130c77626d5de2e`
- Contract: `d5e6a50d4e71e76f65cbaf55a22d2088ff4caf2d2f163364b54d0564b45b8071`
- Test report: `4f1a97f98be13fa373f3b3b5ef0d7ae9f1326c6d26f45f0f3e7a1dc5f9915330`
- Blocker matrix: `fcb0cdc2da44a6de6dc5a23d1882d45123b474fcb31c0a3dbd9f3487758ac7cd`
- Readiness: `519f60ad83aec6510c911a43c416eb67b7df2856df721f6be8689970b246135a`

The exact next task is `TASK-039E3-R2R-UTILITY-PROTOCOL-V4-R1-FOCUSED-INDEPENDENT-REAUDIT`. Evaluator implementation and execution authorization remain unavailable.
