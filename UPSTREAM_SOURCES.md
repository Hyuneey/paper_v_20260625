# Upstream Reference Repositories

## microsoft/ARGOS

- Repository: https://github.com/microsoft/ARGOS
- Role: architectural reference for training-time agentic rule generation
- License: MIT
- Pin: <TASK-000에서 확인한 commit SHA>

### Inspect

- runtime/engine.py
- agent/detection_agent.py
- agent/repair_agent.py
- agent/review_agent.py
- selector/

### Reuse conceptually

- Detection → Repair → Review workflow
- verifier feedback and rule refinement
- rule ranking/selection
- training-time LLM, runtime deterministic execution

### Do not reuse directly

- univariate value/label/index dataset contract
- arbitrary LLM-generated Python execution
- test-set evaluation during rule construction
- point-adjusted evaluation as the default
- Azure OpenAI-only provider coupling

---

## d-ailin/GDN

- Repository: https://github.com/d-ailin/GDN
- Role: reference implementation for relation candidate learning
- License: MIT
- Pin: <TASK-000에서 확인한 commit SHA>

### Inspect

- models/GDN.py
- models/graph_layer.py
- datasets/TimeDataset.py
- scripts/process_swat.py
- main.py

### Reuse conceptually

- sensor ID embeddings
- embedding cosine similarity
- Top-K learned graph
- graph-attention forecasting

### Must modify

- modern PyTorch/PyG port
- apply CandidateUniverse C_i mask before Top-K
- exclude self-edges from persisted candidate relations
- separate message-passing self-loops from relation artifacts
- export stable candidate-edge artifacts

### Do not reuse directly

- legacy Python/PyTorch/PyG environment
- report=best or test-label threshold selection
- original temporal split logic
- preprocessing/downsampling without explicit approval
