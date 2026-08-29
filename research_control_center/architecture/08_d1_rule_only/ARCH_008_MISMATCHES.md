# ARCH-008 Mismatches

| ID | Misleading wording | Audited evidence | Severity | Recommended action |
|---|---|---|---|---|
| A008-M01 | 788 alarm seconds | 788 is anomalous rule records; 630 unique decision seconds | MEDIUM | Name the object level |
| A008-M02 | 630 rule violations | 630 is deduplicated alarm seconds | MEDIUM | Keep rule-record and second counts separate |
| A008-M03 | 626 normal false episodes | 626 is total alarm episodes; 574 are normal false episodes | HIGH | Preserve label-based classification |
| A008-M04 | 13/14 point recall or precision | It is attack-event overlap recall | HIGH | State event definition and denominator |
| A008-M05 | D1 is Agentic Rule-only | T2 is excluded from COMMON-42 | HIGH | Use COMMON-42 Verified Relational Rule-only |
| A008-M06 | D1 directly tests LLM Rule-only | COMMON-42 is shared T0/T1/T1-B executable-equivalent authority | HIGH | Mark direct LLM-arm runtime as not tested |
| A008-M07 | Higher pilot Recall proves superiority | D1 FAR is 40.50255787059723 versus D0 0.4939336325682589 | HIGH | Separate sensitivity and burden |
| A008-M08 | Complementarity is validated | D1-only=3 is a 14-event development-pilot signal | HIGH | Require independent expanded validation |
| A008-M09 | FAR/hour is point FPR | It counts normal false episodes per normal labeled hour | MEDIUM | Use episode-rate wording |
| A008-M10 | test1 is independent final validation | test1 is development / INNER pilot | HIGH | Keep pilot label |
| A008-M11 | D1 prediction was durably persisted before labels | It was validated and shallow-frozen in memory; public file followed metrics | HIGH | Require durable gate prospectively |
| A008-M12 | High FAR has an established cause | No frozen general cause decomposition exists | MEDIUM | Record CAUSE_NOT_YET_ANALYZED |
| A008-M13 | The 14 event units are statistically independent | Source establishes operational contiguous label-one event units only | MEDIUM | Do not upgrade operational separation to statistical independence |

Totals: 13 mismatches; CRITICAL 0, HIGH 8, MEDIUM 5, LOW 0.
