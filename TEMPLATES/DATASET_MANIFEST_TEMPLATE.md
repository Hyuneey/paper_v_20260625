# SWaT Dataset Manifest Template

```yaml
schema_version: "1.0"
dataset_name: "SWaT"
source_kind: "official_itrust | kaggle_mirror | other"
source_reference: "<URL or request reference>"
dataset_edition: "<e.g. A1 Dec 2015 or unverified>"
normal_data_version: "<v0, v1, or unverified>"
terms_acknowledged: true
terms_acknowledged_at: "<ISO-8601>"
local_root_env: "SWAT_DATA_ROOT"
files:
  - logical_role: "normal"
    relative_path: "<local relative path>"
    sha256: "<hash>"
  - logical_role: "attack"
    relative_path: "<local relative path>"
    sha256: "<hash>"
feature_count: 51
feature_names_hash: "<hash>"
timestamp_column: "<name>"
timestamp_format: "<format>"
sampling_period_seconds: 1.0
label_column: "<name>"
label_encoding:
  normal: "<value>"
  attack: "<value>"
canonical_rule_view:
  sampling_period_seconds: 1.0
  preprocessing: []
optional_gdn_view:
  sampling_period_seconds: 10.0
  aggregation: "median"
  label_aggregation: "max"
notes: []
```

Do not include raw rows or absolute paths in committed manifests.
