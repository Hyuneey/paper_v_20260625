# TASK-039AR: Official HAI 23.05 Distribution Byte Equivalence

## Objective

Remediate the official Git-LFS budget block by selectively acquiring the same
ten HAI 23.05 payload files from the official Kaggle dataset owned by
`icsdataset`, while retaining the pinned official Git commit and Git-LFS
pointers as identity and integrity authority.

## Preserved Blocked History

Before remediation, the complete local sequence above `origin/main` was:

1. `3f272b7ba7a313b31bde4b589b65cb3094f72aec` - TASK-039A implementation;
2. `8ad80118c5272a7d62e20fa5f69cf366720bccbf` - sanitized acquisition block;
3. `14f3d3d12ae2e3140758b49b6770c423f3de6c12` - blocked provenance result.

The sequence is preserved at remote branch `task-039a-blocked-lfs`, whose tip
is `14f3d3d12ae2e3140758b49b6770c423f3de6c12`. `origin/main` remained
`5ac59b9e77ff52fe7beb85276f1ca8ae42c9bf4e` during recovery. Inspection of
`8ad80118` confirmed that its tree contains the reusable implementation and no
authoritative passing result, so it is the remediation base.

## Execution Order

1. Commit this implementation and synthetic tests.
2. Query only official Kaggle API v1 metadata and freeze the complete version
   inventory in Git.
3. From that clean metadata commit, download exactly the ten allowlisted files
   through the per-file endpoint.
4. Require exact SHA-256 and size equality with both the official Git-LFS
   pointer and TASK-039A config for every file.
5. Materialize only verified bytes into the local official checkout's LFS
   object store.
6. Resume the complete TASK-039A audit without changing its scientific or
   privacy boundary.

The implementation uses Python standard-library HTTPS against Kaggle API v1;
no Kaggle package installation is required. Redirects are restricted to frozen
official delivery hosts, and no response URL is persisted.

## Completion

TASK-039AR passes only as
`passed_official_distribution_byte_equivalence`. TASK-039A must then also pass
as `passed_hai_2305_official_provenance_audit` before `main` may be pushed or
TASK-039B may begin.
