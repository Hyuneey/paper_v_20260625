# GDN PyG Softmax Compatibility Audit

## Three-way audit

- Pinned upstream GDN at `9853899da860682669a134e4af315d036aab4eca`,
  `models/graph_layer.py`: `softmax(alpha, edge_index_i, size_i)`.
- Frozen project port before GDNC:
  `softmax(alpha, edge_index_i, size_i)`.
- Installed torch-geometric 2.8.0:
  `(src, index=None, ptr=None, num_nodes=None, dim=0)`.

The upstream call's third argument had PyG 1.5-era `num_nodes` meaning. In
PyG 2.8, the third positional argument is `ptr`. Passing the integer process
size in that position caused `AttributeError: 'int' object has no attribute
'dim'` before the first seed completed.

## Corrected binding

The project-owned port now calls a narrow wrapper:

```python
def upstream_sparse_softmax_compat_v1(src, index, num_nodes):
    return torch_geometric.utils.softmax(
        src,
        index=index,
        num_nodes=num_nodes,
    )
```

This changes only dependency API binding. `src`, grouping `index`, node count,
normalization dimension, graph edges, attention logits, and downstream
coefficients retain their upstream mathematical roles. The upstream checkout,
model equations, architecture, learned Top-K graph, prediction loss,
preprocessing, optimizer, hyperparameters, seeds, and ranking are unchanged.

## Evidence and claim boundary

Synthetic parity is evaluated against an independent grouped-softmax reference,
not against the broken PyG 2.8 positional call. No HAI candidate result existed
when the correction and tolerances were frozen. META, STAT, and BR2 pair-level
results were not consulted.

The compatibility receipt binds the original fidelity receipt, the failed GDNR
execution receipt, the exact environment receipt, and the corrected source
hash. Its classification is `documented_non_scientific_api_adapter`.
