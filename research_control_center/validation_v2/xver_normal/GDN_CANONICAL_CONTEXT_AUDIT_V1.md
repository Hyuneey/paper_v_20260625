# Canonical GDN context and external mapping audit

Task: HAI-XVER-NORMAL-PREP-001. Parent: `3a410f5b6aa32ce7aa7547ddc445cf50c1aa347b`.
Stage A and all HAI23 scientific authorities remain unchanged.

## Context identity

EXP-01C imports the frozen 37-node `P1_FEATURE_ORDER`. Twelve nodes are
candidate sources, twelve are targets and thirteen are context-only.
The model reads numeric tensors and their ordered node indices; engineering
role/unit metadata is not numerically consumed. The already-approved strict
role mapping remains mandatory for Rule sources/targets. Context-only nodes
use `NOT_REQUIRED_FOR_CONTEXT_ONLY_GDN` for role/unit; no engineering meaning
or unit is fabricated.

The external context is the ordered intersection of that frozen P1 universe
with exact tag identities in every version-local normal schema. Header
membership comes from the independently self-hashed parent projection receipts;
P1 identity comes from the frozen canonical EXP-01C P1 universe, not a guessed
prefix or alias. Unknown and replacement nodes are not admitted.

- HAI22: 36 mapped nodes; `P1_PP04D` absent.
- HAI21: 30 mapped nodes; `P1_PIT01_HH`, `P1_PP04`, `P1_PP04D`,
  `P1_PP04SP`, `P1_SOL01D`, `P1_SOL03D`, `P1_TIT03` absent.
- Both: `SCHEMA_BOUND_PARTIAL_CONTEXT_REPLICATION`; aliases and added nodes: 0.

`P1_PP04D` is not an unresolved role/unit blocker: it is absent in both external
normal schemas. No synthetic replacement, zero-fill, or substitution is used.
Context-only finite numeric type checks are completed by the separately
versioned positive-allowlist projection receipt, not inferred from a header.

## Model compatibility

`exp01c_backend_v1._model_type_v1` parameterizes embeddings, batched graph
offsets and output shapes by node count. The shared encoder, horizon head,
self-excluded Top-5 graph, fixed-edge masking, loss, optimizer and scaler
contracts are unchanged. Historical `exp03b_gdn_v1.infer` hardcodes HAI23
row counts/order and must not be called for external versions.

Synthetic CUDA tests instantiate fresh 36/30-node models; check forward/backward,
output/embedding shapes, self exclusion, repeat prediction invariance, graph
variant equivalence within the frozen tolerance, exact CPU/GPU window/target
generation, and purged raw-support nonoverlap. This is a synthetic preflight,
not one of the 12 scientific runs and not a full training throughput benchmark.
No HAI23 weights are loaded.

## Separate unresolved evidence method

Context and variable-node support are ready. The split-pure event-conditioned
provider estimator is not uniquely specified by the frozen historical paths.
See `GDN_EVENT_EVIDENCE_BINDING_DECISION_V1.md`. No scientific run or provider
readiness is claimed by the context/projection contracts.
