# DG05 executable authority closure V1

Status: `COMPLETE_QA_PASS_DG05_EXECUTABLE_CLOSURE_FROZEN`

This task closed the eight pre-access execution blockers reported by the immutable `MULTIPANEL-DG05-EXEC-001` audit. It did not execute DG-05. Attack/test payload access, label/scenario access, and real eligibility generation were all zero.

## Frozen boundary

The scientific preregistration, method bundle, portfolios, detector methods, Fusion semantics, metrics, eTaPR parameters, statistical contrasts, and panel definitions are unchanged. DEC-029 remains historical as `APPROVED_CONDITIONAL_TWO_PHASE` with execution suspended by the pre-access blocker. It cannot authorize the new executable hashes. A renewed DG-05 V2 approval is required.

## Blocker closure

| Blocker | Closure | Evidence | Status |
|---|---|---|---|
| B1 | State initialization accepts only the exact executable manifest and replays all nested scientific and executable authorities. Every transition binds the manifest, prior state, execution identity, evidence, and source commit. | `DG05_EXECUTABLE_AUTHORITY_MANIFEST_V1.json`; `EXECUTION_STATE_MACHINE_AUTHORITY_V1.json` | PASS |
| B2 | Result authorities use deterministic canonical bytes. The independent oracle accepts paths only and reopens the executable manifest, dispatch registry, complete cell census, terminal receipts, projections, timestamps, scenarios, denominators, eTaPR coordinates, and result bytes before recomputation. | implementation plus independent oracle | PASS |
| B3 | Method-blind scenario, denominator, and bound result builders are executable and covered by an end-to-end rehearsal. | `SYNTHETIC_DG05_REHEARSAL_V1.json` | PASS |
| B4 | Full official process scope distinguishes verified P1, verified non-P1, and unresolved identities. | `FULL_PROCESS_SCOPE_AUTHORITY_V1.json`; `P1_ELIGIBILITY_CUSTODIAN_V3.json` | PASS |
| B5 | Prediction, projection, timestamp, scenario, denominator, eTaPR, and paired-result coordinates must replay and agree on version, physical file, and authority hash. | production adapter and result tests | PASS |
| B6 | Label/scenario custody runs in a fresh process with a separately persisted private resource policy, closed source-format adapters, prediction-root denial, durable consume-before-read, and no prediction-capable request field. | `run_dg05_label_custodian_v1.py` | PASS |
| B7 | Production positive-allowlist projection and a closed, typed executor bind six detector assets and an exact-seven Rule-runtime registry. Candidate-portfolio lineage, retained semantic Rules, private relation/numeric bytes, Formal V4 semantics, and the pending DG05 V2 runtime-use authority are separate bindings. | `PRODUCTION_ADAPTER_AUTHORITY_V1.json`; `RULE_RUNTIME_SUBAUTHORITY_REGISTRY_V1.json` | PASS |
| B8 | PCA and Isolation Forest have separate panel-specific fit, threshold, model, mapping, callable, implementation-source, schema, and environment bindings. The bound callable is invoked, its source bytes replay at production time, and Fusion uses the bound local runtime helper. | `DETECTOR_SUBAUTHORITY_REGISTRY_V1.json`; `METHOD_DISPATCH_REGISTRY_V1.json` | PASS |

## Full process scope

The authority is based on the public official HAI technical-manual point tables, the frozen official schemas, and the already-frozen HAI23 DCS/process-graph evidence for x-tag identities.

| Version | Official schema identities | Verified P1 | Verified non-P1 | Unresolved |
|---|---:|---:|---:|---:|
| HAI 23.05 | 86 | 44 | 42 | 0 |
| HAI 22.04 | 86 | 44 | 42 | 0 |
| HAI 21.03 | 79 | 38 | 40 | 1 |

HAI21 has 79 observed header identities although its manual declares 78 points. `P2_SIT02` is the single header-only, manual-undocumented identity and remains `UNRESOLVED`; it is not guessed into P1 or non-P1.

## Detector and dispatch closure

The six detector subauthorities are panel- and method-specific. They preserve their existing PCA/Isolation Forest implementations, fit authorities, threshold authorities, private model-byte hashes, and feature mappings. The dispatch registry contains 23 exact panel/method entries: 9 for HAI23 and 7 each for HAI22 and HAI21. The derived file-by-method census contains 72 cells: 9 + 28 + 35.

## Synthetic two-phase rehearsal

The production adapters were exercised on synthetic label-bearing containers through the complete two-phase path:

`manifest initialization → positive allowlist projection → 72-cell dispatch → 71 success + 1 deliberate method failure receipt → global freeze → one lease → fresh-process custodian → 146 synthetic scenarios → method-blind P1 denominator → 23 result authorities → 23 independent result replays`.

The rehearsal reached `RESULT_INTEGRITY_AUDITED`. Seven distinct post-label authority mutations were rejected with their exact expected failure classes: manifest, metric, Rule portfolio, Fusion, P1 custodian, prediction bytes, and detector threshold. The intentional failed cell remained a failure and yielded `NOT_EVALUABLE_INCOMPLETE_PREDICTION_COVERAGE`; it was never converted into an empty prediction or a scientific negative.

## Authority hashes

- Scientific preregistration V2: `cffa6f00dadee1bdd400cdbee545eb9cccd93dcf5da8c6bab3f67809644e8c61`
- Executable manifest: `586202aedc3ea7996646035f29ee5c6fa62824ed4c0a255cd6bff17f0202ac42`
- State machine: `71e0febb462aa0580799781b9e8f2605ca944da3285f2720896dadb88a734beb`
- Full process scope: `0e4fb08ca07cf713df2e5021d9e2fe1721ec99a308cf7656ac63894b40ffe619`
- P1 custodian V3: `f688fae22866ac5bac7ac4517fd9171d7f0d907044f3afee9cd7a609a8919166`
- Detector registry: `c5f3f834435af6615e120f57c68c5d47eb66be8c07c4870c9f5fb0ee9cd832bb`
- Rule-runtime registry: `074768ef863e481482337df4af16ee12c5ef36fb52c2129417d0ad39aa98dd14`
- Dispatch registry: `246e19e4c9bcd81f8e139bd5ac609dac6db8a98add16013e1205641bb0c03433`
- Cell census: `87167612f6efa76b678334f7df66400a1fed40ee2264952f416b730f1836c009`
- Production adapters: `fdbd373815c09e042c4cce0edaa2541a7cca7a46874f268481799db8a72539cb`
- Synthetic rehearsal: `1f8790f482d759b51b51ac6cd3c7ca2087bf6632d4f629da4b2ab91cd9aa1c7c`
- Nested byte-replay bundle: `2f260ddeb5e64177578d140f7ce573921c4ff43cbe9886cbfddc8fe7d99a3f01`
- Independent QA: `30484d1204affa02dc5ba0079f06bc4b6d6be9c128a80f4a84c3b75b1543775a`
- Executable closure: `18dc3203e1b050aca5d052f9b7995cd9ba7a5fe5f3fbe2cfb6d4aae357b482b8`

## Scientific interpretation

This is an execution-authority and custody result, not attack-performance evidence. No held-out, external-version, superiority, generalization, or causal claim follows from the synthetic rehearsal.

Independent read-only QA passed and the final closure authority was regenerated against its immutable receipt. The exact next gate is `DG-05 REAPPROVAL — EXECUTABLE V2`.
