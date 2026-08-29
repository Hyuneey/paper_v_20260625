# ARCH-008 Output Levels

| Level | Object | Producer / deduplication | Frozen count | Metric relevance |
|---|---|---|---:|---|
| 1 | Rule opportunity | One applicable descriptor-source-event envelope | 6,031 | Evaluation denominator for rule execution, not attack recall |
| 2 | Rule outcome record | One terminal record per opportunity | 6,031 | Includes evaluated normal/anomaly; frozen abstain and error counts are zero |
| 3 | Anomalous rule record | Outcome record with `alarm_emitted=true` | 788 | Rule-level violations; duplicates may share a decision second |
| 4 | Unique alarm second | Decision indices deduplicated across rules | 630 | Input to episode construction |
| 5 | Alarm episode | Maximal run of consecutive alarm seconds | 626 | Total D1 alarm episodes before label-based false/attack classification |
| 6 | Attack event detected | Maximal contiguous label-one event overlapped by at least one alarm episode | 13 of 14 | Attack-event Recall numerator |
| 7 | Normal false episode | Alarm episode overlapping no attack timestamp | 574 | Normal false-episode numerator |
| 8 | FAR/hour | Normal false episodes divided by normal labeled seconds over 3,600 | 40.50255787059723 | Episode rate, not point FPR |

`788`, `630`, `626`, and `574` therefore cannot be substituted for one another. In particular, 626 is the total alarm-episode count, not the normal false-episode count.
