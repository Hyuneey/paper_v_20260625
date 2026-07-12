# KPI Dataset Manifest for ARGOS Rule-Only Smoke

TASK-024 prepares one public KPI series for the first ARGOS rule-only
reproduction smoke. It does not run a real ARGOS benchmark, does not call a real
LLM provider, and does not approve benchmark or thesis claims.

## Source

| Field | Value |
|---|---|
| Repository | `https://github.com/NetManAIOps/KPI-Anomaly-Detection` |
| Source commit | `d06bda15d511d930cbf4e6a6de14bd94d790f0f2` |
| Commit date | `2022-08-08T06:48:01Z` |
| Train package | `Finals_dataset/phase2_train.csv.zip` |
| Ground-truth package | `Finals_dataset/phase2_ground_truth.hdf.zip` |

Downloaded packages, extracted files, and converted CSVs are stored only under
ignored `artifacts/private_argos_reproduction/task024/` paths.

## Package Records

| Package | Git blob SHA | Local SHA-256 | Bytes |
|---|---|---|---:|
| `phase2_train.csv.zip` | `f07375e9ec10789d9f473301734c9cb00e9b6279` | `5611dec5c912353427ac28f6c6481126a485b1229d0ca9692dc3462aa9116081` | 16293543 |
| `phase2_ground_truth.hdf.zip` | `41397b55ae955849357eb7006334f2c11a32bca6` | `308b0e58555ccdc71d852aa53d15be8f24d415fef599136763e3df3849e29bd2` | 16254356 |

Extracted files:

- `phase2_train.csv`: SHA-256 `4807dc9f1f6df31e0688b47734e52b6249ef7680840837a99800bfec6393331d`, 176109012 bytes.
- `phase2_ground_truth.hdf`: SHA-256 `13a16d8bccf6ae47ee8787c2164eccba3986fcefe72abfe3733996018ba7a284`, 100308352 bytes.

## Selection Audit

Selection policy:

- require valid train records;
- require the ground-truth package to be present;
- reject malformed timestamps, values, or labels;
- require at least 100 rows;
- require both normal and anomaly labels in the selected KPI series;
- choose the lexicographically smallest eligible KPI ID;
- do not select based on ARGOS performance.

Result:

| Field | Value |
|---|---|
| Available KPI IDs | 29 |
| Eligible KPI IDs | 29 |
| Selected KPI ID | `05f10d3a-239c-3bef-9bdc-a2feeb0037aa` |
| Selected row count | 146255 |
| Selected label counts | `0`: 144970, `1`: 1285 |
| Malformed timestamp count | 0 |
| Malformed value count | 0 |
| Malformed label count | 0 |

## ARGOS Conversion

Converted schema:

```text
value,label,index
```

The `index` field is zero-based source row order within the selected KPI ID.
The source timestamp is validated but is not copied into the ARGOS CSV.

| Field | Value |
|---|---|
| Converted private path | `artifacts/private_argos_reproduction/task024/converted/05f10d3a-239c-3bef-9bdc-a2feeb0037aa_argos.csv` |
| Converted SHA-256 | `f6a6d834e23417da5cd0e87af227ae62f0c12a73f080afa08b08a2d332aa5d55` |
| Converted rows | 146255 |
| Preprocessing version | `task024_minimal_kpi_to_argos_v1` |

The tracked JSON manifest is
`docs/task_reports/TASK-024_KPI_DATASET_MANIFEST.json`.

## Limitations

- The pinned ARGOS checkout references `utility/generate_csv.py`, but TASK-024
  did not find that script in the inspected ARGOS history.
- A minimal adapter under `experiments/argos_reproduction/` is used instead.
- The HDF ground-truth package is downloaded, hashed, and extracted, but not
  parsed in this smoke. Labels for this first rule-only plumbing smoke come
  from the `phase2_train.csv` label column.
- This preparation is not a benchmark result.
