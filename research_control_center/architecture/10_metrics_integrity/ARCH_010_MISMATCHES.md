# ARCH-010 Mismatches

| ID | Documented behavior | Actual implementation | Type | Scientific impact | Severity | Recommended action |
|---|---|---|---|---|---|---|
| M-010-01 | point alarms and episodes used interchangeably | points are deduplicated then grouped | TERMINOLOGY | denominators can be misread | MEDIUM | keep object hierarchy visible |
| M-010-02 | D1 rule record treated as alarm second | 788 records collapse to 630 seconds | TERMINOLOGY | overstates temporal alarm coverage | MEDIUM | report both levels |
| M-010-03 | attack event and alarm episode conflated | event units come from labels; episodes from predictions | TERMINOLOGY | Recall meaning becomes wrong | MEDIUM | use separate terms |
| M-010-04 | FAR/hour described as FPR | FAR numerator is episodes and denominator exposure hours | METRIC | invalid cross-study interpretation | HIGH | always say episodes/hour |
| M-010-05 | mixed episode handling omitted | any attack overlap excludes whole episode from normal-FP numerator | BOUNDARY | FAR depends on boundary rule | MEDIUM | document half-open whole-episode rule |
| M-010-06 | all methods said to use an identical pipeline | wrappers differ but common semantics match | COMPARABILITY | hides D1 normalization | MEDIUM | use SEMANTICALLY_EQUIVALENT |
| M-010-07 | D1 abstain/non-opportunity silently called normal | both contribute no alarm timestamp at metric interface | NORMALIZATION | runtime meaning can be erased | HIGH | disclose Boolean-interface conversion |
| M-010-08 | D2 V2 presented as independent test | V2 is test1-informed development | SPLIT_ROLE | development reuse can be mistaken for confirmation | HIGH | retain development label |
| M-010-09 | 14 units called independent events | only contiguous-run identity is established | STATISTICS | overstates effective evidence | HIGH | use contiguous attack-event units |
| M-010-10 | integrity PASS presented as validation PASS | integrity checks identity/custody/arithmetic only | CLAIM | overstates scientific support | HIGH | separate integrity and validity |
| M-010-11 | cross-arm comparison fully source-reproducible | comparison artifact exists but aggregation source is not discoverable | LINEAGE | final aggregation edge is partial | MEDIUM | triage in GAP-000 |
| M-010-12 | generic episode/event helper fully enforces one-second file-local semantics | file and sampling constraints arrive from caller authority | CONTRACT | future multi-file/missing-time misuse is possible | MEDIUM | triage explicit contract checks |

Counts: **12 total; CRITICAL 0; HIGH 5; MEDIUM 7; LOW 0.** No verified metric tampering or scientific leakage was found.
