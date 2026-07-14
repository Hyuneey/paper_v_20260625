# Multivariate Graph Schema

## Graph definition

The directed attributed graph is `G = (V, E)`. It is persisted under
`schemas/graph_schema.json` and must point to a CandidateUniverse created before
graph scoring.

## Nodes

Allowed node types are `sensor`, `actuator`, `derived_state`, and
`subsystem_state`. Required fields are node ID, variable and display names,
type, subsystem, physical unit, data type, allowed states, sampling interval,
and metadata provenance.

Derived nodes must be project-owned, versioned transformations. They cannot be
invented by an agent inside a rule request.

## Edges

An edge is directed from a registered source node to a registered target node.
It records relation-family candidates, lag range, regimes, evidence sources,
support, confidence, uncertainty, semantics, and provenance.

Allowed semantics:

- `physical_topology`
- `documented_dependency`
- `temporal_association`
- `statistical_dependency`
- `attack_metadata_weak_prior`
- `subsystem_prior`
- `learned_graph_candidate`

Each edge separately records whether it is physical, documented, statistical,
or weakly supervised. `causal_claim_allowed` is always false.

## Candidate origins

Candidates may come from physical topology, subsystem membership, compatible
types, temporal association, GDN-style scores, bounded statistical screening,
or attack metadata as a weak prior. Attack metadata cannot create labels for
causal or physical ground truth.

The graph model may rank or remove CandidateUniverse edges. It cannot add an
unregistered variable or a pair outside the approved universe.

## Validation rules

- Source and target node IDs must exist and differ.
- Persisted candidate self-edges are prohibited.
- Relation-family candidates must come from the versioned registry.
- Lag units and node sampling intervals must be structurally compatible.
- Confidence is bounded to `[0,1]`; uncertainty includes method and bounds.
- Edge provenance must identify its CandidateUniverse or source artifacts.
- Graph scoring and message-passing self-loops are separate artifacts.

## Claim vocabulary

Allowed: candidate relation, predictive relation, temporal association,
documented dependency, graph-ranked pair.

Prohibited without independent evidence: causal edge, root cause, physical
law, universal invariant.
