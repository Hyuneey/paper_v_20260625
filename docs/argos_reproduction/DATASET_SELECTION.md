# ARGOS Reproduction Dataset Selection

TASK-023 recommends one initial public dataset/subset for a future ARGOS reproduction stage. It does not download the dataset, run a benchmark, or approve final performance claims.

## Upstream Dataset Support

ARGOS README states that supported datasets are KPI and Yahoo and that input
CSV files are expected to follow the univariate `value,label,index` contract.
The current pinned ARGOS checkout references a preprocessing script path
`argos/utility/generate_csv.py`, but that `utility` directory is not present in
the pinned checkout inspected by TASK-023.

## Dataset Options

| Dataset | Public availability | Terms clarity | Upstream support | Smoke cost | Paper similarity | Decision |
|---|---|---|---|---|---|---|
| KPI | Public GitHub repository `NetManAIOps/KPI-Anomaly-Detection`; repository page reports MIT license. | Clearer than Yahoo for first reproduction because license is visible in repository metadata and LICENSE file. | ARGOS README names KPI as supported. | Finals ZIP artifacts are about 16 MB each before extraction; future one-series subset can be small. | Used in ARGOS paper. | Selected for first public reproduction subset. |
| Yahoo S5 | Publicly known benchmark, but ARGOS README points to Yahoo Webscope. | Requires Webscope access/terms review before use. | ARGOS README names Yahoo as supported. | Potentially small, but access route is less direct. | Used in ARGOS paper. | Deferred. |

## Selected Initial Dataset/Subsetting Decision

Selected dataset/subset:

```yaml
decision_id: DEC-027-DATASET-SUBDECISION
dataset: KPI
source_repository: https://github.com/NetManAIOps/KPI-Anomaly-Detection
source_kind: public_github_dataset
license_observed: MIT
initial_package:
  train_path: Finals_dataset/phase2_train.csv.zip
  train_git_blob_sha: f07375e9ec10789d9f473301734c9cb00e9b6279
  train_size_bytes: 16293543
  ground_truth_path: Finals_dataset/phase2_ground_truth.hdf.zip
  ground_truth_git_blob_sha: 41397b55ae955849357eb7006334f2c11a32bca6
  ground_truth_size_bytes: 16254356
initial_subset_policy: one-by-one single KPI series extracted after future approved download
download_status: not_downloaded_in_TASK_023
hash_status: github_blob_sha_recorded_only; local_sha256_required_after_download
```

Why this is the first target:

- It is public and used by the ARGOS paper.
- The repository exposes license metadata as MIT.
- ARGOS README explicitly lists KPI as supported.
- The future reproduction can choose one KPI series after approved download and
  convert it to the ARGOS `value,label,index` contract.

Limitations:

- TASK-023 did not download or inspect file contents.
- Exact KPI series ID, row count, local SHA-256, and converted
  `value,label,index` CSV hash must be recorded in a future approved dataset
  preparation task.
- This decision is for ARGOS reproduction only and does not affect SWaT
  DEC-007.

## Required Future Manifest Fields

Before a real ARGOS reproduction run, record:

- source URL;
- repository commit or release reference;
- Git blob SHA and local SHA-256 for downloaded packages;
- extracted file names;
- selected KPI ID or series ID;
- converted ARGOS CSV path;
- converted CSV SHA-256;
- row count;
- label schema;
- train/validation/test split policy;
- preprocessing script version;
- terms/license acknowledgement.
