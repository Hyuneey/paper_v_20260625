# Combined prediction schema

## V1

`ScientificCombinedPredictionArtifactV1` binds execution/design/authorization,
D0 prediction, D1 prediction, source-map and fusion-evidence identities. Each of
54,000 ordered records contains `physical_row_index`, `d2_alarm_emitted`,
`trigger_class`, and `combined_decision_identity`. Root fields preserve the
label-blind flags, D0-preservation result, trigger counts, point-alarm count and
artifact self-hash.

## V2

`ScientificCombinedPredictionArtifactV2` adds separate V2 design,
native-horizon-map, and evidence-token authorities. Its record keeps the row,
final Boolean alarm, V2 trigger class and decision identity. Private evidence
contains active-source/token details; the public prediction does not expose
private source-time coordinates.

The schema does not contain an evaluation label. Episode and event results are
downstream metric objects, not fields that influence fusion.
