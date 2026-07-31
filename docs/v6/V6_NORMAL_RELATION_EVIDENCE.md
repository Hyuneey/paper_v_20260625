# V6 Normal Relation Evidence

## Scope

`NormalRelationEvidenceV1` is the only core evidence type for v6 rule
construction. It describes one normal-data delayed response from one discrete
source to one continuous target. It is not an attack window, detector error,
causal model, physical invariant, validity decision, or runtime authorization.

## Required Lineage

The artifact binds dataset, view, `normal_relation_calibration` split, explicit
process scope, variable metadata, candidate universe and edge, operating
regime, matched-normal references, parameter references, provenance, and
creation metadata. Every artifact reference is a lowercase SHA-256.

## Evidence States

- `supported`: at least one matched response, stable relation, lag and
  absolute-magnitude summaries, matched-normal reference, and lag/tolerance
  parameter references.
- `insufficient_support`: registered machine-readable insufficiency reason;
  summaries and parameter references may be absent.
- `unstable`: unstable stability result and registered reason.

Support counts satisfy:

```text
trigger = evaluable + right_censored
evaluable = matched + missing
```

Distribution summaries are finite and ordered. Response magnitude has explicit
`absolute_response_magnitude` semantics, including for decrease relations.
Stability records observations only; no pass threshold is invented.

## Boundary

`raw_values_included`, `label_performance_used`, and
`detector_context_used` are always false. Physical causality, root cause, and
universal invariant claims are prohibited. `EvidencePackageV1` remains
anomaly-anchored and has no automatic conversion path.
