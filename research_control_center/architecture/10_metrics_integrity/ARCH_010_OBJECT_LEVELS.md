# ARCH-010 Metric Object Levels

| Level | Definition | Producer | Deduplication | Consumer |
|---|---|---|---|---|
| D0 SPE score | One nonnegative residual score per test1 row | D0 PCA-SPE scorer | none | D0 comparator |
| D0 point alarm | `score > threshold` Boolean at a physical row | D0 comparator | one record per row | episode constructor |
| D1 opportunity | One source-event / relation evaluation opportunity | V4 rule evaluator | not an alarm object | rule outcome logic |
| D1 rule outcome record | Terminal result for one opportunity | V4 evaluator | relation-specific records retained | D1 prediction adapter |
| D1 anomalous rule record | `evaluated_anomaly` terminal record with a decision row | D1 prediction adapter | duplicates retained at record level | alarm-second adapter |
| unique alarm second | Set-deduplicated physical row containing one or more alarms | common adapter | set by physical row | episode constructor |
| D2 combined alarm | Per-row Boolean, `D0 OR admitted D1 evidence` | V1/V2 policy | one Boolean per row | episode constructor |
| alarm episode | Maximal run of adjacent alarm rows, represented `[start,end)` | common utility metric | unique rows before grouping | Recall and FAR |
| attack-event unit | Maximal run of strict label token `1`, `[start,end)` | label-event constructor | one unit per maximal run | Recall denominator |
| detected attack-event unit | Attack unit overlapped by at least one alarm episode | event-overlap evaluator | event counted once | Recall numerator |
| normal false episode | Alarm episode with no overlap with any attack unit | normal evaluator | mixed episodes are not split | FAR numerator |
| normal exposure | Number of rows whose strict label token is `0`, at one second per row | label exposure counter | row count | FAR denominator |
| Attack-event Recall | detected attack-event units / all attack-event units | metric evaluator | event-unit level | result report |
| FAR/hour | normal false episodes / (normal exposure seconds / 3600) | metric evaluator | episode level | result report |

D1's 6,031 opportunities, 788 anomalous records, 630 unique alarm seconds, 626 episodes, and 574 normal false episodes are intentionally different counts.
