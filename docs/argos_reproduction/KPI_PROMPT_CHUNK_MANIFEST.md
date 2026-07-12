# KPI Prompt Chunk Manifest

TASK-025 selects one deterministic KPI training chunk for ARGOS
`train-LLM-only` prompt capture. Raw rows and the full prompt are stored only
under ignored `artifacts/` paths.

## Frozen Inputs

| Field | Value |
|---|---|
| ARGOS commit | `6b24161ff08de069840a1fb4fbaecf7bf8e393f1` |
| Mode | `train-LLM-only` |
| Combined mode | deferred |
| KPI source commit | `d06bda15d511d930cbf4e6a6de14bd94d790f0f2` |
| Selected KPI ID | `05f10d3a-239c-3bef-9bdc-a2feeb0037aa` |
| Converted CSV SHA-256 | `f6a6d834e23417da5cd0e87af227ae62f0c12a73f080afa08b08a2d332aa5d55` |

## Selection Policy

The chunk selection follows a predeclared rule:

1. Use only the selected KPI series.
2. Use the converted ARGOS `value,label,index` CSV from TASK-024.
3. Resolve chunk size from pinned ARGOS defaults: `1000`.
4. Apply ARGOS one-by-one split behavior: `train_test_split=0.7`, then
   `val_split=0.2`, leaving the ARGOS train partition.
5. Scan chunks in increasing start-position order.
6. Require at least one normal and one anomaly label.
7. Select the first eligible chunk.
8. Do not use generated-rule performance or detector performance.

## Selected Chunk

| Field | Value |
|---|---|
| Start position | 0 |
| End position exclusive | 1000 |
| Start index | 0 |
| End index inclusive | 999 |
| Row count | 1000 |
| Label counts | `0`: 996, `1`: 4 |
| Chunk hash | `550f47a55f37a18337c097ae4033808ef591d75407581c2e9b3cf8da1ed42015` |
| Selection policy hash | `6e36b229e05834547771c81c9f6c763d58c8c2bda50752dac0440560bf8d3b3c` |

The complete private chunk artifact is:

```text
artifacts/private_argos_reproduction/task025/chunks/selected_chunk.json
```

The tracked JSON manifest is:

```text
docs/task_reports/TASK-025_PROMPT_CHUNK_MANIFEST.json
```

## Boundary

This is an ARGOS rule-only prompt-capture smoke. It is not a benchmark result
and must not be used as a thesis performance claim.
