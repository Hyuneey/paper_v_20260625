# ARCH-009 mismatch register

| ID | Misleading description | Audited correction | Severity |
|---|---|---|---|
| M-009-01 | D2 is neural/model fusion | Both policies are deterministic Boolean/source gates | MEDIUM |
| M-009-02 | V1 recovered detector misses | Frozen recovery is 0/3 | HIGH |
| M-009-03 | V2 recovered detector misses | Frozen recovery is 0/3 | HIGH |
| M-009-04 | V2 independently validates V1 | V2 is test1-informed development on the same split | HIGH |
| M-009-05 | D2 improved recall | D0 V1 and V2 are all 11/14 | HIGH |
| M-009-06 | D2 reduced FAR | V1 and V2 FAR exceed D0 | HIGH |
| M-009-07 | Detector+Rule generally failed | Only V1/V2 on the INNER pilot were tested | HIGH |
| M-009-08 | Every D1 response enters D2 | Both policies impose a two-source temporal gate | MEDIUM |
| M-009-09 | Fusion occurs at attack-event level | Fusion is pointwise; event grouping is downstream | HIGH |
| M-009-10 | Labels participate in fusion | Both combined predictions are frozen before label access | MEDIUM |
| M-009-11 | D2 has no durable gate | Both V1 and V2 persist/reopen predictions before labels | MEDIUM |
| M-009-12 | Fourteen statistically independent events | Fourteen contiguous operational event units; independence unestablished | HIGH |

Totals: **12** — CRITICAL 0, HIGH 8, MEDIUM 4, LOW 0.
