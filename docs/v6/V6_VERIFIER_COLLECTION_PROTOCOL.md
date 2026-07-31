# V6 Verifier Collection Protocol

`DelayedResponseArtifactCollectionProtocolV1` is the bounded structural
interface shared by the historical TASK-032 collection and the v6 canonical
collection.

It exposes:

- graph, evidence, and parameters;
- graph, edge, evidence, normal-reference, and parameter lookups;
- non-authoritative rule-binding and runtime flags.

The verifier and runtime-authority modules no longer import the concrete
Phase-1 collection class.

## Normalized Evidence

The internal `NormalizedEvidenceViewV1` projects either:

- legacy `EvidencePackageV1`; or
- v6 `RuleEvidenceBindingV1`.

The view is not persisted and creates no new evidence. It contains only fields
needed for deterministic graph, lag, split, evidence, normal-reference, and
claim checks.

## Verifier Boundary

The twenty ordered stages and legacy result semantics remain unchanged. V6
evidence adds fail-closed checks for:

- `normal_relation_calibration`;
- exact `EVID-V6-*` binding;
- exact `NREF-V6-*` matched-normal binding;
- label-free and non-authoritative evidence;
- graph, variable, regime, dataset, lag, and parameter agreement.

Normal false-fire, inner attack coverage, detector recovery, and no-op
selection do not enter deterministic validity.
