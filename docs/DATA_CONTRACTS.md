# Data Contracts Proposal

This is a design proposal for TASK-001. No production code is implemented in TASK-000.

## Core principles

1. Validate local files before use.
2. Record dataset provenance before split creation.
3. Split raw timelines before windowing.
4. Enforce split roles at API boundaries.
5. Keep canonical rule view separate from optional GDN view.
6. Never use final test data for training, calibration, rule construction, threshold selection, or verifier tuning.

## Proposed roles

| Role | Permitted use |
|---|---|
| `train_normal` | GDN or candidate learner training |
| `calibration_normal` | relation profiling and numeric calibration |
| `validation` | deterministic verification and refinement feedback |
| `test` | final evaluation only |

## Proposed schemas

```python
class SplitRole(str, Enum):
    TRAIN_NORMAL = "train_normal"
    CALIBRATION_NORMAL = "calibration_normal"
    VALIDATION = "validation"
    TEST = "test"

@dataclass(frozen=True)
class DatasetManifest:
    schema_version: str
    dataset_name: str
    source_kind: str
    source_reference: str
    dataset_edition: str
    normal_data_version: str
    terms_acknowledged: bool
    files: tuple[DatasetFile, ...]
    feature_count: int
    feature_names_hash: str
    timestamp_column: str
    timestamp_format: str
    label_column: str
    sampling_period_seconds: float

@dataclass(frozen=True)
class DataViewManifest:
    schema_version: str
    view_name: str
    dataset_manifest_id: str
    sampling_period_seconds: float
    preprocessing_config: Mapping[str, Any]
    source_file_ids: tuple[str, ...]

@dataclass(frozen=True)
class SplitManifest:
    schema_version: str
    dataset_manifest_id: str
    data_view_id: str
    role: SplitRole
    index_ranges: tuple[tuple[int, int], ...]
    permitted_use: tuple[str, ...]
    purge_gap: int
    random_seed: int | None
```

## Required guards

```python
def assert_split_permitted(role: SplitRole, operation: str) -> None: ...
```

Initial operation mapping:

- `train_candidate_learner`: `train_normal`
- `profile_relation`: `calibration_normal`
- `calibrate_rule_parameters`: `calibration_normal`
- `verify_rule`: `validation`
- `final_evaluate`: `test`

## Current dataset contract warning

The local `normal.csv` and `attack.csv` files appear to be label-filtered subsets of `merged.csv`. TASK-001 must not infer official split roles from file names alone.
