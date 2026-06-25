# TASK-004 Progress Report

## Summary

Implemented the mask-enforced GDN candidate-edge extraction core. The new module computes embedding cosine similarity, applies the `CandidateUniverse` mask before Top-K, rejects persisted self-edges, and exports provenance-rich GDN candidate-edge artifacts.

TASK-004 is not fully closed yet. DEC-010 has been resolved by installing CPU-only PyTorch/PyG, so the remaining work is the real modern PyTorch/PyG GDN training backend.

## Changed files

- `src/paperworks/__init__.py`
- `src/paperworks/gdn/__init__.py`
- `src/paperworks/gdn/masked.py`
- `configs/gdn/masked_extraction_smoke.json`
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

Changed:

- Root package export now includes `gdn`.

## Design decisions and rationale

- Reimplemented GDN-style embedding cosine and Top-K extraction without copying upstream code.
- Applied `CandidateUniverse` mask before Top-K selection.
- Preserved candidate direction as source-to-target.
- Rejected self-edges from persisted candidate artifacts.
- Kept message-passing self-loops separate via `message_passing_self_loops()`.
- Added deterministic embedding smoke checkpoint support to test provenance and masking without unavailable ML dependencies.
- Recorded and then resolved DEC-010 with a CPU-only PyTorch/PyG environment.

## Commands run

```powershell
$env:PYTHONPATH="C:\Users\hyun\Desktop\paperworks\260625\src"
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_gdn_masked_extraction -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q src tests
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m json.tool configs\gdn\masked_extraction_smoke.json
git ls-files dataset external
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install torch --index-url https://download.pytorch.org/whl/cpu
& "C:\Users\hyun\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install torch_geometric
```

## Test, lint, and type-check results

Unit tests:

```text
Ran 41 tests
OK
```

GDN-specific tests:

```text
Ran 10 tests
OK
```

`compileall` passed. JSON validation passed for the GDN smoke config. Dedicated lint/type-check commands are not configured yet.

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
- `docs/GDN_MASKED_EXTRACTION.md`
- `docs/task_reports/TASK-004_REPORT.md`

No raw SWaT rows, real GDN checkpoints, or real-data candidate edge artifacts were produced.

## Research-invariant checks

- No test split is accepted for smoke checkpoint fitting or edge extraction.
- Every exported edge must be inside `C_i`.
- Persisted candidate self-edges are rejected.
- Message-passing self-loops are not exported as candidate relations.
- No test labels, threshold selection, or upstream `report=best` behavior is used.
- No causal interpretation is assigned to GDN edges.
- No upstream code was copied.

## Known limitations

- The deterministic smoke backend is not a replacement for trained GDN.
- No real SWaT GDN-view preprocessing or training was run.
- No model checkpoint from a neural GDN trainer was produced.

## Unresolved decisions / recommended next task

Open decisions:

- DEC-008: Candidate feasibility gate criteria before TASK-005.
- DEC-009: Real-data candidate policy for statistical and fallback origins.

Recommended next action:

- Complete the real CPU PyTorch/PyG GDN training backend for TASK-004.
