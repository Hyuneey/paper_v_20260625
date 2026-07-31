# V6 Normal Evidence Rule Binding

`NormalRelationEvidenceV1` remains the scientific source. TASK-039P1C does not
convert it to anomaly-anchored `EvidencePackageV1`.

## Normal Reference Binding

`NormalReferenceSetBindingV1` maps one or more matched-normal SHA-256
references to one Rule v1-compatible `NREF-V6-*` ID. It preserves dataset,
view, split, process, subsystem, regime, and deterministic matching-policy
lineage. It contains no raw values and grants no authority.

## Evidence Binding

`RuleEvidenceBindingV1` maps one supported normal-evidence artifact to one
Rule v1-compatible `EVID-V6-*` ID. It preserves:

- the original evidence ID and self-hash;
- explicit graph edge and regime-condition bindings;
- canonical parameter IDs and source hashes;
- the generated normal-reference binding;
- candidate lag bounds;
- supported and prohibited claim boundaries.

Required supported claims are `state_conditioned_response` and `typical_lag`.
Physical causality, root cause, and universal-invariant claims remain
prohibited.

## Explicit Mapping

Names never create scientific bindings. The builder requires:

- candidate-edge hash to canonical `EDGE-*`;
- condition hash to canonical condition ID and exact artifact hash;
- calibration-parameter hash to canonical `PARAM-*`;
- explicit persistence, support, and severity parameter roles.

Missing mappings return `pending_context`; contradictory mappings return
`invalid_source`. Decrease evidence returns `unsupported_source`.
