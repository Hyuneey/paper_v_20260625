# Dataset Manifest Draft

This draft records the current local CSV files as unverified smoke-test inputs. It is not an approved final SWaT provenance manifest.

```yaml
schema_version: "1.0"
artifact_type: "dataset_manifest"
dataset_name: "SWaT"
dataset_status: "local_unverified_smoke_test"
source_kind: "kaggle_mirror"
source_reference: "https://www.kaggle.com/datasets/vishala28/swat-dataset-secure-water-treatment-system"
source_description_status: "researcher_supplied_kaggle_notes"
notebook_version_sync: "will_not_continually_sync_with_new_notebook_versions"
dataset_edition: "unverified"
normal_data_version: "unverified"
terms_of_use_status: "unverified"
terms_acknowledged: false
local_root_env: "SWAT_DATA_ROOT"
raw_data_git_policy:
  commit_raw_files: false
  commit_extracted_windows: false
  commit_swat_derived_fixtures: false
  commit_raw_sequence_plots: false
  ignore_patterns:
    - "dataset/"
    - "data/raw/"
    - "data/swat/"
    - "*.csv"
    - "*.xlsx"
    - "*.parquet"
files:
  - logical_role: "local_smoke_normal_label_subset"
    relative_path: "normal.csv"
    bytes: 402374633
    rows_excluding_header: 1387098
    sha256: "efa3dfd271fd33402d04ff4323d92ba739758bb2d4b9c6e9cc205980891f111f"
    label_counts:
      Normal: 1387098
      Attack: 0
  - logical_role: "local_smoke_attack_label_subset"
    relative_path: "attack.csv"
    bytes: 15162438
    rows_excluding_header: 54621
    sha256: "81977a6206ba954781df5481481ef1c39e94a405980f4f45b98e9c0a9cedadd2"
    label_counts:
      Normal: 0
      Attack: 54621
  - logical_role: "local_smoke_merged_label_subset"
    relative_path: "merged.csv"
    bytes: 426855390
    rows_excluding_header: 1441719
    sha256: "5472928b8faf51430f4490628c6fe99487d58d5826a41460ab26aee69dde22a4"
    label_counts:
      Normal: 1387098
      Attack: 54621
schema:
  file_format: "csv"
  column_count: 53
  feature_count: 51
  timestamp_column: "Timestamp"
  timestamp_format_detected: "%d/%m/%Y %I:%M:%S %p"
  label_column: "Normal/Attack"
  label_encoding:
    normal: "Normal"
    attack: "Attack"
  sampling_period_seconds: 1.0
  feature_columns:
    - FIT101
    - LIT101
    - MV101
    - P101
    - P102
    - AIT201
    - AIT202
    - AIT203
    - FIT201
    - MV201
    - P201
    - P202
    - P203
    - P204
    - P205
    - P206
    - DPIT301
    - FIT301
    - LIT301
    - MV301
    - MV302
    - MV303
    - MV304
    - P301
    - P302
    - AIT401
    - AIT402
    - FIT401
    - LIT401
    - P401
    - P402
    - P403
    - P404
    - UV401
    - AIT501
    - AIT502
    - AIT503
    - AIT504
    - FIT501
    - FIT502
    - FIT503
    - FIT504
    - P501
    - P502
    - PIT501
    - PIT502
    - PIT503
    - FIT601
    - P601
    - P602
    - P603
canonical_rule_view:
  source_view: "canonical_rule_view"
  sampling_period_seconds: 1.0
  preprocessing: []
optional_gdn_view:
  enabled: false
notes:
  - "These files are smoke-test / feasibility inputs only."
  - "Claimed source is the Kaggle SWaT Dataset: Secure Water Treatment System page supplied by the researcher."
  - "Researcher-supplied notes state that the data was sourced directly from the SWaT industrial testbed operated by the contributing organization."
  - "Researcher-supplied notes state that data was collected continuously under normal operation and controlled cyber-attack scenarios."
  - "Researcher-supplied notes state that the Kaggle dataset will not continually sync with new notebook versions."
  - "Kaggle terms, file list, and exact edition still require manual/API verification."
  - "Do not treat normal.csv and attack.csv as official SWaT train/test files."
  - "Do not use current files for final evaluation claims."
  - "Prefer merged.csv only for schema inspection and preliminary timeline reconstruction."
```
