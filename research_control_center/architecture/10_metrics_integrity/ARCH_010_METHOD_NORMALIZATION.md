# Cross-method Metric Normalization

Classification: **SEMANTICALLY_EQUIVALENT** metric interface; **FAIR_WITH_LIMITATIONS** for current common metrics.

| Method | Native output | Common alarm-second interface |
|---|---|---|
| D0 | Complete Boolean prediction at every test1 row | true rows become alarm seconds |
| D1 | Opportunity-level terminal rule records | only `evaluated_anomaly` records with a non-null `decision_physical_row_index` contribute; rows are set-deduplicated |
| D2 V1/V2 | Complete combined Boolean prediction at every test1 row | true rows become alarm seconds |

D1 non-opportunity, non-alarming, and abstain states contribute no alarm timestamp and are therefore operationally `NO_ALARM` at the Boolean metric interface. That does not erase their different runtime meaning. The frozen D1 cohort has zero abstain records. D1 is timestamped at the post-horizon decision row, not the source trigger row.

All methods share the same test1 row grid, label authority, 14 event units, 51,019 normal seconds, half-open overlap rule, zero-gap episode grouping, Recall formula, and FAR formula. They do not use one single monolithic wrapper: method-specific adapters and evidence records remain separate. D0 continuously evaluates each timestamp; D1 only creates opportunities. The common Recall/FAR comparison is therefore useful but structurally limited.

The frozen cross-arm comparison artifact reports the common values, but its aggregation source is not discoverable in the current scientific tree. Per-arm metric code and self-hashed artifacts are traceable; the final cross-arm aggregation edge is **PARTIAL**.
