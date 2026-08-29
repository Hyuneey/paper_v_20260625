# Prior High-Risk Carryover Disposition

| Source | Prior finding | Disposition | ARCH-005 evidence / next owner |
|---|---|---|---|
| ARCH-000 | Canonical verifier/runtime authority versus task-specific authority | PARTIALLY_RESOLVED | The two planes and frozen D1 authority are mapped; no proposal-to-RuleV1 bridge exists. A future explicit bridge is a code/design task. |
| ARCH-000 | Multiple construction/recovery entrypoints obscure the authoritative path | PARTIALLY_RESOLVED | Frozen construction uses task validity V2 and frozen D1 uses V4/evaluator/committed grant. Broader runtime-entrypoint equivalence remains for ARCH-006. |
| ARCH-000 | D1 task-specific trace versus canonical `RuntimeTraceV1` | DEFER_TO_ARCH_006 | ARCH-005 proves the authority plane but does not prove trace-schema or explanation equivalence. |
| ARCH-003 | Construction and runtime numeric authority identities differ | RESOLVED | Qualified resolution: focused audit proves 420/420 shared-value equality; V4 intentionally rebinds new runtime identities and keeps horizon descriptor-bound. Identity equality is not claimed. |
| ARCH-004 | Proposal admissibility may be mistaken for canonical RuleV1 validity | REQUIRES_CODE_FIX | An explicitly authorized future bridge is the design alternative; no tracked lossless materialization bridge exists today. |
| ARCH-004 | Distinct failures collapse into `no_rule` | REQUIRES_CODE_FIX | Frozen three cases are interpretable unsupported-variable rejections, but the general persisted taxonomy remains conflated. |
| ARCH-004 | COMMON-42/D1 may be called Agentic or LLM Rule-only | RESOLVED | COMMON-42 is the T0/T1/T1-B shared V4 projection; T2 is excluded. Preferred term is COMMON-42 Verified Relational Rule-only. |

Summary: 2 resolved (one qualified), 2 partially resolved, 1 deferred to ARCH-006, and 2 code/design-fix candidates. No code was changed in ARCH-005.
