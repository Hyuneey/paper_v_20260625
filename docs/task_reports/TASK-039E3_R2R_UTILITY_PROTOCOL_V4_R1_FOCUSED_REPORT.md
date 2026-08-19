# TASK-039E3 R2R Utility Protocol V4 R1 focused independent re-audit

Status: `passed_task039e3_r2r_utility_protocol_v4_r1_focused_independent_reaudit`

Base: `743d2c3ab7dbd1a1729a057cbd046f88c06b59e4`

Focused Audit Commit A: `32fbe151794d40ae0e60e0638b8c8c854e7d5143`

The focused audit independently attacked only the four R1-remediated authority boundaries. The oracle reconstructed public coordinate identity with the Python standard library and lower committed authorities; R1 production validators were attack subjects rather than the primary source of expected values.

## Four findings

| Finding | Independent attacks | Accepted invalid authoritative cases | Result |
|---|---:|---:|---|
| Opportunity row/time semantic identity | 8 | 0 | CLOSED |
| Caller full-census authority | 9 | 0 | CLOSED |
| Recursive exact internal types | 18 | 0 | CLOSED |
| Runtime evaluator-evidence authority | 13 | 0 | CLOSED |

Total focused adversarial cases: 48. Total focused test methods: 62. No invalid authoritative case was accepted.

## Coordinate authority

- CSV structure report: `d4f43034e9402806a4f34da943a1e39191503f8f54465d6d1f98b9cdc31bb7c9`
- Coordinate authority: `6bfa5f41564cc09871463b24026b297ac12a347802b4fcecc8a094c94e3f15a0`
- Test1 first/interior/last: PASS
- Test2 first/interior/last: PASS
- Deprecated caller timestamp influence: none
- Historical self-consistent timestamp bypass accepted: 0

## Census authority

- Enumeration contract: `7f854ef13afb5c2e7f5864faac249ccdd3e39060f2d2b09811e8792481b9db5b`
- Empty, singleton, caller-selected 39, and one-row × 42: all rejected
- Authoritative caller census hashes issued: 0
- Real enumeration authority available: false

## Recursive type authority

- Policy: `d0f549f2ce9b9ac058aa362d9579068fec2fb03a2d2cde4a4495ecc3d70db7f0`
- Historical tuple-to-list attacks: 8/8 rejected
- Focused additional widening/subtype attacks: 10/10 rejected
- Read-only lane extended attacks: 52/52 rejected

## Runtime evidence authority

- Contract: `20c7247c31045dc38e99dcac147abce284e7f375799dd45e9232af318e10a15e`
- Caller source window, target window, `within_split`, and `response_matched` authority: false
- Synthetic helper scope: `SYNTHETIC_CONTRACT_ONLY`
- Synthetic metric-custody acceptances: 0
- Real source evidence authority available: false
- Real response evidence authority available: false

## Minimal invariants

- COMMON: 42 relations, 9 sources, 10 targets
- Numeric descriptor: `665af1d58d672dfe8109c01e5dcb4e8f19aa2303a8f6100bfd20b3272c3bd928`
- New reference set: `d14cf57a33a4e7018cbd2342f1a5fb9fc78dfd9d86f912512a903740316c73ae`
- References: 420
- Evaluator schema: 12/10/22
- COMMON footprint: 9/10/19
- T2 utility authorized: false

## Execution results

- Focused independent: 62/62 PASS
- R1 remediation: 36/36 PASS
- Original V4: 51/51 PASS
- V3: 27/27 PASS
- V1/V2: 40 PASS, 2 documented private-custody skips
- Normal-only public/synthetic: 106/106 PASS
- compileall, pip check, git diff check, public JSON self-hash and cross-binding: PASS

Production V4, the R1 remediation test, original V4 test, and historical blocked-audit test/helper remained byte-identical. No private registry, numeric values, HAI data, labels, attack intervals, utility computation, provider, API key, network, or scientific LLM was accessed.

## Report hashes

- Audit: `8c66590f222ad656add781745a361e483ba0ecd3c42bccbfa11f08cfaa6550ae`
- Coordinate: `88596b092847cd65aa53d9a3972f58410d592eb8833b1d23bf8ca9266cb52d2a`
- Census: `241e6b3d86c2fedfca9acc6106529a9dee240f082d03f574cbc3157e95475018`
- Type: `c36e1d98c170d7ac5a728159ae90f8e8f5de6e49fa9914f0953f328c15aa3161`
- Evidence: `d5666ac9cd60846497e7430e2e8223c0e61ae77fbbfadaefff060a6ba45ef044`
- Test report: `7d4bd04d72a25836b17231e8842232086ed881de8d85934e149b1d7e7bf4efb7`
- Readiness: `8ce41985d44ac0d8c00fbdc9b445c2fb5afebff410b4621effd0ad4f0c7312a1`
- Bundle: `2d8fb4f4400af6f95c387de2b6b7b4bdff9a007813fd16515dfbd11d4fc7e0df`
- Receipt: `09cf661a21cb4bd0d5ad356c2cf725264d76aeaffc7963858425e88267717509`

This PASS authorizes evaluator implementation only. Utility execution authorization remains false. The exact next task is `TASK-039E3-R2R-UTILITY-EVALUATOR-V1-IMPLEMENTATION-AND-FREEZE`.
