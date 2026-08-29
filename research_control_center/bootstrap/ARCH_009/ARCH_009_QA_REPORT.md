# ARCH-009 independent QA

Status: `PASS` — 20/20 questions passed.

| # | QA question | Verdict | Evidence summary |
|---:|---|---|---|
| 1 | D2 role correct? | PASS | Deterministic detector-preserving fusion pilot; not validated production fusion. |
| 2 | V1 policy source-supported? | PASS | Pointwise D0 OR exact-index two-distinct-source gate. |
| 3 | V2 policy source-supported? | PASS | Native-horizon active-token two-source gate. |
| 4 | Same-second precise? | PASS | Equality of D1 `decision_physical_row_index`, not trigger time or event overlap. |
| 5 | Distinct-source counting correct? | PASS | Canonical source identities are set-deduplicated. |
| 6 | Native-horizon/persistence precise? | PASS | Inclusive `i <= t <= i+h`, split-end clipped; no extra persistence threshold. |
| 7 | D0 preservation verified? | PASS | Both policies preserve every D0 alarm pointwise. |
| 8 | D0/D1 frozen before fusion? | PASS | Committed bytes, hashes, schemas and authority identities are checked. |
| 9 | Labels excluded? | PASS | Fusion reads no raw features or labels; custody opens after persistence. |
| 10 | V1 result mapped? | PASS | 11/14, 10 normal false episodes, FAR 0.7056194750975128, recovery 0/3. |
| 11 | V2 result mapped? | PASS | 11/14, 98 normal false episodes, FAR 6.915070855955625, recovery 0/3. |
| 12 | Recovery 0/3 supported? | PASS | Frozen metric and integrity evidence agree for both policies. |
| 13 | V2 test1-informed explicit? | PASS | Marked `TEST1_INFORMED_DEVELOPMENT`; not independent confirmation. |
| 14 | D2 durable freeze supported? | PASS | Atomic write, fsync/replace, reopen and validation precede label access. |
| 15 | FAR/hour interpreted correctly? | PASS | Normal false alarm episodes per normal exposure hour, not point FPR. |
| 16 | Fusion utility not overclaimed? | PASS | Current V1/V2 pilot does not support improvement. |
| 17 | General value unvalidated? | PASS | No general Detector+Rule conclusion is drawn. |
| 18 | Event-unit terminology correct? | PASS | Current-facing output uses 14 contiguous units and says independence is unestablished. |
| 19 | No new statistics? | PASS | Frozen evidence only; no new metric or significance calculation. |
| 20 | Zero scientific computation? | PASS | Safety counters and audit method report zero scientific execution. |

One stale current-facing `14개 독립 사건` phrase was found during review,
corrected in the generator, regenerated, and rescanned. No conflict remains
among source, frozen reports, registry, dashboard or generated summaries.
