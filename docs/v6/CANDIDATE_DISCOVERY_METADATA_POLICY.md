# Candidate Discovery Metadata Policy

`TASK-039C-META` uses no HAI feature values. Approved evidence is limited to
the official HAI technical manual, approved P1 reference graph, reviewed
variable-role metadata, equipment or subsystem membership, and reviewed
manual semantic mappings.

Evidence tiers are ordered:

1. `M1_EXPLICIT`: official documentation supports a direct relationship or
   directly connected control/process chain.
2. `M2_GRAPH_ADJACENT`: the approved official P1 graph contains a compatible
   direct adjacency without a direct causal statement.
3. `M3_SUBSYSTEM_SUPPORTED`: a reviewed common equipment or subsystem chain
   makes the pair semantically plausible without a direct graph edge.
4. `UNSUPPORTED`: no approved metadata evidence supports prioritization.

Within a tier, ranking uses the number of independent official references,
then canonical source and target identities. The official graph is a weak
relation reference, not causal truth. LLM semantic guessing is prohibited.

Policy hash: `5fc43a043f0e75a56cab855a466a97a394fc1a6fdb67461b17696034547e4af3`.
