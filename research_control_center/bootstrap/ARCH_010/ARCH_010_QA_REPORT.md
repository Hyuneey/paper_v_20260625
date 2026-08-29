# ARCH-010 Independent QA

Status: **PASS** — 20/20 required questions.

| # | Question | Verdict | Evidence summary |
|---:|---|---|---|
| 1 | Attack-event construction | PASS | maximal contiguous strict-label-1 half-open runs |
| 2 | Count 14 | PASS | frozen D0/D1/D2 metric and integrity artifacts |
| 3 | Independence | PASS | explicitly NOT_ESTABLISHED |
| 4 | Event hit | PASS | any non-empty half-open episode overlap |
| 5 | Recall | PASS | detected units / 14 |
| 6 | Point adjustment | PASS | PA-FREE; no grace or dilation |
| 7 | Episode grouping | PASS | set dedup; exact +1 adjacency |
| 8 | Normal false episode | PASS | no attack overlap; mixed episodes not split |
| 9 | Exposure | PASS | 51,019 strict label-0 seconds |
| 10 | FAR/hour | PASS | false episodes / exposure hours |
| 11 | Cross-method interface | PASS | semantically equivalent after adapters |
| 12 | D1 non-opportunity | PASS | no alarm timestamp; runtime meaning retained; abstain 0 |
| 13 | D0/D1 overlap | PASS | 10 / 1 / 3 / 0 event-unit vectors |
| 14 | D0-miss recovery | PASS | D1 3/3; V1/V2 0/3 secondary diagnostic |
| 15 | Frozen values | PASS | artifact-grounded; aggregation source gap marked PARTIAL |
| 16 | Integrity scope | PASS | identity/custody/order/schema/arithmetic/report binding |
| 17 | Integrity vs validity | PASS | scientific validity explicitly excluded |
| 18 | V2 status | PASS | TEST1_INFORMED_DEVELOPMENT |
| 19 | Inferential tests | PASS | NONE_FROZEN_OR_AUTHORITATIVE |
| 20 | Zero execution | PASS | static/RCC-only QA; test2 0 |

Initial QA found incorrect function names and paths in the catalog. The coordinator corrected all rows against actual repository definitions; re-review confirmed all 16 paths and symbols exist. No unresolved conflict remains.

Mismatches: 12 total; CRITICAL 0; HIGH 5; MEDIUM 7; LOW 0. Privacy and safety PASS.
