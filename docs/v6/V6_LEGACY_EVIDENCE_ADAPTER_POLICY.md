# V6 Legacy Evidence Adapter Policy

## Input

The adapter accepts serialized mappings representing one legacy
`RelationProfile` and one `RelationEvidencePack`. It does not import legacy
classes and does not adapt anomaly-anchored `EvidencePackageV1`.

External context must supply dataset/view/split/process lineage, metadata and
candidate references, operating regime, matched-normal references, stability,
parameter references, response direction, and creation metadata.

## Mapping Gate

The source split must be `calibration_normal`, and the requested target role
must explicitly be `normal_relation_calibration`. Unsupported relation or
split semantics terminate without a target.

Terminal statuses are:

- `created`;
- `pending_context`;
- `unsupported_source`;
- `invalid_source`.

Only aggregate counts and explicitly named summaries are mapped. Raw trigger
and response events, calibrated numeric values, attack labels, detector
errors, and anomaly events are not copied. Missing p95, persistence, and
magnitude-unit semantics are reported as information loss.

The adapter never emits a partial target and grants neither rule validity nor
runtime authority.
