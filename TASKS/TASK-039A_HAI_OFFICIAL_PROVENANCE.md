# TASK-039A: HAI 23.05 Official Provenance Audit

## Objective

Verify the official `icsdataset/hai` snapshot and the exact HAI 23.05 Git-LFS
objects, then publish only structural provenance and a dataset-neutral
`DatasetManifestV2`.

## Frozen Source

- Repository: `https://github.com/icsdataset/hai`
- Snapshot: `2a814cebc9a66b06c9e5cd545e2d72e65d383737`
- HAI/HAIEnd 23.05 introduction:
  `ebcd09bbb432a35be39dcfaf1d800083fd06777b`
- LFS include: `hai-23.05/**`
- Official byte-equivalent payload remediation: TASK-039AR may use only
  `icsdataset/hai-security-dataset` with metadata-first, file-selective access.
- HAIEnd and all other alternate sources: excluded

## Execution Separation

Commit A freezes implementation, schemas, expected hashes, synthetic tests,
and privacy policy. No real audit result is included. From a clean Commit A,
the official checkout is cloned outside this repository with LFS smudge
disabled, detached at the pinned commit, and only `hai-23.05/**` is
materialized. Commit B records sanitized public results only.

## Public Boundary

Public artifacts may contain file hashes and sizes, structural CSV metadata,
aggregate label alignment and event counts, reference inventory, and a private
custody artifact hash. They must not contain raw rows, feature statistics,
attack intervals, attack targets, positive-point counts, event ordering, or
absolute local paths.

## Completion

Passing status is `passed_hai_2305_official_provenance_audit`. A pass verifies
source and structural readiness only. Process feasibility and process
selection remain TASK-039B.
