# Candidate Discovery GDN Policy

`TASK-039C-GDN` is authorized only for a source-faithful learned graph aligned
with `d-ailin/GDN` commit
`9853899da860682669a134e4af315d036aab4eca`. Before training, it must produce
an `UpstreamGDNFidelityReceipt` establishing the frozen architecture, graph
construction, embeddings, Top-K semantics, prediction loss, preprocessing,
optimizer, hyperparameters, and absence of hidden scientific modifications.

The existing deterministic and Torch/PyG smoke trainers cannot identify as
GDN. Failure to establish fidelity returns
`blocked_upstream_gdn_backend_unresolved`; no substitute method is allowed.

The arm may use the P1 candidate-learning view on train1 and train2 only.
Seeds are exactly `11`, `23`, and `37`, with identical architecture and
hyperparameters. Outputs are projected onto the common 144-pair universe.

Ranking uses edge-selection frequency first, median upstream graph similarity
second, then source and target identity. Attention is supplementary graph
evidence and cannot be called causal importance. Post-hoc XAI is not a primary
C-GDN method.

Policy hash: `9c2387a98312ef6c96ddcd17a871ceb70a96b670eb4a39a7269878101f2ba41a`.
