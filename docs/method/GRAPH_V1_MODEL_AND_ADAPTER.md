# Graph v1 Model and Phase 1 Adapter

`CandidateGraphV1` and its nested frozen records cover every field in the
canonical graph schema. Parsing begins with the TASK-032A `graph` registry,
then verifies the self-hash and bounded document coherence: unique IDs,
registered endpoints, no self-edges, ordered lag and uncertainty ranges, and
disabled causal claims.

These checks do not establish that a relation is physically correct or causal.
Every graph edge remains a candidate relation.

The Phase 1 graph adapter consumes serialized CandidateUniverse and optional
GDN edge mappings. It does not import Phase 1 classes or `paperworks.gdn`.
CandidateUniverse membership is checked before an optional GDN-ranked edge is
emitted. Node metadata, regimes, lag range, support, uncertainty, confidence,
edge semantics, and provenance must be supplied explicitly. Missing context
returns `pending_context` with no partial graph.

GDN similarity is not copied into graph confidence or presented as causality.
Only a structurally valid, hash-verified target can receive adapter status
`created`.
