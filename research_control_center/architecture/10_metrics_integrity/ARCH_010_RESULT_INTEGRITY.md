# Result Integrity Pipeline

## Lineage

```text
prediction identity + label identity + metric contract
→ metric result → integrity receipt → public report → RCC/thesis-facing number
```

| Check | D0 | D1 | D2 V1 | D2 V2 |
|---|---|---|---|---|
| prediction identity/hash | CHECKED | CHECKED downstream; pre-label object freeze weaker | CHECKED | CHECKED |
| label identity/hash | CHECKED | CHECKED | CHECKED | CHECKED |
| row count/order | CHECKED | CHECKED opportunity/index closure | CHECKED | CHECKED |
| prediction before label | durable persist/reopen | validated shallow-frozen object; not durable file gate | durable persist/reopen | durable persist/reopen |
| arithmetic/formula consistency | CHECKED | CHECKED | CHECKED | CHECKED |
| report/result binding | CHECKED | CHECKED | CHECKED | CHECKED |
| post-result mutation | rejected/zero | checked downstream | rejected/zero | rejected/zero |

D1's downstream hashes and metric audits improve traceability but cannot retroactively provide the stronger atomic file-before-label boundary used by D0 and D2.

## Integrity can establish

- the expected frozen prediction and label authorities were used;
- ordering, row counts, schemas, and arithmetic agree;
- custody/report identities match the audited artifacts;
- recorded mutation counters and replay checks passed.

## Integrity cannot establish

- sufficient sample size or statistical independence;
- absence of development-set reuse;
- generalization, superiority, causality, operational usefulness, or human benefit.

D2 V2 remains `TEST1_INFORMED_DEVELOPMENT`. Integrity PASS does not convert it into independent validation. No frozen authoritative inferential test exists.
