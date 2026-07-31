# TASK-039P1A: Dataset-Neutral Data and Split Foundation

## Status

`passed_dataset_neutral_data_split_foundation`

## Scope

TASK-039P1A adds versioned, dataset-neutral contracts and compatibility
adapters without changing the existing v1 data classes or migrating any
consumer.

Implemented:

- `DatasetFileV2`, `DatasetManifestV2`, `DataViewManifestV2`, and
  `SplitManifestV2`;
- seven explicit v6 split roles and eleven fail-closed operations;
- split-before-windowing, maximum-lag-aware purge checks, and range-local
  windows;
- explicit, loss-reporting v1 adapters;
- four independent Draft 2020-12 v6 schemas and a separate v2 registry;
- synthetic contract, permission, adapter, schema, and import-boundary tests.

## Frozen Boundaries

- Existing v1 data contracts and behavior remain unchanged.
- CandidateUniverse, GDN, profiling, planners, verifier, runtime, and
  evaluation consumers are not migrated.
- Legacy `validation` and `test` roles receive no implicit v6 meaning.
- Adapters cannot grant sealed access or infer process scope.
- Dataset data, providers, Agents, detectors, rule runtimes, outer partitions,
  and sealed partitions are not accessed.

## Parent Sequence

TASK-039P1 remains incomplete and is decomposed into:

1. TASK-039P1A: data and split foundation;
2. TASK-039P1B: evidence and construction outcomes;
3. TASK-039P1C: canonical collection and verifier/runtime decoupling;
4. TASK-039P1D: GDN import and fidelity decision support.

## Claim Boundary

TASK-039P1A provides dataset-neutral contracts and split governance only. It
does not establish HAI readiness, process feasibility, rule construction,
detector performance, Agentic value, or thesis results.
