# Upstream Sources

## microsoft/ARGOS

- Repository: https://github.com/microsoft/ARGOS
- Local reference path: `external/argos`
- Pinned commit: `6b24161ff08de069840a1fb4fbaecf7bf8e393f1`
- Commit summary: `6b24161 Add rule mutation implementation, parallel training, and OpenEvolve baseline (#13)`
- License: MIT
- Code copied or adapted: none in TASK-000

### Files inspected

- `pyproject.toml`
- `requirements.txt`
- `LICENSE`
- `README.md`
- `datasets/dataset.py`
- `runtime/engine.py`
- `runtime/server.py`
- `agent/detection_agent.py`
- `agent/repair_agent.py`
- `agent/review_agent.py`
- `agent/mutate_agent.py`
- `agent/prompts/detection.py`
- `agent/prompts/repair.py`
- `agent/prompts/review.py`
- `selector/train_perf_selector.py`
- `eval_metrics/point_f1.py`
- `eval_metrics/point_f1pa.py`
- `eval_metrics/event_f1pa.py`
- `driver.py`

### Concepts to reuse

- Training-time planner/repair/review loop.
- Verifier feedback as a structured refinement signal.
- Rule ranking/selection as a separate stage.
- Distinction between generated candidate rules and runtime rule execution.

### Code or behavior not to reuse

- Univariate `value,label,index` dataset contract.
- LLM-generated Python as the rule artifact.
- `exec`-based or dynamically loaded rule execution.
- Test-set evaluation during rule construction or repair.
- Point-adjusted F1 as the default evaluation metric.
- Azure/OpenAI-specific coupling in core logic.

### Findings

ARGOS is useful as an architectural reference, but it directly conflicts with this project's safety and split policies. This project must parse LLM output as JSON DSL, then evaluate only through deterministic DSL/runtime code.

## d-ailin/GDN

- Repository: https://github.com/d-ailin/GDN
- Local reference path: `external/gdn`
- Pinned commit: `9853899da860682669a134e4af315d036aab4eca`
- Commit summary: `9853899 add some process scripts and readme`
- License: MIT
- Code copied or adapted: none in TASK-000

### Files inspected

- `README.md`
- `install.sh`
- `LICENSE`
- `main.py`
- `train.py`
- `test.py`
- `evaluate.py`
- `models/GDN.py`
- `models/graph_layer.py`
- `datasets/TimeDataset.py`
- `scripts/process_swat.py`
- `util/preprocess.py`
- `util/net_struct.py`
- `util/data.py`
- `util/iostream.py`

### Concepts to reuse

- Sensor/node ID embeddings.
- Cosine similarity over learned embeddings.
- Top-K learned graph as a relation-candidate source.
- Graph-attention forecasting architecture.

### Required adaptations

- Port to modern supported PyTorch/PyG.
- Apply `CandidateUniverse C_i` mask before Top-K.
- Exclude self-edges from persisted candidate-relation artifacts.
- Keep message-passing self-loops separate from exported candidate relations.
- Export stable candidate-edge artifacts with source, target, rank, score, K, seed, feature order, source view, and provenance.

### Code or behavior not to reuse

- Legacy Python/PyTorch/PyG dependency stack as the main environment.
- `report=best` or any test-label threshold selection.
- Original temporal split/windowing behavior without split-before-windowing review.
- Original SWaT preprocessing/downsampling without explicit approval.

### Findings

GDN's `models/GDN.py` computes cosine similarity over all node embeddings and calls `torch.topk` over the full similarity matrix. It does not apply this project's per-target candidate mask before Top-K. `models/graph_layer.py` removes and then adds self-loops for message passing, so candidate relation export must explicitly distinguish relation artifacts from internal self-loops.

### TASK-004 adaptation notes

- Code copied: none.
- Code adapted: none.
- Conceptually reimplemented:
  - node-embedding cosine similarity,
  - Top-K graph extraction,
  - self-loop separation for message passing.
- Project-specific changes:
  - `CandidateUniverse` mask is applied before Top-K,
  - persisted candidate self-edges are rejected,
  - candidate edges include `candidate_universe_id`, `feature_order_hash`, `checkpoint_id`, source view, sampling period, K, seed, rank, and candidate origins.
- TASK-004 implementation:
  - added a project-owned CPU PyTorch/PyG synthetic trainer in `src/paperworks/gdn/torch_backend.py`,
  - uses PyG `MessagePassing` for mean neighbor aggregation,
  - keeps learned embedding export and masked candidate-edge export under project-owned schemas,
  - does not copy upstream modules.
