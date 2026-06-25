# DEC-007 Official SWaT Resolution Package

Status: prepared, not resolved

Preferred final-evaluation source: official iTrust SWaT request route.

Current local/Kaggle CSV files remain `local_unverified_smoke_test` and must not
be used for final SWaT performance claims.

## Resolution Gate

DEC-007 for the final primary benchmark may be marked resolved only after all
items below are complete. The source route is official iTrust only.

| Requirement | Status |
|---|---|
| Official iTrust source selected | pending |
| Terms acknowledged | pending |
| Exact edition/version/file list recorded | pending |
| Approved files hashed locally | pending |
| Final split protocol frozen | pending |
| Final metric protocol frozen | pending |
| Sealed-test access policy approved | pending |
| Git artifact policy approved | pending |

## Official iTrust Request Checklist

Record outside Git:

- request date,
- requester name,
- requester organization,
- organization email used,
- dataset requested: `SWaT`,
- iTrust request confirmation,
- iTrust approval or download authorization,
- download date,
- downloaded archive/file names,
- storage location outside the Git worktree,
- private record reference ID to cite in tracked manifests.

Tracked files must not contain private request emails, tokens, download links,
personal information, or raw data.

## Terms Acknowledgement

Record in tracked manifest:

- `terms_acknowledged: true | false`,
- `terms_acknowledged_by`,
- `terms_acknowledged_date`,
- `terms_source_url`,
- `required_credit_statement`,
- `no_sharing_acknowledged`,
- `publication_notification_acknowledged`.

Do not mark terms as acknowledged until the researcher confirms compliance with
the iTrust dataset terms for this project.

## Official SWaT Manifest Schema

Use `OfficialSwatProvenanceManifest` from `paperworks.data`.

Required tracked fields:

- `dataset_name`,
- `source_route`,
- `request_record_reference`,
- `approval_record_reference`,
- `terms_acknowledged`,
- `terms_acknowledged_by`,
- `terms_acknowledged_date`,
- `terms_source_url`,
- `required_credit_statement`,
- `no_sharing_acknowledged`,
- `publication_notification_acknowledged`,
- `dataset_edition`,
- `dataset_version`,
- `files`,
- `split_protocol_frozen`,
- `metric_protocol_frozen`,
- `sealed_test_access_policy_approved`,
- `git_artifact_policy_approved`,
- `final_test_opened: false` before execution.

Each file record must include:

- logical role,
- relative path under `SWAT_DATA_ROOT`,
- SHA-256 hash,
- byte size,
- row count if computed,
- version note.

## SHA-256 Hashing Procedure

Approved files must be stored outside Git and accessed through `SWAT_DATA_ROOT`.

Example Python usage:

```python
from pathlib import Path
from paperworks.data import build_official_swat_file_record

record = build_official_swat_file_record(
    root=Path(r"D:\local\swat_official"),
    relative_path="SWaT_A1_A2_Dec_2015/train.csv",
    logical_role="official_train_normal",
    rows_excluding_header=None,
    file_version_note="SWaT A1 and A2 Dec 2015",
)
print(record.sha256)
```

Example PowerShell hash command:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath "D:\local\swat_official\SWaT_A1_A2_Dec_2015\train.csv"
```

Do not commit the approved files.

## Final Split Protocol Freeze

Before sealed test access:

- split before windowing,
- define `train_normal`, `calibration_normal`, `validation`, and `test`,
- record raw index/timestamp ranges,
- record purge gap,
- record source file hashes,
- record preprocessing config,
- record random seed if any,
- freeze all thresholds, K values, prompt configs, verifier configs, and fusion weights.

After sealed test access, changes to thresholds, K, prompts, rules, or fusion
weights are prohibited for the primary run.

## Final Metric Protocol Freeze

Primary metrics:

- PA-free precision,
- PA-free recall,
- PA-free F1,
- AUROC,
- AUPRC,
- event/range metrics only if pre-registered.

Supplementary metrics:

- point-adjusted metrics, clearly labeled with `point_adjusted_`,
- range IoU if applicable.

Point-adjusted metrics must not be primary and must not be used for model,
threshold, rule, K, prompt, or fusion selection.

## Allowed Git-Tracked Artifacts

Allowed:

- manifests,
- file hashes,
- schema summaries,
- config snapshots,
- split manifests,
- aggregate metrics,
- aggregate reports,
- non-reconstructive plots only if explicitly approved.

Forbidden:

- raw rows,
- extracted windows,
- downloadable derived samples,
- raw sequence plots,
- private iTrust request emails,
- download links or tokens,
- API keys or secrets.

## Sealed-Test One-Way Execution Log

Use `docs/templates/SEALED_TEST_EXECUTION_LOG_TEMPLATE.md`.

The log must record:

- DEC-007 resolution reference,
- frozen config hashes,
- manifest hash,
- split manifest hash,
- command invoked,
- start/end timestamps,
- code commit,
- final test access timestamp,
- output artifact hashes,
- confirmation that no post-test tuning occurred.

## Current Result

DEC-007 remains unresolved. This package prepares the resolution workflow but
does not approve final test access.
