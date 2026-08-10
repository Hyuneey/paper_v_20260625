# TASK-039C-GDNC Softmax Compatibility Correction

## Authority

TASK-039C-GDNC authorizes one final GDN attempt after exactly one
semantics-preserving dependency API correction. It descends from GDNR result
commit `6474816068aae786a490c634c28d665772bc2243` and reuses the exact verified
Python 3.12.13, torch 2.12.1, and torch-geometric 2.8.0 environment.

The correction is classified as
`documented_non_scientific_api_adapter`. No second code correction, package
change, seed retry, fallback backend, or hyperparameter change is authorized.

## Exact compatibility boundary

The pinned upstream GDN and the failed project port both used:

```python
softmax(alpha, edge_index_i, size_i)
```

Under the upstream PyG 1.5-era contract, the third argument represents
`num_nodes`. Under installed PyG 2.8.0, the signature is:

```text
(src, index=None, ptr=None, num_nodes=None, dim=0)
```

The integer node count therefore bound to `ptr` and failed before seed 11
completed. The only authorized correction is an explicit binding equivalent
to:

```python
softmax(src, index=index, num_nodes=num_nodes)
```

The pinned upstream checkout remains unchanged.

## Pre-data equivalence gate

Before any HAI reread, an independent numerically stable grouped-softmax
reference groups values by `index`, subtracts each group maximum, exponentiates,
and normalizes within that group. It never calls the compatibility wrapper.

The frozen cases cover two groups, repeated indices, unused node IDs,
one-element groups, positive and negative logits, large-magnitude logits, and
multidimensional graph-layer values. Float64 wrapper parity uses absolute and
relative tolerances `1e-12`; the float32 graph-layer parity uses `1e-6`.
These tolerances are fixed before execution and reflect dtype rounding only.

## Execution boundary

Only the P1 candidate-learning view from `hai-train1.csv` and
`hai-train2.csv` may be opened. Seeds 11, 23, and 37 run sequentially exactly
once. Any further runtime, compatibility, or training error terminates GDN for
the current thesis workflow with `failed_gdn_final_attempt` and
`PROCEED_WITH_META_STAT_INTEGRATION_GDN_UNAVAILABLE`.

TASK-039D remains unauthorized.
