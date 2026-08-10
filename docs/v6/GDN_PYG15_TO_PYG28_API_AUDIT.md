# GDN PyG 1.5.0 to 2.8.0 API Audit

The machine-readable authority is
`TASK-039C_GDNP_API_DRIFT_MATRIX.json`. It binds immutable Git blobs from the
pinned upstream GDN commit, official PyG tags 1.5.0 and 2.8.0, and the exact
installed PyG 2.8.0 wheel sources.

The audit confirms two compatibility bindings:

- PyG 1.5 `softmax(src, index, num_nodes)` became PyG 2.8
  `softmax(src, index=None, ptr=None, num_nodes=None, dim=0)`. The existing
  keyword adapter preserves `index` and `num_nodes`.
- PyG 1.5 `MessagePassing` defaulted `node_dim=0`; PyG 2.8 defaults to `-2`.
  Upstream GDN emits messages shaped `[edge_count, heads, channels]`, so
  aggregation must remain on dimension zero. The project port now binds that
  dimension explicitly.

Flow remains source-to-target: `edge_index_j` is the source,
`edge_index_i` is the destination, `size_i`/`dim_size` is the destination-node
count, and addition aggregates one message per destination index. Removal and
re-addition of self-loops, head handling, bias, embedding arguments, and the
non-ranking attention path retain their executed semantics.

PyG 2.8 GATConv's own explicit `node_dim=0` is supporting API evidence only;
the custom embedding-conditioned upstream GraphLayer is not replaced.
