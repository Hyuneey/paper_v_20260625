# GDN GraphLayer Mathematical Parity

The test-only reference in
`paperworks.gdn.pure_torch_graph_layer_reference_v1` uses core PyTorch only.
It does not import PyG MessagePassing, PyG aggregation, PyG softmax, PyG
scatter, or the project GraphLayer.

For deterministic float64 and float32 fixtures, the reference independently:

1. projects node inputs;
2. removes existing self-loops and appends one loop per node;
3. gathers source/destination projected features and embeddings;
4. evaluates the upstream attention equations and LeakyReLU;
5. performs stable destination-grouped softmax;
6. forms `x_j * alpha` messages;
7. aggregates with `index_add_(dim=0, index=destination)`;
8. applies head concat/mean and bias.

The gates compare processed edges, indices, logits, coefficients, messages,
aggregates, outputs, gradients, and one Adam update. The complete
GraphLayer→BatchNorm1d→ReLU path is checked in evaluation and training mode.
A six-node complete GDN then passes forward, backward, optimizer-step,
same-seed replay, and learned-graph checks. A separate synthetic training loop
exercises multiple training batches, validation, best-state capture/reload,
graph extraction, and 144-pair projection.

Tolerances are fixed before real execution: float64 absolute/relative
`1e-12`; float32 absolute/relative `1e-6`.
