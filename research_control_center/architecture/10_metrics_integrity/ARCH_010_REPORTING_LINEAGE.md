# Reporting Lineage

| Edge | Status | Qualification |
|---|---|---|
| frozen D0 prediction → D0 metric | VERIFIED | durable pre-label persistence and replay |
| frozen D1 object → D1 metric | VERIFIED_WITH_QUALIFICATION | label-blind object freeze; no durable file gate |
| frozen D2 V1/V2 prediction → metric | VERIFIED | durable pre-label persistence and replay |
| label authority → event/exposure objects | VERIFIED | existing private-custody/integrity evidence only |
| per-arm metric → integrity receipt | VERIFIED | identities and arithmetic checked |
| per-arm results → cross-arm comparison artifact | PARTIAL | artifact is frozen; aggregation source is not discoverable in current tree |
| result → current RCC | VERIFIED | exact frozen values and pilot qualifiers retained |
| result → scientific validation claim | FORBIDDEN | integrity and pilot observations do not establish validation |

Current-facing RCC documents must use “14 contiguous attack-event units; statistical independence not established,” “COMMON-42 Verified Relational Rule-only,” and “V2 test1-informed development.” Historical records are not rewritten broadly.
