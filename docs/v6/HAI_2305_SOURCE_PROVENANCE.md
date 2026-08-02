# HAI 23.05 Source Provenance

TASK-039A pins the official repository at
`2a814cebc9a66b06c9e5cd545e2d72e65d383737` and permits only the official
GitHub remote and its Git-LFS endpoints. The checkout and raw files remain
outside the paper repository.

The implementation freeze is complete. The first real execution reached the
pinned snapshot but was blocked by the official repository's LFS budget; that
trace is preserved on `task-039a-blocked-lfs`.

TASK-039AR authorizes only `icsdataset/hai-security-dataset` as an official
selective payload transport. The Kaggle bytes must exactly equal the frozen Git
LFS OIDs and sizes before TASK-039A resumes. No moving ref, mirror, unrelated
archive, whole multi-version download, or HAIEnd payload is authorized.
