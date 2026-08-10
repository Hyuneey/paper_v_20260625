# TASK-039C-GDNP: PyG Port Compatibility Closure

Status is established by the task-owned compatibility and execution receipts.

This task reopens the upstream-aligned GDN port only to close demonstrated
PyG 1.5.0 to 2.8.0 API-semantic differences before any new HAI value access.
The exact Windows CPython 3.12.13 CPU environment remains frozen at
`torch==2.12.1`, `torch-geometric==2.8.0`, and the existing environment receipt.

The production compatibility boundary is limited to:

1. the already approved sparse-softmax keyword binding that preserves the old
   third-argument `num_nodes` meaning; and
2. explicit `MessagePassing(..., node_dim=0)` to preserve PyG 1.5 aggregation
   over the edge dimension.

No GDN equation, architecture, graph Top-K, preprocessing rule, optimizer,
hyperparameter, seed, data split, candidate universe, or ranking rule may
change. The pure-PyTorch GraphLayer implementation is reference-only and may
never serve as an execution backend or fallback.

HAI train1/train2 may be opened only from a clean compatibility-closed Commit A
after the API matrix has no unresolved rows and forward, backward, index,
GNNLayer, tiny-model, and tiny-training gates pass. Train3, train4, test,
labels, attacks, BR2 pair outcomes, META, and STAT remain prohibited.

Any real seed failure terminates the task without ranking. All three seeds
11, 23, and 37 must complete once, in order, under denominator three before a
candidate result can be serialized.
