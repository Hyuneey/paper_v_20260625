# ARCH-007 D0 State Machine

| State | Operation | Failure behavior |
|---|---|---|
| NOT_STARTED | no private authority loaded | repeated real entry is rejected |
| GRANT_REPLAYED | committed one-attempt grant and numeric backend validated | mismatch fails closed |
| PRIVATE_AUTHORITY_VALIDATED | frozen preprocessing/model/threshold hashes and schemas replayed | stale or malformed authority rejected |
| FEATURE_PARSED | exact test1 feature identity and 37-column frame parsed | labels are not yet accessible |
| SCORES_COMPUTED | SPE vector and strict `score > threshold` mask created | non-finite/shape errors fail closed |
| PREDICTION_FROZEN | public prediction bytes atomically written and replay-validated | label access gate opens only now |
| LABEL_PARSED | test1 labels opened and aligned to frozen timestamps | pre-freeze access rejected |
| METRICS_COMPUTED | alarm episodes and two pilot metrics produced | prediction bytes must still match |
| RESULT_FROZEN | result reports and integrity bindings finalized | mutation fails closed |

Point decision truth table:

| Condition | Point output |
|---|---|
| `score < threshold` | NORMAL / no alarm |
| `score == threshold` | NORMAL / no alarm |
| `score > threshold` | ALARM |
| invalid/non-finite authority or input | hard error, not NORMAL |

D0 has a binary scientific point prediction after valid input. Invalid data or authority is a system failure; it is not an abstention.

