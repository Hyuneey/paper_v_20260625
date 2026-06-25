# GDN Masked Candidate Extraction

TASK-004 progress implements the project-specific masked edge extraction contract around the GDN embedding-similarity idea.

## Upstream Reference

Reference repository:

`https://github.com/d-ailin/GDN`

Pinned commit:

`9853899da860682669a134e4af315d036aab4eca`

Files inspected for this step:

- `external/gdn/models/GDN.py`
- `external/gdn/models/graph_layer.py`

No upstream code was copied. The implementation reuses the concepts of node embeddings, cosine similarity, and Top-K learned graph extraction.

## Key Upstream Difference

The upstream `GDN.py` computes cosine similarity over all node embeddings and applies `torch.topk` directly to the full similarity matrix.

This project requires:

1. compute embedding cosine similarity,
2. apply the `CandidateUniverse` mask before Top-K,
3. exclude candidate self-edges,
4. select at most K sources per target,
5. export only edges inside `C_i`,
6. keep message-passing self-loops separate from persisted candidate relations.

## Implemented Modules

- `paperworks.gdn.GDNExtractionConfig`
- `paperworks.gdn.EmbeddingCheckpoint`
- `paperworks.gdn.GDNEdgeRecord`
- `paperworks.gdn.GDNEdgeArtifact`
- `paperworks.gdn.cosine_similarity_matrix()`
- `paperworks.gdn.extract_masked_topk_edges()`
- `paperworks.gdn.message_passing_self_loops()`
- `paperworks.gdn.fit_deterministic_embedding_checkpoint()`
- `paperworks.gdn.TorchGDNTrainingConfig`
- `paperworks.gdn.TorchGDNEmbeddingModel`
- `paperworks.gdn.fit_torch_gdn_embedding_checkpoint()`

## Edge Artifact Contract

Each exported edge includes:

- `source`
- `target`
- `embedding_similarity`
- `rank`
- `K`
- `seed`
- `candidate_origins`
- `candidate_universe_id`
- `feature_order_hash`
- `source_view`
- `sampling_period_seconds`
- `checkpoint_id`

The artifact also records:

- dataset manifest ID,
- split name,
- feature order,
- Top-K config,
- run index,
- extraction config,
- message-passing self-loop count.

Self-loops are represented only by `message_passing_self_loops(feature_order)` and are not exported as candidate edges.

## Current Backend Status

DEC-010 resolved the first modern backend as CPU-only PyTorch/PyG:

- `torch 2.12.1+cpu`
- `torch_geometric 2.8.0`
- CUDA unavailable in the current environment

This step implements and tests both a deterministic embedding smoke backend and a CPU PyTorch/PyG synthetic trainer. Both paths validate split guards, checkpoint provenance, mask enforcement, Top-K export, and artifact schemas.

## CPU PyTorch/PyG Trainer

`fit_torch_gdn_embedding_checkpoint()` trains a small synthetic GDN-style graph forecaster:

- PyTorch `nn.Embedding` stores node embeddings.
- PyG `MessagePassing` performs mean neighbor aggregation over candidate edges plus internal self-loops.
- A small MLP predicts the next time step from current value, neighbor aggregate, and node embedding.
- Learned node embeddings are exported through `EmbeddingCheckpoint`.
- `extract_masked_topk_edges()` remains the only candidate-edge exporter.

The trainer is intentionally minimal. It validates the modern PyTorch/PyG environment, split guards, deterministic seeds, and embedding-to-mask export flow without adopting the legacy upstream environment.

## Test Coverage

`tests/test_gdn_masked_extraction.py` covers:

- candidate-mask enforcement,
- self-candidate exclusion,
- message-passing self-loop separation,
- K larger than candidate count,
- empty candidate set behavior,
- feature-order mismatch rejection,
- deterministic seed behavior,
- synthetic training smoke test,
- no-test-split guard,
- behavioral comparison against a small reference cosine calculation.

## Non-Goals In This Step

- No raw SWaT training run.
- No final GDN checkpoint from real data.
- No test-label threshold selection.
- No upstream `report=best`.
- No real SWaT training run.
