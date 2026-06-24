---
id: TASK-001
title: Implement local-only dataset manifests, data views, and leakage-safe splits
status: blocked
depends_on: [TASK-000]
phase_gate: Milestone 1
suggested_branch: task-001-data-contracts
---

# TASK-001: Dataset Manifests, Views, and Leakage-Safe Splits

## 1. Goal

Implement typed local-data contracts, exact SWaT provenance manifests, canonical/optional data views, and deterministic split manifests that enforce permitted use and split-before-windowing.

## 2. Architecture context

Every later module depends on this task. Response-delay rules require high-resolution data, while GDN may use a separate downsampled view. These views must be traceable and must not leak overlapping windows across splits.

## 3. Preconditions

- TASK-000 approved.
- `SWAT_DATA_ROOT` is available locally.
- Dataset edition/version status is documented.
- Canonical rule-view policy is approved or explicitly recorded as an open decision.

## 4. Inputs

- local SWaT files,
- approved dataset-provenance record,
- approved preprocessing config,
- split policy,
- purge-gap policy.

## 5. Required outputs

- `DatasetManifest` schema,
- local-file validator using `SWAT_DATA_ROOT`,
- canonical rule-view contract,
- optional GDN-view contract,
- `SplitManifest` schema,
- deterministic raw-timeline split generator,
- purge-gap window generator,
- split-use guard,
- synthetic test fixtures,
- updated `docs/DATA_CONTRACTS.md` and `docs/DATASET_PROVENANCE.md`.

## 6. Required interfaces

```python
class SplitRole(str, Enum):
    TRAIN_NORMAL = "train_normal"
    CALIBRATION_NORMAL = "calibration_normal"
    VALIDATION = "validation"
    TEST = "test"

class DataViewName(str, Enum):
    CANONICAL_RULE = "canonical_rule"
    GDN = "gdn"

@dataclass(frozen=True)
class DatasetManifest:
    dataset_name: str
    source_kind: str
    source_reference: str
    dataset_edition: str
    normal_data_version: str
    file_fingerprints: Mapping[str, str]
    feature_count: int
    feature_names_hash: str
    timestamp_column: str
    sampling_period_seconds: float
    label_column: str
    label_encoding: Mapping[str, str | int]
    schema_version: str

@dataclass(frozen=True)
class DataViewManifest:
    name: DataViewName
    sampling_period_seconds: float
    preprocessing_config: Mapping[str, Any]
    upstream_dataset_manifest_id: str
    fingerprint: str

@dataclass(frozen=True)
class SplitManifest:
    dataset_manifest_id: str
    data_view_id: str
    role: SplitRole
    raw_index_ranges: tuple[tuple[int, int], ...]
    purge_gap_samples: int
    seed: int | None
    schema_version: str


def assert_split_permitted(role: SplitRole, operation: str) -> None: ...
```

## 7. Core rules

1. Access raw files through local configuration; do not copy them into the repository.
2. Split raw timelines before creating windows.
3. Generate windows independently within each split.
4. Apply a purge gap of at least `window_size - 1`; include maximum lag when configured.
5. Fit scalers only on approved normal training data.
6. The canonical rule view must preserve the approved high-resolution timing.
7. The GDN view, if created, must record downsampling and label aggregation explicitly.
8. Do not infer dataset edition/version silently.

## 8. In scope

- CSV/XLSX schema adapters approved in TASK-000,
- label normalization,
- timestamp validation,
- fingerprinting,
- view construction,
- manifest serialization,
- leakage guards,
- synthetic fixtures.

## 9. Out of scope

- GDN training,
- relation profiling,
- candidate metadata inference,
- test-based tuning,
- automatic Kaggle or iTrust download.

## 10. Data governance

- No real SWaT rows/windows in Git-tracked tests.
- Committed manifests use relative logical names, never absolute local paths.
- Logs must not print raw sequences.
- CI uses synthetic data.

## 11. Acceptance criteria

1. Same files/config/seed produce semantically identical manifests.
2. File hash changes are detected.
3. `test` is rejected by training, profiling, calibration, and refinement APIs.
4. Raw ranges do not overlap across splits.
5. Generated windows cannot cross split or purge boundaries.
6. Every view records sampling period and preprocessing.
7. Canonical and GDN views can be traced to the same dataset manifest.
8. No raw SWaT data appears in Git status.

## 12. Required tests

- manifest round trip,
- hash-change detection,
- unknown edition handling,
- irregular timestamp rejection or explicit policy,
- raw-range overlap rejection,
- split-before-window leakage test,
- purge-gap test,
- split-role negative tests,
- view sampling/aggregation provenance test,
- synthetic-only CI test.

## 13. Stop conditions

Stop if:

- source files cannot be fingerprinted,
- sampling interval is ambiguous and profiling depends on it,
- split policy is not approved,
- implementing the loader would require committing data.
