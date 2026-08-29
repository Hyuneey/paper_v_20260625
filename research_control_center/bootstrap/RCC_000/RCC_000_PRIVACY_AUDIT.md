# RCC-000 Privacy and Data-Boundary Audit

## Scope

This audit inspected Git object names, tracked public files, public custody
metadata, the exact-blob legacy-path disposition, and the existing path scanner.
It did not open raw HAI data, test1/test2 features, labels, private numeric
registries, models, thresholds, FusionEvidenceV2, or MetricEvidenceV2.

- Audited scientific checkpoint: `origin/research-v6-thesis-checkpoint` at
  `2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e`.
- Additional documentation overlay checked: thesis branch at
  `ebc5a57bfdb7d8266f96f2990338effb9d0a2743`.
- Scientific executions: `0`.
- Test2 feature-byte reads: `0`.
- Test2 label reads: `0`.
- Private payload opens: `0`.

## Tracked-tree findings

| Gate | Result |
|---|---:|
| `.env` candidates | `0` |
| database candidates | `0` |
| private model/binary suffix candidates | `0` |
| raw HAI test CSV/parquet candidates | `0` |
| secret or credential pattern matches | `0` |
| new unpublished current-host path files | `0` |
| current generator absolute-path emission capability | `0` |
| established private scientific-value exposures | `0` |

The repository contains seven tracked CSV files, all in public reporting/test
fixture roles; none matched the raw HAI/test filename policy. `.gitignore`
continues to block CSV by default, artifact directories, `.env` variants, and
private model/data formats.

## Legacy locator disposition

The earlier base inventory reconciles to `156` host-locator occurrences in
`30` files. After the prospective generator fix, the current checkpoint keeps
`155` occurrences in `29` exact allowlisted blobs. These are already-published
historical environment locators, not current runtime authorities, credentials,
raw rows, or private scientific values. The scanner permits only the exact
repository-relative path plus exact blob SHA listed in
`docs/reproducibility/LEGACY_PUBLIC_HOST_PATH_DISPOSITION_V1.json`; a one-byte
change invalidates grandfathering.

Six additional generic path strings occur only in synthetic negative-test
fixtures and do not match the current host identity. They are not live
locators.

## Required off-Git boundary

The following must remain outside Git:

- official raw HAI payloads, including test1/test2 features and labels;
- local split/data roots and machine-local custody bindings;
- private normal-only numeric registries and calibrated values;
- private PCA model and threshold payloads;
- private D1 relation evidence where governed as private;
- private FusionEvidenceV2 and MetricEvidenceV2 payloads;
- provider credentials and unredacted private provider responses.

Git may retain only public code/configs, aggregate public reports, sanitized
predictions/metrics, logical roles, content hashes, and public custody/status
records.

## Current checkout caveat

The primary checkout contains pre-existing untracked preservation/worktree
directories. They were not added by RCC-000 and are not Git-tracked. The
tracked-tree privacy verdict therefore comes from explicit refs and Git blobs,
not from treating every local untracked directory as public content.

## Verdict

`PRIVATE_EXPOSURES = 0`

`PRIVACY_AUDIT = PASS_WITH_GRANDFATHERED_LEGACY_LOCATOR_METADATA`

The legacy count is reported separately and is not a reason to rewrite frozen
history.
