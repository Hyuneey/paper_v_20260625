# ARCH-008 Result Lineage

| Edge | Status | Evidence |
|---|---|---|
| COMMON-42 → V4 runtime authority | VERIFIED | descriptor, registry, evaluator and authorization identities in frozen execution artifacts |
| V4 runtime → D1 prediction | VERIFIED | prediction artifact hash `58c3c49f...` bound by execution receipt and integrity audit |
| Prediction complete → label access | VERIFIED_WITH_GOVERNANCE_QUALIFICATION | object validated before `_load_real_label_custody_v1`; no durable pre-label file |
| Prediction → attack/episode metrics | VERIFIED | prediction hash is bound in D1 metrics and metric-oracle artifacts |
| Metrics → frozen D1 result | VERIFIED | independent result-integrity audit passed arithmetic, census, label independence and immutability checks |
| Frozen D0/D1 predictions + one label parse → comparison | VERIFIED | comparison pins exact prediction hashes, derives arm metrics and overlap, then binds its output hashes; arm executions are zero |
| Result → RCC claim wording | VERIFIED | `claims.csv` remains pilot-only/unvalidated and terminology is COMMON-42 Verified Relational Rule-only |
| Result → thesis-facing wording | CONSTRAINED_NOT_GLOBALLY_REWRITTEN | professor note and claim matrix define allowed wording; ARCH-008 did not rewrite every thesis document |

The frozen pilot has no verified leakage finding. The absence of atomic durable prediction persistence before labels is a governance weakness for future independent validation, not evidence that the existing pilot was altered.
