# DEC-007 SWaT Provenance Precheck

Status: unresolved

This precheck records what can be verified before opening any final SWaT
evaluation path. It does not approve final test access and does not convert the
current local CSV files into final-evaluation data.

## Verified Public Sources

Official iTrust dataset pages checked on 2026-06-25:

- [iTrust Datasets](https://www.sutd.edu.sg/itrust/itrust-labs/datasets/)
- [iTrust Request for Datasets](https://www.sutd.edu.sg/itrust/request-for-datasets/)
- [iTrust Terms of Usage](https://www.sutd.edu.sg/itrust/itrust-labs/datasets/terms-of-usage/)
- [iTrust Summary of Available Datasets](https://www.sutd.edu.sg/itrust/itrust-labs/datasets/summary-of-available-datasets/)

Observed from the public iTrust pages:

- iTrust lists Secure Water Treatment (SWaT) among available datasets.
- iTrust says dataset requests may take up to three working days.
- The request form includes SWaT as a selectable dataset.
- The request form requires agreement to the iTrust dataset terms.
- The terms require credit to iTrust/SUTD when publishing work using the data.
- The terms require informing iTrust when such work is published.
- The terms prohibit sharing the dataset with others.
- The summary page lists SWaT `A1 & A2 Dec 2015` among available datasets.

## Current Local Data Status

Current local files remain:

- `dataset_status: local_unverified_smoke_test`
- `source_kind: kaggle_mirror`
- `terms_of_use_status: unverified`
- `dataset_edition: unverified`

The local files are:

- `normal.csv`
- `attack.csv`
- `merged.csv`

These files appear label-separated or derived from a merged file. They are not
yet established as official iTrust train/test files and must not be used for
final SWaT performance claims.

## DEC-007 Cannot Be Resolved Yet

DEC-007 remains open because the following are still missing:

- documented official iTrust request/approval record or approved alternative,
- confirmed terms acknowledgement for this project,
- exact dataset edition/version selected for final evaluation,
- official or approved file list,
- file hashes for the approved final-evaluation files,
- final split protocol,
- sealed test access policy,
- primary and supplementary metric list approval,
- Git-tracking policy for final evaluation artifacts.

## Required Researcher Actions

Before final SWaT evaluation:

1. Decide whether final evaluation will use official iTrust SWaT files or a
   researcher-approved Kaggle mirror.
2. If using iTrust, request the dataset through the official iTrust form and
   retain the approval/download record outside Git.
3. Confirm that project usage satisfies the iTrust terms.
4. Record the exact dataset edition/version and file names.
5. Hash the approved local files without committing the files.
6. Approve a final split protocol.
7. Approve final-test access policy.
8. Approve the final metric list.
9. Approve which aggregate artifacts may be tracked in Git.

## Recommended Final-Evaluation Policy

Until explicitly changed by the researcher:

- Use PA-free metrics as primary.
- Keep point-adjusted metrics supplementary only.
- Do not tune thresholds, K, prompts, rules, or fusion weights on final test.
- Use `SWAT_DATA_ROOT` for local data access.
- Do not commit raw rows, extracted windows, raw-sequence plots, or downloadable
  derived samples.
- Treat any post-test change as a separate exploratory run, not the primary
  result.

## Result

DEC-007 remains unresolved. TASK-014 remains limited to harness code, configs,
documentation, and synthetic tests.
