# V6 Canonical Context Collection

`CanonicalDelayedResponseArtifactCollectionV1` is the dataset-neutral context
accepted by the canonical delayed-response verifier and runtime-authority
path. It contains:

- `DatasetManifestV2`, `DataViewManifestV2`, and `SplitManifestV2`;
- one `CandidateGraphV1`;
- one `NormalRelationEvidenceV1`;
- one `RuleEvidenceBindingV1`;
- one `NormalReferenceSetBindingV1`;
- the exact tuple of `CalibrationParameterV1` artifacts.

The collection exposes only deterministic lookups for graph, edge, evidence,
normal-reference, and parameter IDs. It grants neither rule-binding nor
runtime authority.

## Build Result

`CanonicalContextBuildResultV1` is all-or-nothing:

- `created`: complete collection and both bindings;
- `pending_context`: an explicit edge, condition, parameter, severity, or
  persistence mapping is missing;
- `unsupported_source`: evidence is insufficient, unstable, or uses the
  unsupported decrease direction;
- `invalid_source`: a supplied artifact or mapping contradicts canonical
  identity, hash, variable, process, regime, lag, or direction constraints.

Failed results contain no partial collection or binding artifact.

## First-MVP Constraints

The bridge supports exactly one process and one source-to-target delayed
increase relation. The split role is
`normal_relation_calibration`. All constituent self-hashes are reparsed and
verified when the collection is created.

Collection integrity does not establish utility, governance selection,
deployment approval, causal semantics, or experimental performance.
