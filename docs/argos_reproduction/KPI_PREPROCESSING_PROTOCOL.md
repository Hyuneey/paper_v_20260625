# KPI Preprocessing Protocol

TASK-024 defines a minimal, auditable KPI-to-ARGOS adapter for the first
rule-only reproduction smoke. It does not add preprocessing code to
`src/paperworks`.

## Upstream Script Check

The pinned ARGOS README references `utility/generate_csv.py`. TASK-024 inspected
ARGOS history for that path and related `utility`, `util`, and `scripts`
preprocessing paths. No compatible historical `generate_csv.py` script was
confirmed.

Decision:

```yaml
upstream_generate_csv_status: not_confirmed
adapter_location: experiments/argos_reproduction/kpi_prepare.py
adapter_scope: minimal_public_kpi_to_argos_schema
production_src_paperworks_change: false
```

## Adapter Contract

Input:

- `phase2_train.csv.zip`;
- `phase2_ground_truth.hdf.zip`, presence and hash only for TASK-024;
- config file `configs/argos_reproduction/task024_kpi_sandbox_smoke.json`.

Output:

- private converted CSV under ignored `artifacts/`;
- tracked aggregate manifest at
  `docs/task_reports/TASK-024_KPI_DATASET_MANIFEST.json`.

Tracked outputs must contain hashes, counts, selected KPI ID, schema, and
preprocessing policy only. They must not contain raw rows or converted CSV
content.

## Deterministic Series Selection

The adapter selects exactly one KPI series by a predeclared rule:

1. Parse train CSV columns `timestamp`, `value`, `label`, and `KPI ID`.
2. Validate timestamps, numeric values, and binary labels.
3. Keep KPI IDs with at least the configured minimum row count.
4. Keep KPI IDs with both normal and anomaly labels.
5. Sort eligible KPI IDs lexicographically.
6. Select the first eligible ID.

The selected KPI ID is not chosen using ARGOS rule performance, detector
performance, or benchmark metrics.

## Conversion

For the selected KPI ID, write only:

```text
value,label,index
```

`index` is the zero-based row order within that KPI ID after filtering. The
original timestamp is used only for validation and is not persisted in the
ARGOS CSV.

## Boundary

This adapter exists for ARGOS reproduction preparation only. It must not be
used as evidence of benchmark performance and must not alter the proposed
`paperworks` method implementation under `src/paperworks`.
