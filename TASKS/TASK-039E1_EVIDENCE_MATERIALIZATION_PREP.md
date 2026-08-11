# TASK-039E1-PREP: Synthetic Construction-Evidence Materialization

## Status

`passed_task039e1_evidence_materialization_preparation`

## Objective

Prepare deterministic, synthetic-only machinery that can later convert an
exact confirmed-relation binding, D1 source/target parameters, a D1
fit-supported directional record, a D2 confirmation record, and
preregistered D0 window constants into construction-evidence artifacts.

This branch consumes no real confirmation result or relation identity, opens
no private ledger or HAI data, calls no LLM, generates no rule, and grants no
runtime authority. It creates no TASK-039E1 authorization.

## Synthetic private-ledger counterparts

The preparation defines immutable structural counterparts for:

- a D1 source parameter record;
- a D1 target parameter record;
- a D1 directional fit-supported record;
- a D2 confirmation record.

Every accepted identity uses the `SYNTHETIC_` prefix. Every fixture record
declares itself synthetic and non-real. Numeric fixture values are visibly
fake and exist only in tests; the production preparation contracts contain no
real D1/D2 values or scientific numeric defaults.

## Exact materialization

`materialize_construction_evidence_v1(...)` validates:

- exact source and target identities;
- exact source and target directions;
- exact selected horizon;
- exact source/target parameter record hashes;
- exact D1 directional record hash;
- exact D2-to-D1 and D2 parameter bindings;
- exact relation-to-D1 and relation-to-D2 evidence references;
- D1-derived threshold, tolerance, and target-scale origins;
- fit-parameter reuse without retuning;
- `calibration_confirmed` status;
- content-derived numeric references.

Any mismatch fails closed. Collection materialization rejects duplicate
relation bindings.

## Private evidence and numeric authority

`PrivateConstructionEvidenceV1` contains construction-only values for the
source step threshold, source stability tolerance, target noise scale,
selected horizon, and seven preregistered window constants. Each numeric value
is bound to all of the following:

- its exact numeric role and value origin;
- source parameter record hash;
- target parameter record hash;
- D1 fit evidence hash;
- D2 confirmation evidence hash;
- window-constant bundle hash.

The resulting numeric reference is a deterministic hash over that complete
binding, including the private value. A changed value or provenance hash
therefore changes the reference and cannot satisfy the frozen E0 relation.
The materializer also emits E0's reference-only
`ApprovedNumericEvidenceBundleV1`; arbitrary numeric literals remain
prohibited.

## Window constants

`PreregisteredWindowConstantBundleV1` covers source pre/post windows, minimum
source stability fraction, source refractory period, cross-source isolation
radius, target baseline window, and target response window. The bundle binds
to D0 protocol, source-event, target-response, and confirmation policy hashes.
Its values are non-learned, never LLM-generated, and grant no runtime
authority.

## Public manifest and resolver

`PublicConstructionEvidenceManifestEntryV1` exposes relation identity,
directions, approved numeric role names, private record hash, and provenance
hashes. It contains no private numeric value or raw HAI. Selected horizon is
included only when a hashed disclosure policy permits it.

`resolve_private_numeric_reference_v1(...)` returns a construction-only
private value only when relation binding, numeric role, numeric reference,
private evidence hash, and approved evidence authority all match and runtime
authority remains false. The resolver cannot grant runtime authority.

## Non-authority statement

- Real D2 result consumed: `false`.
- Real confirmed relation identity consumed: `false`.
- D1 private ledger accessed: `false`.
- D2 private ledger accessed: `false`.
- HAI accessed: `false`.
- LLM called: `false`.
- Rule generated: `false`.
- Runtime authority: `false`.
- E1 authorization created: `false`.
