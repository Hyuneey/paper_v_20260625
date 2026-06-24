# Implementation Notes

## TASK-000 conclusion

The six TASK-000 decisions are recorded as resolved in `docs/DECISIONS_REQUIRED.md`.

The current directory is a work-order pack plus local data and upstream references. It is not a functioning implementation repository yet.

## Proposed package boundaries

Use the module boundaries in `IMPLEMENTATION_PLAN.md`:

```text
src/<package>/
  data/
  metadata/
  candidates/
  gdn/
  profiling/
  dsl/
  planning/
  verification/
  runtime/
  evaluation/
```

Runtime code must not import planning or LLM provider modules.

## Recommended TASK-001 configuration

Start TASK-001 only after raw SWaT files are confirmed untracked by Git and `.gitignore` is verified in a valid repository.

Initial proposed config:

```yaml
dataset_name: SWaT
dataset_status: local_unverified_smoke_test
source_kind: unknown
local_root_env: SWAT_DATA_ROOT
canonical_rule_view:
  sampling_period_seconds: 1.0
  preprocessing: []
optional_gdn_view:
  enabled: false
split_policy:
  strategy: smoke_test_only_until_official_provenance
  split_before_windowing: true
  purge_gap_policy: window_size_minus_one_plus_max_lag
raw_data_committed: false_required
```

Do not treat `normal.csv` as official `train_normal` or `attack.csv` as official `test`. The current CSVs are smoke-test / feasibility inputs only; prefer `merged.csv` for schema inspection and preliminary timeline reconstruction.

## Suggested implementation sequence after decisions

1. Add root package/test/lint configuration.
2. Verify `.gitignore` blocks raw SWaT and derived time-series files before initializing or using a real repository.
3. Implement `DatasetManifest` and local file validator.
4. Implement split-role enums and permission guards.
5. Implement split-before-windowing tests using synthetic fixtures only.
6. Generate a local dataset manifest with hashes, but do not commit raw data.

## Upstream adaptation notes

- ARGOS: copy no modules. Recreate only provider-neutral planner/refiner interfaces after Phase Gate B.
- GDN: implement a minimal modern port. Add `C_i` masking before Top-K and exclude candidate self-edges from exported artifacts.

## Edits recommended for later tickets

No task text must be changed now. Later tickets should reference the decisions in `docs/DECISIONS_REQUIRED.md` once approved.
