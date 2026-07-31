# V6 GDN Fidelity Audit

## Conclusion

The current project does not contain a source-faithful production GDN
backend. `paperworks.gdn.masked` is a reusable project-owned extraction
component. Both embedding trainers are synthetic smoke infrastructure.

| Dimension | Pinned upstream GDN | Current Torch/PyG smoke backend |
|---|---|---|
| Input shape | Sliding window per node, batch x node x window | Adjacent scalar rows, batch x node |
| Training target | Next value per node | Next scalar row per node |
| Node embeddings | Cosine graph, attention conditioning, output gating | Decoder input and exported checkpoint |
| Learned graph | Dynamic cosine Top-K each forward pass | Fixed CandidateUniverse graph |
| Candidate mask | Absent | CandidateUniverse constrains graph; masked extraction applies mask before Top-K |
| Graph layer | Custom additive attention | Mean aggregation |
| Embedding-conditioned attention | Present | Absent |
| Self-loop handling | Remove then add in GraphLayer | Explicit message-passing loops appended |
| Output gating | GNN output multiplied by embedding | Value, neighbor mean, and embedding concatenated |
| Batch normalization/dropout | Multiple BN layers and dropout 0.2 | Absent |
| Objective | Mean squared next-value error | Mean squared next-row error |
| Checkpoint selection | Validation-loss early stop and saved state | Fixed epochs and final embedding export |
| Split/window policy | TimeDataset creates windows and mode-dependent stride | Caller rows plus legacy train-normal guard |

Shared terms such as embeddings, MSE, and message passing do not establish
equivalence. The missing dynamic graph, custom attention, and output stack are
material scientific differences.

## Frozen Classifications

| Component | Classification | Scientific GDN claim | Production ranking |
|---|---|---:|---:|
| `fit_deterministic_embedding_checkpoint` | `synthetic_smoke_only` | No | No |
| `TorchGDNEmbeddingModel` and trainer | `synthetic_smoke_only` | No | No |
| `paperworks.gdn.masked` | `project_owned_extraction_component` | No complete-model claim | No by itself |

The masked extractor intentionally applies the approved mask before Top-K,
excludes persisted self-edges, separates message-passing loops, and adds
project provenance. Those are v6 controls, not recovered upstream behavior.

No real data was accessed and no model was trained for this audit.
