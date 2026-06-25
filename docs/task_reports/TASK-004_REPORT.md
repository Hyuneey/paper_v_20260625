# TASK-004 Completion Report

## Summary

Implemented the modern CPU PyTorch/PyG synthetic GDN path and the mask-enforced GDN candidate-edge extraction core. The module trains a small graph forecaster on approved normal-only synthetic sequences, exports learned node embeddings, applies the `CandidateUniverse` mask before Top-K, rejects persisted self-edges, and produces provenance-rich candidate-edge artifacts.

## Changed files

- `src/paperworks/__init__.py`
- `src/paperworks/gdn/__init__.py`
- `src/paperworks/gdn/masked.py`
- `src/paperworks/gdn/torch_backend.py`
- `configs/gdn/masked_extraction_smoke.json`
- `configs/gdn/torch_training_smoke.json`
- `tests/test_gdn_masked_extraction.py`
- `docs/GDN_MASKED_EXTRACTION.md`
- `docs/UPSTREAM_SOURCES.md`
- `docs/DECISIONS_REQUIRED.md`
- `docs/task_reports/TASK-004_REPORT.md`

## Interfaces added or changed

Added:

- `GDNExtractionConfig`
- `EmbeddingCheckpoint`
- `GDNEdgeRecord`
- `GDNEdgeArtifact`
- `GDNExtractionError`
- `cosine_similarity_matrix()`
- `extract_masked_topk_edges()`
- `message_passing_self_loops()`
- `fit_deterministic_embedding_checkpoint()`
- `TorchGDNTrainingConfig`
- `TorchGDNEmbeddingModel`
- `fit_torch_gdn_embedding_checkpoint()`

Changed:

- Root package export now includes `gdn`.

## Design decisions and rationale

- Reimplemented GDN-style embedding cosine and Top-K extraction without copying upstream code.
- Applied `CandidateUniverse` mask before Top-K selection.
- Preserved candidate direction as source-to-target.
- Rejected self-edges from persisted candidate artifacts.
- Kept message-passing self-loops separate via `message_passing_self_loops()`.
- Added deterministic embedding smoke checkpoint support to test provenance and masking.
- Added CPU PyTorch/PyG synthetic trainer using `MessagePassing`, node embeddings, and a small next-step forecaster.
- Recorded and then resolved DEC-010 with a CPU-only PyTorch/PyG environment.

## Commands run

```powershell
$env:PYTHONPATH="C:\Users\hyun\Desktop\paperworks\260625\src"
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_gdn_masked_extraction -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q src tests
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m json.tool configs\gdn\masked_extraction_smoke.json
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m json.tool configs\gdn\torch_training_smoke.json
git ls-files dataset external
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install torch --index-url https://download.pytorch.org/whl/cpu
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install torch_geometric
```

## Test, lint, and type-check results

Unit tests:

```text
Ran 44 tests
OK
```

GDN-specific tests:

```text
Ran 13 tests
OK
```

`compileall` passed. JSON validation passed for the GDN smoke and torch training configs. Dedicated lint/type-check commands are not configured yet.

Dependency check after installation:

```text
torch 2.12.1+cpu
torch cuda available False
torch cuda version None
torch_geometric 2.8.0
MessagePassing MessagePassing
```

## Artifacts produced

- `configs/gdn/masked_extraction_smoke.json`
- `configs/gdn/torch_training_smoke.json`
- `docs/GDN_MASKED_EXTRACTION.md`
- `docs/task_reports/TASK-004_REPORT.md`

No raw SWaT rows or real-data candidate edge artifacts were produced. Checkpoints are synthetic in-memory `EmbeddingCheckpoint` artifacts in tests.

## Research-invariant checks

- No test split is accepted for smoke checkpoint fitting or edge extraction.
- PyTorch/PyG training path accepts only `train_normal`.
- Every exported edge must be inside `C_i`.
- Persisted candidate self-edges are rejected.
- Message-passing self-loops are not exported as candidate relations.
- No test labels, threshold selection, or upstream `report=best` behavior is used.
- No causal interpretation is assigned to GDN edges.
- No upstream code was copied.

## Known limitations

- The synthetic CPU trainer is a minimal modern-port smoke path, not a full reproduction of upstream GDN performance.
- No real SWaT GDN-view preprocessing or training was run.
- No persisted real-data model checkpoint was produced.

## Unresolved decisions / recommended next task

Open decisions:

- DEC-008: Candidate feasibility gate criteria before TASK-005.
- DEC-009: Real-data candidate policy for statistical and fallback origins.

Recommended next action:

- TASK-005: Candidate feasibility smoke/gate report, after resolving DEC-008 and deciding whether DEC-009 should stay metadata-only for the first smoke run.
